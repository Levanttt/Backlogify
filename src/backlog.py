class Game:
    """Satu game di backlog: data jadi atribut, hitungan turunannya jadi method."""

    def __init__(self, title, price, est_hours, played_hours):
        self.title = title
        self.price = price
        self.est_hours = est_hours
        self.played_hours = played_hours

    @classmethod
    def from_row(cls, row):
        return cls(row["title"], row["price"], row["est_hours"], row["played_hours"])

    def remaining_hours(self):
        """Menghitung sisa jam bermain"""
        return max(0, self.est_hours - self.played_hours)

    def unplayed_value(self):
        """
        Menghitung total nilai (Rp) yang belum "kepakai", proporsional
        terhadap sisa jam yang belum dimainkan dari tiap game.
        """
        if self.est_hours <= 0:
            return 0
        return self.price * self.remaining_hours() / self.est_hours


def get_unplayed_value(library):
    """Menghitung total nilai yang belum dimainkan dari seluruh game."""
    return sum(Game.from_row(row).unplayed_value() for row in library)


def get_remaining_hours(library):
    """Menghitung total sisa jam bermain dari game yang belum tamat."""
    return sum(
        Game.from_row(row).remaining_hours()
        for row in library
        if row["status"] != "Completed"
    )


def get_priority_game(library):
    """Mencari game aktif yang sisa jam bermainnya paling sedikit."""
    active_games = [row for row in library if row["status"] != "Completed"]
    if not active_games:
        return None
    return min(active_games, key=lambda row: Game.from_row(row).remaining_hours())
