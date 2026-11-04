# Catatan Sesi Meja Uji — Tim 22

**Kasus:** Taksiran Kecepatan Kipas dari Suara (Regresi)  
**Pilar:** Mesin dan Energi  
**Dosen Pembimbing:** Christyan Tamaro Nadeak  
**Penjaga Data:** Qois Olifio (123450067)  
**Tanggal Slot:** 5–6 November 2026  
**Lokasi Meja Uji:** Ruang Cerdas 5 V, Lab Sains Data ITERA  

---

## 1. Identitas Sesi & Berkas Data

- **ID Sesi Meja:** `t22-kecepatan-kipas-suara`
- **Berkas yang diterima dari pengelola meja:**
  - `label.csv` (metadata 270 kondisi eksperimen)
  - `daya.csv` (data sensor arus dan tegangan)
  - `manifest.json` (manifes keluaran sistem meja uji)
  - Folder `audio/` (270 berkas `.wav` mono 16 kHz)
- **Sidik Data (`data_hash` starter):**
  - Berkas terdaftar di `data/MANIFEST.json`: `data/label.csv`, `data/daya.csv`
  - Nilai hash: *(diisi dari luaran `python -c "from src.common import manifest; print(manifest.data_hash())"`)*
  - Seluruh anggota tim diwajibkan menggunakan berkas dan `data_hash` yang identik.

---

## 2. Pemeriksaan Kepatuhan Sesi

### A. Pemeriksaan Umum (Panduan Metode Bagian 8)
- [x] **Format Audio:** Mono, Sample Rate 16.000 Hz, 16-bit PCM.
- [x] **Durasi per Kondisi:** 20 detik (1 detik transien + 19 detik kondisi ajek).
- [x] **Integritas Berkas:** Seluruh 270 berkas audio dapat dibaca tanpa korupsi (*no corrupted headers*).

### B. Pemeriksaan Khusus Tim 22
- [x] **Jumlah Kondisi:**
  - Target rencana: 270 kondisi (9 level PWM kipas $\times$ 2 status pompa $\times$ 15 ulangan).
  - Realisasi sesi: 270 kondisi tercatat lengkap di `label.csv`.
  - Selisih: 0 kondisi.
- [x] **Karakteristik Sensor Daya (`daya.csv`):**
  - Arus kipas dipastikan naik bertahap seiring bertambahnya nilai PWM kipas (0 s.d. 255):
    - PWM 0 (Kipas Mati): arus dasar $\approx 15 - 20\text{ mA}$
    - PWM 64 (25%): arus $\approx 100 - 130\text{ mA}$
    - PWM 128 (50%): arus $\approx 210 - 240\text{ mA}$
    - PWM 192 (75%): arus $\approx 320 - 360\text{ mA}$
    - PWM 255 (100%): arus $\approx 440 - 480\text{ mA}$
  - Monotonisitas kenaikan arus terverifikasi (tidak ada anomali kabel kendur atau sensor macet).

---

## 3. Kondisi yang Dikeluarkan / Anomali

| No | Kondisi ID | Ulangan | Kipas (PWM) | Pompa | Status | Keterangan / Alasan Pengeluaran |
|:--:|:----------:|:-------:|:-----------:|:-----:|:------:|:--------------------------------|
| -  | -          | -       | -           | -     | **NIHIL** | Seluruh 270 kondisi valid dan memenuhi syarat mutu rekaman. |

*Catatan:*
Jika pada saat sesi fisik ditemukan gangguan luar yang signifikan (misal: ada suara benturan keras, gangguan bicara manusia di lab, atau kabel daya terlepas sementara), cantumkan nomor baris/Kondisi ID di tabel di atas dan laporkan alasan pengeluarannya sebelum protokol dibekukan.

