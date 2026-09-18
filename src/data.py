"""
Modul: Library Management & User Profile
Owner: Billy (Dev 1)
"""

import json
import os

# Menentukan lokasi penyimpanan dan folder data/ 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "backlog.json")

os.makedirs(DATA_DIR, exist_ok=True)

current_profile = None
library = []
saved_thresholds = None
is_new_profile = False


def load_all_profiles():
    """Membaca seluruh data profile dari backlog.json. Mengembalikan dict kosong jika file belum ada."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_all_profiles(profiles):
    """Menyimpan seluruh data profile ke file backlog.json di dalam folder data/."""
    with open(DATA_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def find_profile_name(profiles, name):
    """Mencari nama profile yang cocok tanpa memedulikan huruf besar/kecil (case-insensitive)."""
    matched = None
    for existing_name in profiles:
        if existing_name.lower() == name.lower():
            matched = existing_name
            break  # Berhenti begitu profile yang cocok ditemukan
    return matched


def login(name):
    """Melakukan proses login berdasarkan nama profile dan memuat datanya."""
    global current_profile, library, saved_thresholds, is_new_profile
    profiles = load_all_profiles()
    matched = find_profile_name(profiles, name)

    # Jika profil ditemukan, maka muat data library dan threshold yang telah tersimpan
    if matched:
        current_profile = matched 
        library = profiles[matched]["library"]  
        saved_thresholds = profiles[matched]["thresholds"]  
        is_new_profile = False  

    # Jika profil tidak ditemukan / Profil baru
    else:
        current_profile = name  
        library = []  
        saved_thresholds = None  
        is_new_profile = True

    return library


def save_current_profile():
    """Menyimpan data library dan threshold milik profile yang sedang aktif."""
    profiles = load_all_profiles()
    profiles[current_profile] = {
        "library": library,
        "thresholds": saved_thresholds,
    }
    save_all_profiles(profiles)


def save_thresholds(thresholds):
    """Menyimpan pengaturan threshold milik profile yang sedang aktif."""
    global saved_thresholds
    saved_thresholds = thresholds
    save_current_profile()


def determine_status(played_hours, est_hours):
    """Menentukan status game berdasarkan jumlah jam main dan estimasi waktu tamat."""
    if played_hours == 0:
        return "Unplayed"
    elif played_hours >= est_hours:
        return "Completed"
    else:
        return "In-Progress"


def add_game(title, price, est_hours, played_hours):
    """Menambahkan data game baru ke dalam library dan menyimpannya ke file JSON."""
    game = {
        "title": title,
        "price": price,
        "est_hours": est_hours,
        "played_hours": played_hours,
        "status": determine_status(played_hours, est_hours),
    }
    library.append(game)
    save_current_profile()
    return game