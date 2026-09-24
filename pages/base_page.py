"""
Base Page Object - berisi helper umum yang dipakai semua page object.
"""

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
import time

from config import DEFAULT_TIMEOUT


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, DEFAULT_TIMEOUT)

    # ---------- Locator helpers ----------
    def find(self, locator, timeout=None):
        w = WebDriverWait(self.driver, timeout or DEFAULT_TIMEOUT)
        return w.until(EC.presence_of_element_located(locator))

    def find_clickable(self, locator, timeout=None):
        w = WebDriverWait(self.driver, timeout or DEFAULT_TIMEOUT)
        return w.until(EC.element_to_be_clickable(locator))

    def find_all(self, locator, timeout=None):
        w = WebDriverWait(self.driver, timeout or DEFAULT_TIMEOUT)
        try:
            w.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            return []
        return self.driver.find_elements(*locator)

    def is_present(self, locator, timeout=1):
        """
        Cek kehadiran elemen. Tahan terhadap error TRANSIE UIA2 yang
        pernah mematikan test: 'socket hang up' dan 'Timed out waiting
        for the root AccessibilityNodeInfo' (UI thread sibuk karena
        emulator kehabisan RAM saat Chrome load) -> tunggu sebentar
        lalu coba lagi sampai `timeout` habis.
        Default 1 dtk (feedback user: jangan lama) - kasus butuh
        tunggu lebih lama sudah memakai timeout eksplisit.
        """
        import time as _time
        deadline = _time.time() + timeout
        while True:
            remaining = deadline - _time.time()
            if remaining <= 0:
                return False
            try:
                WebDriverWait(self.driver, max(0.5, remaining)).until(
                    EC.presence_of_element_located(locator)
                )
                return True
            except TimeoutException:
                return False
            except Exception:
                # error transien koneksi/accessibility -> retry
                _time.sleep(1)

    # ---------- Actions ----------
    def tap(self, locator, timeout=2):
        """
        Tap elemen secara DEFENSIF: TIDAK PERNAH melempar exception.
        Race condition (elemen stale, overlay loading, animasi) tidak
        boleh mematikan test di tengah alur -> return None supaya caller
        bisa SKIP (sesuai filosofi test: elemen tidak ada -> SKIP).
        Default timeout 2 dtk (feedback user: klik harus CEPAT, jangan
        nunggu lama) - kalau elemen clickable, tap langsung jalan.
        """
        try:
            el = self.find_clickable(locator, timeout)
            el.click()
            return el
        except Exception:
            pass
        # Fallback: node dengan locator ini ADA di tree tapi match pertama
        # (atau semuanya) tidak lolos cek 'element_to_be_clickable'
        # WebDriver (mis. ada beberapa node ber-desc sama & match pertama
        # bukan node yang clickable) -> klik node clickable PERTAMA yang
        # visible di antara semua match. (Kasus nyata: run_e2e4 gagal di
        # bottom nav 'Apps' padahal elemennya ada & clickable=true.)
        try:
            els = self.driver.find_elements(*locator)
        except Exception:
            return None
        for el in els:
            try:
                if el.get_attribute("clickable") != "true":
                    continue
                if not el.is_displayed():
                    continue
                el.click()
                return el
            except Exception:
                continue
        # Retry terakhir dengan jeda (React Native kadang butuh waktu
        # render), tetap TANPA raise.
        time.sleep(0.15)
        try:
            el = self.find_clickable(locator, 2)
            el.click()
            return el
        except Exception:
            return None

    def type_text(self, locator, text, timeout=None, clear_first=True):
        try:
            el = self.find(locator, timeout)
        except Exception:
            return None
        if clear_first:
            try:
                el.clear()
            except Exception:
                pass
        try:
            el.send_keys(text)
        except Exception:
            return None
        return el

    def get_text(self, locator, timeout=None):
        return self.find(locator, timeout).text

    def scroll_down(self, times=1, pause=0.2):
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.75)
        end_y = int(size["height"] * 0.25)
        for _ in range(times):
            self.driver.swipe(start_x, start_y, start_x, end_y, 350)
            time.sleep(pause)

    def swipe(self, direction="down", pause=0.3):
        """Swipe halaman: 'up' (ke bawah) atau 'down' (ke atas)."""
        size = self.driver.get_window_size()
        x = size["width"] // 2
        if direction == "down":
            self.driver.swipe(x, int(size["height"] * 0.75), x, int(size["height"] * 0.3), 350)
        else:
            self.driver.swipe(x, int(size["height"] * 0.3), x, int(size["height"] * 0.75), 350)
        time.sleep(pause)

    def go_back(self):
        self.driver.back()
        time.sleep(0.15)

    def tap_outside(self, y_frac=0.25):
        """Tap area atas layar (untuk menutup modal/dropdown)."""
        size = self.driver.get_window_size()
        try:
            self.driver.tap([(size["width"] // 2, int(size["height"] * y_frac))], 100)
        except Exception:
            pass
        time.sleep(0.15)

    def find_fab(self):
        """
        Floating Action Button (FAB "+"): ViewGroup clickable di pojok
        kanan-bawah tanpa content-desc/text (terverifikasi dari scan).
        Kembalikan element atau None.
        """
        size = self.driver.get_window_size()
        try:
            els = self.driver.find_elements(
                AppiumBy.XPATH, '//android.view.ViewGroup[@clickable="true"]'
            )
        except Exception:
            return None
        for e in els:
            try:
                cx = e.location["x"] + e.size["width"] // 2
                cy = e.location["y"] + e.size["height"] // 2
            except Exception:
                continue
            if cx > size["width"] * 0.7 and cy > size["height"] * 0.75:
                try:
                    desc = (e.get_attribute("content-desc") or "").strip()
                    if desc:
                        continue  # ada label -> bukan FAB ikon kosong
                except Exception:
                    pass
                return e
        return None
