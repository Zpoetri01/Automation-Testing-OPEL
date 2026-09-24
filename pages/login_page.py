"""
LoginPage
=========
Locator SUDAH terverifikasi dari scan "Login.txt" (3 tahap layar):

1. Halaman awal app OPEL (package com.antam.opel.development) - tombol "Masuk"
   (content-desc "Masuk, " / text "Masuk") -> membuka halaman login
   B2C (Chrome custom tab, host antamapps.b2clogin.com).
2. Halaman login B2C (Chrome custom tab) - berisi tombol "Login dengan
   Google" (text) yang memicu popup pemilihan akun Google.
3. Popup "Pilih akun" (masih dalam Chrome custom tab, host
   accounts.google.com) - berisi:
   - heading "Pilih akun" (resource-id "headingText")
   - list akun Google yang sudah tersimpan di device, tiap item
     content-desc berformat "{Nama} {email}" (mis. "Ratih Dian
     rdiananggraeni06@gmail.com")
   - tombol "Gunakan akun lain" (content-desc) untuk login pakai akun
     yang belum ada di daftar
   - tombol "Scroll ke bawah" (content-desc) kalau akun yang dicari
     belum terlihat di daftar

CATATAN: karena ini WebView/Chrome custom tab, elemen tetap bisa
diakses via UiAutomator2 (text/content-desc) tanpa perlu switch
context - konsisten dengan pendekatan locator di seluruh project ini.
"""

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import time


