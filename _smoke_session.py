"""Smoke test: buat sesi Appium dengan caps conftest, cek app terbuka."""
import sys

sys.path.insert(0, r"D:\Magang\ANTAM\opel-mobile-2")

from appium import webdriver
from appium.options.android import UiAutomator2Options

from config import APPIUM_SERVER, CAPABILITIES

opts = UiAutomator2Options().load_capabilities(CAPABILITIES)
drv = webdriver.Remote(APPIUM_SERVER, options=opts)
print("SESSION_OK")
print("package   =", drv.current_package)
print("activity  =", drv.current_activity)
drv.quit()
print("SMOKE_DONE")
