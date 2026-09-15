"""
Modul: Backlog Intelligence
Owner: Billy (Dev 1)

"""

from helpers import aggregate


def get_unplayed_value(library):
    """Menghitung total harga game yang belum pernah dimainkan."""
    # Menggunakan aggregate untuk menghitung total harga game.
    # Lambda pertama memilih game yang jam mainnya masih 0 (played_hours == 0).
    # Lambda kedua mengambil nilai harga (price) untuk dijumlahkan.
    return aggregate(library, lambda g: g["played_hours"] == 0, lambda g: g["price"])


def get_remaining_hours(library):
    """Menghitung total sisa jam bermain dari game yang belum tamat."""
    return aggregate( # Menggunakan aggregate untuk mengumpulkan akumulasi sisa jam main.
        library,
        lambda g: g["status"] != "Completed", # Lambda disini berfungsi untuk menyaring game yang statusnya belum selesai (bukan Completed).
        lambda g: max(0, g["est_hours"] - g["played_hours"]), # Lambda disini berfungsi untuk menghitung selisih estimasi jam tamat dikurangi jam main saat ini.
    )


def get_priority_game(library):
    """Mencari game aktif yang sisa jam bermainnya paling sedikit."""
    # Menyaring seluruh game yang belum tamat ke dalam daftar active_games.
    active_games = [g for g in library if g["status"] != "Completed"]
    if not active_games:
        return None

    # Menggunakan fungsi min dengan parameter key lambda untuk memilih game dengan sisa jam terkecil.
    return min(active_games, key=lambda g: g["est_hours"] - g["played_hours"])