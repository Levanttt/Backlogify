import altair as alt
import streamlit as st
import data
import backlog
import analytics
import helpers_web as hw

st.set_page_config(page_title="Backlogify", page_icon="🎮", layout="wide")

WARNA_STATUS = {"Unplayed": "#ff4b4b", "In-Progress": "#faca2b", "Completed": "#21c354"}
WARNA_BAGIAN = {"Ngendap": "#ff4b4b", "Terpakai": "#21c354"}

def _mulai_sesi():
    st.session_state.logged_in = True
    st.session_state.username = data.current_profile
    st.session_state.profile_id = data.current_profile_id
    if data.is_new_profile:
        st.session_state.needs_setup = True
    # Token di URL bikin login bertahan saat halaman di-refresh.
    st.query_params["t"] = data.make_token(data.current_profile_id)


# --- SISTEM LOGIN ---
if "logged_in" not in st.session_state and "t" in st.query_params:
    if data.restore(st.query_params["t"]):
        _mulai_sesi()
    else:
        st.query_params.clear()

if "logged_in" not in st.session_state:
    st.title("Selamat Datang di Backlogify")
    st.write("Silakan login atau daftar untuk mengakses data backlog kamu.")

    tab_masuk, tab_daftar = st.tabs(["Masuk", "Daftar"])

    with tab_masuk:
        with st.form("form_login"):
            username = st.text_input("Nama Profile")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk")

        if submit_login:
            if data.login(username, password) is None:
                st.error("Nama atau password salah.")
            else:
                _mulai_sesi()
                st.rerun()

    with tab_daftar:
        with st.form("form_daftar"):
            new_name = st.text_input("Nama Profile Baru")
            new_pass = st.text_input("Password", type="password")
            new_pass2 = st.text_input("Ulangi Password", type="password")
            submit_daftar = st.form_submit_button("Daftar")

        if submit_daftar:
            if new_pass != new_pass2:
                st.error("Password dan ulangi password tidak sama.")
            else:
                ok, pesan = data.register(new_name, new_pass)
                if not ok:
                    st.error(pesan)
                elif data.login(new_name, new_pass) is None:
                    st.error("Pendaftaran berhasil, tapi gagal masuk. Coba login manual.")
                else:
                    _mulai_sesi()
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
            st.session_state.needs_setup = False
            st.rerun()

    st.stop()

# --- SIDEBAR NAVIGASI ---
st.sidebar.title(f"Halo, {st.session_state.username}!")
MENU = [
    "Koleksi & Summary",
    "Registrasi Game Baru",
    "Evaluasi Pembelian",
    "Pengaturan Threshold",
]
if "menu" not in st.session_state:
    # Setelah refresh, buka lagi menu terakhir dari URL (default ke menu pertama).
    m = st.query_params.get("menu")
    st.session_state.menu = m if m in MENU else MENU[0]
menu = st.sidebar.radio("Navigasi Menu", MENU, key="menu")
st.query_params["menu"] = menu

st.sidebar.markdown("---")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()

