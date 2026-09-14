"""
Modul: Cost & Spending Analytics
Owner: Irfan (Lead)
"""


def calculate_cph(price, hours):
    """Menghitung biaya per jam (Cost-per-Hour)."""
    if hours > 0:
        return price / hours
    return price


def get_total_spent(library):
    """Menghitung total pengeluaran seluruh game dengan perulangan biasa."""
    total = 0
    for game in library:
        total += game["price"]
    return total