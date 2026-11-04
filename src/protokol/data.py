"""Pemuat data kasus tim — MILIK TIM, dibekukan setelah Sprint 0 dengan persetujuan pembimbing.

Isi oleh Penjaga Data & Evaluasi. Kontrak yang dipakai penilai dan baseline starter:

    TUGAS = "klasifikasi"  # atau "regresi"
    muat() -> (X_train, y_train, X_val, y_val, X_test, y_test)

- X berupa array NumPy (bentuk bebas: [N, fitur], [N, C, H, W], [N, langkah, fitur]);
  y klasifikasi = label bulat 0..K-1, y regresi = float.
- Split latih/validasi WAJIB memakai ``src.common.split`` (seed 2026) agar sama di semua laptop.
- y_test boleh ``None`` bila dataset tidak punya bagian uji; bila ada, data uji hanya dievaluasi
  sekali di sprint terakhir.
- Berkas data dibaca dari ``data/`` dan dicantumkan di ``data/MANIFEST.json`` (sidik data).

Contoh lengkap: ``contoh_fashion_mnist.py`` di folder ini.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import wavfile
from scipy.signal import resample_poly, stft

from src.common import manifest, split

TUGAS = "regresi"

SR = 16000
N_MELS = 64
N_FFT = 1024
HOP_LENGTH = 512
ULANGAN_UJI = {13, 14, 15}


def _filterbank_mel(sr: int = SR, n_fft: int = N_FFT, n_mels: int = N_MELS) -> np.ndarray:
    m_min = 2595.0 * np.log10(1.0 + 0.0 / 700.0)
    m_max = 2595.0 * np.log10(1.0 + (sr / 2.0) / 700.0)
    m_pts = np.linspace(m_min, m_max, n_mels + 2)
    f_pts = 700.0 * (10.0 ** (m_pts / 2595.0) - 1.0)
    bins = np.floor((n_fft + 1) * f_pts / sr).astype(int)

    fb = np.zeros((n_mels, n_fft // 2 + 1), dtype=np.float32)
    for m in range(1, n_mels + 1):
        kiri, tengah, kanan = bins[m - 1], bins[m], bins[m + 1]
        if tengah > kiri:
            fb[m - 1, kiri:tengah] = (np.arange(kiri, tengah) - kiri) / (tengah - kiri)
        if kanan > tengah:
            fb[m - 1, tengah:kanan] = (kanan - np.arange(tengah, kanan)) / (kanan - tengah)
    return fb


_MEL_FB = _filterbank_mel()


def _potong_log_mel(path_wav: Path) -> np.ndarray:
    sr_asli, y = wavfile.read(path_wav)
    if y.ndim > 1:
        y = y.mean(axis=1)
    y = y.astype(np.float32)
    if np.abs(y).max() > 1.0:
        y /= 32768.0
    if sr_asli != SR:
        y = resample_poly(y, SR, sr_asli).astype(np.float32)

    y = y[SR:]  # buang 1 detik pertama setiap kondisi
    n_segmen = len(y) // SR

    segmen = []
    for i in range(n_segmen):
        potongan = y[i * SR : (i + 1) * SR]
        _, _, zxx = stft(
            potongan, fs=SR, nperseg=N_FFT, noverlap=N_FFT - HOP_LENGTH,
            padded=False, boundary=None
        )
        power = np.abs(zxx) ** 2
        mel = _MEL_FB @ power
        log_mel = 10.0 * np.log10(np.maximum(mel, 1e-10))
        log_mel -= log_mel.max()
        segmen.append(log_mel.astype(np.float32))
    return np.stack(segmen)


def _nomor_ulangan(val) -> int:
    return int(str(val).lower().replace("rep", "").strip())


def _duty_persen(row: pd.Series) -> float:
    if "Duty_Persen" in row and pd.notna(row["Duty_Persen"]):
        return float(str(row["Duty_Persen"]).replace("%", "").strip())
    pwm = row["PWM_Kipas"] if "PWM_Kipas" in row else row["kipas"]
    return (float(pwm) / 255.0) * 100.0


def _cari_folder_sesi(folder_sesi: str | Path | None) -> Path:
    if folder_sesi is not None:
        return Path(folder_sesi)
    akar_data = manifest.AKAR / "data"
    if (akar_data / "audio").is_dir():
        return akar_data
    for sub in sorted(akar_data.iterdir()):
        if sub.is_dir() and (sub / "audio").is_dir():
            return sub
    return akar_data


def _cari_csv_metadata(folder: Path) -> Path:
    # Prioritaskan label.csv, kemudian CSV metadata lain yang memiliki kolom Ulangan
    calon = list(folder.glob("label.csv")) or list(folder.glob("*label*.csv"))
    if not calon:
        for f in sorted(folder.glob("*.csv")):
            if f.name.lower() in ("daya.csv", "sensor.csv", "lingkungan.csv", "daya_sensor.csv"):
                continue
            try:
                kolom = pd.read_csv(f, nrows=1).columns
                if any(c in kolom for c in ("Ulangan", "ulangan", "rep", "Kondisi_ID", "PWM_Kipas")):
                    calon.append(f)
                    break
            except Exception:
                continue
    if not calon:
        calon = list(manifest.AKAR.glob("LEMBAR_SESI*.csv"))
    if not calon:
        raise FileNotFoundError(f"Tidak ditemukan berkas CSV metadata/label di {folder} maupun akar repositori.")
    return calon[0]


def muat(folder_sesi: str | Path | None = None):
    """Memuat dataset suara kipas Tim 22 sesuai protokol pembagian per ulangan."""
    folder = _cari_folder_sesi(folder_sesi)
    berkas_csv = _cari_csv_metadata(folder)
    df = pd.read_csv(berkas_csv)

    kol_ulangan = next((c for c in ("Ulangan", "ulangan", "rep") if c in df.columns), None)
    if kol_ulangan is None:
        raise ValueError(f"Berkas {berkas_csv.name} tidak memiliki kolom nomor ulangan ('Ulangan'/'ulangan'/'rep').")

    kol_audio = next((c for c in ("file_audio", "audio", "file", "path") if c in df.columns), None)
    folder_audio = folder / "audio"
    daftar_wav = sorted(folder_audio.glob("*.wav")) if folder_audio.is_dir() else []

    if kol_audio is None and not daftar_wav:
        raise FileNotFoundError(
            f"Tidak ditemukan berkas audio .wav di {folder_audio}. "
            "Pastikan folder sesi memuat subfolder 'audio/' berisi rekaman .wav "
            "atau berikan path folder_sesi saat memanggil muat()."
        )

    semua_ulangan = sorted({_nomor_ulangan(v) for v in df[kol_ulangan]})
    ulangan_non_uji = np.array([u for u in semua_ulangan if u not in ULANGAN_UJI])
    idx_tr, idx_va = split.indeks(len(ulangan_non_uji))
    ulangan_latih = set(ulangan_non_uji[idx_tr].tolist())
    ulangan_val = set(ulangan_non_uji[idx_va].tolist())

    data = {k: {"X": [], "y": [], "u": set()} for k in ("latih", "val", "uji")}

    for i, (_, row) in enumerate(df.iterrows()):
        u = _nomor_ulangan(row[kol_ulangan])
        if u in ulangan_latih:
            kunci = "latih"
        elif u in ulangan_val:
            kunci = "val"
        else:
            kunci = "uji"

        if kol_audio is not None:
            path_wav = Path(str(row[kol_audio]))
            if not path_wav.is_file():
                path_wav = folder_audio / path_wav.name
        else:
            if i >= len(daftar_wav):
                raise IndexError(
                    f"Jumlah baris metadata ({len(df)}) melebihi jumlah berkas audio ({len(daftar_wav)})."
                )
            path_wav = daftar_wav[i]

        if not path_wav.is_file():
            raise FileNotFoundError(f"Berkas audio tidak ditemukan: {path_wav}")

        fitur = _potong_log_mel(path_wav)
        target = _duty_persen(row)

        data[kunci]["X"].append(fitur)
        data[kunci]["y"].append(np.full(len(fitur), target, dtype=np.float32))
        data[kunci]["u"].add(u)

    assert data["latih"]["u"].isdisjoint(data["uji"]["u"]), "Bocor: ulangan latih & uji beririsan!"
    assert data["latih"]["u"].isdisjoint(data["val"]["u"]), "Bocor: ulangan latih & val beririsan!"
    assert data["val"]["u"].isdisjoint(data["uji"]["u"]), "Bocor: ulangan val & uji beririsan!"

    X_train = np.concatenate(data["latih"]["X"]).astype(np.float32)
    y_train = np.concatenate(data["latih"]["y"]).astype(np.float32)
    X_val = np.concatenate(data["val"]["X"]).astype(np.float32)
    y_val = np.concatenate(data["val"]["y"]).astype(np.float32)
    X_test = np.concatenate(data["uji"]["X"]).astype(np.float32)
    y_test = np.concatenate(data["uji"]["y"]).astype(np.float32)

    mean = X_train.mean(axis=(0, 2), keepdims=True)
    std = X_train.std(axis=(0, 2), keepdims=True) + 1e-8

    X_train = (X_train - mean) / std
    X_val = (X_val - mean) / std
    X_test = (X_test - mean) / std

    return X_train, y_train, X_val, y_val, X_test, y_test
