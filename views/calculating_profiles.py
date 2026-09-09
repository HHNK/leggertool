import datetime
import logging
import time
import traceback
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget

from legger.sql_models.legger_database import LeggerDatabase
from legger.sql_models.legger_database import load_spatialite
from legger.utils.automatic_fill_legger import automatic_fill_legger
from legger.utils.calc_gradient import calc_gradient
from legger.utils.profile_match_a import doe_profinprof, maaktabellen
from legger.utils.redirect_flows_to_main_branches import redirect_flows
from legger.utils.snap_points import snap_points
from legger.utils.theoretical_profiles import create_variants

# tmp for testing

# -*- coding: utf-8 -*-

log = logging.getLogger(__name__)



class ProfileCalculationWidget(QWidget):  # , FORM_CLASS):
    """Dialog for making the pre-process steps for the Legger"""
    closingDialog = pyqtSignal()

    def __init__(
            self, parent, iface, polder_datasource, ts_datasource,
            parent_class):
        """Constructor

        parent (QtWidget): Qt parent Widget
        iface (QgisInterface: QGiS interface
        polder_datasource (str): Path to the 'legger' spatialite of a polder
        ts_datasource (TimeseriesDatasourceModel): 3di datasource of results
        parent_class: the tool class which instantiated this widget. Is used
             here for storing volatile information
        returns: None
        """
        super(ProfileCalculationWidget, self).__init__(parent)

        self.parent_class = parent_class
        self.iface = iface
        self.polder_datasource = polder_datasource
        self.ts_datasource = ts_datasource
        self.timestep = -1
        self.surge_selection = -1

        errormessage = "Kies eerst 3di output (model en netCDF) in de 'Select 3di results' van 3di plugin."
        try:
            self.path_model_db = self.ts_datasource.model_spatialite_filepath
        except:
            self.path_model_db = errormessage

        try:

            self.path_result_db = self.ts_datasource.rows[0].datasource_layer_helper.sqlite_gridadmin_filepath.replace(
                '\\', '/')

        except:
            self.path_result_db = errormessage

        try:
            self.path_result_nc = self.ts_datasource.rows[0].file_path.value
        except:
            self.path_result_nc = errormessage

        if self.path_model_db is None:
            self.path_model_db = errormessage

        # timestep combobox
        self.last_timestep_text = 'laatste tijdstap'
        self.timestamps = []

        self.setup_ui()

        # surge combobox
        self.last_surge_text = "kies opstuwingsnorm"

    def closeEvent(self, event):
        """
        event (QtEvent): event triggering close
        returns: None
        """

        self.closingDialog.emit()
        self.close()
        event.accept()

    def save_spatialite(self):
        """Change active modelsource. Called by combobox when selected
        spatialite changed
        returns: None
        """

        self.close()

    def explain_step_old_3di(self):
        """
        Uitleg van stap 3si
        """
        # detailed information on UPPER ROW groupbox
        self.msg_upper_row = QtWidgets.QMessageBox(self)
        self.msg_upper_row.setIcon(QtWidgets.QMessageBox.Information)
        self.msg_upper_row.setText("<b>Het selecteren van een tijdstap voor de leggerdatabase<b>")
        self.msg_upper_row.setInformativeText("In het netCDF bestand waar de 3di resultaten zijn opgeslagen is per "
                                              "'flowline' voor elke tijdstap informatie beschikbaar. Dit betekent dat "
                                              "eerst een tijdstap gekozen moet worden om de resultaten van deze tijdstap "
                                              "op te kunnen halen.\n"
                                              "In het geval van de hydraulische toets, wat gebruikt wordt voor de legger, "
                                              "zijn we geinteresseerd in de debieten over de 'flowlines' waarbij "
                                              "de neerslag som een stationair evenwicht heeft berijkt.\n\n"
                                              "Tip: In de BWN studie rekenen we een som door van 1 dag droog, 5 "
                                              "dagen regen en weer 2 dagen droog. Voor het meest stationaire moment "
                                              "selecteer de tijdstap aan het einde van de bui. Standaard is dit de"
                                              "tijdstap net onder de waarde 518400, maar kan afwijken. De slider van"
                                              "de tijdstappen moet tussen ongeveer 2/3 en 3/4 van de grootste tijdstap")

        self.box_step3diold.addWidget(self.msg_upper_row)

    def execute_redirect_flows(self):
        change_flow_direction = self.change_flow_direction_checkbox.isChecked()
        redirect_flows(self.polder_datasource, change_flow_direction=change_flow_direction)
        self.feedbacktext.setText("Debieten zijn aangepast.")

    def show_step_help(self, title, explanation):
        """Display a short explanation for a step."""
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(f"<b>{title}</b>")
        msg.setInformativeText(explanation)
        msg.exec_()

    def explain_step3(self):
        """
        Uitleg van stap 3
        """
        # detailed information on UPPER ROW groupbox
        self.msg_middle_row = QtWidgets.QMessageBox(self)
        self.msg_middle_row.setIcon(QtWidgets.QMessageBox.Information)
        self.msg_middle_row.setText("<b>Het berekenen van de varianten voor de leggerdatabase<b>")
        self.msg_middle_row.setInformativeText("Alle randvoorwaarden zijn nu bekend:\n"
                                               "breedte, diepte, Q, talud.\n"
                                               "Met de gekozen norm voor verhang wordt met iteraties berekend "
                                               "welke mogelijke leggerprofielen er mogelijk zijn. Dit betekent dat "
                                               "per hydro-object idealiter een hele lijst van 'mogelijke profielen' "
                                               "wordt berekend. Dat betekent dat er vanuit hydraulisch oogpunt dus "
                                               "ruimte is voor keuze.\n"
                                               "Let op: als een bestaande 'leggerdatabase' is ingelezen, dan kan het "
                                               "zo zijn dat door deze actie uit te voeren bestaande varianten worden "
                                               "overschreven met nieuwe (omdat randvoorwaarde verhang nu anders is.")

        self.box_step3.addWidget(self.msg_middle_row)

    def execute_step3_calculate_variants(self):

        db = LeggerDatabase(self.polder_datasource)
        # do one query, don't know what the reason was for this...

        self.feedbackmessage = ""

        try:
            self.feedbackmessage = self.feedbackmessage + f"\n{datetime.datetime.now().isoformat()[:19]} - Start profielen berekening."
            create_variants(self.polder_datasource)
            self.feedbackmessage = self.feedbackmessage + f"\n{datetime.datetime.now().isoformat()[:19]} - Profielen zijn berekend."
        except Exception as e:
            # raise e
            log.exception(e)
            self.feedbackmessage = self.feedbackmessage + (f"\n{datetime.datetime.now().isoformat()[:19]} - "
                                                           f"Fout, profielen konden niet worden berekend. melding: \n"
                                                           f"{e}\n"
                                                           f"{traceback.format_exc()}")
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

    def execute_add_standard_profiles(self):
        try:
            automatic_fill_legger(self.polder_datasource, add_only=True)
        except Exception as e:
            log.exception(e)
            self.feedbacktext.setText("fout bij toevoegen standaard profielen")
        else:
            self.feedbacktext.setText("standaard profielen toegevoegd")

    def execute_fill_standard_profiles(self):
        try:
            automatic_fill_legger(self.polder_datasource, fill_where_possible=True)
        except Exception as e:
            log.exception(e)
            self.feedbacktext.setText("fout bij invullen standaard profielen waar mogelijk")
        else:
            self.feedbacktext.setText("standaard profielen zijn ingevuld waar mogelijk")

    def execute_step5(self):

        con_legger = load_spatialite(self.polder_datasource)

        maaktabellen(con_legger.cursor())
        con_legger.commit()
        resultaat = doe_profinprof(con_legger.cursor(), con_legger.cursor())
        con_legger.commit()
        self.feedbacktext.setText(resultaat)
        self.feedbacktext.setText("De fit % zijn berekend.")

    def execute_snap_points(self):
        con_legger = load_spatialite(self.polder_datasource)

        snap_points(con_legger.cursor())

        self.feedbacktext.setText("De punten zijn gesnapt.")

    def post_process(self):
        calc_gradient(self.polder_datasource)
        self.feedbacktext.setText("Totaal gradient berekend")

    def export_to_gdb(self):
        from legger.utils.export_to_demo_gpkg import export_sqlite_view_to_geopackage
        export_sqlite_view_to_geopackage(self.polder_datasource, self)
        self.feedbacktext.setText("Export gelukt.")


    def setup_ui(self):
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.information_row = QtWidgets.QHBoxLayout()
        self.information_row.setObjectName("Information row")
        self.bottom_row = QtWidgets.QHBoxLayout()
        self.bottom_row.setObjectName("Bottom row")
        self.feedback_row = QtWidgets.QHBoxLayout()
        self.feedback_row.setObjectName("Feedback row")
        self.exit_row = QtWidgets.QHBoxLayout()
        self.exit_row.setObjectName("Exit row")

        # Selected file name and location in INFORMATION ROW groupbox
        self.polder_filename = QtWidgets.QLineEdit(self)
        self.polder_filename.setText(self.polder_datasource)
        self.polder_filename.setObjectName("polder legger filename")

        # Assembling INFORMATION ROW groubox
        self.box_info = QtWidgets.QVBoxLayout()
        self.box_info.addWidget(self.polder_filename)  # intro text toevoegen aan box.

        self.groupBox_info = QtWidgets.QGroupBox(self)
        self.groupBox_info.setTitle("Bestanden gekozen:")
        self.groupBox_info.setLayout(self.box_info)  # box toevoegen aan groupbox
        self.information_row.addWidget(self.groupBox_info)

        # Assembling step 1 - snap_points
        self.snap_points_button = QtWidgets.QPushButton(self)
        self.snap_points_button.setObjectName("Snap points")
        self.snap_points_button.clicked.connect(self.execute_snap_points)
        self.snap_points_help_button = QtWidgets.QPushButton(self)
        self.snap_points_help_button.setObjectName("uitleg_stap1")
        self.snap_points_help_button.setText("Uitleg")
        self.snap_points_help_button.clicked.connect(
            lambda: self.show_step_help(
                "Stap 1: snap hydroobjecten",
                "Snapt de uiteinden van de hydroobjecten op elkaar zodat de punten goed aansluiten voor de netwerkanalyse."
            ))
        self.groupBox_snap_points = QtWidgets.QGroupBox(self)
        self.groupBox_snap_points.setTitle("Stap 1: snap hydroobjecten")
        self.box_snap_points = QtWidgets.QHBoxLayout()
        self.box_snap_points.addWidget(self.snap_points_button)
        self.box_snap_points.addWidget(self.snap_points_help_button)
        self.groupBox_snap_points.setLayout(self.box_snap_points)  # box toevoegen aan groupbox

        # Assembling step 2 - redirect_flows
        self.change_flow_direction_checkbox = QtWidgets.QCheckBox("stroomrichting aanpasbaar", self)
        self.change_flow_direction_checkbox.setChecked(True)

        self.step_redirect_flow_button = QtWidgets.QPushButton(self)
        self.step_redirect_flow_button.setObjectName("redirect_flow")
        self.step_redirect_flow_button.clicked.connect(self.execute_redirect_flows)
        self.step_redirect_flow_help_button = QtWidgets.QPushButton(self)
        self.step_redirect_flow_help_button.setObjectName("uitleg_stap2")
        self.step_redirect_flow_help_button.setText("Uitleg")
        self.step_redirect_flow_help_button.clicked.connect(
            lambda: self.show_step_help(
                "Stap 2: kies eindpunten en daarna her-verdeel 3di debiet",
                "Kies eerst zelf de de juiste eindpunten in de kolom 'eindpunt_geselecteerd' van de laag 'debiet'! Eindpunten zijn alle plaatsen waar de afvoer het modelgebied verlaat, zoals gemalen of randvoorwaarden.\n"
                "De leggertool doet een suggestie in 'eindpunt_potentieel'. Als er geen eindpunt wordt geselecteerd wordt de kolom potentieel gebruikt. \n"
                "Het herverdelen dwingt stroming die via niet-primaire watergangen loopt via het primaire watersysteem. Het doel hiervan is om omloop te voorkomen en daarmee te zorgen dat de hele afvoer door de primaire profielen past. \n"
                "In complexe situaties kan de afvoer van niet-primaire wateren een andere primaire route nemen. Bijvoorbeeld bij parallelle routes of meerdere eindpunten. De afvoer op primaire routes kan niet lager worden. In sommige gevallen geeft het herverdelen zonder 'stroomrichting omkeerbaar' betere resultaat. Hiermee kan geëxperimenteerd worden. \n"
                "Controleer de resultaten van het herverdelen met de lagen in de layer group 'herverdelingscheck'. Met de puntenbalansen kunnen ook model of koppelfouten opgespoord worden, pas deze in de input aan en her-verdeel opnieuw. "
            ))

        self.groupBox_step_redirect_flows = QtWidgets.QGroupBox(self)
        self.groupBox_step_redirect_flows.setTitle("stap 2: kies eindpunten en daarna herverdeel 3di debiet")
        self.box_step_redirect_flows = QtWidgets.QVBoxLayout()
        self.box_step_redirect_flows.addWidget(self.change_flow_direction_checkbox)
        self.box_step_redirect_flows.addWidget(self.step_redirect_flow_button)
        self.box_step_redirect_flows.addWidget(self.step_redirect_flow_help_button)
        self.groupBox_step_redirect_flows.setLayout(self.box_step_redirect_flows)  # box toevoegen aan groupbox

        # surge selection:
        self.form_row = QtWidgets.QGridLayout(self)

        # Assembling step 3 row
        self.step3_button = QtWidgets.QPushButton(self)
        self.step3_button.setObjectName("stap3")
        self.step3_button.clicked.connect(self.execute_step3_calculate_variants)
        self.step3_explanation_button = QtWidgets.QPushButton(self)
        self.step3_explanation_button.setObjectName("uitleg_stap3")
        self.step3_explanation_button.setText("Uitleg")
        self.step3_explanation_button.clicked.connect(
            lambda: self.show_step_help(
                "Stap 3: bereken profielvarianten",
                "Bereken alle mogelijke profielvarianten op basis van de gekozen randvoorwaarden. Hier ontstaat de lijst met mogelijke leggerprofielen per object.\n"
                "Let op: als een bestaande 'leggerdatabase' is ingelezen, dan kan het "
                "zo zijn dat door deze actie uit te voeren bestaande varianten worden "
                "overschreven met nieuwe (omdat randvoorwaarde verhang nu anders is."
            ))

        self.groupBox_step3 = QtWidgets.QGroupBox(self)
        self.groupBox_step3.setTitle("Stap 3: bereken profielvarianten")
        self.box_step3 = QtWidgets.QVBoxLayout()
        self.box_step3.addLayout(self.form_row)
        self.box_step3.addWidget(self.step3_button)
        self.box_step3.addWidget(self.step3_explanation_button)
        self.groupBox_step3.setLayout(self.box_step3)  # box toevoegen aan groupbox

        # Assembling step 4 row
        self.step4_button = QtWidgets.QPushButton(self)
        self.step4_button.setObjectName("stap4")
        self.step4_button.setText("Standaard profielen toevoegen")
        self.step4_button.clicked.connect(self.execute_add_standard_profiles)
        self.step4_explanation_button = QtWidgets.QPushButton(self)
        self.step4_explanation_button.setObjectName("uitleg_stap4")
        self.step4_explanation_button.setText("Uitleg")
        self.step4_explanation_button.clicked.connect(
            lambda: self.show_step_help(
                "Stap 4: standaard profielen toevoegen",
                "Voegt standaardprofielen toe uit de vaste profielset. Deze worden nog niet automatisch ingevuld."
            ))

        self.groupBox_step4 = QtWidgets.QGroupBox(self)
        self.groupBox_step4.setTitle("Stap 4: standaard profielen toevoegen")
        self.box_step4 = QtWidgets.QVBoxLayout()
        self.box_step4.addWidget(self.step4_button)
        self.box_step4.addWidget(self.step4_explanation_button)
        self.groupBox_step4.setLayout(self.box_step4)

        # Assembling optional fill step
        self.step_optional_fill_button = QtWidgets.QPushButton(self)
        self.step_optional_fill_button.setObjectName("optioneel invullen")
        self.step_optional_fill_button.setText("OPTIONEEL: Standaardprofielen invullen waar mogelijk")
        self.step_optional_fill_button.clicked.connect(self.execute_fill_standard_profiles)
        self.step_optional_fill_explanation_button = QtWidgets.QPushButton(self)
        self.step_optional_fill_explanation_button.setObjectName("uitleg_optioneel_invullen")
        self.step_optional_fill_explanation_button.setText("Uitleg")
        self.step_optional_fill_explanation_button.clicked.connect(
            lambda: self.show_step_help(
                "OPTIONEEL: Standaardprofielen invullen waar mogelijk",
                "Vult standaardprofielen in waar deze passen en aan de verhangnorm voldoen. Vraag bij de invuller na of zij/hij deze vooraf ingevuld wil hebben."
            ))

        self.groupBox_step_optional_fill = QtWidgets.QGroupBox(self)
        self.groupBox_step_optional_fill.setTitle("OPTIONEEL: Standaardprofielen invullen waar mogelijk")
        self.box_step_optional_fill = QtWidgets.QVBoxLayout()
        self.box_step_optional_fill.addWidget(self.step_optional_fill_button)
        self.box_step_optional_fill.addWidget(self.step_optional_fill_explanation_button)
        self.groupBox_step_optional_fill.setLayout(self.box_step_optional_fill)

        # Assembling step 5 row
        self.step5_button = QtWidgets.QPushButton(self)
        self.step5_button.setObjectName("Stap 5")
        self.step5_button.clicked.connect(self.execute_step5)
        self.step5_explanation_button = QtWidgets.QPushButton(self)
        self.step5_explanation_button.setObjectName("uitleg_stap5")
        self.step5_explanation_button.setText("Uitleg")
        self.step5_explanation_button.clicked.connect(
            lambda: self.show_step_help(
                "Stap 5: bepaal score per variant",
                "Bepaalt de fit van elke profielvariant weergegeven als score aan de hand van gemeten profielen. Let op, pas bij deze stap worden de profielvarianten toegevoegd."
            ))

        self.groupBox_step5 = QtWidgets.QGroupBox(self)
        self.groupBox_step5.setTitle("Stap 5: bepaal score per variant")
        self.box_step5 = QtWidgets.QHBoxLayout()
        self.box_step5.addWidget(self.step5_button)
        self.box_step5.addWidget(self.step5_explanation_button)
        self.groupBox_step5.setLayout(self.box_step5)  # box toevoegen aan groupbox

        # Assembling run all
        self.run_post_process_button = QtWidgets.QPushButton(self)
        self.run_post_process_button.clicked.connect(self.post_process)
        self.post_process_help_button = QtWidgets.QPushButton(self)
        self.post_process_help_button.setText("Uitleg")
        self.post_process_help_button.clicked.connect(
            lambda: self.show_step_help(
                "Totale opstuwing per peilgebied",
                "Berekent de totale opstuwing per peilgebied door alle verhang bij elkaar op te tellen. Voegt voor elke duiker of brug in het traject 1 cm opstuwing toe. Bekijk het resultaat onder 'Opstuwing' in de laag 'Totale opstuwing'. De knop kan opnieuw worden gebruikt om na aanpassingen de totale opstuwing opnieuw te berekenen."
            ))
        self.groupBox_post_process = QtWidgets.QGroupBox(self)
        self.groupBox_post_process.setTitle("Totale opstuwing per peilgebied")
        self.box_run_post_process = QtWidgets.QHBoxLayout()
        self.box_run_post_process.addWidget(self.run_post_process_button)
        self.box_run_post_process.addWidget(self.post_process_help_button)
        self.groupBox_post_process.setLayout(self.box_run_post_process)  # box toevoegen aan groupbox

        # export button
        self.run_export_button = QtWidgets.QPushButton(self)
        self.run_export_button.clicked.connect(self.export_to_gdb)
        self.export_help_button = QtWidgets.QPushButton(self)
        self.export_help_button.setText("Uitleg")
        self.export_help_button.clicked.connect(
            lambda: self.show_step_help(
                "Export legger",
                "Exporteert de hydroobjecten met afvoer, verhang en gekozen profielen voor verdere verwerking of uitwisseling. Deze worden gebruikt voor verwerking in DAMO."
            ))
        self.groupBox_export = QtWidgets.QGroupBox(self)
        self.groupBox_export.setTitle("Export legger")
        self.box_run_export = QtWidgets.QHBoxLayout()
        self.box_run_export.addWidget(self.run_export_button)
        self.box_run_export.addWidget(self.export_help_button)
        self.groupBox_export.setLayout(self.box_run_export)

        # Assembling feedback row
        self.feedbacktext = QtWidgets.QTextEdit(self)
        self.feedbackmessage = "Nog geen berekening uitgevoerd"
        self.feedbacktext.setText(self.feedbackmessage)
        self.feedbacktext.setObjectName("feedback")

        self.feedback_row.addWidget(self.feedbacktext)

        # Assembling exit row
        self.cancel_button = QtWidgets.QPushButton(self)
        self.cancel_button.setObjectName("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.exit_row.addWidget(self.cancel_button)

        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setObjectName("Close")
        self.save_button.clicked.connect(self.save_spatialite)
        self.exit_row.addWidget(self.save_button)

        # Lay-out in elkaar zetten.
        self.verticalLayout.addLayout(self.information_row)
        self.verticalLayout.addWidget(self.groupBox_snap_points)
        self.verticalLayout.addWidget(self.groupBox_step_redirect_flows)
        self.verticalLayout.addWidget(self.groupBox_step3)
        self.verticalLayout.addWidget(self.groupBox_step4)
        self.verticalLayout.addWidget(self.groupBox_step_optional_fill)
        self.verticalLayout.addWidget(self.groupBox_step5)
        self.verticalLayout.addLayout(self.bottom_row)
        self.verticalLayout.addWidget(self.groupBox_post_process)
        self.verticalLayout.addWidget(self.groupBox_export)
        # self.verticalLayout.addWidget(self.groupBox_step3diold)
        self.verticalLayout.addLayout(self.feedback_row)
        self.verticalLayout.addLayout(self.exit_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):

        Dialog.setWindowTitle("Bereken de profielvarianten van de polder")
        self.save_button.setText("Opslaan en sluiten")
        self.step_redirect_flow_button.setText("Kies eerst eindpunten, dan herverdeel debieten")
        self.step3_explanation_button.setText("Uitleg")
        self.step3_button.setText("Bereken alle mogelijke leggerprofielen")
        self.step4_button.setText("Standaard profielen toevoegen")
        self.step5_button.setText("Bereken de fit van de berekende profielen")
        self.snap_points_button.setText("Snap hydroobjecten")
        self.snap_points_help_button.setText("Uitleg")
        self.step_redirect_flow_help_button.setText("Uitleg")
        self.step4_explanation_button.setText("Uitleg")
        self.step_optional_fill_explanation_button.setText("Uitleg")
        self.step5_explanation_button.setText("Uitleg")
        self.post_process_help_button.setText("Uitleg")
        self.export_help_button.setText("Uitleg")

        self.step_optional_fill_button.setText("OPTIONEEL: Standaardprofielen invullen waar mogelijk")
        self.run_post_process_button.setText("Opstuwing op basis van gekozen legger")
        self.run_export_button.setText("Export voor DAMO")

        self.cancel_button.setText("Cancel")
