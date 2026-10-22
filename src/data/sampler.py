"""
LungRay Weighted Multi-Task Batch Sampler (src/data/sampler.py)
==============================================================
Inviolable Constraint (Ràng buộc 5 - Anti-Task Starvation):
- The NIH dataset (112k) is massive compared to COVIDx (16k+) and TB (4.2k).
- A uniform random sampling would cause severe task starvation for Head B/C.
- Mandatory: WeightedMultiTaskBatchSampler guarantees a fixed ratio within EVERY batch:
    * 60% NIH ChestX-ray14
    * 25% COVIDx CXR-4
    * 15% Tuberculosis (TB) Database

For batch_size=16 the exact integer allocation is 10 NIH / 4 COVIDx / 2 TB
(closest achievable composition to 60:25:15). Smaller task pools are
deterministically oversampled with fresh shuffles when they run out.
"""
import math
from typing import Iterator, List, Sequence

import numpy as np
from torch.utils.data import Sampler


class WeightedMultiTaskBatchSampler(Sampler[List[int]]):
    """Yields batches composed of a fixed task ratio (60% NIH, 25% COVIDx, 15% TB)."""

    def __init__(
        self,
        nih_indices: Sequence[int],
        covid_indices: Sequence[int],
        tb_indices: Sequence[int],
        batch_size: int = 16,
        ratios: Sequence[float] = (0.60, 0.25, 0.15),
        shuffle: bool = True,
        seed: int = 42,
    ):
        if batch_size < 3:
            raise ValueError(
                f"batch_size must be at least 3 to include all three tasks, got {batch_size}."
            )
        if len(ratios) != 3:
            raise ValueError(f"ratios must contain exactly 3 values, got {ratios}.")
        if not (len(nih_indices) and len(covid_indices) and len(tb_indices)):
            raise ValueError(
                "WeightedMultiTaskBatchSampler requires non-empty index pools for all 3 tasks "
                f"(NIH={len(nih_indices)}, COVIDx={len(covid_indices)}, TB={len(tb_indices)})."
            )

        self.nih_indices = np.asarray(nih_indices)
        self.covid_indices = np.asarray(covid_indices)
        self.tb_indices = np.asarray(tb_indices)

        self.batch_size = batch_size
        self.shuffle = shuffle
        self.seed = seed
        self.rng = np.random.default_rng(seed)

        # Largest-remainder integer allocation, e.g. 16 -> (10, 4, 2).
        quotas = np.asarray(ratios, dtype=float)
        quotas = quotas / quotas.sum() * batch_size
        counts = np.floor(quotas).astype(int)
        remainder = batch_size - int(counts.sum())
        if remainder > 0:
            fractional_order = np.argsort(-(quotas - counts))
            counts[fractional_order[:remainder]] += 1
        elif remainder < 0:
            counts[np.argsort(counts)[: -remainder]] -= 1

        self.n_nih = max(1, int(counts[0]))
        self.n_covid = max(1, int(counts[1]))
        self.n_tb = max(1, batch_size - self.n_nih - self.n_covid)
        if self.n_nih + self.n_covid + self.n_tb != batch_size:
            self.n_nih = batch_size - self.n_covid - self.n_tb

        # One epoch spans the primary (largest) dataset.
        self.num_batches = max(1, math.ceil(len(self.nih_indices) / self.n_nih))

    def __len__(self) -> int:
        return self.num_batches

    def _draw(
        self, pool: np.ndarray, pointer: int, count: int
    ) -> tuple[List[int], int, np.ndarray]:
        """Draws ``count`` indices, cycling/reshuffling the pool when exhausted."""
        drawn: List[int] = []
        while len(drawn) < count:
            if pointer >= len(pool):
                pool = self.rng.permutation(pool) if self.shuffle else pool.copy()
                pointer = 0
            take = min(count - len(drawn), len(pool) - pointer)
            drawn.extend(pool[pointer:pointer + take].tolist())
            pointer += take
        return drawn, pointer, pool

    def __iter__(self) -> Iterator[List[int]]:
        nih_pool = self.rng.permutation(self.nih_indices) if self.shuffle else self.nih_indices.copy()
        covid_pool = self.rng.permutation(self.covid_indices) if self.shuffle else self.covid_indices.copy()
        tb_pool = self.rng.permutation(self.tb_indices) if self.shuffle else self.tb_indices.copy()

        nih_ptr = covid_ptr = tb_ptr = 0

        for _ in range(self.num_batches):
            nih_chunk, nih_ptr, nih_pool = self._draw(nih_pool, nih_ptr, self.n_nih)
            covid_chunk, covid_ptr, covid_pool = self._draw(covid_pool, covid_ptr, self.n_covid)
            tb_chunk, tb_ptr, tb_pool = self._draw(tb_pool, tb_ptr, self.n_tb)

            batch = nih_chunk + covid_chunk + tb_chunk
            if self.shuffle:
                self.rng.shuffle(batch)
            yield batch
