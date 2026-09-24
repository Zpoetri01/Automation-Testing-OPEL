"""
Test 2: Pilih menu Apps dari bottom navigation.
Bisa dijalankan sendiri: pytest tests/test_02_pilih_apps.py
"""
import pytest
from utils.nav_helper import goto_apps_menu


@pytest.mark.order(2)
def test_pilih_apps(driver):
    apps = goto_apps_menu(driver)
    assert apps.is_loaded()
