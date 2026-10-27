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


SORT_KEYS = {
    "Default": None,
    "Sisa jam terkecil": lambda row: Game.from_row(row).remaining_hours(),
    "Harga tertinggi": lambda row: -row["price"],
}


def linear_search(items, target):
    """Cari target dari awal. Return (indeks, jumlah pengecekan), indeks -1 kalau tidak ada."""
    checks = 0
    for i, item in enumerate(items):
        checks += 1
        if item == target:
            return i, checks
    return -1, checks


def insertion_sort(items, key=lambda x: x):
    """Urutkan salinan items. Return (hasil, jumlah perbandingan, jumlah geseran)."""
    result = items.copy()  
    comparisons = shifts = 0
    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if key(result[j]) > key(current):
                result[j + 1] = result[j]
                shifts += 1
                j -= 1
            else:
                break
        result[j + 1] = current
    return result, comparisons, shifts


def sort_library(library, mode):
    """Urutkan library sesuai mode di SORT_KEYS tanpa mengubah library asli."""
    key = SORT_KEYS[mode]
    if key is None:
        return library
    return insertion_sort(library, key=key)[0]

