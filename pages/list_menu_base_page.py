"""
ListMenuBasePage
=================
Semua menu (Aktivitas Tambang, Ore Getting, Feeding WP, Catching WP,
Supply, Barging) memakai pola halaman yang sama (TERVERIFIKASI dari scan
USB device CPH2591, scans/*.xml):

  - header dengan tombol back (content-desc = ikon chevron '\\uf053')
  - filter Tanggal (content-desc 'Tanggal, <hari>, <tanggal>')
  - search bar (resource-id RNE__SearchBar, placeholder beda per menu/tab)
  - list data / empty state 'Data Tidak Ditemukan'
  - FAB tambah data: ViewGroup clickable di pojok kanan-bawah TANPA
    content-desc/text -> BasePage.find_fab()
  - form isian: dropdown 'Pilih <x>' (clickable View, desc = placeholder),
    EditText 'Ketik disini..' setelah label, tombol 'Simpan' (desc)
  - kalender: undefined.header.title / .leftArrow / .rightArrow,
    undefined.day_YYYY-MM-DD, tombol 'Pilih' (desc)

ATURAN APP (terverifikasi saat scan):
  - Pengisian data HANYA boleh untuk tanggal hari ini / kemarin. Kalau
    filter tanggal bukan hari ini, tap FAB memunculkan toast
    'Tidak dapat menambah data ...' -> `open_add_form()` mendeteksinya
    dan mengembalikan False (otomatis SKIP sesuai skenario).
  - Dropdown bisa kosong (mis. shift belum terdaftar untuk akun tsb).
    `select_dropdown_option()` otomatis SKIP kalau tidak ada opsi.
"""

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
from config import (
    FILTER_START_DAYS_AGO, FILTER_END_DAYS_AGO,
    APP_PACKAGE,
)
import datetime
import re
import time


