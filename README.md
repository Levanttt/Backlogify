# Backlogify

Backlogify adalah aplikasi Python berbasis Streamlit untuk memantau backlog game dan memutuskan apakah sebuah game layak dibeli sekarang. Aplikasi ini dibuat sebagai proyek kelompok mata kuliah Programming Fundamental.

Masalah yang diselesaikan: pemain sering membeli game saat diskon tanpa melihat game yang belum dimainkan, sehingga uang dan waktu menumpuk di backlog. Backlogify mencatat koleksi game, menghitung uang yang masih ngendap, lalu memberi keputusan BUY atau WAIT berdasarkan threshold yang pemain tetapkan sendiri.

## Fitur

| Menu | Fungsi |
| --- | --- |
| Login dan profile | Login berbasis nama profile, tanpa password. Profile baru mengisi threshold awal sebelum masuk ke dashboard. |
| Koleksi dan Summary | Ringkasan total game, nilai koleksi, uang ngendap, dan sisa jam backlog. Mengubah jam main, mengubah target estimasi, dan menghapus game. |
| Registrasi Game Baru | Menambah game dengan judul, harga, estimasi jam tamat, dan jam main saat ini. Estimasi jam bisa diisi manual atau diambil dari HowLongToBeat. |
| Evaluasi Pembelian | Menilai game yang ingin dibeli terhadap backlog dan threshold, lalu menampilkan BUY atau WAIT beserta reason, action plan, harga bayar, dan cost per hour. |
| Pengaturan Threshold | Mengubah tiga batas toleransi: maksimal uang ngendap, maksimal sisa jam backlog, dan minimal diskon. |

## Cara menjalankan di komputer sendiri

Prasyarat: Git dan Python 3.10 atau lebih baru. Koneksi internet hanya dibutuhkan untuk mengambil estimasi jam dari HowLongToBeat, dan fitur itu bisa dilewati dengan mengisi estimasi manual.

Langkah 1: clone repo dan masuk ke foldernya.

```
git clone <url-repo>
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
pip install streamlit howlongtobeatpy
```

Langkah 4: jalankan aplikasi di terminal, dari folder root repo.

```
streamlit run src/app_web.py
```

Browser terbuka otomatis di `http://localhost:8501`. Tekan Ctrl+C di terminal untuk menghentikan aplikasi. Perintahnya harus `streamlit run src/app_web.py`.

Data akan tersimpan di `data/backlog.json` pada komputer masing-masing. File dan foldernya dibuat otomatis saat aplikasi pertama kali jalan, dan file itu tidak ikut di-commit, jadi data satu orang tidak terlihat oleh orang lain.

## Cara pakai

1. Masuk dengan nama profile. Nama baru akan membuat profile baru dan langsung membuka Setup Awal Threshold. Isi tiga batas toleransi, atau pakai nilai default: uang ngendap maksimal Rp 1,000,000, sisa jam backlog maksimal 50 jam, dan diskon minimal 50%.
2. Buka Registrasi Game Baru untuk memasukkan game yang sudah kamu punya: judul, harga beli, estimasi jam tamat, dan jam main saat ini. Tombol Berikan Opsi Gaya Main Otomatis mengambil estimasi dari HowLongToBeat.
3. Buka Koleksi dan Summary untuk melihat ringkasan backlog, lalu ubah jam main, ubah target estimasi, atau hapus game.
4. Sebelum membeli game baru, buka Evaluasi Pembelian. Isi judul, harga asli, diskon, dan estimasi jam, lalu tekan Jalankan Evaluasi Decision Engine untuk mendapat BUY atau WAIT.
5. Ubah batas toleransi kapan saja lewat Pengaturan Threshold. Tombol Logout ada di sidebar.

## Masalah umum

- `Error: Invalid value: File does not exist: app_web.py`: perintah dijalankan dari folder yang salah. Jalankan dari root repo dengan `streamlit run src/app_web.py`.
- `streamlit` tidak dikenali atau muncul `ModuleNotFoundError`: virtual environment belum aktif, atau `pip install` belum dijalankan.
- Aktivasi virtual environment diblokir di PowerShell: jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` di terminal yang sama, lalu aktifkan lagi.
- Muncul pesan Gagal ambil data estimasi otomatis: koneksi lambat atau HowLongToBeat diblokir jaringan. Isi estimasi jam secara manual.
- Port 8501 sedang dipakai: jalankan `streamlit run src/app_web.py --server.port 8502`.

## Roadmap

Ke depan, penyimpanan data akan dipindah ke database dan aplikasi Streamlit akan di-deploy.

## Batasan saat ini

- Login hanya memakai nama profile, jadi siapa pun yang tahu nama itu bisa membuka profile-nya.
- Data tersimpan di satu file JSON lokal, sehingga belum cocok untuk banyak pengguna di server publik.
- Estimasi dari HowLongToBeat butuh koneksi dan bisa diblokir oleh jaringan tertentu.
