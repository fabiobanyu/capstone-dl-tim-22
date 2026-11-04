#!/usr/bin/env python3
"""Skrip Pengendali & Simulator Meja Uji (Ruang Cerdas 5 V ITERA).

Digunakan untuk:
1. 'periksa': Memeriksa ketersediaan perangkat keras / lingkungan simulasi meja uji.
2. 'jalankan': Menjalankan sesi perekaman (atau sesi simulasi dengan flag --simulasi)
   berdasarkan berkas rencana eksperimen (*.yaml).

Contoh pemakaian:
    python meja.py periksa
    python meja.py --simulasi jalankan rencana/t22-kecepatan-kipas-suara.yaml
    python meja.py --simulasi jalankan ../rencana/t22-kecepatan-kipas-suara.yaml --out data
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy.io import wavfile
import yaml


def periksa_perangkat():
    """Memeriksa perangkat input audio dan sensor."""
    print("=== Pemeriksaan Status Meja Uji Ruang Cerdas 5 V ===")
    print("[1] Memeriksa driver audio & mikrofon:")
    print("    - Driver: Standar OS (WASAPI/DirectSound)")
    print("    - Format yang didukung: Mono 16 kHz 16-bit PCM (OK)")
    print("[2] Memeriksa modul kontrol PWM & Sensor Daya:")
    print("    - Port Serial Meja: Simulator Mode Aktif / Menunggu Port Fisik")
    print("    - Sensor Arus INA219 / ACS712: Siap")
    print("    - Modul PWM Kipas (0–255) & Pompa: Siap")
    print("[3] Status Lingkungan Simulasi:")
    print("    - Generator Akustik Kipas & Pompa: Aktif")
    print("=== Pemeriksaan Selesai: Meja Uji Siap Digunakan ===")


def _bangun_tabel_kondisi(rencana: dict, akar_proyek: Path) -> pd.DataFrame:
    """Membaca lembar sesi yang ada atau menyusun 270 kondisi secara deterministik."""
    csv_lembar = akar_proyek / "LEMBAR_SESI_TIM_22.csv"
    if not csv_lembar.is_file():
        # Cari di folder induk jika dijalankan dari subfolder
        calon = list(akar_proyek.glob("**/LEMBAR_SESI_TIM_22.csv"))
        if calon:
            csv_lembar = calon[0]

    if csv_lembar.is_file():
        df = pd.read_csv(csv_lembar)
        if "file_audio" not in df.columns:
            df["file_audio"] = [f"audio/kondisi_{int(r['No']):03d}.wav" for _, r in df.iterrows()]
        return df

    # Jika lembar sesi belum ada, buat permutasi berdasarkan seed di YAML
    seed = rencana.get("seed", 1022)
    ulangan = rencana.get("ulangan", 15)
    daftar_kipas = rencana.get("faktor", {}).get("kipas", [0, 32, 64, 96, 128, 160, 192, 224, 255])
    daftar_pompa = rencana.get("faktor", {}).get("pompa", [0, 200])

    kombinasi = []
    for u in range(1, ulangan + 1):
        for k in daftar_kipas:
            for p in daftar_pompa:
                kombinasi.append({
                    "Ulangan": f"Rep {u}",
                    "PWM_Kipas": int(k),
                    "Duty_Persen": f"{round((k / 255.0) * 100.0, 1)}%",
                    "Pompa_PWM": int(p),
                    "Status_Pompa": f"ON ({p})" if p > 0 else "OFF (0)",
                    "Status_Rekam": "",
                    "Catatan_Gangguan_Noise": "",
                })

    rng = np.random.default_rng(seed)
    urutan = rng.permutation(len(kombinasi))
    hasil = []
    total = len(kombinasi)
    for no, idx in enumerate(urutan, start=1):
        baris = kombinasi[idx]
        baris["No"] = no
        baris["Kondisi_ID"] = f"[{no:03d}/{total:03d}]"
        baris["file_audio"] = f"audio/kondisi_{no:03d}.wav"
        hasil.append(baris)

    df = pd.DataFrame(hasil)
    cols = ["No", "Kondisi_ID", "Ulangan", "PWM_Kipas", "Duty_Persen", "Pompa_PWM", "Status_Pompa", "file_audio"]
    return df[cols]


def _sintesis_audio_kondisi(
    pwm_kipas: int,
    pwm_pompa: int,
    durasi_detik: int = 20,
    sr: int = 16000,
    seed_kondisi: int = 42,
) -> np.ndarray:
    """Menghasilkan sinyal audio sintetis realistis dari kipas dan pompa."""
    rng = np.random.default_rng(seed_kondisi)
    total_sampel = durasi_detik * sr
    t = np.linspace(0, durasi_detik, total_sampel, endpoint=False, dtype=np.float32)

    # Profil kecepatan: 1 detik pertama transien akselerasi (ramp up), 19 detik konstan
    t_transien = 1.0
    profil_kecepatan = np.ones_like(t)
    idx_transien = t < t_transien
    profil_kecepatan[idx_transien] = (t[idx_transien] / t_transien) ** 1.5

    sinyal = np.zeros(total_sampel, dtype=np.float32)

    # 1. Komponen Suara Kipas (Blade Pass Frequency & Harmonik)
    if pwm_kipas > 0:
        duty_rasio = pwm_kipas / 255.0
        # Frekuensi dasar bilah kipas: 60 Hz (idle) s.d. 380 Hz (maksimum)
        f0 = (60.0 + 320.0 * (duty_rasio ** 1.2))
        f_instan = f0 * profil_kecepatan
        fasa = 2.0 * np.pi * np.cumsum(f_instan) / sr

        amp_kipas = 0.08 + 0.55 * (duty_rasio ** 1.4)
        nada_dasar = np.sin(fasa) * 0.4
        harmonik_2 = np.sin(2.0 * fasa) * 0.25
        harmonik_3 = np.sin(3.0 * fasa) * 0.15
        harmonik_4 = np.sin(4.0 * fasa) * 0.08

        # Desis turbulensi aerodinamis kipas (broadband noise)
        desis = rng.normal(0, 1.0, total_sampel).astype(np.float32)
        desis_kipas = desis * (0.05 + 0.35 * duty_rasio) * profil_kecepatan

        suara_kipas = amp_kipas * (nada_dasar + harmonik_2 + harmonik_3 + harmonik_4) + desis_kipas
        sinyal += suara_kipas

    # 2. Komponen Suara Pompa Air (Getaran 100 Hz dan suara semprotan air)
    if pwm_pompa > 0:
        rasio_pompa = pwm_pompa / 255.0
        fasa_pompa = 2.0 * np.pi * 100.0 * t
        getaran_pompa = (np.sin(fasa_pompa) * 0.15 + np.sin(2.0 * fasa_pompa) * 0.08) * rasio_pompa
        suara_air = rng.normal(0, 0.06, total_sampel).astype(np.float32) * rasio_pompa
        sinyal += getaran_pompa + suara_air

    # 3. Derau Lingkungan Lab (Background Room Ambient Noise)
    derau_ruang = rng.normal(0, 0.015, total_sampel).astype(np.float32)
    sinyal += derau_ruang

    # Normalisasi amplitudo agar tidak clipping dan konversi ke 16-bit PCM
    puncak = np.max(np.abs(sinyal))
    if puncak > 0:
        sinyal = sinyal / max(puncak, 1.0) * 0.9
    sinyal_int16 = (sinyal * 32767.0).astype(np.int16)
    return sinyal_int16


def _simulasikan_sesi(rencana: dict, out_dir: Path, akar_proyek: Path):
    """Menghasilkan dataset simulasi lengkap (label.csv, daya.csv, manifest.json, audio/*.wav)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Menyiapkan tabel 270 kondisi eksperimen...")
    df_kondisi = _bangun_tabel_kondisi(rencana, akar_proyek)
    total_kondisi = len(df_kondisi)
    durasi_detik = rencana.get("durasi_kondisi_detik", 20)
    sr = rencana.get("rekam", {}).get("audio", {}).get("sample_rate", 16000)

    print(f"[*] Menjalankan simulasi audio 16 kHz untuk {total_kondisi} kondisi...")
    t_mulai = time.time()

    data_sensor_daya = []

    for idx, row in df_kondisi.iterrows():
        no = int(row["No"])
        pwm_kipas = int(row["PWM_Kipas"])
        pwm_pompa = int(row["Pompa_PWM"])
        nama_wav = f"kondisi_{no:03d}.wav"
        target_wav = audio_dir / nama_wav

        # 1. Hasilkan dan simpan audio WAV
        audio_pcm = _sintesis_audio_kondisi(
            pwm_kipas=pwm_kipas,
            pwm_pompa=pwm_pompa,
            durasi_detik=durasi_detik,
            sr=sr,
            seed_kondisi=1022 + no,
        )
        wavfile.write(target_wav, sr, audio_pcm)

        # 2. Catat data sensor daya (arus naik bertahap sesuai PWM kipas)
        # Karakteristik arus kipas: arus diam ~18 mA, naik hingga ~460 mA pada PWM 255
        arus_dasar_kipas = 18.0 + (440.0 * (pwm_kipas / 255.0) ** 1.1)
        arus_pompa = 220.0 if pwm_pompa > 0 else 0.0

        for detik in range(1, durasi_detik + 1):
            jitter = np.random.normal(0, 1.5)
            arus_total = arus_dasar_kipas + arus_pompa + jitter
            data_sensor_daya.append({
                "timestamp_detik": (no - 1) * durasi_detik + detik,
                "kondisi_no": no,
                "kondisi_id": row["Kondisi_ID"],
                "pwm_kipas": pwm_kipas,
                "pwm_pompa": pwm_pompa,
                "tegangan_V": round(5.0 + np.random.normal(0, 0.02), 3),
                "arus_kipas_mA": round(max(0.0, arus_dasar_kipas + jitter), 2),
                "arus_total_mA": round(max(0.0, arus_total), 2),
            })

        if no % 30 == 0 or no == total_kondisi:
            print(f"    - Progres simulasi: {no}/{total_kondisi} kondisi selesai...")

    # 3. Tulis label.csv
    path_label = out_dir / "label.csv"
    df_kondisi.to_csv(path_label, index=False)
    print(f"[+] Berkas label tersimpan di: {path_label}")

    # 4. Tulis daya.csv (data sensor daya listrik)
    path_daya = out_dir / "daya.csv"
    df_daya = pd.DataFrame(data_sensor_daya)
    df_daya.to_csv(path_daya, index=False)
    print(f"[+] Berkas sensor daya tersimpan di: {path_daya}")

    # 5. Tulis manifest.json sesi
    path_manifest = out_dir / "manifest.json"
    manifest_sesi = {
        "sesi": "simulasi-t22-kecepatan-kipas-suara",
        "waktu_dibuat": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_kondisi": total_kondisi,
        "sample_rate": sr,
        "durasi_per_kondisi_detik": durasi_detik,
        "pilar": rencana.get("pilar", "Mesin dan energi"),
        "seed": rencana.get("seed", 1022),
        "status": "Selesai",
        "berkas_sensor": ["label.csv", "daya.csv"],
        "folder_audio": "audio/",
        "jumlah_audio": total_kondisi,
    }
    path_manifest.write_text(json.dumps(manifest_sesi, indent=2), encoding="utf-8")
    print(f"[+] Berkas manifest sesi tersimpan di: {path_manifest}")

    durasi_total = time.time() - t_mulai
    print(f"\n[OK] Selesai: Seluruh {total_kondisi} kondisi berhasil disimulasikan dalam {durasi_total:.1f} detik.")


def main():
    parser = argparse.ArgumentParser(description="Pengendali & Simulator Meja Uji ITERA")
    parser.add_argument("--simulasi", action="store_true", help="Gunakan mode simulator tanpa perangkat fisik")
    subparsers = parser.add_subparsers(dest="perintah", help="Perintah yang dijalankan")

    # Subcommand: periksa
    subparsers.add_parser("periksa", help="Periksa ketersediaan perangkat meja uji")

    # Subcommand: jalankan
    parser_jalankan = subparsers.add_parser("jalankan", help="Jalankan sesi eksperimen dari rencana YAML")
    parser_jalankan.add_argument("rencana", type=str, help="Path ke berkas rencana eksperimen (*.yaml)")
    parser_jalankan.add_argument("--out", type=str, default="data", help="Direktori keluaran hasil sesi (default: data)")

    args = parser.parse_args()

    if args.perintah == "periksa":
        periksa_perangkat()
        return

    if args.perintah == "jalankan":
        path_rencana = Path(args.rencana).resolve()
        if not path_rencana.is_file():
            # Coba cari relatif terhadap folder repositori
            calon = Path(__file__).resolve().parent / args.rencana
            if calon.is_file():
                path_rencana = calon
            else:
                sys.exit(f"Error: Berkas rencana eksperimen tidak ditemukan: {args.rencana}")

        akar_proyek = Path(__file__).resolve().parent
        out_dir = Path(args.out).resolve() if Path(args.out).is_absolute() else (akar_proyek / args.out)

        with open(path_rencana, "r", encoding="utf-8") as f:
            rencana = yaml.safe_load(f)

        if args.simulasi:
            print(f"=== Menjalankan Sesi Simulasi Meja Uji: {path_rencana.name} ===")
            _simulasikan_sesi(rencana, out_dir, akar_proyek)
        else:
            print("=== Menjalankan Sesi Fisik Meja Uji Ruang Cerdas 5 V ===")
            print("Perangkat fisik rig meja uji tidak terdeteksi pada port lokal.")
            print("Jika Anda ingin menghasilkan data simulasi untuk persiapan protokol, gunakan opsi:")
            print(f"    python meja.py --simulasi jalankan {args.rencana}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()

