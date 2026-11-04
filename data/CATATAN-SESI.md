# Catatan Sesi Meja Uji — Tim 22

> [!WARNING]
> **STATUS: DRAF SIMULASI PERSIAPAN (PRA-SESI)**  
> **Data rekaman fisik meja uji BELUM DITERIMA** (jadwal slot tim: 5–6 November 2026).  
> Dokumen ini saat ini memuat **hasil pengujian simulasi awal (`meja.py --simulasi`)** untuk memverifikasi pipeline, format berkas, pemotong audio, dan integritas data loader. Dokumen ini akan diperbarui dengan data rekaman fisik setelah data resmi diserahkan pengelola meja lab.

**Kasus:** Taksiran Kecepatan Kipas dari Suara (Regresi)  
**Pilar:** Mesin dan Energi  
**Dosen Pembimbing:** Christyan Tamaro Nadeak  
**Penjaga Data:** Qois Olifio (123450067)  
**Jadwal Slot:** 5–6 November 2026 (Slot Operator 5 Nov 10.00–11.00 WIB, Slot Otomatis Malam 6 Nov 00.00–04.00 WIB)  
**Lokasi Meja Uji:** Ruang Cerdas 5 V, Lab Sains Data ITERA  

---

## 1. Identitas Sesi Simulasi & Berkas Data

- **ID Sesi:** `simulasi-t22-kecepatan-kipas-suara` (Tahap Uji Coba Pra-Slot)
- **Struktur berkas yang disiapkan untuk sesi:**
  - `label.csv` (metadata 270 kondisi: taraf PWM, status pompa, nomor ulangan, nama file audio)
  - `daya.csv` (data sensor arus dan tegangan)
  - `manifest.json` (manifes sesi meja uji)
  - Folder `audio/` (270 berkas `.wav` mono 16 kHz)
- **Sidik Data (`data_hash` starter):**
  - Berkas terdaftar di `data/MANIFEST.json`: `data/label.csv`, `data/daya.csv`, dan seluruh berkas di `data/audio/*.wav`.
  - Dihitung oleh `src.common.manifest.data_hash()` agar seluruh anggota tim memakai data identik.

---

## 2. Hasil Pemeriksaan Pipeline pada Data Simulasi

### A. Pemeriksaan Umum (Panduan Metode Bagian 8)
- [x] **Format Audio:** Mono, Sample Rate 16.000 Hz, 16-bit PCM.
- [x] **Durasi per Kondisi:** 20 detik (1 detik transien akselerasi + 19 detik kondisi stabil).
- [x] **Integritas Berkas:** Seluruh 270 berkas audio simulasi terbaca utuh tanpa kerusakan header.

### B. Pemeriksaan Khusus Kasus Tim 22
- [x] **Jumlah Kondisi:**
  - Rencana: 270 kondisi (9 level PWM kipas $\times$ 2 status pompa $\times$ 15 ulangan).
  - Realisasi simulasi: 270 kondisi lengkap tercatat di `label.csv`. Selisih = 0 kondisi.
- [x] **Karakteristik Sensor Daya (`daya.csv`):**
  - Arus kipas terverifikasi naik bertahap secara monoton terhadap nilai PWM:
    - PWM 0 (Kipas Mati): $\approx 17.9\text{ mA}$
    - PWM 64 (25%): $\approx 114.2\text{ mA}$
    - PWM 128 (50%): $\approx 224.1\text{ mA}$
    - PWM 192 (75%): $\approx 340.0\text{ mA}$
    - PWM 255 (100%): $\approx 458.0\text{ mA}$
  - Monotonisitas kenaikan arus terverifikasi pada data sensor.

---

## 3. Catatan Kondisi yang Dikeluarkan / Anomali

| No | Kondisi ID | Ulangan | Kipas (PWM) | Pompa | Status | Keterangan / Alasan Pengeluaran |
|:--:|:----------:|:-------:|:-----------:|:-----:|:------:|:--------------------------------|
| -  | -          | -       | -           | -     | **SIMULASI: NIHIL** | Pada tahap simulasi, seluruh 270 kondisi dihasilkan lengkap. |

*Rencana Aksi Sesi Riil (5–7 Nov):*  
Jika saat slot rekaman fisik di lab terjadi anomali (misalnya: mikrofon terlepas, kabel longgar, atau kebisingan manusia ekstrem di lab), kondisi bermasalah akan dicatat nomor ID-nya pada tabel ini beserta alasan pengeluarannya sebelum protokol evaluasi dibekukan bersama pembimbing.
