import base64
import io
import socket
from dataclasses import replace
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend.app.api import create_api
from backend.app.config import load_config
from backend.app.service import VoiceSecurityService
from backend.app.storage import SQLiteStorage
from main import create_app


class FakeEmbedding:
    version = "fake-embedding-v1"
    sha256 = "fake-embedding-sha256"

    def embed(self, waveform: np.ndarray) -> np.ndarray:
        return np.asarray([1.0, 0.0], dtype=np.float32)


class FakeDigits:
    version = "fake-digits-v1"
    sha256 = "fake-digits-sha256"

    def __init__(self) -> None:
        self.enrollment_responses = iter(["0123", "4567", "8901"])
        self.verification_digits = ""

    def recognize(self, waveform: np.ndarray, sample_rate: int) -> str:
        if self.verification_digits:
            return self.verification_digits
        return next(self.enrollment_responses)


def _audio_base64() -> str:
    buffer = io.BytesIO()
    sf.write(buffer, np.full(16_000, 0.05, dtype=np.float32), 16_000, format="WAV")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _client(tmp_path, embedding=None, digits=None) -> tuple[TestClient, FakeDigits, FakeEmbedding]:
    config = replace(load_config(), sqlite_path=tmp_path / "elisa.sqlite3")
    fake_embedding = embedding or FakeEmbedding()
    fake_digits = digits or FakeDigits()
    service = VoiceSecurityService(config, fake_embedding, fake_digits, SQLiteStorage(config.sqlite_path))
    return TestClient(create_api(service)), fake_digits, fake_embedding


def _enroll(client: TestClient, encoded_audio: str, user_id: str = "alice") -> None:
    response = client.post(
        "/enroll",
        json={
            "user_id": user_id,
            "audio_samples": [
                {"digits": digits, "audio_base64": encoded_audio}
                for digits in ("0123", "4567", "8901")
            ],
        },
    )
    assert response.status_code == 200, response.text


def test_api_full_cycle_is_offline_and_single_use(monkeypatch, tmp_path) -> None:
    original_connect = socket.socket.connect

    def fail_network(*args, **kwargs):
        address = args[1] if len(args) > 1 else kwargs.get("address")
        host = address[0] if isinstance(address, tuple) else ""
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise AssertionError("inference attempted an outbound network connection")
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", fail_network)
    config = replace(load_config(), sqlite_path=tmp_path / "elisa.sqlite3")
    digits = FakeDigits()
    service = VoiceSecurityService(config, FakeEmbedding(), digits, SQLiteStorage(config.sqlite_path))
    client = TestClient(create_api(service))
    encoded_audio = _audio_base64()
    assert client.get("/").status_code == 200

    enrollment = client.post(
        "/enroll",
        json={
            "user_id": "alice",
            "audio_samples": [
                {"digits": "0123", "audio_base64": encoded_audio},
                {"digits": "4567", "audio_base64": encoded_audio},
                {"digits": "8901", "audio_base64": encoded_audio},
            ],
        },
    )
    assert enrollment.status_code == 200, enrollment.text

    challenge = client.post("/challenge", json={"user_id": "alice"})
    assert challenge.status_code == 200
    digits.verification_digits = challenge.json()["digits"]
    verification = client.post(
        "/verify",
        json={
            "user_id": "alice",
            "challenge_id": challenge.json()["challenge_id"],
            "audio_base64": encoded_audio,
        },
    )
    assert verification.status_code == 200
    assert verification.json()["decision"] == "pass"
    assert verification.json()["digit_match"] is True
    assert verification.json()["model_versions"] == {"embedding": "fake-embedding-v1", "digit": "fake-digits-v1"}

    reused = client.post(
        "/verify",
        json={
            "user_id": "alice",
            "challenge_id": challenge.json()["challenge_id"],
            "audio_base64": encoded_audio,
        },
    )
    assert reused.status_code == 400
    assert reused.json()["detail"]["reason_code"] == "challenge_reused"


