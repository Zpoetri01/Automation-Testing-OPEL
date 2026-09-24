"""
CatchingWpPage - berdasarkan scan device & emulator.

2 tab: Fleet (tanggal + search + FAB + form) dan Kelola Tumpukan
(item tumpukan + tombol 'Selesai' -> dialog Batal/OK).
Field form terverifikasi: Shift, Jenis Kegiatan, Pemeriksa, Material,
Plant, Asal, Tujuan, Jarak (m).
"""
from pages.list_menu_base_page import ListMenuBasePage

FIELDS = [
    {"label": "Shift", "type": "dropdown", "placeholder": "Pilih shift"},
    {"label": "Jenis Kegiatan", "type": "dropdown", "placeholder": "Pilih jenis kegiatan", "search": "Catching"},
    {"label": "Pemeriksa", "type": "dropdown", "placeholder": "Pilih pemeriksa", "search": "Check"},
    {"label": "Material", "type": "dropdown", "placeholder": "Pilih material", "search": "WASHED"},
    {"label": "Plant", "type": "dropdown", "placeholder": "Pilih plant", "search": "Block"},
    {"label": "Asal", "type": "dropdown", "placeholder": "Pilih asal", "search": "1080"},
    {"label": "Tujuan", "type": "dropdown", "placeholder": "Pilih tujuan", "search": "EFO"},
    {"label": "Jarak (m)", "type": "text"},
    {"label": "Ekskavator", "type": "dropdown", "placeholder": "Pilih ekskavator", "search": "1PS"},
    {"label": "Dumptruck", "type": "dropdown", "placeholder": "Pilih dumptruck", "search": "1DT"},
]


class CatchingWpPage(ListMenuBasePage):
    TITLE = "Catching"
    TABS = ["Fleet", "Kelola Tumpukan"]
    SEARCH_PLACEHOLDER = "Cari asal, tujuan atau kode tumpukan"
    FIELDS = FIELDS

    def do_all_available(self, dummy_data: dict = None):
        """
        Skenario user (3.4 Catching), URUT sesuai alur user:
        1. tab Fleet, tanggal hari ini (aturan app utk tambah data)
        2. FAB tambah -> isi seluruh form dummy -> Simpan
        3. muncul data baru -> buka entry teratas (kalau Detail belum
           terbuka otomatis setelah Simpan)
        4. Lihat Log Pergerakan -> kembali
        5. bagian excavator: Breakdown -> isi form dummy SAMPAI unggah
           foto (foto item dummy di-push otomatis) -> Simpan
        6. bagian Dumptruck: isi Bucket
        7. Tambah Ritase -> dropdown 'Pilih kode tumpukan' ->
           TAMBAHKAN KODE TUMPUKAN BARU + pilih Kategori -> Simpan
           -> popup OK
        8. Kembali -> cari tanggal 4 September 2026
        9. tab Kelola Tumpukan -> item PALING ATAS -> tombol Selesai
           -> konfirmasi OK -> kembali
        """
        self.open_tab("Fleet")
        self.ensure_date_today()
        print("[ALUR] 1) tab Fleet -> klik tombol tambah -> isi seluruh form dummy -> Simpan")
        if self.open_add_form():
            self.fill_form_fields(self.FIELDS, dummy_data or {})
            self.submit()
            self.after_save_wait_list_or_detail()
        print("[ALUR] 2) buka bagian Catching yang baru dibuat/diisi")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            print("[ALUR] 3) Lihat Log Pergerakan -> kembali")
            self.open_log_pergerakan_and_back()
            print("[ALUR] 4) Breakdown bagian excavator -> isi form + unggah foto otomatis -> Simpan")
            self.breakdown_with_photo()
            print("[ALUR] 5) bagian Dumptruck: isi Bucket")
            self.fill_bucket_dumptruck()
            print("[ALUR] 6) Tambah Ritase -> tambahkan kode tumpukan BARU + pilih kategori -> Simpan -> popup OK")
            self.tambah_ritase(create_new_pile=True)
        print("[ALUR] 7) Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)")
        self.go_back_to_list()
        self.set_date_range_past()
        print("[ALUR] 8) tab Kelola Tumpukan -> item PALING ATAS -> klik Selesai -> OK")
        self.open_tab("Kelola Tumpukan")
        self.finish_first_pile()
