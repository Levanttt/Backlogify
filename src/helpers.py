"""
Modul: Validasi Input & Utility Bersama
Owner: Rafael (Dev 3)

"""
import os
import json
import os
import urllib.request

def get_float_input(prompt):
    """Minta input angka dari user, ulang terus sampai valid."""
    # Perulangan tanpa batas, hanya berhenti (lewat return) kalau input berhasil diubah jadi angka.
    while True:
        raw = input(prompt)
        try:
            return float(raw)
        except ValueError:
            print("Input harus berupa angka, coba lagi.")

def get_usd_to_idr_rate():
    """Mengambil kurs USD ke IDR terbaru. Jika gagal, return kurs fallback 16000."""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={"User-Agent": "Backlogify/1.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read())
            return float(data["rates"]["IDR"])
    except Exception:
        return 16000.0  # Fallback nilai konstan jika offline / API down

def clear_screen():
    """Membersihkan layar terminal agar UX lebih rapi."""
    os.system('cls' if os.name == 'nt' else 'clear')
