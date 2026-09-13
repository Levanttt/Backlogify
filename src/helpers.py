"""
Modul: Validasi Input & Utility Bersama
Owner: Rafael (Dev 3)

"""


def aggregate(items, filter_fn, value_fn):
    """Filter items, lalu jumlahkan value_fn dari yang lolos filter."""
    return sum(value_fn(item) for item in items if filter_fn(item))


def get_float_input(prompt):
    """Minta input angka dari user, ulang terus sampai valid."""
    while True:
        raw = input(prompt)
        try:
            return float(raw)
        except ValueError:
            print("Input harus berupa angka, coba lagi.")