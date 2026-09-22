import streamlit as st
import data
import backlog
import analytics
import api

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
        new_unplayed = st.number_input("Batas Maksimal Uang Ngendap (Rp)", value=1000000.0, step=50000.0)
        new_hours = st.number_input("Batas Maksimal Sisa Jam Backlog", value=50.0, step=5.0)
        new_disc = st.number_input("Batas Minimal Diskon Game (%)", value=50.0, min_value=0.0, max_value=100.0)
        
        if st.form_submit_button("Simpan & Lanjut ke Dashboard"):
            threshold_data = {
                "max_unplayed_value": new_unplayed,
                "max_backlog_hours": new_hours,
                "min_discount_percent": new_disc
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
    
    if data.library:
        st.dataframe(data.library, use_container_width=True)
    else:
        st.info("Koleksi backlog kamu masih kosong.")

elif menu == "Registrasi Game Baru":
    st.header("Registrasi Game Backlog")
    
    title = st.text_input("Judul Game")
    price = st.number_input("Harga Beli Final (Rp)", min_value=0.0, step=5000.0)
    
    st.markdown("**Estimasi Jam Tamat (HowLongToBeat)**")
    if st.button("Cari Waktu Tamat via API"):
        with st.spinner("Mencari data ke HLTB..."):
            hltb_data = api.get_estimated_hours(title)
            st.session_state.hltb_menu1 = hltb_data
            if not hltb_data:
                st.warning("Data tidak ditemukan. Silakan input manual.")
                
    est_hours = 0.0
    is_manual = True
    if "hltb_menu1" in st.session_state and st.session_state.hltb_menu1:
        opts = st.session_state.hltb_menu1
        label_opsi = [
            ("Main Story", opts["main_story"]),
            ("Main + Sides", opts["main_extra"]),
            ("Completionist", opts["completionist"]),
        ]
        opsi_tersedia = [label for label, jam in label_opsi if jam is not None]
        if opsi_tersedia:
            is_manual = False
            playstyle = st.selectbox("Pilih Target Penyelesaian", opsi_tersedia + ["Input Manual"])
            if playstyle == "Input Manual":
                is_manual = True
            else:
                est_hours = dict(label_opsi)[playstyle]
            
    if is_manual:
        est_hours = st.number_input("Input Jam Tamat (Manual)", min_value=0.0, step=1.0)
        
    st.markdown("---")
    st.markdown("**Lacak Playtime Saat Ini**")
    mode = st.radio("Metode Input:", ["Input jam langsung", "Input persentase progress (%)"])
    
    if mode == "Input jam langsung":
        played_hours = st.number_input("Jam Main Saat Ini", min_value=0.0, step=1.0)
    else:
        progress_pct = st.slider("Persentase Progress (%)", 0, 100, 0)
        played_hours = (progress_pct / 100) * est_hours
        st.caption(f"Setara dengan: **{played_hours:.1f} Jam**")
        
    if st.button("Tambahkan ke Pustaka", type="primary"):
        if title.strip() == "":
            st.error("Judul game tidak boleh kosong!")
        else:
            data.add_game(title, price, est_hours, played_hours)
            st.success(f"Berhasil! '{title}' telah ditambahkan ke backlog kamu.")
            if "hltb_menu1" in st.session_state:
                del st.session_state["hltb_menu1"] # Reset state API

elif menu == "Evaluasi Pembelian":
    st.header("Evaluasi Pembelian Game Baru")
    new_title = st.text_input("Judul Game Target")

    if st.session_state.get("eval_title") != new_title:
        st.session_state.eval_deal = None
        st.session_state.eval_hltb = None

    if st.button("Cek Diskon & Waktu via API"):
        with st.spinner("Mengambil data CheapShark & HLTB..."):
            st.session_state.eval_deal = api.get_discount_info(new_title)  
            st.session_state.eval_hltb = api.get_estimated_hours(new_title)
            st.session_state.eval_title = new_title

    def_price, def_disc = 0.0, 0.0
    if st.session_state.get("eval_deal"):
        def_price = st.session_state.eval_deal['price_original']
        def_disc = float(st.session_state.eval_deal['discount_percent'])
        st.success(f"Sistem mendeteksi kemungkinan diskon {def_disc:.0f}% (Estimasi harga asli Rp {def_price:,.0f}).")
        st.caption("Jika nominal API kurang akurat (karena Regional Pricing Steam), silakan koreksi angka di bawah.")
        
    col1, col2 = st.columns(2)
    with col1:
        input_price = st.number_input("Harga Asli (Rp)", value=float(def_price), step=5000.0)
    with col2:
        input_disc = st.number_input("Diskon (%)", value=float(def_disc), min_value=0.0, max_value=100.0)
        
    st.markdown("---")
    eval_est_hours = 0.0
    is_manual_eval = True
    if st.session_state.get("eval_hltb"):
        opts_eval = st.session_state.eval_hltb
        label_opsi_eval = [
            ("Main Story", opts_eval["main_story"]),
            ("Main + Sides", opts_eval["main_extra"]),
            ("Completionist", opts_eval["completionist"]),
        ]
        opsi_tersedia_eval = [label for label, jam in label_opsi_eval if jam is not None]
        if opsi_tersedia_eval:
            is_manual_eval = False
            playstyle_eval = st.selectbox("Gaya Main (HLTB)", opsi_tersedia_eval + ["Input Manual"])
            if playstyle_eval == "Input Manual":
                is_manual_eval = True
            else:
                eval_est_hours = dict(label_opsi_eval)[playstyle_eval]
        
    if is_manual_eval:
        eval_est_hours = st.number_input("Estimasi Jam Tamat", min_value=0.0, step=1.0)
        
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
            if tot_unplayed > max_unplay: reasons.append(f"Uang ngendap kamu (Rp {tot_unplayed:,.0f}) melampaui batas.")
            if tot_rem_hours > max_hrs: reasons.append(f"Sisa waktu backlog ({tot_rem_hours:.0f} Jam) melampaui batas.")
            if input_disc < min_disc: reasons.append(f"Diskon belum mencapai batas minimal yang kamu tetapkan ({min_disc:.0f}%).")
            
            st.markdown("### Hasil Keputusan")
            if reasons:
                st.error("KEPUTUSAN: WAIT (TUNDA PEMBELIAN)")
                for r in reasons:
                    st.warning(f"• {r}")
            else:
                st.success("KEPUTUSAN: BUY (AMAN DIBELI)")
                st.info("Kondisi backlog kamu aman dan indikator diskon memenuhi standar.")
                
            st.write(f"**Harga Bayar Akhir:** Rp {actual_price:,.0f} &nbsp;&nbsp;|&nbsp;&nbsp; **Cost per Hour:** Rp {pot_cph:,.0f} / Jam")

elif menu == "Pengaturan Threshold":
    st.header("Pengaturan Threshold & Limit")
    st.write("Sesuaikan toleransi Backlogify dalam memberikan rekomendasi keputusan pembelian game kamu.")
    
    current_unplayed = data.saved_thresholds.get("max_unplayed_value", 1000000.0)
    current_hours = data.saved_thresholds.get("max_backlog_hours", 50.0)
    current_disc = data.saved_thresholds.get("min_discount_percent", 50.0)
    
    with st.form("threshold_form"):
        new_unplayed = st.number_input("Batas Maksimal Uang Ngendap (Rp)", value=float(current_unplayed), step=50000.0)
        new_hours = st.number_input("Batas Maksimal Sisa Jam Backlog", value=float(current_hours), step=5.0)
        new_disc = st.number_input("Batas Minimal Diskon Game (%)", value=float(current_disc), min_value=0.0, max_value=100.0)
        
        submitted = st.form_submit_button("Simpan Pengaturan")
        if submitted:
            data.save_thresholds({
                "max_unplayed_value": new_unplayed,
                "max_backlog_hours": new_hours,
                "min_discount_percent": new_disc
            })
            st.success("Batas threshold berhasil diperbarui dan disimpan secara lokal!")