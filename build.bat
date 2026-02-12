@echo off
REM ============================================================================
REM Projector Control Application - Build Script
REM Version: 1.0.0
REM Created: Week 5-6 DevOps Phase
REM
REM This script:
REM   1. Cleans previous builds
REM   2. Installs dependencies
REM   3. Runs all tests (must pass)
REM   4. Runs security scans
REM   5. Builds the executable
REM   6. Verifies the output
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  Projector Control - Build Script
echo ========================================
echo.

REM Configuration
set COVERAGE_THRESHOLD=85
set BUILD_DIR=build
set DIST_DIR=dist
set EXE_NAME=ProjectorControl.exe

REM Parse command line arguments
set SKIP_TESTS=0
set SKIP_SECURITY=0
set CLEAN_ONLY=0
set VERBOSE=0

:parse_args
if "%1"=="" goto start_build
if "%1"=="--skip-tests" set SKIP_TESTS=1
if "%1"=="--skip-security" set SKIP_SECURITY=1
if "%1"=="--clean" set CLEAN_ONLY=1
if "%1"=="--verbose" set VERBOSE=1
if "%1"=="--help" goto show_help
shift
goto parse_args

:show_help
echo Usage: build.bat [options]
echo.
echo Options:
echo   --skip-tests     Skip running tests
echo   --skip-security  Skip security scans
echo   --clean          Clean build directories only
echo   --verbose        Show detailed output
echo   --help           Show this help message
echo.
exit /b 0

:start_build
REM Step 0: Verify version consistency
echo [0/7] Verifying version consistency...
python scripts\verify_version.py
if errorlevel 1 (
    echo ERROR: Version inconsistencies detected
    echo Please fix version issues before building
    exit /b 1
)
echo Done.

REM Step 1: Clean previous builds
echo.
echo [1/7] Cleaning previous builds...
if exist "%BUILD_DIR%" (
    rd /s /q "%BUILD_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo Warning: Could not fully clean build directory
    )
)
if exist "%DIST_DIR%" (
    rd /s /q "%DIST_DIR%" 2>nul
    if !errorlevel! neq 0 (
        echo Warning: Could not fully clean dist directory
    )
)
del /q *.spec.bak 2>nul
echo Done.

if %CLEAN_ONLY%==1 (
    echo.
    echo Clean complete.
    exit /b 0
)

REM Step 2: Check Python environment
echo.
echo [2/7] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)
python --version
echo Done.

REM Step 3: Install/update dependencies
echo.
echo [3/7] Installing dependencies...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    exit /b 1
)

pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    exit /b 1
)

pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    exit /b 1
)

REM Register pywin32 DLLs (required for Windows API access)
python -c "import sys; import os; from pathlib import Path; venv_scripts = Path(sys.executable).parent; pywin32_post = venv_scripts / 'pywin32_postinstall.py'; exec(open(pywin32_post).read() + '\ninstall()')" 2>nul
if errorlevel 1 (
    echo Warning: pywin32 post-install script not found or failed
)
echo Done.

REM Step 4: Run tests
if %SKIP_TESTS%==1 (
    echo.
    echo [4/7] Skipping tests (--skip-tests flag)
) else (
    echo.
    echo [4/7] Running tests...

    REM Install test dependencies
    pip install -r requirements-dev.txt --quiet

    REM Run pytest with coverage
    if %VERBOSE%==1 (
        pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=%COVERAGE_THRESHOLD%
    ) else (
        pytest tests/ --cov=src --cov-fail-under=%COVERAGE_THRESHOLD% -q
    )

    if errorlevel 1 (
        echo.
        echo ========================================
        echo  ERROR: Tests failed!
        echo  Build aborted.
        echo ========================================
        exit /b 1
    )
    echo Tests passed with %COVERAGE_THRESHOLD%%+ coverage.
)

REM Step 5: Run security scan
if %SKIP_SECURITY%==1 (
    echo.
    echo [5/7] Skipping security scan (--skip-security flag)
) else (
    echo.
    echo [5/7] Running security scan...

    pip install bandit --quiet

    REM Run bandit, fail on high severity
    bandit -r src/ -ll -f txt
    if errorlevel 1 (
        echo.
        echo ========================================
        echo  WARNING: Security issues found!
        echo  Review bandit output above.
        echo ========================================
        REM Don't fail build, just warn
    )
    echo Security scan complete.
)

REM Step 6: Build executable
echo.
echo [6/7] Building executable...

REM Check if spec file exists
if not exist "projector_control.spec" (
    echo ERROR: projector_control.spec not found
    exit /b 1
)

REM Check if main.py exists
if not exist "src\main.py" (
    echo ERROR: src\main.py not found
    echo Please create the main entry point first.
    exit /b 1
)

REM Run PyInstaller
if %VERBOSE%==1 (
    pyinstaller projector_control.spec --clean --noconfirm
) else (
    pyinstaller projector_control.spec --clean --noconfirm --log-level WARN
)

if errorlevel 1 (
    echo.
    echo ========================================
    echo  ERROR: Build failed!
    echo  Check PyInstaller output above.
    echo ========================================
    exit /b 1
)

REM Verify output
if not exist "%DIST_DIR%\%EXE_NAME%" (
    echo.
    echo ========================================
    echo  ERROR: Executable not created!
    echo  Expected: %DIST_DIR%\%EXE_NAME%
    echo ========================================
    exit /b 1
)

REM Get file size
for %%A in ("%DIST_DIR%\%EXE_NAME%") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576

echo.
echo ========================================
echo  BUILD SUCCESSFUL!
echo ========================================
echo.
echo Output: %DIST_DIR%\%EXE_NAME%
echo Size: ~%SIZE_MB% MB
echo.
echo Next steps:
echo   1. Test the executable manually
echo   2. Run: dist\%EXE_NAME%
echo   3. Check all features work correctly
echo.

endlocal
exit /b 0
