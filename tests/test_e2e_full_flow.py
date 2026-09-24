"""
End-to-End Flow (sesuai alur user, DIJALANKAN SEKALI SAJA dari login
sampai logout - tanpa login ulang / testing berulang):
1. Buka aplikasi OPEL -> Login -> masuk dengan GOOGLE ->
   pilih akun poetri4y@gmail.com -> berhasil ke Beranda
2. Beranda -> langsung pindah ke halaman Apps
3. Apps -> scroll ke bagian UBP BAUKSIT TAYAN
   3.1 Aktivitas Tambang  (tambah dummy -> simpan -> tambah LAGI ->
       log pergerakan -> Standby kuning + simpan -> Selesai merah + ya ->
       Kembali -> filter rentang tanggal masa lampau -> kembali)
   3.2 Ore Getting        (tambah dummy -> simpan -> Standby kuning +
       simpan -> isi Bucket -> Tambah Ritase -> Tambahkan Kode Tumpukan
       -> OK -> tambah dumptruck bebas -> hapus satu dumptruck -> OK ->
       Selesai merah + ya -> Kembali -> filter rentang tanggal masa
       lampau -> tab Kelola Tumpukan -> item teratas -> Selesai -> kembali)
   3.3 Feeding WP         (tambah dummy -> simpan -> + Tambah WP ->
       pilih WP Operasi -> simpan -> klik panah expand WP -> isi Bucket
       -> tambahkan tumpukan -> simpan -> OK -> Kembali -> filter
       rentang tanggal masa lampau -> tab Kelola WP -> status item
       teratas, isi form sampai OK -> kembali)
   3.4 Catching           (tambah dummy -> simpan -> log pergerakan ->
       Breakdown excavator + unggah foto -> simpan -> isi Bucket
       dumptruck -> Tambah Ritase -> dropdown kode tumpukan -> TAMBAHKAN
       kode tumpukan BARU + pilih kategori -> simpan -> popup OK ->
       Kembali -> filter rentang tanggal masa lampau -> Kelola Tumpukan
       -> item teratas -> Selesai + OK -> kembali)
   3.5 Supply             (tambah dummy -> simpan -> Bucket dumptruck ->
       Tambah Ritase + simpan -> popup OK -> Selesai merah + YA ->
       Kembali -> filter rentang tanggal masa lampau -> Kelola Jembatan
       Timbang -> item teratas -> Mulai Operasi/Standby/Breakdown
       (kecuali Selesai) -> isi form sampai OK -> kembali ke Fleet ->
       filter rentang tanggal masa lampau -> kembali)
   3.6 Barging            (tambah dummy -> simpan -> log pergerakan ->
       Kembali -> Selesai merah + YA -> Kembali -> filter rentang
       tanggal masa lampau -> kembali)
4. Profil -> scroll sampai bawah
5. Logout -> menu Keluar -> popup -> Ya

Aturan pengisian data (aturan app):
- TAMBAH data hanya boleh utk hari ini/kemarin -> pakai tanggal HARI INI
- Filter tanggal = KALENDER RENTANG TANGGAL MASA LAMPAU (lusa s/d
  kemarin), dipakai SETELAH data selesai diisi
- Dropdown -> pilih opsi pertama kalau ada, kalau modal search-select
  ketik kata kunci field (Tayan/EFO/1PS/1DT/TEST), SKIP kalau kosong
- Field teks -> isi data dummy, SKIP kalau tidak tersedia
- Semua langkah defensif: kalau elemen tidak ada, SKIP tanpa gagal

Jalankan seluruh flow:
    pytest tests/test_e2e_full_flow.py -v
"""
import pytest

from utils.nav_helper import ensure_logged_in, goto_apps_menu
from pages.home_page import HomePage
from pages.profile_page import ProfilePage
from pages.aktivitas_tambang_page import AktivitasTambangPage
from pages.ore_getting_page import OreGettingPage
from pages.feeding_wp_page import FeedingWpPage
from pages.catching_wp_page import CatchingWpPage
from pages.supply_page import SupplyPage
from pages.barging_page import BargingPage

from utils.dummy_data import (
    AKTIVITAS_TAMBANG_DUMMY,
    ORE_GETTING_DUMMY,
    FEEDING_WP_DUMMY,
    CATCHING_WP_DUMMY,
    SUPPLY_DUMMY,
    BARGING_DUMMY,
)


def _kerjakan_menu(driver, menu_opener, page_cls, dummy, nama):
    """Buka menu dari Apps, kerjakan semua yang tersedia, kembali ke Apps.
    `menu_opener` adalah bound method milik objek AppsPage (mis.
    apps.open_aktivitas_tambang) -> dipanggil tanpa argumen."""
    apps = goto_apps_menu(driver)
    menu_opener()
    page = page_cls(driver)
    page.do_all_available(dummy)
    page.go_back()
    print(f"[HASIL] {nama} [selesai]")


@pytest.mark.order(1)
def test_e2e_opel_flow(driver):
    # 1 & 2. Buka aplikasi & login dengan Google
    home = ensure_logged_in(driver)
    assert home.is_loaded(), "Gagal masuk ke Beranda"
    print("[HASIL] Login [berhasil]")

    # 3. Pilih Apps
    apps = goto_apps_menu(driver)
    assert apps.is_loaded(), "Halaman Apps tidak termuat"

    # 4. Menu Mining > UBP BAUKSIT TAYAN
    print("\n=== [3.1] Aktivitas Tambang ===")
    _kerjakan_menu(driver, apps.open_aktivitas_tambang, AktivitasTambangPage, AKTIVITAS_TAMBANG_DUMMY, "3.1 Aktivitas Tambang")
    print("\n=== [3.2] Ore Getting ===")
    _kerjakan_menu(driver, apps.open_ore_getting, OreGettingPage, ORE_GETTING_DUMMY, "3.2 Ore Getting")
    print("\n=== [3.3] Feeding WP ===")
    _kerjakan_menu(driver, apps.open_feeding_wp, FeedingWpPage, FEEDING_WP_DUMMY, "3.3 Feeding WP")
    print("\n=== [3.4] Catching ===")
    _kerjakan_menu(driver, apps.open_catching_wp, CatchingWpPage, CATCHING_WP_DUMMY, "3.4 Catching")

    # 5. Menu Quality Control > UBP BAUKSIT TAYAN
    print("\n=== [3.5] Supply ===")
    _kerjakan_menu(driver, apps.open_supply, SupplyPage, SUPPLY_DUMMY, "3.5 Supply")
    print("\n=== [3.6] Barging ===")
    _kerjakan_menu(driver, apps.open_barging, BargingPage, BARGING_DUMMY, "3.6 Barging")

    # 6. Kembali -> Beranda -> Profil
    print("\n=== [4] Profil (scroll sampai bawah) ===")
    home = ensure_logged_in(driver)
    home.goto_profil()
    print("[HASIL] 4 Profil [selesai]")

    # 7. Logout
    print("\n=== [5] Logout (Keluar -> Ya) ===")
    profile = ProfilePage(driver)
    assert profile.logout(), "Tombol logout tidak ditemukan - cek pages/profile_page.py"
    print("[HASIL] 5 Logout [selesai]")
