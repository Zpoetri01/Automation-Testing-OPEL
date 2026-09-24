"""
AktivitasTambangPage - TERVERIFIKASI dari scan device & emulator.

List: tombol back, filter Tanggal, search 'Cari asal atau tujuan',
FAB tambah data. Form: District (read-only), dropdown Shift / Jenis
Kegiatan / Pemeriksa / Plant / Lokasi / Unit-Alat, teks Deskripsi
Lokasi & Jarak (m), tombol Simpan. Tidak ada sub-tab.
"""
from pages.list_menu_base_page import ListMenuBasePage
import time

FIELDS = [
    {"label": "Shift", "type": "dropdown", "placeholder": "Pilih shift"},
    {"label": "Jenis Kegiatan", "type": "dropdown", "placeholder": "Pilih jenis kegiatan", "search": "Aktivitas"},
    {"label": "Pemeriksa", "type": "dropdown", "placeholder": "Pilih pemeriksa", "search": "Check"},
    {"label": "Plant", "type": "dropdown", "placeholder": "Pilih plant", "search": "Block"},
    {"label": "Lokasi", "type": "dropdown", "placeholder": "Pilih lokasi", "search": "Tayan"},
    {"label": "Deskripsi Lokasi", "type": "text"},
    {"label": "Jarak (m)", "type": "text"},
    {"label": "Unit/Alat", "type": "dropdown", "placeholder": "Pilih unit/alat", "search": "1PS"},
]


class AktivitasTambangPage(ListMenuBasePage):
    TITLE = "Aktivitas Tambang"
    SEARCH_PLACEHOLDER = "Cari asal atau tujuan"
    FIELDS = FIELDS

    def do_all_available(self, dummy_data: dict = None):
        """
        Skenario user (3.1 Aktivitas Tambang):
        1. filter tanggal -> hari ini (aturan app: tambah data hanya
           utk hari ini/kemarin)
        2. FAB tambah -> isi SELURUH form dummy -> Simpan
        3. muncul data baru di list
        4. klik tombol TAMBAH LAGI dan pilih bebas (tambah entry kedua)
        5. buka entry teratas -> Lihat Log Pergerakan -> kembali
        6. tombol Standby (kuning, global) -> isi form dummy -> Simpan
        7. tombol Selesai (merah, global) -> konfirmasi 'Ya'
        8. Kembali ke list -> filter tanggal 4 September 2026 -> kembali
        """
        self.ensure_date_today()
        # ---- tambah entry #1 (dari list, FAB) ----
        print("[ALUR] 1) klik tombol tambah -> isi seluruh form dummy -> Simpan")
        if self.open_add_form():
            self.fill_form_fields(self.FIELDS, dummy_data or {})
            self.submit()
            self.after_save_wait_list_or_detail()
        # ---- data baru muncul: halaman DETAIL entry tsb terbuka
        # (halaman yang sama dengan Lihat Log Pergerakan). JANGAN
        # Kembali dulu -> klik tombol TAMBAH BESAR di halaman Detail
        # itu = modal 'Tambah Unit/Alat' -> pilih SATU unit bebas ----
        print("[ALUR] 2) di halaman Detail entry baru -> klik tombol TAMBAH besar -> modal 'Tambah Unit/Alat' -> pilih unit bebas")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            self.tambah_entry_dari_detail()
        # ---- kembali ke Detail entry -> alur Detail ----
        print("[ALUR] 3) buka entry teratas -> Lihat Log Pergerakan -> kembali")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            self.open_log_pergerakan_and_back()
            print("[ALUR] 4) tombol Standby kuning -> isi form dummy -> Simpan")
            self.standby_then_save()
            print("[ALUR] 5) tombol Selesai merah -> konfirmasi Ya")
            self.tap_global_selesai()
        # ---- kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin) ----
        print("[ALUR] 6) klik Kembali -> filter rentang tanggal masa lampau")
        self.go_back_to_list()
        self.set_date_range_past()
