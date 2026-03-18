@echo off
echo Activating yuga conda environment...
call D:\conda\Scripts\activate.bat yuga
echo.
echo Environment activated. You can now run:
echo   python temp_tests/test_ardhakati.py
echo.
D:\conda\envs\yuga\python.exe %*