class ListMenuBasePage(BasePage):
    BTN_BACK = (AppiumBy.XPATH, '//*[@content-desc=""]')
    SEARCH_INPUT = (AppiumBy.ID, "RNE__SearchBar")
    # App 2.5.15: resource-id RN tidak lagi dipakai (RNE__SearchBar
    # hilang dari dump) -> deteksi search bar lewat TEKS 'Cari..'
    # (semua menu list memilikinya, mis. 'Cari asal atau tujuan').
    # KECUALIKAN 'Cari menu atau fitur...' milik halaman Apps (bukti
    # 23 Sep: halaman Apps salah terdeteksi sebagai halaman list).
    SEARCH_INPUT_TEXT = (AppiumBy.XPATH,
                         '//*[contains(@text,"Cari") and not(contains(@text,"menu"))'
                         ' or contains(@content-desc,"Cari") and not(contains(@content-desc,"menu"))]')
    DATE_PICKER_BTN = (AppiumBy.XPATH,
                       '//*[contains(@content-desc,"Tanggal,")'
                       ' or (@clickable="true" and contains(@content-desc,"2026")'
                       ' and not(contains(@content-desc,":")))]')
    # CATATAN app 2.5.15: pill tanggal desc-nya ', Rabu, 23 September 2026, '
    # TANPA kata 'Tanggal,' (label 'Tanggal' TextView terpisah) -> fallback
    # kedua: elemen clickable ber-desc tahun TANPA ':' (kartu entry punya
    # jam, mis. '23 Sep 2026 07:00, ...' -> punya ':' -> tidak match)
    EMPTY_STATE_TITLE = (AppiumBy.XPATH, '//*[@text="Data Tidak Ditemukan"]')

    # ---- Kalender pilih tanggal (terverifikasi dari scan) ----
    CAL_HEADER_TITLE = (AppiumBy.XPATH, '//*[@resource-id="undefined.header.title"]')
    CAL_PREV_MONTH = (AppiumBy.XPATH, '//*[@resource-id="undefined.header.leftArrow"]')
    CAL_NEXT_MONTH = (AppiumBy.XPATH, '//*[@resource-id="undefined.header.rightArrow"]')
    CAL_CONFIRM_BTN = (AppiumBy.XPATH, '//*[@content-desc="Pilih"]')

    # ---- Form isian ----
    BTN_SUBMIT = (AppiumBy.XPATH, '//*[@content-desc="Simpan" or @text="Simpan"]')

    # ---- Halaman Detail (terverifikasi scan e1_detail / d2_detail_bottom) ----
    DETAIL_HEADER = (AppiumBy.XPATH, '//*[@content-desc="Detail"]')
    BTN_LOG_PERGERAKAN = (AppiumBy.XPATH, '//*[@content-desc="Lihat Log Pergerakan"]')
    BTN_TAMBAH_RITASE = (AppiumBy.XPATH, '//*[@content-desc="Tambah Ritase"]')
    BTN_TAMBAH_WP = (AppiumBy.XPATH,
                     '//*[contains(@content-desc,"Tambah WP") or contains(@text,"Tambah WP")]')
    BTN_HAPUS = (AppiumBy.XPATH, '//*[contains(@content-desc,"Hapus") or contains(@text,"Hapus")]')
    BTN_KEMBALI = (AppiumBy.XPATH,
                   '//*[contains(@content-desc,"Kembali") or contains(@text,"Kembali")]')
    BTN_YA = (AppiumBy.XPATH, '//*[@content-desc="Ya" or @text="Ya"]')

    # Tombol status unit di halaman Detail / item di tab kelola (urutan
    # sesuai tampilan app: Mulai Operasi, Standby (kuning), Breakdown, Selesai (merah))
    STATUS_BUTTONS = ["Mulai Operasi", "Standby", "Breakdown", "Selesai"]

    # ---- Dialog konfirmasi 'selesaikan tumpukan' (terverifikasi) ----
    CONFIRM_DIALOG_OK = (AppiumBy.XPATH, '//*[@content-desc="OK"]')
    CONFIRM_DIALOG_CANCEL = (AppiumBy.XPATH, '//*[@content-desc="Batal"]')

    # Toast blokir tambah data (terverifikasi):
    # 'Tidak dapat menambah data - Pengisian data hanya dapat dilakukan
    # untuk tanggal hari ini, atau tanggal kemarin ...'
    BLOCK_TOAST = (AppiumBy.XPATH, '//*[contains(@content-desc,"Tidak dapat menambah data")]')

    MONTHS_ID = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    WEEKEND_NAMES = {"Minggu", "Sabtu"}

    # ----------------------------------------------------------------
    # Navigasi
    # ----------------------------------------------------------------
    def go_back(self, max_backs=3):
        """Kembali ke halaman utama (Apps/Beranda). Tap tombol back
        berulang sampai bottom nav terlihat (form -> list -> Apps)."""
        nav_apps = (AppiumBy.XPATH, '//*[@content-desc="Apps"]')
        for _ in range(max_backs):
            if self.is_present(nav_apps, timeout=0.6):
                return
            if self.is_present(self.BTN_BACK, timeout=0.6):
                self.tap(self.BTN_BACK)
            else:
                try:
                    self.driver.back()
                except Exception:
                    pass
            time.sleep(0.15)

    def open_tab(self, tab_label: str):
        """Buka tab berdasarkan content-desc (mis. 'Fleet', 'Kelola
        Tumpukan'). Pakai contains() supaya tetap match kalau desc
        diawali ikon/koma. RETRY sampai tab bar ter-render (bukti run
        23 Sep: halaman baru dibuka masih loading -> 'Fleet' tidak
        ketemu padahal tab-nya ada di dump belakangan)."""
        locator = (AppiumBy.XPATH, f'//*[contains(@content-desc,"{tab_label}")]')
        for _ in range(8):
            if self.is_present(locator, timeout=1):
                if self.tap(locator, timeout=2) is not None:
                    time.sleep(0.15)
                    return True
            time.sleep(0.4)
        print(f"[TAB] '{tab_label}' tidak ditemukan")
        return False
        return False

    # ----------------------------------------------------------------
    # Kalender / tanggal
    # ----------------------------------------------------------------
    def _open_calendar(self):
        if not self.is_present(self.DATE_PICKER_BTN, timeout=5):
            return False
        self.tap(self.DATE_PICKER_BTN)
        time.sleep(0.15)
        return self.is_present(self.CAL_HEADER_TITLE, timeout=3)

    def _navigate_calendar_to(self, month: int, year: int):
        target_label = f"{self.MONTHS_ID[month - 1]} {year}"
        for _ in range(24):
            if not self.is_present(self.CAL_HEADER_TITLE, timeout=2):
                return False
            current = self.get_text(self.CAL_HEADER_TITLE).strip()
            if current == target_label:
                return True
            try:
                cur_m = self.MONTHS_ID.index(current.split()[0]) + 1
                cur_y = int(current.split()[-1])
            except (ValueError, IndexError):
                return False
            if (cur_y, cur_m) < (year, month):
                self.tap(self.CAL_NEXT_MONTH, timeout=2)
            else:
                self.tap(self.CAL_PREV_MONTH, timeout=2)
            time.sleep(0.15)
        return False

    def _day_cell(self, day: int, month: int, year: int):
        rid = f"undefined.day_{year:04d}-{month:02d}-{day:02d}"
        locator = (AppiumBy.XPATH, f'//*[@resource-id="{rid}"]')
        if self.is_present(locator, timeout=2):
            return self.find(locator, timeout=2)
        return None

    def _confirm_calendar(self):
        if self.is_present(self.CAL_CONFIRM_BTN, timeout=3):
            self.tap(self.CAL_CONFIRM_BTN)
            time.sleep(0.15)
            return True
        return False

    def _selectable_day_cell(self, day_date):
        """Cell kalender untuk tanggal `day_date`. Kalau cell disabled
        (tidak ada data di tanggal itu - app menandai desc 'disabled'),
        DIGANTI otomatis dengan hari masa lampau terdekat yang aktif
        (feedback user: elemen tidak muncul -> ganti otomatis, BUKAN
        SKIP)."""
        cell = self._day_cell(day_date.day, day_date.month, day_date.year)
        if cell is None:
            return None
        try:
            desc = (cell.get_attribute("content-desc") or "")
        except Exception:
            return cell
        if "disabled" not in desc:
            return cell
        for offset in range(1, 8):
            d = day_date - datetime.timedelta(days=offset)
            c2 = self._day_cell(d.day, d.month, d.year)
            if c2 is None:
                continue
            try:
                d2 = (c2.get_attribute("content-desc") or "")
            except Exception:
                continue
            if "disabled" not in d2:
                print(f"[TANGGAL] {day_date.day} {self.MONTHS_SHORT[day_date.month-1]}"
                      f" disabled -> ganti {d.day} {self.MONTHS_SHORT[d.month-1]}")
                return c2
        return cell  # tidak ada pengganti -> kembalikan apa adanya

    def set_date_range_past(self):
        """
        Skenario user (23 Sep 2026): filter tanggal tiap menu =
        KALENDER RENTANG TANGGAL MASA LAMPAU (lusa s/d kemarin),
        BUKAN satu tanggal. Langkah: buka kalender -> tap tanggal MULAI
        -> tap tanggal AKHIR -> tombol 'Pilih'. Kalau kalender menutup
        sendiri setelah tap pertama (app single-date), filter tanggal
        tunggal sudah terpasang dan dianggap berhasil. Cell disabled
        diganti otomatis hari aktif terdekat.
        """
        today = datetime.date.today()
        start = today - datetime.timedelta(days=FILTER_START_DAYS_AGO)
        end = today - datetime.timedelta(days=FILTER_END_DAYS_AGO)
        if not self._open_calendar():
            print("[TANGGAL] tombol filter tanggal tidak ditemukan -> SKIP")
            self._dump_screen("auto_tanggal_fail")
            return False
        if not self._navigate_calendar_to(start.month, start.year):
            self.tap_outside()
            return False
        start_cell = self._selectable_day_cell(start)
        if start_cell is None:
            self.tap_outside()
            return False
        try:
            start_cell.click()
        except Exception:
            pass
        time.sleep(0.2)
        # kalender bisa menutup sendiri setelah tap pertama (single-date)
        if not self.is_present(self.CAL_HEADER_TITLE, timeout=2):
            print(f"[TANGGAL] kalender tertutup setelah tap {start.day} "
                  f"{self.MONTHS_SHORT[start.month-1]} -> filter tanggal "
                  "tunggal terpasang (OK)")
            return True
        if (end.month, end.year) != (start.month, start.year):
            if not self._navigate_calendar_to(end.month, end.year):
                self.tap_outside()
                return False
        end_cell = self._selectable_day_cell(end)
        if end_cell is not None:
            try:
                end_cell.click()
            except Exception:
                pass
            time.sleep(0.2)
        ok = self._confirm_calendar()
        print(f"[TANGGAL] rentang {start.day} {self.MONTHS_SHORT[start.month-1]}"
              f" - {end.day} {self.MONTHS_SHORT[end.month-1]} dipilih: {ok}")
        return ok

    def set_date_today(self):
        """
        Set filter tanggal ke HARI INI (tanggal entry sesuai aturan app:
        isi data hanya boleh hari ini/kemarin).
        """
        today = datetime.date.today()
        return self.set_date(today.day, today.month, today.year)

    def ensure_date_today(self):
        """
        Sesuai ALUR USER: jangan utak-atik tanggal dulu — langsung klik
        tambah. Kalender HANYA dibuka kalau filter tanggal sedang BUKAN
        hari ini (mis. sisa run sebelumnya memfilter 4 September), karena
        app memblokir tambah data kalau filter bukan hari ini/kemarin.
        Kalau filter SUDAH hari ini -> tidak buka kalender sama sekali.
        """
        today = datetime.date.today()
        try:
            btn = self.find(self.DATE_PICKER_BTN, timeout=3)
            desc = (btn.get_attribute("content-desc") or "").strip()
        except Exception:
            return False
        # filter RENTANG (mis. '21 Sep - 22 Sep 2026') -> BUKAN hari ini
        # -> samakan ke hari ini dulu (aturan app)
        if re.search(r"\d{1,2}\s+\w+\s*-\s*\d{1,2}\s+\w+", desc):
            return self.set_date_today()
        m = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", desc)
        if m:
            day = int(m.group(1))
            month_name = m.group(2)
            year = int(m.group(3))
            if (day == today.day and year == today.year
                    and month_name == self.MONTHS_ID[today.month - 1]):
                return True  # sudah hari ini -> langsung bisa tambah
        # filter bukan hari ini -> samakan dulu (aturan app)
        return self.set_date_today()

    def set_date(self, day: int, month: int, year: int):
        """Buka kalender, arahkan ke bulan yang diminta, tap tanggal, konfirmasi."""
        if not self._open_calendar():
            return False
        if not self._navigate_calendar_to(month, year):
            self.tap_outside()
            return False
        cell = self._day_cell(day, month, year)
        if cell is None:
            self.tap_outside()
            return False
        try:
            cell.click()
        except Exception:
            pass
        time.sleep(0.15)
        return self._confirm_calendar()

    # ----------------------------------------------------------------
    # Tambah data / form
    # ----------------------------------------------------------------
    def dismiss_permission_dialog(self):
        """Dialog izin Android (lokasi/notifikasi/dll) -> tap 'While using
        the app' / 'Allow' kalau muncul (terverifikasi di emulator).
        CEPAT (feedback user 22 Sep): SATU query gabungan utk semua
        label - sebelumnya 4 cek x 1 dtk = jeda 4 dtk SEBELUM mengisi
        form padahal dialog jarang muncul."""
        locator = (AppiumBy.XPATH,
                   '//*[@text="While using the app" or @text="Allow"'
                   ' or @text="Izinkan" or @text="ALLOW"]')
        if self.is_present(locator, timeout=1.5):
            try:
                self.tap(locator, timeout=2)
            except Exception:
                pass
            time.sleep(0.25)
            return True
        return False

    def open_add_form(self):
        """
        Tap FAB tambah data. Kalau FAB tidak ada -> False.
        Kalau muncul toast 'Tidak dapat menambah data' (tanggal bukan
        hari ini/kemarin) -> tutup toast & kembalikan False (SKIP).
        """
        fab = None
        for _ in range(6):  # FAB butuh waktu render setelah simpan/loading
            fab = self.find_fab()
            if fab is not None:
                break
            time.sleep(0.15)
        if fab is None:
            return False
        try:
            fab.click()
        except Exception:
            return False
        time.sleep(0.15)
        self.dismiss_permission_dialog()
        if self.is_present(self.BLOCK_TOAST, timeout=1.5):
            # tambah data diblokir app untuk tanggal ini -> SKIP
            self.tap_outside()
            time.sleep(0.25)
            return False
        return True

    # Tombol/control form yang JANGAN dianggap opsi dropdown: React Native
    # tidak meng-unmount layar di belakang modal, jadi tombol-tombol form
    # (Simpan, Tanggal, dst) tetap ada di tree bersamaan dengan opsi modal.
    _NON_OPTION_DESC_FRAGMENTS = (
        "Simpan", "Tanggal", "Kembali", "Batal", "OK", "Hapus",
        "Tambah", "Pilih", "Cari", "Beranda", "Apps", "Aktivitas",
        "Profil", "Keluar", "Masuk", "Lihat", "Ritase",
        "Kelola", "Fleet",  # tab bar / judul tab (bukan opsi dropdown)
    )
    # Pola label yang MURNI waktu saja (mis. sel time picker '14:55') -
    # JANGAN pakai pola waktu longgar: opsi shift sah mengandung jam
    # ('Shift 01 (07:00 s/d 19:00)') dan wajib TETAP bisa dipilih
    # (bug 22 Sep: pola longgar memfilter semua opsi shift -> field
    # malah dianggap tanpa opsi dan diketik di kotak cari).
    _PURE_TIME_PATTERN = re.compile(r"^\s*\d{1,2}:\d{2}\s*$")

    def _is_non_option_label(self, label: str):
        """True kalau label BUKAN opsi dropdown: fragmen tombol form
        (Simpan/Tanggal/dll) ATAU field datetime (ikon jam/kalender
        / - bukti dump status_pre_fill: field 'Waktu
        Mulai' clickable ikut terambil picker opsi -> malah membuka
        time picker) ATAU label yang isinya MURNI jam."""
        if any(frag.lower() in label.lower()
               for frag in self._NON_OPTION_DESC_FRAGMENTS):
            return True
        if "" in label or "" in label:  # ikon jam/kalender
            return True
        if self._PURE_TIME_PATTERN.search(label):
            return True
        # ikon FontAwesome MURNI (mis. panah back '' - bukti 23 Sep:
        # back arrow diklik sebagai 'opsi' -> alur nyasar ke Apps)
        if self._PUA_CHARS.fullmatch(label):
            return True
        # field datetime (ikon jam/kalender + jam, mis. ', 08:50, ' -
        # bukti 24 Sep: kandidat opsi palsu di form Tambah WP)
        if re.search(r"\d{1,2}:\d{2}", label) and self._PUA_CHARS.search(label):
            return True
        # pola tanggal = pill kalender / kartu entry list, BUKAN opsi
        if re.search(r"\d{1,2}\s+\w{3,9}\s+\d{4}", label):
            return True
        return False

    def _click_first_dropdown_option(self, placeholder: str, skip: int = 0,
                                     avoid: str = None):
        """Klik opsi dropdown PERTAMA yang visible & clickable.
        Pass 1: android.widget.Button ber-desc (pola umum). Pass 2
        (GANTI otomatis, bukan SKIP): kelas APA PUN yang clickable
        dengan desc/text terisi (opsi modal di app 2.5.15 bukan Button
        - bukti dump status_pre_fill) — tetap kecualikan field
        placeholder itu sendiri, tombol form di belakang modal, field
        datetime 'Waktu Mulai' (lihat _is_non_option_label), dan
        EDITEXT (kotak cari 'Cari <x>..' modal search-select BUKAN
        opsi - bukti 24 Sep: kotak cari diklik sebagai 'opsi' ->
        ekskavator tidak terisi, form ditolak app).
        `skip=N`: lewati N opsi pertama (untuk mencoba opsi BERIKUTNYA
        kalau opsi pertama ditolak app - ganti otomatis).
        `avoid=...`: lewati opsi yang labelnya mengandung teks itu
        (mis. avoid='Stop': WP berstatus Stop DITOLAK app saat simpan -
        bukti 24 Sep '10800000233 - Stop' gagal tersimpan)."""
        xpaths = (
            '//android.widget.Button[@content-desc!=""]',
            '//*[@clickable="true" and (@content-desc!="" or @text!="")]',
        )
        skipped = 0
        for xp in xpaths:
            try:
                options = self.driver.find_elements(AppiumBy.XPATH, xp)
            except Exception:
                continue
            for el in options:
                try:
                    if el.tag_name == "android.widget.EditText":
                        continue  # kotak cari modal, bukan opsi
                    desc = (el.get_attribute("content-desc") or "").strip()
                    txt = (el.get_attribute("text") or "").strip()
                except Exception:
                    continue
                label = f"{desc} {txt}".strip()
                if not label or label in ("null", "undefined"):
                    continue
                if placeholder and placeholder.lower() in label.lower():
                    continue  # field dropdown itu sendiri
                if avoid and avoid.lower() in label.lower():
                    continue  # opsi yang dihindari (mis. WP 'Stop')
                if self._is_non_option_label(label):
                    continue
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    if not el.is_displayed():
                        continue
                    if skipped < skip:
                        skipped += 1
                        continue
                    el.click()
                    time.sleep(0.15)
                    return True
                except Exception:
                    continue
        return False

    def _search_in_dropdown_modal(self, search_term: str):
        """Ketik `search_term` di kotak cari modal dropdown (mis.
        'Cari asal..'). Return True kalau berhasil mengetik."""
        try:
            boxes = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.EditText[contains(@hint,"Cari")'
                ' or contains(@text,"Cari")]',
            )
        except Exception:
            return False
        if not boxes:
            return False
        try:
            box = boxes[0]
            box.click()
            try:
                box.clear()
            except Exception:
                pass
            box.send_keys(search_term)
            time.sleep(0.25)
            return True
        except Exception:
            return False

    def _try_pick_first_option(self, placeholder: str, tries=6, skip: int = 0,
                               avoid: str = None):
        """Coba klik opsi dropdown PERTAMA beberapa kali (opsi butuh
        waktu render setelah modal/search). `skip=N` -> lewati N opsi
        pertama (coba opsi berikutnya kalau yang pertama ditolak app).
        `avoid=...` -> lewati opsi berlabel mengandung teks itu."""
        for _ in range(tries):
            if self._click_first_dropdown_option(placeholder, skip=skip,
                                                 avoid=avoid):
                return True
            time.sleep(0.2)
        return False

    def _dump_screen(self, name):
        """Simpan page_source ke scans/ sebagai bukti saat langkah gagal.
        TIDAK menimpa dump yang sudah ada (tambah suffix _1, _2, ...)
        supaya bukti dari beberapa menu dalam satu run tidak hilang."""
        try:
            import os
            os.makedirs("scans", exist_ok=True)
            base, ext = os.path.splitext(name)
            final, i = f"{name}{ext}", 1
            while os.path.exists(f"scans/{final}"):
                final = f"{base}_{i}{ext}"
                i += 1
            with open(f"scans/{final}", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"  [dump] scans/{final}")
        except Exception:
            pass

    def _modal_options_present(self):
        """True kalau ada opsi dropdown yang SUDAH tampil di layar.
        App 2.5.15: opsi modal BUKAN android.widget.Button (bukti dump
        status_pre_fill: 0 Button di tree) -> cek SEMUA clickable
        ber-label yang bukan tombol form / datetime di belakang modal."""
        try:
            options = self.driver.find_elements(
                AppiumBy.XPATH,
                '//*[@clickable="true" and (@content-desc!="" or @text!="")]',
            )
        except Exception:
            return False
        for el in options:
            try:
                desc = (el.get_attribute("content-desc") or "").strip()
                txt = (el.get_attribute("text") or "").strip()
                label = f"{desc} {txt}".strip()
                if not label or label in ("null", "undefined"):
                    continue
                if self._is_non_option_label(label):
                    continue
                if el.get_attribute("clickable") != "true":
                    continue
                if not el.is_displayed():
                    continue
                return True
            except Exception:
                continue
        return False

    def _modal_search_box_present(self):
        """True kalau kotak cari modal dropdown ('Cari <x>..') sudah tampil."""
        try:
            boxes = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.EditText[contains(@hint,"Cari")'
                ' or contains(@text,"Cari")]',
            )
        except Exception:
            return False
        for b in boxes:
            try:
                if b.is_displayed():
                    return True
            except Exception:
                continue
        return False

    def _wait_dropdown_modal(self, max_wait=6):
        """Tunggu modal dropdown benar-benar siap (opsi tampil ATAU kotak
        cari tampil). Polling cepat menggantikan sleep buta - modal RN
        butuh waktu load opsi, dan kalau tidak ditunggu, opsi terlewat
        lalu field dilaporkan 'tidak ada opsi' (SKIP) padahal ada."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            if self._modal_options_present() or self._modal_search_box_present():
                return True
            time.sleep(0.15)
        return False

    def select_dropdown_option(self, field_label: str, placeholder: str,
                               search_term: str = "Tayan",
                               scroll_hunt: bool = True,
                               allow_create_pile: bool = True,
                               option_skip: int = 0,
                               avoid: str = None):
        """
        Buka dropdown 'Pilih <x>' lalu klik opsi PERTAMA.
        Return status string:
          'ok'        -> opsi berhasil dipilih
          'no_field'  -> field tidak ada di tree saat ini (form tervirtualisasi,
                         caller boleh coba LAGI setelah scroll)
          'no_options'-> field ketemu & dibuka, tapi tidak ada opsi (SKIP)
        Modal SEARCH-SELECT: kalau opsi tidak muncul, ketik `search_term`
        di kotak 'Cari..' lalu pilih hasil pertama.
        `scroll_hunt=False` dipakai untuk form MODAL (bottom-sheet):
        kalau field tidak ada (sheet sudah tertutup), JANGAN scroll
        halaman di belakangnya (bukti 23 Sep: hunting malah membuka
        pencarian menu Apps) -> langsung kembalikan 'no_field'.
        CATATAN (terverifikasi scan dd_02/dd_03): saat modal dropdown
        TERBUKA, form di belakangnya HILANG dari tree - jadi kalau field
        tidak ketemu, cek dulu apakah modal sudah terbuka (jangan
        scroll-hunting sia-sia).
        """
        locator = (AppiumBy.XPATH, f'//*[contains(@content-desc,"{placeholder}")]')

        def _sudah_terisi():
            """Field dianggap TERISI kalau placeholder 'Pilih <x>'-nya
            sudah TIDAK ada di tree (desc field berubah jadi nilai -
            feedback user 23 Sep: 'ekskavatornya belum keisi') DAN
            form/sheet-nya TERLIHAT (EditText NON-'Cari' / Simpan ada di
            tree - bukti 24 Sep: (1) field di belakang modal yang masih
            terbuka ikut 'hilang' dari tree -> cek placeholder saja
            false-positive 'terisi' padahal kosong; (2) kotak cari modal
            'Cari <x>..' adalah EditText -> jangan dihitung sebagai
            'form terlihat')."""
            form_vis = (AppiumBy.XPATH,
                        '//android.widget.EditText'
                        '[not(contains(@text,"Cari"))'
                        ' and not(contains(@hint,"Cari"))]')
            for _ in range(4):
                if self.is_present(locator, timeout=1.0):
                    return False   # placeholder masih ada -> belum terisi
                if (self.is_present(self.BTN_SUBMIT, timeout=0.8)
                        or self.is_present(form_vis, timeout=0.8)):
                    return True    # form terlihat & placeholder hilang
                time.sleep(0.4)
            return False  # tidak bisa dipastikan -> anggap belum terisi

        # Kalau field tidak terlihat, kemungkinan modal dropdown SUDAH
        # terbuka (form di belakang modal tidak ada di tree) -> langsung
        # coba pilih opsi dulu.
        if not self.is_present(locator, timeout=1):
            if self._modal_options_present() or self._modal_search_box_present():
                if (self._try_pick_first_option(placeholder, tries=8)
                        and _sudah_terisi()):
                    print(f"[DROPDOWN] '{field_label}': modal sudah terbuka -> opsi pertama dipilih")
                    return "ok"
                # modal NYASAR (bukan milik field ini - pick tidak
                # mengisi field) -> tutup dengan tap netral, lalu lanjut
                # alur tap field biasa di bawah (BUKAN back: back bisa
                # menutup sheet/form - bukti 23 Sep)
                print(f"[DROPDOWN] '{field_label}': modal nyasar -> tutup netral dulu")
                self.tap_outside()
                time.sleep(0.2)
            if not self.is_present(locator, timeout=1.5):
                if not scroll_hunt:
                    print(f"[DROPDOWN] '{field_label}': field tidak ada (modal) -> tanpa scroll-hunting")
                    return "no_field"
                found = False
                for _ in range(8):
                    self._small_scroll_down(wait=0.3)
                    if self.is_present(locator, timeout=1):
                        found = True
                        break
                if not found:
                    print(f"[DROPDOWN] '{field_label}': field belum ter-render -> COBA LAGI")
                    return "no_field"
        # Field di TEPI BAWAH layar (y > 85% tinggi) tap-nya sering
        # tertelan FlatList/tepi -> modal tidak pernah terbuka (bukti
        # run 18 Sep: ekskavator/dumptruck gagal saat y~1926/2220,
        # sukses di posisi lebih tinggi). Geser form sedikit supaya
        # field naik ke area aman SEBELUM tap.
        try:
            el = self.driver.find_element(*locator)
            h = self.driver.get_window_size()["height"]
            if (el.is_displayed()
                    and el.location["y"] + el.size["height"] / 2 > h * 0.85):
                self._small_scroll_down(wait=0.35)
        except Exception:
            pass
        try:
            self.tap(locator, timeout=3)
        except Exception:
            return "no_field"
        # TUNGGU modal siap (opsi ter-load), baru coba pilih.
        self._wait_dropdown_modal(max_wait=6)
        if "dumptruck" in placeholder.lower():
            # bukti 24 Sep: dump ISI MODAL dumptruck (kenapa pilihannya
            # tidak pernah menempel di field seksi Tambah Unit/Alat)
            self._dump_screen("auto_dt_modal_open")
        if not (self._modal_options_present() or self._modal_search_box_present()):
            # modal ternyata tidak terbuka -> dump bukti, tap ulang field sekali
            self._dump_screen("dd_modal_missing")
            try:
                self.tap(locator, timeout=3)
                self._wait_dropdown_modal(max_wait=6)
            except Exception:
                pass

        # 1) opsi langsung muncul -> klik yang pertama
        if self._try_pick_first_option(placeholder, tries=8, skip=option_skip,
                                       avoid=avoid):
            if _sudah_terisi():
                print(f"[DROPDOWN] '{field_label}' -> opsi pertama dipilih")
                return "ok"
            # pilihan DI-RESET app (opsi ditolak, mis. dumptruck sudah
            # dipakai unit lain - bukti 24 Sep) -> GANTI otomatis: buka
            # ulang modal field ini lalu coba opsi BERIKUTNYA
            print(f"[DROPDOWN] '{field_label}': pilihan di-reset app -> coba opsi berikutnya")
            try:
                self.tap(locator, timeout=3)
                self._wait_dropdown_modal(max_wait=6)
            except Exception:
                pass
            if self._try_pick_first_option(placeholder, tries=6, skip=1,
                                           avoid=avoid):
                if _sudah_terisi():
                    print(f"[DROPDOWN] '{field_label}' -> opsi berikutnya dipilih (ganti otomatis)")
                    return "ok"

        # 2) modal search-select: ketik kata kunci -> pilih hasil pertama
        if search_term and self._search_in_dropdown_modal(search_term):
            self._wait_dropdown_modal(max_wait=3)
            if self._try_pick_first_option(placeholder, tries=8) and _sudah_terisi():
                print(f"[DROPDOWN] '{field_label}' -> opsi dipilih "
                      f"(cari '{search_term}')")
                return "ok"

        # 3) dropdown KODE TUMPUKAN tanpa opsi -> GANTI otomatis: buat
        # kode tumpukan BARU lewat 'Tambahkan Kode Tumpukan' di modal
        # (alur user 23 Sep: kode tumpukan Feeding wajib jalan - bukan
        # SKIP). Modal masih terbuka di sini. `allow_create_pile=False`
        # dipakai di dalam dialog kode itu sendiri (jangan buat rekursif).
        if "kode tumpukan" in placeholder.lower() and allow_create_pile:
            if self._create_new_pile_in_dropdown():
                print(f"[DROPDOWN] '{field_label}': kode tumpukan BARU "
                      "dibuat (ganti otomatis)")
                return "ok"

        # tetap tidak ada opsi -> dump bukti, tutup modal netral, SKIP
        print(f"[DROPDOWN] '{field_label}': tidak ada opsi tersedia -> SKIP")
        self._dump_screen(f"auto_dropdown_fail_{field_label.replace(' ', '_').replace('/', '_')}")
        self.tap_outside()
        time.sleep(0.15)
        return "no_options"

    def _first_fillable_y(self):
        """Y terkecil dari field isian yang sedang ter-render (buat
        deteksi apakah form masih bisa di-scroll / sudah mentok bawah)."""
        ys = []
        try:
            els = self.driver.find_elements(
                AppiumBy.XPATH, '//android.widget.EditText[contains(@text,"Ketik")]'
            )
            ys += [el.location["y"] for el in els]
        except Exception:
            pass
        try:
            els = self.driver.find_elements(
                AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih ")]'
            )
            ys += [el.location["y"] for el in els]
        except Exception:
            pass
        return min(ys) if ys else None

    def scroll_form_to_top(self, max_swipes=8):
        """
        Kembalikan form ke posisi PALING ATAS (sesuai alur user: isi dari
        awal dulu, baru boleh scroll ke bawah). Berhenti begitu field
        'Pilih <x>' paling atas sudah terlihat (y < 40% tinggi layar).
        """
        for _ in range(max_swipes):
            try:
                els = self.driver.find_elements(
                    AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih ")]'
                )
                ys = []
                for e in els[:10]:
                    try:
                        ys.append(e.location["y"])
                    except Exception:
                        pass
                h = self.driver.get_window_size()["height"]
                if ys and min(ys) < h * 0.4:
                    return True  # sudah di atas form
            except Exception:
                pass
            self.swipe("up", pause=0.2)
        return True

    def _ensure_field_visible(self, locator, max_scrolls=8):
        """
        Form OPEL panjang & tervirtualisasi: field di bawah lipatan TIDAK
        ada di tree sampai di-scroll. Asumsi: pengisian mulai dari ATAS
        form (lihat scroll_form_to_top), jadi pencarian cukup scroll ke
        BAWAH sampai locator muncul dan posisinya nyaman di layar.
        BERHENTI kalau form sudah mentok supaya field yang memang tidak
        ada tidak membuat scroll tanpa akhir.
        """
        if self.is_present(locator, timeout=2):
            found = True
        else:
            found = False
            for _ in range(max_scrolls):
                before = self._first_fillable_y()
                self.scroll_down(times=1, pause=0.2)
                if self.is_present(locator, timeout=2):
                    found = True
                    break
                after = self._first_fillable_y()
                if before is not None and after == before:
                    break  # sudah mentok bawah / tidak ada field baru
        if not found:
            return False
        # posisikan nyaman: tidak mepet tepi atas/bawah layar
        try:
            size = self.driver.get_window_size()
            for _ in range(5):
                el = self.find(locator, timeout=2)
                y = el.location["y"]
                if y < size["height"] * 0.2:
                    self.swipe("up", pause=0.2)    # terlalu atas -> geser turun
                elif y > size["height"] * 0.8:
                    self.scroll_down(times=1, pause=0.2)  # terlalu bawah
                else:
                    break
        except Exception:
            pass
        return True

    def _small_scroll_down(self, wait=0.3):
        """Scroll KECIL (setengah layar) supaya field di bawah lipatan
        tidak kelewat (scroll penuh bisa melompati field). `wait` penting
        karena form tervirtualisasi: field baru butuh waktu untuk
        ter-render setelah scroll.
        POSISI MULAI SWIPE (akar masalah 24 Sep): mulai dari 0.5H sering
        TERTELAN elemen interaktif yang kebetulan ada di titik itu
        (field dropdown terakhir / baris tombol status per-unit) ->
        form TIDAK scroll, Simpan/Tambah Dumptruck tak pernah muncul.
        Keyboard terbuka juga menelan swipe dari 0.65H. Jadi: kalau
        keyboard terbuka -> mulai 0.45H (area form di atas keyboard);
        kalau tidak -> mulai 0.65H (di bawah field, area kosong)."""
        try:
            kb = self.driver.is_keyboard_shown()
        except Exception:
            kb = False
        size = self.driver.get_window_size()
        x = size["width"] // 2
        start = 0.45 if kb else 0.65
        self.driver.swipe(x, int(size["height"] * start),
                          x, int(size["height"] * (start - 0.35)), 200)
        time.sleep(wait)

    _PUA_CHARS = re.compile("[-]")  # ikon FontAwesome (private use area)

    def _label_for_edittext(self, el):
        """
        Label field untuk sebuah EditText = TextView TERDEKAT di ATAS-nya
        (berdasar bounds/posisi layar). Ini jauh lebih andal daripada
        urutan tree (`preceding::`), karena di React Native TextView
        placeholder dropdown tetangga sering berada di antara label
        dan input, sehingga label ketukar dengan placeholder ('Pilih
        lokasi' dianggap label 'Deskripsi Lokasi', dsb).
        """
        try:
            ey = el.location["y"]
        except Exception:
            return ""
        try:
            texts = self.driver.find_elements(AppiumBy.XPATH,
                                              "//android.widget.TextView")
        except Exception:
            return ""
        best, best_bottom = "", None
        for t in texts:
            try:
                txt = (t.get_attribute("text") or "").strip()
                cleaned = self._PUA_CHARS.sub("", txt).strip()
                if len(cleaned) < 2:
                    continue
                if not t.is_displayed():
                    continue
                ty = t.location["y"]
                bottom = ty + t.size["height"]
                if bottom > ey + 8:      # harus di ATAS input
                    continue
                if ey - bottom > 180:    # jangan terlalu jauh di atas
                    continue
                if best_bottom is None or bottom > best_bottom:
                    best, best_bottom = cleaned, bottom
            except Exception:
                continue
        return best

    def _visible_fillables(self):
        """Field isian yang terlihat sekarang: [(kind, payload, y)].
        kind 'dd' -> payload = content-desc; kind 'text' -> payload =
        label field."""
        items = []
        try:
            dd_els = self.driver.find_elements(
                AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih ")]'
            )
        except Exception:
            dd_els = []
        for el in dd_els:
            try:
                desc = (el.get_attribute("content-desc") or "").strip()
                if not desc:
                    continue
                items.append(("dd", desc, el.location["y"]))
            except Exception:
                continue
        try:
            edits = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.EditText[contains(@text,"Ketik")'
                ' or contains(@text,"Tulis")]',
            )
        except Exception:
            edits = []
        for el in edits:
            try:
                y = el.location["y"]
            except Exception:
                continue
            label = self._label_for_edittext(el)
            if not label:
                continue
            items.append(("text", label, y))
        return items

    def _fillable_signature(self):
        """Snapshot field yang terlihat (posisi dikuantisasi 60px) untuk
        mendeteksi apakah scroll benar-benar memajukan form."""
        sig = []
        for kind, payload, y in self._visible_fillables():
            sig.append((kind, payload, y // 60))
        return tuple(sorted(sig, key=lambda t: t[2]))

    def _dismiss_keyboard_soft(self):
        """Tutup keyboard TANPA back-press. `hide_keyboard()` Appium di
        Android menekan tombol BACK -> pada bottom-sheet RN justru
        MENUTUP SHEET (bukti run 22 Sep: sheet Standby hilang dari tree
        setelah isi Deskripsi) dan pada FORM FULL-PAGE ikut menutup
        form (bukti 23 Sep: form Feeding hilang setelah isi Jarak ->
        alur nyasar ke Apps). Gantinya: tap TextView PALING ATAS di
        area tengah-atas layar (DI DALAM sheet/form, netral) - RN
        Android menutup keyboard saat tap di luar EditText dan tap
        diteruskan tanpa efek lain. TextView yang TERTUTUP elemen
        clickable di titiknya DILEWATI (tap-nya bisa memicu field
        dropdown/back)."""
        # CEPAT (feedback user 24 Sep: 'lama banget isi Jarak'): versi lama
        # tanya lokasi/size SATU-SATU ke Appium (ratusan round-trip ->
        # puluhan detik). Versi ini parse SATU dump page_source lalu pilih
        # titik tap dari bounds-nya (1 request saja, < 1 detik).
        try:
            h = self.driver.get_window_size()["height"]
            src = self.driver.page_source
        except Exception:
            return False
        texts, boxes = [], []
        for m in re.finditer(r'<([\w.]+)\s([^>]*?)/?>', src):
            attrs = m.group(2)
            bnd = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
            if not bnd:
                continue
            x0, y0, x1, y1 = (int(v) for v in bnd.groups())
            if re.search(r'clickable="true"', attrs):
                boxes.append((x0, y0, x1 - x0, y1 - y0))
            if m.group(1) != "android.widget.TextView":
                continue
            t = re.search(r'text="([^"]*)"', attrs)
            if not t or not t.group(1).strip():
                continue
            txt = t.group(1).strip()
            if len(txt) > 30:
                continue
            texts.append((txt, x0, y0, x1, y1))
        best, best_y = None, None
        for _, x0, y0, x1, y1 in texts:
            if not (h * 0.3 < y0 < h * 0.65):
                continue
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            covered = any(bx <= cx <= bx + bw and by <= cy <= by + bh
                          for bx, by, bw, bh in boxes)
            if covered:
                continue
            if best_y is None or y0 < best_y:
                best, best_y = (cx, cy), y0
        if best is not None:
            try:
                self.driver.tap([best], 50)
                return True
            except Exception:
                pass
        return False

    def _fill_edittext_by_label(self, label: str, dummy_values,
                                dismiss_keyboard=True):
        """
        Isi EditText 'Ketik disini..' milik field berlabel `label`.
        Label DI-RESOLVE ULANG dari posisi layar tepat sebelum mengisi
        (indeks tree bisa bergeser setelah modal dropdown buka/tutup).
        `dismiss_keyboard=False` dipakai untuk form MODAL (bottom-sheet):
        tutup keyboard lewat tap netral judul sheet, BUKAN hide_keyboard
        (back-press menutup sheet).
        Return:
          True/False -> sudah DICOBA (sukses/gagal)
          None       -> EditText belum ter-render (virtualisasi) -> coba
                       lagi setelah scroll.
        """
        import random
        try:
            edits = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.widget.EditText[contains(@text,"Ketik")'
                ' or contains(@text,"Tulis")]',
            )
        except Exception:
            return None
        if not edits:
            return None
        target = None
        for el in edits:
            lbl = self._label_for_edittext(el)
            if not lbl:
                continue
            if (lbl.lower() == label.lower()
                    or label.lower() in lbl.lower()
                    or lbl.lower() in label.lower()):
                target = el
                break
        if target is None:
            return None
        value = None
        if isinstance(dummy_values, dict):
            for k2, val in dummy_values.items():
                if k2.lower() in label.lower():
                    value = val
                    break
        if value is None:
            value = (random.randint(10, 500)
                     if ("jarak" in label.lower() or "m)" in label
                         or "bucket" in label.lower())
                     else f"TEST-{random.randint(100, 999)}")
        try:
            target.click()
            try:
                target.clear()
            except Exception:
                pass
            target.send_keys(str(value))
            if dismiss_keyboard:
                try:
                    self.driver.hide_keyboard()
                except Exception:
                    pass
            else:
                self._dismiss_keyboard_soft()
            print(f"[FORM] '{label}': OK {value}")
            return True
        except Exception:
            return False

    def _fill_visible_form_topdown(self, dummy_values: dict,
                                   expected_placeholders=None,
                                   search_by_placeholder=None):
        """
        CORE pengisian form:
        - Isi field yang TERLIHAT, urut dari yang PALING ATAS.
        - Field yang belum ter-render (FlatList tervirtualisasi) TIDAK
          langsung di-SKIP: ditandai 'coba lagi' dan diulang setelah
          scroll kecil sampai field benar-benar muncul.
        - Dropdown 'Pilih <x>' -> klik lalu pilih opsi pertama; kalau
          modalnya search-select, ketik kata kunci dari
          `search_by_placeholder` (fallback 'Tayan').
        - Berhenti kalau SEMUA field yang diharapkan sudah diproses,
          atau form terbukti mentok (3 scroll tanpa perubahan, maks
          2 sweep atas-ke-bawah).
        """
        results = {}
        processed = set()   # sudah DICOBA benar-benar (sukses/gagal final)
        attempts = {}       # key -> jumlah gagal sementara
        expected = list(expected_placeholders or [])
        search_by_placeholder = search_by_placeholder or {}

        # Guard posisi: kalau form terbuka dalam keadaan ke-scroll (sisa
        # run sebelumnya) dan tidak ada field 'Pilih <x>' di 1/3 atas
        # layar, geser ke ATAS dulu supaya field paling atas tidak
        # kelewat. Kalau form sudah di atas -> TANPA scroll sama sekali.
        # Form tanpa dropdown (form status) dianggap sudah OK begitu
        # EditText-nya terlihat (jangan scroll layar di belakangnya).
        for _ in range(4):
            try:
                dd = self.driver.find_elements(
                    AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih ")]'
                )
                edits = self.driver.find_elements(
                    AppiumBy.XPATH,
                    '//android.widget.EditText[contains(@text,"Ketik")]',
                )
                h = self.driver.get_window_size()["height"]
                ys = [e.location["y"] for e in dd[:8]]
                if ys and min(ys) < h * 0.35:
                    break  # dropdown paling atas sudah terlihat -> posisi OK
                if not ys and edits:
                    break  # form tanpa dropdown (status) sudah terlihat -> OK
            except Exception:
                pass
            self.swipe("up", pause=0.15)

        def _search_for(desc):
            for ph, term in search_by_placeholder.items():
                if ph.lower() in desc.lower():
                    return term
            return "Tayan"

        no_progress = 0
        sweeps = 0
        while True:
            # 1) isi semua field yang terlihat & belum diproses,
            #    urut dari yang paling atas
            todo = sorted(self._visible_fillables(), key=lambda t: t[2])
            for kind, payload, _ in todo:
                key = payload
                if key in processed:
                    continue
                if attempts.get(key, 0) >= 5:
                    processed.add(key)   # sudah dicoba berkali-kali -> selesai
                    results[key] = False
                    print(f"[FORM] '{key}': gagal berulang kali -> SKIP")
                    continue
                if kind == "dd":
                    desc = payload
                    status = self.select_dropdown_option(
                        desc, desc, search_term=_search_for(desc)
                    )
                    if status == "ok":
                        processed.add(desc)
                        results[desc] = True
                        attempts[desc] = 0
                    elif status == "no_field":
                        attempts[desc] = attempts.get(desc, 0) + 1
                        # field belum ter-render -> JANGAN di-skip,
                        # diulang setelah scroll
                    else:  # no_options: field ketemu tapi kosong
                        attempts[desc] = attempts.get(desc, 0) + 1
                        if attempts[desc] >= 2:
                            processed.add(desc)
                            results[desc] = False
                else:
                    label = payload
                    # dismiss_keyboard=False: tap netral, BUKAN
                    # hide_keyboard (back menutup form full-page juga -
                    # bukti 23 Sep: form Feeding hilang setelah isi
                    # Jarak -> alur nyasar ke Apps)
                    ok = self._fill_edittext_by_label(
                        label, dummy_values, dismiss_keyboard=False)
                    if ok is None:
                        attempts[label] = attempts.get(label, 0) + 1
                    else:
                        processed.add(label)
                        results[label] = ok
                        attempts[label] = 0

            # 2) semua field yang DIHARAPKAN sudah diproses -> selesai
            if expected and all(
                any(ph.lower() in str(k).lower() for k in processed)
                for ph in expected
            ):
                break

            # 3) belum -> scroll kecil, cek apakah form benar-benar maju
            before = self._fillable_signature()
            self._small_scroll_down()
            after = self._fillable_signature()
            if before == after:
                no_progress += 1
                if no_progress >= 3:
                    # mentok bawah: kalau masih ada field yang belum
                    # diproses, sweep SEKALI lagi dari atas (modal
                    # dropdown kadang menggeser scroll form)
                    sweeps += 1
                    if sweeps >= 3:
                        break
                    self.scroll_form_to_top()
                    no_progress = 0
            else:
                no_progress = 0
        # sisa field yang DIHARAPKAN tapi belum diproses -> catat + dump
        # (bukti 23 Sep: feeding berhenti di Ekskavator, kode tumpukan &
        # dumptruck hilang diam-diam -> Simpan tak pernah ketemu)
        if expected:
            unprocessed = [
                ph for ph in expected
                if not any(ph.lower() in str(k).lower() for k in processed)
            ]
            if unprocessed:
                print(f"[FORM] sisa field belum diproses: {unprocessed}")
                self._dump_screen("auto_form_sisa")
        return results

    def _dropdown_already_filled(self, label: str):
        """
        True kalau dropdown berlabel `label` SUDAH terisi otomatis oleh
        app sehingga placeholder-nya tidak ada lagi (desc field jadi
        nilai terpilih, mis. ', Ore Getting' - terverifikasi: field
        'Jenis Kegiatan' terisi default oleh app). Deteksi: TextView
        ber-label `label` + clickable view terdekat DI BAWAH-nya yang
        desc-nya mengandung ',' dan BUKAN 'Pilih <x>'.
        """
        try:
            labs = self.driver.find_elements(
                AppiumBy.XPATH, f'//*[@text="{label}"]')
        except Exception:
            return False
        for lab in labs:
            try:
                if not lab.is_displayed():
                    continue
                ly = lab.location["y"] + lab.size["height"]
                views = self.driver.find_elements(
                    AppiumBy.XPATH,
                    '//*[contains(@content-desc,",") and @clickable="true"]')
                best, best_d = None, None
                for v in views:
                    try:
                        if not v.is_displayed():
                            continue
                        vy = v.location["y"]
                    except Exception:
                        continue
                    if vy < ly:
                        continue
                    d = vy - ly
                    if best_d is None or d < best_d:
                        best, best_d = v, d
                if best is not None and best_d is not None and best_d < 300:
                    desc = (best.get_attribute("content-desc") or "").strip()
                    if desc and "Pilih" not in desc:
                        return True
            except Exception:
                continue
        return False

    def fill_form_fields(self, fields: list, dummy_values: dict):
        """
        Isi form URUT ATAS-KE-BAWAH tanpa scroll awal (sesuai masukan
        user: field paling atas langsung diisi supaya tidak kelewat).
        Loop TIDAK berhenti sebelum semua field di `fields` sudah
        diproses (atau form terbukti mentok). Field yang datanya tidak
        tersedia -> SKIP (defensif).
        """
        # dropdown yang SUDAH terisi otomatis app TIDAK dimasukkan ke
        # expected -> loop tidak scroll-sweep percuma (percepat pengisian)
        expected = [
            f.get("placeholder", f["label"])
            for f in fields
            if f["type"] == "dropdown"
            and not self._dropdown_already_filled(f["label"])
        ]
        expected += [f["label"] for f in fields if f["type"] == "text"]
        # kata kunci pencarian per dropdown (modal search-select)
        search_by_placeholder = {
            f.get("placeholder", f["label"]): f.get("search", "Tayan")
            for f in fields if f["type"] == "dropdown"
        }
        results = self._fill_visible_form_topdown(
            dummy_values or {}, expected, search_by_placeholder
        )
        # VERIFIKASI PASCA-ISI (feedback user 24 Sep: 'kode tumpukannya
        # belum keisi udah main simpan aja'): placeholder 'Pilih <x>'
        # yang MASIH ada di tree -> isi ulang (maks 2 ronde) SEBELUM
        # tombol Simpan di-tap. CEPAT: cek SEMUA placeholder dari SATU
        # page_source (versi lama is_present satu-satu = detik per field).
        for ronde in range(2):
            try:
                src = self.driver.page_source
            except Exception:
                break
            still = [ph for ph in expected
                     if "Pilih " in ph and ph in src]
            if not still:
                break
            print(f"[FORM] field masih kosong sebelum Simpan: {still}"
                  f" -> isi ulang (ronde {ronde+1})")
            for ph in still:
                self.select_dropdown_option(
                    ph, ph,
                    search_term=search_by_placeholder.get(ph, "Tayan"),
                )
        # JANGAN scroll form ke atas lagi (feedback user 22 Sep): form
        # yang selesai diisi otomatis berhenti di BAWAH (tempat tombol
        # Simpan) -> submit() langsung bisa tap tanpa scroll ke bawah
        # ulang. Hasil per-field tidak dipakai caller (semua page hanya
        # memanggil tanpa mengambil return).
        return results

    def fill_form_dynamically(self, dummy_values: dict):
        """
        Fallback untuk halaman yang field-nya belum terverifikasi semua
        (mis. Feeding WP / form status): scan form yang terbuka lalu isi
        urut atas-ke-bawah (dropdown -> pilih opsi pertama; teks ->
        dummy). Tanpa scroll awal, jeda minimal.
        """
        self._fill_visible_form_topdown(dummy_values)
        return True

    def _scroll_to(self, locator, max_scrolls=12):
        """
        Scroll KECIL ke bawah sampai ada elemen `locator` yang visible
        pada posisi nyaman di layar (0.1H - 0.8H). Kembalikan element
        atau None. Dipakai di halaman Detail (FlatList tervirtualisasi:
        tombol di bawah lipatan TIDAK ada di tree sebelum di-scroll).
        GUARD (feedback user 23 Sep: 'kenapa ngescroll ke bawah lagi
        sampai bawah app'): kalau dialog/loading menutupi layar,
        selesaikan DULU - JANGAN scroll buta di belakangnya."""
        self.wait_loading_done(max_wait=3)
        if self.handle_confirm_dialog(confirm=True, timeout=0.8):
            print("[SCROLL] dialog menutupi layar -> dikonfirmasi dulu, baru scroll")
            time.sleep(0.15)
        for _ in range(max_scrolls):
            try:
                els = self.driver.find_elements(*locator)
                h = self.driver.get_window_size()["height"]
                for el in els:
                    try:
                        if not el.is_displayed():
                            continue
                        y = el.location["y"]
                        if h * 0.08 <= y <= h * 0.8:
                            return el
                    except Exception:
                        continue
            except Exception:
                pass
            self._small_scroll_down(wait=0.25)
        return None

    def submit(self):
        """Tap tombol Simpan kalau tersedia. Kembalikan True kalau di-tap.
        CEPAT (feedback user 22 Sep): begitu Simpan ada di tree langsung
        tap, TANPA tunggu posisi 'nyaman' di layar. Simpan ada di BAWAH
        form (FlatList tervirtualisasi): kalau belum ter-render, scroll
        KECIL cepat ke bawah sampai muncul - JANGAN langsung SKIP (kalau
        tidak di-tap, data tidak tersimpan). DEFENSIF: race condition
        (tombol tertutup overlay loading/dialog) tidak boleh mematikan
        test -> False + SKIP."""
        if self.tap(self.BTN_SUBMIT, timeout=1.5) is not None:
            time.sleep(0.15)
            return True
        # keyboard mungkin masih terbuka (swipe tertelan keyboard -
        # bukti 24 Sep) -> tutup netral dulu, baru scroll-hunting Simpan
        self._dismiss_keyboard_soft()
        for _ in range(8):
            if self.is_present(self.BTN_SUBMIT, timeout=0.5):
                if self.tap(self.BTN_SUBMIT, timeout=1) is not None:
                    time.sleep(0.15)
                    return True
            self._small_scroll_down(wait=0.15)
        # RONDE 2 (bukti auto_submit_fail 24 Sep): FlatList form bisa
        # MACET - tree berhenti di field terakhir dan Simpan TIDAK
        # PERNAH di-render walau di-scroll. Form RE-MOUNT penuh setiap
        # modal dropdown buka-tutup (form di belakang modal HILANG dari
        # tree lalu muncul lagi) -> paksa buka-tutup dropdown TERBAWAH
        # supaya list re-render lengkap termasuk Simpan.
        try:
            els = self.driver.find_elements(
                AppiumBy.XPATH,
                '//*[@clickable="true" and contains(@content-desc,",")]')
            vis = [e for e in els if e.is_displayed()]
            if vis:
                vis.sort(key=lambda e: e.location["y"], reverse=True)
                vis[0].click()
                self._wait_dropdown_modal(max_wait=4)
                self.tap_outside()
                time.sleep(0.3)
        except Exception:
            pass
        # RONDE 3: geser form ke ATAS dulu (re-render isi list) lalu
        # sweep ke bawah LAGI sampai Simpan benar-benar muncul. Jangan
        # menyerah: kalau Simpan tidak di-tap, data tidak tersimpan
        # (feedback user: no SKIP).
        self.scroll_form_to_top(max_swipes=6)
        self._dismiss_keyboard_soft()
        for _ in range(12):
            if self.is_present(self.BTN_SUBMIT, timeout=0.5):
                if self.tap(self.BTN_SUBMIT, timeout=1) is not None:
                    time.sleep(0.15)
                    return True
            self._small_scroll_down(wait=0.15)
        print("[FORM] tombol 'Simpan' tidak ditemukan sampai bawah form -> SKIP")
        self._dump_screen("auto_submit_fail")  # bukti: kondisi form saat ini
        return False

    def submit_or_confirm(self, scroll=True):
        """Tap 'Simpan' kalau ada; kalau TIDAK ada, tap tombol 'OK'
        (mini form/dialog bottom sheet OPEL sering disimpan lewat tombol
        OK Batal/OK, BUKAN Simpan - bukti dump auto_pile_form_fail: dialog
        'Apakah Anda yakin ingin menambah ritase ...?'). GANTI otomatis,
        bukan SKIP. `scroll=False` untuk form MODAL: sweep scroll menutup
        modal (pola bug form status run #2)."""
        if self.is_present(self.BTN_SUBMIT, timeout=1):
            if self.tap(self.BTN_SUBMIT, timeout=2) is not None:
                time.sleep(0.15)
                return True
        if scroll and self._scroll_to(self.BTN_SUBMIT, max_scrolls=6) is not None:
            if self.tap(self.BTN_SUBMIT, timeout=2) is not None:
                time.sleep(0.15)
                return True
        if self.handle_confirm_dialog(confirm=True, timeout=1.5):
            print("[FORM] disimpan via tombol OK (ganti otomatis dari Simpan)")
            return True
        return False

    def _tap_simpan_or_ok(self, max_wait=6):
        """Tap tombol 'Simpan' pada form MODAL TANPA swipe sama sekali.
        Sweep pada modal bottom-sheet RN menyeret/menutup sheet (bukti
        run 22 Sep: submit() yang scroll malah MENUTUP form Standby
        lalu dump hanya menampilkan Detail di belakangnya). Polling
        cepat menunggu Simpan muncul di tree (form bisa re-mount
        setelah modal dropdown buka/tutup). Fallback: tombol OK dialog."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            if self.is_present(self.BTN_SUBMIT, timeout=1):
                if self.tap(self.BTN_SUBMIT, timeout=2) is not None:
                    time.sleep(0.15)
                    return True
            time.sleep(0.2)
        self._dump_screen("status_no_simpan")  # bukti tree saat Simpan hilang
        if self.handle_confirm_dialog(confirm=True, timeout=1.5):
            print("[FORM] disimpan via tombol OK (ganti otomatis dari Simpan)")
            return True
        return False

    def _wait_menit_berbeda(self):
        """ALUR USER (23 Sep): form dengan 'Waktu Mulai' (Standby, Tambah
        WP, status) TIDAK BOLEH SEMENIT dengan 'waktu kegiatan terakhir'
        entry - app MENOLAK simpan. Tunggu pergantian menit sejak Detail
        dibuka (maks ~1 menit; tanpa jeda kalau sudah beda menit)."""
        t0 = getattr(self, "_detail_opened_at", 0)
        if t0:
            while time.time() // 60 <= t0 // 60:
                time.sleep(1)

    def _fill_pile_code(self, value):
        """Isi dialog kode tumpukan. PRIORITAS DROPDOWN (feedback user
        23 Sep: 'kode tumpukan asal ngapain diketik kalo bisa di
        dropdown' - ketik kode asal bisa ngestuck karena tidak match
        format/kode tidak terdaftar): kalau ada field dropdown kode
        tumpukan -> PILIH opsi pertama (opsi 'Tambahkan Kode Tumpukan'
        ikut terpilih kalau jadi opsi pertama di modal). Ketik EditText
        HANYA kalau tidak ada dropdown sama sekali."""
        dd_loc = (AppiumBy.XPATH,
                  '//*[contains(@content-desc,"kode tumpukan")'
                  ' or contains(@content-desc,"Kode Tumpukan")]')
        if self.is_present(dd_loc, timeout=1):
            self.select_dropdown_option("Kode Tumpukan", "kode tumpukan",
                                        search_term=None,
                                        scroll_hunt=False,
                                        allow_create_pile=False)
            # dropdown kode sudah dipilih -> kategori/dropdown lain
            # di dialog tetap diisi opsi pertama (gentle, tanpa ketik)
            self._fill_status_form_gentle({"Kode": value})
            return
        # tidak ada dropdown -> field kategori + EditText kode (fallback)
        self._fill_status_form_gentle({"Kode": value})
        try:
            edits = self.driver.find_elements(
                AppiumBy.XPATH, '//android.widget.EditText')
        except Exception:
            return
        for e in edits:
            try:
                if not e.is_displayed():
                    continue
                if value in (e.get_attribute("text") or ""):
                    return  # sudah terisi
            except Exception:
                continue
        for e in edits:
            try:
                if not e.is_displayed():
                    continue
                e.click()
                try:
                    e.clear()
                except Exception:
                    pass
                e.send_keys(value)
                try:
                    self.driver.hide_keyboard()
                except Exception:
                    pass
                return
            except Exception:
                continue

    def _expand_dumptruck_row(self):
        """GANTI otomatis: tap baris 'Dumptruck - ...' di Detail untuk
        me-expand bagiannya (field Bucket/tumpukan kadang baru ter-render
        setelah baris di-expand - bukti dump auto_ritase_fail Supply:
        baris clickable tanpa Bucket). Kalau tap membuka halaman lain,
        balik ke Detail."""
        for xp in (
            '//*[contains(@content-desc,"Dumptruck -") and @clickable="true"]',
            '//*[contains(@text,"Dumptruck -") and @clickable="true"]',
        ):
            try:
                els = self.driver.find_elements(AppiumBy.XPATH, xp)
            except Exception:
                continue
            for el in els[:6]:
                try:
                    if not el.is_displayed():
                        continue
                    el.click()
                    time.sleep(0.2)
                    # kalau tap membuka halaman lain -> kembali ke Detail
                    if not (self.is_present(self.DETAIL_HEADER, timeout=1)
                            or self.is_present(self.BTN_LOG_PERGERAKAN, timeout=1)):
                        try:
                            self.driver.back()
                        except Exception:
                            pass
                        time.sleep(0.2)
                    return True
                except Exception:
                    continue
        return False

    def _ensure_on_detail(self):
        """Pastikan halaman Detail terbuka sebelum aksi tombol status.
        Bukti run #3 (dump auto_selesai_fail 3.1): alur bisa nyasar ke
        halaman LIST -> GANTI otomatis: buka ulang entry teratas (bukan
        SKIP)."""
        if (self.is_present(self.DETAIL_HEADER, timeout=2)
                or self.is_present(self.BTN_LOG_PERGERAKAN, timeout=2)):
            return True
        print("[DETAIL] tidak di halaman Detail -> buka ulang entry teratas (ganti otomatis)")
        self.go_back_to_list()
        if self.open_first_entry_in_list():
            return self.wait_for_detail(max_wait=8)
        return False

    def _relaunch_app_clean(self, wait=3):
        """GANTI otomatis utk desync a11y React Native: form modal yang
        dibuka dari halaman Detail bisa TIDAK muncul di accessibility
        tree (bukti run 22 Sep 2026: tree tetap menampilkan Detail saat
        form 'Tambah Aktivitas' terlihat di layar) -> restart app untuk
        membersihkan state a11y yang macet."""
        try:
            self.driver.terminate_app(APP_PACKAGE)
        except Exception:
            pass
        time.sleep(1)
        try:
            self.driver.activate_app(APP_PACKAGE)
        except Exception:
            pass
        time.sleep(wait)
        return True

    # ----------------------------------------------------------------
    # Halaman DETAIL setelah Simpan (terverifikasi scan 2026-09-04)
    # ----------------------------------------------------------------
    def handle_detail_after_save(self, max_wait=12):
        """
        Setelah Simpan form fleet, app membuka halaman Detail (ada
        loading 'Mohon tunggu..'). Alur sesuai skenario user:
        1. tunggu halaman Detail termuat (desc 'Detail')
        2. buka 'Lihat Log Pergerakan' lalu balik
        3. buka 'Tambah Ritase' kalau ada (form kecil: dropdown
           'Pilih kode tumpukan' + Simpan)
        4. tap tombol global 'Selesai' (paling bawah) + konfirmasi
           dialog kalau muncul ('Ya' / 'OK')
        """
        detail = (AppiumBy.XPATH, '//*[@content-desc="Detail"]')
        if not self.is_present(detail, timeout=max_wait):
            return False
        time.sleep(0.4)

        # 2) lihat log pergerakan lalu balik
        log_btn = (AppiumBy.XPATH, '//*[@content-desc="Lihat Log Pergerakan"]')
        if self.is_present(log_btn, timeout=3):
            self.tap(log_btn)
            time.sleep(0.4)
            try:
                self.driver.back()
            except Exception:
                pass
            time.sleep(0.4)
            self.is_present(detail, timeout=5)

        # 3) tambah ritase (kalau halaman ini punya)
        ritase_btn = (AppiumBy.XPATH, '//*[@content-desc="Tambah Ritase"]')
        if self.is_present(ritase_btn, timeout=3):
            self.tap(ritase_btn)
            time.sleep(0.4)
            self.select_dropdown_option(
                "Kode Tumpukan Tujuan", "Pilih kode tumpukan"
            )
            self.submit()
            time.sleep(0.4)

        # 4) tombol global Selesai (paling bawah)
        try:
            btns = self.driver.find_elements(
                AppiumBy.XPATH, '//*[@content-desc="Selesai"]'
            )
            if btns:
                btns[-1].click()
                time.sleep(0.4)
        except Exception:
            pass

        # dialog konfirmasi kalau muncul
        self.handle_confirm_dialog(confirm=True)  # OK/Batal
        ya = (AppiumBy.XPATH, '//*[@content-desc="Ya"]')
        if self.is_present(ya, timeout=2):
            self.tap(ya)
            time.sleep(0.4)
        return True

    # ----------------------------------------------------------------
    # Alur halaman Detail sesuai skenario user (4 September 2026)
    # ----------------------------------------------------------------
    def _first_clickable(self, locator):
        """Ambil elemen PERTAMA yang clickable & enabled dari `locator`.
        Kembalikan None kalau semua disabled (mis. entry sudah Selesai
        -> app mengunci tombol tambah/status)."""
        try:
            els = self.driver.find_elements(*locator)
        except Exception:
            return None
        for el in els:
            try:
                if el.get_attribute("clickable") == "true":
                    return el
            except Exception:
                continue
        return None

    def wait_for_detail(self, max_wait=12):
        """Tunggu halaman Detail termuat (header desc 'Detail') DAN
        overlay loading 'Mohon tunggu..' sudah hilang (kalau belum,
        tombol-tombol di Detail tidak bisa di-tap). Catat waktu Detail
        terbuka - dipakai standby: 'Waktu Mulai' form tidak boleh satu
        menit dengan waktu kegiatan terakhir entry (alur user 23 Sep)."""
        if not self.is_present(self.DETAIL_HEADER, timeout=max_wait):
            return False
        self._detail_opened_at = time.time()
        return self.wait_loading_done()

    def wait_loading_done(self, max_wait=15):
        """Tunggu overlay loading ('Mohon tunggu..' / 'Sedang memuat data')
        hilang dari layar. Cek pertama PASTI cepat (biasanya loading
        memang sudah tidak ada) supaya jeda tidak menumpuk."""
        loading = (AppiumBy.XPATH,
                   '//*[@text="Mohon tunggu.." or @text="Sedang memuat data"]')
        deadline = time.time() + max_wait
        while time.time() < deadline:
            if not self.is_present(loading, timeout=0.4):
                return True
            time.sleep(0.15)
        return not self.is_present(loading, timeout=1)

    def open_log_pergerakan_and_back(self):
        """Buka 'Lihat Log Pergerakan', tunggu, lalu kembali ke Detail.
        TERVERIFIKASI (dump auto_selesai_fail.xml): back dari halaman Log
        Pergerakan bisa mendarat ke LIST (bukan Detail) - kalau begitu,
        buka ulang entry teratas supaya alur Detail tetap jalan."""
        btn = self._first_clickable(self.BTN_LOG_PERGERAKAN)
        if btn is None:
            print("[LOG PERGERAKAN] tombol tidak ada/disabled -> SKIP")
            return False
        try:
            btn.click()
        except Exception:
            print("[LOG PERGERAKAN] tombol gagal di-tap -> SKIP")
            return False
        time.sleep(0.25)
        try:
            self.driver.back()
        except Exception:
            pass
        time.sleep(0.15)
        if not self.wait_for_detail(max_wait=6):
            # mendarat di list -> buka ulang entry teratas
            print("[LOG PERGERAKAN] setelah back tidak di Detail -> buka ulang entry teratas")
            self.go_back_to_list()
            if not self.open_first_entry_in_list():
                print("[LOG PERGERAKAN] gagal kembali ke Detail -> SKIP")
                return False
        print("[LOG PERGERAKAN] dibuka lalu kembali ke Detail")
        return True

    def after_save_wait_list_or_detail(self, max_wait=15):
        """
        Setelah tap Simpan, app menampilkan loading 'Mohon tunggu..'
        lalu kembali ke LIST (kartu tanggal) atau langsung ke DETAIL
        (bervariasi per menu). Return 'detail' / 'list' / 'unknown'.
        """
        self.wait_loading_done(max_wait=max_wait)
        self.dismiss_permission_dialog()
        if self.wait_for_detail(max_wait=4):
            return "detail"
        if self.is_present(self.SEARCH_INPUT, timeout=3):
            return "list"
        return "unknown"

    def tap_status_button(self, status: str, last: bool = False):
        """
        Tap tombol status di halaman Detail. `last=False` -> tombol PALING
        ATAS (bagian unit pertama, mis. Breakdown excavator); `last=True`
        -> tombol PALING BAWAH (tombol GLOBAL Standby kuning / Selesai
        merah di bar bawah halaman). Halaman Detail tervirtualisasi ->
        scroll dulu kalau tombol belum ter-render. Hanya tap yang
        clickable & visible, diurut BERDASAR POSISI LAYAR (bukan urutan
        tree). Cocokkan content-desc ATAU text (beberapa halaman hanya
        mengekspos label via text).
        Kalau tidak ketemu: pastikan masih di Detail (buka ulang entry -
        bukti run #3 bisa nyasar ke list), lalu GANTI otomatis ke status
        LAIN yang tersedia (kecuali Selesai - alur selesai punya langkah
        sendiri) supaya alur tetap jalan, bukan SKIP.
        """
        locator = (AppiumBy.XPATH,
                   f'//*[@content-desc="{status}" or @text="{status}"]')

        def _clickable_list(loc):
            try:
                els = self.driver.find_elements(*loc)
            except Exception:
                return []
            out = []
            for el in els:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    if not el.is_displayed():
                        continue
                    out.append((el.location["y"], el))
                except Exception:
                    continue
            out.sort(key=lambda t: t[0])
            return out

        def _tap(clickable):
            if not clickable:
                return False
            el = clickable[-1][1] if last else clickable[0][1]
            try:
                el.click()
            except Exception:
                return False
            time.sleep(0.15)
            return True

        if not self.is_present(locator, timeout=2):
            self._scroll_to(locator, max_scrolls=10)
        if _tap(_clickable_list(locator)):
            return True
        # GANTI otomatis: kalau tidak di Detail, buka ulang entry teratas
        # lalu coba sekali lagi
        if self._ensure_on_detail():
            if _tap(_clickable_list(locator)):
                return True
        # GANTI otomatis: status lain yang tersedia di layar
        for alt in self.STATUS_BUTTONS:
            if alt == status or alt == "Selesai":
                continue
            alt_loc = (AppiumBy.XPATH,
                       f'//*[@content-desc="{alt}" or @text="{alt}"]')
            if not self.is_present(alt_loc, timeout=1):
                continue
            if _tap(_clickable_list(alt_loc)):
                print(f"[STATUS] '{status}' tidak ada -> GANTI otomatis '{alt}'")
                return True
        print(f"[STATUS] tombol '{status}' tidak ditemukan -> SKIP")
        return False

    def _fill_status_form_gentle(self, dummy_values=None):
        """Isi form kecil (modal) TANPA scroll/gesek sama sekali:
        sweep dengan scroll menutup modal (bukti dump _5/_6: form hilang
        setelah fill_form_dynamically). Satu pass field yang terlihat:
        dropdown -> pilih opsi pertama; EditText -> teks dummy.
        Keyboard ditutup dengan TAP NETRAL (bukan hide_keyboard: back
        menutup sheet - bukti run 22 Sep)."""
        for kind, payload, _ in self._visible_fillables():
            try:
                if kind == "dd":
                    # status form: jangan search 'Tayan' (opsi standby/
                    # alasan bukan lokasi) - langsung pilih opsi pertama.
                    # scroll_hunt=False: kalau field hilang (sheet sudah
                    # tertutup), JANGAN scroll halaman di belakangnya.
                    self.select_dropdown_option(payload, payload,
                                                search_term=None,
                                                scroll_hunt=False)
                else:
                    self._fill_edittext_by_label(payload, dummy_values or {},
                                                 dismiss_keyboard=False)
            except Exception:
                continue

    def fill_status_form_and_submit(self, reopen_status="Standby"):
        """Form kecil status (Standby/Breakdown): isi field dummy + Simpan
        + konfirmasi popup OK kalau muncul. Tunggu form TERBUKA dulu
        (tombol Simpan muncul) - form butuh waktu render setelah tap
        tombol status. Kalau form tidak muncul: dump layar ASLI dulu
        (sebelum apa pun ditutup), lalu cek dialog konfirmasi - beberapa
        alur meminta konfirmasi SEBELUM form terbuka - tap OK lalu
        tunggu form sekali lagi. JANGAN sweep halaman di belakang form
        (fill_form_dynamically hanya dipanggil kalau form benar-benar
        terbuka). Kalau sheet TERTUTUP di tengah pengisian, BUKA ULANG
        tombol status lalu isi ulang (maks 3x) - bukan SKIP."""
        def _form_ready():
            return self.is_present(self.BTN_SUBMIT, timeout=1)

        deadline = time.time() + 8
        while time.time() < deadline:
            if _form_ready():
                break
            time.sleep(0.2)
        if not _form_ready():
            print("[STATUS] form status belum terbuka -> dump bukti layar asli")
            self._dump_screen("auto_status_form_fail")
            if self.handle_confirm_dialog(confirm=True):
                print("[STATUS] dialog dikonfirmasi -> tunggu form status")
                deadline = time.time() + 6
                while time.time() < deadline:
                    if _form_ready():
                        break
                    time.sleep(0.2)
        if not _form_ready():
            print("[STATUS] form status tetap tidak terbuka -> SKIP")
            return False
        self._dump_screen("status_pre_fill")  # bukti: form terbuka di tree
        for attempt in range(3):
            self._fill_status_form_gentle()
            time.sleep(0.15)
            if _form_ready():
                break
            print(f"[STATUS] sheet tertutup saat isi (percobaan {attempt+1})"
                  f" -> buka ulang '{reopen_status}' lalu isi ulang")
            if reopen_status == "Standby":
                el2 = self._global_standby_button()
                if el2 is None:
                    break
                try:
                    el2.click()
                except Exception:
                    break
            elif not self.tap_status_button(reopen_status, last=True):
                break
            deadline = time.time() + 6
            while time.time() < deadline and not _form_ready():
                time.sleep(0.2)
        if not _form_ready():
            print("[STATUS] sheet tetap tidak bisa diisi -> dump bukti")
            self._dump_screen("auto_status_form_fail")
            return False
        self._dump_screen("status_post_fill")  # bukti: kondisi tree setelah isi
        # JANGAN submit() scroll: sweep pada modal menutup sheet
        # (bukti run 22 Sep: Simpan hilang dari tree + sheet tertutup)
        ok = self._tap_simpan_or_ok()
        time.sleep(0.15)
        self.handle_confirm_dialog(confirm=True)  # popup OK kalau ada
        if ok:
            print("[STATUS] form status diisi dummy & disimpan")
            return True
        print("[STATUS] form status terbuka tapi gagal disimpan -> dump bukti")
        self._dump_screen("auto_status_form_fail")
        return False

    def _global_standby_button(self):
        """Tombol Standby GLOBAL (kuning, bar paling bawah Detail) =
        Standby yang SEBARIS (rentang y tumpang-tindih) dengan tombol
        Selesai merah. Tombol per-unit (excavator/dumptruck) TIDAK
        sebaris dengan Selesai. (feedback user 24 Sep: 'klik standby
        yang di excavator gabisa, mending yang bawah aja' -> jangan
        tap tombol per-unit, pakai bar global.) Kalau bar global belum
        ter-render (virtualisasi), scroll kecil dulu, lalu fallback
        tombol Standby PALING BAWAH yang terlihat."""
        st_loc = (AppiumBy.XPATH, '//*[@content-desc="Standby" or @text="Standby"]')
        se_loc = (AppiumBy.XPATH, '//*[@content-desc="Selesai" or @text="Selesai"]')
        for _ in range(10):
            try:
                sts = self.driver.find_elements(*st_loc)
                ses = self.driver.find_elements(*se_loc)
            except Exception:
                return None
            clickable = []
            for el in sts:
                try:
                    if el.get_attribute("clickable") != "true" or not el.is_displayed():
                        continue
                    y = el.location["y"]
                    clickable.append((y, el))
                except Exception:
                    continue
            rows = []
            for el in ses:
                try:
                    if el.get_attribute("clickable") != "true" or not el.is_displayed():
                        continue
                    y0 = el.location["y"]
                    rows.append((y0 - 50, y0 + el.size["height"] + 50))
                except Exception:
                    continue
            clickable.sort(key=lambda t: -t[0])  # paling bawah dulu
            for y, el in clickable:
                cy = y + el.size["height"] / 2
                if any(a <= cy <= b for a, b in rows):
                    return el
            # Selesai belum ter-render = bar global belum kelihatan ->
            # JANGAN tap tombol per-unit (feedback user 24 Sep: klik
            # standby per-unit berkali-kali tidak mempan) -> scroll
            # terus sampai bar global muncul.
            self._small_scroll_down(wait=0.3)
        return clickable[0][1] if clickable else None

    def standby_then_save(self):
        """Skenario: tap Standby GLOBAL (kuning, bar bawah) -> isi form
        dummy -> Simpan. CUKUP SEKALI (feedback user 22 Sep): kalau
        gagal, langsung lanjut ke Selesai TANPA tap ulang. Kalau form
        masih terbuka di tree, tutup supaya langkah berikutnya (Selesai
        merah) tidak menabrak modal.
        ALUR USER (23 Sep): form standby punya 'Waktu Mulai' default
        waktu sekarang - kalau SEMENIT dengan 'waktu kegiatan terakhir'
        entry, app MENOLAK -> tunggu menit berganti dulu sebelum tap
        Standby (maks ~1 menit, tanpa jeda kalau sudah beda menit)."""
        self._wait_menit_berbeda()
        el = self._global_standby_button()
        if el is None:
            return False
        try:
            el.click()
        except Exception:
            return False
        time.sleep(0.25)
        ok = self.fill_status_form_and_submit()
        if not ok:
            # tutup modal KALAU masih terbuka (Simpan di tree) dengan
            # tap Simpan sekali lagi; kalau sudah di Detail biarkan.
            # back BUTA overshoot list -> Apps (bukti run 22 Sep: dump
            # auto_selesai_fail_4 = halaman Apps setelah back berlebih).
            print("[STATUS] standby gagal diisi -> tutup modal kalau masih terbuka, lanjut alur")
            if self.is_present(self.BTN_SUBMIT, timeout=1):
                self.tap(self.BTN_SUBMIT, timeout=2)
                time.sleep(0.2)
            elif not (self.is_present(self.DETAIL_HEADER, timeout=1)
                      or self.is_present(self.BTN_LOG_PERGERAKAN, timeout=1)):
                try:
                    self.driver.back()
                except Exception:
                    pass
                time.sleep(0.2)
        return ok

    def breakdown_with_photo(self):
        """Skenario Catching: tap Breakdown PERTAMA (bagian excavator) ->
        isi form dummy sampai unggah foto (foto item dummy di-push
        otomatis) -> Simpan. Form modal -> isi GENTLE (sweep menutup
        modal, bukti run #3: fill_form_dynamically menutup form lalu
        'Simpan tidak ditemukan')."""
        if not self.tap_status_button("Breakdown"):
            return False
        time.sleep(0.25)
        self._fill_status_form_gentle({})
        photo = self.upload_photo_if_available(scroll=False)
        print("[BREAKDOWN] foto dummy " + ("diunggah" if photo else "tidak tersedia -> tetap lanjut"))
        time.sleep(0.15)
        ok = self.submit_or_confirm(scroll=False)
        # popup konfirmasi OK setelah Simpan breakdown WAJIB diklik
        # (alur user 23 Sep: 'kok ga klik ok untuk ekskavator' - popup
        # tertinggal menutupi layar sampai Bucket/Ritase gagal)
        self.handle_confirm_dialog(confirm=True, timeout=2)
        time.sleep(0.15)
        if not ok:
            self._dump_screen("auto_breakdown_fail")
        return ok

    def tap_global_selesai(self):
        """Tap tombol Selesai GLOBAL (merah, PALING BAWAH halaman Detail),
        lalu konfirmasi dialog 'Ya' / 'OK' kalau muncul.
        SKIP kalau tombolnya disabled/tidak ada. Cocokkan content-desc
        ATAU text, diurut berdasar posisi layar (paling bawah = global)."""
        locator = (AppiumBy.XPATH, '//*[@content-desc="Selesai" or @text="Selesai"]')
        if not self.is_present(locator, timeout=2):
            self._scroll_to(locator, max_scrolls=12)
        try:
            btns = self.driver.find_elements(*locator)
        except Exception:
            btns = []
        clickable = []
        for b in btns:
            try:
                if b.get_attribute("clickable") != "true":
                    continue
                if not b.is_displayed():
                    continue
                clickable.append((b.location["y"], b))
            except Exception:
                continue
        if not clickable:
            print("[SELESAI] tombol global 'Selesai' tidak ada/disabled -> coba fallback tombol Selesai teratas (per-unit) + dump bukti")
            self._dump_screen("auto_selesai_fail")
            # GANTI otomatis: pastikan di Detail (bukti run #3: alur bisa
            # nyasar ke list -> dump menampilkan list, bukan Detail) lalu
            # coba kumpulkan tombol lagi
            if self._ensure_on_detail():
                try:
                    btns = self.driver.find_elements(*locator)
                except Exception:
                    btns = []
                for b in btns:
                    try:
                        if b.get_attribute("clickable") != "true":
                            continue
                        if not b.is_displayed():
                            continue
                        clickable.append((b.location["y"], b))
                    except Exception:
                        continue
            # fallback: Selesai per-unit PALING ATAS (beberapa halaman
            # Detail tidak punya bar global bawah)
            if not clickable:
                try:
                    if self.tap_status_button("Selesai"):
                        time.sleep(0.25)
                        if self.is_present(self.BTN_YA, timeout=3):
                            self.tap(self.BTN_YA)
                        elif self.handle_confirm_dialog(confirm=True):
                            pass
                        print("[SELESAI] fallback: tombol Selesai per-unit diklik")
                        return True
                except Exception:
                    pass
                print("[SELESAI] tombol 'Selesai' benar-benar tidak ada -> SKIP")
                return False
        clickable.sort(key=lambda t: t[0])
        try:
            clickable[-1][1].click()  # paling bawah = bar global
        except Exception:
            return False
        time.sleep(0.25)
        if self.is_present(self.BTN_YA, timeout=3):
            self.tap(self.BTN_YA)
            time.sleep(0.15)
            print("[SELESAI] entry diselesaikan (konfirmasi 'Ya')")
            return True
        if self.handle_confirm_dialog(confirm=True):
            print("[SELESAI] entry diselesaikan (konfirmasi OK)")
            return True
        print("[SELESAI] tombol 'Selesai' diklik tanpa dialog konfirmasi")
        return True

    def _on_menu_list(self):
        """Apakah sekarang di halaman LIST menu? App 2.5.15 TIDAK pakai
        resource-id RN: deteksi lewat (1) search bar berteks 'Cari..'
        ATAU (2) pill tanggal clickable di bagian ATAS layar (desc
        berpola '.. 22 Sep 2026 ..', y < 400)."""
        if self.is_present(self.SEARCH_INPUT, timeout=1.5):
            return True
        if self.is_present(self.SEARCH_INPUT_TEXT, timeout=1.5):
            return True
        try:
            els = self.driver.find_elements(
                AppiumBy.XPATH, '//*[@clickable="true"]')
            for e in els:
                try:
                    if not e.is_displayed():
                        continue
                    if e.location["y"] > 400:
                        continue
                    d = (e.get_attribute("content-desc") or "")
                    if re.search(r"\d{1,2}\s+\w{3,9}\s+\d{4}", d):
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _on_apps_page(self):
        """Apakah sekarang di halaman Apps/Beranda (bottom nav terlihat)?
        Menu list TIDAK punya bottom nav 'Aktivitas' -> aman sebagai
        penanda nyasar."""
        return self.is_present(
            (AppiumBy.XPATH, '//*[@content-desc="Aktivitas"]'), timeout=1)

    def _reopen_menu_from_apps(self):
        """GANTI otomatis: dari halaman Apps, buka ulang menu ini lewat
        itemnya (desc mengandung TITLE) supaya kembali ke LIST menu."""
        title = getattr(self, "TITLE", None)
        if not title:
            return False
        locator = (AppiumBy.XPATH,
                   f'//*[contains(@content-desc,"{title}") and @clickable="true"]')
        if not self.is_present(locator, timeout=2):
            return False
        try:
            els = self.driver.find_elements(*locator)
        except Exception:
            return False
        for el in els:
            try:
                if not el.is_displayed():
                    continue
                el.click()
                time.sleep(0.2)
                return True
            except Exception:
                continue
        return False

    def go_back_to_list(self):
        """Tap 'Kembali' (kalau ada) atau back sampai halaman list terlihat
        (search bar / filter tanggal). Tunggu loading dulu & timeout
        CUKUP (bukti run 22 Sep: timeout 0.8s saat list masih loading
        -> back kelewatan ke Apps, alur nyasar). Kalau NYASAR ke
        Apps/Beranda/launcher: JANGAN back terus (bukti 23 Sep: back
        ganda sampai ke LAUNCHER Android) - buka ulang menu dari Apps
        (ganti otomatis)."""
        self.wait_loading_done(max_wait=4)
        for _ in range(4):
            if self._on_menu_list():
                return True
            # tunggu loading selesai dulu, cek list DUA KALI sebelum
            # nekat back lagi (bukti 23 Sep: form Feeding gagal simpan
            # -> back ganda nyasar sampai Apps/launcher)
            self.wait_loading_done(max_wait=3)
            if self._on_menu_list():
                return True
            if self._on_apps_page():
                print("[BACK] nyasar ke halaman Apps -> buka ulang menu ini (ganti otomatis)")
                self._reopen_menu_from_apps()
                self.wait_loading_done(max_wait=4)
                if self._on_menu_list():
                    return True
                continue
            if self.is_present(self.BTN_KEMBALI, timeout=1.5):
                self.tap(self.BTN_KEMBALI)
            else:
                try:
                    self.driver.back()
                except Exception:
                    pass
            time.sleep(0.2)
            self.wait_loading_done(max_wait=3)
        ok = self._on_menu_list()
        if not ok:
            self._dump_screen("auto_back_overshoot")  # bukti: nyasar ke mana
        return ok

    def tap_top_item(self):
        """
        Tap item PALING ATAS di tab kelola (mis. Kelola Jembatan
        Timbang) kalau itemnya perlu dibuka dulu sebelum tombol
        statusnya bisa di-tap. Defensif: kalau tidak ada kartu yang
        cocok, lanjut saja (tombol status mungkin langsung terlihat
        di baris item).
        """
        for xp in (
            '//*[contains(@text,"Jembatan") and @clickable="true"]',
            '//*[contains(@content-desc,"Jembatan") and @clickable="true"]',
            '//*[contains(@text,"2026") and @clickable="true"]',
        ):
            try:
                els = self.driver.find_elements(AppiumBy.XPATH, xp)
            except Exception:
                continue
            for el in els[:6]:
                try:
                    desc = ((el.get_attribute("content-desc") or "")
                            + (el.get_attribute("text") or ""))
                    if (self._PUA_CHARS.match(desc) and "2026" in desc):
                        continue  # pill tanggal (jangan diklik - buka kalender)
                    el.click()
                    time.sleep(0.15)
                    return True
                except Exception:
                    continue
        return False

    def _entry_detail_usable(self):
        """Detail entry ini masih bisa dioperasikan? Ada tombol status
        yang clickable? Entry yang SUDAH SELESAI tombol statusnya
        disabled semua (feedback user 22 Sep: 'itu udah selesai jadi
        gabisa pake yg sudah selesai... harus discroll') -> jangan
        dipakai, cari entry lain."""
        for status in self.STATUS_BUTTONS:
            loc = (AppiumBy.XPATH,
                   f'//*[@content-desc="{status}" or @text="{status}"]')
            try:
                els = self.driver.find_elements(*loc)
            except Exception:
                continue
            for el in els:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    if not el.is_displayed():
                        continue
                    return True
                except Exception:
                    continue
        return False

    def open_first_entry_in_list(self):
        """
        Tap entry PALING ATAS di list supaya halaman Detail terbuka.
        Kartu list = ViewGroup clickable dengan content-desc diawali
        tanggal, mis. '04 Sep 2026 07:00, 10800000233 - EFO Bukit 6
        (WP 1 2), WASHE...' (Terverifikasi scan j5_list.xml: TextView
        tanggal TIDAK clickable, yang clickable kartunya ber-desc).
        Kandidat diurut BERDASAR POSISI LAYAR supaya yang paling atas
        (entry terbaru) yang dipilih lebih dulu. Entry yang SUDAH
        SELESAI (tombol status disabled semua) dilewati: back -> scroll
        list -> coba entry berikutnya (feedback user 22 Sep: harus
        di-scroll, jangan pakai yang sudah selesai).
        Guard: harus di halaman LIST menu (search bar / filter tanggal
        ada di tree) - kalau tidak, JANGAN hunting di halaman lain
        (bukti run 22 Sep: hunting di Apps malah scroll nyasar).
        """
        if not self._on_menu_list():
            print("[LIST] bukan halaman list menu -> tidak bisa buka entry")
            return False
        candidates = []
        seen_ids = set()
        # pola tanggal HARI INI (format kartu list, mis. '15 Sep 2026 07:00, ...')
        today = datetime.date.today()
        today_pat = f"{today.day:02d} {self.MONTHS_SHORT[today.month - 1]} {today.year}"
        for xp in (
            f'//*[contains(@content-desc,"{today_pat}") and @clickable="true"]',
            f'//*[contains(@text,"{today_pat}") and @clickable="true"]',
            '//*[contains(@content-desc,"2026") and @clickable="true"]',
            '//*[contains(@text,"2026") and @clickable="true"]',
        ):
            try:
                els = self.driver.find_elements(AppiumBy.XPATH, xp)
            except Exception:
                continue
            for el in els:
                try:
                    eid = el.id
                    if eid in seen_ids:
                        continue
                    seen_ids.add(eid)
                    if not el.is_displayed():
                        continue
                    desc = ((el.get_attribute("content-desc") or "")
                            + (el.get_attribute("text") or ""))
                    if "Tanggal," in desc:
                        continue  # tombol filter tanggal, BUKAN kartu entry
                    if el.location["y"] < 420:
                        continue  # pill tanggal di area atas (app 2.5.15
                        # desc-nya ', 22 Sep 2026, ' tanpa 'Tanggal,') ->
                        # jangan diklik sebagai entry (bukti diag 22 Sep:
                        # pill malah membuka kalender)
                    if (self._PUA_CHARS.match(desc) and "2026" in desc):
                        continue  # pill tanggal app baru: desc DIAWALI
                        # ikon kalender (bukti 24 Sep: pill y~500 diklik
                        # sebagai entry -> kalender TERBUKA BERULANG-ULANG,
                        # user: 'ngulang terus buka kalendernya')
                    candidates.append((el.location["y"], el))
                except Exception:
                    continue
        candidates.sort(key=lambda t: t[0])
        print(f"[LIST] kandidat entry: {len(candidates)} (pola '{today_pat}')")
        for pass_i in range(3):
            for _, el in candidates:
                try:
                    el.click()
                    time.sleep(0.15)
                    self.wait_loading_done(max_wait=8)
                    if self.wait_for_detail(max_wait=8):
                        if self._entry_detail_usable():
                            print("[LIST] entry dibuka -> Detail (bisa dioperasikan)")
                            return True
                        print("[LIST] entry sudah SELESAI -> back, cari entry lain (ganti otomatis)")
                        try:
                            self.driver.back()
                        except Exception:
                            pass
                        time.sleep(0.2)
                        self.wait_loading_done(max_wait=6)
                    else:
                        try:
                            self.driver.back()
                        except Exception:
                            pass
                        time.sleep(0.2)
                except Exception:
                    continue
            # semua kandidat terpakai/tidak bisa -> scroll list sedikit
            # lalu kumpulkan kandidat baru (entry di bawah lipatan)
            self._small_scroll_down(wait=0.2)
            time.sleep(0.1)
        print("[LIST] tidak ada entry yang bisa dibuka -> SKIP")
        self._dump_screen("auto_list_fail")
        return False

    # ----------------------------------------------------------------
    # Dumptruck / Ritase (Ore Getting, Catching WP, Supply)
    # ----------------------------------------------------------------
    def fill_bucket_dumptruck(self, _retried=False):
        """
        Isi field 'Bucket' pada bagian Dumptruck (atau WP) di halaman
        Detail: scroll sampai label 'Bucket' + EditText-nya ter-render,
        lalu ketik nilai dummy.
        Kalau Bucket belum muncul (baris dumptruck belum di-expand /
        bucket baru ada setelah tumpukan ditambah - bukti dump
        auto_ritase_fail Supply: Detail tanpa Bucket): GANTI otomatis -
        expand baris dumptruck, atau tambah kode tumpukan dulu, lalu
        cek ulang. Kalau entry sudah Selesai (EditText diganti TextView)
        -> SKIP defensif.
        """
        from utils.dummy_data import BUCKET_VALUE
        label = (AppiumBy.XPATH, '//*[@text="Bucket"]')
        if not self.is_present(label, timeout=2):
            self._scroll_to(label, max_scrolls=12)
        locator = (AppiumBy.XPATH,
                   '//*[@text="Bucket"]/following::android.widget.EditText[1]')
        if not self.is_present(locator, timeout=3):
            if not _retried:
                # GANTI otomatis 1: expand baris dumptruck -> cek ulang
                if self._expand_dumptruck_row():
                    print("[BUCKET] Bucket belum ter-render -> GANTI otomatis: baris dumptruck di-expand")
                    return self.fill_bucket_dumptruck(_retried=True)
                # GANTI otomatis 2: Supply tidak punya Bucket sebelum ada
                # tumpukan -> tambah kode tumpukan dulu -> cek ulang
                if self.is_present(
                    (AppiumBy.XPATH, '//*[contains(@content-desc,"Tambah Kode Tumpukan")]'),
                    timeout=2,
                ):
                    print("[BUCKET] field Bucket tidak ada -> GANTI otomatis: tambah kode tumpukan dulu")
                    if self.tambah_kode_tumpukan():
                        return self.fill_bucket_dumptruck(_retried=True)
            print("[BUCKET] field Bucket tidak ada (entry selesai?) -> SKIP + dump bukti")
            self._dump_screen("auto_bucket_fail")
            return False
        try:
            self.type_text(locator, str(BUCKET_VALUE))
            try:
                self.driver.hide_keyboard()
            except Exception:
                pass
            print(f"[BUCKET] Dumptruck: OK {BUCKET_VALUE}")
            return True
        except Exception:
            return False

    def fill_bucket_wp(self):
        """Isi field 'Bucket' pada bagian WP (sama dengan bucket
        dumptruck - label 'Bucket' + EditText setelahnya)."""
        return self.fill_bucket_dumptruck()

    def _create_new_pile_in_dropdown(self):
        """
        Dalam dropdown 'Pilih kode tumpukan': cari opsi 'Tambahkan Kode
        Tumpukan' (atau 'Tambah'/'Buat'/'Baru' yang TERLIHAT, bukan
        tombol 'Tambah Ritase' di belakang modal), buka form kode
        tumpukan baru, isi kode + pilih Kategori, lalu Simpan.
        Sesuai alur user: "pilih tambahkan kode tumpukan ... pilih
        kategori, lalu simpan" -> popup OK.
        """
        from utils.dummy_data import KODE_TUMPUKAN_BARU
        # 1) buka dropdown kode tumpukan di form Ritase
        field = (AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih kode tumpukan")]')
        if self.is_present(field, timeout=3):
            try:
                self.tap(field, timeout=3)
            except Exception:
                return False
            self._wait_dropdown_modal(max_wait=6)
        # 2) cari opsi 'Tambahkan Kode Tumpukan' di dalam modal. Opsi
        # ini sering ada di BAWAH daftar kode tumpukan (di luar viewport
        # modal) -> kalau belum terlihat, scroll kecil DI DALAM modal
        # (bukan layar di belakangnya) lalu cari lagi - feedback user
        # 24 Sep: 'tumpukan barunya belum diklik' di Ore Getting.
        clicked = False
        for _ in range(4):
            for label in ("Tambahkan Kode Tumpukan", "Tambahkan",
                          "Tambah Kode", "Tambah"):
                locator = (AppiumBy.XPATH,
                           f'//*[contains(@content-desc,"{label}") or contains(@text,"{label}")]')
                if not self.is_present(locator, timeout=1.5):
                    continue
                try:
                    els = self.driver.find_elements(*locator)
                except Exception:
                    continue
                for el in els[:10]:
                    try:
                        if el.get_attribute("clickable") != "true":
                            continue
                        desc = ((el.get_attribute("content-desc") or "")
                                + (el.get_attribute("text") or ""))
                        if "Ritase" in desc:
                            continue  # tombol 'Tambah Ritase' di belakang modal
                        if not el.is_displayed():
                            continue
                        el.click()
                        clicked = True
                        break
                    except Exception:
                        continue
                if clicked:
                    break
            if clicked:
                break
            try:
                size = self.driver.get_window_size()
                self.driver.swipe(size["width"] // 2,
                                  int(size["height"] * 0.6),
                                  size["width"] // 2,
                                  int(size["height"] * 0.4), 200)
            except Exception:
                break
            time.sleep(0.2)
        if not clicked:
            # tidak ada opsi tambahkan -> tutup modal (fallback: opsi
            # pertama biasa dipilih oleh caller)
            try:
                self.driver.back()
            except Exception:
                pass
            time.sleep(0.15)
            return False
        # 3) mini form: Kode (teks) + Kategori (dropdown, Catching).
        # Form modal: isi GENTLE (tanpa scroll - sweep menutup modal,
        # sama seperti form status). Tombol simpan = 'Simpan' (Catching)
        # ATAU 'OK' bottom sheet (Ore Getting - bukti dump
        # auto_pile_form_fail run #3: dialog Batal/OK tanpa Simpan).
        time.sleep(0.15)
        self._fill_pile_code(KODE_TUMPUKAN_BARU)
        time.sleep(0.15)
        ok = self.submit_or_confirm(scroll=False)
        time.sleep(0.25)
        # dialog konfirmasi berikutnya: 'Apakah Anda yakin ingin
        # menambah ritase di ... dan tumpukan ... ?' -> OK
        self.handle_confirm_dialog(confirm=True, timeout=2)
        if ok:
            print(f"[TUMPUKAN] kode tumpukan baru dibuat: {KODE_TUMPUKAN_BARU}")
            return True
        print("[TUMPUKAN] form kode tumpukan gagal disimpan -> dump bukti")
        self._dump_screen("auto_pile_form_fail")
        return False

    def tambah_ritase(self, create_new_pile: bool = False):
        """
        Skenario: 'Tambah Ritase' di halaman Detail -> isi form ->
        Simpan -> popup konfirmasi OK.
        create_new_pile=True: kode tumpukan BARU dibuat lewat dropdown
        (isi kode + pilih kategori, Simpan) sesuai alur user Catching
        & Ore Getting ("pilih tambahkan kode tumpukan dan klik OK").
        """
        if not self.is_present(self.BTN_TAMBAH_RITASE, timeout=2):
            if self._scroll_to(self.BTN_TAMBAH_RITASE, max_scrolls=12) is None:
                # GANTI otomatis: menu yang tidak punya ritase (Supply -
                # bukti dump auto_ritase_fail run #3: yang ada tombol
                # '+ Tambah Kode Tumpukan', bukan 'Tambah Ritase')
                if self.is_present(
                    (AppiumBy.XPATH, '//*[contains(@content-desc,"Tambah Kode Tumpukan")]'),
                    timeout=2,
                ):
                    print("[RITASE] tombol 'Tambah Ritase' tidak ada -> GANTI otomatis: '+ Tambah Kode Tumpukan'")
                    return self.tambah_kode_tumpukan()
                print("[RITASE] tombol 'Tambah Ritase' tidak ada -> SKIP + dump bukti")
                self._dump_screen("auto_ritase_fail")
                return False
        self.wait_loading_done()  # jaga-jaga: overlay loading belum hilang
        # tombol bisa DISABLED (entry sudah Selesai) -> SKIP, jangan timeout
        btn = self._first_clickable(self.BTN_TAMBAH_RITASE)
        if btn is None:
            print("[RITASE] tombol 'Tambah Ritase' disabled (entry selesai?) -> SKIP")
            return False
        try:
            btn.click()
        except Exception as exc:
            print(f"[RITASE] tombol 'Tambah Ritase' gagal di-tap -> SKIP ({exc})")
            return False
        time.sleep(0.15)
        self.wait_loading_done(max_wait=8)
        if create_new_pile:
            self._create_new_pile_in_dropdown()
        # Setelah kode tumpukan dibuat/dipilih, app bisa LANGSUNG minta
        # konfirmasi 'Apakah Anda yakin ingin menambah ritase ...?'
        # (dialog Batal/OK - bukti dump auto_pile_form_fail run #3:
        # Simpan tidak pernah muncul karena ritase ditambahkan lewat
        # dialog) -> tap OK (ganti otomatis dari Simpan).
        time.sleep(0.2)
        if self.handle_confirm_dialog(confirm=True, timeout=2):
            print("[RITASE] ritase dikonfirmasi via dialog OK (ganti otomatis)")
            return True
        # form ritase masih terbuka? (field kode tumpukan / tombol Simpan)
        form_open = (
            self.is_present(
                (AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih kode tumpukan")]'),
                timeout=2,
            )
            or self.is_present(self.BTN_SUBMIT, timeout=2)
        )
        if not form_open:
            print("[RITASE] form ritase sudah tertutup (selesai via dialog OK)")
            return True
        # kalau field kode tumpukan masih kosong -> pilih opsi pertama
        if self.is_present(
            (AppiumBy.XPATH, '//*[contains(@content-desc,"Pilih kode tumpukan")]'),
            timeout=3,
        ):
            self.select_dropdown_option(
                "Kode Tumpukan Tujuan", "Pilih kode tumpukan",
                search_term="TEST",
            )
        submitted = self.submit_or_confirm(scroll=False)  # mini form modal
        time.sleep(0.25)
        self.handle_confirm_dialog(confirm=True, timeout=2)  # popup OK
        if submitted:
            print("[RITASE] form ritase disimpan (popup OK)")
        return submitted

    def tambah_kode_tumpukan(self):
        """
        GANTI otomatis untuk alur 'Tambah Ritase' di menu yang TIDAK
        punya ritase (Supply - bukti dump auto_ritase_fail run #3:
        yang ada '+ Tambah Kode Tumpukan', bukan 'Tambah Ritase').
        Tap '+ Tambah Kode Tumpukan' -> dialog kecil: isi kode ->
        OK (bottom sheet Batal/OK) -> konfirmasi popup OK.
        """
        from utils.dummy_data import KODE_TUMPUKAN_BARU
        clicked = False
        for label in ("Tambah Kode Tumpukan",):
            locator = (AppiumBy.XPATH,
                       f'//*[contains(@content-desc,"{label}") or contains(@text,"{label}")]')
            if not self.is_present(locator, timeout=2):
                self._scroll_to(locator, max_scrolls=8)
            try:
                els = self.driver.find_elements(*locator)
            except Exception:
                continue
            for el in els[:10]:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    desc = ((el.get_attribute("content-desc") or "")
                            + (el.get_attribute("text") or ""))
                    if "Pilih" in desc:
                        continue  # dropdown 'Pilih kode tumpukan', bukan tombol
                    if not el.is_displayed():
                        continue
                    el.click()
                    clicked = True
                    break
                except Exception:
                    continue
            if clicked:
                break
        if not clicked:
            print("[TUMPUKAN] tombol '+ Tambah Kode Tumpukan' tidak ada -> SKIP")
            return False
        time.sleep(0.3)
        self.wait_loading_done(max_wait=8)
        # dialog kode: isi GENTLE (modal, jangan sweep) -> OK
        self._fill_pile_code(KODE_TUMPUKAN_BARU)
        time.sleep(0.15)
        ok = self.submit_or_confirm(scroll=False)
        time.sleep(0.2)
        self.handle_confirm_dialog(confirm=True, timeout=2)
        if ok:
            print(f"[TUMPUKAN] kode tumpukan ditambahkan: {KODE_TUMPUKAN_BARU}")
            return True
        print("[TUMPUKAN] form kode tumpukan gagal disimpan -> dump bukti")
        self._dump_screen("auto_kode_tumpukan_fail")
        return False

    def tambah_dumptruck(self):
        """
        Alur user: "Klik tombol tambah lalu pilih dumptruck bebas" ->
        tombol 'Tambah Dumptruck'/'+ Tambah Dumptruck' (BUKAN 'Tambah
        Ritase'/'Tambah WP'/'+ Tambah Kode Tumpukan') di halaman Detail
        -> modal pilih dumptruck -> opsi pertama -> OK.
        Halaman Detail tervirtualisasi -> expand baris Dumptruck dulu
        kalau tombol belum ter-render, lalu SCROLL. Fallback terakhir:
        tombol ikon plus clickable.
        """
        # baris Dumptruck mungkin belum di-expand -> tombol belum ada
        if not self.is_present(
            (AppiumBy.XPATH, '//*[contains(@content-desc,"Tambah")]'),
            timeout=1,
        ):
            self._expand_dumptruck_row()
        clicked = False
        for label in ("Tambah Dumptruck", "+ Tambah Dumptruck",
                      "Tambah DT", "Tambah"):
            locator = (AppiumBy.XPATH,
                       f'//*[contains(@content-desc,"{label}") or contains(@text,"{label}")]')
            if not self.is_present(locator, timeout=2):
                self._scroll_to(locator, max_scrolls=10)
            try:
                els = self.driver.find_elements(*locator)
            except Exception:
                continue
            for el in els[:12]:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    desc = ((el.get_attribute("content-desc") or "")
                            + (el.get_attribute("text") or ""))
                    if "Ritase" in desc or "WP" in desc or "Kode" in desc:
                        continue
                    if not el.is_displayed():
                        continue
                    el.click()
                    clicked = True
                    break
                except Exception:
                    continue
            if clicked:
                break
        if not clicked:
            # fallback: tombol ikon plus (FontAwesome fa-plus dll) di Detail
            for icon in ("", "", "", ""):
                locator = (AppiumBy.XPATH,
                           f'//*[@content-desc="{icon}" or @text="{icon}"]')
                try:
                    els = self.driver.find_elements(*locator)
                except Exception:
                    continue
                for el in els[:8]:
                    try:
                        if el.get_attribute("clickable") != "true":
                            continue
                        if not el.is_displayed():
                            continue
                        el.click()
                        clicked = True
                        break
                    except Exception:
                        continue
                if clicked:
                    break
        if not clicked:
            print("[DUMPTRUCK] tombol tambah dumptruck tidak ada -> SKIP + dump bukti")
            self._dump_screen("auto_dumptruck_fail")
            return False
        # TUNGGU modal pilih dumptruck siap (jangan klik sebelum opsi load)
        self._wait_dropdown_modal(max_wait=6)
        # modal pilih dumptruck -> opsi pertama (mis. '1DT01 - Dumptruck')
        self._try_pick_first_option("", tries=8)
        time.sleep(0.15)
        self.handle_confirm_dialog(confirm=True, timeout=2)
        print("[DUMPTRUCK] dumptruck ditambahkan")
        return True

    def hapus_first_dumptruck(self):
        """Alur user: "klik tombol hapus pada salah satu dumptruck dan
        pilih OK" -> tap 'Hapus' PERTAMA yang clickable -> konfirmasi OK.
        Baris Dumptruck tervirtualisasi -> expand dulu kalau tombol belum
        ter-render (bukti dump auto_bucket_fail_3: tombol 'Hapus' ada di
        baris Dumptruck setelah ter-render)."""
        locator = self.BTN_HAPUS
        if not self.is_present(locator, timeout=2):
            self._expand_dumptruck_row()
            self._scroll_to(locator, max_scrolls=12)
        btn = self._first_clickable(locator)
        if btn is None:
            print("[HAPUS] tombol 'Hapus' tidak ada/disabled -> SKIP + dump bukti")
            self._dump_screen("auto_hapus_fail")
            return False
        try:
            btn.click()
        except Exception:
            return False
        time.sleep(0.25)
        if self.handle_confirm_dialog(confirm=True):
            print("[HAPUS] dumptruck dihapus (OK)")
            return True
        print("[HAPUS] dialog konfirmasi hapus tidak muncul -> dump bukti")
        self._dump_screen("auto_hapus_fail")
        return False

    # ----------------------------------------------------------------
    # Foto dummy untuk upload (form Breakdown Catching WP)
    # ----------------------------------------------------------------
    def ensure_photo_on_device(self):
        """Push foto dummy PNG ke /sdcard/Download + media scan supaya
        muncul di photo picker Android."""
        import base64
        from utils.dummy_data import TEST_PHOTO_B64
        path = "/sdcard/Download/opel_test_photo.png"
        try:
            self.driver.push_file(path, base64.b64decode(TEST_PHOTO_B64))
        except Exception:
            return False
        try:
            self.driver.execute_script(
                "mobile: shell",
                {"command": "am", "args": [
                    "broadcast",
                    "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
                    "-d", "file://" + path,
                ]},
            )
        except Exception:
            pass
        return True

    def upload_photo_if_available(self, scroll=True):
        """Cari tombol unggah foto di form (desc/text mengandung
        'Unggah'/'Upload'/'Lampir'/'Kamera'/'Ambil Foto'/'Pilih Foto'/
        'Ambil'/'Foto' - TANPA 'Galeri': alur user 24 Sep JANGAN buka
        galeri, pakai KAMERA), scroll kecil dulu kalau belum
        ter-render, tap, lalu ambil foto via kamera (shutter ->
        konfirmasi). `scroll=False` untuk form MODAL (sweep menutup
        modal). Kalau tidak ketemu -> SKIP (defensif)."""
        self.ensure_photo_on_device()
        tapped = False
        for c in ("Unggah", "Upload", "Lampir", "Kamera",
                  "Ambil Foto", "Pilih Foto", "Ambil", "Foto"):
            locator = (AppiumBy.XPATH,
                       f'//*[contains(@content-desc,"{c}") or contains(@text,"{c}")]')
            if not self.is_present(locator, timeout=2):
                # form tervirtualisasi -> scroll kecil sampai tombol muncul
                if scroll:
                    self._scroll_to(locator, max_scrolls=8)
            try:
                els = self.driver.find_elements(*locator)
            except Exception:
                continue
            for el in els[:8]:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    if not el.is_displayed():
                        continue
                    el.click()
                    tapped = True
                    break
                except Exception:
                    continue
            if tapped:
                break
        if not tapped:
            print("[FOTO] tombol unggah foto tidak ditemukan -> dump bukti sheet")
            self._dump_screen("auto_foto_button_fail")
            return False
        time.sleep(0.4)
        return self._take_camera_photo()

    def _take_camera_photo(self, max_wait=25):
        """ALUR USER (24 Sep): foto via KAMERA saja, JANGAN buka galeri.
        Kalau muncul chooser -> tap opsi 'Kamera'. Kalau gallery picker
        (album 'Downloads') malah terbuka -> back lalu cari opsi Kamera.
        Lalu tap tombol SHUTTER (lingkaran besar bawah-tengah) ->
        konfirmasi centang/'Selesai'/OK."""
        deadline = time.time() + max_wait
        kamera_clicked = False
        while time.time() < deadline:
            # 0) gallery picker terbuka? -> tutup, jangan dipakai
            gallery = (AppiumBy.XPATH,
                       '//*[contains(@text,"Downloads")'
                       ' or contains(@content-desc,"Downloads")]')
            if self.is_present(gallery, timeout=0.8):
                try:
                    self.driver.back()
                except Exception:
                    pass
                time.sleep(0.4)
                continue
            # 1) opsi 'Kamera' pada chooser -> tap
            kam = (AppiumBy.XPATH,
                   '//*[contains(@content-desc,"Kamera")'
                   ' or contains(@text,"Kamera")]')
            if not kamera_clicked and self.is_present(kam, timeout=1):
                self.tap(kam, timeout=2)
                kamera_clicked = True
                time.sleep(0.8)
                continue
            # 2) shutter: ImageButton besar area bawah-tengah / desc
            for xp in (
                '//*[contains(@content-desc,"Shutter")]',
                '//*[contains(@content-desc,"shutter")]',
                '//*[contains(@content-desc,"Ambil foto")]',
                '//android.widget.ImageButton[@clickable="true"]',
            ):
                try:
                    els = self.driver.find_elements(AppiumBy.XPATH, xp)
                except Exception:
                    continue
                for el in els[:10]:
                    try:
                        if not el.is_displayed():
                            continue
                        if xp.startswith("//android.widget.ImageButton"):
                            cy = el.location["y"] + el.size["height"] / 2
                            h = self.driver.get_window_size()["height"]
                            if not (h * 0.6 <= cy <= h * 0.95):
                                continue
                        el.click()
                        time.sleep(0.6)
                        # 3) konfirmasi hasil foto (centang/'Selesai'/OK)
                        for conf in (
                            '//*[contains(@content-desc,"Selesai")]',
                            '//*[contains(@content-desc,"Done")]',
                            '//*[contains(@content-desc,"OK")]',
                            '//*[@text="OK"]',
                            '//*[contains(@content-desc,"check")]',
                        ):
                            if self.is_present(
                                (AppiumBy.XPATH, conf), timeout=2):
                                self.tap((AppiumBy.XPATH, conf), timeout=2)
                                time.sleep(0.5)
                                return True
                        return True  # shutter di-tap, tanpa tombol konfirmasi
                    except Exception:
                        continue
            time.sleep(0.5)
        return False

    # ----------------------------------------------------------------
    # Tombol TAMBAH di halaman DETAIL (Aktivitas Tambang)
    # ----------------------------------------------------------------
    def _click_bottom_center_add_button(self):
        """CEPAT (feedback user 22 Sep): tombol TAMBAH BESAR di
        bawah-tengah halaman Detail (satu halaman dgn Lihat Log
        Pergerakan) = ViewGroup clickable TANPA desc/text di area
        tengah-bawah (bukti dump auto_tambah_detail_fail.xml:
        b=[475,1767][648,1939], BUKAN pojok kanan-bawah seperti FAB
        list). Satu pass find_elements TANPA scroll — jangan buang
        waktu label-hunting dulu."""
        try:
            els = self.driver.find_elements(
                AppiumBy.XPATH,
                '//android.view.ViewGroup[@clickable="true"]')
        except Exception:
            return False
        size = self.driver.get_window_size()
        w, h = size["width"], size["height"]
        for e in els:
            try:
                if not e.is_displayed():
                    continue
                desc = (e.get_attribute("content-desc") or "").strip()
                txt = (e.get_attribute("text") or "").strip()
                if desc or txt:
                    continue  # berlabel -> bukan tombol ikon kosong
                cx = e.location["x"] + e.size["width"] / 2
                cy = e.location["y"] + e.size["height"] / 2
                sz = e.size
                if not (w * 0.25 <= cx <= w * 0.75):
                    continue  # harus di bawah-TENGAH (bukan pojok)
                if cy <= h * 0.5:
                    continue
                if not (100 <= sz["width"] <= 400
                        and 100 <= sz["height"] <= 400):
                    continue
                e.click()
                return True
            except Exception:
                continue
        return False

    def tambah_entry_dari_detail(self):
        """
        Alur user 3.1 Aktivitas Tambang: di halaman Detail entry yang
        baru dibuat, tombol TAMBAH BESAR di bawah-tengah membuka MODAL
        'Tambah Unit/Alat' (BUKAN form entry baru!) -> pilih SATU
        unit/alat bebas (opsi pertama). Terbukti dump diag 22 Sep 2026:
        modal = judul text 'Tambah Unit/Alat', kotak 'Cari kode alat',
        daftar opsi clickable ber-desc ('1PS01 - Excavator', ...).
        Misdiagnosis lama ('desync a11y'): kode mencari field form
        'Pilih shift' padahal yang terbuka adalah PICKER unit.
        """
        clicked = self._click_bottom_center_add_button()
        if not clicked:
            # fallback: label/ikon/FAB (jarang terpakai di app baru)
            for label in ("Tambah Aktivitas", "Tambah Data", "Tambah Lagi", "Tambah"):
                locator = (AppiumBy.XPATH,
                           f'//*[contains(@content-desc,"{label}") or contains(@text,"{label}")]')
                if not self.is_present(locator, timeout=0.8):
                    continue
                try:
                    els = self.driver.find_elements(*locator)
                except Exception:
                    continue
                for el in els[:12]:
                    try:
                        if el.get_attribute("clickable") != "true":
                            continue
                        desc = ((el.get_attribute("content-desc") or "")
                                + (el.get_attribute("text") or ""))
                        if "Ritase" in desc:
                            continue
                        if not el.is_displayed():
                            continue
                        el.click()
                        clicked = True
                        break
                    except Exception:
                        continue
                if clicked:
                    break
        if not clicked:
            fab = self.find_fab()
            if fab is not None:
                try:
                    fab.click()
                    clicked = True
                except Exception:
                    pass
        if not clicked:
            print("[TAMBAH UNIT] tombol tambah di halaman Detail tidak ada -> SKIP + dump bukti")
            self._dump_screen("auto_tambah_unit_fail")
            return False
        time.sleep(0.3)
        self.wait_loading_done(max_wait=8)
        self.dismiss_permission_dialog()
        # tunggu modal 'Tambah Unit/Alat' muncul di tree
        deadline = time.time() + 5
        modal_seen = False
        while time.time() < deadline:
            if self.is_present(
                    (AppiumBy.XPATH,
                     '//*[contains(@text,"Tambah Unit") '
                     'or contains(@content-desc,"Tambah Unit")]'),
                    timeout=0.8):
                modal_seen = True
                break
            time.sleep(0.3)
        if not modal_seen:
            print("[TAMBAH UNIT] modal 'Tambah Unit/Alat' tidak muncul -> SKIP + dump bukti")
            self._dump_screen("auto_tambah_unit_fail")
            return False
        # pilih opsi unit PERTAMA: clickable ber-desc mengandung ' - '
        # (pola '1PS01 - Excavator'), di area opsi (bukan kotak Cari)
        picked = False
        try:
            opts = self.driver.find_elements(
                AppiumBy.XPATH, '//*[@clickable="true"]')
        except Exception:
            opts = []
        for o in opts:
            try:
                if not o.is_displayed():
                    continue
                d = (o.get_attribute("content-desc") or "").strip()
                if " - " not in d:
                    continue  # bukan opsi unit ('<kode> - <jenis>')
                if o.location["y"] < 1250:
                    continue  # di atas area opsi (judul/waktu/search)
                o.click()
                picked = True
                print(f"[TAMBAH UNIT] unit dipilih bebas: {d[:40]}")
                break
            except Exception:
                continue
        if not picked:
            print("[TAMBAH UNIT] tidak ada opsi unit -> SKIP + dump bukti")
            self._dump_screen("auto_tambah_unit_fail")
        time.sleep(0.3)
        self.wait_loading_done(max_wait=6)
        # pastikan kembali di Detail (modal tertutup)
        if not (self.is_present(self.DETAIL_HEADER, timeout=2)
                or self.is_present(self.BTN_LOG_PERGERAKAN, timeout=2)):
            try:
                self.driver.back()
            except Exception:
                pass
            time.sleep(0.2)
        print("[TAMBAH UNIT] selesai, kembali ke Detail")
        return picked

    # ----------------------------------------------------------------
    # Feeding WP: '+ Tambah WP' di halaman Detail
    # ----------------------------------------------------------------
    def tambah_wp_operasi(self):
        """Detail Feeding WP: tap '+ Tambah WP' (BUKAN FAB bulat) ->
        FORM 'Tambah WP' terbuka (bukti dump auto_bucket_fail run #3:
        field 'Waktu Mulai', 'Pilih WP', 'Pilih dumptruck', 'Simpan' -
        BUKAN modal picker). Pilih WP dari dropdown; kalau dropdown WP
        KOSONG -> GANTI otomatis: isi dumptruck lalu Simpan (jangan
        SKIP). Kalau Simpan gagal -> tutup form (back) supaya alur
        Detail berikutnya tetap jalan."""
        btn = self._first_clickable(self.BTN_TAMBAH_WP)
        if btn is None:
            self._scroll_to(self.BTN_TAMBAH_WP, max_scrolls=10)
            btn = self._first_clickable(self.BTN_TAMBAH_WP)
        if btn is None:
            print("[TAMBAH WP] tombol '+ Tambah WP' tidak ada/disabled -> SKIP")
            return False
        # form punya 'Waktu Mulai' -> tunggu beda menit dengan waktu
        # kegiatan terakhir (alur user: app menolak kalau semenit)
        self._wait_menit_berbeda()
        try:
            btn.click()
        except Exception as exc:
            print(f"[TAMBAH WP] tombol '+ Tambah WP' gagal di-tap -> SKIP ({exc})")
            return False
        # form 'Tambah WP' terbuka -> pilih WP dari dropdown. ALUR USER:
        # "pilih salah satu WP untuk OPERASI" -> lewati WP berstatus
        # Stop (bukti 24 Sep: '10800000233 - Stop' terpilih tapi simpan
        # DITOLAK app -> form terbuka lagi dengan field di-reset)
        time.sleep(0.3)
        self.wait_loading_done(max_wait=8)
        status = self.select_dropdown_option("WP", "Pilih WP", search_term="WP",
                                             avoid="Stop")
        if status == "ok":
            # CUKUP SEKALI (feedback user 24 Sep: 'gausah dua kali, cukup
            # sekali tambah aja'): pilih dumptruck SEKALI -> tunggu menit
            # beda -> Simpan SEKALI. Tidak ada loop percobaan ulang.
            self.select_dropdown_option("Dumptruck", "Pilih dumptruck",
                                        search_term="1DT")
            self._detail_opened_at = time.time()
            self._wait_menit_berbeda()
            ok = self._submit_tambah_wp_and_verify()
            if ok:
                print("[TAMBAH WP] WP dipilih & disimpan")
                return True
            print("[TAMBAH WP] simpan gagal -> dump bukti")
        else:
            # dropdown WP kosong -> GANTI otomatis: isi dumptruck & Simpan
            print("[TAMBAH WP] dropdown WP kosong -> GANTI otomatis: isi dumptruck lalu Simpan")
            self.select_dropdown_option("Dumptruck", "Pilih dumptruck",
                                        search_term="1DT")
            ok = self._submit_tambah_wp_and_verify()
            if ok:
                print("[TAMBAH WP] disimpan tanpa WP (ganti otomatis)")
                return True
            print("[TAMBAH WP] Simpan tanpa WP gagal -> dump bukti")
        self._dump_screen("auto_wp_form_fail")
        # tutup form supaya alur berikutnya (panah/bucket/tumpukan)
        # tetap berjalan di halaman Detail
        try:
            self.driver.back()
        except Exception:
            pass
        time.sleep(0.2)
        return False

    def _submit_tambah_wp_and_verify(self):
        """Simpan form 'Tambah WP' lalu VERIFIKASI form benar-benar
        tertutup PERMANEN. ALUR USER (24 Sep): 'Waktu Mulai' seksi TIDAK
        BOLEH SEMENIT dengan 'waktu kegiatan terakhir' - interaksi isi
        field terjadi di menit yang sama dengan Waktu Mulai seksi ->
        app MENOLAK simpan & me-reset field (bukti dump 24 Sep:
        Dumptruck kembali 'Pilih dumptruck'). -> tunggu menit berganti
        SETELAH isi, SEBELUM tap Simpan (maks ~1 menit)."""
        # baca Waktu Mulai SEKSI (desc DIAWALI ikon jam, pola
        # ', HH:MM, ' - BUKAN 'Waktu Mulai: 07:00' milik baris
        # unit) lalu tunggu menit wall-clock melewatinya
        try:
            shown = None
            for el in self.driver.find_elements(
                AppiumBy.XPATH, '//*[contains(@content-desc,":")]'
            ):
                m = re.match(r"^[-]+,?\s*(\d{1,2}):(\d{2})",
                             el.get_attribute("content-desc") or "")
                if m:
                    shown = int(m.group(1)) * 60 + int(m.group(2))
                    break
            if shown is not None:
                waited = 0
                now = time.localtime()
                while ((now.tm_hour * 60 + now.tm_min) <= shown
                       and waited < 65):
                    time.sleep(1)
                    waited += 1
                    now = time.localtime()
                if waited:
                    print(f"[TAMBAH WP] tunggu menit berganti {waited}s"
                          " (aturan Waktu Mulai vs kegiatan terakhir)")
        except Exception:
            pass
        ok = self.submit_or_confirm(scroll=False)
        time.sleep(0.2)
        self.handle_confirm_dialog(confirm=True, timeout=2)
        if not ok:
            return False
        form_title = (AppiumBy.XPATH, '//*[contains(@text,"Tambah Unit/Alat")]')
        for delay in (1.0, 2.0, 3.0):
            time.sleep(delay)
            reopened = (self.is_present(self.BTN_SUBMIT, timeout=0.8)
                        or self.is_present(form_title, timeout=0.8))
            if reopened:
                print("[TAMBAH WP] Simpan di-tap tapi form TERBUKA LAGI"
                      " (ditolak app) -> dump bukti")
                self._dump_screen("auto_wp_save_fail")
                return False
        return True

    def expand_wp_first(self):
        """
        Alur user Feeding WP: "klik panah untuk menampilkan WP yang
        telah ditambahkan agar muncul dibawahnya". Panah ekspand =
        ikon clickable pada baris WP. Strategi: (1) ikon panah chevron
        FontAwesome clickable di dekat teks 'WP', (2) fallback tap baris
        WP itu sendiri.
        """
        wp_text = (AppiumBy.XPATH, '//*[contains(@text,"WP")]')
        if not self.is_present(wp_text, timeout=2):
            self._scroll_to(wp_text, max_scrolls=12)
        # (1) ikon panah (chevron-down/right dll) clickable di dekat baris WP
        for icon in ("", "", "", "", "", ""):
            locator = (AppiumBy.XPATH, f'//*[@content-desc="{icon}" or @text="{icon}"]')
            try:
                els = self.driver.find_elements(*locator)
            except Exception:
                continue
            for el in els[:10]:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    if not el.is_displayed():
                        continue
                    el.click()
                    time.sleep(0.15)
                    # kalau setelah klik muncul field Bucket/tumpukan -> sukses
                    if self.is_present(
                        (AppiumBy.XPATH, '//*[contains(@text,"Bucket")]'),
                        timeout=2,
                    ):
                        print("[WP] panah ekspand WP diklik -> WP tampil")
                        return True
                except Exception:
                    continue
        # (2) fallback: tap baris WP yang clickable
        for xp in (
            '//*[contains(@content-desc,"WP") and @clickable="true"]',
            '//*[contains(@text,"WP") and @clickable="true"]',
        ):
            try:
                els = self.driver.find_elements(AppiumBy.XPATH, xp)
            except Exception:
                continue
            for el in els[:8]:
                try:
                    if not el.is_displayed():
                        continue
                    el.click()
                    time.sleep(0.15)
                    if self.is_present(
                        (AppiumBy.XPATH, '//*[contains(@text,"Bucket")]'),
                        timeout=2,
                    ):
                        print("[WP] baris WP diklik -> WP tampil")
                        return True
                except Exception:
                    continue
        # (3) GANTI otomatis: tidak ada baris WP (WP belum ditambahkan)
        # -> expand baris dumptruck supaya bagiannya (Bucket/tumpukan)
        # tetap tampil dan alur lanjut
        if self._expand_dumptruck_row():
            if (self.is_present(
                    (AppiumBy.XPATH, '//*[contains(@text,"Bucket")]'),
                    timeout=2)
                    or self.is_present(
                        (AppiumBy.XPATH, '//*[contains(@content-desc,"Tambah Tumpukan")'
                                          ' or contains(@content-desc,"Tambah Ritase")]'),
                        timeout=2)):
                print("[WP] baris WP tidak ada -> GANTI otomatis: baris dumptruck di-expand")
                return True
        print("[WP] panah ekspand WP tidak ditemukan -> SKIP")
        return False

    def tambah_tumpukan(self):
        """
        Alur user Feeding WP: "tambahkan tumpukan lanjut simpan dan klik
        OK" -> tombol 'Tambah Tumpukan' ATAU '+ Tambah Kode Tumpukan'
        (bukti dump auto_bucket_fail_3: tombol tumpukan di baris WP
        bernama '+ Tambah Kode Tumpukan' - label 'Kode' DIPERBOLEHKAN,
        hanya 'Kelola'/'Ritase' yang dikecualikan) -> form mini -> isi
        dummy (kode tumpukan pakai format KODE_TUMPUKAN_BARU) -> Simpan
        -> popup OK.
        """
        from utils.dummy_data import KODE_TUMPUKAN_BARU
        clicked_label = None
        for label in ("Tambah Tumpukan", "Tambahkan Tumpukan",
                      "Tambah Kode Tumpukan", "Tambahkan Kode Tumpukan",
                      "Tumpukan"):
            locator = (AppiumBy.XPATH,
                       f'//*[contains(@content-desc,"{label}") or contains(@text,"{label}")]')
            if not self.is_present(locator, timeout=2):
                continue
            try:
                els = self.driver.find_elements(*locator)
            except Exception:
                continue
            for el in els[:12]:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    desc = ((el.get_attribute("content-desc") or "")
                            + (el.get_attribute("text") or ""))
                    if "Kelola" in desc or "Ritase" in desc:
                        continue
                    if not el.is_displayed():
                        continue
                    el.click()
                    clicked_label = label
                    break
                except Exception:
                    continue
            if clicked_label:
                break
        if not clicked_label:
            print("[TUMPUKAN] tombol 'Tambah Tumpukan'/'+ Tambah Kode Tumpukan' tidak ada -> SKIP")
            return False
        time.sleep(0.15)
        self.wait_loading_done(max_wait=8)
        # form mini (kode tumpukan/dropdown) -> isi GENTLE (modal, sweep
        # menutupnya - pola sama dengan form status) -> Simpan/OK
        if "Kode" in clicked_label:
            # dialog kode tumpukan baru -> isi kode format baku + field lain
            self._fill_pile_code(KODE_TUMPUKAN_BARU)
        else:
            self._fill_status_form_gentle({})
        ok = self.submit_or_confirm(scroll=False)
        time.sleep(0.15)
        self.handle_confirm_dialog(confirm=True)  # popup OK
        print("[TUMPUKAN] tumpukan ditambahkan (OK)" if ok
              else "[TUMPUKAN] form tumpukan gagal disimpan -> dump bukti")
        if not ok:
            self._dump_screen("auto_tumpukan_form_fail")
        return ok

    def open_first_entry_detail(self):
        """
        Kalau form tambah diblokir app (entry hari ini sudah ada),
        buka DETAIL entry teratas yang tersimpan di list (kartu
        tanggal) supaya alur detail tetap teruji. Kembalikan True
        kalau berhasil membuka detail.
        """
        cards = None
        try:
            cards = self.driver.find_elements(
                AppiumBy.XPATH, '//*[contains(@text,"Sep 2026")]'
            )
        except Exception:
            pass
        if not cards:
            return False
        try:
            cards[0].click()
        except Exception:
            return False
        return self.handle_detail_after_save()

    def verify_entry_in_list(self, keyword="Tayan"):
        """
        Verifikasi pasca-simpan: pastikan berada di layar list, refresh
        filter tanggal hari ini, lalu ketik `keyword` di search bar
        untuk memastikan data yang baru ditambahkan muncul di hasil
        pencarian. Search dibersihkan kembali setelahnya.
        """
        if not self.is_present(self.SEARCH_INPUT, timeout=4):
            try:
                self.driver.back()
                time.sleep(0.4)
            except Exception:
                pass
        if not self.is_present(self.SEARCH_INPUT, timeout=4):
            return False
        # refresh filter tanggal (hari ini) setelah data masuk
        self.set_date_today()
        try:
            search = self.find(self.SEARCH_INPUT, timeout=3)
            search.click()
            search.send_keys(keyword)
            time.sleep(0.4)
            try:
                self.driver.hide_keyboard()
            except Exception:
                pass
            time.sleep(0.4)
            has_result = self.is_present(
                (AppiumBy.XPATH, f'//*[contains(@text,"{keyword}")]'), timeout=3
            )
            try:
                search = self.find(self.SEARCH_INPUT, timeout=2)
                search.clear()
            except Exception:
                pass
            time.sleep(0.15)
            return has_result
        except Exception:
            return False

    def set_first_item_status(self, statuses, fill_form=True):
        """
        Tab kelola ('Kelola WP' Feeding WP / 'Kelola Jembatan Timbang'
        Supply): tap tombol status pada item PALING ATAS. `statuses` =
        daftar kandidat dicoba berurutan sesuai kondisi app (mis.
        ['Mulai Operasi', 'Standby', 'Breakdown', 'Selesai']) - yang
        PERTAMA tersedia di layar yang di-tap ("sesuaikan dengan yang
        ada" sesuai skenario user). `fill_form=True`: kalau terbuka
        form status -> isi dummy -> Simpan -> OK ("isi formnya sampai
        ok" sesuai alur user). Kembalikan status yang berhasil, atau None.
        """
        for status in statuses:
            locator = (AppiumBy.XPATH,
                       f'//*[@content-desc="{status}" or @text="{status}"]')
            if not self.is_present(locator, timeout=3):
                continue
            try:
                els = self.driver.find_elements(*locator)
            except Exception:
                continue
            # urutkan berdasar POSISI LAYAR: kandidat paling atas =
            # tombol milik item teratas di list
            candidates = []
            for el in els:
                try:
                    if el.get_attribute("clickable") != "true":
                        continue
                    if not el.is_displayed():
                        continue
                    candidates.append((el.location["y"], el))
                except Exception:
                    continue
            clicked = False
            if candidates:
                candidates.sort(key=lambda t: t[0])
                try:
                    candidates[0][1].click()
                    clicked = True
                except Exception:
                    clicked = False
            if not clicked and els:
                try:
                    els[0].click()
                    clicked = True
                except Exception:
                    continue
            if clicked:
                time.sleep(0.25)
                self.wait_loading_done(max_wait=8)
                # form status (Kategori/Keterangan/Waktu) -> isi GENTLE
                # (modal, sweep menutupnya) -> Simpan/OK
                if fill_form and self.is_present(self.BTN_SUBMIT, timeout=3):
                    self._fill_status_form_gentle({})
                    self.submit_or_confirm(scroll=False)
                    time.sleep(0.15)
                self.handle_confirm_dialog(confirm=True, timeout=2)
                print(f"[STATUS] '{status}' diterapkan pada item teratas")
                return status
        print("[STATUS] tidak ada tombol status tersedia pada item teratas -> dump bukti")
        self._dump_screen("auto_status_fail")
        return None

    def set_wp_status_first_item(self, status="Selesai"):
        """Wrapper lama: tap `status` pada item WP PALING ATAS."""
        return self.set_first_item_status([status]) is not None

    # ----------------------------------------------------------------
    # Dialog konfirmasi
    # ----------------------------------------------------------------
    def handle_confirm_dialog(self, confirm: bool = True, timeout: float = 3):
        """Dialog 'Apakah Anda yakin ingin menyelesaikan tumpukan ini?' (Batal/OK).
        DEFENSIF: dialog bisa hilang saat animasi -> jangan pernah raise.
        `timeout` kecil (1-2) untuk jalur cepat supaya jeda tidak lama."""
        if confirm and self.is_present(self.CONFIRM_DIALOG_OK, timeout=timeout):
            if self.tap(self.CONFIRM_DIALOG_OK) is not None:
                time.sleep(0.25)
                return True
        if not confirm and self.is_present(self.CONFIRM_DIALOG_CANCEL, timeout=timeout):
            if self.tap(self.CONFIRM_DIALOG_CANCEL) is not None:
                time.sleep(0.25)
                return True
        return False

    # ----------------------------------------------------------------
    # Kelola Tumpukan (Ore Getting / Catching WP)
    # ----------------------------------------------------------------
    def finish_first_pile(self):
        """
        Tab 'Kelola Tumpukan': klik 'Selesai' pada item PALING ATAS saja,
        lalu konfirmasi OK pada dialog 'Apakah Anda yakin ingin
        menyelesaikan tumpukan ini?'.
        Tombol diurut berdasar POSISI LAYAR (paling atas = item teratas),
        bukan urutan tree (React Native tidak menjamin urutan node sama
        dengan urutan tampilan).
        Kembalikan True kalau aksi dilakukan, False kalau tidak ada
        item/tombol (SKIP).
        """
        locator = (AppiumBy.XPATH,
                   '//*[@content-desc="Selesai" or @text="Selesai"]')
        if not self.is_present(locator, timeout=5):
            print("[TUMPUKAN] tombol 'Selesai' tidak ada di tab Kelola Tumpukan -> dump bukti")
            self._dump_screen("auto_tumpukan_fail")
            return False
        try:
            els = self.driver.find_elements(*locator)
        except Exception:
            return False
        visible = []
        for el in els:
            try:
                if el.get_attribute("clickable") != "true":
                    continue
                if not el.is_displayed():
                    continue
                visible.append((el.location["y"], el))
            except Exception:
                continue
        if not visible:
            print("[TUMPUKAN] tombol 'Selesai' disabled semua (tumpukan sudah selesai?) -> dump bukti")
            self._dump_screen("auto_tumpukan_fail")
            return False
        visible.sort(key=lambda t: t[0])
        try:
            visible[0][1].click()  # paling atas = item teratas
        except Exception:
            return False
        time.sleep(0.25)
        confirmed = self.handle_confirm_dialog(confirm=True, timeout=2)
        time.sleep(0.25)
        print("[TUMPUKAN] tumpukan teratas diselesaikan (OK)" if confirmed
              else "[TUMPUKAN] tombol diklik tanpa dialog konfirmasi")
        return confirmed
