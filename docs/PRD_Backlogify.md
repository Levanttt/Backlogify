# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Backlogify: Backlog & Purchase Decision Analytics


## 1. Overview produk

| | |
|---|---|
| Nama produk | Backlogify |
| Tipe aplikasi | Web Dashboard Analitik & Decision Engine (Streamlit) |
| Konteks | Project mata kuliah Program Fundamental Python, Semester 5 |
| Tim | Kelompok 3 |
| Status | MVP berjalan, penyimpanan JSON lokal, dashboard web selesai |

## 2. Masalah & tujuan

Problem statement: gamer sering membeli game secara impulsif saat sale, sehingga backlog menumpuk dan uang mengendap tanpa nilai guna.

Goal: aplikasi membantu gamer mengambil keputusan belanja yang rasional (BUY vs WAIT) lewat tiga sinyal:
- Cost-per-Hour, efisiensi uang terhadap waktu main
- Uang Ngendap, nilai uang yang belum kepakai, dihitung proporsional terhadap sisa jam yang belum dimainkan di tiap game
- Total sisa jam backlog

## 3. Target pengguna

Gamer PC/konsol yang rutin membeli game saat diskon dan menumpuk backlog.

## 4. Ruang lingkup fitur (MVP)

Fitur terbagi jadi lima area. Tiap area dipegang satu orang dan mencakup semua fungsi/menu yang kepake di alur itu, walau fungsinya tersebar di beberapa file. Satu fungsi yang dipakai lebih dari satu fitur tetap punya satu penanggung jawab utama, dicatat di tiap fitur di bawah.

### Fitur 1: Login & Profile Management (pemilik: Nabil)

- User memilih atau mengetik nama profil saat membuka app, tanpa password. Ini memisahkan data antar pengguna pada instance Streamlit yang sama.
- Kalau nama profil sudah ada, sistem memuat library dan threshold tersimpan milik profil itu lewat `data.login()`. Kalau belum ada, sistem membuat profil baru dan mengarahkan user ke alur Setup Awal Threshold sebelum masuk dashboard.
- File dan fungsi utama: `data.py` (`login`, `find_profile_name`, `load_all_profiles`, `save_all_profiles`), blok "SISTEM LOGIN" dan "SETUP AWAL UNTUK PROFIL BARU" di `app_web.py`.
- State profil aktif (`current_profile`, `library`, `saved_thresholds`, `is_new_profile`) disimpan di `st.session_state`, bukan variabel global module, supaya dua profil yang login bersamaan tidak saling menimpa data. `data.library` dan `data.saved_thresholds` tetap bisa dibaca dari `app_web.py` lewat `__getattr__` di level module `data.py`. Isu sebelumnya soal state global sudah diperbaiki (lihat Bagian 8).

### Fitur 2: Smart Estimate & Custom Threshold Management (pemilik: Alwi)

- Smart Estimate: modul mengambil estimasi durasi tamat lewat `howlongtobeatpy`/`api.get_estimated_hours()`, dibungkus try-except. Kalau panggilan API gagal atau timeout, user memasukkan estimasi jam secara manual. Integrasinya murni ke HLTB.
- Fungsi `pilih_estimasi_jam()` di `helpers_web.py` jadi kanal pengiriman Smart Estimate ke menu lain, dipanggil dari Registrasi Game Baru, tab Update Target di Koleksi & Summary, dan Evaluasi Pembelian. Alwi merawat fungsi ini karena isinya memang logic Smart Estimate, tapi fitur lain tetap boleh menyesuaikan titik panggilnya masing-masing kalau kebutuhan tampilannya beda.
- Modul memakai caching bawaan Streamlit untuk hasil API call, bukan mekanisme cache/retry custom.
- Custom Threshold Management: user mengatur dan menyimpan sendiri batas Unplayed Value, sisa jam backlog, dan minimal diskon, per profile, lewat `data.save_thresholds()`. Mencakup form Setup Awal Threshold (saat profil baru pertama login) dan menu Pengaturan Threshold. Login/Multi-user dan Custom Limits sudah disepakati masuk MVP scope, jadi ini fitur utama, bukan tugas sampingan.

