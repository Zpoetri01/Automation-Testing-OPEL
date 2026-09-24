"""
Data dummy untuk mengisi field bertipe TEXT (EditText) di form.
Key HARUS sama persis dengan label field ("Deskripsi Lokasi", "Jarak (m)", dst)
karena dipakai oleh ListMenuBasePage.fill_form_fields().

Field bertipe DROPDOWN ("Shift", "Plant", dst) TIDAK diisi dari sini -
lihat TODO di pages/list_menu_base_page.py (select_dropdown_option) karena
opsi/isi pilihan dropdown belum ter-capture di locator manapun.
"""

import random
import string


def random_number(min_val=1, max_val=999):
    return random.randint(min_val, max_val)


def random_text(prefix="TEST", length=5):
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}-{suffix}"


# --- Aktivitas Tambang ---
AKTIVITAS_TAMBANG_DUMMY = {
    "Deskripsi Lokasi": random_text("LOKASI"),
    "Jarak (m)": random_number(10, 500),
}

# --- Ore Getting ---
ORE_GETTING_DUMMY = {
    "Jarak (m)": random_number(10, 500),
}

# --- Feeding WP --- (field form belum diketahui, dikosongkan dulu)
FEEDING_WP_DUMMY = {}

# --- Catching WP ---
CATCHING_WP_DUMMY = {
    "Jarak (m)": random_number(10, 500),
}

# --- Supply ---
SUPPLY_DUMMY = {
    "Jarak (m)": random_number(10, 500),
}

# --- Barging ---
BARGING_DUMMY = {
    "Jarak (m)": random_number(10, 500),
}

# --- Foto dummy untuk upload (form Breakdown Catching WP) ---
# PNG 64x64 polos (merah), dibuat manual supaya test TIDAK butuh file eksternal.
# Dipush ke /sdcard/Download/opel_test_photo.png lalu dipilih lewat photo picker.
TEST_PHOTO_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAe0lEQVR4nO3PUQkAIBTAwBfMEPYPYA5D+HEIgwW4"
    "zdnr64YLGtCCBrSgAS1oQAsa0IIGtKABLWhACxrQgga0oAEtaEALGtCCBrSgAS1oQAsa0IIGtKABLWhACxrQgga0"
    "oAEtaEALGtCCBrSgAS1oQAsa0IIGtKABLXjsAoMhIVqZxCarAAAAAElFTkSuQmCC"
)

# Data dummy tambahan utk form kecil di halaman Detail
BUCKET_VALUE = random_number(3, 25)  # isian Bucket dumptruck
KODE_TUMPUKAN_BARU = f"TEST{random_number(100000, 999999)}"  # kode tumpukan baru
