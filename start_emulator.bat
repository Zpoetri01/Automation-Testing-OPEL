@echo off
rem ============================================================
rem  Start Emulator OPEL (AVD: OPEL) - JENDELA TERLIHAT + AMAN
rem  Flag AMAN supaya tidak crash / putus di tengah run:
rem    -gpu swiftshader_indirect  -> render software (hindari crash driver GPU)
rem    -no-snapshot-load          -> jangan load snapshot (hindari snapshot korup)
rem    -no-boot-anim              -> boot lebih cepat
rem    -memory 3072               -> RAM emulator 3GB
rem    TANPA -qt-hide-window      -> jendela emulator TERLIHAT
rem  CATATAN: kalau emulator lama (jendela tersembunyi dari Android
rem  Studio) masih jalan, pakai restart_emulator.bat.
rem ============================================================
setlocal
set "SDK=%LOCALAPPDATA%\Android\Sdk"
set "ADB=%SDK%\platform-tools\adb.exe"
set "EMU=%SDK%\emulator\emulator.exe"

"%ADB%" devices | findstr /r "emulator-[0-9][0-9]*\s*device" >nul 2>&1
if %errorlevel%==0 (
    echo Emulator SUDAH jalan:
    "%ADB%" devices
    echo.
    echo Kalau jendelanya tidak terlihat, jalankan restart_emulator.bat
    echo (emulator lama berjalan dalam mode tersembunyi).
) else (
    echo Menjalankan emulator OPEL dengan flag aman...
    start "OPEL Emulator" /D "%TEMP%" "%EMU%" -avd OPEL -gpu swiftshader_indirect -no-snapshot-load -no-boot-anim -memory 3072 -cores 4
    echo Menunggu boot selesai (biasanya 3-5 menit)...
    :waitboot
    timeout /t 10 /nobreak >nul
    for /f "delims=" %%b in ('"%ADB%" -s emulator-5554 shell getprop sys.boot_completed 2^>nul') do set BOOT=%%b
    if not "%BOOT%"=="1" goto waitboot
    echo Boot selesai. Menyalakan layar & menonaktifkan animasi (anti putus saat testing)...
    "%ADB%" -s emulator-5554 shell svc power stayon true
    "%ADB%" -s emulator-5554 shell settings put global window_animation_scale 0
    "%ADB%" -s emulator-5554 shell settings put global transition_animation_scale 0
    "%ADB%" -s emulator-5554 shell settings put global animator_duration_scale 0
    "%ADB%" -s emulator-5554 shell input keyevent 82
    echo.
    echo EMULATOR SIAP. Jendela emulator sudah terlihat di layar.
)
pause
