# Protokol Evaluasi Tim 22

**Status: Menggunakan data primer meja uji (`sesi-20261117-220432`, 17 Nov 2026); diajukan lewat Pull Request untuk persetujuan pembimbing.**

| Butir | Rancangan / ketentuan kasus |
|---|---|
| Kasus | Estimasi duty PWM kipas dari suara; regresi. |
| Data primer | Rekaman fisik tim di meja uji Ruang Cerdas 5 V (`data/sesi-20261117-220432/`), mikrofon mono laju asli 48 kHz dalam potongan kontinu 60 detik (`audio-0001.wav` s.d. `audio-0100.wav`), dipetakan ke tiap kondisi lewat `label.csv` dan `audio_index.csv`. |
| Rancangan perekaman | Kipas: 0, 32, 64, 96, 128, 160, 192, 224, 255; pompa: 0 dan 200; 15 ulangan (`ulangan 1` s.d. `15`); 20 detik per kondisi dengan jeda 2 detik antar kondisi (total 270 kondisi lengkap). |
| Label | Target kontinu taraf PWM kipas dalam rentang `0.0` s.d. `255.0`: `y = kipas` (0, 32, 64, 96, 128, 160, 192, 224, 255). Rentang 0 s.d. 255 disepakati untuk seluruh model tim (CNN, TL, Transformer, Autoencoder). PWM bukan pengukuran RPM. |
| Masukan | Potongan audio kondisi di-resample dari 48 kHz ke 16 kHz; buang 1 detik pertama tiap kondisi (transien akselerasi); potong sisa menjadi segmen utuh @ 1 detik tanpa tumpang tindih (16.000 sampel/segmen), sisa sampel < 1 detik di akhir rekaman dibuang (menghasilkan 18 atau 19 segmen per kondisi, total 5.067 segmen). Ekstraksi log-mel 64 pita (`n_mels=64`, `n_fft=1024`, `hop_length=512`, skala dB terhadap daya maksimum per segmen). |
| Pembagian | Pemisahan wajib per ulangan (`1` s.d. `15`). Ulangan 13 s.d. 15 (3 ulangan, 54 kondisi, 1.018 segmen) dikunci sebagai data uji. Ulangan 1 s.d. 12 (12 ulangan, 216 kondisi) dibagi menjadi latih dan validasi dengan memanggil `src.common.split.indeks(12)` (seed 2026, `porsi_val=0.1` menghasilkan 11 ulangan latih / 3.711 segmen dan 1 ulangan validasi `ulangan 7` / 338 segmen), lalu diverifikasi bebas irisan dengan `assert`. |
| Normalisasi | Standarisasi z-score per pita frekuensi mel (`mean` dan `std` dihitung pada sumbu sampel dan frame waktu dari `X_train` saja). Parameter `mean` dan `std` dari `X_train` dipakai untuk menormalisasi `X_train`, `X_val`, dan `X_test`. |
| Metrik | Evaluator menghitung MAE, RMSE, dan R² pada skala PWM (0 s.d. 255). Sesuai kartu kasus yang meminta MAE dalam persen duty, hasil MAE untuk laporan dikonversi dengan rumus `MAE persen = MAE PWM / 255 * 100`. Laporkan rerata ± simpangan baku dari tiga seed konfigurasi akhir, ukuran ONNX (KB), dan latensi (ms) di laptop meja. |
| Pembanding | MFCC rata-rata dan simpangan + Random Forest atau SVM; baseline ridge starter merupakan pemeriksaan jalur (`val_mae = 15.024312`, `val_rmse = 18.903305`, `val_r2 = 0.947384`) dan bukan pengganti pembanding yang diminta. |
| Anggaran | Pelatihan <= 20 menit per run di CPU laptop atau anggaran kasus yang disetujui pembimbing; catat durasi dan perangkat. |
| Data uji | Dievaluasi sekali oleh Penjaga Data pada sprint terakhir; data tim lain hanya untuk uji tambahan sesuai kartu kasus. |
| Manifest / data_hash | Menggunakan `data/MANIFEST.json` dari starter. Mencantumkan seluruh 110 berkas data sesi primer `data/sesi-20261117-220432/` sehingga sidik data (`data_hash`) konsisten untuk semua anggota tim (`c70ef6fa3c33a2da1ff7d7050f56af9b` pada evaluator). |

## Keputusan teknis yang diterapkan pada `src/protokol/data.py`

1. **Kompatibilitas Group Split dengan `src.common.split`:** Tanpa mengubah `src/common/split.py`, fungsi `split.indeks()` dipanggil pada array daftar nomor ulangan non-uji (12 grup), bukan pada indeks baris segmen. Hasil indeks grup tersebut memetakan ulangan mana yang masuk ke latih dan validasi, sehingga aturan `src.common.split` (seed 2026) dan aturan anti-bocor antar ulangan terpenuhi sekaligus.
2. **Pemotongan rekaman kontinu & kompatibilitas metadata:** Pada sesi asli, berkas audio berdurasi 60 detik per potongan (`audio-0001.wav` s.d. `audio-0100.wav`), sehingga kondisi dipotong berdasarkan interval `t_mulai_host` dan `t_selesai_host` di `label.csv` melalui indeks `audio_index.csv` dan di-resample dari 48 kHz ke 16 kHz (`resample_poly`). Jalur pencocokan satu berkas per kondisi (`_temukan_file_audio`) tetap dipertahankan untuk kompatibilitas mundur.
3. **Penyeragaman target regresi PWM 0 s.d. 255 dan konversi MAE persen:** Label target `y` diseragamkan pada rentang nilai PWM kipas `0.0` s.d. `255.0` untuk seluruh model tim. Untuk pelaporan akhir sesuai kartu kasus, nilai MAE dari skala PWM dikonversi ke persen duty dengan rumus `MAE persen = MAE PWM / 255 * 100`.
4. **Pemeriksaan anti-bocor otomatis:** Setiap pemanggilan `muat()` menjalankan pemeriksaan `set.isdisjoint` pada himpunan nomor ulangan latih, validasi, dan uji sebelum mengembalikan array.

Persetujuan pembimbing dan tautan PR: *diajukan pada PR ini*.
