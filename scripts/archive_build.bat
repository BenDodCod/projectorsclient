@echo off
REM ============================================================================
REM Build Archiving Script
REM
REM This script:
REM   1. Creates timestamped archive directory
REM   2. Copies executable, logs, and manifest to archive
REM   3. Generates SHA256 checksum
REM   4. Maintains last 10 builds (deletes older ones)
REM
REM Usage:
REM   call scripts\archive_build.bat
REM
REM Expected to be called from project root after successful build
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set ARCHIVE_ROOT=archive\builds
set MAX_ARCHIVES=10
set EXE_NAME=ProjectorControl.exe
set DIST_DIR=dist
set BUILD_DIR=build

REM Generate timestamp for archive folder (YYYYMMDD_HHMMSS format)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM Archive directory path
set ARCHIVE_DIR=%ARCHIVE_ROOT%\%TIMESTAMP%

echo.
echo ========================================
echo  Archiving Build
echo ========================================
echo.

REM Check if executable exists
if not exist "%DIST_DIR%\%EXE_NAME%" (
    echo ERROR: Executable not found at %DIST_DIR%\%EXE_NAME%
    echo Cannot archive build.
    exit /b 1
)

REM Create archive directory
echo Creating archive directory: %ARCHIVE_DIR%
if not exist "%ARCHIVE_ROOT%" mkdir "%ARCHIVE_ROOT%"
if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"

REM Copy executable
echo Copying executable...
copy "%DIST_DIR%\%EXE_NAME%" "%ARCHIVE_DIR%\" >nul
if errorlevel 1 (
    echo WARNING: Failed to copy executable
) else (
    echo   - %EXE_NAME%
)

REM Copy build manifest (if exists)
if exist "build_manifest.json" (
    echo Copying build manifest...
    copy "build_manifest.json" "%ARCHIVE_DIR%\" >nul
    if errorlevel 1 (
        echo WARNING: Failed to copy build manifest
    ) else (
        echo   - build_manifest.json
    )
)

REM Copy smoke test report (if exists)
if exist "smoke_test_report.txt" (
    echo Copying smoke test report...
    copy "smoke_test_report.txt" "%ARCHIVE_DIR%\" >nul
    if errorlevel 1 (
        echo WARNING: Failed to copy smoke test report
    ) else (
        echo   - smoke_test_report.txt
    )
)

REM Copy PyInstaller warnings file (if exists)
if exist "%BUILD_DIR%\ProjectorControl\warn-ProjectorControl.txt" (
    echo Copying build warnings...
    copy "%BUILD_DIR%\ProjectorControl\warn-ProjectorControl.txt" "%ARCHIVE_DIR%\build_warnings.txt" >nul
    if errorlevel 1 (
        echo WARNING: Failed to copy build warnings
    ) else (
        echo   - build_warnings.txt
    )
)

REM Copy build analysis (if exists)
if exist "docs\build_analysis.md" (
    echo Copying build analysis...
    copy "docs\build_analysis.md" "%ARCHIVE_DIR%\" >nul
    if errorlevel 1 (
        echo WARNING: Failed to copy build analysis
    ) else (
        echo   - build_analysis.md
    )
)

REM Generate SHA256 checksum
echo Generating checksum...
certutil -hashfile "%ARCHIVE_DIR%\%EXE_NAME%" SHA256 > "%ARCHIVE_DIR%\checksum.txt" 2>nul
if errorlevel 1 (
    echo WARNING: Failed to generate checksum
) else (
    REM Extract just the hash from certutil output
    for /f "skip=1 tokens=1" %%a in (%ARCHIVE_DIR%\checksum.txt) do (
        echo %%a > "%ARCHIVE_DIR%\checksum.txt"
        goto :done_checksum
    )
    :done_checksum
    echo   - checksum.txt
)

REM Create archive info file
echo Creating archive info...
(
    echo Build Archive: %TIMESTAMP%
    echo ========================================
    echo.
    echo Date: %date% %time%
    echo Executable: %EXE_NAME%
    echo.
    echo Files in this archive:
    dir /b "%ARCHIVE_DIR%"
    echo.
    echo To restore this build:
    echo   1. Copy %EXE_NAME% to desired location
    echo   2. Review build_manifest.json for version info
    echo   3. Check smoke_test_report.txt for validation results
) > "%ARCHIVE_DIR%\README.txt"

echo   - README.txt
echo.

REM Count existing archives
set ARCHIVE_COUNT=0
for /d %%d in ("%ARCHIVE_ROOT%\*") do (
    set /a ARCHIVE_COUNT+=1
)

echo Total archives: %ARCHIVE_COUNT%

REM Clean up old archives if we exceed MAX_ARCHIVES
if %ARCHIVE_COUNT% gtr %MAX_ARCHIVES% (
    echo Cleaning up old archives (keeping last %MAX_ARCHIVES%)...

    REM Get list of directories sorted by name (oldest first)
    set DELETE_COUNT=0
    set /a KEEP_COUNT=%ARCHIVE_COUNT% - %MAX_ARCHIVES%

    for /f "skip=%MAX_ARCHIVES% delims=" %%d in ('dir /b /o:n "%ARCHIVE_ROOT%"') do (
        set /a DELETE_COUNT+=1
        if !DELETE_COUNT! leq %KEEP_COUNT% (
            echo   Deleting: %%d
            rd /s /q "%ARCHIVE_ROOT%\%%d" 2>nul
        )
    )
)

echo.
echo ========================================
echo  Archive Complete
echo ========================================
echo.
echo Archive location: %ARCHIVE_DIR%
echo.

endlocal
exit /b 0
