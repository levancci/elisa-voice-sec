"""SpeechBrain-compatible ECAPA feature extraction."""

from __future__ import annotations

import numpy as np
import torch
from speechbrain.lobes.features import Fbank
from speechbrain.processing.features import InputNormalization


class EcapaFrontend:
    """Reproduce the saved ECAPA hyperparams without loading its classifier."""

    def __init__(self) -> None:
        self.compute_features = Fbank(n_mels=80)
        self.mean_var_norm = InputNormalization(norm_type="sentence", std_norm=False)

    def __call__(self, waveform: np.ndarray) -> np.ndarray:
        signal = torch.from_numpy(np.asarray(waveform, dtype=np.float32)).unsqueeze(0)
        with torch.no_grad():
            features = self.compute_features(signal)
            features = self.mean_var_norm(features, torch.ones(1))
        return features[0].cpu().numpy().astype(np.float32)
