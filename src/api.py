"""
Modul: Game Info & API Integrator
Owner: Alwi (Dev 2)

Integrasi:
- howlongtobeatpy  -> estimasi durasi tamat (main_story, dalam jam)
- CheapShark API   -> harga & diskon terbaru

Kedua fungsi return None kalau gagal (bukan raise), supaya app.py gampang
cek: `if hasil is None: minta input manual`.
"""

import requests
from difflib import SequenceMatcher

try:
    from howlongtobeatpy import HowLongToBeat
except ImportError:
    HowLongToBeat = None

CHEAPSHARK_DEALS_URL = "https://www.cheapshark.com/api/1.0/deals"
CHEAPSHARK_HEADERS = {
    "User-Agent": "Backlogify/1.0 (Kelompok 3 - Program Fundamental Python UTS project)"
}


def _similarity(a, b):
    """Skor kemiripan dua string, 0.0 - 1.0. Dipakai buat milih hasil
    paling cocok waktu API balikin banyak kandidat untuk satu judul."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def get_estimated_hours(title):
    """
    Input   : title (str) - judul game
    Process : cari lewat howlongtobeatpy, lalu pilih hasil dengan judul
              paling mirip ke `title` (bukan asal ambil hasil pertama),
              dibungkus try-except karena HLTB scraping tidak resmi.
    Output  : est_hours (float, dari main_story) kalau ketemu & valid,
              None kalau API gagal / tidak ada hasil / main_story kosong.
    """
    if HowLongToBeat is None:
        return None

    try:
        results = HowLongToBeat().search(title)
    except Exception:
        # HLTB down, timeout, format response berubah, dll -> fallback manual
        return None

    if not results:
        return None

    best_match = max(results, key=lambda r: _similarity(title, r.game_name))

    if best_match.main_story is None or best_match.main_story <= 0:
        return None

    return float(best_match.main_story)


def get_discount_info(title):
    """
    Input   : title (str) - judul game
    Process : GET ke CheapShark /deals?title=..., lalu dari daftar deal
              yang balik, pilih yang judulnya (field "title") paling mirip
              ke `title`. Dibungkus try-except untuk network/HTTP error.
    Output  : dict {
                  "price_original": float,
                  "price_discounted": float,
                  "discount_percent": float
              } kalau ketemu, None kalau gagal / tidak ada deal.
    """
    try:
        response = requests.get(
            CHEAPSHARK_DEALS_URL,
            params={"title": title, "limit": 10},
            headers=CHEAPSHARK_HEADERS,
            timeout=5,
        )
        response.raise_for_status()
        deals = response.json()
    except Exception:
        # request gagal, timeout, response bukan JSON valid, dll -> fallback manual
        return None

    if not deals:
        return None

    def match_key(deal):
        title_score = _similarity(title, deal.get("title", ""))
        try:
            savings_score = float(deal.get("savings", 0))
        except (TypeError, ValueError):
            savings_score = 0.0
        # utamakan judul paling mirip; kalau seri (beberapa deal untuk
        # game yang sama dari toko berbeda), pilih yang diskonnya paling besar
        return (title_score, savings_score)

    best_match = max(deals, key=match_key)

    try:
        price_original = float(best_match["normalPrice"])
        price_discounted = float(best_match["salePrice"])
        discount_percent = float(best_match["savings"])
    except (KeyError, TypeError, ValueError):
        return None

    return {
        "price_original": price_original,
        "price_discounted": price_discounted,
        "discount_percent": discount_percent,
    }


if __name__ == "__main__":
    # Contoh pemanggilan manual, buat ngetes modul ini sendirian
    # (jalankan: python api.py)
    test_title = "Red Dead Redemption 2"

    print(f"Testing get_estimated_hours('{test_title}')...")
    hours = get_estimated_hours(test_title)
    if hours is not None:
        print(f"  -> Estimasi tamat: {hours} jam")
    else:
        print("  -> Gagal / tidak ketemu, pakai input manual.")

    print(f"\nTesting get_discount_info('{test_title}')...")
    discount = get_discount_info(test_title)
    if discount is not None:
        # Catatan: harga dari CheapShark dalam USD, bukan Rupiah
        print(f"  -> Harga asli   : ${discount['price_original']:,.2f} USD")
        print(f"  -> Harga diskon : ${discount['price_discounted']:,.2f} USD")
        print(f"  -> Diskon       : {discount['discount_percent']:.0f}%")
    else:
        print("  -> Gagal / tidak ketemu, pakai input manual.")