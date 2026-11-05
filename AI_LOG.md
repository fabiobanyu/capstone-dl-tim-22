# AI_LOG — Tim 22

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-03 | 12345678 | Copilot | kerangka DataLoader | ganti normalisasi, tambah seed worker |
| 2026-10-31 | 123450104 | Codex (OpenAI) | Menyusun draf protokol, status manifest, dan pesan pemuat untuk Sprint 0 | Draf disesuaikan dengan kartu kasus; parameter yang belum diketahui dibiarkan terbuka. Belum ditinjau tim/pembimbing. |
| 2026-10-31 | 123450104 | Codex (OpenAI) | Memperbaiki pemanggilan baseline dan tabel regresi di run_all.py | Menggunakan baseline bawaan yang ada; pengujian memakai data buatan hanya untuk memeriksa kode. Belum ditinjau tim. |
| 2026-11-05 | 123450104 | Codex (OpenAI) | Menyesuaikan CNN dengan label rasio duty 0–1 | Menambahkan validasi skala, keluaran sigmoid, dan memakai normalisasi dari pemuat tim. Masih perlu penyelarasan pemuat data dan pengujian dengan data tim. |
| 2026-11-05 | 123450104 | Codex (OpenAI) | Menyesuaikan CNN dengan skala PWM 0–255 sesuai keputusan tim | Target dinormalkan hanya untuk perhitungan loss; prediksi dikembalikan ke 0–255. MAE dikonversi ke persen saat pelaporan. |
| 2026-11-04 | 123450067 | Antigravity | Menyeragamkan target regresi ke PWM 0–255, simulator meja.py, dan mitigasi pembacaan data loader | Mengubah target y ke skala PWM 0–255 agar selaras dengan model Autoencoder Rahmah, menambahkan pencocokan audio deterministik via metadata, dan menyusun validasi otomatis periksa_sesi.py. |
