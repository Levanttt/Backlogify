"""
Modul: Backlog Intelligence
Owner: Billy (Dev 1)

"""

def get_unplayed_value(library):
    """Menghitung total harga game yang belum pernah dimainkan."""
    total = 0
    # Memeriksa setiap game satu per satu, menjumlahkan harga yang jam mainnya masih 0.
    for game in library:
        if game["played_hours"] == 0:
            total += game["price"]
    return total


def get_remaining_hours(library):
    """Menghitung total sisa jam bermain dari game yang belum tamat."""
    total = 0
    # Memeriksa setiap game, hanya menjumlahkan sisa jam dari yang statusnya belum Completed.
    for game in library:
        if game["status"] != "Completed":
            # Menggunakan max(0, ...) supaya sisa jam tidak menjadi minus kalau jam main melebihi estimasi.
            total += max(0, game["est_hours"] - game["played_hours"])
    return total


def get_priority_game(library):
    """Mencari game aktif yang sisa jam bermainnya paling sedikit."""
    priority_game = None
    smallest_remaining = None

    # Menelusuri seluruh game untuk mencari kandidat dengan sisa jam bermain paling kecil.
    for game in library:
        if game["status"] != "Completed":
            remaining = game["est_hours"] - game["played_hours"]
            # Menyimpan game ini sebagai kandidat terbaik kalau belum ada kandidat, atau sisa jamnya lebih kecil dari kandidat sebelumnya.
            if priority_game is None or remaining < smallest_remaining:
                priority_game = game
                smallest_remaining = remaining

    return priority_game