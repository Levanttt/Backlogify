"""
Modul: Decision Engine & Dashboard UI
Owner: Irfan (Lead) - Decision Engine, Menu 2 & Menu 4
        Nabil (Dev 4) - Tampilan Koleksi & Ringkasan, Menu 3
"""

import analytics
import api
import backlog
import data
from helpers import get_float_input, get_float_input_or_default

max_backlog_hours = 50.0
min_discount_percent = 50.0
max_unplayed_value = 1000000.0

def main():
    """Menjalankan navigasi menu utama."""
    global max_backlog_hours, min_discount_percent, max_unplayed_value

    name = input("Masukkan Nama Profile: ")
    data.login(name)
    print(f"\nSelamat datang, {name}! ({len(data.library)} game di backlog kamu)\n")

    # Jika profile yang baru di input tidak ada, maka tampilkan setup awal.
    if data.is_new_profile:
        setup_thresholds_first_time()
    else:
        # Profile lama, load threshold yang sudah pernah disimpan.
        max_unplayed_value = data.saved_thresholds["max_unplayed_value"]
        max_backlog_hours = data.saved_thresholds["max_backlog_hours"]
        min_discount_percent = data.saved_thresholds["min_discount_percent"]

    while True:
        print_header("BACKLOGIFY - GAMING PURCHASE DECISION PLATFORM")
        print("1. Registrasi Game Backlog Baru")
        print("2. Evaluasi Pembelian Game Baru")
        print("3. Lihat Koleksi & Summary Backlog")
        print("4. Atur Threshold Keputusan (Custom Limits)")
        print("5. Keluar")
        choice = input("Pilih Menu (1-5): ")

        if choice == "1":
            menu_add_game()
        elif choice == "2":
            menu_evaluate_purchase()
        elif choice == "3":
            menu_view_summary()
        elif choice == "4":
            menu_set_thresholds()
        elif choice == "5":
            print("\nTerima kasih telah menggunakan Backlogify!")
            break
        else:
            print("\nPilihan tidak valid, silakan coba lagi.")

def setup_thresholds_first_time():
    """Ditampilkan sekali waktu profile baru pertama kali login."""
    print_header("SETUP AWAL - THRESHOLD DECISION ENGINE")
    print("Threshold ini dipakai untuk mengevaluasi keputusan setiap kamu ingin beli game baru.")
    print("\nNilai Default:")
    print(f"  Batas Maksimal Uang Ngendap (Rp) : Rp {max_unplayed_value:,.0f}")
    print(f"  Batas Maksimal Sisa Jam Backlog  : {max_backlog_hours:.0f} Jam")
    print(f"  Batas Minimal Diskon Game (%)    : {min_discount_percent:.0f}%")
    print("-" * 65)
    print("1. Pakai Default")
    print("2. Atur Custom")
    choice = input("Pilih (1/2): ")

    # Custom pakai ulang menu_set_thresholds yang sudah ada.
    if choice == "2":
        menu_set_thresholds()

    data.save_thresholds({
        "max_backlog_hours": max_backlog_hours,
        "min_discount_percent": min_discount_percent,
        "max_unplayed_value": max_unplayed_value,
    })


def print_header(title):
    """Mencetak garis pemisah antarmuka menu."""
    print("\n" + "=" * 65)
    print(title)
    print("=" * 65)


def get_est_hours_with_fallback(title):
    """Coba ambil estimasi jam tamat otomatis dari HowLongToBeat, tampilkan
    gaya main yang datanya beneran ada (yang None dilewati), user tetap
    bisa input manual kalau mau."""
    hltb_data = api.get_estimated_hours(title)

    if hltb_data is None:
        print("\n(Sistem tidak menemukan data waktu tamat otomatis, silakan input manual)")
        return get_float_input("Masukkan Estimasi Jam Tamat : ")

    label_gaya_main = [
        ("Main Story", hltb_data["main_story"]),
        ("Main + Sides", hltb_data["main_extra"]),
        ("Completionist", hltb_data["completionist"]),
    ]
    pilihan = [(label, jam) for label, jam in label_gaya_main if jam is not None]

    if not pilihan:
        print("\n(HLTB tidak punya data durasi untuk game ini, silakan input manual)")
        return get_float_input("Masukkan Estimasi Jam Tamat : ")

    print(f"\n[Sistem menemukan estimasi waktu tamat untuk '{title}']")
    for i, (label, jam) in enumerate(pilihan, 1):
        print(f"{i}. {label:<13}: {jam:.0f} Jam")
    print(f"{len(pilihan) + 1}. Input Manual Angka Sendiri")

    pilih = input(f"Pilih target penyelesaian kamu (1-{len(pilihan) + 1}, Default 1): ").strip()

    if pilih.isdigit() and 1 <= int(pilih) <= len(pilihan):
        return pilihan[int(pilih) - 1][1]
    elif pilih == str(len(pilihan) + 1):
        return get_float_input("Masukkan Estimasi Jam Tamat : ")
    else:
        # Default ke opsi pertama (Main Story kalau ada) waktu Enter langsung ditekan.
        return pilihan[0][1]


