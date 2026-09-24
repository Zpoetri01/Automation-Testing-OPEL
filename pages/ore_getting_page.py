"""
OreGettingPage - TERVERIFIKASI dari scan device & emulator.

2 tab: Fleet (tanggal + search 'Cari asal atau tujuan' + FAB + form)
dan Kelola Tumpukan (search 'Cari Kode Tumpukan' + item tumpukan
dengan tombol 'Selesai' -> dialog konfirmasi Batal/OK).

Form field terverifikasi: Shift, Jenis Kegiatan, Pemeriksa, Plant,
Asal, Tujuan, Jarak (m), Ekskavator.
"""
from pages.list_menu_base_page import ListMenuBasePage

FIELDS = [
    {"label": "Shift", "type": "dropdown", "placeholder": "Pilih shift"},
    {"label": "Jenis Kegiatan", "type": "dropdown", "placeholder": "Pilih jenis kegiatan", "search": "Getting"},
    {"label": "Pemeriksa", "type": "dropdown", "placeholder": "Pilih pemeriksa", "search": "Check"},
    {"label": "Material", "type": "dropdown", "placeholder": "Pilih material", "search": "WASHED"},
    {"label": "Plant", "type": "dropdown", "placeholder": "Pilih plant", "search": "Block"},
    {"label": "Asal", "type": "dropdown", "placeholder": "Pilih asal", "search": "1080"},
    {"label": "Tujuan", "type": "dropdown", "placeholder": "Pilih tujuan", "search": "EFO"},
    {"label": "Jarak (m)", "type": "text"},
    {"label": "Ekskavator", "type": "dropdown", "placeholder": "Pilih ekskavator", "search": "1PS"},
    {"label": "Dumptruck", "type": "dropdown", "placeholder": "Pilih dumptruck", "search": "1DT"},
]


class OreGettingPage(ListMenuBasePage):
    TITLE = "Ore Getting"
    TABS = ["Fleet", "Kelola Tumpukan"]
    SEARCH_PLACEHOLDER = "Cari asal atau tujuan"
    FIELDS = FIELDS

    def do_all_available(self, dummy_data: dict = None):
        """
        Skenario user (3.2 Ore Getting), URUT sesuai alur user + REVISI
        23 Sep:
        1. tab Fleet, tanggal hari ini (aturan app utk tambah data)
        2. FAB tambah -> isi seluruh form dummy -> Simpan
        3. muncul data baru -> buka entry teratas (kalau Detail belum
           terbuka otomatis setelah Simpan)
        4. tombol Standby (kuning, global) -> isi form dummy -> Simpan
        5. bagian Dumptruck: isi Bucket DULU
        6. klik Tambah Ritase -> muncul Tambah Kode Tumpukan -> OK
           (REVISI 23 Sep: SETELAH KODE JANGAN DISELESAIKAN DULU - kalau
           entry Selesai merah dulu, tumpukan TIDAK MUNCUL di Kelola
           Tumpukan)
        7. klik tombol tambah -> pilih dumptruck bebas
        8. klik tombol Hapus pada salah satu dumptruck -> OK
        9. Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)
        10. tab Kelola Tumpukan -> tumpukan MUNCUL -> klik Selesai -> OK
        11. kembali ke tab Fleet -> Selesai merah -> Ya (alur Selesai
            merah tetap dijalankan SETELAH tumpukan diselesaikan)
        """
        self.open_tab("Fleet")
        self.ensure_date_today()
        print("[ALUR] 1) tab Fleet -> klik tombol tambah -> isi seluruh form dummy -> Simpan")
        if self.open_add_form():
            self.fill_form_fields(self.FIELDS, dummy_data or {})
            self.submit()
            self.after_save_wait_list_or_detail()
        print("[ALUR] 2) buka bagian Ore Getting yang baru dibuat/diisi")
        if not self.wait_for_detail():
            self.go_back_to_list()
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            print("[ALUR] 3) tombol Standby kuning -> isi form dummy -> Simpan")
            self.standby_then_save()                      # standby kuning
            print("[ALUR] 4) bagian Dumptruck: isi Bucket DULU")
            self.fill_bucket_dumptruck()                  # bucket dulu
            print("[ALUR] 5) klik Tambah Ritase -> muncul Tambah Kode Tumpukan -> OK")
            self.tambah_ritase(create_new_pile=True)      # tambahkan kode tumpukan -> OK
            print("[ALUR] 6) klik tombol tambah -> pilih dumptruck bebas")
            self.tambah_dumptruck()                       # tambah dumptruck bebas
            print("[ALUR] 7) klik Hapus pada salah satu dumptruck -> OK")
            self.hapus_first_dumptruck()                  # hapus salah satu -> OK
            # REVISI 23 Sep: JANGAN Selesai merah dulu - biarkan tumpukan
            # MUNCUL di tab Kelola Tumpukan (entry selesai = tumpukan hilang)
        print("[ALUR] 8) klik Kembali -> filter rentang tanggal masa lampau (lusa s/d kemarin)")
        self.go_back_to_list()
        self.set_date_range_past()                        # kalender rentang masa lampau
        # ---- Kelola Tumpukan: tumpukan muncul -> Selesai ----
        print("[ALUR] 9) tab Kelola Tumpukan -> item PALING ATAS -> klik Selesai")
        self.open_tab("Kelola Tumpukan")
        self.finish_first_pile()
        # ---- kembali ke Fleet -> Selesai merah + Ya (alur asli) ----
        print("[ALUR] 10) tab Fleet -> buka entry -> Selesai merah -> Ya")
        self.open_tab("Fleet")
        if not self.wait_for_detail():
            self.open_first_entry_in_list()
        if self.wait_for_detail():
            self.tap_global_selesai()                     # selesai merah -> ya