def test_short_enrollment_audio_is_rejected_before_inference(tmp_path) -> None:
    class CountingEmbedding(FakeEmbedding):
        calls = 0

        def embed(self, waveform: np.ndarray) -> np.ndarray:
            self.calls += 1
            return super().embed(waveform)

    class CountingDigits(FakeDigits):
        calls = 0

        def recognize(self, waveform: np.ndarray, sample_rate: int) -> str:
            self.calls += 1
            return super().recognize(waveform, sample_rate)

    embedding = CountingEmbedding()
    digits = CountingDigits()
    config = replace(load_config(), sqlite_path=tmp_path / "elisa.sqlite3")
    service = VoiceSecurityService(config, embedding, digits, SQLiteStorage(config.sqlite_path))
    client = TestClient(create_api(service))
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros(4_000, dtype=np.float32), 16_000, format="WAV")

    response = client.post(
        "/enroll",
        json={
            "user_id": "alice",
            "audio_samples": [
                {"digits": digits, "audio_base64": base64.b64encode(buffer.getvalue()).decode("ascii")}
                for digits in ("0123", "4567", "8901")
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["reason_code"] == "audio_too_short"
    assert embedding.calls == 0
    assert digits.calls == 0


def test_wrong_digit_is_rejected(tmp_path) -> None:
    client, digits, _ = _client(tmp_path)
    encoded_audio = _audio_base64()
    _enroll(client, encoded_audio)
    challenge = client.post("/challenge", json={"user_id": "alice"}).json()
    digits.verification_digits = "0000" if challenge["digits"] != "0000" else "1111"

    response = client.post("/verify", json={"user_id": "alice", "challenge_id": challenge["challenge_id"], "audio_base64": encoded_audio})

    assert response.status_code == 200
    assert response.json()["decision"] == "denied"
    assert response.json()["reason_codes"] == ["digits_mismatch"]


def test_wrong_speaker_is_rejected(tmp_path) -> None:
    class WrongSpeakerEmbedding(FakeEmbedding):
        enrolled = False

        def embed(self, waveform: np.ndarray) -> np.ndarray:
            if self.enrolled:
                return np.asarray([0.0, 1.0], dtype=np.float32)
            return super().embed(waveform)

    embedding = WrongSpeakerEmbedding()
    client, digits, _ = _client(tmp_path, embedding=embedding)
    encoded_audio = _audio_base64()
    _enroll(client, encoded_audio)
    embedding.enrolled = True
    challenge = client.post("/challenge", json={"user_id": "alice"}).json()
    digits.verification_digits = challenge["digits"]

    response = client.post("/verify", json={"user_id": "alice", "challenge_id": challenge["challenge_id"], "audio_base64": encoded_audio})

    assert response.status_code == 200
    assert response.json()["decision"] == "denied"
    assert response.json()["reason_codes"] == ["speaker_below_threshold"]


def test_expired_challenge_is_rejected(tmp_path) -> None:
    client, _, _ = _client(tmp_path)
    challenge = client.post("/challenge", json={"user_id": "alice"}).json()
    with SQLiteStorage(tmp_path / "elisa.sqlite3")._connect() as connection:
        connection.execute("UPDATE challenges SET expires_at = 0 WHERE challenge_id = ?", (challenge["challenge_id"],))

    response = client.post("/verify", json={"user_id": "alice", "challenge_id": challenge["challenge_id"], "audio_base64": _audio_base64()})

    assert response.status_code == 400
    assert response.json()["detail"]["reason_code"] == "challenge_expired"


def test_wrong_user_challenge_is_rejected(tmp_path) -> None:
    client, _, _ = _client(tmp_path)
    challenge = client.post("/challenge", json={"user_id": "alice"}).json()

    response = client.post("/verify", json={"user_id": "bob", "challenge_id": challenge["challenge_id"], "audio_base64": _audio_base64()})

    assert response.status_code == 400
    assert response.json()["detail"]["reason_code"] == "challenge_user_mismatch"


def test_challenge_uses_csprng_and_configured_length(tmp_path) -> None:
    client, _, _ = _client(tmp_path)

    challenges = [client.post("/challenge", json={"user_id": "alice"}).json() for _ in range(20)]

    assert all(len(challenge["digits"]) == load_config().challenge_length for challenge in challenges)
    assert len({challenge["digits"] for challenge in challenges}) > 1


def test_real_models_complete_offline_cycle_with_non_loopback_blocked(monkeypatch, tmp_path) -> None:
    original_connect = socket.socket.connect

    def block_non_loopback(*args, **kwargs):
        address = args[1] if len(args) > 1 else kwargs.get("address")
        host = address[0] if isinstance(address, tuple) else ""
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise AssertionError("real inference attempted an outbound network connection")
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", block_non_loopback)
    import backend.app.service as service_module

    challenge_digits = iter([7, 6, 3, 4])
    monkeypatch.setattr(service_module.secrets, "randbelow", lambda _: next(challenge_digits))
    app = create_app(storage_path=tmp_path / "real.sqlite3")
    client = TestClient(app)
    data_root = Path("data/phase2/p02/quiet")
    enrollment = []
    for path in sorted((data_root / "enrollment").glob("*.wav")):
        enrollment.append({"digits": path.stem.split("_", 1)[1], "audio_base64": base64.b64encode(path.read_bytes()).decode("ascii")})

    enrolled = client.post("/enroll", json={"user_id": "p02", "audio_samples": enrollment})
    assert enrolled.status_code == 200, enrolled.text
    challenge = client.post("/challenge", json={"user_id": "p02"})
    assert challenge.json()["digits"] == "7634"
    verification_audio = base64.b64encode((data_root / "verification" / "01_7634.wav").read_bytes()).decode("ascii")

    verified = client.post("/verify", json={"user_id": "p02", "challenge_id": challenge.json()["challenge_id"], "audio_base64": verification_audio})

    assert verified.status_code == 200, verified.text
    assert verified.json()["digit_match"] is True
    assert verified.json()["model_versions"]["embedding"] == "local-onnx-qdq-conv-only-v1"
    assert verified.json()["model_versions"]["digit"] == "vosk-model-small-en-us-0.15"