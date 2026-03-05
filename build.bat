@echo off
chcp 65001 >NUL
title ZapretTester Build
echo ============================================================
echo   ZapretTester - Build Standalone EXE
echo ============================================================
echo.

:: Check Python
python --version >NUL 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python from https://python.org and add to PATH.
    echo.
    pause
    exit /b 1
)
echo [OK] Python found:
python --version
echo.

:: Install dependencies
echo [1/3] Installing dependencies...
echo.
pip install PyQt6 pyinstaller psutil requests ping3
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.

:: Check required files
echo [2/3] Checking files...
if not exist "zapret_tester.py" (
    echo ERROR: zapret_tester.py not found!
    echo Make sure you run this bat from the same folder as zapret_tester.py
    pause
    exit /b 1
)
if not exist "zapret_tester.spec" (
    echo ERROR: zapret_tester.spec not found!
    pause
    exit /b 1
)
if not exist "1.ico"   echo WARNING: 1.ico not found
if not exist "on.png"  echo WARNING: on.png not found
if not exist "off.png" echo WARNING: off.png not found
echo.

:: Build
echo [3/3] Building EXE...
echo.
pyinstaller zapret_tester.spec --clean --noconfirm
echo.

:: Result
if exist "dist\ZapretTester.exe" (
    echo ============================================================
    echo   SUCCESS: dist\ZapretTester.exe
    echo.
    echo   Copy ZapretTester.exe somewhere and place a "zapret"
    echo   folder next to it with your zapret discord youtube files.
    echo ============================================================
) else (
    echo ============================================================
    echo   BUILD FAILED - see errors above
    echo ============================================================
)
echo.
pause
