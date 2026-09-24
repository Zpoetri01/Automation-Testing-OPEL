"""
AppsPage - TERVERIFIKASI dari scan device & emulator (scans/*.xml).

Halaman Apps adalah SATU halaman scroll dengan section header:
    MINING           -> UBP BAUKSIT TAYAN: Dashboard Tayan,
                        Aktivitas Tambang, Ore Getting, Feeding WP,
                        Catching WP
    QUALITY CONTROL  -> UBP BAUKSIT TAYAN: Supply, Barging
    UTILITY / PEI / OTHERS / MENU LAINNYA -> (tidak dipakai)

Catatan penting:
  - 'UBP BAUKSIT TAYAN' muncul DUA KALI (section MINING & QUALITY
    CONTROL), jadi navigasi ke menu memakai content-desc menu-nya
    langsung (unik), bukan nama UBP.
  - Section QUALITY CONTROL bukan tab - cukup scroll ke bawah sampai
    menu Supply/Barging terlihat.
"""

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import time


class AppsPage(BasePage):
    UBP_BAUKSIT_TAYAN_LABEL = (AppiumBy.XPATH, '//*[@text="UBP BAUKSIT TAYAN"]')
    SECTION_QUALITY_CONTROL = (AppiumBy.XPATH, '//*[@text="QUALITY CONTROL"]')

    MENU_DASHBOARD_TAYAN = (AppiumBy.XPATH, '//*[@content-desc="Dashboard Tayan"]')
    MENU_AKTIVITAS_TAMBANG = (AppiumBy.XPATH, '//*[@content-desc="Aktivitas Tambang"]')
    MENU_ORE_GETTING = (AppiumBy.XPATH, '//*[@content-desc="Ore Getting"]')
    MENU_FEEDING_WP = (AppiumBy.XPATH, '//*[@content-desc="Feeding WP"]')
    MENU_CATCHING_WP = (AppiumBy.XPATH, '//*[@content-desc="Catching WP"]')
    MENU_SUPPLY = (AppiumBy.XPATH, '//*[@content-desc="Supply" or @text="Supply"]')
    MENU_BARGING = (AppiumBy.XPATH, '//*[@content-desc="Barging" or @text="Barging"]')

    def is_loaded(self):
        # bottom nav 'Apps' (content-desc) menandakan halaman utama terbuka
        return self.is_present((AppiumBy.XPATH, '//*[@content-desc="Apps"]'), timeout=8)

    def _open_menu(self, desc: str):
        """Scroll sampai menu dengan content-desc mengandung `desc` terlihat,
        lalu tap. (di emulator desc diawali ikon, mis. '<ikon>, Aktivitas
        Tambang' -> pakai contains, bukan exact match.)
        CEPAT & PRESISI (feedback user 22 Sep): swipe KECIL (35% layar)
        + cek tiap langkah — jangan swipe besar sampai overshoot ke
        section jauh (menu berikutnya bersebelahan dengan menu sebelumnya
        di section yang sama)."""
        locator = (AppiumBy.XPATH, f'//*[contains(@content-desc,"{desc}")]')
        size = self.driver.get_window_size()
        x = size["width"] // 2
        y_hi = int(size["height"] * 0.62)
        y_lo = int(size["height"] * 0.28)
        for _ in range(8):
            if self.is_present(locator, timeout=0.8):
                break
            try:
                self.driver.swipe(x, y_hi, x, y_lo, 250)
                time.sleep(0.2)
            except Exception:
                break
        for _ in range(8):
            if self.is_present(locator, timeout=0.8):
                break
            try:
                self.driver.swipe(x, y_lo, x, y_hi, 250)
                time.sleep(0.2)
            except Exception:
                break
        self.tap(locator, timeout=2)

    # ---- Menu Mining (UBP BAUKSIT TAYAN) ----
    def open_aktivitas_tambang(self):
        self._open_menu("Aktivitas Tambang")

    def open_ore_getting(self):
        self._open_menu("Ore Getting")

    def open_feeding_wp(self):
        self._open_menu("Feeding WP")

    def open_catching_wp(self):
        self._open_menu("Catching WP")

    # ---- Menu Quality Control (UBP BAUKSIT TAYAN) ----
    def open_supply(self):
        self._open_menu("Supply")

    def open_barging(self):
        self._open_menu("Barging")
