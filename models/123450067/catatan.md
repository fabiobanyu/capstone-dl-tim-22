# Catatan model 123450067

## Alasan optimizer

Optimizer utama yang dipilih untuk jalur *transfer learning* ini adalah **AdamW** (*learning rate* awal $1 \times 10^{-3}$ pada *regression head* dan $1 \times 10^{-4}$ hingga $1 \times 10^{-5}$ pada lapisan *backbone* saat *unfreezing*):
1. **Decoupled Weight Decay:** Berbeda dengan Adam standar yang menerapkan penalti $L_2$ langsung pada perhitungan gradien momentum, AdamW memisahkan peluruhan bobot (*weight decay*) dari pembaruan adaptif. Hal ini krusial untuk mencegah bobot fitur representasi awal (*pretrained weights*) rusak secara drastis (*catastrophic forgetting*) saat beradaptasi ke domain spektrogram audio kipas.
2. **Konvergensi Cepat dengan Laju Bertingkat (*Discriminative Learning Rates*):** Karena tugas regresi PWM menuntut pemetaan nilai kontinu yang presisi dari fitur frekuensi tinggi, optimizer adaptif berbasis momen orde pertama dan kedua mempercepat konvergensi pada kepala regresi baru tanpa memerlukan *tuning schedule* manual yang rumit pada tahap awal.

## Regularisasi

Untuk menahan risiko *overfitting* pada rekaman audio durasi 1 detik dan menjaga model tetap ringan saat diekspor ke ONNX, skema regularisasi yang dirancang meliputi:
- **Dropout (0.2 – 0.3):** Diletakkan di antara lapisan *linear/dense* pada *regression head* sebelum pemetaan akhir ke 1 nilai kontinu untuk mencegah dependensi berlebih pada unit laten tertentu.
- **Weight Decay ($1 \times 10^{-4}$):** Diintegrasikan melalui AdamW untuk membatasi magnitudo bobot dan menstabilkan generalisasi pada data validasi *GroupKFold*.
- **SpecAugment Sederhana (Time & Frequency Masking):** Masking acak pada 1–2 pita frekuensi dan beberapa *time-step* spektrogram selama pelatihan agar model tidak hanya mengandalkan harmonik bunyi pada frekuensi tertentu.
- **Early Stopping:** Pemantauan metrik validasi MAE dengan *patience* 7–10 *epoch* untuk menghentikan pelatihan sebelum model menghafal karakteristik kebisingan latar (*background noise*) sesi tertentu.

## Pencarian hyperparameter (tabel)

Eksplorasi *hyperparameter* dirancang untuk membandingkan kapasitas *backbone*, laju pembelajaran, dan tingkat regularisasi terhadap metrik target tim (MAE % *duty* dan latensi inferensi):

| Eksperimen ID | Arsitektur Backbone | Strategi Pembekuan | Learning Rate (Head / Backbone) | Dropout | Batch Size | MAE Validasi (% duty) | Latensi ONNX (ms) | Ukuran ONNX (KB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| EXP-01 | MobileNetV3-Small | Frozen (Feature Extractor) | $1 \times 10^{-3}$ / - | 0.2 | 32 | *Menunggu data* | *Uji meja* | *Uji meja* |
| EXP-02 | MobileNetV3-Small | Unfreeze 2 Blok Akhir | $1 \times 10^{-3}$ / $1 \times 10^{-4}$ | 0.2 | 32 | *Menunggu data* | *Uji meja* | *Uji meja* |
| EXP-03 | MobileNetV3-Small | Unfreeze Penuh (*Fine-tune*) | $5 \times 10^{-4}$ / $5 \times 10^{-5}$ | 0.3 | 32 | *Menunggu data* | *Uji meja* | *Uji meja* |
| EXP-04 | ResNet-18 | Frozen (Feature Extractor) | $1 \times 10^{-3}$ / - | 0.2 | 32 | *Menunggu data* | *Uji meja* | *Uji meja* |
| EXP-05 | ResNet-18 | Unfreeze Layer 4 | $1 \times 10^{-3}$ / $1 \times 10^{-4}$ | 0.2 | 16 | *Menunggu data* | *Uji meja* | *Uji meja* |

> *Catatan: Nilai metrik dan latensi akan diisi secara berkala selama Sprint 1 dan Sprint 2 setelah data rekaman meja uji 5–6 November 2026 tersedia.*

## Ablation (>= 2)

Dua studi ablasi utama yang disiapkan untuk mengisolasi kontribusi komponen arsitektur terhadap performa regresi:

1. **Ablasi 1: Pengaruh Derajat Unfreezing Backbone Pretrained**
   - *Variasi A (Frozen Feature Extractor):* Seluruh bobot *backbone* dibekukan; hanya *regression head* yang dilatih dari nol.
   - *Variasi B (Partial Unfreezing):* Membuka gradien pada 1–2 blok residual/konvolusi teratas dari *backbone* untuk menyesuaikan representasi fitur spesifik akustik kipas.
   - *Tujuan:* Menguji apakah representasi bawaan (*ImageNet/Audio*) sudah cukup memadai untuk membedakan level PWM atau membutuhkan adaptasi fitur spasial spektrogram secara parsial.

2. **Ablasi 2: Dampak Regularisasi Kombinasi (Dropout vs SpecAugment)**
   - *Variasi A (Baseline Head):* Regression head tanpa Dropout dan tanpa SpecAugment pada input log-mel.
   - *Variasi B (Dropout Only):* Penambahan Dropout 0.2 pada regression head.
   - *Variasi C (Dropout + SpecAugment):* Penambahan Dropout 0.2 serta Frequency/Time Masking pada tensor masukan.
   - *Tujuan:* Menilai ketahanan model terhadap variasi noise rekaman antar-sesi meja uji (GroupKFold).

## Hasil 3 seed konfigurasi akhir

Konfigurasi terbaik yang terpilih dari hasil ablasi akan dievaluasi menggunakan 3 *random seed* (42, 123, 2026) sesuai protokol penilaian dosen pembimbing:

| Random Seed | MAE (% duty) | RMSE | Waktu Inferensi / Latensi (ms) | Ukuran File ONNX (KB) |
| :--- | :--- | :--- | :--- | :--- |
| Seed 42 | *TBD* | *TBD* | *TBD* | *TBD* |
| Seed 123 | *TBD* | *TBD* | *TBD* | *TBD* |
| Seed 2026 | *TBD* | *TBD* | *TBD* | *TBD* |
| **Rata-rata $\pm$ Std** | **-** | **-** | **-** | **-** |

*Status saat ini: Menunggu tersedianya dataset rekaman meja uji tim (jadwal: 5–6 November 2026) dan integrasi pipeline data `GroupKFold` tim.*