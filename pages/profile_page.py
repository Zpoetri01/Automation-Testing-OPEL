"""
ProfilePage - berdasarkan "PAGES PROFILE.txt" + scan "Logout.txt".

Berisi: Favorit (Finding, Alarm, Form Deklarasi Kesehatan, Dokumen),
Akun dan Keamanan (Akun Saya, Biometrics), Informasi (Kontak Darurat,
SIM Perusahaan), Seputar Aplikasi (Ubah Bahasa - ID/EN).

Dialog konfirmasi logout SUDAH terverifikasi dari scan "Logout.txt"
(popup "Perhatian! Apakah anda yakin untuk logout?" dengan tombol
"Tidak" / "Ya").

CATATAN: tombol pemicu logout ("Logout"/"Keluar" di menu Profil) belum
ter-capture di scan -> logout() memakai strategi bertingkat:
  1. scroll penuh halaman Profil sambil cari tombol
  2. kalau tidak ketemu, buka 'Akun Saya' dan cari di dalamnya
"""

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import time


class ProfilePage(BasePage):
    AKUN_SAYA = (AppiumBy.XPATH, '//*[contains(@content-desc,"Akun Saya")]')

    # kandidat tombol pemicu logout (belum terverifikasi, multi-strategi)
    BTN_LOGOUT = (AppiumBy.XPATH,
                  '//*[@text="Logout" or @text="Keluar" or @text="Sign Out" or @text="Sign out"'
                  ' or contains(@content-desc,"Logout") or contains(@content-desc,"Keluar")'
                  ' or contains(@content-desc,"Sign out") or contains(@content-desc,"Sign Out")]')

    # ---- Dialog konfirmasi logout (terverifikasi dari "Logout.txt") ----
    DIALOG_TITLE = (AppiumBy.XPATH, '//*[@text="Perhatian!"]')
    DIALOG_MESSAGE = (AppiumBy.XPATH, '//*[@text="Apakah anda yakin untuk logout?"]')
    BTN_CONFIRM_LOGOUT = (AppiumBy.XPATH, '//*[@content-desc="Ya"]')
    BTN_CANCEL_LOGOUT = (AppiumBy.XPATH, '//*[@content-desc="Tidak"]')

    def open_akun_saya(self):
        self.tap(self.AKUN_SAYA)
        time.sleep(0.4)

    def is_logout_dialog_present(self, timeout=5):
        return self.is_present(self.DIALOG_MESSAGE, timeout=timeout)

    def confirm_logout(self):
        """Tap 'Ya' pada dialog konfirmasi 'Apakah anda yakin untuk logout?'."""
        if self.is_logout_dialog_present(timeout=5):
            self.tap(self.BTN_CONFIRM_LOGOUT)
            return True
        return False

    def cancel_logout(self):
        """Tap 'Tidak' pada dialog konfirmasi logout (batal logout)."""
        if self.is_logout_dialog_present(timeout=5):
            self.tap(self.BTN_CANCEL_LOGOUT)
            return True
        return False

    def _find_logout_button(self, max_scrolls=10):
        """Cari tombol pemicu logout ('Keluar') sambil scroll ke bawah
        (sesuai skenario: scroll sampai bawah halaman Profil)."""
        for _ in range(max_scrolls):
            if self.is_present(self.BTN_LOGOUT, timeout=2):
                return True
            self.scroll_down(times=1, pause=0.7)
        return self.is_present(self.BTN_LOGOUT, timeout=2)

    def logout(self):
        """
        1. Cari tombol pemicu logout di halaman Profil (scroll penuh).
        2. Kalau tidak ketemu, coba di dalam 'Akun Saya'.
        3. Setelah dialog konfirmasi muncul -> tap 'Ya'.
        """
        if self._find_logout_button():
            self.tap(self.BTN_LOGOUT)
            time.sleep(0.4)
            if self.confirm_logout():
                return True

        # strategi 2: di dalam halaman 'Akun Saya'
        if self.is_present(self.AKUN_SAYA, timeout=3):
            self.open_akun_saya()
            if self._find_logout_button():
                self.tap(self.BTN_LOGOUT)
                time.sleep(0.4)
                if self.confirm_logout():
                    return True
        return False
