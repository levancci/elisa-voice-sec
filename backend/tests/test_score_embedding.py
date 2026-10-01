import numpy as np

from tools.score_embedding import waveform_to_features


def test_waveform_features_have_eighty_bins() -> None:
    features = waveform_to_features(np.zeros(16_000, dtype=np.float32))

    assert features.shape[1] == 80
    assert features.shape[0] > 0
    assert np.isfinite(features).all()