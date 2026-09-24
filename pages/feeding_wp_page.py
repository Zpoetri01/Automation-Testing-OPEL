"""
FeedingWpPage - berdasarkan scan device & emulator + log run e2e.

2 tab: 'Kelola WP' dan 'Fleet', search 'Cari WP'.
Form Fleet (terverifikasi dari run e2e): Shift, Jenis Kegiatan,
Pemeriksa, Material, Plant, Asal, Kode Tumpukan, Ekskavator,
Dumptruck. Field yang belum ter-render tetap di-SKIP defensif oleh
core pengisian (form tervirtualisasi FlatList).
"""
from pages.list_menu_base_page import ListMenuBasePage

FIELDS = [
    {"label": "Shift", "type": "dropdown", "placeholder": "Pilih shift"},
    {"label": "Jenis Kegiatan", "type": "dropdown", "placeholder": "Pilih jenis kegiatan", "search": "Feeding"},
    {"label": "Pemeriksa", "type": "dropdown", "placeholder": "Pilih pemeriksa", "search": "Check"},
    {"label": "Material", "type": "dropdown", "placeholder": "Pilih material"},
    {"label": "Plant", "type": "dropdown", "placeholder": "Pilih plant", "search": "Block"},
    {"label": "Asal", "type": "dropdown", "placeholder": "Pilih asal", "search": "Tayan"},
    {"label": "Kode Tumpukan", "type": "dropdown", "placeholder": "Pilih kode tumpukan", "search": "TEST"},
    {"label": "Ekskavator", "type": "dropdown", "placeholder": "Pilih ekskavator", "search": "1PS"},
    {"label": "Dumptruck", "type": "dropdown", "placeholder": "Pilih dumptruck", "search": "1DT"},
]


class FeedingWpPage(ListMenuBasePage):
    TITLE = "Feeding WP"
    TABS = ["Kelola WP", "Fleet"]
    SEARCH_PLACEHOLDER = "Cari WP"
    FIELDS = FIELDS

    def do_all_available(self, dummy_data: dict = None):
        """
        Skenario user (3.3 Feeding WP), URUT sesuai alur user:
        1. tab Fleet, tanggal hari ini (aturan app utk tambah data)
        2. FAB tambah -> isi seluruh form dummy -> Simpan
        3. muncul data baru -> buka entry teratas (kalau Detail belum
           terbuka otomatis setelah Simpan)
        4. tombol '+ Tambah WP' (BUKAN FAB bulat) -> pilih salah satu
           WP untuk Operasi -> Simpan
        5. klik PANAH untuk menampilkan WP yang ditambahkan
        6. isi Bucket pada WP tsb -> tambahkan tumpukan -> Simpan -> OK
        7. Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)
        8. tab Kelola WP -> item PALING ATAS -> pilih salah satu status
           (Mulai Operasi / Standby / Breakdown / Selesai, sesuaikan
           yang tersedia) -> isi form sampai OK -> kembali
        """
        self.open_tab("Fleet")
        self.ensure_date_today()
        print("[ALUR] 1) tab Fleet -> klik tombol tambah -> isi seluruh form dummy -> Simpan")
        if self.open_add_form():
            self.fill_form_fields(self.FIELDS, dummy_data or {})
            self.submit()
            self.after_save_wait_list_or_detail()
        print("[ALUR] 2) buka bagian Feeding WP yang baru dibuat/diisi")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            print("[ALUR] 3) klik '+ Tambah WP' (BUKAN tombol tambah bulat) -> pilih WP Operasi -> Simpan")
            self.tambah_wp_operasi()       # + Tambah WP -> pilih WP -> Simpan
            print("[ALUR] 4) klik panah -> WP yang ditambahkan tampil di bawahnya")
            self.expand_wp_first()         # klik panah -> WP muncul di bawah
            print("[ALUR] 5) isi Bucket WP -> tambahkan tumpukan -> Simpan -> OK")
            self.fill_bucket_wp()          # isi Bucket pada WP
            self.tambah_tumpukan()         # tambahkan tumpukan -> Simpan -> OK
        print("[ALUR] 6) Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)")
        self.go_back_to_list()
        self.set_date_range_past()        # kalender rentang masa lampau
        print("[ALUR] 7) tab Kelola WP -> item PALING ATAS -> pilih status yang tersedia (Operasi/Standby/Breakdown/Selesai) -> isi form sampai OK")
        self.open_tab("Kelola WP")
        self.set_first_item_status(self.STATUS_BUTTONS, fill_form=True)
