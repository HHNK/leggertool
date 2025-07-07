import os

from qgis._core import Qgis, QgsVectorLayer, QgsDataSourceUri, QgsProject, QgsFields, QgsField, QgsWkbTypes, QgsFeature
from qgis.core import QgsVectorFileWriter, QgsMessageLog

from PyQt5.QtCore import QSettings, QVariant

from PyQt5.QtWidgets import QFileDialog

if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    os.environ["PROJ_LIB"] = "/Applications/QGIS-LTR2.app/Contents/Resources/proj"
    os.environ["GDAL_DATA"] = "/Applications/QGIS-LTR2.app/Contents/Resources/gdal"


from legger.utils.spatialite import load_spatialite
from legger.utils.user_message import messagebar_message


def export_sqlite_view_to_geopackage(sqlite_path, parent=None):
    """
    Export een gespecificeerde view uit een SQLite database naar een GeoPackage,
    waarbij de gebruiker het output bestand kan kiezen via een dialoog.
    """
    # 1. Controleer of de SQLite database bestaat

    # make sure (last version) of view exists
    session = load_spatialite(sqlite_path)

    view_name = 'hydroobj_sel_export_damo'

    settings = QSettings('leggertool', 'filepaths')
    try:
        init_path = settings.value('last_used_damo_export_path', type=str)
    except:
        init_path = os.path.expanduser("~")  # get path to respectively "user" folder

    output_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Selecteer of maak het output GeoPackage bestand",
        init_path,
        "GeoPackage Files (*.gpkg)"
    )

    if output_path:
        settings.setValue('last_used_damo_export_path',
                          os.path.dirname(output_path))
    else:
        QgsMessageLog.logMessage("Gebruiker heeft het output GeoPackage bestand niet geselecteerd.", "Export SQLite View", Qgis.Info)
        return

    if not output_path.lower().endswith('.gpkg'):
        output_path += '.gpkg'

    if os.path.exists(output_path):
        os.remove(output_path)

    # 4. Stel de URI samen om de view in QGIS te laden als een vectorlaag
    uri = QgsDataSourceUri()
    uri.setDatabase(sqlite_path.replace('\\', '/'))
    # view so use select
    uri.setDataSource('', '(SELECT * FROM {})'.format(view_name), 'GEOMETRY')

    # uri = f"file:'{sqlite_path}'?query=(SELECT * FROM {view_name})"
    # uri += "&field=geometry&crs=EPSG:28992" # Pas CRS indien nodig aan

    # 5. Maak een tijdelijke vectorlaag aan vanuit de URI
    print(f"URI: {uri.uri()}")
    vlayer = QgsVectorLayer(uri.uri(), view_name, "spatialite")

    if not vlayer.isValid():
        print(f"Fout bij het laden van de view '{view_name}'. Controleer de view.")
        QgsMessageLog.logMessage(f"Fout bij het laden van de view '{view_name}'. Controleer de view.", "Export SQLite View", Qgis.Critical)
        messagebar_message("Export SQLite View", f"Fout bij het laden van de view '{view_name}'. Controleer de view.",  2, 20)
        return

    # 6. Stel de opties in voor het wegschrijven naar GeoPackage
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.crs = vlayer.crs() # Behoud het CRS van de virtuele laag
    options.writeBBox = False

    # 6d stel in welk type de velden worden
    double_fieds = [ 
                    ["streefpeil",                   6],
                    ["zomerpeil",                    6],
                    ["waterbreedte_BGT",             8],
                    ["WS_AANVOERDEBIET",             8],
                    ["WS_AFVOERDEBIET",              8],
                    ["WS_BODEMBREEDTE",              6],
                    ["geselecteerde_hydraulische_diepte",         6],
                    ["geselecteerde_hydraulische_waterbreedte",   6],
                    ["WS_TALUD_LINKS",               6],
                    ["WS_TALUD_RECHTS",              6],
                    ["inlaatverhang",                6],
                    ["afvoerverhang",                6],
                    ["WS_BODEMHOOGTE",               6],
                    ["WS_DIEPTE_DROGE_BEDDING",      6],
                    ["geselecteerde_bodembreedte_onderhoud",      6],
                    ["geselecteerde_diepte_onderhoud",      6],
                    ]
    # 1. Define your desired fields and types
    fields = QgsFields()
    fields.append(QgsField("CODE", QVariant.String,len=50))
    fields.append(QgsField("CATEGORIE", QVariant.Int,len=3))
    fields.append(QgsField("grondsoort", QVariant.String))
    for field in double_fieds:
        fields.append(QgsField(field[0], QVariant.Double,prec=field[1]))
    fields.append(QgsField("WS_MAX_BEGROEIING", QVariant.Int,len=5))
    fields.append(QgsField("opmerkingen", QVariant.String))
    

    # 2. Create a memory layer with these fields
    mem_layer = QgsVectorLayer(f"{QgsWkbTypes.displayString(vlayer.wkbType())}?crs={vlayer.crs().authid()}", "temp", "memory")
    mem_layer.dataProvider().addAttributes(fields)
    mem_layer.updateFields()

    # 3. Copy features from the original layer, mapping attributes as needed
    for feat in vlayer.getFeatures():
        new_feat = QgsFeature(fields)
        # Map attributes here, e.g.:
        new_feat.setAttribute("CODE", feat["CODE"])
        new_feat.setAttribute("CATEGORIE", feat["CATEGORIE"])
        new_feat.setAttribute("grondsoort", feat["grondsoort"])
        for field in double_fieds:
            new_feat.setAttribute(field[0], feat[field[0]])
        new_feat.setAttribute("WS_MAX_BEGROEIING", feat["WS_MAX_BEGROEIING"])
        new_feat.setAttribute("opmerkingen", feat["opmerkingen"])
        new_feat.setGeometry(feat.geometry())
        mem_layer.dataProvider().addFeature(new_feat)

    mem_layer.updateExtents()

    # 7. Voer de export uit
    write_result, error_message, new_file, new_layer = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, output_path, QgsProject.instance().transformContext(), options)

    print(f"output writeAsVectorFormatV3: {write_result} {error_message}")
    if write_result == QgsVectorFileWriter.NoError:
        QgsMessageLog.logMessage(f"View '{view_name}' succesvol geëxporteerd naar: {output_path}", "Export SQLite View", Qgis.Info)
        messagebar_message("Export SQLite View", f"View '{view_name}' succesvol geëxporteerd naar: {output_path}", 3, 10)
    else:
        QgsMessageLog.logMessage(f"Fout bij het exporteren van de view '{view_name}': {error_message}", "Export SQLite View", Qgis.Critical)
        messagebar_message("Export SQLite View", f"Fout bij het exporteren van de view '{view_name}': {error_message}", 2, 20)


if __name__ == "__main__":
    import sys
    from qgis.PyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    sqlite_path = r'/Users/bastiaanroos/Documents/testdata/leggertool/Westerkogge Standaard profiel vs gegenereerd/Westerkogge_check_verhang_verschil.sqlite'

    # Define a simple callback
    def my_callback(item, variant):
        print(f"Callback executed for item {item.hydrovak['hydro_id']} with variant {variant.id}")

    # Controleer of de SQLite database bestaat
    if not os.path.exists(sqlite_path):
        QgsMessageLog.logMessage(f"SQLite database niet gevonden: {sqlite_path}", "Export SQLite View", Qgis.Critical)
    else:
        # Start het exportproces
        export_sqlite_view_to_geopackage(sqlite_path)

    sys.exit(app.exec_())
