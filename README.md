# Legger

Toolset for assigning 'legger' profiles to channels (hydro objects), based on
the water gradiant calculated with 3di model results

Current version is tested for QGIS version 3.4 and 3.12 and ThreeDiToolbox version 1.13

## Installation

Steps for installation of this QGIS plugin:

1. Make sure the 64-bit version of QGIS 3.4 or higher is installed.

2. Install the 3di QGIS plugin. See installation instruction on:
   https://github.com/nens/threedi-qgis-plugin/wiki

3. The following Python packages are required for the tool, that don't (necessarly) come with every QGIS package:
    - shapely
    - pandas
    - descartes

   If these packages indeed are missing, download the wheels for pandas 0.23.4 and descartes 1.1.0
   Download shapely from the site:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
   Probably you need the version Shapely‑1.xxx.xxx‑cp37‑cp37m‑win_amd64.whl

4. Find the program root of your QGIS installation or OSGeo4w64 installation (Windows Batch file). Start the commandline
   through the OSGeo4W??.bat file.
   Check if everything is working well be testing with the command `pip`. Sometimes you first have to run the
   command `bin\py3_env.bat`

5. For PANDAS and DESCARTES: It might be required to update pip before installing pandas and descartes:
   ```
    python -m pip install --upgrade pip
    pip install wheel
   ```
   Then:
   ```
    python -m pip install path/to/wheel/wheel.whl
   ```
   or navigate to folder where wheel is downloaded to and:
   ```
    python -m pip install wheel.whl
   ```

   A short-cut might be to not work with wheels. It's a bit faster, but be careful with package versions.
   Type in command prompt, and replace between <..> with package name (like pandas), example:
   ```
    python -m pip install <package>
   ```

6. For installing SHAPELY start a command prompt (cmd) and go to the QGIS or OSgeo4w64 root directory (cd xxxx)
   First remove the old version of shapely
   ```
    del apps\python37\lib\site-packages\shapely.pth
   ```
   and install new version
   ```
   bin\python -m pip install --force-reinstall <<path to downloaded whl file>>
   ```

7. Copy the legger tool directory (the directory containing this readme) to the qgis plugin folder
   This folder is situated under:
   <<user directory>>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\legger

   Make sure the name of the folder is called "legger"

## Alternative steps

8. If the plugin doesn't recognize packages (like the just installed pandas and descartes) you can copy the packages to:
   <<user directory>>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\legger\external

   In practice that means you already have a Python installed where these packages can be installed to. Just make sure
   you have Python 3.7.x installed when you decide to take this route.

## development remarks

after adding an icon in the media folder and link in the file resources.qrc, generate a new resources.py with the
command:

```
pyrcc4 -o resources.py resources.qrc
```

```sqlite

SELECT varianten.id                        AS varianten_id,
       varianten.begroeiingsvariant_id     AS varianten_begroeiingsvariant_id,
       varianten.diepte                    AS varianten_diepte,
       varianten.waterbreedte              AS varianten_waterbreedte,
       varianten.bodembreedte              AS varianten_bodembreedte,
       varianten.talud                     AS varianten_talud,
       varianten.hydraulische_diepte       AS varianten_hydraulische_diepte,
       varianten.hydraulische_waterbreedte AS varianten_hydraulische_waterbreedte,
       varianten.hydraulische_bodembreedte AS varianten_hydraulische_bodembreedte,
       varianten.hydraulische_talud        AS varianten_hydraulische_talud,
       varianten.verhang                   AS varianten_verhang,
       varianten.verhang_inlaat            AS varianten_verhang_inlaat,
       varianten.afvoer_leidend            AS varianten_afvoer_leidend,
       varianten.opmerkingen               AS varianten_opmerkingen,
       varianten.hydro_id                  AS varianten_hydro_id,
       varianten.standaard_profiel_code    AS varianten_standaard_profiel_code
FROM varianten
WHERE varianten.hydro_id = 218588
  AND (
    (EXISTS (SELECT 1
             FROM hydroobject
             WHERE hydroobject.id = varianten.hydro_id
               AND hydroobject.begroeiingsvariant_id = varianten.begroeiingsvariant_id))
        OR (EXISTS (SELECT 1
                    FROM hydroobject
                    WHERE hydroobject.id = varianten.hydro_id
                      AND hydroobject.begroeiingsvariant_id IS NULL))
        AND (EXISTS (SELECT 1
                     FROM begroeiingsvariant
                     WHERE varianten.begroeiingsvariant_id = begroeiingsvariant.id
                       AND begroeiingsvariant.is_default = 1)
               ))
  AND varianten.diepte < 0.400001
  AND varianten.diepte > 0.399999
```

```sqlite

SELECT varianten.id                        AS varianten_id,
       varianten.begroeiingsvariant_id     AS varianten_begroeiingsvariant_id,
       varianten.diepte                    AS varianten_diepte,
       varianten.waterbreedte              AS varianten_waterbreedte,
       varianten.bodembreedte              AS varianten_bodembreedte,
       varianten.talud                     AS varianten_talud,
       varianten.hydraulische_diepte       AS varianten_hydraulische_diepte,
       varianten.hydraulische_waterbreedte AS varianten_hydraulische_waterbreedte,
       varianten.hydraulische_bodembreedte AS varianten_hydraulische_bodembreedte,
       varianten.hydraulische_talud        AS varianten_hydraulische_talud,
       varianten.verhang                   AS varianten_verhang,
       varianten.verhang_inlaat            AS varianten_verhang_inlaat,
       varianten.afvoer_leidend            AS varianten_afvoer_leidend,
       varianten.opmerkingen               AS varianten_opmerkingen,
       varianten.hydro_id                  AS varianten_hydro_id,
       varianten.standaard_profiel_code    AS varianten_standaard_profiel_code
FROM varianten
WHERE varianten.hydro_id = 218588
  AND varianten.begroeiingsvariant_id = 1
  AND varianten.diepte < 0.400001
  AND varianten.diepte > 0.399999
```