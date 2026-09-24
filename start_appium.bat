@echo off
rem ============================================
rem  Start Appium Server untuk testing OPEL
rem  Cek dulu apakah Appium sudah jalan di port 4723;
rem  kalau belum, jalankan. Biarkan window ini TERBUKA
rem  selama testing.
rem ============================================
setlocal
set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
set "ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk"
title Appium Server - OPEL Testing

curl -s -o nul http://127.0.0.1:4723/status
if %errorlevel%==0 (
    echo Appium SUDAH jalan di http://127.0.0.1:4723 - tidak perlu start lagi.
    echo Cek status: buka http://127.0.0.1:4723/status di browser.
) else (
    echo Menjalankan Appium... biarkan window ini terbuka selama testing.
    echo Tutup window ini untuk menghentikan Appium.
    appium
)
pause
