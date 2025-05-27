"""
    Interface for adding profiles manually via a dialog window.
    This widget allows users to define ditch dimensions, select vegetation type,
    calculate hydraulic properties, visualize the profile, and save it.
"""
import os.path
import sqlite3
from decimal import Decimal

from PyQt5.QtCore import QSettings, pyqtSignal, Qt

if __name__ == '__main__':
    import sys
    sys.path.append(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )



from qgis.PyQt import QtCore, QtWidgets

import pyqtgraph as pg
from legger.utils.theoretical_profiles import calc_pitlo_griffioen
from legger.sql_models.legger_database import load_spatialite
from legger.utils.formats import try_round
from legger.utils.theoretical_profiles import HydroObject


class LeggerPlotWidget(pg.PlotWidget):
    """
    A custom PlotWidget using pyqtgraph to display the ditch cross-section.
    """
    def __init__(self, parent=None, name=""):
        """
        Initialize the plot widget.

        Args:
            parent: The parent widget.
            name (str): An optional name for the plot widget.
        """
        super(LeggerPlotWidget, self).__init__(parent)
        self.name = name
        self.showGrid(True, True, 1)
        self.setLabel("bottom", "breedte", "m")
        self.setLabel("left", "hoogte", "m tov waterlijn")
        self.getAxis('left').enableAutoSIPrefix(False)
        self.getAxis('bottom').enableAutoSIPrefix(False)

        # Initialize dimension attributes
        self.water_width = 0
        self.water_depth = 0
        self.talud = 1 # Avoid division by zero if draw_lines is called before set_data
        self.bottom_width = 0
        self.hydraulic_depth = 0
        self.hydraulic_bottom_width = 0
        self.inlet_offset = 0

        self.profile_plot = pg.PlotDataItem(
            x=[],
            y=[],
            connect='finite',
            pen=pg.mkPen(
                # green
                color='#00FF00',
                width=3
            )
        )
        self.hydraulic_plot = pg.PlotDataItem(
            x=[],
            y=[],
            connect='finite',
            pen=pg.mkPen(
                # orange
                color='#FFA500',
                width=3
            )
        )
        self.inlet_plot = pg.PlotDataItem(
            x=[],
            y=[],
            connect='finite',
            pen=pg.mkPen(
                # blue
                color='#0000FF',
                width=3
            )
        )
        self.addItem(self.profile_plot)
        self.addItem(self.hydraulic_plot)
        self.addItem(self.inlet_plot)

    def set_data(self,
                 water_width,
                 water_depth,
                 talud,
                 bottom_width,
                 hydraulic_depth,
                 hydraulic_bottom_width,
                 inlet_offset
                 ):
        """
        Set the ditch dimension data and trigger a redraw.

        """
        self.water_width = float(water_width)
        self.water_depth = float(water_depth)
        self.talud = float(talud)
        self.bottom_width = float(bottom_width)
        self.hydraulic_depth = float(hydraulic_depth)
        self.hydraulic_bottom_width = float(hydraulic_bottom_width)
        self.inlet_offset = float(inlet_offset)

        self.draw_lines()

    def draw_lines(self):
        """
        Clear the existing plot and draw the trapezoidal ditch profile.
        """
        # self.clear()

        self.profile_plot.setData(
            x=[
            - 0.5 * self.water_width,
            -0.5 * self.bottom_width,
            0.5 * self.bottom_width,
            0.5 * self.water_width
        ],
            y=[
            0,
            -1 * self.water_depth,
            -1 * self.water_depth,
            0
        ])

        # hydraulic
        self.hydraulic_plot.setData(
            x=[
                -0.5 * self.hydraulic_bottom_width,
                0.5 * self.hydraulic_bottom_width
            ],
            y=[
                -1 * self.hydraulic_depth,
                -1 * self.hydraulic_depth,
            ],
        )

        if self.inlet_offset > 0:
            self.inlet_plot.setData(
                x=[- 0.5 * self.water_width,0.5 * self.water_width],
                y=[-1 * self.inlet_offset, -1 * self.inlet_offset],
            )
        else:
            self.inlet_plot.setData(
                x=[],
                y=[],
            )

        self.autoRange()

