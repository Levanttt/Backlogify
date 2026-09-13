# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Backlogify: Backlog & Purchase Decision Analytics

## 1. Overview produk

| | |
|---|---|
| Nama produk | Backlogify |
| Tipe aplikasi | Web Dashboard Analitik & Decision Engine (Streamlit) |
| Konteks | Project mata kuliah Program Fundamental Python, Semester 5 |
| Tim | Kelompok 3 |
| Status | Prototype & Technical Spec |

## 2. Masalah & tujuan

Problem statement: gamer sering membeli game secara impulsif saat sale, sehingga backlog menumpuk dan uang mengendap tanpa nilai guna.

Goal: aplikasi membantu gamer mengambil keputusan belanja yang rasional (`BUY` vs `WAIT`) lewat tiga sinyal:
- Cost-per-Hour, efisiensi uang terhadap waktu main
- Unplayed Value, nilai uang yang mengendap di game yang belum dimainkan
- Total sisa jam backlog

## 3. Target pengguna

Gamer PC/konsol yang rutin membeli game saat diskon dan menumpuk backlog.

## 4. Ruang lingkup fitur (MVP)

Fitur terbagi jadi 5 modul. Tiap modul berupa kumpulan fungsi dalam file terpisah sesuai lingkup Fundamental Python yang sederhana.

### Modul 1: Library management & user profile (`data.py`)
- User memilih atau mengetik nama saat membuka app pertama kali, tanpa password. Ini memisahkan data antar pengguna pada satu perangkat. Modul tidak menyediakan hashing, session, atau proteksi akses lain.
- User menambahkan data game (judul, platform, harga, status, jam main). Modul menyimpan data ini ke `backlog.json`, per profile.
- User mengedit progress dengan memasukkan jam main langsung.
- Modul menghitung status game (Unplayed, In-Progress, Completed) otomatis, dengan membandingkan jam main terhadap estimasi durasi tamat. User tidak mengubah field ini secara manual.

### Modul 2: Game info & API integrator (`api.py`)
- Modul mengambil estimasi durasi tamat lewat `howlongtobeatpy`, dan membungkus pemanggilan ini dalam try-except. Kalau panggilan API gagal atau timeout, user memasukkan estimasi jam secara manual. Modul tidak butuh sistem fallback file terpisah.
- Modul mengambil data harga dan diskon lewat CheapShark API.
- Genre bersifat opsional. Modul mengambilnya otomatis dari CheapShark atau HLTB kalau tersedia; kalau tidak, user mengisi genre manual. Breakdown per genre di Modul 3 tetap berjalan dengan data manual ini.
- Modul memakai `@st.cache_data` bawaan Streamlit untuk cache hasil API call. Tim tidak membangun mekanisme cache atau retry custom.

### Modul 3: Cost & spending analytics (`analytics.py`)
- Modul menghitung Cost-per-Hour (CPH) per game: harga dibagi jam main, dengan penanganan divide-by-zero untuk game yang belum dimainkan.
- Modul menghitung total pengeluaran dan breakdown per platform atau genre.
- Modul memakai fungsi Python native (`sum`, list comprehension, `dict`) untuk agregasi. Pandas muncul hanya di layer visualisasi seperti `st.bar_chart`, bukan di logic inti.

### Modul 4: Backlog intelligence (`backlog.py`)
- Modul menghitung Unplayed Value: total harga game dengan jam main nol.
- Modul menghitung total sisa jam backlog: durasi tamat dikurangi jam main, untuk game yang belum selesai.
- Modul membuat Priority Score sederhana, dengan ranking berdasarkan CPH terendah. Game paling worth it selesai duluan.
- Modul 3 dan 4 memakai satu fungsi agregasi generik yang sama, misalnya `aggregate(games, filter_fn, value_fn)`. Ini mencegah logic filter-sum dobel di dua tempat.

### Modul 5: Decision engine & dashboard UI (`app.py`)
- Modul menampilkan metrik utama di Streamlit: total spending, unplayed value, sisa jam backlog.
- Modul mengevaluasi keputusan `BUY` vs `WAIT` berdasarkan aturan di Bagian 5.
- User mengatur dan menyimpan sendiri Custom Limits/Threshold: batas Unplayed Value, jam sisa backlog, dan minimal diskon, per profile. Kondisi ekonomi tiap orang beda, jadi limit ini beda juga. Kalau user belum mengatur limit sendiri, modul memakai nilai default di Bagian 5.


## 5. Aturan logika decision engine

Sistem merekomendasikan `WAIT` kalau salah satu kondisi berikut terpenuhi:

| Kondisi | Default threshold | Bisa di-custom? |
|---|---|---|
| Total Unplayed Value | > Rp 1.000.000 | Ya, per profile |
| Total Sisa Jam Backlog | > 50 jam | Ya, per profile |
| Diskon Game Baru | < 50% | Ya, per profile |

Kalau semua indikator ada dalam batas aman, sistem merekomendasikan `BUY`.

Nilai default di atas jadi fallback untuk profile baru yang belum mengatur limit sendiri.

Sistem pakai logic rule-based lewat if/else. Modul tidak butuh model prediksi atau ML untuk mencapai tujuan produk.


## 6. Spesifikasi teknis

- Bahasa & framework: Python 3.x, Streamlit.
- Penyimpanan data: file JSON lokal (`backlog.json`), berstruktur per profile:
  ```json
  {
    "andi": {
      "games": [ {"judul": "...", "platform": "...", "harga": 0, "jam_main": 0, "genre": "..."} ],
      "limits": {"unplayed_value": 1000000, "backlog_hours": 50, "min_discount": 50}
    },
    "budi": { "games": [...], "limits": {...} }
  }
  ```
- Dependensi: `streamlit`, `requests`, `howlongtobeatpy` (opsional, best-effort). Tim menambahkan pandas hanya kalau chart Streamlit butuh; `st.bar_chart` biasa jalan dengan `dict`/list saja.
- Struktur kode: function-based per modul. Gunakan class hanya kalau butuh inheritance atau polymorphism, dan scope ini sebetulnya tidak butuh keduanya.


## 7. Batasan & out of scope

- Aplikasi tidak menangani transaksi pembayaran nyata. Hanya analitik dan simulasi keputusan.
- Profile/login tidak pakai password. Modul tidak punya autentikasi, enkripsi, atau proteksi akses. Siapa pun yang membuka app bisa memilih atau melihat profile mana pun.
- Aplikasi tidak sync ke cloud, dan tidak mendukung multi-device. Aplikasi menyimpan data lokal, dalam satu file JSON pada satu perangkat.


## 8. Future improvements

- Autentikasi sungguhan, dengan password dan hashing. Ini jadi relevan kalau tim deploy publik atau lintas perangkat nanti.
- Cloud sync atau database, untuk akses dari banyak device.
- Genre classification otomatis lewat sumber data tambahan, kalau CheapShark atau HLTB tidak mengembalikan genre yang lengkap.


## 9. Pembagian tugas

| Nama | Modul | File |
|---|---|---|
| Irfan (Lead) | Decision Engine & Cost Analytics | `app.py`, `analytics.py` |
| Billy (Dev 1) | Library Management & Backlog Intelligence | `data.py`, `backlog.py` |
| Alwi (Dev 2) | Game Info & API Integrator | `api.py` |
| Rafael (Dev 3) | Validasi Input & Data Sampel | `helpers.py` |
| Nabil (Dev 4) | Tampilan Koleksi & Ringkasan (Menu 3) | bagian display di `app.py` |