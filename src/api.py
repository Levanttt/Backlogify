"""
Modul: Game Info & API Integrator
Owner: Alwi (Dev 2)

Integrasi:
- howlongtobeatpy  -> estimasi durasi tamat (main_story, main_extra, completionist)

Fungsi publik return None kalau gagal (bukan raise), supaya app.py gampang
cek: `if hasil is None: minta input manual`.
"""

import concurrent.futures

from howlongtobeatpy import HowLongToBeat

# howlongtobeatpy sendiri pakai timeout 60 detik PER request internal, dan satu
# search() bisa berupa beberapa request berantai. Kalau tidak dibatasi dari sini,
# koneksi yang lambat/diblokir bisa bikin app kelihatan hang bermenit-menit.
HLTB_TIMEOUT_SECONDS = 15


def get_estimated_hours(title):
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
    except Exception as e:
        print(f"[HLTB ERROR] {type(e).__name__}: {e}")
        return None


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