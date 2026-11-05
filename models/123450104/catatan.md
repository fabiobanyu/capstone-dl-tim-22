# Catatan model CNN — Fabio (123450104)

## Status

Kerangka CNN menggunakan target rasio 0–1 sesuai kartu kasus. Pemuat data tim di main masih menggunakan persen 0–100, sehingga belum kompatibel dan perlu diselaraskan oleh tim sebelum pengujian bersama. Belum ada hasil data rekaman asli.

## Masukan dan Keluaran

- **Masukan**: Log-mel 64 pita, 1 detik (bentuk `[N, 1, 64, waktu]`, `waktu >= 4`).
- **Keluaran**: Rasio duty kontinu 0–1. MAE pada skala ini dikalikan 100 untuk dilaporkan dalam persen duty.
- **Normalisasi**: Dilakukan sekali oleh pemuat data tim berdasarkan statistik data latih; CNN tidak mengulang normalisasi.

## Arsitektur & Keputusan Desain

1. **Feature Extractor**:
   - Conv2d(1 -> 16, kernel 3x3, pad 1) + ReLU + MaxPool2d(2)
   - Conv2d(16 -> 32, kernel 3x3, pad 1) + ReLU + MaxPool2d(2)
   - Conv2d(32 -> 64, kernel 3x3, pad 1) + ReLU
   - AdaptiveAvgPool2d((1, 1))
2. **Regressor Head**:
   - Flatten + Dropout(p=0.2)
   - Linear(64 -> 1) + Sigmoid (rasio 0–1)
3. **Optimizer**: Adam dengan learning rate 0.001 dan weight decay 0.0001 (L2 regularization).
4. **Fungsi Rugi**: Mean Squared Error (MSE Loss) untuk pelatihan regresi kontinu. Metrik evaluasi utama: Mean Absolute Error (MAE dalam % duty).

## Catatan hasil simulasi sebelumnya (belum terverifikasi ulang)

Catatan versi sebelumnya mencantumkan data simulasi 270 kondisi. File metrik dan data yang mendasari angka ini belum tersedia untuk diperiksa di laptop ini; hasil berikut bukan hasil model yang baru disesuaikan:
- **Jumlah sampel**: 5.130 jendela (latih: 4.617, validasi: 513)
- **Epoch**: 10
- **Durasi komputasi**: 20.5 detik (CPU laptop)
- **Metrik Validasi**:
  - MAE: **2.8642%** duty
  - RMSE: **3.2796%** duty
- **Keluaran**: Valid 1D array (`shape = (513,)`) tanpa nilai NaN/Inf.

Evaluator starter menulis `val_mae` dalam satuan yang sama dengan label (rasio 0–1). Untuk MAE persen duty, kalikan `val_mae` dengan 100; jangan menyunting `metrics.json` secara manual.

## Rencana Lanjutan (Sprint 1)

1. Menguji variasi arsitektur (Ablation 1: tanpa Dropout, Ablation 2: penambahan filter / layer konvolusi).
2. Melatih pada data primer rekaman meja setelah data tersedia dari sesi 5 Nov.
3. Menjalankan 3 seed (seed 1, 2, 3) dan mencatat tabel komparasi serta variansi MAE.
4. Mengekspor model ke format ONNX dan mengukur ukuran model (KB) serta latensi inferensi (ms).
