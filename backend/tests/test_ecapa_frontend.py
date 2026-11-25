from pathlib import Path

import numpy as np

from backend.app.audio import decode_audio
from backend.app.config import load_config
from backend.app.ecapa_frontend import EcapaFrontend


def test_ecapa_frontend_preserves_speechbrain_shape_and_scale() -> None:
    root = Path(__file__).parents[2]
    path = root / "data" / "phase2" / "p02" / "quiet" / "verification" / "01_7634.wav"

    features = EcapaFrontend()(decode_audio(path.read_bytes(), load_config()))

    assert features.shape == (401, 80)
    assert np.isclose(float(features.std()), 15.949265, atol=0.01)