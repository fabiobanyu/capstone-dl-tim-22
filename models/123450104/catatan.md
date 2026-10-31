# Catatan model CNN — Fabio (123450104)

## Status

Rancangan awal CNN regresi; belum dilatih atau dievaluasi pada rekaman kipas tim.
Data dan protokol pembagian kelompok masih menunggu kesepakatan/persetujuan pembimbing.

## Masukan dan keluaran sementara

- Masukan: log-mel 64 pita berbentuk `[N, 64, waktu]` atau `[N, 1, 64, waktu]`.
- Target dan prediksi: duty PWM dalam persen (0–100), bukan RPM. Skala target perlu disepakati tim.
- Normalisasi per pita dihitung dari data latih saja. Periksa agar tidak menormalisasi dua kali setelah protokol final tersedia.
- Pemisahan data ditangani `src.protokol.data.muat()`, bukan oleh model ini.

## Rancangan awal

- Dua tahap konvolusi dan pooling, satu konvolusi tambahan, global average pooling, dan satu keluaran regresi.
- Optimizer Adam (awal learning rate 0,001) untuk percobaan awal; belum dibandingkan dengan optimizer lain.
- Dropout 0,2 dan weight decay 0,0001 sebagai regularisasi awal. Sepuluh epoch adalah titik awal, belum hasil tuning.
- Loss pelatihan MSE; evaluasi utama tim adalah MAE dalam persen duty.

## Yang masih harus dikerjakan

- Sesuaikan pemrosesan dan satuan dengan protokol yang disetujui; pastikan split berdasarkan grup.
- Latih dan evaluasi dengan data nyata, lalu catat durasi, metrik, dan konfigurasi yang benar-benar dijalankan.
- Catat pencarian hyperparameter, minimal dua variasi/ablation, dan tiga seed pada konfigurasi akhir.
- Ekspor ONNX dan ukur ukuran serta latensi pada laptop yang ditentukan.

Belum ada hasil eksperimen atau metrik data nyata untuk dilaporkan.
