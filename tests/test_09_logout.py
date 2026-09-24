"""
Test 9: Kembali ke Beranda, buka Profil, lalu Logout.
Dialog konfirmasi logout ("Apakah anda yakin untuk logout?" -> Ya/Tidak)
terverifikasi dari scan "Logout.txt". Tombol pemicunya dicari dengan
scroll penuh halaman Profil (+ 'Akun Saya' sebagai fallback).
Bisa dijalankan sendiri: pytest tests/test_09_logout.py
"""
import pytest
from utils.nav_helper import ensure_logged_in
from pages.profile_page import ProfilePage


@pytest.mark.order(9)
def test_logout(driver):
    home = ensure_logged_in(driver)
    home.goto_profil()

    profile = ProfilePage(driver)
    success = profile.logout()
    assert success, (
        "Tombol Logout belum ditemukan - lengkapi locator BTN_LOGOUT "
        "di pages/profile_page.py setelah scan ulang halaman Profil."
    )
