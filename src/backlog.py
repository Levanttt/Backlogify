"""
Modul: Backlog Intelligence
Owner: Billy (Dev 1)

"""

def get_unplayed_value(library):
    """
    Menghitung total nilai (Rp) yang belum "kepakai", proporsional
    terhadap sisa jam yang belum dimainkan dari tiap game.
    """
    total = 0
    for game in library:
        if game["est_hours"] > 0:
            sisa_jam = max(0, game["est_hours"] - game["played_hours"])
            rasio_sisa = sisa_jam / game["est_hours"]
            total += game["price"] * rasio_sisa
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

    # Mencari seluruh game untuk mencari kandidat dengan sisa jam bermain paling kecil.
    for game in library:
        if game["status"] != "Completed":
            # Menghitung sisa jam bermain dari game tersebut.
            remaining = game["est_hours"] - game["played_hours"]
            # Simpan game ini kalau belum ada patokan ATAU sisa jamnya lebih singkat dari game sebelumnya.
            if priority_game is None or remaining < smallest_remaining:
                priority_game = game
                smallest_remaining = remaining

    return priority_game