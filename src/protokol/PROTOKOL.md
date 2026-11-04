# Rancangan protokol evaluasi — Tim 22

**Status: DRAF, diajukan lewat Pull Request untuk persetujuan pembimbing.** Dikembangkan menggunakan data simulasi (`meja.py --simulasi`); jangan melaporkan angka akhir sebelum data meja fisik tersedia (sekitar 7 Nov).

| Butir | Rancangan / ketentuan kasus |
|---|---|
| Kasus | Estimasi duty PWM kipas dari suara; regresi. |
| Data primer | Rekaman tim di meja uji, mikrofon mono 16 kHz di dalam `data/` (`audio/`). Tahap persiapan menggunakan sesi simulasi (`python meja.py --simulasi jalankan ../rencana/t22-kecepatan-kipas-suara.yaml`). |
| Rancangan perekaman | Kipas: 0, 32, 64, 96, 128, 160, 192, 224, 255; pompa: 0 dan 200; 15 ulangan (`Rep 1` s.d. `Rep 15`); 20 detik per kondisi (total 270 rekaman). |
| Label | Target kontinu taraf PWM kipas otomatis dalam rentang `0.0` s.d. `255.0`: `y = PWM_Kipas` (0, 32, 64, 96, 128, 160, 192, 224, 255). Rentang 0–255 disepakati untuk seluruh model tim (CNN, TL, Transformer, Autoencoder). PWM bukan pengukuran RPM. |
| Masukan | Audio 16 kHz; buang 1 detik pertama tiap kondisi (transien akselerasi); potong sisa 19 detik menjadi 19 segmen @ 1 detik tanpa tumpang tindih (16.000 sampel/segmen). Ekstraksi log-mel 64 pita (`n_mels=64`, `n_fft=1024`, `hop_length=512`, skala dB terhadap daya maksimum per segmen). Sisa sampel < 1 detik di akhir rekaman dibuang. |
| Pembagian | Pemisahan wajib per ulangan (`Rep 1` s.d. `Rep 15`). Ulangan 13–15 (3 ulangan, 54 rekaman, 1.026 segmen) dikunci sebagai data uji. Ulangan 1–12 (12 ulangan, 216 rekaman) dibagi menjadi latih dan validasi dengan memanggil `src.common.split.indeks(12)` (seed 2026, `porsi_val=0.1` -> 11 ulangan latih / 3.762 segmen dan 1 ulangan validasi `Rep 7` / 342 segmen), lalu diverifikasi bebas irisan dengan `assert`. |
| Normalisasi | Standarisasi z-score per pita frekuensi mel (`mean` dan `std` dihitung pada sumbu sampel dan frame waktu dari `X_train` saja). Parameter `mean` dan `std` dari `X_train` dipakai untuk menormalisasi `X_train`, `X_val`, dan `X_test`. |
| Metrik | MAE dalam satuan taraf PWM (rentang 0–255) sebagai metrik utama; laporkan rerata ± simpangan baku dari tiga seed konfigurasi akhir, ukuran ONNX (KB) dan latensi (ms) di laptop meja. Evaluator regresi juga menghitung RMSE dan R². |
| Pembanding | MFCC rata-rata dan simpangan + Random Forest atau SVM; baseline ridge starter merupakan pemeriksaan jalur dan bukan pengganti pembanding yang diminta. |
| Anggaran | Pelatihan ≤ 20 menit per run di CPU laptop atau anggaran kasus yang disetujui pembimbing; catat durasi dan perangkat. |
| Data uji | Dievaluasi sekali oleh Penjaga Data pada sprint terakhir; data tim lain hanya untuk uji tambahan sesuai kartu kasus. |
| Manifest / data_hash | Menggunakan `data/MANIFEST.json` dari starter. Mencantumkan seluruh berkas data dan rekaman audio yang dipakai sehingga sidik data (`data_hash`) konsisten untuk semua anggota tim. |

## Keputusan teknis yang diterapkan pada `src/protokol/data.py`

1. **Kompatibilitas Group Split dengan `src.common.split`:** Tanpa mengubah `src/common/split.py`, fungsi `split.indeks()` dipanggil pada array daftar nomor ulangan non-uji (12 grup), bukan pada indeks baris segmen. Hasil indeks grup tersebut memetakan ulangan mana yang masuk ke latih dan validasi, sehingga aturan `src.common.split` (seed 2026) dan aturan anti-bocor antar ulangan terpenuhi sekaligus.
2. **Pencocokan berkas audio via metadata:** Berkas audio tidak dipasangkan berdasarkan urutan indeks semata, melainkan dicocokkan secara deterministik menggunakan kolom `file_audio`, atau nomor kondisi `No` (`kondisi_NNN.wav`), atau `Kondisi_ID` pada metadata lembar sesi.
3. **Penyeragaman target regresi PWM 0–255:** Label target `y` diseragamkan pada rentang nilai PWM kipas `0.0` s.d. `255.0` agar selaras dengan arsitektur regresi seluruh tim (termasuk kepala regresi Autoencoder Rahmah yang membatasi rentang ke 0–255) dan metrik evaluasi MAE bernilai konsisten.
4. **Pemeriksaan anti-bocor otomatis:** Setiap pemanggilan `muat()` menjalankan pemeriksaan `set.isdisjoint` pada himpunan nomor ulangan latih, validasi, dan uji sebelum mengembalikan array.

Persetujuan pembimbing dan tautan PR: *diajukan pada PR ini*.
