"""
Modul: Backlog Intelligence
Owner: Billy (Dev 1)

"""

def get_unplayed_value(library):
    """Hitung total harga game yang 0 jam main."""
    total = 0
    for game in library:
        if game["played_hours"] == 0:
            total += game["price"]
    return total


def get_remaining_hours(library):
    """Hitung total sisa jam main game yang belum tamat."""
    total = 0
    for game in library:
        if game["status"] != "Completed":
            sisa_jam = game["est_hours"] - game["played_hours"]
            if sisa_jam > 0:
                total += sisa_jam
    return total


def get_priority_game(library):
    """Cari 1 game aktif yang paling sedikit sisa jamnya (paling dekat tamat)."""
    # Mengumpulkan game yang belum tamat
    active_games = []
    for game in library:
        if game["status"] != "Completed":
            active_games.append(game)

    if not active_games:
        return None

    # Mencari game yang sisa jamnya paling kecil
    priority_game = active_games[0]
    for game in active_games:
        sisa_game_ini = game["est_hours"] - game["played_hours"]
        sisa_priority = priority_game["est_hours"] - priority_game["played_hours"]

        if sisa_game_ini < sisa_priority:
            priority_game = game

    return priority_game