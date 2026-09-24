import streamlit as st
import data
import backlog
import analytics
import helpers_web as hw

st.set_page_config(page_title="Backlogify", page_icon="🎮", layout="wide")

# --- SISTEM LOGIN ---
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

# --- KONTEN MENU LIBRARY ---
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
                # dibatasi max 100 & dijaga kalau est_hours 0, biar slider-nya
                # gak crash atau nampilin progress yang ngaco
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

            new_target, _ = hw.pilih_estimasi_jam(
                game["title"],
                key_prefix=f"target_{index}",
                default_manual=game["est_hours"],
                label_manual="Target Estimasi Jam Tamat yang Baru",
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
                    hw.reset_pilihan_estimasi(f"target_{index}")
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

    est_hours, _ = hw.pilih_estimasi_jam(title, key_prefix="menu1")

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

            hw.reset_pilihan_estimasi("menu1")

            # semua widget Menu 1 bakal ke-reset setelah submit
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
 
    eval_est_hours, _ = hw.pilih_estimasi_jam(new_title, key_prefix="eval")
 
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
 
            # Game yang paling deket kelar di backlog kamu, buat saran
            closest_game = backlog.get_priority_game(data.library)
            if closest_game:
                rem_closest = closest_game["est_hours"] - closest_game["played_hours"]
                action_plan = f"Selesaikan '{closest_game['title']}' dulu (sisa {rem_closest:.0f} jam)."
            else:
                action_plan = "Backlog kamu aman, silakan beli game baru!"
 
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
                action_plan = "Aman buat dibeli sekarang!"
 
            st.write(f"**Rekomendasi Aksi:** {action_plan}")
 
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