def menu_add_game():
    """MENU 1: Menambahkan game baru ke dalam koleksi."""
    print_header("BACKLOGIFY - REGISTRASI GAME BACKLOG")
    title = input("Masukkan Judul Game       : ")
    
    print("\n(Catatan: Masukkan nominal harga final yang kamu bayar saat membeli game ini)")
    price = get_float_input("Masukkan Harga Beli (Rp)  : ")
    
    est_hours = get_est_hours_with_fallback(title)

    print("\nPilih Mode Lacak Playtime:")
    print("1. Direct Hours (Input angka jam langsung)")
    print("2. Progress Percentage (Input persentase %)")
    mode = input("Pilih Mode (1/2): ")

    if mode == "1":
        played_hours = get_float_input("Jam Main Saat Ini : ")
    else:
        progress_pct = get_float_input("Estimasi Progress (%) : ")
        played_hours = (progress_pct / 100) * est_hours

    game = data.add_game(title, price, est_hours, played_hours)

    total_spent = analytics.get_total_spent(data.library)
    total_unplayed = backlog.get_unplayed_value(data.library)
    total_backlog_hours = backlog.get_remaining_hours(data.library)

    print_header("GAME BERHASIL DITAMBAHKAN KE BACKLOG")
    print(f"Judul Game\t: {game['title']}")
    print(f"Harga Beli\t: Rp {game['price']:,.0f}")
    print(f"Playtime\t: {game['played_hours']:.1f} / {game['est_hours']:.0f} Jam")
    print(f"Status\t\t: {game['status']}")

    print("\n--- AKUMULASI TOTAL BACKLOG KAMU SAAT INI ---")
    print(f"Total Koleksi Game\t: {len(data.library)} Game")
    print(f"Total Nilai Koleksi\t: Rp {total_spent:,.0f}")
    print(f"Uang Ngendap\t: Rp {total_unplayed:,.0f} (Limit: Rp {max_unplayed_value:,.0f})")
    print(f"Total Sisa Jam Backlog\t: {total_backlog_hours:.1f} Jam (Limit: {max_backlog_hours:.0f} Jam)")


def menu_evaluate_purchase():
    """MENU 2: Multi-Factor Decision Engine (Fitur Utama)."""
    print_header("BACKLOGIFY - EVALUASI PEMBELIAN GAME BARU")
    new_title = input("Masukkan Judul Game Target : ")
    deal = api.get_discount_info(new_title)

    print("-" * 65)

    if deal is not None:
        print(f"[CheapShark: diskon {deal['discount_percent']:.0f}%, harga asli sekitar "
                f"Rp {deal['price_original']:,.0f} - referensi toko luar, harga lokal bisa beda]")
        new_price_original = get_float_input_or_default(
            f"Harga Asli Rp (Enter = Rp {deal['price_original']:,.0f}): ",
            deal["price_original"],
        )
        new_discount_percent = get_float_input_or_default(
            f"Diskon % (Enter = {deal['discount_percent']:.0f}%): ",
            deal["discount_percent"],
        )
    else:
        print("(Sistem tidak mendeteksi info diskon otomatis, silakan isi manual)")
        new_price_original = get_float_input("Masukkan Harga Asli (Rp)   : ")
        new_discount_percent = get_float_input("Masukkan Diskon (%)        : ")

    new_est_hours = get_est_hours_with_fallback(new_title)
    actual_new_price = new_price_original * (1 - (new_discount_percent / 100))
    potential_cph = analytics.calculate_cph(actual_new_price, new_est_hours)

    total_unplayed = backlog.get_unplayed_value(data.library)
    total_rem_hours = backlog.get_remaining_hours(data.library)
    closest_game = backlog.get_priority_game(data.library)

    if closest_game:
        rem_closest = closest_game["est_hours"] - closest_game["played_hours"]
        action_plan = f"Selesaikan '{closest_game['title']}' dulu (sisa {rem_closest:.0f} jam)."
    else:
        action_plan = "Backlog kamu aman, silakan beli game baru!"

    reasons = []
    if total_unplayed > max_unplayed_value:
        reasons.append(f"Uang ngendap (Rp {total_unplayed:,.0f}) melebihi limit Rp {max_unplayed_value:,.0f}")
    if total_rem_hours > max_backlog_hours:
        reasons.append(f"Sisa backlog ({total_rem_hours:.0f} jam) melebihi limit {max_backlog_hours:.0f} jam")
    if new_discount_percent < min_discount_percent:
        reasons.append(f"Diskon ({new_discount_percent:.0f}%) di bawah toleransi minimal {min_discount_percent:.0f}%")

    if reasons:
        decision = "WAIT"
        reason = " | ".join(reasons) 
    else:
        decision = "BUY"
        reason = f"Potensi CPH efisien (Rp {potential_cph:,.0f}/jam) & indikator backlog aman."
        action_plan = "Aman buat dibeli sekarang!"

    # Output Hasil
    print_header(f"HASIL EVALUASI: {new_title.upper()}")
    print("\n--- DETAIL GAME TARGET ---")
    print(f"Harga Asli\t: Rp {new_price_original:,.0f}")
    print(f"Diskon\t\t: {new_discount_percent:.0f}% (Harga Bayar: Rp {actual_new_price:,.0f})")
    print(f"Estimasi Tamat\t: {new_est_hours:.0f} Jam")
    print(f"Potensi CPH\t: Rp {potential_cph:,.0f} / Jam")

    print("\n--- KONDISI BACKLOG VS THRESHOLD ---")
    print(f"Total Uang Ngendap\t: Rp {total_unplayed:,.0f} (Limit: Rp {max_unplayed_value:,.0f})")
    print(f"Total Sisa Jam\t: {total_rem_hours:.0f} Jam Main (Limit: {max_backlog_hours:.0f} Jam)")
    print(f"Diskon Game\t: {new_discount_percent:.0f}% (Min Toleransi: {min_discount_percent:.0f}%)")

    print(f"\nDECISION RECOMMENDATION : [{decision}]")
    print(f"Reason : {reason}")
    print(f"Action : {action_plan}")


