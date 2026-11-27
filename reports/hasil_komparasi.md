# Komparasi Sprint 1 pada data primer

Sesi `sesi-20261117-220432`, seed 1, 3.711 segmen latih dan 338 segmen validasi dari ulangan 7.
Sidik data untuk semua jalur: `c70ef6fa3c33a2da1ff7d7050f56af9b`.
MAE dalam persen duty dihitung sebagai MAE PWM dibagi 255 dan dikali 100.
Data uji disimpan untuk Sprint 2.

## Artefak yang tercatat di repo

| Jalur | MAE validasi (% duty) | MAE validasi (PWM) |
|---|---:|---:|
| MFCC + Random Forest | 4.45 | 11.353027 |
| Transfer Learning | 3.35 | 8.536732 |
| Transformer | 1.73 | 4.406243 |
| Autoencoder | 2.11 | 5.376626 |
| CNN | 7.86 | 20.036744 |

Pembanding MFCC + Random Forest memakai 13 koefisien per frame, diringkas menjadi 26 fitur
dengan rata-rata dan simpangan baku per jendela satu detik. CNN mendapat MAE 7,86% duty,
lebih tinggi 3,41 poin persentase dari pembanding (4,45% duty, selisih dihitung sebelum pembulatan).
Pemeriksaan tambahan pada arsip simulasi menghasilkan MAE 0,51% duty dari 342 segmen validasi.

## Pelatihan ulang untuk demo di laptop

Dijalankan dengan `python run_all.py --seeds 1` pada data dan pembagian yang sama.
Angka pelatihan ulang di bawah ini ditampilkan di demo. Tiap kondisi pompa berisi 169 segmen validasi.

| Jalur | MAE validasi (% duty) | Pompa mati (% duty) | Pompa nyala (% duty) |
|---|---:|---:|---:|
| MFCC + Random Forest | 4.45 | 7.54 | 1.37 |
| Transfer Learning | 3.35 | 4.32 | 2.37 |
| Transformer | 1.85 | 2.05 | 1.65 |
| Autoencoder | 2.16 | 2.81 | 1.50 |
| CNN | 7.87 | 9.89 | 5.85 |
