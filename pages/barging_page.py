"""
BargingPage - berdasarkan scan device & emulator.

Tanpa sub-tab. Field form terverifikasi: Shift, Jenis Kegiatan,
Pemeriksa, Material, Plant, Asal, Tujuan, Jarak (m).
"""
from pages.list_menu_base_page import ListMenuBasePage

FIELDS = [
    {"label": "Shift", "type": "dropdown", "placeholder": "Pilih shift"},
    {"label": "Jenis Kegiatan", "type": "dropdown", "placeholder": "Pilih jenis kegiatan", "search": "Barging"},
    {"label": "Pemeriksa", "type": "dropdown", "placeholder": "Pilih pemeriksa", "search": "Check"},
    {"label": "Material", "type": "dropdown", "placeholder": "Pilih material"},
    {"label": "Plant", "type": "dropdown", "placeholder": "Pilih plant", "search": "Block"},
    {"label": "Asal", "type": "dropdown", "placeholder": "Pilih asal", "search": "Tayan"},
    {"label": "Tujuan", "type": "dropdown", "placeholder": "Pilih tujuan", "search": "EFO"},
    {"label": "Jarak (m)", "type": "text"},
    {"label": "Ekskavator", "type": "dropdown", "placeholder": "Pilih ekskavator", "search": "1PS"},
]


class BargingPage(ListMenuBasePage):
    TITLE = "Barging"
    SEARCH_PLACEHOLDER = "Cari asal atau tujuan"
    FIELDS = FIELDS

    def do_all_available(self, dummy_data: dict = None):
        """
        Skenario user (3.6 Barging), URUT sesuai alur user:
        1. tanggal hari ini (aturan app utk tambah data)
        2. FAB tambah -> isi seluruh form dummy -> Simpan
        3. muncul data baru -> buka entry teratas (kalau Detail belum
           terbuka otomatis setelah Simpan)
        4. Lihat Log Pergerakan -> kembali
        5. tombol Selesai (merah, global) -> konfirmasi 'YA'
        6. Kembali -> pilih tanggal 4 September 2026 -> kembali
        """
        self.ensure_date_today()
        print("[ALUR] 1) klik tombol tambah -> isi seluruh form dummy -> Simpan")
        if self.open_add_form():
            self.fill_form_fields(self.FIELDS, dummy_data or {})
            self.submit()
            self.after_save_wait_list_or_detail()
        print("[ALUR] 2) buka bagian Barging yang baru dibuat/diisi")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            print("[ALUR] 3) Lihat Log Pergerakan -> kembali")
            self.open_log_pergerakan_and_back()
            print("[ALUR] 4) tombol Selesai merah -> konfirmasi YA")
            self.tap_global_selesai()
        print("[ALUR] 5) Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)")
        self.go_back_to_list()
        self.set_date_range_past()
