"""
Modul: Library Management & User Profile
Owner: Billy (Dev 1)

"""

# Data awal (sample), representasi koleksi game user
library = [
    {"title": "Cyberpunk 2077", "price": 350000, "played_hours": 10, "est_hours": 50, "status": "In-Progress"},
    {"title": "The Witcher 3", "price": 90000, "played_hours": 40, "est_hours": 50, "status": "In-Progress"},
    {"title": "Hollow Knight", "price": 60000, "played_hours": 0, "est_hours": 25, "status": "Unplayed"},
]


def determine_status(played_hours, est_hours):
    """Tentukan status game berdasarkan jam main vs estimasi durasi tamat."""
    if played_hours == 0:
        return "Unplayed"
    elif played_hours >= est_hours:
        return "Completed"
    else:
        return "In-Progress"


def add_game(title, price, est_hours, played_hours):
    """Tambahkan game baru ke library dan kembalikan entry-nya."""
    game = {
        "title": title,
        "price": price,
        "est_hours": est_hours,
        "played_hours": played_hours,
        "status": determine_status(played_hours, est_hours),
    }
    library.append(game)
    return game