"""
Test 1: Buka aplikasi OPEL & Login dengan akun Google.
Bisa dijalankan sendiri: pytest tests/test_01_login.py
"""
import pytest
from utils.nav_helper import ensure_logged_in


@pytest.mark.order(1)
def test_login_google(driver):
    home = ensure_logged_in(driver)
    assert home.is_loaded()
