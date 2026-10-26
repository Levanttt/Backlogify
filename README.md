# Backlogify

Backlogify adalah aplikasi Python berbasis Streamlit untuk memantau backlog game dan memutuskan apakah sebuah game layak dibeli sekarang. Aplikasi ini dibuat sebagai proyek mata kuliah Programming Fundamental.

Masalah yang diselesaikan: pemain sering membeli game saat diskon tanpa melihat game yang belum dimainkan, sehingga uang dan waktu menumpuk di backlog. Backlogify mencatat koleksi game, menghitung uang yang masih ngendap, lalu memberi keputusan BUY atau WAIT berdasarkan threshold yang pemain tetapkan sendiri.

Versi online: <url-deploy>

## Fitur

| Menu | Fungsi |
| --- | --- |
| Login dan profile | Daftar dan masuk dengan nama profile dan password. Profile baru mengisi threshold awal sebelum masuk ke dashboard. Login bertahan saat halaman di-refresh. |
| Koleksi dan Summary | Chart status game, uang ngendap per game, dan pemakaian threshold, ditambah kartu ringkasan total game, nilai koleksi, uang ngendap, dan sisa jam backlog. Tabel game bisa diurutkan. Jam main, target estimasi, dan penghapusan game dikelola dari sini. Koleksi bisa diekspor dan diimpor lewat CSV. |
| Registrasi Game Baru | Menambah game dengan judul, harga, estimasi jam tamat, dan jam main saat ini. Estimasi jam bisa diisi manual atau diambil dari HowLongToBeat. |
| Evaluasi Pembelian | Menilai game yang ingin dibeli terhadap backlog dan threshold, lalu menampilkan BUY atau WAIT beserta alasan, rekomendasi aksi, harga bayar, dan cost per hour. Game yang sedang dievaluasi belum dihitung sebagai backlog karena belum dibeli. |
| Pengaturan Threshold | Mengubah tiga batas toleransi: maksimal uang ngendap, maksimal sisa jam backlog, dan minimal diskon. |

## Struktur kode

- `app_web.py`: halaman Streamlit (login, menu, chart, form).
- `data.py`: akses Supabase, login, token sesi, dan operasi game (tambah, ubah, hapus, ekspor, impor CSV).
- `backlog.py`: kelas `Game`, perhitungan uang ngendap dan sisa jam, game prioritas, pencarian linear, dan insertion sort.
- `analytics.py`: perhitungan total pengeluaran dan cost per hour.
- `api.py`: pengambilan estimasi jam dari HowLongToBeat.
- `helpers_web.py`: input angka, pesan flash, dan pilihan estimasi jam.

## Cara menjalankan di komputer sendiri

Prasyarat: Git, Python 3.10 atau lebih baru, dan sebuah project Supabase. Koneksi internet juga dibutuhkan untuk HowLongToBeat, tapi fitur itu bisa dilewati dengan mengisi estimasi manual.

Langkah 1: clone repo dan masuk ke foldernya.

```
git clone (https://github.com/Levanttt/Backlogify.git)
cd Backlogify
```

Langkah 2: buat dan aktifkan virtual environment.

```
python -m venv .venv
.venv\Scripts\activate
```

Di macOS atau Linux, ganti perintah aktivasi dengan `source .venv/bin/activate`.

Langkah 3: install dependency.

```
pip install -r requirements.txt
```

Langkah 4: siapkan database di Supabase. Buat dua tabel dengan kolom berikut.

- `profiles`: `id`, `name`, `password_hash`, `max_unplayed_value`, `max_backlog_hours`, `min_discount_percent`.
- `games`: `id`, `profile_id` (mengacu ke `profiles.id`), `title`, `price`, `played_hours`, `est_hours`, `status`, `created_at`.

Langkah 5: buat file `.streamlit/secrets.toml` berisi tiga nilai berikut. File ini sudah masuk `.gitignore`, jangan di-commit.

```
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "key-dari-project-supabase"
AUTH_SECRET = "string-acak-panjang"
```

`AUTH_SECRET` dipakai untuk menandatangani token login. Cara membuat nilainya:

```
python -c "import secrets; print(secrets.token_hex(32))"
```

Langkah 6: jalankan aplikasi dari folder root repo.

```
streamlit run src/app_web.py
```

