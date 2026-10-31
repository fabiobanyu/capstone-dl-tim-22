# Catatan Eksperimen Autoencoder

## Identitas
- Nama: Rahmah Gustriana Deka
- NIM: 123450102
- Jalur model: Autoencoder (AE)

## Tujuan
Membangun model Autoencoder untuk mempelajari representasi fitur audio kipas dan memanfaatkan representasi tersebut untuk memprediksi nilai PWM kipas.

## Data dan Input
- Sumber: Rekaman audio kipas dari dataset tim.
- Sampling rate: 16 kHz.
- Fitur: Log-Mel Spectrogram.
- Jumlah mel band: 64.
- Durasi setiap sampel: 1 detik.

## Rancangan Arsitektur
- Encoder: mempelajari representasi laten dari fitur audio.
- Decoder: merekonstruksi fitur input.
- Regression head: memprediksi PWM kipas dari representasi laten.
- Output regresi: nilai PWM kipas pada rentang 0–255.

## Rencana Pelatihan
- Tugas: Regresi.
- Loss rekonstruksi: MSE.
- Loss prediksi PWM: MSE.
- Optimizer: Adam.
- Evaluasi: MAE.
- Jumlah seed: 3.
- Perangkat: CPU laptop.

## Status
Rancangan awal. Implementasi dan pelatihan menunggu pemuat dataset tim tersedia.

## Hasil Uji Awal Arsitektur
- Tanggal: 31 Oktober 2026
- Status: Berhasil
- Input uji: Tensor acak berukuran (4, 64).
- Output rekonstruksi: (4, 64).
- Output prediksi PWM: (4,).
- Framework: PyTorch CPU.
- Catatan: Uji ini hanya memeriksa bentuk keluaran model, bukan performa prediksi pada dataset sebenarnya.

## Pekerjaan yang Belum Dilakukan
- Pelatihan menggunakan rekaman audio kipas.
- Evaluasi MAE, RMSE, dan R².
- Pengujian dengan 3 seeds.
- Ekspor model ke ONNX.
- Pengukuran ukuran model dan latensi.