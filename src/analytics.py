"""
Modul: Cost & Spending Analytics
Owner: Irfan (Lead)

"""

from helpers import aggregate


def calculate_cph(price, hours):
    """Hitung biaya per jam. Kalau jam masih 0, CPH dianggap sama dengan harga penuh."""
    if hours > 0:
        return price / hours
    return price


def get_total_spent(library):
    """Total uang yang sudah dikeluarkan untuk seluruh koleksi."""
    return aggregate(library, lambda g: True, lambda g: g["price"])