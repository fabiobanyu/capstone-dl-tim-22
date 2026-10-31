"""CNN awal untuk regresi duty PWM dari log-mel. Data dan protokol tim masih draf.

    python models/123450104/run.py --seed 1
    python models/123450104/run.py --seed 1 --final  # uji hanya pada sprint terakhir

Asumsi sementara: X berbentuk [N, 64, waktu] atau [N, 1, 64, waktu],
dan y berisi duty dalam persen (0–100). Pastikan sesuai protokol yang disetujui.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
from src.protokol import data  # noqa: E402

NIM = "123450104"


class CNNRegresi(nn.Module):
    def __init__(self):
        super().__init__()
        self.fitur = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)), nn.Flatten(), nn.Dropout(0.2),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.fitur(x).squeeze(1)


def siapkan_fitur(X):
    X = np.asarray(X, dtype=np.float32)
    if X.ndim == 3:
        X = X[:, None, :, :]
    if X.ndim != 4 or X.shape[1] != 1 or X.shape[2] != 64 or X.shape[3] < 4:
        raise ValueError("X harus berbentuk [N, 64, waktu] atau [N, 1, 64, waktu], waktu >= 4")
    if not np.isfinite(X).all():
        raise ValueError("Fitur mengandung nilai tidak valid")
    return X


def latih_dan_prediksi(seed: int, final: bool):
    torch.manual_seed(seed)
    np.random.seed(seed)
    Xtr, ytr, Xva, _, Xte, _ = data.muat()
    Xtr, Xva = siapkan_fitur(Xtr), siapkan_fitur(Xva)
    ytr = np.asarray(ytr, dtype=np.float32).reshape(-1)
    if len(Xtr) == 0 or len(Xva) == 0 or len(ytr) != len(Xtr):
        raise ValueError("Data latih/validasi kosong atau jumlah label latih tidak cocok")
    if not np.isfinite(ytr).all() or np.any((ytr < 0) | (ytr > 100)):
        raise ValueError("Label latih harus berupa duty persen dalam rentang 0–100")
    # Statistik per pita dihitung dari latih saja; sesuaikan jika protokol sudah menormalisasi X.
    mean = Xtr.mean(axis=(0, 3), keepdims=True)
    std = Xtr.std(axis=(0, 3), keepdims=True)
    std = np.maximum(std, 1e-6)
    Xtr, Xva = (Xtr - mean) / std, (Xva - mean) / std
    dataset = TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ytr))
    batches = DataLoader(dataset, batch_size=32, shuffle=True)
    model = CNNRegresi()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=0.0001)
    for _ in range(10):
        model.train()
        for x, y in batches:
            optimizer.zero_grad()
            loss = nn.functional.mse_loss(model(x), y)
            loss.backward()
            optimizer.step()

    def prediksi(X):
        model.eval()
        loader = DataLoader(torch.from_numpy(X), batch_size=32)
        with torch.no_grad():
            return np.concatenate([model(x).numpy() for x in loader]).astype(np.float32)

    val = prediksi(Xva)
    if final:
        if Xte is None:
            raise ValueError("Data uji tidak tersedia untuk --final")
        Xte = siapkan_fitur(Xte)
        if len(Xte) == 0:
            raise ValueError("Data uji kosong")
        return val, prediksi((Xte - mean) / std)
    return val, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--final", action="store_true", help="evaluasi uji hanya pada sprint terakhir")
    ap.add_argument("--perangkat", default="cpu laptop")
    args = ap.parse_args()
    mulai = time.time()
    val, test = latih_dan_prediksi(args.seed, args.final)
    durasi = time.time() - mulai
    out = AKAR / "results" / NIM
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "pred_val.npy", val)
    perintah = [sys.executable, "-m", "src.common.evaluate", "--nim", NIM, "--model", "cnn",
                "--seed", str(args.seed), "--pred-val", str(out / "pred_val.npy"),
                "--durasi", f"{durasi:.1f}", "--perangkat", args.perangkat]
    if test is not None:
        np.save(out / "pred_test.npy", test)
        perintah += ["--pred-test", str(out / "pred_test.npy")]
    subprocess.run(perintah, check=True, cwd=AKAR)


if __name__ == "__main__":
    main()
