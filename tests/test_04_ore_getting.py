"""
Test 4: Menu Mining > UBP BAUKSIT TAYAN > Ore Getting
Semua tab: Fleet (tambah data) + Kelola Tumpukan (Selesai item teratas).
Bisa dijalankan sendiri: pytest tests/test_04_ore_getting.py
"""
import pytest
from utils.nav_helper import goto_apps_menu
from pages.ore_getting_page import OreGettingPage
from utils.dummy_data import ORE_GETTING_DUMMY


@pytest.mark.order(4)
def test_ore_getting(driver):
    apps = goto_apps_menu(driver)
    apps.open_ore_getting()

    page = OreGettingPage(driver)
    page.do_all_available(ORE_GETTING_DUMMY)
    page.go_back()
