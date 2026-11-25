"""Decode and validate audio before model inference."""

from __future__ import annotations

import io

import numpy as np
import soundfile as sf

from .config import BackendConfig


class AudioRejected(ValueError):
    """Raised when audio fails a pre-inference validation."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def decode_audio(audio: bytes, config: BackendConfig) -> np.ndarray:
    try:
        waveform, sample_rate = sf.read(io.BytesIO(audio), dtype="float32", always_2d=False)
    except Exception as exc:
        raise AudioRejected("invalid_audio", "Audio could not be decoded.") from exc
    if waveform.ndim == 2:
        waveform = waveform.mean(axis=1)
    if waveform.ndim != 1 or waveform.size == 0:
        raise AudioRejected("invalid_audio", "Audio must contain a non-empty mono or stereo signal.")
    waveform = np.asarray(waveform, dtype=np.float32)
    if sample_rate != config.sample_rate_hz:
        source_times = np.arange(waveform.size, dtype=np.float64) / sample_rate
        target_size = max(1, round(waveform.size * config.sample_rate_hz / sample_rate))
        target_times = np.arange(target_size, dtype=np.float64) / config.sample_rate_hz
        waveform = np.interp(target_times, source_times, waveform).astype(np.float32)
    peak = float(np.max(np.abs(waveform)))
    if peak > 1.0:
        waveform = waveform / peak
    duration = waveform.size / config.sample_rate_hz
    if duration < config.minimum_speech_seconds:
        raise AudioRejected("audio_too_short", "Audio is shorter than the configured minimum.")
    if duration > config.maximum_speech_seconds:
        raise AudioRejected("audio_too_long", "Audio exceeds the configured maximum.")
    if float(np.sqrt(np.mean(np.square(waveform)))) < config.speech_rms_threshold:
        raise AudioRejected("silence", "Audio does not contain enough speech energy.")
    return waveform