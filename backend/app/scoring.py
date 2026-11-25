"""Shared voiceprint aggregation and cosine scoring."""

from __future__ import annotations

import numpy as np


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
    return vector / max(float(np.linalg.norm(vector)), 1e-12)


def aggregate_voiceprint(embeddings: list[np.ndarray] | np.ndarray) -> np.ndarray:
    matrix = np.asarray(embeddings, dtype=np.float32)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("at least one one-dimensional embedding is required")
    return normalize_embedding(np.mean(matrix, axis=0))


def cosine_similarity(attempt_embedding: np.ndarray, voiceprint: np.ndarray) -> float:
    attempt = normalize_embedding(attempt_embedding)
    profile = normalize_embedding(voiceprint)
    if attempt.shape != profile.shape:
        raise ValueError(f"embedding shape mismatch: {attempt.shape} != {profile.shape}")
    return float(np.dot(attempt, profile))
