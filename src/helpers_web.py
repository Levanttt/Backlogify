"""
Modul: Helper Input Streamlit
Owner: Rafael (Dev 3)

Kumpulan wrapper untuk widget input Streamlit, biar format & behavior-nya
seragam di semua halaman. Kalau mau ubah step / format / validasi, cukup
ubah di sini, gak perlu kejar-kejar tiap number_input di app_web.py.
"""

import streamlit as st

import api


def _num_input(label, key=None, default=0, step=1, max_value=None):
    return st.number_input(
        label,
        min_value=0,
        max_value=max_value,
        step=step,
        value=default,
        format="%d",  # memaksakan input gak ada koma
        key=key,
    )


def input_rupiah(label, key=None, default=0, step=5000):
    """Input angka Rupiah."""
    return _num_input(label, key, default, step)


def input_persen(label, key=None, default=0, step=1):
    """Input persentase, dibatasi 0-100."""
    return _num_input(label, key, default, step, max_value=100)


def input_jam(label, key=None, default=0, step=1):
    """Input durasi dalam jam."""
    return _num_input(label, key, default, step)


def flash_success(message):
    """Tampilkan notifikasi sukses (toast kanan atas, auto-hilang)."""
    st.toast(message, icon="✅")


def flash_error(message):
    """Tampilkan notifikasi gagal (toast kanan atas, auto-hilang)."""
    st.toast(message, icon="⚠️")


def flash_info(message):
    """Tampilkan notifikasi info (toast kanan atas, auto-hilang)."""
    st.toast(message, icon="ℹ️")


def pilih_estimasi_jam(title, key_prefix, default_manual=None, label_manual=None):
    """Minta user pilih estimasi jam main game, pakai HLTB atau input manual."""
    label_manual = label_manual or "Masukkan Target Estimasi Kamu Bermain Game Ini"
    k_hasil = f"{key_prefix}_hltb"
    k_judul = f"{key_prefix}_hltb_title"
    k_dicari = f"{key_prefix}_hltb_searched"

    # Buang sesi lama kalau judulnya berubah, biar gak salah pakai hasil HLTB dari game sebelumnya
    if st.session_state.get(k_judul) != title:
        st.session_state[k_hasil] = None
        st.session_state[k_dicari] = False

    if st.button("Berikan Opsi Gaya Main Otomatis", key=f"{key_prefix}_btn_hltb"):
        if not title.strip():
            st.error("Isi judul game dulu sebelum minta opsi gaya main!")
        else:
            with st.spinner("Mengambil data estimasi..."):
                st.session_state[k_hasil] = api.get_estimated_hours(title.strip())
                st.session_state[k_judul] = title.strip()
                st.session_state[k_dicari] = True

    hasil = st.session_state.get(k_hasil)
    if st.session_state.get(k_dicari) and st.session_state.get(k_judul) == title and hasil is None:
        st.warning(
            "Gagal ambil data estimasi otomatis. Kemungkinan judul tidak ada di "
            "database, koneksi lambat, atau situsnya diblokir jaringan kamu. "
            "Silakan input manual di bawah."
        )

    if hasil:
        # Buat dict opsi: label (Main Story / Main + Sides / Completionist) -> jam
        opsi = {
            f"{label} - {jam:.0f} jam": jam
            for label, jam in [
                ("Main Story", hasil["main_story"]),
                ("Main + Sides", hasil["main_extra"]),
                ("Completionist", hasil["completionist"]),
            ]
            if jam is not None  # HLTB kadang cuma punya sebagian data
        }
        if opsi:
            pilihan = st.selectbox(
                "Pilih Gaya Main",
                list(opsi) + ["Input Manual"],
                key=f"{key_prefix}_select_gaya_main",
            )
            if pilihan != "Input Manual":
                return opsi[pilihan], False
            st.caption("Atau")

    est_hours = input_jam(
        label_manual,
        key=f"{key_prefix}_manual_hours",
        default=int(default_manual) if default_manual else 0,
    )
    return est_hours, True


def reset_pilihan_estimasi(key_prefix):
    """Buang cache hasil pilih_estimasi_jam untuk key_prefix tertentu.
    Panggil ini abis datanya sukses disimpan, biar form berikutnya mulai bersih."""
    for suffix in ["_hltb", "_hltb_title", "_hltb_searched"]:
        k = f"{key_prefix}{suffix}"
        if k in st.session_state:
            del st.session_state[k]