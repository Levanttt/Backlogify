"""
Modul: Library Management & User Profile
Owner: Billy (Dev 1)

Backend: Supabase (Postgres + Auth). Semua baca/tulis library & profile
langsung ke Supabase, tidak ada penyimpanan lokal.

Catatan desain:
- State per-user (current_profile, library, dst) disimpan di st.session_state
  dengan prefix "data_", bukan variabel global modul. Modul Python di-import
  sekali per proses server, jadi variabel global akan dipakai bersama oleh
  semua sesi browser dan data antar user bisa tercampur.
- Client Supabase juga dibuat per sesi (_sb), karena setelah login client
  menyimpan token milik user tersebut. Satu client bersama berarti token
  satu user dipakai untuk request user lain.
- __getattr__ di bawah membuat `data.library` dkk tetap bisa dibaca dari
  app_web.py seperti biasa, tapi isinya milik sesi yang sedang aktif.
- Tiap dict game di `library` juga punya key "id" (uuid dari Supabase),
  dipakai internal buat update/delete row yang tepat.
"""

import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

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


def _sb():
    if "data_sb" not in st.session_state:
        st.session_state.data_sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state.data_sb


def determine_status(played_hours, est_hours):
    if played_hours == 0:
        return "Unplayed"
    elif played_hours >= est_hours:
        return "Completed"
    else:
        return "In-Progress"


def _fetch_games(profile_id):
    res = (
        _sb().table("games")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at")
        .execute()
    )
    return res.data


def _load_profile(user):
    res = _sb().table("profiles").select("*").eq("user_id", user.id).execute()

    if res.data:
        profile = res.data[0]
        # Profil yang dibuat tapi belum sempat setup threshold masih berisi None.
        # Anggap belum selesai setup supaya app_web.py menampilkan form setup lagi.
        is_new = profile["max_unplayed_value"] is None
        thresholds = None if is_new else {
            "max_unplayed_value": profile["max_unplayed_value"],
            "max_backlog_hours": profile["max_backlog_hours"],
            "min_discount_percent": profile["min_discount_percent"],
        }
        games = _fetch_games(profile["id"])
    else:
        # Nama tampilan diambil dari bagian depan email, supaya tidak perlu field tambahan.
        profile = _sb().table("profiles").insert({
            "name": user.email.split("@")[0],
            "user_id": user.id,
        }).execute().data[0]
        thresholds, games, is_new = None, [], True

    _set(
        current_profile=profile["name"],
        current_profile_id=profile["id"],
        library=games,
        saved_thresholds=thresholds,
        is_new_profile=is_new,
    )
    return games


def login(email, password):
    # Password salah / email tidak terdaftar akan raise error dari Supabase Auth.
    res = _sb().auth.sign_in_with_password({"email": email, "password": password})
    return _load_profile(res.user)


def register(email, password):
    # Email yang sudah terdaftar ditolak otomatis oleh Supabase Auth.
    res = _sb().auth.sign_up({"email": email, "password": password})
    if res.session is None:
        # Terjadi kalau "Confirm email" aktif di dashboard Supabase.
        raise Exception("Pendaftaran berhasil. Cek email untuk konfirmasi, lalu login.")
    return _load_profile(res.user)


def save_thresholds(thresholds):
    _set(saved_thresholds=thresholds)
    _sb().table("profiles").update({
        "max_unplayed_value": thresholds["max_unplayed_value"],
        "max_backlog_hours": thresholds["max_backlog_hours"],
        "min_discount_percent": thresholds["min_discount_percent"],
    }).eq("id", st.session_state.data_current_profile_id).execute()


def add_game(title, price, est_hours, played_hours):
    game = {
        "profile_id": st.session_state.data_current_profile_id,
        "title": title,
        "price": price,
        "played_hours": played_hours,
        "est_hours": est_hours,
        "status": determine_status(played_hours, est_hours),
    }
    res = _sb().table("games").insert(game).execute()
    saved_game = res.data[0]
    st.session_state.data_library.append(saved_game)
    return saved_game


def update_played_hours(index, played_hours):
    game = st.session_state.data_library[index]
    new_status = determine_status(played_hours, game["est_hours"])

    _sb().table("games").update({
        "played_hours": played_hours,
        "status": new_status,
    }).eq("id", game["id"]).execute()

    game["played_hours"] = played_hours
    game["status"] = new_status
    return game


def update_est_hours(index, est_hours):
    game = st.session_state.data_library[index]
    new_status = determine_status(game["played_hours"], est_hours)

    _sb().table("games").update({
        "est_hours": est_hours,
        "status": new_status,
    }).eq("id", game["id"]).execute()

    game["est_hours"] = est_hours
    game["status"] = new_status
    return game


def delete_game(index):
    game = st.session_state.data_library[index]
    _sb().table("games").delete().eq("id", game["id"]).execute()
    return st.session_state.data_library.pop(index)