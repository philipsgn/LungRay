"""
LungRay Weighted Multi-Task Batch Sampler (src/data/sampler.py)
==============================================================
Inviolable Constraint (Ràng buộc 5 - Anti-Task Starvation):
- The NIH dataset (112k) is massive compared to COVID-19 (21k) and TB (4.2k).
- A uniform random sampling would result in 16 NIH : 3 COVID : 1 TB, causing severe task starvation.
- Mandatory: WeightedMultiTaskBatchSampler guarantees a fixed ratio within EVERY batch:
    * 60% NIH ChestX-ray14
    * 25% COVID-19 Radiography Database
    * 15% Tuberculosis (TB) Database
"""
import math
from typing import Iterator, List, Sequence
import numpy as np
import torch
from torch.utils.data import Sampler


class WeightedMultiTaskBatchSampler(Sampler[List[int]]):
    """
    Yields batches composed of a fixed task ratio (60% NIH, 25% COVID, 15% TB).
    """

    def __init__(
        self,
        nih_indices: Sequence[int],
        covid_indices: Sequence[int],
        tb_indices: Sequence[int],
        batch_size: int = 16,
        ratios: Sequence[float] = (0.60, 0.25, 0.15),
        shuffle: bool = True,
        seed: int = 42
    ):
        self.nih_indices = np.array(nih_indices)
        self.covid_indices = np.array(covid_indices)
        self.tb_indices = np.array(tb_indices)

        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Calculate exact counts per batch
        self.n_nih = max(1, int(round(batch_size * ratios[0])))
        self.n_covid = max(1, int(round(batch_size * ratios[1])))
        self.n_tb = batch_size - self.n_nih - self.n_covid
        if self.n_tb <= 0:
            self.n_tb = 1
            self.n_nih = batch_size - self.n_covid - self.n_tb

        # Number of batches per epoch is determined by primary dataset (NIH)
        self.num_batches = math.ceil(len(self.nih_indices) / self.n_nih)

    def __len__(self) -> int:
        return self.num_batches

    def __iter__(self) -> Iterator[List[int]]:
        # Shuffle indices if enabled
        if self.shuffle:
            nih_idx = self.rng.permutation(self.nih_indices)
            covid_idx = self.rng.permutation(self.covid_indices)
            tb_idx = self.rng.permutation(self.tb_indices)
        else:
            nih_idx = self.nih_indices.copy()
            covid_idx = self.covid_indices.copy()
            tb_idx = self.tb_indices.copy()

        nih_ptr = 0
        covid_ptr = 0
        tb_ptr = 0

        for _ in range(self.num_batches):
            # 1. Sample NIH chunk
            if nih_ptr + self.n_nih > len(nih_idx):
                # Reshuffle & wrap around
                remaining = nih_idx[nih_ptr:].tolist()
                nih_idx = self.rng.permutation(self.nih_indices) if self.shuffle else self.nih_indices.copy()
                needed = self.n_nih - len(remaining)
                nih_chunk = remaining + nih_idx[:needed].tolist()
                nih_ptr = needed
            else:
                nih_chunk = nih_idx[nih_ptr:nih_ptr + self.n_nih].tolist()
                nih_ptr += self.n_nih

            # 2. Sample COVID chunk (oversampled if needed)
            if covid_ptr + self.n_covid > len(covid_idx):
                remaining = covid_idx[covid_ptr:].tolist()
                covid_idx = self.rng.permutation(self.covid_indices) if self.shuffle else self.covid_indices.copy()
                needed = self.n_covid - len(remaining)
                covid_chunk = remaining + covid_idx[:needed].tolist()
                covid_ptr = needed
            else:
                covid_chunk = covid_idx[covid_ptr:covid_ptr + self.n_covid].tolist()
                covid_ptr += self.n_covid

            # 3. Sample TB chunk (oversampled if needed)
            if tb_ptr + self.n_tb > len(tb_idx):
                remaining = tb_idx[tb_ptr:].tolist()
                tb_idx = self.rng.permutation(self.tb_indices) if self.shuffle else self.tb_indices.copy()
                needed = self.n_tb - len(remaining)
                tb_chunk = remaining + tb_idx[:needed].tolist()
                tb_ptr = needed
            else:
                tb_chunk = tb_idx[tb_ptr:tb_ptr + self.n_tb].tolist()
                tb_ptr += self.n_tb

            # Combine batch and yield
            batch = nih_chunk + covid_chunk + tb_chunk
            if self.shuffle:
                self.rng.shuffle(batch)
            yield batch
