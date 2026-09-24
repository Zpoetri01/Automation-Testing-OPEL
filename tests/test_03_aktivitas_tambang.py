"""
Test 3: Menu Mining > UBP BAUKSIT TAYAN > Aktivitas Tambang
Tanggal hari ini, isi dropdown (opsi pertama) + field teks (dummy),
submit kalau tersedia. Bisa dijalankan sendiri.
"""
import pytest
from utils.nav_helper import goto_apps_menu
from pages.aktivitas_tambang_page import AktivitasTambangPage
from utils.dummy_data import AKTIVITAS_TAMBANG_DUMMY


@pytest.mark.order(3)
def test_aktivitas_tambang(driver):
    apps = goto_apps_menu(driver)
    apps.open_aktivitas_tambang()

    page = AktivitasTambangPage(driver)
    page.do_all_available(AKTIVITAS_TAMBANG_DUMMY)
    page.go_back()