Browser terbuka otomatis di `http://localhost:8501`. Tekan Ctrl+C di terminal untuk menghentikan aplikasi.

## Deploy ke Streamlit Community Cloud

1. Push repo ke GitHub, lalu buat app baru di Streamlit Community Cloud dan arahkan ke file `app_web.py`.
2. Di pengaturan app, isi menu Secrets dengan tiga nilai yang sama seperti `secrets.toml` di atas.
3. Setiap push ke branch yang di-deploy memicu redeploy otomatis. Pakai Reboot app hanya jika muncul error modul yang tidak sinkron setelah update.

## Cara pakai

1. Daftar dengan nama profile dan password, lalu masuk. Nama 3 sampai 30 karakter (huruf, angka, spasi, titik, atau strip) dan password minimal 6 karakter. Profile baru langsung membuka Setup Awal Threshold. Isi tiga batas toleransi atau pakai nilai default: uang ngendap maksimal Rp 1,000,000, sisa jam backlog maksimal 50 jam, dan diskon minimal 50%.
2. Buka Registrasi Game Baru untuk memasukkan game yang sudah kamu punya: judul, harga beli, estimasi jam tamat, dan jam main saat ini. Tombol Berikan Opsi Gaya Main Otomatis mengambil estimasi dari HowLongToBeat.
3. Buka Koleksi dan Summary untuk melihat chart dan ringkasan backlog. Ikon filter di samping judul tabel mengatur urutan tabel. Bagian Kelola Game dipakai untuk mengubah jam main, mengubah target estimasi, atau menghapus game.
4. Sebelum membeli game baru, buka Evaluasi Pembelian. Isi judul, harga asli, diskon, dan estimasi jam, lalu tekan Jalankan Evaluasi Decision Engine untuk mendapat BUY atau WAIT.
5. Ubah batas toleransi kapan saja lewat Pengaturan Threshold. Tombol Logout ada di sidebar.

## Ekspor dan impor CSV

Menu Koleksi dan Summary punya expander Ekspor / Impor CSV di bawah tabel.

- Ekspor: tombol Unduh CSV menghasilkan file `backlog.csv` dengan header `judul,harga,estimasi_jam,jam_main`, satu baris per game.
- Impor: unggah file dengan format yang sama, lalu tekan Impor. Baris pertama dianggap header.
- Baris yang tidak valid dilewati dan dilaporkan dengan nomor barisnya, misalnya angka yang salah, kolom kurang, nilai negatif, estimasi nol, atau judul yang sudah ada.
- Judul boleh mengandung koma, karena pemisah dibaca dari tiga kolom terakhir.

## Masalah umum

- `Error: Invalid value: File does not exist: app_web.py`: perintah dijalankan dari folder yang salah. Jalankan dari root repo.
- `streamlit` tidak dikenali atau muncul `ModuleNotFoundError`: virtual environment belum aktif, atau `pip install` belum dijalankan.
- Aktivasi virtual environment diblokir di PowerShell: jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` di terminal yang sama, lalu aktifkan lagi.
- `KeyError: 'AUTH_SECRET'` atau error serupa untuk `SUPABASE_URL` dan `SUPABASE_KEY`: nilai di `secrets.toml` (lokal) atau menu Secrets (Streamlit Cloud) belum diisi.
- `AttributeError` pada modul `data` setelah update di Streamlit Cloud: gunakan Reboot app.
- Muncul pesan Gagal ambil data estimasi otomatis: koneksi lambat atau HowLongToBeat diblokir jaringan. Isi estimasi jam secara manual.
- Game yang belum rilis tidak punya data durasi di HowLongToBeat, jadi estimasi harus diisi manual.
- Port 8501 sedang dipakai: jalankan `streamlit run src/app_web.py --server.port 8502`.

## Batasan saat ini

- Token login disimpan di URL (parameter `t`) agar sesi bertahan saat refresh, dan berlaku 7 hari. Siapa pun yang memegang URL dengan token yang masih aktif bisa membuka profile itu, jadi jangan bagikan URL setelah login.
- Estimasi dari HowLongToBeat butuh koneksi dan bisa diblokir oleh jaringan tertentu.
- Aplikasi tidak memproses pembayaran. Hasilnya hanya analisis dan simulasi keputusan.