# Lembar Sesi Eksperimen Meja Uji — Tim 22

**Kasus:** Taksiran Kecepatan Kipas dari Suara (Regresi)  
**Meja Uji:** Ruang Cerdas 5 V, Lab Sains Data ITERA  
**Jadwal Slot:**
- Slot Operator: Kamis, 5 Nov 2026, 10.00–11.00 WIB
- Slot Otomatis Malam: Jumat, 6 Nov 2026, 00.00–04.00 WIB
**Dosen Pembimbing:** Christyan Tamaro Nadeak  
**Total Kondisi:** 270 kondisi (Seed: 1022) | Durasi: 20s rekam + 2s jeda (~1 jam 39 menit)

---

## Pembagian Peran di Meja
1. **Koordinator Sesi:** Fabio Banyu Cyto (123450104)
2. **Operator Rekam:** Sania Dwi Ayu Lestari (123450086)
3. **Operator Alat:** Rahmah Gustriana Deka (123450102)
4. **Pencatat Kejadian:** Qois
5. **Penjaga Suara:** Fabio & Sania

---

## Checklist Sebelum Menyalakan Skrip
- [ ] Air di wadah A terisi penuh (agar pompa celup tidak menyala kering).
- [ ] Mikrofon webcam mono 16 kHz terdeteksi (`python meja.py periksa`).
- [ ] Jalankan uji satu kondisi (Ctrl+C setelah 1 kondisi) untuk cek level audio.
- [ ] Seluruh anggota tim berada pada posisi masing-masing dan tidak berbicara saat kondisi aktif.

---

## Sampel 20 Kondisi Pertama (Sesi Siang Operator 5 Nov)
*Catatan: Seluruh 270 kondisi lengkap dapat dilihat dan dicetak langsung dari berkas `LEMBAR_SESI_TIM_22.html`.*

| No | Kondisi ID | Ulangan | Kipas (PWM) | Pompa | Status | Catatan Gangguan / Noise Luar |
|:--:|:----------:|:-------:|:-----------:|:-----:|:------:|:------------------------------|
| 1 | [001/270] | Rep 4 | 192 (75%) | 0 (OFF) | [ ] OK | |
| 2 | [002/270] | Rep 14 | 160 (63%) | 0 (OFF) | [ ] OK | |
| 3 | [003/270] | Rep 3 | 192 (75%) | 200 (ON) | [ ] OK | |
| 4 | [004/270] | Rep 4 | 255 (100%) | 200 (ON) | [ ] OK | |
| 5 | [005/270] | Rep 5 | 160 (63%) | 0 (OFF) | [ ] OK | |
| 6 | [006/270] | Rep 7 | 224 (88%) | 0 (OFF) | [ ] OK | |
| 7 | [007/270] | Rep 5 | 0 (0%) | 0 (OFF) | [ ] OK | |
| 8 | [008/270] | Rep 14 | 255 (100%) | 200 (ON) | [ ] OK | |
| 9 | [009/270] | Rep 12 | 160 (63%) | 200 (ON) | [ ] OK | |
| 10 | [010/270] | Rep 6 | 128 (50%) | 200 (ON) | [ ] OK | |
| 11 | [011/270] | Rep 1 | 32 (13%) | 0 (OFF) | [ ] OK | |
| 12 | [012/270] | Rep 14 | 128 (50%) | 0 (OFF) | [ ] OK | |
| 13 | [013/270] | Rep 15 | 32 (13%) | 200 (ON) | [ ] OK | |
| 14 | [014/270] | Rep 6 | 32 (13%) | 200 (ON) | [ ] OK | |
| 15 | [015/270] | Rep 13 | 32 (13%) | 200 (ON) | [ ] OK | |
| 16 | [016/270] | Rep 5 | 255 (100%) | 200 (ON) | [ ] OK | |
| 17 | [017/270] | Rep 4 | 255 (100%) | 0 (OFF) | [ ] OK | |
| 18 | [018/270] | Rep 6 | 192 (75%) | 200 (ON) | [ ] OK | |
| 19 | [019/270] | Rep 10 | 32 (13%) | 200 (ON) | [ ] OK | |
| 20 | [020/270] | Rep 8 | 255 (100%) | 200 (ON) | [ ] OK | |
| 21 | [021/270] | Rep 1 | 64 (25%) | 0 (OFF) | [ ] OK | |
| 22 | [022/270] | Rep 12 | 96 (38%) | 200 (ON) | [ ] OK | |
| 23 | [023/270] | Rep 2 | 192 (75%) | 0 (OFF) | [ ] OK | |
| 24 | [024/270] | Rep 10 | 192 (75%) | 0 (OFF) | [ ] OK | |
| 25 | [025/270] | Rep 1 | 0 (0%) | 200 (ON) | [ ] OK | |

*(Kondisi 26 sampai 270 dilanjutkan pada slot malam otomatis)*

---

## Pemeriksaan Pasca Sesi
1. Pastikan skrip menulis log terakhir bertuliskan "Selesai" dan berkas `manifest.json` terbuat.
2. Pengelola meja menyalin seluruh data ke flash disk tim.
3. Kembalikan meja ke keadaan acuan (matikan alat, rapikan kabel, tutup pintu kotak).
4. Foto lembar sesi ini dengan kamera HP dan simpan bersama data tim.
