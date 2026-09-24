import sys
import time

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_connection import AppiumConnection

from config import APPIUM_SERVER, CAPABILITIES

# Console Windows biasanya cp1252 -> print content-desc berisi ikon
# FontAwesome (mis. '') akan melempar UnicodeEncodeError dan
# MEMATIKAN test di tengah alur. Paksa UTF-8 dengan fallback 'replace'.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class ResilientAppiumConnection(AppiumConnection):
    """AppiumConnection yang TAHAN 'socket hang up' transien: koneksi
    adb/HTTP kedip sebentar, atau server uiautomator2 di device putus
    sesaat, TIDAK boleh mematikan seluruh run e2e. Perintah yang sama
    diulang dengan backoff pendek. Klik ganda akibat retry jarang dan
    lebih baik daripada run 40 menit hilang."""

    _TRANSIENT_MARKERS = (
        "socket hang up", "could not proxy", "connection reset",
        "connection aborted", "broken pipe",
    )

    def execute(self, command, params=None, timeout=None):
        for attempt in range(4):
            if attempt:
                time.sleep(0.4 * attempt)
            try:
                resp = super().execute(command, params)
            except Exception as e:  # noqa: BLE001
                if self._is_transient(str(e)) and attempt < 3:
                    print(f"  [RETRY] koneksi kedip ({e}) -> coba {attempt + 1}/3")
                    continue
                raise
            err = self._resp_error(resp)
            if err and self._is_transient(err) and attempt < 3:
                print(f"  [RETRY] server putus ({err}) -> coba {attempt + 1}/3")
                continue
            return resp
        return resp  # tidak tercapai

    @classmethod
    def _is_transient(cls, text):
        t = (text or "").lower()
        return any(m in t for m in cls._TRANSIENT_MARKERS)

    @staticmethod
    def _resp_error(resp):
        try:
            value = resp.get("value") if isinstance(resp, dict) else None
            if isinstance(value, dict) and "error" in value:
                return value.get("message") or ""
        except Exception:
            pass
        return ""


@pytest.fixture(scope="session")
def driver():
    options = UiAutomator2Options().load_capabilities(CAPABILITIES)
    drv = webdriver.Remote(ResilientAppiumConnection(APPIUM_SERVER), options=options)
    # 0.5s BUKAN 2s: implicit wait 2s membuat SETIAP lookup elemen yang
    # belum ada bayar 2 detik (mis. polling 'Simpan' di luar viewport,
    # opsi modal belum ter-load) - menumpuk jadi jeda menit per halaman.
    # Eksplisit WebDriverWait (find/find_clickable/is_present) tidak
    # terpengaruh: mereka tetap polling sendiri sampai timeout-nya.
    drv.implicitly_wait(0.5)
    yield drv
    drv.quit()
