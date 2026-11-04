"""Transformer encoder atas patch untuk regresi duty PWM dari log-mel — Sania (123450086).

    python models/123450086/run.py --seed 1
    python models/123450086/run.py --seed 1 --final   # uji hanya sekali, sprint terakhir

Alur model:
    log-mel [N, 64, waktu]
      -> normalisasi per pita (statistik dari data latih saja)
      -> potong menjadi patch (default 8 x 8), tiap patch diproyeksikan ke vektor d_model
      -> + token [CLS] + positional embedding (posisi frekuensi + posisi waktu)
      -> Transformer encoder (self-attention antar patch)
      -> kepala regresi dari token [CLS] -> 1 angka duty PWM

Asumsi sementara (cek lagi setelah protokol tim dibekukan):
    - X berbentuk [N, 64, waktu] atau [N, 1, 64, waktu];
    - y berupa duty (persen atau 0-255). Target distandarkan dari data latih,
      lalu prediksi dikembalikan ke satuan semula, jadi satuan y tidak perlu diubah di sini.
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
from src.protokol import data  # noqa: E402  (protokol tim yang dibekukan)

NIM = Path(__file__).resolve().parent.name     # nama folder = NIM
JALUR = "trf"                                   # cnn | tl | rnn | trf | ae

# ---- Hyperparameter awal (catat perubahan & alasannya di catatan.md) ----
PATCH_FREKUENSI = 8      # tinggi patch (pita mel)
PATCH_WAKTU = 8          # lebar patch (frame waktu)
D_MODEL = 64             # dimensi vektor tiap patch
JUMLAH_HEAD = 4          # head self-attention
JUMLAH_LAPIS = 2         # lapis encoder
D_FEEDFORWARD = 128
DROPOUT = 0.1
EPOCH = 15
BATCH = 32
LR = 1e-3
WEIGHT_DECAY = 0.01


class TransformerPatch(nn.Module):
    """Transformer encoder kecil di atas patch log-mel (gaya ViT/AST)."""

    def __init__(self, n_mel: int, n_waktu: int):
        super().__init__()
        if n_mel % PATCH_FREKUENSI:
            raise ValueError(f"Jumlah pita mel ({n_mel}) harus habis dibagi PATCH_FREKUENSI ({PATCH_FREKUENSI})")
        self.n_patch_f = n_mel // PATCH_FREKUENSI
        self.n_patch_t = -(-n_waktu // PATCH_WAKTU)          # pembulatan ke atas; sisa waktu di-pad
        self.n_waktu_pad = self.n_patch_t * PATCH_WAKTU

        # Patch embedding: Conv2d dengan kernel = stride = ukuran patch
        # sama dengan memotong patch lalu memproyeksikannya secara linear.
        self.patch_embed = nn.Conv2d(1, D_MODEL, kernel_size=(PATCH_FREKUENSI, PATCH_WAKTU),
                                     stride=(PATCH_FREKUENSI, PATCH_WAKTU))
        self.cls = nn.Parameter(torch.zeros(1, 1, D_MODEL))
        # Positional embedding terpisah untuk sumbu frekuensi dan waktu:
        # model perlu tahu patch ini berada di frekuensi berapa (penting untuk nada kipas).
        self.pos_f = nn.Parameter(torch.zeros(1, self.n_patch_f, 1, D_MODEL))
        self.pos_t = nn.Parameter(torch.zeros(1, 1, self.n_patch_t, D_MODEL))
        self.pos_cls = nn.Parameter(torch.zeros(1, 1, D_MODEL))
        for p in (self.cls, self.pos_f, self.pos_t, self.pos_cls):
            nn.init.trunc_normal_(p, std=0.02)

        lapis = nn.TransformerEncoderLayer(D_MODEL, JUMLAH_HEAD, D_FEEDFORWARD, DROPOUT,
                                           batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(lapis, JUMLAH_LAPIS, enable_nested_tensor=False)
        self.kepala = nn.Sequential(nn.LayerNorm(D_MODEL), nn.Linear(D_MODEL, 1))

    def forward(self, x):                                   # x: [B, 1, 64, waktu]
        sisa = self.n_waktu_pad - x.shape[-1]
        if sisa > 0:
            x = nn.functional.pad(x, (0, sisa))
        x = x[..., : self.n_waktu_pad]
        p = self.patch_embed(x)                             # [B, D, n_patch_f, n_patch_t]
        p = p.permute(0, 2, 3, 1) + self.pos_f + self.pos_t  # [B, n_patch_f, n_patch_t, D]
        p = p.flatten(1, 2)                                 # [B, jumlah_patch, D]
        cls = (self.cls + self.pos_cls).expand(len(p), -1, -1)
        z = self.encoder(torch.cat([cls, p], dim=1))
        return self.kepala(z[:, 0]).squeeze(1)              # baca dari token [CLS]


def siapkan_fitur(X) -> np.ndarray:
    X = np.asarray(X, dtype=np.float32)
    if X.ndim == 3:
        X = X[:, None, :, :]
    if X.ndim != 4 or X.shape[1] != 1:
        raise ValueError(f"X harus berbentuk [N, 64, waktu] atau [N, 1, 64, waktu], didapat {X.shape}")
    if not np.isfinite(X).all():
        raise ValueError("Fitur mengandung NaN/Inf")
    return X


def latih_dan_prediksi(seed: int, final: bool) -> tuple[np.ndarray, np.ndarray | None]:
    torch.manual_seed(seed)
    np.random.seed(seed)
    Xtr, ytr, Xva, _, Xte, _ = data.muat()
    Xtr, Xva = siapkan_fitur(Xtr), siapkan_fitur(Xva)
    ytr = np.asarray(ytr, dtype=np.float32).reshape(-1)
    if len(Xtr) == 0 or len(Xva) == 0 or len(ytr) != len(Xtr):
        raise ValueError("Data latih/validasi kosong atau jumlah label latih tidak cocok")

    # Normalisasi fitur per pita mel, statistik dari data latih saja (aturan kartu kasus).
    mean = Xtr.mean(axis=(0, 3), keepdims=True)
    std = np.maximum(Xtr.std(axis=(0, 3), keepdims=True), 1e-6)
    Xtr, Xva = (Xtr - mean) / std, (Xva - mean) / std
    # Target distandarkan agar skala loss wajar (y bisa persen atau 0-255).
    y_mean, y_std = float(ytr.mean()), float(max(ytr.std(), 1e-6))
    y_min, y_max = float(ytr.min()), float(ytr.max())
    ytr_z = (ytr - y_mean) / y_std

    gen = torch.Generator().manual_seed(seed)
    batches = DataLoader(TensorDataset(torch.from_numpy(Xtr), torch.from_numpy(ytr_z)),
                         batch_size=BATCH, shuffle=True, generator=gen)
    model = TransformerPatch(n_mel=Xtr.shape[2], n_waktu=Xtr.shape[3])
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    jadwal = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCH * len(batches))
    n_param = sum(p.numel() for p in model.parameters())
    print(f"[{NIM}] Transformer patch {PATCH_FREKUENSI}x{PATCH_WAKTU}, "
          f"{model.n_patch_f * model.n_patch_t} patch, {n_param:,} parameter", flush=True)

    for ep in range(EPOCH):
        model.train()
        total = 0.0
        for x, y in batches:
            opt.zero_grad()
            loss = nn.functional.mse_loss(model(x), y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)   # menjaga pelatihan Transformer stabil
            opt.step()
            jadwal.step()
            total += loss.item() * len(x)
        print(f"  epoch {ep + 1:2d}/{EPOCH}  loss latih (terstandar) {total / len(Xtr):.4f}", flush=True)

    def prediksi(X: np.ndarray) -> np.ndarray:
        model.eval()
        with torch.no_grad():
            z = np.concatenate([model(x).numpy() for x in DataLoader(torch.from_numpy(X), batch_size=128)])
        return np.clip(z * y_std + y_mean, y_min, y_max).astype(np.float32)

    pred_val = prediksi(Xva)
    pred_test = None
    if final:
        if Xte is None:
            raise ValueError("Data uji tidak tersedia untuk --final")
        pred_test = prediksi((siapkan_fitur(Xte) - mean) / std)
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
