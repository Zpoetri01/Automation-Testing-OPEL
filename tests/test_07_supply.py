"""
Test 7: Menu Quality Control > UBP BAUKSIT TAYAN > Supply
Semua tab (Fleet, Kelola Jembatan Timbang), tambah data, submit.
Bisa dijalankan sendiri: pytest tests/test_07_supply.py
"""
import pytest
from utils.nav_helper import goto_apps_menu
from pages.supply_page import SupplyPage
from utils.dummy_data import SUPPLY_DUMMY


@pytest.mark.order(7)
def test_supply(driver):
    apps = goto_apps_menu(driver)
    apps.open_supply()

    page = SupplyPage(driver)
    page.do_all_available(SUPPLY_DUMMY)
    page.go_back()
