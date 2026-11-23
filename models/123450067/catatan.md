# Catatan model 123450067

## Alasan optimizer

Model memakai **AdamW** dengan laju pembelajaran bertingkat (*discriminative learning rates*): `1e-3` pada lapisan adaptor (`Conv2d(1 -> 3)` + `BatchNorm2d`) dan kepala regresi, serta `5e-4` pada *backbone* `MobileNetV3-Small` saat tahap *fine-tuning*, dipadukan dengan penjadwalan `CosineAnnealingLR`.

1. **Decoupled Weight Decay (`1e-4`):** AdamW memisahkan penalti peluruhan bobot dari pembaruan momentum adaptif sehingga bobot pralatih ImageNet tidak cepat rusak saat menyesuaikan diri ke domain spektrogram suara kipas.
2. **Pelatihan dua tahap:** 2 *epoch* pertama hanya melatih adaptor dan kepala regresi (*backbone* dibekukan, `features.eval()` agar statistik BatchNorm pralatih tidak bergeser), lalu dilanjutkan 8 *epoch* *fine-tuning* penuh.

## Regularisasi

- **Dropout (`0.2`):** Diletakkan sebelum lapisan keluaran regresi (`Linear(128, 1)`) agar kepala regresi tidak bergantung pada fitur laten tunggal.
- **Weight Decay (`1e-4`):** Diterapkan lewat AdamW pada seluruh parameter model.
- **Gradient Clipping (`max_norm=1.0`):** Menjaga kestabilan pembaruan gradien selama fase *fine-tuning*.
- **Standardisasi target sementara:** Target PWM `0.0` s.d. `255.0` distandarkan memakai `mean` dan `std` data latih selama perhitungan *loss* MSE, lalu dikembalikan ke skala PWM dan dibatasi ke `[0.0, 255.0]` saat inferensi.

## Pencarian hyperparameter (data simulasi)

Seluruh uji coba di bawah ini dijalankan pada data simulasi 270 kondisi (`data_hash: a8922184f4e06b82ad3c1125e53e4506`, `n_train=3762`, `n_val=342`, `batch_size=32`, CPU laptop). Angka masih bersifat sementara hingga data rekaman fisik meja uji tersedia.

| ID | Backbone & Input | Strategi Pembekuan | Epoch | LR (Head / Backbone) | Val MAE (PWM / % duty) | Val RMSE | Val R² | Durasi (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SIM-01 | MobileNetV3-Small (`64x30`) | Frozen penuh | 10 | `1e-3` / - | `32.9950` (`12.94%`) | `43.9424` | `0.71597` | `51.3` |
| SIM-02 | MobileNetV3-Small (`64x30`) | Unfreeze 3 blok akhir | 10 | `1e-3` / `1e-4` | `22.5021` (`8.82%`) | `30.8713` | `0.85981` | `83.7` |
| SIM-03 | MobileNetV3-Small (`64x30`) | Unfreeze penuh | 10 | `1e-3` / `1e-4` | `13.0413` (`5.11%`) | `17.7658` | `0.95357` | `147.4` |
| SIM-04 | MobileNetV3-Small (`96x96`) | Unfreeze 3 blok akhir | 10 | `1e-3` / `1e-4` | `11.0899` (`4.35%`) | `15.2473` | `0.96580` | `104.5` |
| SIM-05 | MobileNetV3-Small (`96x96`) | Unfreeze penuh | 12 | `1e-3` / `5e-4` | `2.7454` (`1.08%`) | `3.9694` | `0.99768` | `289.2` |
| **SIM-06** | **MobileNetV3-Small (`96x96` + Adaptor `1->3`)** | **Warmup 2 + Fine-tune 8** | **10** | **`1e-3` / `5e-4`** | **`1.9434` (`0.76%`)** | **`2.8087`** | **`0.99884`** | **`251.9`** |

## Ablation (>= 2)

1. **Ablasi 1: Derajat *unfreezing* pada *backbone* pralatih (`SIM-01` vs `SIM-02` vs `SIM-03` pada input `64x30`)**
   - Membuka gradien seluruh *backbone* menurunkan `val_mae` dari `32.9950` (beku penuh) dan `22.5021` (3 blok akhir) menjadi `13.0413`. Fitur citra ImageNet perlu adaptasi bobot agar peka terhadap pola harmonik spektrogram suara kipas.
2. **Ablasi 2: Resolusi masukan & adaptor kanal (`SIM-02` vs `SIM-04`, serta `SIM-05` vs `SIM-06`)**
   - *MobileNetV3-Small* memiliki total *stride* 32 sehingga input `64x30` tereduksi menjadi `2x1` sebelum *pooling*. Mengubah ukuran spasial ke `(96, 96)` menurunkan `val_mae` parsial dari `22.5021` menjadi `11.0899`.
   - Penambahan adaptor `Conv2d(1, 3) + BatchNorm2d` beserta 2 *epoch* *warmup* sebelum *fine-tuning* menurunkan `val_mae` lebih lanjut menjadi `1.9434` (`0.76%` *duty*) dalam waktu 251.9 detik.

## Hasil 3 seed konfigurasi akhir

Pada data simulasi saat ini baru dijalankan `seed 1` (`val_mae = 1.943447`, `val_rmse = 2.808664`, `val_r2 = 0.99884`, `durasi_detik = 251.9`). Pengujian 3 seed (`--seed 1 2 3`), pengukuran ukuran ONNX, serta latensi inferensi akan diisi setelah data rekaman fisik meja uji tersedia.

| Random Seed | Val MAE (PWM) | Val MAE (% duty) | Val RMSE | Val R² | Durasi (s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Seed 1 (Simulasi) | `1.943447` | `0.76%` | `2.808664` | `0.99884` | `251.9` |
| Seed 2 | *Menunggu data meja* | - | - | - | - |
| Seed 3 | *Menunggu data meja* | - | - | - | - |
| **Rata-rata ± Std** | **-** | **-** | **-** | **-** | **-** |