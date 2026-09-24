@echo off
rem ============================================================
rem  Restart Emulator OPEL dengan JENDELA TERLIHAT
rem  Dipakai kalau emulator sedang jalan tapi jendelanya TIDAK
rem  muncul (biasanya di-start Android Studio mode tersembunyi
rem  dengan flag -qt-hide-window).
rem ============================================================
setlocal
set "SDK=%LOCALAPPDATA%\Android\Sdk"
set "ADB=%SDK%\platform-tools\adb.exe"
set "EMU=%SDK%\emulator\emulator.exe"

echo Menghentikan emulator lama...
"%ADB%" emu kill >nul 2>&1
timeout /t 5 /nobreak >nul
taskkill /F /IM emulator.exe >nul 2>&1
taskkill /F /IM qemu-system-x86_64.exe >nul 2>&1
timeout /t 5 /nobreak >nul

echo Menjalankan emulator OPEL (jendela terlihat)...
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
echo EMULATOR SIAP DAN TERLIHAT.
pause
