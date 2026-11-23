# Catatan Sesi Meja Uji - Tim 22

**Status: DATA PRIMER RESMI MEJA UJI**
Dokumen ini mencatat hasil kurasi dan pemeriksaan data rekaman fisik meja uji untuk sesi `sesi-20261117-220432`.

**Kasus:** Taksiran Kecepatan Kipas dari Suara (Regresi)
**Pilar:** Mesin dan Energi
**Dosen Pembimbing:** Christyan Tamaro Nadeak
**Penjaga Data:** Qois Olifio (123450067)
**Waktu Perekaman Sesi:** 17 November 2026, 22:04:32 s.d. 23:43:34 WIB
**Lokasi Meja Uji:** Ruang Cerdas 5 V, Lab Sains Data ITERA (`host: sditera-civ`, `versi_perekam: 1.13`, `simulasi=False`)

---

## 1. Identitas Sesi & Berkas Data

- **ID Sesi:** `sesi-20261117-220432` (Arsip `tim22_sesi-20261117-220432.tar`)
- **Lokasi lokal tim:** `data/sesi-20261117-220432/` (berkas audio dan sensor diabaikan `.gitignore` dan dibagikan ke tim melalui Google Drive).
- **Struktur berkas sesi:**
  - `label.csv` (metadata 270 kondisi: `no`, `ulangan`, `kipas`, `pompa`, `t_mulai_host`, `t_selesai_host`, `suhu_C`, `lux`)
  - `audio_index.csv` (indeks waktu potong kontinu tiap berkas audio terhadap `t_mulai_host`)
  - Folder `audio/` (100 berkas `.wav` mono 48.000 Hz 16-bit PCM: `audio-0001.wav` s.d. `audio-0099.wav` berdurasi ~60 detik, dan `audio-0100.wav` ekor sesi 0,417 detik)
  - `daya.csv`, `aktuator.csv`, `digital.csv`, `imu.csv`, `lingkungan.csv`, `rencana.yaml`, `manifest.json`, `log.txt`
- **Sidik Data (`data_hash`):**
  - Seluruh 110 berkas sesi terdaftar di `data/MANIFEST.json`.
  - `manifest.data_hash()` murni: `5c035f31ae305ce00e593692c029b47c`
  - `data_hash` evaluator (`split:2026`): `c70ef6fa3c33a2da1ff7d7050f56af9b`

---

## 2. Hasil Pemeriksaan Pipeline pada Data Primer

### A. Pemeriksaan Umum (Panduan Metode Bagian 8)
- [x] **Kecocokan SHA-256 (`manifest.json` sesi):** 108 dari 109 entri cocok persis SHA-256 dan ukuran byte-nya. Hanya `log.txt` yang berselisih 103 byte (1.908 B vs 1.805 B) karena baris penutup log ditulis sesudah `manifest.json` selesai disusun.
- [x] **Format Audio:** Mono, Sample Rate asli 48.000 Hz, 16-bit PCM (di-resample ke 16.000 Hz oleh `src/protokol/data.py`).
- [x] **Integritas & Cakupan Durasi:** Seluruh 100 berkas `.wav` terbaca utuh tanpa kerusakan header. Berdasarkan pemetaan `audio_index.csv`, seluruh 270 kondisi tercakup audio selama 19,969 detik s.d. 20,001 detik tanpa kondisi bisu (`RMS = 0` nihil).

### B. Pemeriksaan Khusus Kasus Tim 22
- [x] **Jumlah Kondisi:**
  - Rencana: 270 kondisi (9 taraf PWM kipas x 2 status pompa x 15 ulangan).
  - Realisasi: 270 kondisi lengkap tercatat di `label.csv` (18 kombinasi x 15 ulangan, suhu ruangan 26,0 s.d. 27,9 °C). Selisih = 0 kondisi.
- [x] **Karakteristik Sensor Daya (`daya.csv`, kanal `kipas` setelah 1 detik transien awal):**
  - Rerata arus kipas terverifikasi naik bertahap secara monoton terhadap taraf PWM:
    - PWM 0: `-0.13 mA`
    - PWM 32: `22.16 mA`
    - PWM 64: `53.42 mA`
    - PWM 96: `83.95 mA`
    - PWM 128: `112.79 mA`
    - PWM 160: `141.78 mA`
    - PWM 192: `168.34 mA`
    - PWM 224: `198.00 mA`
    - PWM 255: `240.23 mA`

---

## 3. Catatan Kondisi yang Dikeluarkan / Anomali

Seluruh **270 kondisi dipertahankan** (0 kondisi dikeluarkan). Dua temuan minor selama kurasi dicatat di bawah ini untuk transparansi analisis:

| No | Ulangan | Kipas (PWM) | Pompa | Status | Keterangan / Catatan Kurasi |
|:--:|:-------:|:-----------:|:-----:|:------:|:----------------------------|
| 1 | 1 | 224 | 0 | **Dipertahankan** | Awal kondisi mulai 30,7 ms sebelum `audio-0001.wav` tercatat (durasi audio 19,969 s), menghasilkan 18 segmen stabil (sesuai aturan pembuangan sisa < 1 s). |
| 256 | 10 | 0 | 200 | **Dipertahankan** | Mengalami lonjakan amplitudo sesaat mencapai `0.99997` (23 sampel *clipping*) pada detik ke-15; segmen lainnya stabil (`RMS ~0.009`) dan dinormalisasi per segmen oleh log-mel. |
| 63 kondisi | Campuran | Campuran | Campuran | **Dipertahankan** | Akibat perbedaan kecil waktu jam *host* (< 1,5 ms) sehingga durasi terliput berada di `19,9986` s.d. `19,9999` s, kondisi tersebut menghasilkan 18 segmen (bukan 19) setelah 1 s transien dibuang tanpa *padding*. |

*Catatan:* Pada sesi ini kolom `pintu_awal` dan `pintu_akhir` di `label.csv` kosong dan sensor digital tidak mencatat gangguan penanda pintu.
