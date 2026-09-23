"""
Modul: Validasi Input & Utility Bersama
Owner: Rafael (Dev 3)

"""
import os

def get_float_input(prompt):
    """Minta input angka dari user, ulang terus sampai valid."""
    while True:
        raw = input(prompt)
        try:
            return float(raw)
        except ValueError:
            print("Input harus berupa angka, coba lagi.")

def clear_screen():
    """Membersihkan layar terminal agar UX lebih rapi."""
    os.system('cls' if os.name == 'nt' else 'clear')