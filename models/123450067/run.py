"""Kerangka awal regresi untuk jalur Transfer Learning (TL) estimasi nilai PWM kipas.

Catatan: Berkas ini masih menggunakan jaringan regresi sederhana untuk memverifikasi
alur pemuat data dan evaluator pada skala PWM 0-255. Model pralatih (pretrained backbone)
untuk jalur transfer learning akan dipasang pada tahap pemodelan berikutnya.

    python models/123450067/run.py --seed 1
    python models/123450067/run.py --seed 1 --final  # sprint terakhir
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

NIM = Path(__file__).resolve().parent.name     # 123450067
JALUR = "tl"                                   # Transfer learning


def latih_dan_prediksi(seed: int, final: bool) -> tuple[np.ndarray, np.ndarray | None]:
    """Kembalikan (pred_val, pred_test|None) dalam rentang target PWM 0.0 s.d. 255.0."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    Xtr, ytr, Xva, _, Xte, _ = data.muat()

    def ke_tensor(X):
        return torch.tensor(np.asarray(X, dtype=np.float32)).reshape(len(X), -1)

    X_train, y_train = ke_tensor(Xtr), torch.tensor(np.asarray(ytr, dtype=np.float32)).reshape(-1)
    X_val = ke_tensor(Xva)

    if len(X_train) != len(y_train):
        raise ValueError("Jumlah sampel data latih dan label tidak cocok.")

    model = nn.Sequential(
        nn.Linear(X_train.shape[1], 128),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(128, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = nn.MSELoss()

    dataset = TensorDataset(X_train, y_train)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    for _ in range(5):
        model.train()
        for xb, yb in loader:
            optimizer.zero_grad()
            pred = model(xb).squeeze(-1)
            loss = loss_fn(pred, yb)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        pred_val = model(X_val).squeeze(-1).numpy().astype(np.float32)
        pred_test = None
        if final and Xte is not None:
            pred_test = model(ke_tensor(Xte)).squeeze(-1).numpy().astype(np.float32)

    return pred_val, pred_test


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--final", action="store_true", help="sprint terakhir: evaluasi data uji sekali")
    ap.add_argument("--perangkat", default="cpu laptop")
    a = ap.parse_args()
    t0 = time.time()
    pred_val, pred_test = latih_dan_prediksi(a.seed, a.final)
    durasi = time.time() - t0
    out = AKAR / "results" / NIM
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "pred_val.npy", np.asarray(pred_val))
    perintah = [sys.executable, "-m", "src.common.evaluate", "--nim", NIM, "--model", JALUR, "--seed", str(a.seed),
                "--pred-val", str(out / "pred_val.npy"), "--durasi", f"{durasi:.1f}", "--perangkat", a.perangkat]
    if pred_test is not None:
        np.save(out / "pred_test.npy", np.asarray(pred_test))
        perintah += ["--pred-test", str(out / "pred_test.npy")]
    subprocess.run(perintah, check=True, cwd=AKAR)


if __name__ == "__main__":
    main()