### Fitur 3: Registrasi Game Baru & Data Backend (pemilik: Billy)

- Form tambah game baru: judul, harga, target estimasi jam tamat (lewat Fitur 2), dan playtime awal (input jam langsung atau perkiraan persentase).
- Validasi: judul tidak boleh kosong, estimasi jam harus lebih dari 0.
- Status game (Unplayed, In-Progress, Completed) dihitung otomatis lewat `determine_status()`, user tidak mengubah field ini secara manual.
- File dan fungsi utama: blok "Registrasi Game Baru" di `app_web.py`, `data.add_game()`.
- Data Backend: Billy juga pegang lapisan penyimpanan data (`load_all_profiles()`/`save_all_profiles()` sekarang), dipakai lewat fungsi masing-masing oleh keempat fitur lain. Versi `data.py` yang pakai Supabase sudah dibangun dan pernah jalan, tinggal diaktifkan lagi setelah UTS sebagai arsitektur akhir (lihat Bagian 6).

### Fitur 4: Koleksi & Summary (pemilik: Rafael)

- Menampilkan metric total game, total nilai koleksi, Uang Ngendap, dan sisa jam backlog.
- Tabel detail pustaka game, plus tab Kelola Game: Update Progress (`data.update_played_hours()`), Update Target (`data.update_est_hours()`), dan Hapus Game (`data.delete_game()`).
- Memakai `analytics.get_total_spent()` langsung, dan menampilkan hasil `backlog.get_unplayed_value()`/`backlog.get_remaining_hours()` yang perhitungannya jadi tanggung jawab Fitur 5.

### Fitur 5: Evaluasi Pembelian & Decision Engine (pemilik: Irfan)

- User memasukkan judul, harga asli, diskon, dan estimasi jam game yang mau dibeli.
- Sistem menghitung CPH lewat `analytics.calculate_cph()`, membandingkan kondisi backlog user dengan threshold tersimpan, lalu mengeluarkan rekomendasi BUY atau WAIT sesuai aturan di Bagian 5.
- Pemilik utama dari `backlog.get_unplayed_value()` dan `backlog.get_remaining_hours()`, karena dua fungsi ini eksis untuk mengukur seberapa aman kondisi backlog sebelum keputusan beli, meskipun dipanggil juga sebagai tampilan di Fitur 4.

## 5. Aturan logika decision engine

Sistem merekomendasikan WAIT kalau salah satu kondisi berikut terpenuhi:

| Kondisi | Default threshold | Bisa di-custom? |
|---|---|---|
| Total Uang Ngendap | > Rp 1.000.000 | Ya, per profile |
| Total Sisa Jam Backlog | > 50 jam | Ya, per profile |
| Diskon Game Baru | < 50% | Ya, per profile |

Kalau semua indikator ada dalam batas aman, sistem merekomendasikan BUY.

Uang Ngendap dihitung proporsional terhadap sisa jam tiap game yang belum tamat, lewat rumus `(est_hours - played_hours) / est_hours * price`, dijumlahkan dari seluruh game di library. Game yang belum disentuh sama sekali menyumbang harga penuh, game yang sudah tamat menyumbang nol, dan game yang lagi dimainkan menyumbang sebagian sesuai progressnya.

Priority Score (game yang disarankan diselesaikan duluan) memakai sisa jam bermain paling sedikit sebagai patokan, bukan CPH terendah seperti di rencana awal. Rumusnya lebih sederhana dan sudah berjalan di `backlog.get_priority_game()`.

Nilai default di atas jadi fallback untuk profile baru yang belum mengatur limit sendiri.

Sistem pakai logic rule-based lewat if/else. Modul tidak butuh model prediksi atau ML untuk mencapai tujuan produk.

## 6. Spesifikasi teknis

- Bahasa & framework: Python 3.x, Streamlit.
- Penyimpanan data untuk course ini: file JSON lokal (`backlog.json`), berstruktur per profile, key mengikuti nama variabel Python persis:

