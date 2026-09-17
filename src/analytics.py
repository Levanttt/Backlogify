"""
Modul: Cost & Spending Analytics
Owner: Irfan (Lead)
"""


def calculate_cph(price, hours):
    """Menghitung biaya per jam (Cost-per-Hour)."""
    # Hanya akan dibagi kalau jam main > 0, supaya tidak error ketika dibagi nol.
    if hours > 0:
        return price / hours
    return price


def get_total_spent(library):
    """Menghitung total pengeluaran seluruh game dengan perulangan biasa."""
    total = 0
    # Menjumlahkan harga setiap game yang ada didalam library satu per satu.
    for game in library:
        total += game["price"]
    return total