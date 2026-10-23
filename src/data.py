import hashlib
import hmac
import re
import time
import bcrypt
import httpx
import streamlit as st
from postgrest.exceptions import APIError
from supabase import create_client, Client
from backlog import linear_search

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

_STATE = (
    "current_profile",
    "current_profile_id",
    "library",
    "saved_thresholds",
    "is_new_profile",
)


def __getattr__(name):
    # Hanya dipanggil kalau atribut tidak ada di modul, jadi data.library
    # otomatis membaca dari session_state milik sesi yang sedang berjalan.
    if name in _STATE:
        return st.session_state.get("data_" + name)
    raise AttributeError(name)


def _set(**kw):
    for k, v in kw.items():
        st.session_state["data_" + k] = v


def determine_status(played_hours, est_hours):
    if played_hours == 0:
        return "Unplayed"
    elif played_hours >= est_hours:
        return "Completed"
    else:
        return "In-Progress"


def _fetch_games(profile_id):
    res = (
        supabase.table("games")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at")
        .execute()
    )
    return res.data


NAMA_VALID = re.compile(r"^[A-Za-z0-9 .\-]{3,30}$")


def _cari_profile(name):
    # % dan _ di-escape supaya input user tidak dianggap wildcard oleh ilike.
    pola = name.strip().replace("%", r"\%").replace("_", r"\_")
    res = supabase.table("profiles").select("*").ilike("name", pola).execute()
    return res.data[0] if res.data else None


def register(name, password):
    """Return (True, "") kalau berhasil, atau (False, pesan_error)."""
    name = name.strip()

    if not NAMA_VALID.match(name):
        return False, "Nama 3-30 karakter, hanya huruf, angka, spasi, titik, atau strip."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if len(password.encode()) > 72:
        return False, "Password terlalu panjang (maksimal 72 karakter)."
    if _cari_profile(name):
        return False, "Nama profile sudah dipakai."

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        supabase.table("profiles").insert({
            "name": name,
            "password_hash": hashed,
        }).execute()
    except (APIError, httpx.HTTPError) as e:
        print(f"[REGISTER ERROR] {e}")
        return False, "Gagal mendaftar, coba lagi."
    else:
        return True, ""


def login(name, password):
    """Return library kalau berhasil, None kalau nama/password salah."""
    profile = _cari_profile(name)
    if not profile or not profile.get("password_hash"):
        return None
    if not bcrypt.checkpw(password.encode(), profile["password_hash"].encode()):
        return None
    return _muat_profile(profile)


def _muat_profile(profile):
    # Threshold masih None berarti profil belum selesai setup awal.
    if profile["max_unplayed_value"] is None:
        thresholds, is_new = None, True
    else:
        thresholds, is_new = {
            "max_unplayed_value": profile["max_unplayed_value"],
            "max_backlog_hours": profile["max_backlog_hours"],
            "min_discount_percent": profile["min_discount_percent"],
        }, False

    games = _fetch_games(profile["id"])
    _set(
        current_profile=profile["name"],
        current_profile_id=profile["id"],
        library=games,
        saved_thresholds=thresholds,
        is_new_profile=is_new,
    )
    return games


TOKEN_TTL_DETIK = 7 * 86400


def _sign(payload):
    secret = st.secrets["AUTH_SECRET"].encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def make_token(profile_id):
    """Token bertanda tangan 'id.kadaluarsa.signature' untuk bertahan saat refresh."""
    payload = f"{profile_id}.{int(time.time()) + TOKEN_TTL_DETIK}"
    return f"{payload}.{_sign(payload)}"


def restore(token):
    """Return True kalau token valid dan sesi berhasil dipulihkan."""
    try:
        payload, sig = token.rsplit(".", 1)
        pid, exp = payload.rsplit(".", 1)
    except ValueError:
        return False
    # int(exp) aman karena baru dijalankan setelah signature cocok.
    if not hmac.compare_digest(sig, _sign(payload)) or int(exp) < time.time():
        return False
    res = supabase.table("profiles").select("*").eq("id", pid).execute()
    if not res.data:
        return False
    _muat_profile(res.data[0])
    return True


def save_thresholds(thresholds):
    _set(saved_thresholds=thresholds)
    supabase.table("profiles").update({
        "max_unplayed_value": thresholds["max_unplayed_value"],
        "max_backlog_hours": thresholds["max_backlog_hours"],
        "min_discount_percent": thresholds["min_discount_percent"],
    }).eq("id", st.session_state.data_current_profile_id).execute()


class DataError(Exception):
    """Error validasi data; pesannya aman ditampilkan ke user."""


def add_game(title, price, est_hours, played_hours):
    title = title.strip()
    if not title:
        raise DataError("Judul game tidak boleh kosong.")
    if est_hours <= 0:
        raise DataError("Estimasi jam tamat harus lebih dari 0.")
    if price < 0 or played_hours < 0:
        raise DataError("Harga dan jam main tidak boleh negatif.")
    if is_duplicate_title(title):
        raise DataError(f"'{title}' sudah ada di library kamu.")

    game = {
        "profile_id": st.session_state.data_current_profile_id,
        "title": title,
        "price": price,
        "played_hours": played_hours,
        "est_hours": est_hours,
        "status": determine_status(played_hours, est_hours),
    }
    res = supabase.table("games").insert(game).execute()
    saved_game = res.data[0]
    st.session_state.data_library.append(saved_game)
    return saved_game

def is_duplicate_title(title):
    """Mengecek apakah judul sudah ada di library (tidak peduli huruf besar/kecil)."""
    titles = [game["title"].strip().lower() for game in st.session_state.data_library]
    index, _ = linear_search(titles, title.strip().lower())
    return index != -1

def update_played_hours(index, played_hours):
    game = st.session_state.data_library[index]
    new_status = determine_status(played_hours, game["est_hours"])

    supabase.table("games").update({
        "played_hours": played_hours,
        "status": new_status,
    }).eq("id", game["id"]).execute()

    game["played_hours"] = played_hours
    game["status"] = new_status
    return game


def update_est_hours(index, est_hours):
    game = st.session_state.data_library[index]
    new_status = determine_status(game["played_hours"], est_hours)

    supabase.table("games").update({
        "est_hours": est_hours,
        "status": new_status,
    }).eq("id", game["id"]).execute()

    game["est_hours"] = est_hours
    game["status"] = new_status
    return game


def delete_game(index):
    game = st.session_state.data_library[index]
    supabase.table("games").delete().eq("id", game["id"]).execute()
    return st.session_state.data_library.pop(index)

def export_csv(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("judul,harga,estimasi_jam,jam_main\n")
        for g in st.session_state.data_library:
            f.write(f"{g['title']},{g['price']},{g['est_hours']},{g['played_hours']}\n")


def import_csv(teks):
    """Return (jumlah_berhasil, daftar_pesan_gagal). Baris pertama dianggap header."""
    berhasil, gagal = 0, []
    for no, baris in enumerate(teks.splitlines()[1:], start=2):
        if not baris.strip():
            continue
        try:
            judul, harga, est, main = baris.rsplit(",", 3)
            add_game(judul, float(harga), float(est), float(main))
        except ValueError:
            gagal.append(f"Baris {no}: format salah")
        except DataError as e:
            gagal.append(f"Baris {no}: {e}")
        else:
            berhasil += 1
    return berhasil, gagal