```json
{
  "Levant": {
    "library": [
      {"title": "...", "price": 0, "played_hours": 0, "est_hours": 0, "status": "..."}
    ],
    "thresholds": {
      "max_unplayed_value": 1000000,
      "max_backlog_hours": 50,
      "min_discount_percent": 50
    }
  }
}
```

- Dependensi: `streamlit`, library HTTP yang dipakai `api.py`, `howlongtobeatpy`.
- Struktur kode: function-based per modul, tanpa class. File aktif: `data.py`, `backlog.py`, `analytics.py`, `api.py`, `app_web.py`, `helpers_web.py`. `helpers.py` sudah tidak dipakai, peninggalan dari rencana versi CLI sebelum pindah ke Streamlit, dan tidak dipanggil dari `app_web.py`.
- Arsitektur akhir: JSON lokal ini bersifat sementara. Versi `data.py` yang pakai Supabase (Postgres) sudah pernah dibangun dan jalan, tapi untuk sekarang disimpan dulu dan tim balik ke JSON sampai setelah UTS.

## 7. Batasan & out of scope

- Aplikasi tidak menangani transaksi pembayaran nyata. Hanya analitik dan simulasi keputusan.
- Aplikasi tidak sync ke cloud, dan tidak mendukung multi-device. Data tersimpan lokal, dalam satu file JSON pada satu perangkat.
- Fungsi agregasi generik (`aggregate(items, filter_fn, value_fn)`) yang sempat direncanakan untuk dipakai bersama oleh `analytics.py` dan `backlog.py` tidak jadi dibuat. Dua modul itu masing-masing memakai loop manual sendiri, dianggap cukup untuk scope course ini.

## 8. Known issues

- Bug state global di `data.py` sudah diperbaiki. Sebelumnya `current_profile`, `library`, dan `saved_thresholds` berupa variabel level module, sehingga dua profil yang login bersamaan di instance Streamlit yang sama saling menimpa data. Sekarang state itu ada di `st.session_state` dan sudah dites dengan dua session bersamaan. Pemilik: Fitur 1.
- Dua orang yang menyimpan data pada saat yang sama masih bisa saling menimpa di `backlog.json`, karena penyimpanan membaca seluruh file lalu menulis ulang. Risikonya kecil untuk pemakaian sekarang, dan selesai dengan sendirinya setelah pindah ke Supabase.
- Versi `data.py` yang pakai Supabase masih memakai variabel global yang sama, ditambah `current_profile_id`. Perbaikan `st.session_state` yang sama harus diterapkan di sana waktu versi itu diaktifkan lagi setelah UTS. Pemilik: Billy.

## 9. Future improvements

- Autentikasi password, jadi prasyarat sebelum deploy publik (target akhir project, bukan cuma submission course). Login mengecek kecocokan password dengan username yang diinput, dan pendaftaran profil baru mengecek dulu apakah username sudah dipakai profil lain.
- Fungsi agregasi generik, kalau logic filter-sum di `analytics.py`/`backlog.py` makin banyak dan mulai terasa duplikatif.

## 10. Pembagian tugas

| Nama | Fitur utama | File/fungsi yang disentuh |
|---|---|---|
| Nabil | Login & Profile Management | `data.py` (login, profile), blok login & setup awal di `app_web.py` |
| Alwi | Smart Estimate & Custom Threshold Management | `api.py`, `pilih_estimasi_jam()` di `helpers_web.py`, `data.save_thresholds()`, blok Setup Awal Threshold dan Pengaturan Threshold di `app_web.py` |
| Billy | Registrasi Game Baru & Data Backend | Blok "Registrasi Game Baru" di `app_web.py`, `data.add_game()`; `load_all_profiles()`/`save_all_profiles()` sekarang, plus migrasi ke Supabase (Postgres) setelah UTS, versi `data.py`-nya sudah dibangun dan jalan |
| Rafael | Koleksi & Summary | Blok "Koleksi & Summary" di `app_web.py`, `data.update_played_hours()`/`update_est_hours()`/`delete_game()` |
| Irfan (Lead) | Evaluasi Pembelian & Decision Engine | `analytics.py`, blok "Evaluasi Pembelian" di `app_web.py`, `backlog.get_unplayed_value()`/`get_remaining_hours()` |
