import streamlit as st
import data
import backlog
import analytics
import api
import helpers_web as hw

st.set_page_config(page_title="Backlogify", page_icon="🎮", layout="wide")

# --- SISTEM LOGIN SEDERHANA ---
if "logged_in" not in st.session_state:
    st.title("Selamat Datang di Backlogify")
    st.write("Silakan login untuk mengakses data backlog kamu.")

    username = st.text_input("Masukkan Nama Profile:")
    if st.button("Masuk"):
        if username.strip():
            data.login(username)
            st.session_state.logged_in = True
            st.session_state.username = username

            if getattr(data, 'is_new_profile', False):
                st.session_state.needs_setup = True

            st.rerun()
    st.stop()

# --- SETUP AWAL UNTUK PROFIL BARU ---
if st.session_state.get("needs_setup", False):
    st.header("Setup Awal Threshold")
    st.warning(f"Halo {st.session_state.username}! Karena ini profil baru, silakan tentukan batas toleransi backlog kamu sebelum masuk ke dashboard.")

    with st.form("setup_form_awal"):
        new_unplayed = hw.input_rupiah(
            "Batas Maksimal Uang Ngendap (Rp)",
            default=1000000,
        )
        new_hours = hw.input_jam(
            "Batas Maksimal Sisa Jam Backlog",
            default=50,
        )
        new_disc = hw.input_persen(
            "Batas Minimal Diskon Game (%)",
            default=50,
        )

        if st.form_submit_button("Simpan & Lanjut ke Dashboard"):
            threshold_data = {
                "max_unplayed_value": new_unplayed,
                "max_backlog_hours": new_hours,
                "min_discount_percent": new_disc,
            }
            data.save_thresholds(threshold_data)
            data.saved_thresholds = threshold_data
            st.session_state.needs_setup = False
            st.rerun()

    st.stop()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title(f"Halo, {st.session_state.username}!")
menu = st.sidebar.radio("Navigasi Menu", [
    "Koleksi & Summary",
    "Registrasi Game Baru",
    "Evaluasi Pembelian",
    "Pengaturan Threshold"
])

st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# Tampilkan flash message dari aksi sebelumnya (harus di luar blok Logout)
hw.render_flash()

# --- KONTEN MENU ---

