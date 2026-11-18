#!/usr/bin/env python3
"""Skrip Pemeriksaan Validitas Data Sesi Meja Uji (Tugas 2).

Mendukung format sesi meja uji asli (potongan audio kontinu via audio_index.csv
pada 48 kHz dan daya.csv berbasis kanal) maupun format sesi simulasi lama.

Memeriksa:
1. Kesesuaian jumlah kondisi (target: 270 kondisi = 18 kombinasi x 15 ulangan).
2. Kenaikan arus listrik kipas di daya.csv terhadap nilai PWM (monotonisitas).
3. Integritas seluruh berkas audio .wav (dan kecocokan SHA-256 terhadap manifest.json sesi).
4. Perhitungan sidik data (data_hash) untuk disinkronkan ke seluruh anggota tim.

Contoh pemakaian:
    py periksa_sesi.py --dir data
    py periksa_sesi.py --dir data/sesi-20261117-220432
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.io import wavfile

AKAR = Path(__file__).resolve().parent
sys.path.insert(0, str(AKAR))
from src.common import manifest  # noqa: E402


def _temukan_folder_sesi(folder_data: Path) -> Path:
    if (folder_data / "audio").is_dir():
        return folder_data
    for sub in sorted(folder_data.iterdir()):
        if sub.is_dir() and (sub / "audio").is_dir():
            return sub
    return folder_data


def _cek_manifest_sesi(folder_sesi: Path) -> bool:
    path_man = folder_sesi / "manifest.json"
    if not path_man.is_file():
        return True
    isi = json.loads(path_man.read_text("utf-8"))
    berkas = isi.get("berkas")
    if not isinstance(berkas, dict):
        return True

    hilang, beda = [], []
    for rel, info in berkas.items():
        p = folder_sesi / rel
        if not p.is_file():
            hilang.append(rel)
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        if sha != info.get("sha256") or p.stat().st_size != info.get("bytes"):
            beda.append((rel, p.stat().st_size, info.get("bytes")))

    print("\n[0] Pemeriksaan SHA-256 terhadap manifest.json sesi:")
    print(f"    - Total entri manifest sesi: {len(berkas)}")
    print(f"    - Berkas hilang: {len(hilang)}, selisih ukuran/hash: {len(beda)}")
    if hilang:
        print(f"    - [GAGAL] Hilang: {hilang[:5]}")
        return False
    for rel, sz_disk, sz_man in beda:
        print(f"    - [CATATAN] {rel}: ukuran di disk {sz_disk} B vs manifest {sz_man} B")
    # Hanya anggap gagal jika file data/audio selain log.txt berbeda
    beda_kritis = [b for b in beda if b[0] != "log.txt"]
    if beda_kritis:
        print(f"    - [GAGAL] Berkas data tidak cocok SHA-256: {[b[0] for b in beda_kritis[:5]]}")
        return False
    print("    - Status: [OK] Seluruh berkas data dan audio cocok SHA-256.")
    return True


def _periksa_daya(folder_sesi: Path, df_label: pd.DataFrame) -> bool:
    path_daya = folder_sesi / "daya.csv"
    print("\n[2] Pemeriksaan Khusus Sensor Daya (daya.csv):")
    if not path_daya.is_file():
        print(f"    - [GAGAL] Berkas daya.csv tidak ditemukan di {folder_sesi}")
        return False

    df_daya = pd.read_csv(path_daya)
    kol_pwm = next((c for c in ("pwm_kipas", "PWM_Kipas", "kipas") if c in df_daya.columns), None)
    kol_arus = next((c for c in ("arus_kipas_mA", "arus", "arus_mA", "arus_total_mA") if c in df_daya.columns), None)

    if kol_pwm and kol_arus:
        rerata_arus = df_daya.groupby(kol_pwm)[kol_arus].mean().sort_index()
    elif {"t_host", "kanal", "arus_mA"}.issubset(df_daya.columns) and {"t_mulai_host", "t_selesai_host"}.issubset(df_label.columns):
        kol_kipas = next((c for c in ("kipas", "PWM_Kipas", "pwm_kipas") if c in df_label.columns), None)
        if kol_kipas is None:
            print("    - [GAGAL] Kolom target PWM kipas tidak ditemukan di label.csv")
            return False
        dk = df_daya[df_daya["kanal"] == "kipas"].sort_values("t_host")
        t_host = dk["t_host"].to_numpy()
        arus = dk["arus_mA"].to_numpy()

        nilai_per_pwm: dict[int, list[float]] = {}
        for _, row in df_label.iterrows():
            i0 = int(np.searchsorted(t_host, float(row["t_mulai_host"]) + 1.0, side="left"))
            i1 = int(np.searchsorted(t_host, float(row["t_selesai_host"]), side="right"))
            if i1 > i0:
                nilai_per_pwm.setdefault(int(row[kol_kipas]), []).append(float(arus[i0:i1].mean()))
        rerata_arus = pd.Series({k: float(np.mean(v)) for k, v in sorted(nilai_per_pwm.items())})
    else:
        print(f"    - [GAGAL] Format kolom di {path_daya.name} tidak dikenali.")
        return False

    print("    - Rerata arus kipas per taraf PWM:")
    for pwm, arus_val in rerata_arus.items():
        print(f"      * PWM {int(pwm):3d}: {arus_val:6.2f} mA")

    if len(rerata_arus) >= 2 and bool(np.all(np.diff(rerata_arus.to_numpy()) >= 0)):
        print("    - Status: [OK] Arus kipas naik bertahap sesuai taraf PWM.")
        return True

    print("    - Status: [PERINGATAN] Arus kipas tidak sepenuhnya monoton naik, periksa koneksi sensor.")
    return False


def _periksa_audio(folder_sesi: Path, df_label: pd.DataFrame, n_kondisi: int) -> bool:
    folder_audio = folder_sesi / "audio"
    print("\n[3] Pemeriksaan Rekaman Audio:")
    if not folder_audio.is_dir():
        print(f"    - [GAGAL] Folder audio tidak ditemukan di {folder_audio}")
        return False

    daftar_wav = sorted(folder_audio.glob("*.wav"))
    print(f"    - Total berkas .wav terdeteksi: {len(daftar_wav)}")
    if not daftar_wav:
        print("    - [GAGAL] Tidak ada berkas .wav di folder audio.")
        return False

    sr_set: set[int] = set()
    rusak: list[tuple[str, str]] = []
    for p in daftar_wav:
        try:
            sr, wav = wavfile.read(p)
            sr_set.add(int(sr))
            if len(wav) == 0:
                rusak.append((p.name, "kosong"))
        except Exception as exc:
            rusak.append((p.name, str(exc)))

    if rusak:
        print(f"    - [GAGAL] Berkas audio rusak/kosong: {rusak[:5]}")
        return False
    print(f"    - Integritas header seluruh {len(daftar_wav)} berkas .wav: [OK] (SR={sorted(sr_set)} Hz)")

    path_indeks = folder_sesi / "audio_index.csv"
    if path_indeks.is_file() and {"t_mulai_host", "t_selesai_host"}.issubset(df_label.columns):
        df_idx = pd.read_csv(path_indeks)
        df_idx["t_akhir_host"] = df_idx["t_mulai_host"] + df_idx["jumlah_sampel"] / df_idx["sample_rate"]
        t_awal = df_idx["t_mulai_host"].to_numpy()
        t_akhir = df_idx["t_akhir_host"].to_numpy()

        durasi_kondisi = []
        kurang = []
        for idx_r, row in df_label.iterrows():
            t0, t1 = float(row["t_mulai_host"]), float(row["t_selesai_host"])
            dur = float(np.maximum(0.0, np.minimum(t1, t_akhir) - np.maximum(t0, t_awal)).sum())
            durasi_kondisi.append(dur)
            if dur < 19.0:
                kurang.append((row.get("no", idx_r + 1), dur))
        print(
            f"    - Mode audio kontinu (audio_index.csv): durasi terliput "
            f"{min(durasi_kondisi):.3f}s s.d. {max(durasi_kondisi):.3f}s"
        )
        if kurang:
            print(f"    - [GAGAL] Kondisi dengan audio < 19 detik: {kurang[:5]}")
            return False
        print(f"    - Status: [OK] Seluruh {n_kondisi} kondisi tercakup audio >= 19 detik.")
        return True

    if len(daftar_wav) != n_kondisi:
        print(f"    - Status: [GAGAL] Jumlah berkas audio ({len(daftar_wav)}) != baris metadata ({n_kondisi}).")
        return False
    print(f"    - Status: [OK] Jumlah berkas audio cocok dengan jumlah kondisi ({n_kondisi}).")
    return True


def periksa_sesi(folder_data: Path) -> bool:
    folder_sesi = _temukan_folder_sesi(folder_data)
    print(f"=== Memulai Pemeriksaan Data Sesi: {folder_sesi} ===")
    sukses = _cek_manifest_sesi(folder_sesi)

    path_label = folder_sesi / "label.csv"
    if not path_label.is_file():
        calon = list(folder_sesi.glob("*label*.csv")) or list(AKAR.glob("LEMBAR_SESI*.csv"))
        if calon:
            path_label = calon[0]
        else:
            print(f"[GAGAL] Berkas label.csv tidak ditemukan di {folder_sesi}")
            return False

    df_label = pd.read_csv(path_label)
    n_kondisi = len(df_label)
    print("\n[1] Pemeriksaan Jumlah Kondisi:")
    print(f"    - Berkas metadata: {path_label.name}")
    print(f"    - Jumlah kondisi tercatat: {n_kondisi}")
    if n_kondisi == 270:
        print("    - Status: [OK] Sesuai rencana eksperimen (270 kondisi = 18 kombinasi x 15 ulangan).")
    else:
        print(f"    - Status: [PERHATIAN] Selisih kondisi tercatat: {n_kondisi - 270} (Target: 270).")
        sukses = False

    sukses = _periksa_daya(folder_sesi, df_label) and sukses
    sukses = _periksa_audio(folder_sesi, df_label, n_kondisi) and sukses

    print("\n[4] Pemeriksaan Sidik Data (data_hash):")
    try:
        hash_val = manifest.data_hash()
        print(f"    - data_hash saat ini: {hash_val}")
        print("    - Status: [OK] Hash berhasil dihitung. Pastikan seluruh anggota tim menghasilkan hash yang sama.")
    except Exception as exc:
        print(f"    - Status: [INFO] data/MANIFEST.json belum lengkap atau belum sesuai ({exc}).")
        sukses = False

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
