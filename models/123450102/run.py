
"""Model Autoencoder untuk prediksi PWM kipas."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))

from src.protokol import data  # noqa: E402

NIM = Path(__file__).resolve().parent.name
JALUR = "ae"


class AutoencoderRegresi(nn.Module):
    """Autoencoder dengan kepala regresi untuk memprediksi PWM."""

    def __init__(self, jumlah_fitur: int):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(jumlah_fitur, 256),
            nn.ReLU(),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
        )

        self.decoder = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, 256),
            nn.ReLU(),
            nn.Linear(256, jumlah_fitur),
        )

        self.kepala_regresi = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        laten = self.encoder(x)
        rekonstruksi = self.decoder(laten)
        prediksi = self.kepala_regresi(laten) * 255.0
        return rekonstruksi, prediksi.squeeze(1)


def ke_tensor(X):
    X = np.asarray(X, dtype=np.float32)
    return torch.tensor(X).reshape(len(X), -1)


def latih_dan_prediksi(seed: int, final: bool):
    torch.manual_seed(seed)
    np.random.seed(seed)

    Xtr, ytr, Xva, _, Xte, _ = data.muat()

    X_train = ke_tensor(Xtr)
    X_val = ke_tensor(Xva)
    y_train = torch.tensor(
        np.asarray(ytr, dtype=np.float32).reshape(-1)
    )

    if len(X_train) != len(y_train):
        raise ValueError("Jumlah data X_train dan y_train tidak sama.")

    model = AutoencoderRegresi(X_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    loss_rekonstruksi = nn.MSELoss()
    loss_regresi = nn.MSELoss()

    model.train()

    for epoch in range(50):
        for i in range(0, len(X_train), 128):
            xb = X_train[i:i + 128]
            yb = y_train[i:i + 128]

            optimizer.zero_grad()

            hasil_rekonstruksi, prediksi = model(xb)

            loss_ae = loss_rekonstruksi(hasil_rekonstruksi, xb)
            loss_pwm = loss_regresi(prediksi, yb)

            loss = loss_ae + loss_pwm
            loss.backward()
            optimizer.step()

    model.eval()

    with torch.no_grad():
        _, pred_val = model(X_val)
        pred_test = None

        if final and Xte is not None:
            _, pred_test = model(ke_tensor(Xte))
            pred_test = pred_test.numpy()

    return pred_val.numpy(), pred_test


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--perangkat", default="cpu laptop")
    args = parser.parse_args()

    mulai = time.time()
    pred_val, pred_test = latih_dan_prediksi(args.seed, args.final)
    durasi = time.time() - mulai

    output = AKAR / "results" / NIM
    output.mkdir(parents=True, exist_ok=True)

    np.save(output / "pred_val.npy", pred_val)

    perintah = [
        sys.executable,
        "-m", "src.common.evaluate",
        "--nim", NIM,
        "--model", JALUR,
        "--seed", str(args.seed),
        "--pred-val", str(output / "pred_val.npy"),
        "--durasi", f"{durasi:.1f}",
        "--perangkat", args.perangkat,
    ]

    if pred_test is not None:
        np.save(output / "pred_test.npy", pred_test)
        perintah += ["--pred-test", str(output / "pred_test.npy")]

    subprocess.run(perintah, check=True, cwd=AKAR)


if __name__ == "__main__":
    main()
