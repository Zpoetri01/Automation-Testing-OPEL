@echo off
rem ============================================================
rem  RUN TESTS OPEL - one click:
rem    1. cek/pastikan emulator jalan (jika belum, start otomatis)
rem    2. cek/start Appium server
rem    3. jalankan pytest END-TO-END (SATU KALI dari login sampai
rem       logout, TIDAK login ulang / testing berulang)
rem    4. buka laporan HTML
rem  Jalankan: run_tests.bat            (alur e2e penuh, sekali jalan)
rem            run_tests.bat 04         (hanya test_04, dst - debugging)
rem ============================================================
setlocal
cd /d "%~dp0"
set "SDK=%LOCALAPPDATA%\Android\Sdk"
set "ADB=%SDK%\platform-tools\adb.exe"
set "EMU=%SDK%\emulator\emulator.exe"

echo === [1/3] Cek emulator ===
"%ADB%" devices | findstr /r "emulator-[0-9][0-9]*\s*device" >nul 2>&1
if %errorlevel%==0 (
    echo Emulator sudah jalan.
) else (
    echo Menjalankan emulator OPEL...
    start "OPEL Emulator" /D "%TEMP%" "%EMU%" -avd OPEL -gpu swiftshader_indirect -no-snapshot-load -no-boot-anim -memory 3072 -cores 4
    echo Menunggu boot selesai...
    :waitboot
    timeout /t 10 /nobreak >nul
    for /f "delims=" %%b in ('"%ADB%" -s emulator-5554 shell getprop sys.boot_completed 2^>nul') do set BOOT=%%b
    if not "%BOOT%"=="1" goto waitboot
    "%ADB%" -s emulator-5554 shell svc power stayon true
    "%ADB%" -s emulator-5554 shell settings put global window_animation_scale 0
    "%ADB%" -s emulator-5554 shell settings put global transition_animation_scale 0
    "%ADB%" -s emulator-5554 shell settings put global animator_duration_scale 0
    "%ADB%" -s emulator-5554 shell input keyevent 82
    echo Boot selesai.
)

echo === [2/3] Cek Appium server ===
set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
set "ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk"
curl -s -o nul http://127.0.0.1:4723/status
if %errorlevel%==0 (
    echo Appium sudah jalan.
) else (
    echo Menjalankan Appium di window baru... BIARKAN TERBUKA selama testing.
    start "Appium Server - OPEL" cmd /k "set ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk&& set ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk&& appium"
    echo Menunggu Appium siap...
    :waitappium
    timeout /t 3 /nobreak >nul
    curl -s -o nul http://127.0.0.1:4723/status
    if not %errorlevel%==0 goto waitappium
    echo Appium siap.
)

echo === [3/3] Jalankan pytest ===
if "%1"=="" (
    rem Skenario user: testing dijalankan SEKALI saja dari login sampai
    rem logout (test e2e penuh), jangan login ulang & mentesting ulang.
    pytest tests/test_e2e_full_flow.py -v --html=report.html --self-contained-html
) else (
    pytest tests/test_%1_*.py -v --html=report.html --self-contained-html
)
echo.
echo Selesai. Laporan: report.html
start report.html
pause
