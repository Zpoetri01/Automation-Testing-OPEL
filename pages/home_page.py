"""
HomePage (Beranda) - berdasarkan "PAGES BERANDA.txt"
Bottom navigation (Beranda / Apps / Aktivitas / Profil) muncul konsisten
di semua halaman utama, jadi method di sini bisa dipakai lintas page.
"""

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class HomePage(BasePage):
    # Bottom navigation (content-desc terverifikasi dari locator dump)
    NAV_BERANDA = (AppiumBy.XPATH, '//*[@content-desc="Beranda"]')
    NAV_APPS = (AppiumBy.XPATH, '//*[@content-desc="Apps"]')
    NAV_AKTIVITAS = (AppiumBy.XPATH, '//*[@content-desc="Aktivitas"]')
    NAV_PROFIL = (AppiumBy.XPATH, '//*[@content-desc="Profil"]')

    GREETING_TEXT = (AppiumBy.XPATH, '//*[contains(@text,"Selamat")]')

    def is_loaded(self):
        return self.is_present(self.NAV_APPS, timeout=15)

    def goto_beranda(self):
        self.tap(self.NAV_BERANDA)

    def goto_apps(self):
        self.tap(self.NAV_APPS)

    def goto_aktivitas(self):
        self.tap(self.NAV_AKTIVITAS)

    def goto_profil(self):
        self.tap(self.NAV_PROFIL)
