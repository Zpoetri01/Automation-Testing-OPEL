"""
Konfigurasi Appium untuk automation testing aplikasi OPEL (Android).
Device di-detect otomatis dari `adb devices` (USB debugging, atau emulator
yang sedang jalan). Override lewat environment variable bila perlu.

Prioritas pemilihan device:
  1. DEVICE_UDID       -> pakai device dengan UDID tertentu
  2. DEVICE_NAME       -> nama device (untuk emulator, mis. "emulator-5554")
  3. adb devices       -> device pertama yang terhubung (USB / emulator)
"""

import os
import re
import shutil
import subprocess

APPIUM_SERVER = os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723")

APP_PACKAGE = "com.antam.opel.development"
# Activity utama terverifikasi via `cmd package resolve-activity`:
#   com.antam.opel.development/com.antam.opel.MainActivity
APP_ACTIVITY = "com.antam.opel.MainActivity"

# ---- Auto-detect device dari adb ----
ADB_PATH = os.getenv(
    "ADB_PATH",
    shutil.which("adb")
    or os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "Android", "Sdk", "platform-tools", "adb.exe",
    ),
)


def _adb(*args, timeout=15):
    """Jalankan adb dan kembalikan stdout (string)."""
    try:
        out = subprocess.run(
            [ADB_PATH, *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def list_connected_devices():
    """Kembalikan [(udid, state, model)] dari `adb devices -l`."""
    devices = []
    for line in _adb("devices", "-l").splitlines()[1:]:
        parts = line.split()
        # format: <udid>  device  [product:.. model:.. device:.. transport_id:..]
        if len(parts) < 2 or parts[1] != "device":
            continue
        info = dict(p.split(":", 1) for p in parts[2:] if ":" in p)
        devices.append((parts[0], parts[1], info.get("model", "")))
    return devices


def _detect_device():
    udid_env = os.getenv("DEVICE_UDID") or os.getenv("DEVICE_NAME")
    devices = list_connected_devices()
    if not devices:
        # Fallback: emulator standar (nanti kalau dipakai via emulator)
        return os.getenv("DEVICE_NAME", "emulator-5554"), None

    if udid_env:
        for udid, _, model in devices:
            if udid == udid_env:
                return udid, model
        # env diisi tapi tidak cocok dengan yang terhubung -> tetap pakai
        # device pertama (biasanya memang device yang baru dicolok)
    udid, _, model = devices[0]
    return udid, model


def _get_platform_version(udid: str):
    """Ambil versi Android dari device via adb (mis. '14')."""
    env = os.getenv("PLATFORM_VERSION")
    if env:
        return env
    out = _adb("-s", udid, "shell", "getprop", "ro.build.version.release")
    m = re.search(r"\d+(\.\d+)*", out or "")
    return m.group(0) if m else "13"


UDID, DEVICE_MODEL = _detect_device()
PLATFORM_VERSION = _get_platform_version(UDID)

CAPABILITIES = {
    "platformName": "Android",
    "appium:deviceName": DEVICE_MODEL or UDID,
    "appium:udid": UDID,
    "appium:platformVersion": PLATFORM_VERSION,
    "appium:automationName": "UiAutomator2",
    "appium:appPackage": APP_PACKAGE,
    "appium:appActivity": APP_ACTIVITY,
    # Gunakan noReset=True supaya sesi login Google tidak perlu diulang tiap run
    # kalau sudah pernah login sebelumnya di device/emulator.
    "appium:noReset": True,
    "appium:newCommandTimeout": 300,
    "appium:autoGrantPermissions": True,
    # Emulator RAM terbatas: XPath2 evaluator bisa hang saat UI thread sibuk
    # ('Timed out waiting for the root AccessibilityNodeInfo') -> pakai
    # XPath1 (query project ini sederhana, kompatibel).
    "appium:enforceXPath1": True,
}

# Akun Google untuk login (isi lewat environment variable, JANGAN hardcode password).
# Default = akun sesuai skenario user (poetri4y@gmail.com). Kalau email cocok
# (contains) dengan salah satu akun yang SUDAH tersimpan di device/emulator pada
# popup "Pilih akun" / dialog Chrome "Continue as", akun itu langsung dipilih
# (tanpa perlu password). Kalau tidak cocok, alur login akan tap
# "Gunakan akun lain" lalu isi GOOGLE_EMAIL & GOOGLE_PASSWORD secara manual.
GOOGLE_EMAIL = os.getenv("OPEL_GOOGLE_EMAIL", "poetri4y@gmail.com")
GOOGLE_PASSWORD = os.getenv("OPEL_GOOGLE_PASSWORD", "")

# Tanggal target sesuai skenario user: Jumat, 4 September 2026
TARGET_MONTH = "September"
TARGET_YEAR = "2026"
TARGET_DAY = 4

# Filter tanggal terbaru sesuai user (23 Sep 2026): KALENDER RENTANG
# TANGGAL MASA LAMPAU, BUKAN satu tanggal. Rentang = [lusa, kemarin]
# relatif terhadap hari ini saat test berjalan.
FILTER_START_DAYS_AGO = 2   # tanggal mulai rentang = lusa
FILTER_END_DAYS_AGO = 1     # tanggal akhir rentang = kemarin

# Hari libur yang DILEWATI saat memilih tanggal kerja (September 2026):
# - Sabtu/Minggu (akhir pekan)
# - (tidak ada libur nasional di September 2026)
TARGET_MONTH_HOLIDAYS = set()

DEFAULT_TIMEOUT = 10  # detik, untuk WebDriverWait
