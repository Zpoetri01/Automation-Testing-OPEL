"""
Test 5: Menu Mining > UBP BAUKSIT TAYAN > Feeding WP
Semua tab (Kelola WP, Fleet), form diisi dinamis (dummy), submit.
Bisa dijalankan sendiri: pytest tests/test_05_feeding_wp.py
"""
import pytest
from utils.nav_helper import goto_apps_menu
from pages.feeding_wp_page import FeedingWpPage
from utils.dummy_data import FEEDING_WP_DUMMY


@pytest.mark.order(5)
def test_feeding_wp(driver):
    apps = goto_apps_menu(driver)
    apps.open_feeding_wp()

    page = FeedingWpPage(driver)
    page.do_all_available(FEEDING_WP_DUMMY)
    page.go_back()