def first(iterable, condition, default=None):
    for el in iterable:
        if condition(el):
            return el
    return default


class NewWindow(QtWidgets.QWidget):
    """
    Dialog window for manually defining, calculating, and saving a new ditch profile variant.
    """
    closeSignal = pyqtSignal()

    def __init__(self, hydro_id, legger_db_filepath, callback_on_save=None):
        """
        Initialize the dialog window.

        Args:
            hydro_id: number
            legger_db_filepath: path
            callback_on_save (callable, optional): A function to call to save the new variant.
        """

        super(NewWindow, self).__init__()

        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.hydro_id = hydro_id
        self.callback_on_save = callback_on_save

        conn = load_spatialite(legger_db_filepath)

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Step 1: Read the database
        cursor.execute("""
            Select ho.id, ho.code, km.diepte, (ho.zomerpeil - ho.streefpeil) as zpeil_diff, km.breedte, 
            ho.categorieoppwaterlichaam, km.taludvoorkeur, km.grondsoort, 1, ho.debiet, ho.debiet_inlaat 
            from hydroobject ho 
            left outer join kenmerken km on ho.id = km.hydro_id 
            where ho.id = ?
            """,(
            hydro_id,
        ))

        row = cursor.fetchall()
        row = row[0] if len(row) > 0 else None

        if row is None:
            print("Hydro object not found")
            label = QtWidgets.QLabel(self)
            label.setText("Hydrovak not found...")
            return

        self.hydro_code = row[1]

        self.hydro = HydroObject(
            *row
        )

        self.setup_ui()

        # begroeiingsvariant
        cursor.execute("""
            SELECT 
            naam, 
            friction_manning, 
            friction_begroeiing,
            begroeiingsdeel,
            is_default,
            id
            FROM begroeiingsvariant 
            ORDER BY friction_manning""")

        self.variant_mapping = {
            v[0]: {
                'naam': v[0],
                'friction_manning': v[1],
                'friction_begroeiing': v[2],
                'begroeiingsdeel': v[3],
                'is_default': v[4],
                'id': v[5]
            }
            for v in cursor.fetchall()
        }

        default_variant = first(self.variant_mapping.values(), lambda v: v.get('is_default'))
        default_variant = (default_variant.get('naam')
                           if default_variant is not None
                           else list(self.variant_mapping.values())[0].get('naam'))

        self.variants = [el.get('naam') for el in self.variant_mapping.values()]
        self.begroeiings_combo.insertItems(
            0, self.variants
        )
        # grondsoort
        self.grondsoorten = [v for v in HydroObject.slopes.keys()]
        self.grondsoort_combo.insertItems(
            0, self.grondsoorten
        )

        self.settings = QSettings("leggertool", "new_profile")

        defaults = {
            'begroeiingsgraad': self.settings.value("begroeiingsgraad", default_variant),
            'talud': Decimal(self.settings.value("talud", 2)),
            'waterbreedte': Decimal(self.settings.value("waterbreedte", 2.4)),
            'waterdiepte': Decimal(self.settings.value("waterdiepte", 0.5)),
        }

        # default begroeiingsvariant
        self.begroeiings_combo.setCurrentIndex(self.variants.index(defaults['begroeiingsgraad']))
        if self.hydro.grondsoort in self.grondsoorten:
            self.grondsoort_combo.setCurrentIndex(self.grondsoorten.index(self.hydro.grondsoort))
        else:
            self.grondsoort_combo.setCurrentIndex(self.grondsoorten.index('default'))
        self.input_ditch_slope.setValue(defaults.get('talud'))
        self.input_ditch_width.setValue(defaults.get('waterbreedte'))
        self.input_waterdepth.setValue(defaults.get('waterdiepte'))

        self.calculate_and_set_values()

        # connect fields
        self.input_waterdepth.valueChanged.connect(self.calculate_and_set_values)
        self.input_ditch_width.valueChanged.connect(self.calculate_and_set_values)
        self.input_ditch_slope.valueChanged.connect(self.calculate_and_set_values)
        self.begroeiings_combo.currentIndexChanged.connect(self.calculate_and_set_values)
        self.grondsoort_combo.currentIndexChanged.connect(self.calculate_and_set_values)
        self.custom_talud.stateChanged.connect(self.change_custom_talud)

    def close(self):

        self.input_waterdepth.valueChanged.disconnect(self.calculate_and_set_values)
        self.input_ditch_width.valueChanged.disconnect(self.calculate_and_set_values)
        self.input_ditch_slope.valueChanged.disconnect(self.calculate_and_set_values)
        self.begroeiings_combo.currentIndexChanged.disconnect(self.calculate_and_set_values)
        self.grondsoort_combo.currentIndexChanged.disconnect(self.calculate_and_set_values)
        self.custom_talud.stateChanged.disconnect(self.change_custom_talud)

        self.closeSignal.emit()

        super(NewWindow, self).close()

    def calculate_and_set_values(self):

        water_width = Decimal(self.input_ditch_width.value())
        water_depth = Decimal(self.input_waterdepth.value())
        if self.custom_talud.isChecked():
            talud = Decimal(self.input_ditch_slope.value())
            self.settings.setValue("talud", float(talud))
        else:
            talud = None

        begroeiings_variant = self.variants[self.begroeiings_combo.currentIndex()]
        grondsoort = self.grondsoorten[self.grondsoort_combo.currentIndex()]

        self.settings.setValue("begroeiingsgraad", begroeiings_variant)
        self.settings.setValue("waterbreedte", float(water_width))
        self.settings.setValue("waterdiepte", float(water_depth))

        self.hydro.set_grondsoort(grondsoort)

        size = self.hydro.get_profile_and_gradient_from_water_width_and_legger_depth(
            legger_depth=water_depth,
            water_width=water_width,
            slope=talud,
        )

        bv = self.variant_mapping[begroeiings_variant]

        gradient_pitlo_griffioen_inlet = None
        gradient_pitlo_griffioen = None

        if size.get('hydraulic_bottom_width') >= 0:
            if size.get('hydraulic_depth') >= 0.05 and self.hydro.normative_flow is not None:
                gradient_pitlo_griffioen = calc_pitlo_griffioen(
                    abs(self.hydro.normative_flow),
                    size.get('hydraulic_bottom_width'),
                    size.get('hydraulic_depth'),
                    size.get('slope'),
                    bv['friction_manning'],
                    bv['friction_begroeiing'],
                    bv['begroeiingsdeel']
                )

            if size.get('hydraulic_depth_inlet') >= 0.05 and self.hydro.debiet_inlaat is not None:
                gradient_pitlo_griffioen_inlet = calc_pitlo_griffioen(
                    abs(self.hydro.debiet_inlaat),
                    size.get('hydraulic_bottom_width'),
                    size.get('hydraulic_depth_inlet'),
                    size.get('slope'),
                    bv['friction_manning'],
                    bv['friction_begroeiing'],
                    bv['begroeiingsdeel']
                )

        self.output_waterdepth_hydraulic.setText(f"{try_round(size.get('hydraulic_depth'), 2)} m")
        self.output_waterdepth_hydraulic_inlet.setText(f"{try_round(size.get('hydraulic_depth_inlet'), 2)} m")
        self.output_ditch_bottomwidth.setText(f"{try_round(size.get('bottom_width'), 2)} m")
        self.output_ditch_bottomwidth_hydraulic.setText(f"{try_round(size.get('hydraulic_bottom_width'), 2)} m hydraulisch")
        self.input_ditch_slope.setValue(size.get('slope'))

        self.output_norm_gradient.setText(f"{try_round(self.hydro.gradient_norm, 2)} cm/ km")
        self.output_norm_gradient_inlet.setText(f"{try_round(self.hydro.gradient_norm_inlaat, 2)} cm/ km")
        self.output_gradient.setText(f"{try_round(gradient_pitlo_griffioen, 2, '-')} cm/ km")
        self.output_inlet_gradient.setText(f"{try_round(gradient_pitlo_griffioen_inlet, 2, '-')} cm/ km")

        norm = self.hydro.gradient_norm
        valid = True
        if gradient_pitlo_griffioen is None:
            self.output_gradient.setStyleSheet("color: red; font-weight: normal;")
            valid = False
        elif gradient_pitlo_griffioen > self.hydro.gradient_norm:
            # color red
            self.output_gradient.setStyleSheet("color: red; font-weight: normal;")
        else:
            # default color
            self.output_gradient.setStyleSheet("color: black; font-weight: normal;")

        if gradient_pitlo_griffioen_inlet is None:
            if size.get('hydraulic_depth_inlet') < 0.05:
                self.output_waterdepth_hydraulic_inlet.setStyleSheet("color: red; font-weight: normal;")
                valid = False
            else:
                self.output_waterdepth_hydraulic_inlet.setStyleSheet("color: black; font-weight: normal;")
        elif gradient_pitlo_griffioen_inlet > self.hydro.gradient_norm_inlaat:
            # color red
            self.output_inlet_gradient.setStyleSheet("color: red; font-weight: normal;")
        else:
            # default color
            self.output_inlet_gradient.setStyleSheet("color: black; font-weight: normal;")

        # width of the ditch
        if size.get('bottom_width') < 0:
            self.output_ditch_bottomwidth.setStyleSheet("color: red; font-weight: normal;")
            valid = False
        else:
            self.output_ditch_bottomwidth.setStyleSheet("color: black; font-weight: normal;")

        if valid:
            self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(False)

        self.plot_widget.set_data(
            water_width=water_width,
            water_depth=water_depth,
            talud=size.get('slope'),
            bottom_width=size.get('bottom_width'),
            hydraulic_depth=size.get('hydraulic_depth'),
            hydraulic_bottom_width=size.get('hydraulic_bottom_width'),
            inlet_offset=size.get('hydraulic_depth') - size.get('hydraulic_depth_inlet')
        )

        return {
            'begroeiingsvariant': begroeiings_variant,
            'begroeiingsvariant_id': bv.get('id'),
            'water_width': water_width,
            'water_depth': water_depth,
            'talud': size.get('slope'),
            'bottom_width': size.get('bottom_width'),
            'hydraulic_depth': size.get('hydraulic_depth'),
            'hydraulic_bottom_width': size.get('hydraulic_bottom_width'),
            'inlet_offset': size.get('hydraulic_depth') - size.get('hydraulic_depth_inlet'),
            'gradient': gradient_pitlo_griffioen,
            'gradient_inlet': gradient_pitlo_griffioen_inlet,
        }

    def change_custom_talud(self):
        self.input_ditch_slope.setEnabled(self.custom_talud.isChecked())
        self.calculate_and_set_values()

    def cancel_application(self):
        self.close()

    def save_and_close(self):

        out = self.calculate_and_set_values()

        if self.callback_on_save is not None:
            self.callback_on_save(out)

        self.close()

    def setup_ui(self):
        # Hoofd layout definieren
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.gridLayout = QtWidgets.QGridLayout()

        # hydrovak code
        label = QtWidgets.QLabel(self)
        label.setText("Hydrovak code")
        label_value = QtWidgets.QLabel(self)
        label_value.setText(self.hydro_code)
        self.gridLayout.addWidget(label, 0, 0, 1, 1)
        self.gridLayout.addWidget(label_value, 0, 1, 1, 1)

        # invoervelden:
        # grondsoort
        label = QtWidgets.QLabel(self)
        label.setText("Grondsoort")
        self.grondsoort_combo = QtWidgets.QComboBox(self)
        self.gridLayout.addWidget(label, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.grondsoort_combo, 3, 1, 1, 2)

        # begroeiingsgraad
        label = QtWidgets.QLabel(self)
        label.setText("Begroeiingsgraad")
        self.begroeiings_combo = QtWidgets.QComboBox(self)
        self.gridLayout.addWidget(label, 4, 0, 1, 1)
        self.gridLayout.addWidget(self.begroeiings_combo, 4, 1, 1, 2)

        # talud
        label = QtWidgets.QLabel(self)
        label.setText("Custom talud")
        self.custom_talud = QtWidgets.QCheckBox(self)
        self.custom_talud.setChecked(False)
        self.gridLayout.addWidget(label, 5, 0, 1, 1)
        self.gridLayout.addWidget(self.custom_talud, 5, 1, 1, 2)

        # Spinbox talud

        label = QtWidgets.QLabel(self)
        label.setText("Talud")
        # Spinbox talud
        self.input_ditch_slope = QtWidgets.QDoubleSpinBox(self)
        self.input_ditch_slope.setSuffix(" m breedte / m hoogteverschil")
        self.input_ditch_slope.setSingleStep(0.1)
        self.input_ditch_slope.setDisabled(True)
        self.gridLayout.addWidget(label, 6, 0, 1, 1)
        self.gridLayout.addWidget(self.input_ditch_slope, 6, 1, 1, 2)

        # titels: onderhoudsprofiel en hydraulisch profiel
        # label = QtWidgets.QLabel(self)
        # label.setText("Onderhoudsprofiel:")
        # self.gridLayout.addWidget(label, 7, 1, 1, 1)
        # label = QtWidgets.QLabel(self)
        # label.setText("Hydraulisch profiel:")
        # self.gridLayout.addWidget(label, 7, 2, 1, 1)

        # waterbreedte / bodembreedte
        label = QtWidgets.QLabel(self)
        label.setText("Waterbreedte")
        self.input_ditch_width = QtWidgets.QDoubleSpinBox(self)
        self.input_ditch_width.setSuffix(" m")
        self.input_ditch_width.setSingleStep(0.1)
        self.gridLayout.addWidget(label, 8, 0, 1, 1)
        self.gridLayout.addWidget(self.input_ditch_width, 8, 1, 1, 1)

        # output bottom width
        label = QtWidgets.QLabel(self)
        label.setText("Bodembreedte")
        self.output_ditch_bottomwidth = QtWidgets.QLabel(self)
        self.output_ditch_bottomwidth.setText('... m')
        self.output_ditch_bottomwidth_hydraulic = QtWidgets.QLabel(self)
        self.output_ditch_bottomwidth_hydraulic.setText('... m hydraulisch')
        self.gridLayout.addWidget(label, 9, 0, 1, 1)
        self.gridLayout.addWidget(self.output_ditch_bottomwidth, 9, 1, 1, 1)
        self.gridLayout.addWidget(self.output_ditch_bottomwidth_hydraulic, 9, 2, 1, 1)

        # waterdiepte
        label = QtWidgets.QLabel(self)
        label.setText("Onderhoudsdiepte")
        self.input_waterdepth = QtWidgets.QDoubleSpinBox(self)
        self.input_waterdepth.setSuffix(" m")
        self.input_waterdepth.setSingleStep(0.1)

        self.gridLayout.addWidget(label, 10, 0, 1, 1)
        self.gridLayout.addWidget(self.input_waterdepth, 10, 1, 1, 1)

        # gradient
        label = QtWidgets.QLabel(self)
        label.setText("Afvoer:")
        self.gridLayout.addWidget(label, 11, 1, 1, 1)
        label = QtWidgets.QLabel(self)
        label.setText("Inlaat:")
        self.gridLayout.addWidget(label, 11, 2, 1, 1)

        label = QtWidgets.QLabel(self)
        label.setText("Leggeriepte:")
        self.output_waterdepth_hydraulic = QtWidgets.QLabel(self)
        self.output_waterdepth_hydraulic.setText('... m')
        self.output_waterdepth_hydraulic_inlet = QtWidgets.QLabel(self)
        self.output_waterdepth_hydraulic_inlet.setText('... m')
        self.gridLayout.addWidget(label, 12, 0, 1, 1)
        self.gridLayout.addWidget(self.output_waterdepth_hydraulic, 12, 1, 1, 1)
        self.gridLayout.addWidget(self.output_waterdepth_hydraulic_inlet, 12, 2, 1, 1)

        label = QtWidgets.QLabel(self)
        label.setText("Debiet:")
        self.label_debiet = QtWidgets.QLabel(self)
        self.label_debiet.setText(str(round(abs(self.hydro.normative_flow), 4)) + ' m3/s')
        self.label_debiet_inlet = QtWidgets.QLabel(self)
        self.label_debiet_inlet.setText(str(round(abs(self.hydro.debiet_inlaat), 4)) + ' m3/s')
        self.gridLayout.addWidget(label, 13, 0, 1, 1)
        self.gridLayout.addWidget(self.label_debiet, 13, 1, 1, 1)
        self.gridLayout.addWidget(self.label_debiet_inlet, 13, 2, 1, 1)

        label = QtWidgets.QLabel(self)
        label.setText("Norm:")
        self.output_norm_gradient = QtWidgets.QLabel(self)
        self.output_norm_gradient.setText("... cm/ km")
        self.output_norm_gradient_inlet = QtWidgets.QLabel(self)
        self.output_norm_gradient_inlet.setText("... cm/ km")
        self.gridLayout.addWidget(label, 14, 0, 1, 1)
        self.gridLayout.addWidget(self.output_norm_gradient, 14, 1, 1, 1)
        self.gridLayout.addWidget(self.output_norm_gradient_inlet, 14, 2, 1, 1)

        label = QtWidgets.QLabel(self)
        label.setText("Verhang:")
        self.output_gradient = QtWidgets.QLabel(self)
        self.output_gradient.setText("... cm/ km")
        self.output_inlet_gradient = QtWidgets.QLabel(self)
        self.output_inlet_gradient.setText("... cm/ km")
        self.gridLayout.addWidget(label, 15, 0, 1, 1)
        self.gridLayout.addWidget(self.output_gradient, 15, 1, 1, 1)
        self.gridLayout.addWidget(self.output_inlet_gradient, 15, 2, 1, 1)

        # Horizontale bovenste rij toevoegen aan bovenkant verticale HOOFD layout.
        self.verticalLayout.addLayout(self.gridLayout)

        # FIGUREN MAKEN
        # Figuur vlak aanmaken
        self.plot_widget = LeggerPlotWidget(self)
        # set min height to 400px
        self.plot_widget.setMinimumHeight(300)

        # Figuurvlak toevoegen in het MIDDEN van de hoofd lay-out.
        self.verticalLayout.addWidget(self.plot_widget)

        # OPSLAAN / ANNULEREN KNOPPEN
        # Vlak maken voor de knoppen
        self.bottom_row = QtWidgets.QHBoxLayout()  # knoppen komen naast elkaar dus een horizontal layout.
        self.bottom_row.setObjectName("Bottom_row")

        # Sluiten knop
        self.cancel_button = QtWidgets.QPushButton(self)
        self.cancel_button.setText("Annuleer")
        self.cancel_button.clicked.connect(self.cancel_application)
        self.bottom_row.addWidget(self.cancel_button)

        # Opslaan knop
        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setText("Opslaan en sluiten")
        self.save_button.clicked.connect(self.save_and_close)
        self.bottom_row.addWidget(self.save_button)

        # Opslaan / Annuleer knoppen toevoegen aan onderkant verticale HOOFD layout
        self.verticalLayout.addLayout(self.bottom_row)

        self.setWindowTitle("Extra profiel")
        QtCore.QMetaObject.connectSlotsByName(self)

# Example usage (for testing purposes, typically instantiated from elsewhere in the plugin)
if __name__ == '__main__':
    import sys
    from qgis.PyQt.QtWidgets import QApplication
    app = QApplication(sys.argv)

    db_path = r'/Users/bastiaanroos/Documents/testdata/leggertool/Westerkogge Standaard profiel vs gegenereerd/Westerkogge_check_verhang_verschil.sqlite'
    # Define a simple callback
    def my_callback(item, variant):
        print(f"Callback executed for item {item.hydrovak['hydro_id']} with variant {variant.id}")

    # Create and show the window
    window = NewWindow(113298, db_path, callback_on_save=my_callback)
    window.show()
    sys.exit(app.exec_())