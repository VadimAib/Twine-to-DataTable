@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo Twine to DataTable Conversion Pipeline
echo ============================================================
echo.

REM Check arguments
set "INPUT_FILE=%~1"

if "%INPUT_FILE%"=="" (
    REM Auto-search for .twee file
    for %%f in (*.twee) do (
        set "INPUT_FILE=%%f"
        goto :found
    )
    echo ERROR: No .twee file found
    echo Usage: build_dialogue.bat ^<input.twee^>
    pause
    exit /b 1
)

:found

echo Input file: "%INPUT_FILE%"
echo.

REM Create folders if not exist
if not exist "temp" mkdir temp
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

REM Run pipeline with logging
REM Pass only the logs directory, Python will generate the filename
python scripts\run_pipeline.py "%INPUT_FILE%" "logs"

if errorlevel 1 (
    echo.
    echo ERROR: Pipeline failed. Check logs folder for details.
    pause
    exit /b 1
)

pause