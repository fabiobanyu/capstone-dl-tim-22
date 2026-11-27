"""Pembanding non-DL Tim 22 pada data latih dan validasi protokol bersama."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.fft import dct
from sklearn.ensemble import RandomForestRegressor

from src.common import manifest, split
from src.protokol import data

N_MFCC = 13


def fitur_mfcc(log_mel: np.ndarray) -> np.ndarray:
    """DCT-II per frame, lalu rangkum setiap detik dengan mean dan simpangan."""
    mfcc = dct(log_mel, type=2, axis=1, norm="ortho")[:, :N_MFCC, :]
    return np.concatenate([mfcc.mean(axis=2), mfcc.std(axis=2)], axis=1)


def muat_fitur(folder_sesi: Path | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    folder = data._cari_folder_sesi(folder_sesi)
    label = pd.read_csv(data._cari_csv_metadata(folder))
    kol_ulangan = next((key for key in ("Ulangan", "ulangan", "rep") if key in label), None)
    if kol_ulangan is None:
        raise ValueError("Kolom ulangan tidak ditemukan pada metadata sesi.")
    ulangan = sorted(set(label[kol_ulangan].map(data._nomor_ulangan)) - data.ULANGAN_UJI)
    idx_latih, idx_val = split.indeks(len(ulangan))
    grup_latih = {ulangan[i] for i in idx_latih}
    grup_val = {ulangan[i] for i in idx_val}

    audio = folder / "audio"
    indeks = folder / "audio_index.csv"
    terindeks = indeks.is_file() and {"t_mulai_host", "t_selesai_host"}.issubset(label.columns)
    pembaca = data._PembacaAudioTerindeks(audio, indeks) if terindeks else None
    kol_audio = next((key for key in ("file_audio", "audio", "file", "path") if key in label), None)

    latih, validasi, pwm_latih, pwm_validasi = [], [], [], []
    for _, baris in label.iterrows():
        grup = data._nomor_ulangan(baris[kol_ulangan])
        if grup not in grup_latih and grup not in grup_val:
            continue
        if pembaca is not None:
            gelombang, sr = pembaca.potong_kondisi(baris["t_mulai_host"], baris["t_selesai_host"])
            log_mel = data._ekstrak_log_mel(gelombang, sr)
        else:
            path = data._temukan_file_audio(audio, baris, kol_audio)
            log_mel = data._potong_log_mel(path)

        fitur = fitur_mfcc(log_mel)
        pwm = np.full(len(fitur), data._ambil_pwm(baris), dtype=np.float32)
        if grup in grup_latih:
            latih.append(fitur)
            pwm_latih.append(pwm)
        else:
            validasi.append(fitur)
            pwm_validasi.append(pwm)

    return (
        np.concatenate(latih),
        np.concatenate(pwm_latih),
        np.concatenate(validasi),
        np.concatenate(pwm_validasi),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    mulai = time.perf_counter()
    X_train, y_train, X_val, y_val = muat_fitur()
    print(f"MFCC: {len(X_train)} latih, {len(X_val)} validasi, {X_train.shape[1]} fitur", flush=True)

    model = RandomForestRegressor(n_estimators=150, min_samples_leaf=2, random_state=args.seed, n_jobs=-1)
    model.fit(X_train, y_train)
    prediksi = model.predict(X_val)
    durasi = time.perf_counter() - mulai

    _, y_train_protokol, _, y_val_protokol, _, _ = data.muat()
    if not np.array_equal(y_train, y_train_protokol) or not np.array_equal(y_val, y_val_protokol):
        raise ValueError("Urutan label MFCC berbeda dari pemisahan protokol tim.")

    folder = manifest.AKAR / "results" / "baseline"
    folder.mkdir(parents=True, exist_ok=True)
    pred_val = folder / "pred_val.npy"
    np.save(pred_val, prediksi)
    subprocess.run(
        [sys.executable, "-m", "src.common.evaluate", "--nim", "baseline",
         "--model", "mfcc_rf", "--seed", str(args.seed), "--pred-val", str(pred_val),
         "--durasi", f"{durasi:.1f}", "--perangkat", "cpu laptop"],
        check=True,
        cwd=manifest.AKAR,
    )


if __name__ == "__main__":
    main()
