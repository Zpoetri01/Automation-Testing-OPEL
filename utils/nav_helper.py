"""
Helper navigasi supaya tiap file test bisa dijalankan berdiri sendiri
(tidak wajib urut) maupun sebagai bagian dari end-to-end suite.
"""

import time
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.apps_page import AppsPage
from config import GOOGLE_EMAIL, GOOGLE_PASSWORD, APP_PACKAGE


def ensure_logged_in(driver):
    """
    Pastikan sudah login & berada di Beranda.
    Urutan: cek Beranda -> aktifkan app -> polling sampai layar dikenali
    (Beranda ATAU alur login; fresh install/cold start splash-nya LAMBAT,
    bukti run 21 Sep: is_login_flow_active 6 dtk keburu timeout saat
    splash) -> login kalau perlu -> kalau sedang di layar lain dalam
    app, back sampai Beranda muncul.
    """
    home = HomePage(driver)
    if home.is_loaded():
        return home

    # app mungkin tertutup / di background (mis. launcher) -> aktifkan
    try:
        driver.activate_app(APP_PACKAGE)
    except Exception:
        pass

    login = LoginPage(driver)
    # tunggu layar dikenali dulu (splash pertama kali bisa > 10 dtk)
    deadline = time.time() + 25
    while time.time() < deadline:
        if home.is_loaded():
            return home
        if login.is_login_flow_active(timeout=1):
            break
        time.sleep(0.5)

    if login.is_login_flow_active(timeout=6):
        # memang belum login / di tengah alur login -> alur login Google
        login.login(GOOGLE_EMAIL, GOOGLE_PASSWORD)
        time.sleep(0.4)
        # Beranda butuh waktu load setelah redirect login -> polling
        home = HomePage(driver)
        deadline = time.time() + 15
        while time.time() < deadline:
            if home.is_loaded():
                return home
            time.sleep(0.5)
        # Login otomatis belum berhasil (mis. Google minta verifikasi
        # password manual) -> tunggu user login sendiri di emulator.
        print("[LOGIN] Silakan login manual di emulator (maks 3 menit)...")
        for _ in range(36):
            if home.is_loaded():
                return home
            time.sleep(5)
        assert home.is_loaded(), "Gagal login / halaman Beranda tidak termuat"

    # sedang di layar lain dalam app (menu/form sisa run sebelumnya)
    # -> tekan back sampai halaman utama muncul
    for _ in range(6):
        try:
            driver.back()
        except Exception:
            break
        time.sleep(0.4)
        if home.is_loaded():
            return home

    raise AssertionError(
        "Tidak bisa mencapai halaman Beranda - cek kondisi app di device/emulator"
    )


def goto_apps_menu(driver):
    apps = AppsPage(driver)
    for attempt in range(3):
        home = ensure_logged_in(driver)
        try:
            home.goto_apps()
        except Exception:
            # layar bisa berubah (mis. sesi expired -> dilempar ke login)
            time.sleep(0.4)
            continue
        if apps.is_loaded():
            return apps
        time.sleep(0.4)
    assert apps.is_loaded(), "Halaman Apps tidak termuat"
    return apps
