"""
Modul: Validasi Input & Utility Bersama
Owner: Rafael (Dev 3)

"""

def get_float_input(prompt):
    """Minta input angka dari user, ulang terus sampai valid."""
    while True:
        raw = input(prompt)
        try:
            return float(raw)
        except ValueError:
            print("Input harus berupa angka, coba lagi.")