"""Application service for enrollment and challenge-response verification."""

from __future__ import annotations

import logging
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import numpy as np

from .audio import AudioRejected, decode_audio
from .config import BackendConfig
from .models import DigitModel, EmbeddingModel
from .scoring import aggregate_voiceprint, cosine_similarity
from .storage import ChallengeRecord, SQLiteStorage


class ServiceError(ValueError):
    def __init__(self, reason_code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.status_code = status_code


@dataclass(frozen=True)
class EnrollmentSample:
    digits: str
    audio: bytes


class VoiceSecurityService:
    def __init__(self, config: BackendConfig, embedding: EmbeddingModel, digits: DigitModel, storage: SQLiteStorage, logger: logging.Logger | None = None) -> None:
        self.config = config
        self.embedding = embedding
        self.digits = digits
        self.storage = storage
        self.logger = logger or logging.getLogger(config.logger_name)

    def enroll(self, user_id: str, samples: list[EnrollmentSample]) -> dict[str, object]:
        if len(samples) < self.config.minimum_enrollment_samples:
            raise ServiceError("not_enough_enrollment_samples", "More enrollment samples are required.")
        if any(len(sample.digits) != self.config.challenge_length for sample in samples):
            raise ServiceError("invalid_enrollment_prompt", "Every enrollment prompt must have four digits.")
        if set("".join(sample.digits for sample in samples)) != set("0123456789"):
            raise ServiceError("enrollment_digits_incomplete", "Enrollment prompts must cover all ten digits.")
        embeddings: list[np.ndarray] = []
        for sample_index, sample in enumerate(samples, start=1):
            try:
                waveform = self._decode(sample.audio)
            except AudioRejected as exc:
                raise ServiceError(exc.reason_code, str(exc)) from exc
            recognized = self.digits.recognize(waveform, self.config.sample_rate_hz)
            if recognized != sample.digits:
                raise ServiceError(
                    "enrollment_digits_mismatch",
                    f"Sample {sample_index}: expected {sample.digits}, recognized {recognized or 'no digits'}. Please retry enrollment.",
                )
            embeddings.append(self.embedding.embed(waveform))
        matrix = np.asarray(embeddings, dtype=np.float32)
        voiceprint = aggregate_voiceprint(matrix)
        self.storage.save_enrollment(user_id, matrix, voiceprint, self.embedding.version, self.embedding.sha256)
        return {"user_id": user_id, "sample_count": len(samples), "model_version": self.embedding.version}

    def challenge(self, user_id: str) -> dict[str, object]:
        digits = "".join(str(secrets.randbelow(10)) for _ in range(self.config.challenge_length))
        record = ChallengeRecord(secrets.token_urlsafe(18), user_id, digits, time.time() + self.config.challenge_ttl_seconds, False)
        self.storage.save_challenge(record)
        return {"challenge_id": record.challenge_id, "digits": digits, "expires_at": record.expires_at}

    def verify(self, user_id: str, challenge_id: str, audio: bytes) -> dict[str, object]:
        started = time.perf_counter()
        record = self.storage.get_challenge(challenge_id)
        if record is None:
            raise ServiceError("challenge_unknown", "Challenge was not found.")
        if record.user_id != user_id:
            raise ServiceError("challenge_user_mismatch", "Challenge belongs to another user.")
        if record.used:
            raise ServiceError("challenge_reused", "Challenge has already been used.")
        if record.expires_at <= time.time():
            raise ServiceError("challenge_expired", "Challenge has expired.")
        if not self.storage.mark_challenge_used(challenge_id):
            raise ServiceError("challenge_reused", "Challenge has already been used.")
        try:
            waveform = self._decode(audio)
        except AudioRejected as exc:
            self._log_attempt(started, {"decision": "denied", "reason_codes": [exc.reason_code], "challenge_id": challenge_id})
            raise ServiceError(exc.reason_code, str(exc)) from exc
        with ThreadPoolExecutor(max_workers=2) as executor:
            digit_future = executor.submit(self.digits.recognize, waveform, self.config.sample_rate_hz)
            embedding_future = executor.submit(self.embedding.embed, waveform)
            recognized = digit_future.result()
            attempt_embedding = embedding_future.result()
        enrolled = self.storage.get_enrollment(user_id)
        if enrolled is None:
            raise ServiceError("not_enrolled", "User has no enrollment.")
        voiceprint, model_version, model_hash = enrolled
        if model_version != self.embedding.version or model_hash != self.embedding.sha256:
            raise ServiceError("model_version_mismatch", "Enrollment requires the active model version.")
        score = cosine_similarity(attempt_embedding, voiceprint)
        digit_match = recognized == record.digits
        decision = digit_match and score >= self.config.speaker_threshold
        reasons = [] if decision else (["digits_mismatch"] if not digit_match else []) + (["speaker_below_threshold"] if score < self.config.speaker_threshold else [])
        result = {"digit_match": digit_match, "recognized_digits": recognized, "speaker_score": score, "threshold": self.config.speaker_threshold, "decision": "pass" if decision else "denied", "reason_codes": reasons, "model_versions": {"embedding": self.embedding.version, "digit": self.digits.version}, "model_hashes": {"embedding": self.embedding.sha256, "digit": self.digits.sha256}, "latency_ms": (time.perf_counter() - started) * 1000}
        self._log_attempt(started, result)
        return result

    def _decode(self, audio: bytes) -> np.ndarray:
        return decode_audio(audio, self.config)

    def _log_attempt(self, started: float, payload: dict[str, object]) -> None:
        payload.setdefault("latency_ms", (time.perf_counter() - started) * 1000)
        self.storage.log_attempt(time.time(), payload)
        self.logger.info("voice_attempt %s", payload)