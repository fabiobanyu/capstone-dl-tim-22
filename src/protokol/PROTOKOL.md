# Rancangan protokol evaluasi — Tim 22

**Status: DRAF, belum dibekukan dan belum disetujui pembimbing.** Lengkapi bersama
Penjaga Data & Evaluasi dan pembimbing; jangan melaporkan angka sebelum data tersedia.

| Butir | Rancangan / ketentuan kasus |
|---|---|
| Kasus | Estimasi duty PWM kipas dari suara; regresi. |
| Data primer | Rekaman tim di meja uji, mikrofon 16 kHz. Tautan pada kartu kasus menunjuk ke [starter](https://github.com/sains-data/capstone-dl-2026-starter), bukan rekaman. Lokasi dan versi data: belum tersedia. |
| Rancangan perekaman | Kipas: 0, 32, 64, 96, 128, 160, 192, 224, 255; pompa: 0 dan 200; 15 ulangan; 20 detik per kondisi. |
| Label | Duty PWM kipas otomatis; usulan satuan target: persen = 100 × PWM / 255. Konfirmasi skala dan metadata dengan operator. PWM bukan pengukuran RPM. |
| Masukan | Audio 16 kHz; buang detik pertama tiap kondisi; potong 1 detik; log-mel 64 pita. Parameter STFT, hop, frekuensi mel, daya/log dan penanganan sisa rekaman: belum disepakati. |
| Pembagian | Kelompok sesi/blok/partisipan harus terpisah antar latih, validasi dan uji; GroupKFold sesuai kartu kasus. Jumlah fold, penetapan kelompok, porsi dan identitas grup: belum ditetapkan. Seed split starter 2026. |
| Normalisasi | Hitung parameter dari data latih saja pada setiap pembagian; gunakan parameter yang sama untuk validasi dan uji. Bentuk normalisasi belum ditetapkan. |
| Metrik | MAE dalam persen duty sebagai metrik utama; laporkan rerata ± simpangan baku dari tiga seed konfigurasi akhir, ukuran ONNX (KB) dan latensi (ms) di laptop meja. Evaluator regresi juga menghitung RMSE dan R². |
| Pembanding | MFCC rata-rata dan simpangan + Random Forest atau SVM; baseline ridge starter merupakan pemeriksaan jalur dan bukan pengganti pembanding yang diminta. |
| Anggaran | Pelatihan ≤ 20 menit per run di CPU laptop atau anggaran kasus yang disetujui pembimbing; catat durasi dan perangkat. |
| Data uji | Dievaluasi sekali oleh Penjaga Data pada sprint terakhir; data tim lain hanya untuk uji tambahan sesuai kartu kasus. |
| Manifest / data_hash | Belum tersedia. Cantumkan seluruh rekaman dan metadata yang dipakai, serta versi/sumber, setelah diperoleh; hash dihitung starter, bukan diisi manual. |

## Hal yang perlu diputuskan sebelum dibekukan

1. Kartu kasus mewajibkan GroupKFold, sedangkan `src/common/split.py` hanya
   menyediakan split indeks acak/kronologis dan tidak menerima grup. Minta arahan
   pembimbing tentang cara menggabungkan split grup dengan keharusan memakai
   `src.common.split` tanpa mengubah `src/common/`. Belum ada split yang sah dibuat.
2. Tentukan format dan nama berkas rekaman, label, ID sesi/blok/ulangan, serta cara
   penyaluran data ke anggota. Pastikan jumlah grup cukup dan kondisi tercakup.
3. Tetapkan fold dan pembagian latih/validasi/uji, parameter ekstraksi fitur,
   normalisasi, seed model, cara pengukuran latensi/ONNX, dan anggaran komputasi.
4. Setelah data dan protokol tersedia, implementasikan `data.py`, isi manifest,
   jalankan baseline starter serta pembanding MFCC yang diwajibkan secara terpisah,
   dan cantumkan hash serta hasil yang benar-benar diperoleh.

Persetujuan pembimbing dan tautan PR: **belum ada**.
