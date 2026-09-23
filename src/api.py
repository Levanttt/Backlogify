"""
Modul: Game Info & API Integrator
Owner: Alwi (Dev 2)

Integrasi:
- howlongtobeatpy  -> estimasi durasi tamat (main_story, main_extra, completionist)

Fungsi publik return None kalau gagal (bukan raise), supaya app.py gampang
cek: `if hasil is None: minta input manual`.
"""

from howlongtobeatpy import HowLongToBeat


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


if __name__ == "__main__":
    test_title = "Red Dead Redemption 2"

    print(f"Testing get_estimated_hours('{test_title}')...")
    durations = get_estimated_hours(test_title)
    if durations is not None:
        for label, jam in durations.items():
            if jam is not None:
                print(f"  -> {label}: {jam:.0f} jam")
    else:
        print("  -> Gagal / tidak ketemu, pakai input manual.")