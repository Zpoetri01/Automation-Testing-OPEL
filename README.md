# OPEL Mobile Automation Testing (Appium + Python + Pytest)

Automation testing untuk aplikasi mobile **OPEL** (`com.antam.opel.development`, APK 2.5.15),
menggunakan Appium, Python, dan Pytest dengan pola **Page Object Model**.

## One Click

1. Pastikan tidak ada emulator tersembunyi yang bentrok:
   `restart_emulator.bat` (kalau jendela emulator tidak muncul)
2. Jalankan seluruh alur e2e (SEKALI jalan dari login sampai logout,
   tidak login ulang / testing berulang):
   `run_tests.bat`
   - otomatis: cek emulator (start kalau belum jalan) -> cek Appium -> pytest -> buka laporan
3. Hanya satu menu, mis. Supply (debugging):
   `run_tests.bat 07`

### Kalau mau dari Android Studio (Device Manager)
1. Buka **Device Manager** -> AVD **OPEL** -> klik ikon ✏️ (Edit)
2. **Graphics: Software - SwiftShader Indirect** (bukan Automatic)
3. **Memory (RAM): 3072 MB**
4. **Boot option: Cold boot** (matikan Quick boot)
5. Kalau AVD tidak mau start karena "already running", berarti masih ada
   proses emulator tersembunyi -> jalankan `restart_emulator.bat` dulu.

### Anti putus saat testing (sudah otomatis di bat)
```bat
adb -s emulator-5554 shell svc power stayon true
adb -s emulator-5554 shell settings put global window_animation_scale 0
adb -s emulator-5554 shell settings put global transition_animation_scale 0
adb -s emulator-5554 shell settings put global animator_duration_scale 0
```

## Alur Testing 

1. **Login** — Masuk -> GOOGLE -> akun `poetri4y@gmail.com` -> Beranda
2. **Beranda -> Apps** -> scroll ke **UBP BAUKSIT TAYAN**
3. **Menu** (tambah dummy -> aksi di detail -> Kembali -> filter **4 September 2026**):
   - 3.1 Aktivitas Tambang: tambah + isi form + simpan, **JANGAN Kembali
     dulu** -> **tambah lagi** (pilih bebas), Lihat Log Pergerakan ->
     kembali, Standby kuning + form dummy + simpan, Selesai merah + ya
   - 3.2 Ore Getting: tambah + simpan, Standby kuning + simpan, isi Bucket
     dumptruck, Tambah Ritase -> Tambahkan Kode Tumpukan -> **OK**,
     tambah dumptruck bebas, hapus salah satu dumptruck + OK,
     Selesai merah + ya; tab Kelola Tumpukan -> klik Selesai item teratas
   - 3.3 Feeding WP: tambah + simpan, `+ Tambah WP` (BUKAN FAB bulat)
     pada bagian dumptruck -> pilih WP Operasi + simpan, klik **PANAH**
     supaya WP yang ditambahkan muncul di bawahnya, isi Bucket WP +
     tambahkan tumpukan -> simpan -> OK; tab Kelola WP -> status item
     teratas (operasi/standby/breakdown/selesai, sesuaikan yang ada) ->
     isi form sampai OK
   - 3.4 Catching: tambah + simpan, Lihat Log Pergerakan -> kembali,
     Breakdown excavator (di bawah tombol log pergerakan) + **unggah
     foto otomatis** (foto dummy PNG di-push ke `/sdcard/Download`) +
     simpan, isi Bucket dumptruck, Tambah Ritase -> dropdown kode
     tumpukan -> **TAMBAHKAN kode tumpukan BARU + pilih kategori** ->
     simpan -> popup OK; tab Kelola Tumpukan -> klik Selesai item
     teratas -> OK
   - 3.5 Supply: tambah + simpan, Bucket dumptruck, Tambah Ritase +
     simpan -> popup OK, Selesai merah -> **YA**; tab Kelola Jembatan
     Timbang -> item teratas -> Mulai Operasi/Standby/Breakdown (kecuali
     Selesai) -> **isi formnya sampai OK**; kembali ke tab Fleet ->
     filter 4 September 2026
   - 3.6 Barging: tambah + simpan, Lihat Log Pergerakan -> Kembali,
     Selesai merah -> YA
4. **Profil** -> scroll sampai bawah
5. **Logout** -> menu **Keluar** -> popup -> **Ya**

> Aturan app: TAMBAH data hanya boleh utk tanggal hari ini/kemarin, jadi
> test memakai tanggal HARI INI saat mengisi, lalu memfilter ke
> 4 September 2026 setelah data masuk (sesuai skenario user).

## Instalasi

```bash
pip install -r requirements.txt
```

Prerequisite: Appium server (via `start_appium.bat`, atau `npm i -g appium` +
`appium driver install uiautomator2`), emulator/device dengan aplikasi OPEL
(uat) terpasang dan akun Google `poetri4y@gmail.com` sudah login di
Chrome/device tersebut.

## Konfigurasi (environment variable, opsional)

```bash
set OPEL_GOOGLE_EMAIL=poetri4y@gmail.com   # default sudah poetri4y
set OPEL_GOOGLE_PASSWORD=********          # hanya utk login manual (akun baru)
set APPIUM_SERVER=http://127.0.0.1:4723
set DEVICE_UDID=emulator-5554
```

## Menjalankan Test

```bash
pytest tests/test_01_login.py -v            # per test (mandiri)
pytest tests/test_e2e_full_flow.py -v       # seluruh alur sekaligus
pytest tests/ -v                            # semua test berurutan
```

## Struktur Project

```
opel-mobile-2/
├── config.py                   # capabilities, akun Google, tanggal target (4 Sep 2026)
├── conftest.py                 # fixture driver (session-scoped)
├── start_emulator.bat          # start emulator OPEL (jendela terlihat, anti crash)
├── restart_emulator.bat        # restart emulator kalau jendelanya tidak muncul
├── start_appium.bat            # start Appium server
├── run_tests.bat               # one click: emulator -> appium -> pytest -> report
├── pages/                      # Page Object per layar
│   ├── base_page.py            # helper umum (tap, type, scroll, FAB, toast)
│   ├── list_menu_base_page.py  # pola list + alur Detail (log pergerakan,
│   │                           #   Standby/Breakdown/Selesai, Bucket, Ritase,
│   │                           #   kode tumpukan baru, foto upload, kalender)
│   ├── login_page.py           # Masuk -> Google -> pilih akun (device & emulator)
│   ├── home_page.py            # bottom nav Beranda/Apps/Aktivitas/Profil
│   ├── apps_page.py            # UBP BAUKSIT TAYAN: Mining & Quality Control
│   ├── aktivitas_tambang_page.py / ore_getting_page.py / feeding_wp_page.py /
│   │   catching_wp_page.py / supply_page.py / barging_page.py
│   └── profile_page.py         # scroll bawah -> Keluar -> dialog -> Ya
├── utils/
│   ├── dummy_data.py           # data dummy + foto dummy (TEST_PHOTO_B64)
│   └── nav_helper.py           # login & navigasi mandiri per test
├── tests/                      # test_01..09 + test_e2e_full_flow
└── scans/                      # dump UI bukti locator (untuk verifikasi)
```

