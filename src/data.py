"""
Modul: Library Management & User Profile
Owner: Billy (Dev 1)

Backend: Supabase (Postgres). Semua baca/tulis library & profile
langsung ke Supabase, tidak ada penyimpanan lokal.

Catatan desain:
- Variabel global (current_profile, library, dst) dipakai sebagai cache
  in-memory per-session, supaya app_web.py bisa tetap akses
  `data.library` seperti biasa. Sumber kebenarannya ada di Supabase.
- Tiap dict game di `library` juga punya key "id" (uuid dari Supabase),
  dipakai internal buat update/delete row yang tepat.
"""

import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

current_profile = None
current_profile_id = None
library = []
saved_thresholds = None
is_new_profile = False


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


def login(name):
    global current_profile, current_profile_id, library, saved_thresholds, is_new_profile

    res = (
        supabase.table("profiles")
        .select("*")
        .ilike("name", name)
        .execute()
    )

    if res.data:
        profile = res.data[0]
        current_profile = profile["name"]
        current_profile_id = profile["id"]
        saved_thresholds = {
            "max_unplayed_value": profile["max_unplayed_value"],
            "max_backlog_hours": profile["max_backlog_hours"],
            "min_discount_percent": profile["min_discount_percent"],
        }
        library = _fetch_games(current_profile_id)
        is_new_profile = False
    else:
        insert_res = (
            supabase.table("profiles")
            .insert({"name": name})
            .execute()
        )
        profile = insert_res.data[0]
        current_profile = profile["name"]
        current_profile_id = profile["id"]
        saved_thresholds = None
        library = []
        is_new_profile = True

    return library


def save_thresholds(thresholds):
    global saved_thresholds
    saved_thresholds = thresholds
    supabase.table("profiles").update({
        "max_unplayed_value": thresholds["max_unplayed_value"],
        "max_backlog_hours": thresholds["max_backlog_hours"],
        "min_discount_percent": thresholds["min_discount_percent"],
    }).eq("id", current_profile_id).execute()


def add_game(title, price, est_hours, played_hours):
    game = {
        "profile_id": current_profile_id,
        "title": title,
        "price": price,
        "played_hours": played_hours,
        "est_hours": est_hours,
        "status": determine_status(played_hours, est_hours),
    }
    res = supabase.table("games").insert(game).execute()
    saved_game = res.data[0]
    library.append(saved_game)
    return saved_game


def update_played_hours(index, played_hours):
    game = library[index]
    new_status = determine_status(played_hours, game["est_hours"])

    supabase.table("games").update({
        "played_hours": played_hours,
        "status": new_status,
    }).eq("id", game["id"]).execute()

    game["played_hours"] = played_hours
    game["status"] = new_status
    return game


def update_est_hours(index, est_hours):
    game = library[index]
    new_status = determine_status(game["played_hours"], est_hours)

    supabase.table("games").update({
        "est_hours": est_hours,
        "status": new_status,
    }).eq("id", game["id"]).execute()

    game["est_hours"] = est_hours
    game["status"] = new_status
    return game


def delete_game(index):
    game = library[index]
    supabase.table("games").delete().eq("id", game["id"]).execute()
    removed = library.pop(index)
    return removed