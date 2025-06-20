import os
import subprocess

from qgis._core import Qgis
from qgis.core import QgsMessageLog

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog

if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )
    os.environ["PROJ_LIB"] = "/Applications/QGIS-LTR2.app/Contents/Resources/proj"
    os.environ["GDAL_DATA"] = "/Applications/QGIS-LTR2.app/Contents/Resources/gdal"


from legger.sql_models.legger_views import create_legger_view_export_damo
from legger.utils.spatialite import load_spatialite
from legger.utils.user_message import messagebar_message


def export_sqlite_view_to_geopackage(sqlite_path, parent=None):
    """
    Export een gespecificeerde view uit een SQLite database naar een GeoPackage,
    waarbij de gebruiker het output bestand kan kiezen via een dialoog.
    """
    # 1. Controleer of de SQLite database bestaat

    session = load_spatialite(sqlite_path)
    create_legger_view_export_damo(session)

    view_name = 'hydroobj_sel_export_damo'

    settings = QSettings('leggertool', 'filepaths')
    try:
        init_path = settings.value('last_used_damo_export_path', type=str)
    except:
        init_path = os.path.expanduser("~")  # get path to respectively "user" folder

    output_layer = 'resultaat_legger'

    output_gpkg_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Selecteer of maak het output GeoPackage bestand",
        init_path,
        "GeoPackage Files (*.gpkg)"
    )

    if output_gpkg_path:
        settings.setValue('last_used_damo_export_path',
                          os.path.dirname(output_gpkg_path))
    else:
        QgsMessageLog.logMessage(
            "Gebruiker heeft het output GeoPackage bestand niet geselecteerd.",
            "Export SQLite View",
            Qgis.Info)
        return

    if not output_gpkg_path.lower().endswith('.gpkg'):
        output_gpkg_path += '.gpkg'

    # dump with GDAL ogr2ogr
    # ogr2ogr
    if os.path.exists(output_gpkg_path):
        # popup if sure
        if QgsMessageLog.confirmWarning("Bestand bestaat al, bestaande vervangen?"):
            os.remove(output_gpkg_path)
        else:
            QgsMessageLog.logMessage("Export afgebroken.", Qgis.Warning)
            return

    try:
        geometry_type = "LINESTRING"  # or "POINT", "LINESTRING", etc.
        ogr_exe = os.path.abspath(
            os.path.join(sys.executable, os.pardir, os.pardir, "bin", "ogr2ogr.exe")
        )
        # if windows, use ogr2ogr.exe else use ogr2ogr
        if not sys.platform.startswith('win'):
            ogr_exe = "ogr2ogr"
        command = (f'"{ogr_exe}" '
                  f'-f "GPKG" -nln {output_layer} '
                   f'-nlt {geometry_type} '
                  f'"{output_gpkg_path}" '
                  f'"{sqlite_path}" '
                  f'-sql "SELECT * FROM {view_name}" ')  # -lco ENCODING=UTF-8

        subprocess.run(command, check=True)
        QgsMessageLog.logMessage(f"View '{view_name}' succesvol geëxporteerd naar: {output_gpkg_path}",
                                 "Export SQLite View", Qgis.Info)
        messagebar_message(
            "Export SQLite View", f"View '{view_name}' succesvol geëxporteerd naar: {output_gpkg_path}", 3, 10)
    except subprocess.CalledProcessError as e:
            print(f"Fout bij het exporteren van de view '{view_name}': {output_gpkg_path}")
            print(e)
            QgsMessageLog.logMessage(f"Fout bij het exporteren van de view '{view_name}': {output_gpkg_path}",
                                     "Export SQLite View", Qgis.Critical)
            messagebar_message(
                "Export SQLite View", f"Fout bij het exporteren van de view '{view_name}': {output_gpkg_path}", 2, 20)



if __name__ == "__main__":
    import sys
    from qgis.PyQt.QtWidgets import QApplication

    app = QApplication(sys.argv)

    sqlite_path = r'/Users/bastiaanroos/Documents/testdata/leggertool/legger_Drieban.sqlite'

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
