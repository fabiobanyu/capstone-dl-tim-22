"""Model Transfer Learning (MobileNetV3-Small) untuk regresi nilai PWM kipas.

    python models/123450067/run.py --seed 1
    python models/123450067/run.py --seed 1 --final  # sprint terakhir

Alur model:
    log-mel [N, 64, waktu]
      -> interpolasi spasial ke (96, 96) + adaptor Conv2d(1 -> 3) + BatchNorm2d
      -> backbone MobileNetV3-Small pralatih (ImageNet) + AdaptiveAvgPool2d
      -> kepala regresi (Linear 576 -> 128 -> Hardswish -> Dropout -> Linear 1)
      -> prediksi PWM kontinu pada rentang 0.0 s.d. 255.0
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
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
from src.protokol import data  # noqa: E402

NIM = Path(__file__).resolve().parent.name     # 123450067
JALUR = "tl"                                   # Transfer learning

UKURAN_INPUT = (96, 96)
BATCH = 32
EPOCH_WARMUP = 2
EPOCH_FINETUNE = 8
LR_KEPALA = 1e-3
LR_BACKBONE = 5e-4
WEIGHT_DECAY = 1e-4
DROPOUT = 0.2


class TransferLearningRegresi(nn.Module):
    """Backbone MobileNetV3-Small pralatih dengan adaptor 1-kanal dan kepala regresi."""

    def __init__(self) -> None:
        super().__init__()
        self.adaptor = nn.Sequential(
            nn.Conv2d(1, 3, kernel_size=1, bias=False),
            nn.BatchNorm2d(3),
        )
        backbone = mobilenet_v3_small(weights=MobileNet_V3_Small_Weights.DEFAULT)
        self.features = backbone.features
        self.avgpool = backbone.avgpool
        in_fitur = backbone.classifier[0].in_features
        self.kepala = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_fitur, 128),
            nn.Hardswish(),
            nn.Dropout(DROPOUT),
            nn.Linear(128, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = nn.functional.interpolate(x, size=UKURAN_INPUT, mode="bilinear", align_corners=False)
        x = self.adaptor(x)
        x = self.features(x)
        x = self.avgpool(x)
        return self.kepala(x).squeeze(1)


def siapkan_fitur(X: np.ndarray) -> np.ndarray:
    """Pastikan bentuk masukan log-mel adalah [N, 1, 64, waktu] tanpa NaN/Inf."""
    X = np.asarray(X, dtype=np.float32)
    if X.ndim == 3:
        X = X[:, None, :, :]
    if X.ndim != 4 or X.shape[1] != 1 or X.shape[2] != 64 or X.shape[3] < 4:
        raise ValueError(f"X harus berbentuk [N, 64, waktu] atau [N, 1, 64, waktu], didapat {X.shape}")
    if not np.isfinite(X).all():
        raise ValueError("Fitur masukan mengandung nilai NaN atau Inf.")
    return X


def _jalankan_epoch(
    model: TransferLearningRegresi,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler | None = None,
    beku_backbone: bool = False,
) -> float:
    """Jalankan satu epoch pelatihan dan kembalikan rata-rata MSE terstandar."""
    model.train()
    if beku_backbone:
        # Jaga statistik BatchNorm pralatih tetap stabil saat bobot backbone dibekukan.
        model.features.eval()

    total_loss = 0.0
    total_sampel = 0
    for xb, yb in loader:
        optimizer.zero_grad()
        loss = nn.functional.mse_loss(model(xb), yb)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if scheduler is not None:
            scheduler.step()
        total_loss += float(loss.item()) * len(xb)
        total_sampel += len(xb)
    return total_loss / max(total_sampel, 1)


def _prediksi_batch(model: TransferLearningRegresi, X: np.ndarray, y_mean: float, y_std: float) -> np.ndarray:
    """Hitung prediksi batch dan kembalikan ke skala PWM 0.0 s.d. 255.0."""
    model.eval()
    loader = DataLoader(torch.from_numpy(X), batch_size=64)
    with torch.no_grad():
        z = np.concatenate([model(xb).numpy() for xb in loader])
    return np.clip(z * y_std + y_mean, 0.0, 255.0).astype(np.float32)


def latih_dan_prediksi(seed: int, final: bool) -> tuple[np.ndarray, np.ndarray | None]:
    """Kembalikan (pred_val, pred_test|None) dalam rentang target PWM 0.0 s.d. 255.0."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    Xtr, ytr, Xva, _, Xte, _ = data.muat()

    Xtr = siapkan_fitur(Xtr)
    Xva = siapkan_fitur(Xva)
    ytr = np.asarray(ytr, dtype=np.float32).reshape(-1)
    if len(Xtr) == 0 or len(Xva) == 0 or len(ytr) != len(Xtr):
        raise ValueError("Data latih/validasi kosong atau jumlah label latih tidak cocok.")
    if not np.isfinite(ytr).all() or np.any((ytr < 0.0) | (ytr > 255.0)):
        raise ValueError("Label latih harus berada pada rentang PWM 0.0 s.d. 255.0.")

    y_mean = float(ytr.mean())
    y_std = float(max(ytr.std(), 1e-6))
    ytr_z = ((ytr - y_mean) / y_std).astype(np.float32)

    gen = torch.Generator().manual_seed(seed)
    loader = DataLoader(
        TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ytr_z)),
        batch_size=BATCH,
        shuffle=True,
        generator=gen,
    )

    model = TransferLearningRegresi()
    n_param = sum(p.numel() for p in model.parameters())
    print(f"[{NIM}] MobileNetV3-Small TL, input {Xtr.shape[2]}x{Xtr.shape[3]} -> {UKURAN_INPUT}, {n_param:,} parameter", flush=True)

    # Tahap 1: pemanasan adaptor dan kepala regresi sementara backbone dibekukan.
    for p in model.features.parameters():
        p.requires_grad = False
    opt_warmup = torch.optim.AdamW(
        [{"params": list(model.adaptor.parameters()) + list(model.kepala.parameters()), "lr": LR_KEPALA}],
        weight_decay=WEIGHT_DECAY,
    )
    for ep in range(EPOCH_WARMUP):
        loss_ep = _jalankan_epoch(model, loader, opt_warmup, beku_backbone=True)
        print(f"  warmup   {ep + 1:2d}/{EPOCH_WARMUP}  loss {loss_ep:.4f}", flush=True)

    # Tahap 2: buka seluruh backbone dengan learning rate bertingkat.
    for p in model.features.parameters():
        p.requires_grad = True
    opt_ft = torch.optim.AdamW(
        [
            {"params": model.features.parameters(), "lr": LR_BACKBONE},
            {"params": list(model.adaptor.parameters()) + list(model.kepala.parameters()), "lr": LR_KEPALA},
        ],
        weight_decay=WEIGHT_DECAY,
    )
    jadwal = torch.optim.lr_scheduler.CosineAnnealingLR(opt_ft, T_max=EPOCH_FINETUNE * len(loader))
    for ep in range(EPOCH_FINETUNE):
        loss_ep = _jalankan_epoch(model, loader, opt_ft, scheduler=jadwal, beku_backbone=False)
        print(f"  finetune {ep + 1:2d}/{EPOCH_FINETUNE}  loss {loss_ep:.4f}", flush=True)

    pred_val = _prediksi_batch(model, Xva, y_mean, y_std)
    pred_test = None
    if final:
        if Xte is None:
            raise ValueError("Data uji tidak tersedia untuk --final.")
        Xte = siapkan_fitur(Xte)
        if len(Xte) == 0:
            raise ValueError("Data uji kosong.")
        pred_test = _prediksi_batch(model, Xte, y_mean, y_std)

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