class LoginPage(BasePage):
    # ---- 1. Halaman awal OPEL ----
    BTN_MASUK = (AppiumBy.XPATH, '//*[contains(@content-desc,"Masuk") or @text="Masuk"]')

    # ---- 2. Halaman login B2C (Chrome custom tab) ----
    # Teks tombol bisa BAHASA INDONESIA ("Login dengan Google") atau
    # ENGLISH ("GOOGLE") tergantung locale B2C -> pakai match fleksibel.
    BTN_LOGIN_DENGAN_GOOGLE = (AppiumBy.XPATH,
                               '//*[contains(@text,"Google") or contains(@text,"GOOGLE")'
                               ' or contains(@content-desc,"Google") or contains(@content-desc,"GOOGLE")]')

    # ---- 3. Popup "Pilih akun" Google ----
    HEADING_PILIH_AKUN = (AppiumBy.XPATH, '//*[@resource-id="headingText" and @text="Pilih akun"]')
    BTN_GUNAKAN_AKUN_LAIN = (AppiumBy.XPATH, '//*[@content-desc="Gunakan akun lain" or @text="Gunakan akun lain"]')
    BTN_SCROLL_KE_BAWAH = (AppiumBy.XPATH, '//*[@content-desc="Scroll ke bawah"]')

    # ---- 3b. Dialog NATIVE Chrome "Continue as <nama>" (emulator Chrome 113,
    # TERVERIFIKASI scan 2026-09-04: yang muncul ini, bukan popup web) ----
    CHROME_ACCOUNT_EMAIL = (AppiumBy.ID, "com.android.chrome:id/account_text_secondary")
    CHROME_CONTINUE_AS = (AppiumBy.ID, "com.android.chrome:id/account_picker_continue_as_button")
    CHROME_SKIP = (AppiumBy.ID, "com.android.chrome:id/account_picker_dismiss_button")

    # Fallback manual (WebView Google Sign-In, dipakai kalau pilih "Gunakan akun lain")
    GOOGLE_EMAIL_INPUT = (AppiumBy.ID, "identifierId")
    GOOGLE_NEXT_BTN = (AppiumBy.XPATH, '//*[@text="Berikutnya" or @text="Next"]')
    # di emulator field sandi = EditText password=true TANPA resource-id
    GOOGLE_PASSWORD_INPUT = (AppiumBy.XPATH, '//android.widget.EditText[@password="true"]')
    GOOGLE_PASSWORD_NEXT_BTN = (AppiumBy.XPATH, '//*[@text="Berikutnya" or @text="Next"]')

    def account_item_locator(self, email: str):
        """Locator item akun di list "Pilih akun" berdasarkan email (content-desc
        berformat "{Nama} {email}")."""
        return (AppiumBy.XPATH, f'//*[contains(@content-desc,"{email}")]')

    def tap_masuk(self):
        """Tap tombol 'Masuk' di halaman awal OPEL."""
        self.tap(self.BTN_MASUK)
        time.sleep(0.25)

    def tap_login_dengan_google(self):
        """Tap tombol 'Login dengan Google' / 'GOOGLE' di halaman login B2C
        (Chrome custom tab). Chrome tab butuh waktu lama load di emulator
        (software rendering) -> tunggu sampai 45 detik."""
        if self.is_present(self.BTN_LOGIN_DENGAN_GOOGLE, timeout=45):
            self.tap(self.BTN_LOGIN_DENGAN_GOOGLE)
            time.sleep(0.25)
            return True
        print("[LOGIN] tombol Google tidak muncul di halaman B2C (45 dtk)")
        return False

    def _wait_login_state(self, max_wait=15):
        """Setelah tap 'Login dengan Google', tunggu sampai salah satu layar
        berikut muncul: dialog Chrome 'Continue as', popup 'Pilih akun',
        form web Google (email/password), atau sudah langsung ke Beranda.
        Koneksi UIA2 bisa PUTUS sementara saat Chrome load (pernah
        'socket hang up' mematikan test di sini) -> error koneksi
        transien TIDAK dibiarkan membunuh test, cukup coba lagi."""
        home = (AppiumBy.XPATH, '//*[@content-desc="Apps"]')
        deadline = time.time() + max_wait
        while time.time() < deadline:
            for loc in (self.CHROME_CONTINUE_AS, self.HEADING_PILIH_AKUN,
                        self.GOOGLE_EMAIL_INPUT, self.GOOGLE_PASSWORD_INPUT,
                        home):
                try:
                    if self.is_present(loc, timeout=0.5):
                        return True
                except Exception:
                    # koneksi putus sesaat -> jeda & coba lagi (max_wait)
                    time.sleep(0.25)
                    break
            time.sleep(0.25)
        return False

    def choose_existing_account_if_present(self, email: str):
        """Di popup 'Pilih akun', pilih akun yang mengandung `email` pada
        content-desc ATAU text (di emulator node akun kadang text-based).
        Kalau `email` kosong, pilih akun PERTAMA di daftar (praktis untuk
        emulator yang hanya punya satu akun Google tersimpan).
        Kalau tidak ditemukan langsung, coba tap 'Scroll ke bawah' dulu (akun lain
        mungkin ada di bawah daftar yang terlihat)."""
        if not self.is_present(self.HEADING_PILIH_AKUN, timeout=8):
            return False

        if email:
            locators = [self.account_item_locator(email),
                        (AppiumBy.XPATH, f'//*[contains(@text,"{email}")]')]
        else:
            # item akun: desc/text berformat '{Nama} {email}' -> mengandung '@'
            locators = [
                (AppiumBy.XPATH, '//*[contains(@content-desc,"@") and @clickable="true"]'),
                (AppiumBy.XPATH, '//*[contains(@text,"@") and @clickable="true"]'),
            ]

        for _ in range(2):  # coba lagi setelah scroll ke bawah
            for locator in locators:
                if self.is_present(locator, timeout=3):
                    self.tap(locator)
                    return True
            if not self.is_present(self.BTN_SCROLL_KE_BAWAH, timeout=3):
                break
            self.tap(self.BTN_SCROLL_KE_BAWAH)
            time.sleep(0.25)
        return False

    def handle_chrome_native_picker(self, email: str):
        """
        Emulator Chrome 113 menampilkan dialog NATIVE 'Continue as <nama>'
        (com.android.chrome:id/account_picker_*) setelah tap 'Login dengan
        Google', BUKAN popup web 'Pilih akun'. Cek email yang ditampilkan:
        cocok dengan `email` (atau `email` kosong) -> tap 'Continue as';
        tidak cocok -> tap 'Skip' supaya jatuh ke popup web 'Pilih akun'.
        """
        if not self.is_present(self.CHROME_CONTINUE_AS, timeout=4):
            return False
        try:
            shown = (self.get_text(self.CHROME_ACCOUNT_EMAIL) or "").strip()
        except Exception:
            shown = ""
        if email and shown and email.lower() not in shown.lower():
            self.tap(self.CHROME_SKIP)
            time.sleep(0.25)
            return False
        self.tap(self.CHROME_CONTINUE_AS)
        return True

    def complete_google_web_login(self, email: str, password: str):
        """
        Selesaikan form web Google Sign-In (accounts.google.com) kalau
        muncul: halaman email (identifierId, mungkin sudah terisi) lalu
        halaman sandi (EditText password=true). Dipakai setelah akun
        dipilih/tidak ditemukan di daftar.
        """
        if self.is_present(self.GOOGLE_EMAIL_INPUT, timeout=6):
            try:
                current = (self.get_text(self.GOOGLE_EMAIL_INPUT) or "").strip()
            except Exception:
                current = ""
            if not current and email:
                self.type_text(self.GOOGLE_EMAIL_INPUT, email)
            self.tap(self.GOOGLE_NEXT_BTN)
            time.sleep(0.25)
        if self.is_present(self.GOOGLE_PASSWORD_INPUT, timeout=8):
            self.type_text(self.GOOGLE_PASSWORD_INPUT, password)
            self.tap(self.GOOGLE_PASSWORD_NEXT_BTN)
            time.sleep(0.25)

    def tap_gunakan_akun_lain(self):
        if self.is_present(self.BTN_GUNAKAN_AKUN_LAIN, timeout=5):
            self.tap(self.BTN_GUNAKAN_AKUN_LAIN)
            time.sleep(0.25)
            return True
        return False

    def login_with_credentials(self, email: str, password: str):
        """Fallback: isi email & password manual (dipakai setelah tap 'Gunakan akun
        lain', atau kalau popup 'Pilih akun' tidak muncul sama sekali)."""
        if self.is_present(self.GOOGLE_EMAIL_INPUT, timeout=5):
            self.type_text(self.GOOGLE_EMAIL_INPUT, email)
            self.tap(self.GOOGLE_NEXT_BTN)
            time.sleep(0.25)
        if self.is_present(self.GOOGLE_PASSWORD_INPUT, timeout=5):
            self.type_text(self.GOOGLE_PASSWORD_INPUT, password)
            self.tap(self.GOOGLE_PASSWORD_NEXT_BTN)
            time.sleep(0.25)

    def is_login_flow_active(self, timeout=6):
        """True kalau sedang berada di SALAH SATU layar alur login: halaman
        awal OPEL ('Masuk'), B2C ('GOOGLE'), dialog Chrome 'Continue as',
        popup 'Pilih akun', atau form web Google (email/password)."""
        locators = [
            self.BTN_MASUK, self.BTN_LOGIN_DENGAN_GOOGLE,
            self.CHROME_CONTINUE_AS, self.HEADING_PILIH_AKUN,
            self.GOOGLE_EMAIL_INPUT, self.GOOGLE_PASSWORD_INPUT,
        ]
        for i, loc in enumerate(locators):
            # layar pertama diberi waktu lebih, sisanya cek cepat
            t = timeout if i == 0 else 1
            if self.is_present(loc, timeout=t):
                return True
        return False

    def login(self, email: str = "", password: str = ""):
        """
        Alur login lengkap (device & emulator), STATE-AWARE: bisa mulai
        dari halaman awal OPEL ATAU dari tengah alur (B2C sudah terbuka,
        popup akun, form web) sisa run sebelumnya:
        1. Tap 'Masuk' di halaman awal OPEL (kalau masih di sana)
        2. Tap 'Login dengan Google' / 'GOOGLE' di halaman B2C
        3. Di emulator: dialog native Chrome 'Continue as' -> tap kalau
           akunnya cocok, 'Skip' kalau tidak.
        4. Di popup web 'Pilih akun': pilih akun sesuai `email`, atau
           'Gunakan akun lain' -> form email & sandi manual.
        5. Kalau Google tetap minta verifikasi -> lengkapi form web
           (identifierId + EditText password).
        """
        mid = None
        if not self.is_present(self.BTN_LOGIN_DENGAN_GOOGLE, timeout=3):
            # belum di B2C -> cek apakah sudah di tengah alur akun
            mid = (
                self.is_present(self.CHROME_CONTINUE_AS, timeout=1)
                or self.is_present(self.HEADING_PILIH_AKUN, timeout=1)
                or self.is_present(self.GOOGLE_EMAIL_INPUT, timeout=1)
                or self.is_present(self.GOOGLE_PASSWORD_INPUT, timeout=1)
            )
            if not mid:
                print("[LOGIN] 1. tap 'Masuk'")
                self.tap_masuk()
                print("[LOGIN] 2. tap 'Login dengan Google'")
                self.tap_login_dengan_google()
        else:
            print("[LOGIN] sudah di halaman B2C -> tap 'Login dengan Google'")
            self.tap_login_dengan_google()

        # tunggu layar login berikutnya (B2C/Chrome bisa lambat di emulator)
        self._wait_login_state(max_wait=30)

        # emulator: dialog native Chrome 'Continue as' muncul lebih dulu
        if self.handle_chrome_native_picker(email):
            print("[LOGIN] 3. dialog Chrome 'Continue as' -> lanjut")
        elif not self.choose_existing_account_if_present(email):
            if self.tap_gunakan_akun_lain():
                print("[LOGIN] 3. pilih 'Gunakan akun lain'")
            # popup 'Pilih akun' tidak muncul -> mungkin langsung ke form web

        self.complete_google_web_login(email, password)

        time.sleep(0.25)  # tunggu proses login & redirect ke Beranda
