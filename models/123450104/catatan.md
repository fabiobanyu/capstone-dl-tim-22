# Catatan model CNN — Fabio (123450104)

## Status

Kerangka CNN memakai label dan prediksi PWM 0–255 sesuai rancangan tim. Pemuat data PR #15 sudah digabung dan menggunakan skala yang sama. CNN telah diuji dengan data simulasi; belum ada hasil data rekaman asli.

## Masukan dan Keluaran

- **Masukan**: Log-mel 64 pita, 1 detik (bentuk `[N, 1, 64, waktu]`, `waktu >= 4`).
- **Keluaran**: PWM kontinu 0–255. MAE dalam skala ini dikalikan 100/255 untuk dilaporkan dalam persen duty.
- **Normalisasi**: Dilakukan sekali oleh pemuat data tim berdasarkan statistik data latih; CNN tidak mengulang normalisasi.

## Arsitektur & Keputusan Desain

1. **Feature Extractor**:
   - Conv2d(1 -> 16, kernel 3x3, pad 1) + ReLU + MaxPool2d(2)
   - Conv2d(16 -> 32, kernel 3x3, pad 1) + ReLU + MaxPool2d(2)
   - Conv2d(32 -> 64, kernel 3x3, pad 1) + ReLU
   - AdaptiveAvgPool2d((1, 1))
2. **Regressor Head**:
   - Flatten + Dropout(p=0.2)
   - Linear(64 -> 1) + Sigmoid (rasio 0–1), dikalikan 255 saat prediksi
3. **Optimizer**: Adam dengan learning rate 0.001 dan weight decay 0.0001 (L2 regularization).
4. **Fungsi Rugi**: Mean Squared Error (MSE Loss), memakai target dibagi 255 selama pelatihan. Prediksi untuk evaluator dikembalikan ke 0–255. Metrik utama: MAE dalam % duty.

## Hasil simulasi terbaru (seed 1)

- Data: simulasi 270 kondisi dari `meja.py`, kode main `29f8fe3`, hash evaluator `a8922184f4e06b82ad3c1125e53e4506`.
- Validasi: 342 segmen; data uji tidak digunakan. Durasi pelatihan dan pemuatan: 32,6 detik pada CPU.
- CNN: MAE 6,681280 PWM = 2,6201% duty; RMSE 8,492593 PWM; R² 0,989391.
- Baseline ridge, diuji ulang pada simulasi dan split yang sama: MAE 11,287073 PWM = 4,4263% duty. Baseline ini bukan pembanding MFCC + Random Forest/SVM yang diwajibkan.
- Angka di atas hanya pengujian simulasi, belum membuktikan performa pada rekaman fisik.

## Catatan hasil simulasi sebelumnya (belum terverifikasi ulang)

Catatan versi sebelumnya mencantumkan data simulasi 270 kondisi. File metrik dan data yang mendasari angka ini belum tersedia untuk diperiksa di laptop ini; hasil berikut bukan hasil model yang baru disesuaikan:
- **Jumlah sampel**: 5.130 jendela (latih: 4.617, validasi: 513)
- **Epoch**: 10
- **Durasi komputasi**: 20.5 detik (CPU laptop)
- **Metrik Validasi**:
  - MAE: **2.8642%** duty
  - RMSE: **3.2796%** duty
- **Keluaran**: Valid 1D array (`shape = (513,)`) tanpa nilai NaN/Inf.

Evaluator starter menulis `val_mae` dalam satuan yang sama dengan label (PWM 0–255). Untuk MAE persen duty, kalikan `val_mae` dengan 100/255; jangan menyunting `metrics.json` secara manual.

## Rencana Lanjutan (Sprint 1)

1. Menguji variasi arsitektur (Ablation 1: tanpa Dropout, Ablation 2: penambahan filter / layer konvolusi).
2. Melatih pada data primer rekaman meja setelah data tersedia dari sesi 5 Nov.
3. Menjalankan 3 seed (seed 1, 2, 3) dan mencatat tabel komparasi serta variansi MAE.
4. Mengekspor model ke format ONNX dan mengukur ukuran model (KB) serta latensi inferensi (ms).
