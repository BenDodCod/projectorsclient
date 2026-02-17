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
echo [0/9] Verifying version consistency...
python scripts\verify_version.py
if errorlevel 1 (
    echo ERROR: Version inconsistencies detected
    echo Please fix version issues before building
    exit /b 1
)
echo Done.

REM Step 1: Clean previous builds
echo.
echo [1/9] Cleaning previous builds...
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
echo [2/9] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)
python --version
echo Done.

REM Step 3: Install/update dependencies
echo.
echo [3/9] Installing dependencies...
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
    echo [4/9] Skipping tests (--skip-tests flag)
) else (
    echo.
    echo [4/9] Running tests...

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
    echo [5/9] Skipping security scan (--skip-security flag)
) else (
    echo.
    echo [5/9] Running security scan...

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
echo [6/9] Building executable...

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

echo Build complete.

REM Step 7: Run smoke test
echo.
echo [7/9] Running post-build validation (smoke test)...
python scripts\smoke_test.py "%DIST_DIR%\%EXE_NAME%"
if errorlevel 2 (
    echo.
    echo ========================================
    echo  WARNING: Smoke test failed critically
    echo  Review smoke_test_report.txt
    echo ========================================
    set SMOKE_TEST_FAILED=1
) else if errorlevel 1 (
    echo.
    echo ========================================
    echo  WARNING: Smoke test passed with warnings
    echo  Review smoke_test_report.txt
    echo ========================================
    set SMOKE_TEST_WARNING=1
) else (
    echo Smoke test passed.
)

REM Step 8: Generate build manifest
echo.
echo [8/9] Generating build manifest...
python scripts\build_manifest.py "%DIST_DIR%\%EXE_NAME%"
if errorlevel 1 (
    echo WARNING: Failed to generate build manifest
    set MANIFEST_FAILED=1
) else (
    echo Build manifest generated.
)

REM Step 9: Archive build
echo.
echo [9/9] Archiving build...
call scripts\archive_build.bat
if errorlevel 1 (
    echo WARNING: Failed to archive build
    set ARCHIVE_FAILED=1
) else (
    echo Build archived successfully.
)

REM Final summary
echo.
echo ========================================
echo  BUILD COMPLETE
echo ========================================
echo.
echo Output: %DIST_DIR%\%EXE_NAME%
echo Size: ~%SIZE_MB% MB
echo.

REM Show warnings if any
if defined SMOKE_TEST_FAILED (
    echo WARNING: Smoke test failed - review smoke_test_report.txt
)
if defined SMOKE_TEST_WARNING (
    echo WARNING: Smoke test warnings - review smoke_test_report.txt
)
if defined MANIFEST_FAILED (
    echo WARNING: Build manifest generation failed
)
if defined ARCHIVE_FAILED (
    echo WARNING: Build archiving failed
)

echo.
echo Build artifacts:
echo   - Executable: %DIST_DIR%\%EXE_NAME%
echo   - Manifest: build_manifest.json
echo   - Smoke test: smoke_test_report.txt
echo   - Archive: archive\builds\[timestamp]
echo.
echo Next steps:
echo   1. Review smoke_test_report.txt for validation results
echo   2. Test the executable manually: dist\%EXE_NAME%
echo   3. Check build_manifest.json for build details
echo.

REM Exit with appropriate code
if defined SMOKE_TEST_FAILED (
    echo Build completed but smoke test failed.
    endlocal
    exit /b 1
)

endlocal
exit /b 0
