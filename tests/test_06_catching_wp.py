"""
Test 6: Menu Mining > UBP BAUKSIT TAYAN > Catching WP
Semua tab: Fleet (tambah data) + Kelola Tumpukan (Selesai item teratas).
Bisa dijalankan sendiri: pytest tests/test_06_catching_wp.py
"""
import pytest
from utils.nav_helper import goto_apps_menu
from pages.catching_wp_page import CatchingWpPage
from utils.dummy_data import CATCHING_WP_DUMMY


@pytest.mark.order(6)
def test_catching_wp(driver):
    apps = goto_apps_menu(driver)
    apps.open_catching_wp()

    page = CatchingWpPage(driver)
    page.do_all_available(CATCHING_WP_DUMMY)
    page.go_back()
