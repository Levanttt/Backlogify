"""
Modul: Validasi Input & Utility Bersama
Owner: Rafael (Dev 3)

"""


def aggregate(items, filter_fn, value_fn):
    """Filter items, lalu jumlahkan value_fn dari yang lolos filter."""
    # 1. for item in items   : Berfungsi untuk memeriksa setiap data di dalam list satu per satu
    # 2. if filter_fn(item)  : Berfungsi untuk menyaring data yang memenuhi syarat (bernilai True)
    # 3. value_fn(item)      : Mengambil nilai angka dari data yang lolos filter
    # 4. sum(...)            : Menjumlahkan seluruh hasil angka tersebut
    return sum(value_fn(item) for item in items if filter_fn(item))


def get_float_input(prompt):
    """Minta input angka dari user, ulang terus sampai valid."""
    while True:
        raw = input(prompt)
        try:
            return float(raw)
        except ValueError:
            print("Input harus berupa angka, coba lagi.")