if menu == "Koleksi & Summary":
    st.header("Koleksi Backlog & Ringkasan Status")

    total_spent = analytics.get_total_spent(data.library)
    total_unplayed = backlog.get_unplayed_value(data.library)
    total_hours = backlog.get_remaining_hours(data.library)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Game", f"{len(data.library)}")
    col2.metric("Total Nilai Koleksi", f"Rp {total_spent:,.0f}")
    col3.metric("Uang Ngendap", f"Rp {total_unplayed:,.0f}")
    col4.metric("Sisa Jam Backlog", f"{total_hours:.0f} Jam")

    st.markdown("---")
    st.subheader("Detail Pustaka Game")

    if not data.library:
        st.info("Koleksi backlog kamu masih kosong.")
    else:
        tampilan = [
            {
                "Judul": g["title"],
                "Harga": f"Rp {g['price']:,.0f}",
                "Playtime": f"{g['played_hours']:.0f} Jam",
                "Estimasi": f"{g['est_hours']:.0f} Jam",
                "Status": g["status"],
            }
            for g in data.library
        ]
        st.dataframe(tampilan, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Kelola Game")

        daftar_judul = [g["title"] for g in data.library]
        pilihan = st.selectbox("Pilih Game", daftar_judul)
        index = daftar_judul.index(pilihan)
        game = data.library[index]

        tab_update, tab_target, tab_hapus = st.tabs([
            "Update Progress",
            "Update Target",
            "Hapus Game",
        ])

        # ---------- Tab 1: Update Progress ----------
        with tab_update:
            st.caption(
                f"Saat ini: {game['played_hours']:.0f}/{game['est_hours']:.0f} Jam "
                f"({game['status']})"
            )

            mode_update = st.radio(
                "Metode input:",
                ["Jam langsung", "Persentase progress"],
                horizontal=True,
                key="mode_update",
                label_visibility="collapsed",
            )

            if mode_update == "Jam langsung":
                new_played = hw.input_jam(
                    "Jam Main Sekarang",
                    key=f"new_played_{index}",          
                    default=int(game["played_hours"]),
                )
            else:
                progress_awal = int(
                    min(game["played_hours"] / game["est_hours"] * 100, 100)
                ) if game["est_hours"] else 0
                pct_update = st.slider(
                    "Perkiraan Progress (%)", 0, 100, progress_awal, key="pct_update"
                )
                new_played = (pct_update / 100) * game["est_hours"]
                st.caption(f"Setara dengan: **{new_played:.1f} Jam**")

            if st.button("Simpan Update Progress", type="primary", key="btn_update"):
                updated = data.update_played_hours(index, new_played)
                hw.flash_success(f"Progress '{updated['title']}' berhasil diupdate.")
                st.rerun()

        # ---------- Tab 2: Update Target ----------
        with tab_target:
            st.caption(
                f"Target saat ini: {game['est_hours']:.0f} Jam "
                f"({game['played_hours']:.0f} Jam sudah dimainkan)"
            )

            st.caption(
                "Belum tahu target yang pas? Kamu bisa ambil opsi gaya main "
                "otomatis, atau cek durasi full walkthrough di YouTube."
            )

            target_key = f"target_hltb_{index}"
            searched_key = f"target_searched_{index}"
            title_key = f"target_title_{index}"

            if st.session_state.get(title_key) != game["title"]:
                st.session_state[target_key] = None
                st.session_state[searched_key] = False

            if st.button("Berikan Opsi Gaya Main Otomatis", key=f"btn_hltb_target_{index}"):
                with st.spinner("Mengambil data estimasi..."):
                    st.session_state[target_key] = api.get_estimated_hours(game["title"])
                    st.session_state[title_key] = game["title"]
                    st.session_state[searched_key] = True

            if (st.session_state.get(searched_key)
                    and st.session_state.get(title_key) == game["title"]
                    and st.session_state.get(target_key) is None):
                st.warning(
                    "Gagal ambil data estimasi otomatis. Kemungkinan: judul "
                    "tidak ada di database, koneksi lambat, atau situsnya "
                    "diblokir jaringan kamu. Silakan input manual di bawah."
                )

            new_target = None
            is_manual_target = True

            if st.session_state.get(target_key):
                opts_target = st.session_state[target_key]
                label_opsi_target = [
                    ("Main Story", opts_target["main_story"]),
                    ("Main + Sides", opts_target["main_extra"]),
                    ("Completionist", opts_target["completionist"]),
                ]
                opsi_tersedia_target = [
                    f"{label} - {jam:.0f} jam"
                    for label, jam in label_opsi_target
                    if jam is not None
                ]

                if opsi_tersedia_target:
                    is_manual_target = False
                    pilihan_target = st.selectbox(
                        "Pilih Gaya Main",
                        opsi_tersedia_target + ["Input Manual"],
                        key=f"select_target_{index}",
                    )
                    if pilihan_target == "Input Manual":
                        is_manual_target = True
                    else:
                        label_terpilih_target = pilihan_target.rsplit(" - ", 1)[0]
                        new_target = dict(label_opsi_target)[label_terpilih_target]

            if is_manual_target:
                st.caption("Atau")
                new_target = hw.input_jam(
                    "Target Estimasi Jam Tamat yang Baru",
                    key=f"manual_target_{index}",
                    default=int(game["est_hours"]),
                )

            st.info(
                "Kalau target baru lebih kecil dari playtime saat ini, "
                "status game otomatis jadi Completed."
            )

            if st.button("Simpan Target Baru", type="primary", key=f"btn_target_{index}"):
                if new_target is None or new_target <= 0:
                    hw.flash_error("Target harus lebih dari 0 jam.")
                    st.rerun()
                else:
                    updated = data.update_est_hours(index, new_target)
                    hw.flash_success(f"Target '{updated['title']}' berhasil diupdate.")
                    for k in [target_key, searched_key, title_key]:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.rerun()

        # ---------- Tab 3: Hapus Game ----------
        with tab_hapus:
            st.warning(
                f"Hapus '{game['title']}' dari library? "
                f"Aksi ini tidak bisa dibatalkan."
            )
            if st.button("Ya, Hapus Game Ini", type="primary", key="btn_hapus"):
                judul_dihapus = game["title"]
                data.delete_game(index)
                hw.flash_success(f"'{judul_dihapus}' berhasil dihapus dari library.")
                st.rerun()

elif menu == "Registrasi Game Baru":
    st.header("Registrasi Game Backlog")

    # Counter versi: naikin tiap kali form berhasil disubmit, biar semua
    # widget di bawahnya ke-reset (karena key-nya berubah).
    if "menu1_version" not in st.session_state:
        st.session_state.menu1_version = 0
    v = st.session_state.menu1_version

    title = st.text_input("Judul Game", key=f"menu1_title_input_{v}")
    price = hw.input_rupiah(
        "Masukkan Harga Game ini saat kamu membelinya (Rp)",
        key=f"menu1_price_{v}",
    )

    st.markdown("---")
    st.markdown("### Masukkan Estimasi Jam Tamat")
    st.caption(
        "Belum tahu berapa lama game ini bisa tamat? Kamu bisa cek estimasi "
        "durasi lewat video full walkthrough di YouTube, biasanya durasinya "
        "mendekati waktu tamat game tersebut."
    )

    if st.session_state.get("menu1_title") != title:
        st.session_state.hltb_menu1 = None
        st.session_state.hltb_menu1_searched = False

    if st.button("Berikan Opsi Gaya Main Otomatis"):
        if not title.strip():
            st.error("Isi judul game dulu sebelum minta opsi gaya main!")
        else:
            with st.spinner("Sedang mengambil data estimasi..."):
                st.session_state.hltb_menu1 = api.get_estimated_hours(title.strip())
                st.session_state.menu1_title = title.strip()
                st.session_state.hltb_menu1_searched = True

    if (st.session_state.get("hltb_menu1_searched")
            and st.session_state.get("menu1_title") == title
            and st.session_state.get("hltb_menu1") is None):
        st.warning(
            "Gagal ambil data estimasi otomatis. Kemungkinan: judul yang kamu cari tidak ada "
            "di database, koneksi lambat, atau situsnya diblokir oleh jaringan kamu. "
            "Silakan input manual di bawah."
        )

    est_hours = 0.0
    is_manual = True

    if st.session_state.get("hltb_menu1"):
        opts = st.session_state.hltb_menu1
        label_opsi = [
            ("Main Story", opts["main_story"]),
            ("Main + Sides", opts["main_extra"]),
            ("Completionist", opts["completionist"]),
        ]
        opsi_tersedia = [
            f"{label} - {jam:.0f} jam"
            for label, jam in label_opsi
            if jam is not None
        ]

        if opsi_tersedia:
            is_manual = False
            playstyle = st.selectbox(
                "Pilih Gaya Main",
                opsi_tersedia + ["Input Manual"],
                key=f"menu1_playstyle_{v}",
            )
            if playstyle == "Input Manual":
                is_manual = True
            else:
                label_terpilih = playstyle.rsplit(" - ", 1)[0]
                est_hours = dict(label_opsi)[label_terpilih]

    if is_manual:
        st.caption("Atau")
        est_hours = hw.input_jam(
            "Masukkan Target Estimasi Kamu Bermain Game Ini",
            key=f"menu1_manual_hours_{v}",
        )

    st.markdown("---")
    st.markdown("**Lacak Playtime Saat Ini**")
    mode = st.radio(
        "Sudah main berapa lama?",
        [
            "Saya ingat berapa jam saya sudah main",
            "Saya tidak ingat, pakai perkiraan persentase saja",
        ],
        key=f"menu1_mode_{v}",
    )

    if mode == "Saya ingat berapa jam saya sudah main":
        played_hours = hw.input_jam("Jam Main Saat Ini", key=f"menu1_played_{v}")
    else:
        progress_pct = st.slider(
            "Perkiraan Progress (%)", 0, 100, 0, key=f"menu1_pct_{v}"
        )
        played_hours = (progress_pct / 100) * est_hours
        st.caption(f"Setara dengan: **{played_hours:.1f} Jam**")

    if st.button("Tambahkan ke Library", type="primary"):
        if title.strip() == "":
            hw.flash_error("Judul game tidak boleh kosong.")
            st.rerun()
        elif est_hours <= 0:
            hw.flash_error("Estimasi jam tamat harus lebih dari 0.")
            st.rerun()
        else:
            data.add_game(title, price, est_hours, played_hours)
            hw.flash_success(f"'{title}' berhasil ditambahkan ke backlog kamu.")

            for k in ["hltb_menu1", "menu1_title", "hltb_menu1_searched"]:
                if k in st.session_state:
                    del st.session_state[k]

            # Naikin versi -> semua widget Menu 1 bakal ke-reset
            st.session_state.menu1_version += 1

            st.rerun()

elif menu == "Evaluasi Pembelian":
    st.header("Evaluasi Pembelian Game Baru")
    new_title = st.text_input("Masukkan Judul Game Target Kamu")

    col1, col2 = st.columns(2)
    with col1:
        input_price = hw.input_rupiah("Masukkan Harga Asli Saat Ini (Rp)")
    with col2:
        input_disc = hw.input_persen("Masukkan Harga Diskon Saat Ini (%)")

    st.markdown("---")
    st.markdown("### Masukkan Rencana Main / Estimasi Jam Tamat")
    st.caption(
        "Belum tahu berapa lama game ini bisa tamat? Kamu bisa cek estimasi "
        "durasi lewat video full walkthrough di YouTube, biasanya durasinya "
        "mendekati waktu tamat game tersebut."
    )

    if st.session_state.get("eval_title") != new_title:
        st.session_state.eval_hltb = None
        st.session_state.eval_hltb_searched = False

    if st.button("Berikan Opsi Gaya Main Otomatis"):
        if not new_title.strip():
            st.error("Isi judul game dulu sebelum minta opsi gaya main!")
        else:
            with st.spinner("Mengambil data estimasi..."):
                st.session_state.eval_hltb = api.get_estimated_hours(new_title.strip())
                st.session_state.eval_title = new_title.strip()
                st.session_state.eval_hltb_searched = True

    if (st.session_state.get("eval_hltb_searched")
            and st.session_state.get("eval_title") == new_title
            and st.session_state.get("eval_hltb") is None):
        st.warning(
            "Gagal ambil data estimasi otomatis. Kemungkinan: judul tidak ada "
            "di database, koneksi lambat, atau situsnya diblokir jaringan kamu. "
            "Silakan input manual di bawah."
        )

    eval_est_hours = 0.0
    is_manual_eval = True

    if st.session_state.get("eval_hltb"):
        opts_eval = st.session_state.eval_hltb
        label_opsi_eval = [
            ("Main Story", opts_eval["main_story"]),
            ("Main + Sides", opts_eval["main_extra"]),
            ("Completionist", opts_eval["completionist"]),
        ]
        opsi_tersedia_eval = [
            f"{label} - {jam:.0f} jam"
            for label, jam in label_opsi_eval
            if jam is not None
        ]

        if opsi_tersedia_eval:
            is_manual_eval = False
            pilihan = st.selectbox(
                "Pilih Gaya Main",
                opsi_tersedia_eval + ["Input Manual"],
            )

            if pilihan == "Input Manual":
                is_manual_eval = True
            else:
                label_terpilih = pilihan.rsplit(" - ", 1)[0]
                eval_est_hours = dict(label_opsi_eval)[label_terpilih]

    if is_manual_eval:
        st.caption("Atau")
        eval_est_hours = hw.input_jam(
            "Masukkan Target Estimasi Kamu Bermain Game Ini"
        )

    st.markdown("---")
    if st.button("Jalankan Evaluasi Decision Engine", type="primary"):
        if input_price <= 0 or eval_est_hours <= 0:
            st.error("Harga dan Estimasi Jam tidak boleh 0!")
        else:
            actual_price = input_price * (1 - (input_disc / 100))
            pot_cph = analytics.calculate_cph(actual_price, eval_est_hours)

            tot_unplayed = backlog.get_unplayed_value(data.library)
            tot_rem_hours = backlog.get_remaining_hours(data.library)

            max_unplay = data.saved_thresholds.get("max_unplayed_value", 1000000.0)
            max_hrs = data.saved_thresholds.get("max_backlog_hours", 50.0)
            min_disc = data.saved_thresholds.get("min_discount_percent", 50.0)

            reasons = []
            if tot_unplayed > max_unplay:
                reasons.append(f"Uang ngendap kamu (Rp {tot_unplayed:,.0f}) sudah melampaui batas yang ditetapkan.")
            if tot_rem_hours > max_hrs:
                reasons.append(f"Sisa waktu backlog kamu ({tot_rem_hours:.0f} Jam) sudah melampaui batas yang ditetapkan.")
            if input_disc < min_disc:
                reasons.append(f"Diskon game ini masih belum mencapai batas minimal yang kamu tetapkan ({min_disc:.0f}%).")

            st.markdown("### Hasil Keputusan")

            if reasons:
                st.error("WAIT (TUNDA PEMBELIAN)")
                st.write("**Alasannya:**")
                for r in reasons:
                    st.warning(r)
            else:
                st.success("BUY (AMAN DIBELI SEKARANG)")
                st.write("**Alasannya:**")
                st.info("Kondisi backlog kamu aman dan indikator diskon memenuhi standar yang ditetapkan.")

            st.write(
                f"**Kamu akan Membayar Harga Game ini dengan Total:** Rp {actual_price:,.0f} "
                f"Setelah Diskon &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"**Dengan Cost per Hour:** Rp {pot_cph:,.0f} / Jam"
            )

elif menu == "Pengaturan Threshold":
    st.header("Pengaturan Threshold & Limit")
    st.write("Sesuaikan toleransi Backlogify dalam memberikan rekomendasi keputusan pembelian game kamu.")

    current_unplayed = data.saved_thresholds.get("max_unplayed_value", 1000000.0)
    current_hours = data.saved_thresholds.get("max_backlog_hours", 50.0)
    current_disc = data.saved_thresholds.get("min_discount_percent", 50.0)

    with st.form("threshold_form"):
        new_unplayed = hw.input_rupiah(
            "Batas Maksimal Uang Ngendap (Rp)",
            default=int(current_unplayed),
        )
        new_hours = hw.input_jam(
            "Batas Maksimal Sisa Jam Backlog",
            default=int(current_hours),
        )
        new_disc = hw.input_persen(
            "Batas Minimal Diskon Game (%)",
            default=int(current_disc),
        )

        submitted = st.form_submit_button("Simpan Pengaturan")
        if submitted:
            data.save_thresholds({
                "max_unplayed_value": new_unplayed,
                "max_backlog_hours": new_hours,
                "min_discount_percent": new_disc,
            })
            hw.flash_success("Batas threshold berhasil diperbarui dan disimpan.")
            st.rerun()