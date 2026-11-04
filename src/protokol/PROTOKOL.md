# Rancangan protokol evaluasi — Tim 22

**Status: DRAF, diajukan lewat Pull Request untuk persetujuan pembimbing.** Dikembangkan menggunakan data simulasi (`meja.py --simulasi`); jangan melaporkan angka akhir sebelum data meja fisik tersedia (sekitar 7 Nov).

| Butir | Rancangan / ketentuan kasus |
|---|---|
| Kasus | Estimasi duty PWM kipas dari suara; regresi. |
| Data primer | Rekaman tim di meja uji, mikrofon mono 16 kHz di dalam `data/` (`audio/`). Tahap persiapan menggunakan sesi simulasi (`python meja.py --simulasi jalankan ../rencana/t22-kecepatan-kipas-suara.yaml`). |
| Rancangan perekaman | Kipas: 0, 32, 64, 96, 128, 160, 192, 224, 255; pompa: 0 dan 200; 15 ulangan (`Rep 1` s.d. `Rep 15`); 20 detik per kondisi (total 270 rekaman). |
| Label | Duty PWM kipas otomatis dalam satuan persen: `y = 100.0 * PWM_Kipas / 255.0` (rentang `0.0` s.d. `100.0`, sesuai kolom `Duty_Persen`). PWM bukan pengukuran RPM. |
| Masukan | Audio 16 kHz; buang 1 detik pertama tiap kondisi (transien); potong sisa 19 detik menjadi 19 segmen @ 1 detik tanpa tumpang tindih (16.000 sampel/segmen). Ekstraksi log-mel 64 pita (`n_mels=64`, `n_fft=1024`, `hop_length=512`, skala dB terhadap daya maksimum per segmen). Sisa sampel < 1 detik di akhir rekaman dibuang. |
| Pembagian | Pemisahan wajib per ulangan (`Rep 1` s.d. `Rep 15`). Ulangan 13–15 (3 ulangan, 54 rekaman, 1.026 segmen) dikunci sebagai data uji. Ulangan 1–12 (12 ulangan, 216 rekaman) dibagi menjadi latih dan validasi dengan memanggil `src.common.split.indeks(12)` (seed 2026, `porsi_val=0.1` -> 11 ulangan latih / 3.762 segmen dan 1 ulangan validasi `Rep 7` / 342 segmen), lalu diverifikasi bebas irisan dengan `assert`. |
| Normalisasi | Standarisasi z-score per pita frekuensi mel (`mean` dan `std` dihitung pada sumbu sampel dan frame waktu dari `X_train` saja). Parameter `mean` dan `std` dari `X_train` dipakai untuk menormalisasi `X_train`, `X_val`, dan `X_test`. |
| Metrik | MAE dalam persen duty sebagai metrik utama; laporkan rerata ± simpangan baku dari tiga seed konfigurasi akhir, ukuran ONNX (KB) dan latensi (ms) di laptop meja. Evaluator regresi juga menghitung RMSE dan R². |
| Pembanding | MFCC rata-rata dan simpangan + Random Forest atau SVM; baseline ridge starter merupakan pemeriksaan jalur dan bukan pengganti pembanding yang diminta. |
| Anggaran | Pelatihan ≤ 20 menit per run di CPU laptop atau anggaran kasus yang disetujui pembimbing; catat durasi dan perangkat. |
| Data uji | Dievaluasi sekali oleh Penjaga Data pada sprint terakhir; data tim lain hanya untuk uji tambahan sesuai kartu kasus. |
| Manifest / data_hash | Menggunakan `data/MANIFEST.json` dari starter. Diperbarui ulang saat data meja fisik masuk. |

## Keputusan teknis yang diterapkan pada `src/protokol/data.py`

1. **Kompatibilitas Group Split dengan `src.common.split`:** Tanpa mengubah `src/common/split.py`, fungsi `split.indeks()` dipanggil pada array daftar nomor ulangan non-uji (12 grup), bukan pada indeks baris segmen. Hasil indeks grup tersebut memetakan ulangan mana yang masuk ke latih dan validasi, sehingga aturan `src.common.split` (seed 2026) dan aturan anti-bocor antar ulangan terpenuhi sekaligus.
2. **Format berkas dan metadata:** Mengacu pada `LEMBAR_SESI_TIM_22.csv` (270 baris) dan keluaran `meja.py --simulasi`, pembaca data mengenali kolom `Ulangan`, `PWM_Kipas` / `Duty_Persen`, serta mencocokkan berkas `.wav` di subfolder `audio/`.
3. **Pemeriksaan anti-bocor otomatis:** Setiap pemanggilan `muat()` menjalankan pemeriksaan `set.isdisjoint` pada himpunan nomor ulangan latih, validasi, dan uji sebelum mengembalikan array.

Persetujuan pembimbing dan tautan PR: *diajukan pada PR ini*.