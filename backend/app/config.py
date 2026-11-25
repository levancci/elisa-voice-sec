"""Configuration loading for the offline backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class BackendConfig:
    challenge_length: int
    challenge_ttl_seconds: int
    minimum_enrollment_samples: int
    recommended_enrollment_samples: int
    sample_rate_hz: int
    minimum_speech_seconds: float
    maximum_speech_seconds: float
    speech_rms_threshold: float
    speaker_threshold: float
    registry_path: Path
    embedding_name: str
    digit_name: str
    sqlite_path: Path
    logger_name: str


def load_config(path: str | Path = "config/default.yaml") -> BackendConfig:
    raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    challenge = raw["challenge"]
    enrollment = raw["enrollment"]
    audio = raw["audio"]
    models = raw["models"]
    storage = raw["storage"]
    return BackendConfig(
        challenge_length=int(challenge["length"]),
        challenge_ttl_seconds=int(challenge["ttl_seconds"]),
        minimum_enrollment_samples=int(enrollment["minimum_samples"]),
        recommended_enrollment_samples=int(enrollment["recommended_samples"]),
        sample_rate_hz=int(audio["sample_rate_hz"]),
        minimum_speech_seconds=float(audio["minimum_speech_seconds"]),
        maximum_speech_seconds=float(audio["maximum_speech_seconds"]),
        speech_rms_threshold=float(audio["speech_rms_threshold"]),
        speaker_threshold=float(raw["scoring"]["speaker_threshold"]),
        registry_path=Path(models["registry_path"]),
        embedding_name=str(models["embedding_name"]),
        digit_name=str(models["digit_name"]),
        sqlite_path=Path(storage["sqlite_path"]),
        logger_name=str(raw["logging"]["name"]),
    )