def menu_view_summary():
    """MENU 3: Menampilkan tabel koleksi dan ringkasan status."""
    total_backlog_hours = backlog.get_remaining_hours(data.library)
    total_unplayed_value = backlog.get_unplayed_value(data.library)
    total_spent = analytics.get_total_spent(data.library)

    if total_unplayed_value > max_unplayed_value:
        status_financial = "[MELEBIHI LIMIT!]"
    else:
        status_financial = "[AMAN]"

    print_header("KOLEKSI BACKLOG & RINGKASAN STATUS")
    print(f"{'No':<3} | {'Judul Game':<18} | {'Harga':<10} | {'Playtime':<10} | {'Status':<12}")
    print("-" * 65)
    # Melakukan pengecekan daftar game yang dimiliki berdasarkan nomor urut.
    for idx, g in enumerate(data.library, 1):
        print(f"{idx:<3} | {g['title']:<18} | Rp {g['price']:<7,.0f} | {g['played_hours']:.0f}/{g['est_hours']:.0f} Jam | {g['status']:<12}")
    print("-" * 65)
    print(f"Total Koleksi\t\t: {len(data.library)} Game")
    print(f"Total Nilai Koleksi\t: Rp {total_spent:,.0f}")
    print(f"Total Uang Ngendap\t: Rp {total_unplayed_value:,.0f} / Limit Kamu Rp {max_unplayed_value:,.0f} {status_financial}")
    print(f"Total Sisa Jam Backlog\t: {total_backlog_hours:.1f} Jam / Limit Kamu {max_backlog_hours:.0f} Jam")


def menu_set_thresholds():
    """MENU 4: Mengatur ulang batas keputusan (Custom Limits)."""
    global max_unplayed_value, max_backlog_hours, min_discount_percent

    print_header("PENGATURAN THRESHOLD DECISION ENGINE")
    print(f"Batas Maksimal Uang Ngendap (Rp)   : Rp {max_unplayed_value:,.0f}")
    print(f"Batas Maksimal Sisa Jam Backlog    : {max_backlog_hours:.0f} Jam")
    print(f"Batas Minimal Diskon Game (%)      : {min_discount_percent:.0f}%")
    print("-" * 65)

    new_val = input("Batas Maksimal Uang (Rp) Ngendap Kamu yang Baru?       (Enter untuk batal): ")
    if new_val.strip():
        max_unplayed_value = float(new_val)

    new_hours = input("Batas Maksimal Sisa Jam Backlog Kamu yang Baru?      (Enter untuk batal): ")
    if new_hours.strip():
        max_backlog_hours = float(new_hours)

    new_disc = input("Batas Minimal Diskon Game (%) Kamu yang Baru?     (Enter untuk batal): ")
    if new_disc.strip():
        min_discount_percent = float(new_disc)

    data.save_thresholds({
        "max_backlog_hours": max_backlog_hours,
        "min_discount_percent": min_discount_percent,
        "max_unplayed_value": max_unplayed_value,
    })

    print("\nTHRESHOLD BERHASIL DIPERBARUI DAN DISIMPAN!")

if __name__ == "__main__":
    main()