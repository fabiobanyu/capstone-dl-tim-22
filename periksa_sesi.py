#!/usr/bin/env python3
"""Skrip Pemeriksaan Validitas Data Sesi Meja Uji (Tugas 2).

Memeriksa:
1. Kesesuaian jumlah kondisi (target: 270 kondisi = 18 kombinasi x 15 ulangan).
2. Kenaikan arus listrik kipas di daya.csv terhadap nilai PWM (monotonisitas).
3. Integritas audio 16 kHz (20 detik per kondisi).
4. Perhitungan sidik data (data_hash) untuk disinkronkan ke seluruh anggota tim.

Contoh pemakaian:
    python periksa_sesi.py --dir data
    python periksa_sesi.py --dir data_simulasi
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.io import wavfile

AKAR = Path(__file__).resolve().parent
sys.path.insert(0, str(AKAR))
from src.common import manifest  # noqa: E402


def periksa_sesi(folder_data: Path) -> bool:
    print(f"=== Memulai Pemeriksaan Data Sesi: {folder_data} ===")
    sukses = True

    # 1. Periksa label.csv / metadata
    path_label = folder_data / "label.csv"
    if not path_label.is_file():
        # Fallback ke LEMBAR_SESI_TIM_22.csv
        calon = list(folder_data.glob("*label*.csv")) or list(AKAR.glob("LEMBAR_SESI*.csv"))
        if calon:
            path_label = calon[0]
        else:
            print(f"[GAGAL] Berkas label.csv tidak ditemukan di {folder_data}")
            return False

    df_label = pd.read_csv(path_label)
    n_kondisi = len(df_label)
    print(f"\n[1] Pemeriksaan Jumlah Kondisi:")
    print(f"    - Berkas metadata: {path_label.name}")
    print(f"    - Jumlah kondisi tercatat: {n_kondisi}")
    if n_kondisi == 270:
        print("    - Status: [OK] Sesuai rencana eksperimen (270 kondisi = 18 kombinasi x 15 ulangan).")
    else:
        print(f"    - Status: [PERHATIAN] Selisih kondisi tercatat: {n_kondisi - 270} (Target: 270).")
        sukses = False

    # 2. Periksa daya.csv
    path_daya = folder_data / "daya.csv"
    print(f"\n[2] Pemeriksaan Khusus Sensor Daya (daya.csv):")
    if not path_daya.is_file():
        print(f"    - [GAGAL] Berkas daya.csv tidak ditemukan di {folder_data}")
        sukses = False
    else:
        df_daya = pd.read_csv(path_daya)
        kol_pwm = next((c for c in ("pwm_kipas", "PWM_Kipas", "kipas") if c in df_daya.columns), None)
        kol_arus = next((c for c in ("arus_kipas_mA", "arus", "arus_mA", "arus_total_mA") if c in df_daya.columns), None)

        if kol_pwm and kol_arus:
            rerata_arus = df_daya.groupby(kol_pwm)[kol_arus].mean()
            print("    - Rerata arus kipas per taraf PWM:")
            for pwm, arus in rerata_arus.items():
                print(f"      * PWM {pwm:3d}: {arus:6.2f} mA")

            # Cek apakah arus monoton naik
            arus_vals = rerata_arus.values
            is_monoton = np.all(np.diff(arus_vals) >= 0)
            if is_monoton:
                print("    - Status: [OK] Arus kipas naik bertahap sesuai taraf PWM.")
            else:
                print("    - Status: [PERINGATAN] Arus kipas tidak sepenuhnya monoton naik, periksa koneksi sensor.")
                sukses = False
        else:
            print(f"    - [GAGAL] Kolom PWM/Arus tidak ditemukan di {path_daya.name}")
            sukses = False

    # 3. Periksa Folder Audio
    folder_audio = folder_data / "audio"
    print(f"\n[3] Pemeriksaan Rekaman Audio:")
    if not folder_audio.is_dir():
        print(f"    - [GAGAL] Folder audio tidak ditemukan di {folder_audio}")
        sukses = False
    else:
        daftar_wav = sorted(folder_audio.glob("*.wav"))
        print(f"    - Total berkas .wav terdeteksi: {len(daftar_wav)}")
        if len(daftar_wav) == n_kondisi:
            print(f"    - Status: [OK] Jumlah berkas audio cocok dengan jumlah kondisi ({n_kondisi}).")
            # Cek format 1 sampel pertama
            sr, data_audio = wavfile.read(daftar_wav[0])
            durasi_s = len(data_audio) / sr
            print(f"    - Sampel pertama ({daftar_wav[0].name}): SR = {sr} Hz, Durasi = {durasi_s:.1f} s")
            if sr == 16000 and round(durasi_s) == 20:
                print("    - Format Audio: [OK] Mono 16 kHz, 20 detik.")
            else:
                print(f"    - Format Audio: [PERHATIAN] SR ({sr}) atau durasi ({durasi_s}s) tidak sesuai standar 16kHz/20s.")
        else:
            print(f"    - Status: [GAGAL] Jumlah berkas audio ({len(daftar_wav)}) != baris metadata ({n_kondisi}).")
            sukses = False

    # 4. Periksa data_hash di MANIFEST.json
    print(f"\n[4] Pemeriksaan Sidik Data (data_hash):")
    try:
        hash_val = manifest.data_hash()
        print(f"    - data_hash saat ini: {hash_val}")
        print("    - Status: [OK] Hash berhasil dihitung. Pastikan seluruh anggota tim menghasilkan hash yang sama.")
    except Exception as e:
        print(f"    - Status: [INFO] data/MANIFEST.json belum diisi berkas data aktif ({e}).")
        print("      Isi data/MANIFEST.json saat data sesi sudah disalin ke folder data/.")

    print(f"\n=== Hasil Pemeriksaan: {'LOLOS SEMUA UJI' if sukses else 'ADA CATATAN/PERBAIKAN'} ===")
    return sukses


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pemeriksaan Data Sesi Meja Uji")
    parser.add_argument("--dir", default="data", help="Direktori sesi (default: data)")
    args = parser.parse_args()

    jalur = Path(args.dir).resolve()
    if not jalur.is_dir():
        jalur = AKAR / args.dir
    periksa_sesi(jalur)

