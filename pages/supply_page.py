"""
SupplyPage - berdasarkan scan device & emulator.

2 tab: Fleet (search 'Cari asal atau tujuan') dan Kelola Jembatan
Timbang (search 'Cari Jembatan Timbang').
Field form terverifikasi: Shift, Jenis Kegiatan, Pemeriksa, Plant,
Asal, Tujuan, Material, Jarak (m).
"""
from pages.list_menu_base_page import ListMenuBasePage

FIELDS = [
    {"label": "Shift", "type": "dropdown", "placeholder": "Pilih shift"},
    {"label": "Jenis Kegiatan", "type": "dropdown", "placeholder": "Pilih jenis kegiatan", "search": "Supply"},
    {"label": "Pemeriksa", "type": "dropdown", "placeholder": "Pilih pemeriksa", "search": "Check"},
    {"label": "Plant", "type": "dropdown", "placeholder": "Pilih plant", "search": "Block"},
    {"label": "Asal", "type": "dropdown", "placeholder": "Pilih asal", "search": "Tayan"},
    {"label": "Tujuan", "type": "dropdown", "placeholder": "Pilih tujuan", "search": "EFO"},
    {"label": "Jarak (m)", "type": "text"},
    {"label": "Ekskavator", "type": "dropdown", "placeholder": "Pilih ekskavator", "search": "1PS"},
    {"label": "Dumptruck", "type": "dropdown", "placeholder": "Pilih dumptruck", "search": "1DT"},
]


class SupplyPage(ListMenuBasePage):
    TITLE = "Supply"
    TABS = ["Fleet", "Kelola Jembatan Timbang"]
    SEARCH_PLACEHOLDER_BY_TAB = {
        "Fleet": "Cari asal atau tujuan",
        "Kelola Jembatan Timbang": "Cari Jembatan Timbang",
    }
    FIELDS = FIELDS

    def do_all_available(self, dummy_data: dict = None):
        """
        Skenario user (3.5 Supply), URUT sesuai alur user:
        1. tab Fleet, tanggal hari ini (aturan app utk tambah data)
        2. FAB tambah -> isi seluruh form dummy -> Simpan
        3. muncul data baru (Detail terbuka otomatis / buka entry teratas)
        4. bagian Dumptruck: isi Bucket
        5. Tambah Ritase -> isi form -> Simpan -> popup OK
        6. tombol Selesai (merah, global) -> konfirmasi 'YA'
        7. Kembali -> pilih tanggal 4 September 2026 -> kembali
        8. tab Kelola Jembatan Timbang -> item PALING ATAS -> pilih
           Mulai Operasi / Standby / Breakdown (KECUALI Selesai),
           sesuaikan yang tersedia -> ISI FORM sampai OK
        9. kembali ke tab Fleet -> cari tanggal 4 September 2026 -> kembali
        """
        self.open_tab("Fleet")
        self.ensure_date_today()
        print("[ALUR] 1) tab Fleet -> klik tombol tambah -> isi seluruh form dummy -> Simpan")
        if self.open_add_form():
            self.fill_form_fields(self.FIELDS, dummy_data or {})
            self.submit()
            self.after_save_wait_list_or_detail()
        print("[ALUR] 2) buka bagian Supply yang baru dibuat/diisi")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            print("[ALUR] 3) bagian Dumptruck: isi Bucket")
            self.fill_bucket_dumptruck()
            print("[ALUR] 4) klik Tambah Ritase -> isi form -> Simpan -> popup OK")
            self.tambah_ritase()          # isi form -> Simpan -> popup OK
            print("[ALUR] 5) tombol Selesai merah -> konfirmasi YA")
            self.tap_global_selesai()     # selesai merah -> YA
        print("[ALUR] 6) Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)")
        self.go_back_to_list()
        self.set_date_range_past()        # kalender rentang masa lampau
        print("[ALUR] 7) tab Kelola Jembatan Timbang -> item PALING ATAS")
        self.open_tab("Kelola Jembatan Timbang")
        self.tap_top_item()
        print("[ALUR] 8) pilih Mulai Operasi/Standby/Breakdown (KECUALI Selesai, sesuaikan yang ada) -> isi form sampai OK")
        self.set_first_item_status(
            ["Mulai Operasi", "Standby", "Breakdown"], fill_form=True
        )                                 # isi form status sampai OK
        print("[ALUR] 9) kembali ke tab Fleet -> filter rentang tanggal masa lampau")
        self.open_tab("Fleet")            # kembali ke tab Fleet
        self.set_date_range_past()        # kalender rentang masa lampau
