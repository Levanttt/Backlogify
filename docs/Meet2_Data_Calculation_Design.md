# MEET 2: DATA AND CALCULATION DESIGN
## Backlogify: Kelompok 3

## 1. Naming convention

| Kategori | Nama Variabel | Tipe Data |
|---|---|---|
| Judul game | `title` | `str` |
| Harga beli | `price` | `float` |
| Jam yang sudah dimainkan | `played_hours` | `float` |
| Estimasi jam tamat (HLTB) | `est_hours` | `float` |
| Status game | `status` | `str` |
| Cost-per-Hour | `cph` | `float` |
| Total pengeluaran | `total_spent` | `float` |
| Total uang ngendap (0 jam main) | `total_unplayed_value` | `float` |
| Total sisa jam backlog | `total_backlog_hours` | `float` |
| Batas maks. sisa jam backlog | `max_backlog_hours` | `float` |
| Batas min. diskon | `min_discount_percent` | `float` |
| Batas maks. uang ngendap | `max_unplayed_value` | `float` |

Nilai `status` yang valid (case-sensitive): `"Unplayed"`, `"In-Progress"`, `"Completed"`

Aturan umum: semua nama variabel pakai `snake_case`. Variabel akumulasi/total diawali `total_`. Variabel batas/threshold diawali `max_` atau `min_`.


## 2. Pembagian tugas & deliverable Meet 2

| Nama | Modul | File | Deliverable Meet 2 |
|---|---|---|---|
| Irfan (Lead) | Decision Engine & Cost Analytics | `app.py`, `analytics.py` | I/O spec Menu 2 & Menu 4, compile dokumen final |
| Billy (Dev 1) | Library Management & Backlog Intelligence | `data.py`, `backlog.py` | I/O spec Menu 1 & fungsi backlog intelligence |
| Alwi (Dev 2) | Game Info & API Integrator | `api.py` | I/O spec proses fetch data (masih stub, fallback manual) |
| Rafael (Dev 3) | Validasi Input & Data Sampel | `helpers.py` | I/O spec fungsi agregasi & validasi input |
| Nabil (Dev 4) | Tampilan Koleksi & Ringkasan (Menu 3) | bagian display di `app.py` | I/O spec Menu 3 |

## 3. Product data dictionary

### Field per game (disimpan di `library`)

| Field | Tipe Data | Deskripsi | Contoh Nilai |
|---|---|---|---|
| `title` | `str` | Judul game | `"Cyberpunk 2077"` |
| `price` | `float` | Harga beli (Rp) | `350000` |
| `played_hours` | `float` | Jam yang sudah dimainkan | `10.0` |
| `est_hours` | `float` | Estimasi jam tamat | `50.0` |
| `status` | `str` | Status progres game | `"In-Progress"` |

### Nilai turunan (dihitung, tidak disimpan permanen)

| Nilai | Tipe Data | Dihitung Lewat | Deskripsi |
|---|---|---|---|
| `cph` | `float` | `analytics.calculate_cph()` | Biaya per jam main |
| `total_spent` | `float` | `analytics.get_total_spent()` | Total uang keluar untuk seluruh koleksi |
| `total_unplayed_value` | `float` | `backlog.get_unplayed_value()` | Total harga game yang belum dimainkan |
| `total_backlog_hours` | `float` | `backlog.get_remaining_hours()` | Total sisa jam main dari game yang belum selesai |

## 4. Input, process, output specification

### Fitur: Registrasi game backlog baru — Billy (Dev 1), Menu 1 di `app.py` & `data.py`
```
Input   : title (str), price (float), est_hours (float), mode pelacakan (1=jam langsung/2=persentase), played_hours atau progress_pct (float)
Process : data.determine_status() membandingkan played_hours dengan est_hours untuk menentukan status; data.add_game() menyimpan entry baru ke library
Output  : game baru masuk ke library, ringkasan total backlog tercetak (total_spent, total_unplayed_value, total_backlog_hours)
```

