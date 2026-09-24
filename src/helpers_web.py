"""
Modul: Helper Input Streamlit
Owner: Rafael (Dev 3)

Kumpulan wrapper untuk widget input Streamlit, biar format & behavior-nya
seragam di semua halaman. Kalau mau ubah step / format / validasi, cukup
ubah di sini, gak perlu kejar-kejar tiap number_input di app_web.py.
"""

import streamlit as st


def input_rupiah(label, key=None, default=0, step=5000):
    """
    Input angka Rupiah. Dipaksa bulat (tanpa desimal) lewat format="%d",
    supaya kursor gak nyangkut di belakang koma pas field diklik.
    """
    return st.number_input(
        label,
        min_value=0,
        step=step,
        value=default,
        format="%d",
        key=key,
    )


def input_persen(label, key=None, default=0, step=1):
    """Input persentase 0-100, dibatasi biar gak bisa lebih/kurang dari itu."""
    return st.number_input(
        label,
        min_value=0,
        max_value=100,
        step=step,
        value=default,
        format="%d",
        key=key,
    )


def input_jam(label, key=None, default=0, step=1):
    """Input durasi dalam jam. Bulat, karena estimasi jam tamat jarang butuh desimal."""
    return st.number_input(
        label,
        min_value=0,
        step=step,
        value=default,
        format="%d",
        key=key,
    )


def flash_success(message):
    """Tampilkan notifikasi sukses (toast kanan atas, auto-hilang)."""
    st.toast(message, icon="✅")


def flash_error(message):
    """Tampilkan notifikasi gagal (toast kanan atas, auto-hilang)."""
    st.toast(message, icon="⚠️")


def flash_info(message):
    """Tampilkan notifikasi info (toast kanan atas, auto-hilang)."""
    st.toast(message, icon="ℹ️")


def render_flash():
    """Placeholder — sudah tidak dipakai. Dibiarkan biar app_web.py
    yang lama tetap jalan tanpa error. Aman untuk dihapus nanti."""
    pass