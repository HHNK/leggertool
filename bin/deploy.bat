
@REM deploy plugin to appdata
@REM pb_tool compile

SET PLUGIN_PATH=%appdata%\3Di\QGIS3\profiles\default\python\plugins

xcopy ..\..\leggertool %PLUGIN_PATH%\legger\ /EXCLUDE:exclude_copy.txt/E/q


@REM @REM https://stackoverflow.com/questions/35988863/using-command-line-batch-to-switch-to-focus-on-app
@REM @REM  Open qgis (needs to be empty project. Then press ctrl+r to reload.)
@REM @REM cannot seem to find out how wildcards work. So we use a couple options how the window is called.
@REM %@Try%
@REM   call sendkeys.bat "*Untitled" "^r" 
@REM %@EndTry%
@REM :@Catch
@REM   call sendkeys.bat "Untitled" "^r" 
@REM :@EndCatch
@REM :@Catch
@REM   call sendkeys.bat "QGIS" "^r" 
@REM :@EndCatch