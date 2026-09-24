"""
Test 8: Menu Quality Control > UBP BAUKSIT TAYAN > Barging
Tanggal hari ini, tambah data (dropdown + dummy), submit.
Bisa dijalankan sendiri: pytest tests/test_08_barging.py
"""
import pytest
from utils.nav_helper import goto_apps_menu
from pages.barging_page import BargingPage
from utils.dummy_data import BARGING_DUMMY


@pytest.mark.order(8)
def test_barging(driver):
    apps = goto_apps_menu(driver)
    apps.open_barging()

    page = BargingPage(driver)
    page.do_all_available(BARGING_DUMMY)
    page.go_back()
