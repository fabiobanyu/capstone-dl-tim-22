# Catatan model 123450086 — Transformer encoder atas patch

## Status

Kerangka `run.py` (tugas #15) sudah ditulis. Menunggu data simulasi lewat `src/protokol/data.py`
(tugas #4, Penjaga Data) untuk diuji pada data tim. Belum ada angka hasil pada data tim.

## Arsitektur awal

- Masukan: log-mel 64 pita, 1 detik, bentuk `[N, 64, waktu]` atau `[N, 1, 64, waktu]`.
- Normalisasi per pita mel; mean dan std dihitung dari data latih saja.
- Patch 8 x 8 (pita x frame) -> patch embedding (Conv2d kernel = stride = ukuran patch) ke d_model 64.
- Token [CLS] + positional embedding terpisah untuk sumbu frekuensi dan waktu.
- Transformer encoder 2 lapis, 4 head, feed-forward 128, dropout 0.1, pre-norm.
- Kepala regresi: LayerNorm + Linear dari token [CLS] -> 1 angka duty.
- Target distandarkan (mean/std data latih), prediksi dikembalikan ke satuan semula lalu dipotong ke rentang label latih.
- Sekitar 73 ribu parameter (perkiraan ~0,3 MB float32), sengaja kecil karena ukuran ONNX dan latensi ikut dinilai.

## Alasan optimizer

AdamW (lr 1e-3, weight decay 0,01) dengan jadwal cosine dan gradient clipping 1,0.
AdamW umum dipakai untuk Transformer; weight decay terpisah dari gradien membantu regularisasi,
dan clipping menjaga pelatihan tetap stabil di awal.

## Regularisasi

Dropout 0,1 di encoder, weight decay 0,01. Rencana: SpecAugment (masking frekuensi/waktu) bila model overfit.

## Pencarian hyperparameter (tabel)

| Konfigurasi | Patch | Lapis | d_model | MAE val (% duty) | Catatan |
|---|---|---|---|---|---|
| awal | 8x8 | 2 | 64 | — | menunggu data tim |

## Ablation (>= 2)

Rencana:
1. Ukuran/bentuk patch: 8x8 vs 16x16 vs patch per frame waktu (64x2).
2. Tanpa positional embedding frekuensi (apakah posisi frekuensi penting untuk nada kipas).

## Hasil 3 seed konfigurasi akhir

Belum ada.
