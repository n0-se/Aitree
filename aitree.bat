@echo off
title AI Context Generator
echo.

:: %~dp0 dynamically grabs the path to this bat file (C:\_usr\data\apps\aitree\)
:: We wrap it in quotes just in case there are ever spaces in the path
:: %~dp0 finds the script path. %* passes arguments (like 'init') to Python.
python3 "%~dp0aitree.py" %*

echo.
echo.