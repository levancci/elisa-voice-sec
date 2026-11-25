"""Offline model adapters used by the backend service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

import numpy as np
import onnxruntime as ort
from vosk import KaldiRecognizer, Model

from .config import BackendConfig
from .ecapa_frontend import EcapaFrontend
from .registry import ModelEntry, ModelRegistry


class EmbeddingModel(Protocol):
    version: str
    sha256: str

    def embed(self, waveform: np.ndarray) -> np.ndarray: ...


class DigitModel(Protocol):
    version: str
    sha256: str

    def recognize(self, waveform: np.ndarray, sample_rate: int) -> str: ...


class OnnxEmbeddingModel:
    def __init__(self, entry: ModelEntry, root: str | Path = ".") -> None:
        self.entry = entry
        self.root = Path(root)
        self.registry_path = self.root / entry.resolved_path
        self.session = ort.InferenceSession(str(self.registry_path), providers=["CPUExecutionProvider"])
        self.frontend = EcapaFrontend()
        self.version = entry.version
        self.sha256 = entry.sha256

    @classmethod
    def from_config(cls, config: BackendConfig, root: str | Path = ".") -> "OnnxEmbeddingModel":
        registry = ModelRegistry(config.registry_path)
        entry = registry.verify_hash(config.embedding_name, root)
        return cls(entry, root)

    def embed(self, waveform: np.ndarray) -> np.ndarray:
        features = self.frontend(waveform)
        input_spec = self.session.get_inputs()[0]
        if len(input_spec.shape) == 3 and input_spec.shape[1] == 80:
            features = features.T
        inputs = {input_spec.name: features[None, :, :]}
        if len(self.session.get_inputs()) > 1:
            length_input = self.session.get_inputs()[1]
            length_dtype = np.float32 if "float" in length_input.type else np.int64
            inputs[length_input.name] = np.asarray([features.shape[-1]], dtype=length_dtype)
        output_name = next(
            (output.name for output in self.session.get_outputs() if output.name.lower().startswith("emb")),
            self.session.get_outputs()[0].name,
        )
        embedding = np.asarray(self.session.run([output_name], inputs)[0], dtype=np.float32).reshape(-1)
        return embedding / max(float(np.linalg.norm(embedding)), 1e-12)


_DIGIT_WORDS = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}


class VoskDigitModel:
    def __init__(self, entry: ModelEntry, root: str | Path = ".") -> None:
        self.entry = entry
        self.model = Model(str(Path(root) / entry.resolved_path))
        self.version = entry.version
        self.sha256 = entry.sha256

    @classmethod
    def from_config(cls, config: BackendConfig, root: str | Path = ".") -> "VoskDigitModel":
        registry = ModelRegistry(config.registry_path)
        entry = registry.verify_hash(config.digit_name, root)
        return cls(entry, root)

    def recognize(self, waveform: np.ndarray, sample_rate: int) -> str:
        grammar = json.dumps(list(_DIGIT_WORDS))
        recognizer = KaldiRecognizer(self.model, sample_rate, grammar)
        recognizer.AcceptWaveform((waveform * 32767).astype(np.int16).tobytes())
        result = json.loads(recognizer.FinalResult())
        return "".join(_DIGIT_WORDS[word] for word in result.get("text", "").split() if word in _DIGIT_WORDS)