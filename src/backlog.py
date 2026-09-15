"""
Modul: Backlog Intelligence
Owner: Billy (Dev 1)

"""

from helpers import aggregate


def get_unplayed_value(library):
    """Total harga game yang belum pernah dimainkan (played_hours == 0)."""
    return aggregate(library, lambda g: g["played_hours"] == 0, lambda g: g["price"])


def get_remaining_hours(library):
    """Total sisa jam main dari game yang belum selesai."""
    return aggregate(
        library,
        lambda g: g["status"] != "Completed",
        lambda g: max(0, g["est_hours"] - g["played_hours"]),
    )


def get_priority_game(library):
    """Cari game aktif dengan sisa jam paling sedikit (paling dekat tamat)."""
    active_games = [g for g in library if g["status"] != "Completed"]
    if not active_games:
        return None
    return min(active_games, key=lambda g: g["est_hours"] - g["played_hours"])