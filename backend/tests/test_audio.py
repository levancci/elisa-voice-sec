import io

import numpy as np
import soundfile as sf
import pytest

from backend.app.audio import AudioRejected, decode_audio
from backend.app.config import load_config


def _wav(samples: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate, format="WAV")
    return buffer.getvalue()


def test_decode_audio_resamples_stereo_and_rejects_silence() -> None:
    config = load_config()
    samples = np.full((8_000, 2), 0.05, dtype=np.float32)

    decoded = decode_audio(_wav(samples, 8_000), config)

    assert decoded.dtype == np.float32
    assert decoded.size == 16_000

    with pytest.raises(AudioRejected, match="enough speech energy"):
        decode_audio(_wav(np.zeros(16_000, dtype=np.float32), 16_000), config)