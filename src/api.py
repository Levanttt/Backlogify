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

# Pembatasan penarikan data 
HLTB_TIMEOUT_SECONDS = 15


def get_estimated_hours(title):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(HowLongToBeat().search, title)
        results = future.result(timeout=HLTB_TIMEOUT_SECONDS)

        if not results:
            return None

        # judul dari user gaperlu exact match tiap katanya dengan database HLTB, jadi ambil hasil yang paling mirip aja
        best_match = max(results, key=lambda r: r.similarity)
        return {
            "main_story": float(best_match.main_story) if best_match.main_story else None,
            "main_extra": float(best_match.main_extra) if best_match.main_extra else None,
            "completionist": float(best_match.completionist) if best_match.completionist else None,
        }
    except concurrent.futures.TimeoutError:
        print(f"[HLTB ERROR] Timeout setelah {HLTB_TIMEOUT_SECONDS} detik")
        return None
    except Exception as e:
        print(f"[HLTB ERROR] {type(e).__name__}: {e}")
        return None
    finally:
        # wait=False: jangan nunggu request yang nyangkut di background selesai,
        executor.shutdown(wait=False)


if __name__ == "__main__":
    # Contoh pemanggilan manual, buat ngetes modul ini
    test_title = "Red Dead Redemption 2"

    print(f"Testing get_estimated_hours('{test_title}')...")
    durations = get_estimated_hours(test_title)
    if durations is not None:
        for label, jam in durations.items():
            if jam is not None:
                print(f"  -> {label}: {jam:.0f} jam")
    else:
        print("  -> Gagal / tidak ketemu, pakai input manual.")