### Fitur: Backlog intelligence, `backlog.py`
```
Input   : library (list of dict)
Process : backlog.get_unplayed_value() dan backlog.get_remaining_hours() memakai helpers.aggregate() dengan filter berbeda; backlog.get_priority_game() mencari game aktif dengan sisa jam paling sedikit
Output  : total_unplayed_value (float), total_backlog_hours (float), game prioritas (dict atau None kalau backlog kosong)
```

### Fitur: Game info & API integrator, `api.py`
```
Input   : title (str) - rencana, belum dipanggil dari app.py
Process : get_estimated_hours() dan get_discount_info() masih stub (raise NotImplementedError), menunggu integrasi howlongtobeatpy dan CheapShark
Output  : belum ada, app.py masih pakai input manual sebagai fallback
```

### Fitur: Cost & spending analytics, `analytics.py`
```
Input   : price (float), hours (float - bisa played_hours atau est_hours tergantung konteks pemanggilan)
Process : calculate_cph() membagi price dengan hours, dengan pengecekan hours == 0; get_total_spent() menjumlahkan seluruh price lewat helpers.aggregate()
Output  : nilai cph (float), total_spent (float)
```

### Fitur: Evaluasi pembelian & custom threshold, `app.py`
```
Input Menu 2 : new_title, new_price_original, new_discount_percent, new_est_hours
Process Menu 2 : hitung actual_new_price dari diskon, potential_cph lewat analytics.calculate_cph(), bandingkan 3 threshold untuk menentukan BUY/WAIT, cari closest_game lewat backlog.get_priority_game()
Output Menu 2 : decision ("BUY"/"WAIT"), reason (str), action_plan (str)

Input Menu 4 : nilai threshold baru (opsional, boleh dikosongkan)
Process Menu 4 : update variabel global max_unplayed_value, max_backlog_hours, min_discount_percent kalau user mengisi
Output Menu 4 : threshold ter-update, konfirmasi tercetak
```

### Fitur: Tampilan koleksi & ringkasan, `app.py`
```
Input   : library (list of dict), threshold aktif (max_unplayed_value, dst)
Process : menu_view_summary() mencetak tabel dari library, membandingkan total_unplayed_value dengan max_unplayed_value untuk status_financial
Output  : tabel koleksi tercetak ke layar, ringkasan total dan status (AMAN/MELEBIHI LIMIT)
```

### Fitur: Validasi input & utility bersama, `helpers.py`
```
Input   : prompt (str) untuk get_float_input(); items, filter_fn, value_fn untuk aggregate()
Process : get_float_input() mengulang sampai user memasukkan angka valid; aggregate() memfilter items lalu menjumlahkan value_fn dari yang lolos
Output  : nilai float valid dari user; hasil sum dari agregasi, dipakai bersama oleh analytics.py dan backlog.py
```

## 5. Basic calculation log

| Kalkulasi | Rumus | Operator yang Dipakai | File |
|---|---|---|---|
| Cost-per-Hour | `price / hours` | `/` | `analytics.py` |
| Total pengeluaran | `sum(price)` | - | `analytics.py` |
| Harga setelah diskon | `price_original * (1 - discount_percent/100)` | `*`, `-`, `/` | `app.py` |
| Total uang ngendap | `sum(price where played_hours == 0)` | `==` | `backlog.py` |
| Total sisa jam backlog | `sum(max(0, est_hours - played_hours) where status != "Completed")` | `-`, `!=` | `backlog.py` |
| Keputusan BUY/WAIT | kombinasi `>`, `<` dari 3 threshold | `>`, `<` | `app.py` |

## 6. Individual contribution log

| Nama | Tanggal | Kontribusi di Meet 2 |
|---|---|---|
| Irfan | | |
| Billy | | |
| Alwi | | |
| Rafael | | |
| Nabil | | |