# --- KONTEN MENU LIBRARY ---
if menu == "Koleksi & Summary":
    st.header("Koleksi Backlog & Ringkasan Status")

    total_spent = analytics.get_total_spent(data.library)
    total_unplayed = backlog.get_unplayed_value(data.library)
    total_hours = backlog.get_remaining_hours(data.library)

    if data.library:
        max_unplay = data.saved_thresholds.get("max_unplayed_value", 1000000.0)
        max_hrs = data.saved_thresholds.get("max_backlog_hours", 50.0)
        kol_donut, kol_bar, kol_batas = st.columns([0.7, 1.5, 1.2])

        # Donut chart
        with kol_donut:
            st.caption("Status Game di Library")
            judul_per_status = {}
            for g in data.library:
                judul_per_status.setdefault(g["status"], []).append(g["title"])
            rows_donut = [
                {
                    "Status": s,
                    "Jumlah": len(judul),
                    # Satu field per judul (maksimal 5), kosong kalau game-nya tidak ada.
                    **{f"G{i + 1}": judul[i] if i < len(judul) else "" for i in range(5)},
                    "Lain": f"+{len(judul) - 5} lainnya" if len(judul) > 5 else "",
                }
                for s, judul in judul_per_status.items()
            ]
            donut = alt.Chart(alt.Data(values=rows_donut)).mark_arc(innerRadius=50).encode(
                theta="Jumlah:Q",
                color=alt.Color(
                    "Status:N",
                    scale=alt.Scale(domain=list(WARNA_STATUS), range=list(WARNA_STATUS.values())),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                tooltip=[
                    alt.Tooltip("Status:N"),
                    alt.Tooltip("Jumlah:Q"),
                    *[
                        alt.Tooltip(f"G{i}:N", title="Game" if i == 1 else " " * (i - 1))
                        for i in range(1, 6)
                    ],
                    alt.Tooltip("Lain:N", title=" " * 5),
                ],
            ).properties(height=250)
            st.altair_chart(donut, use_container_width=True, key=f"donut_{hash(str(rows_donut))}")

        # Bar chart
        with kol_bar:
            kap, leg = st.columns([3, 2])
            kap.caption("Uang yang mengendap / game (Rp)")
            leg.markdown(
                "<div style='text-align:right;font-size:0.875rem;opacity:0.6'>"
                + " &nbsp; ".join(
                    f"<span style='color:{w}'>■</span> {b}" for b, w in WARNA_BAGIAN.items()
                )
                + "</div>",
                unsafe_allow_html=True,
            )
            ngendap = {g["title"]: backlog.Game.from_row(g).unplayed_value() for g in data.library}
            urutan = sorted(ngendap, key=ngendap.get, reverse=True)  # ngendap terbesar di atas
            rows_bar = [
                {"Game": g["title"], "Bagian": bagian, "Rupiah": nilai}
                for g in data.library
                for bagian, nilai in (
                    ("Ngendap", ngendap[g["title"]]),
                    ("Terpakai", g["price"] - ngendap[g["title"]]),
                )
            ]
            bar = alt.Chart(alt.Data(values=rows_bar)).mark_bar().encode(
                y=alt.Y("Game:N", sort=urutan, title=None),
                x=alt.X("Rupiah:Q", title=None),
                color=alt.Color(
                    "Bagian:N",
                    scale=alt.Scale(domain=list(WARNA_BAGIAN), range=list(WARNA_BAGIAN.values())),
                    legend=None,
                ),
                tooltip=["Game:N", "Bagian:N", alt.Tooltip("Rupiah:Q", format=",.0f")],
            ).properties(height=max(250, 30 * len(urutan)))
            st.altair_chart(bar, use_container_width=True, key=f"bar_{hash(str(rows_bar))}")

        # Progress chart
        with kol_batas:
            st.caption("Status Threshold Backlog")
            for label, nilai, batas in [
                ("Uang yang mengendap", total_unplayed, max_unplay),
                ("Sisa jam backlog", total_hours, max_hrs),
            ]:
                persen = nilai / batas * 100 if batas else 0
                st.progress(min(persen / 100, 1.0), text=f"{label}: {persen:.0f}% dari batas yang ditetapkan")
                if nilai > batas:
                    st.error("Melewati batas.")
    

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Game", f"{len(data.library)}")
    col2.metric("Total Nilai Koleksi", f"Rp {total_spent:,.0f}")
    col3.metric("Uang Ngendap", f"Rp {total_unplayed:,.0f}")
    col4.metric("Sisa Jam Backlog", f"{total_hours:.0f} Jam")

    st.markdown("---")
    kolom_judul, kolom_urut = st.columns([20, 1], vertical_alignment="center")
    kolom_judul.subheader("Detail Library Game")
    with kolom_urut.popover(
        "", icon=":material/filter_list:", help="Urutkan tabel", use_container_width=True):
        mode_urut = st.radio(
            "Urutkan tabel", list(backlog.SORT_KEYS), label_visibility="collapsed"
        )

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
            for g in backlog.sort_library(data.library, mode_urut)
        ]
        st.dataframe(tampilan, use_container_width=True, hide_index=True)

    with st.expander("Ekspor / Impor CSV"):
        kiri, kanan = st.columns(2)

        with kiri:
            # File dibuat per profile supaya tidak bentrok antar user di server.
            path = f"export_{data.current_profile_id}.csv"
            data.export_csv(path)
            with open(path, encoding="utf-8") as f:
                st.download_button(
                    "Unduh CSV", f.read(), "backlog.csv", "text/csv",
                    disabled=not data.library,
                )

        with kanan:
            st.caption("Format: judul,harga,estimasi_jam,jam_main (baris pertama header)")
            berkas = st.file_uploader(
                "Impor CSV", type="csv", label_visibility="collapsed",
                key=f"csv_upload_{st.session_state.get('csv_version', 0)}",
            )
            if berkas and st.button("Impor"):
                try:
                    teks = berkas.getvalue().decode("utf-8-sig")
                except UnicodeDecodeError:
                    hw.flash_error("File harus berupa teks UTF-8.")
                else:
                    ok, gagal = data.import_csv(teks)
                    if ok:
                        hw.flash_success(f"{ok} game berhasil diimpor.")
                    if gagal:
                        hw.flash_error("; ".join(gagal[:5]))
                # Key baru membuat uploader kosong lagi setelah impor.
                st.session_state.csv_version = st.session_state.get("csv_version", 0) + 1
                st.rerun()

    if data.library:

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
        try:
            data.add_game(title, price, est_hours, played_hours)
        except data.DataError as e:
            hw.flash_error(str(e))
        else:
            hw.flash_success(f"'{title.strip()}' berhasil ditambahkan ke backlog kamu.")
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
        input_disc = hw.input_persen("Masukkan Diskon Saat Ini (%)")

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
        if not new_title.strip():
            st.error("Judul game tidak boleh kosong!")
        elif input_price <= 0 or eval_est_hours <= 0:
            st.error("Harga atau Estimasi Jam tidak boleh 0!")
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

            st.markdown(f"### Hasil Keputusan untuk {new_title.strip()}")

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