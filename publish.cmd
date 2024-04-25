:: Publish this package to PyPI.
::
@echo off
set "dir=%~dp0."
set "build=%dir%\build"
set "dist=%dir%\dist"

python -m pip install --upgrade build twine

:: Purge previously built files to prevent deleted files being included.
if exist "%build%" rmdir /s /q "%build%"
if exist "%dir%\sts_lib.egg-info" rmdir /s /q "%dir%\sts_lib.egg-info"

python -m build --sdist --wheel "%dir%"
python -m twine upload --skip-existing "%dist%\*"
