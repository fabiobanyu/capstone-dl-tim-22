# Catatan model CNN — Fabio (123450104)

## Status

Kerangka model `run.py` telah selesai diimplementasikan dan diverifikasi berjalan sukses pada data simulasi 1-detik log-mel (5.130 sampel). Saat ini menunggu data rekaman primer meja uji (jadwal 5-7 Nov) dan implementasi data loader tim oleh Penjaga Data.

## Masukan dan Keluaran

- **Masukan**: Log-mel 64 pita, 1 detik (bentuk `[N, 1, 64, waktu]`, `waktu >= 4`).
- **Keluaran**: Nilai kontinu duty PWM dalam rentang persen (0–100%).
- **Normalisasi**: Per-pita (mean dan std dihitung khusus dari subset data latih untuk mencegah data leakage).

## Arsitektur & Keputusan Desain

1. **Feature Extractor**:
   - Conv2d(1 -> 16, kernel 3x3, pad 1) + ReLU + MaxPool2d(2)
   - Conv2d(16 -> 32, kernel 3x3, pad 1) + ReLU + MaxPool2d(2)
   - Conv2d(32 -> 64, kernel 3x3, pad 1) + ReLU
   - AdaptiveAvgPool2d((1, 1))
2. **Regressor Head**:
   - Flatten + Dropout(p=0.2)
   - Linear(64 -> 1)
3. **Optimizer**: Adam dengan learning rate 0.001 dan weight decay 0.0001 (L2 regularization).
4. **Fungsi Rugi**: Mean Squared Error (MSE Loss) untuk pelatihan regresi kontinu. Metrik evaluasi utama: Mean Absolute Error (MAE dalam % duty).

## Hasil Pengujian pada Data Simulasi (Seed 1)

Verifikasi end-to-end dilakukan menggunakan generator data simulasi 270 kondisi (9 level PWM x 2 level pompa x 15 ulangan):
- **Jumlah sampel**: 5.130 jendela (latih: 4.617, validasi: 513)
- **Epoch**: 10
- **Durasi komputasi**: 20.5 detik (CPU laptop)
- **Metrik Validasi**:
  - MAE: **2.8642%** duty
  - RMSE: **3.2796%** duty
- **Keluaran**: Valid 1D array (`shape = (513,)`) tanpa nilai NaN/Inf.

## Rencana Lanjutan (Sprint 1)

1. Menguji variasi arsitektur (Ablation 1: tanpa Dropout, Ablation 2: penambahan filter / layer konvolusi).
2. Melatih pada data primer rekaman meja setelah data tersedia dari sesi 5 Nov.
3. Menjalankan 3 seed (seed 1, 2, 3) dan mencatat tabel komparasi serta variansi MAE.
4. Mengekspor model ke format ONNX dan mengukur ukuran model (KB) serta latensi inferensi (ms).
