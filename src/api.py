"""
Modul: Game Info & API Integrator
Owner: Alwi (Dev 2)

Integrasi:
- howlongtobeatpy  -> estimasi durasi tamat (main_story, main_extra, completionist)
- CheapShark API   -> harga & diskon terbaru, dikonversi ke Rupiah pakai
                    get_usd_to_idr_rate dari helpers.py

Semua fungsi publik return None kalau gagal (bukan raise), supaya app.py
gampang cek: `if hasil is None: minta input manual`.
"""

import json
import urllib.parse
import urllib.request
from difflib import SequenceMatcher

from howlongtobeatpy import HowLongToBeat

from helpers import get_usd_to_idr_rate

CHEAPSHARK_DEALS_URL = "https://www.cheapshark.com/api/1.0/deals"
CHEAPSHARK_HEADERS = {
    "User-Agent": "Backlogify/1.0 (Kelompok 3 - Program Fundamental Python UTS project)"
}


def _similarity(a, b):
    """Skor kemiripan dua string, 0.0 - 1.0. Dipakai khusus untuk CheapShark,
    karena API itu tidak punya similarity bawaan seperti HowLongToBeat."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def get_estimated_hours(title):
    """
    Input   : title (str) - judul game
    Process : cari lewat howlongtobeatpy, ambil entry dengan similarity
            tertinggi (dihitung otomatis oleh howlongtobeatpy sendiri),
            lalu kumpulkan tiga jenis durasi yang tersedia untuk game itu.
    Output  : dict {"main_story": float|None, "main_extra": float|None,
            "completionist": float|None} kalau game ketemu, None kalau
            API gagal / game tidak ketemu. Sebuah gaya main bernilai None
            kalau HLTB memang tidak punya data itu untuk game ini, bukan
            berarti durasinya 0 jam.
    """
    try:
        results = HowLongToBeat().search(title)
        if not results:
            return None

        best_match = max(results, key=lambda r: r.similarity)

        return {
            "main_story": float(best_match.main_story) if best_match.main_story else None,
            "main_extra": float(best_match.main_extra) if best_match.main_extra else None,
            "completionist": float(best_match.completionist) if best_match.completionist else None,
        }
    except Exception:
        return None


def get_discount_info(title):
    """
    Input   : title (str) - judul game
    Process : GET ke CheapShark /deals?title=..., lalu dari daftar deal
            yang balik, pilih yang judulnya (field "title") paling mirip
            ke `title` lewat _similarity, karena CheapShark mencocokkan
            title sebagai substring dan bisa membalikkan game lain juga.
            Kalau ada beberapa deal untuk judul yang sama persis (dari
            toko berbeda), diambil yang diskonnya paling besar. Harga
            dari CheapShark selalu USD, jadi dikonversi ke Rupiah pakai
            get_usd_to_idr_rate sebelum dikembalikan.
    Output  : dict {
                "price_original": float (Rp),
                "price_discounted": float (Rp),
                "discount_percent": float
            } kalau ketemu, None kalau gagal / tidak ada deal.
            Catatan: ini harga toko luar negeri yang dikonversi pakai
            kurs pasar, bukan harga toko lokal Indonesia. Banyak toko
            (termasuk Steam) pakai regional pricing sendiri yang biasanya
            lebih murah dari hasil konversi langsung ini, jadi tetap
            anggap sebagai referensi, bukan harga pasti.
    """
    query = urllib.parse.urlencode({"title": title})
    request = urllib.request.Request(
        f"{CHEAPSHARK_DEALS_URL}?{query}", headers=CHEAPSHARK_HEADERS
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            deals = json.loads(response.read())
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
        return (title_score, savings_score)

    best_match = max(deals, key=match_key)

    try:
        price_original_usd = float(best_match["normalPrice"])
        price_discounted_usd = float(best_match["salePrice"])
        discount_percent = float(best_match["savings"])
    except (KeyError, TypeError, ValueError):
        return None

    rate = get_usd_to_idr_rate()

    return {
        "price_original": price_original_usd * rate,
        "price_discounted": price_discounted_usd * rate,
        "discount_percent": discount_percent,
    }


if __name__ == "__main__":
    # Contoh pemanggilan manual, buat ngetes modul ini sendirian
    # (jalankan: python api.py)
    test_title = "Red Dead Redemption 2"

    print(f"Testing get_estimated_hours('{test_title}')...")
    durations = get_estimated_hours(test_title)
    if durations is not None:
        for label, jam in durations.items():
            if jam is not None:
                print(f"  -> {label}: {jam:.0f} jam")
    else:
        print("  -> Gagal / tidak ketemu, pakai input manual.")

    print(f"\nTesting get_discount_info('{test_title}')...")
    discount = get_discount_info(test_title)
    if discount is not None:
        print(f"  -> Harga asli   : Rp {discount['price_original']:,.0f}")
        print(f"  -> Harga diskon : Rp {discount['price_discounted']:,.0f}")
        print(f"  -> Diskon       : {discount['discount_percent']:.0f}%")
    else:
        print("  -> Gagal / tidak ketemu, pakai input manual.")