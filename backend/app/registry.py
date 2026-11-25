"""Registry-backed model resolution for the Phase 4 backend."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelEntry:
    """A single model entry in the registry."""

    name: str
    kind: str
    version: str
    path: str
    sha256: str
    status: str
    requires_reenrollment_on_change: bool = True
    hash_path: str | None = None

    @property
    def resolved_path(self) -> Path:
        return Path(self.path)

    @property
    def resolved_hash_path(self) -> Path:
        return Path(self.hash_path or self.path)


class ModelRegistry:
    """Load and resolve model metadata from the repository registry."""

    def __init__(self, registry_path: str | Path) -> None:
        self.path = Path(registry_path)
        self._data = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError:
            yaml = None

        raw_text = self.path.read_text(encoding="utf-8")
        if yaml is not None:
            data = yaml.safe_load(raw_text) or {}
            if not isinstance(data, dict):
                raise ValueError(f"Registry at {self.path} did not parse to a dictionary.")
            return data

        return _parse_simple_yaml(raw_text)

    def entries(self) -> dict[str, ModelEntry]:
        model_entries = self._data.get("models", [])
        entries: dict[str, ModelEntry] = {}
        for entry in model_entries:
            if not isinstance(entry, dict):
                continue
            model = ModelEntry(
                name=str(entry["name"]),
                kind=str(entry.get("kind", "unknown")),
                version=str(entry.get("version", "unknown")),
                path=str(entry.get("path", "")),
                sha256=str(entry.get("sha256", "")),
                status=str(entry.get("status", "unknown")),
                requires_reenrollment_on_change=bool(
                    entry.get("requires_reenrollment_on_change", True)
                ),
                hash_path=str(entry["hash_path"]) if entry.get("hash_path") else None,
            )
            entries[model.name] = model
        return entries

    def default_embedding(self) -> ModelEntry:
        default_name = str(self._data.get("default_embedding", ""))
        return self.get(default_name)

    def get(self, name: str) -> ModelEntry:
        entries = self.entries()
        if name not in entries:
            raise KeyError(f"Model '{name}' is not defined in the registry.")
        return entries[name]

    def available_models(self) -> list[str]:
        return sorted(self.entries())

    def verify_hash(self, name: str, root: str | Path = ".") -> ModelEntry:
        model = self.get(name)
        target = Path(root) / model.resolved_hash_path
        if not target.is_file():
            raise FileNotFoundError(f"Model artifact for '{name}' was not found: {target}")
        digest = hashlib.sha256(target.read_bytes()).hexdigest().upper()
        if digest != model.sha256.upper():
            raise ValueError(f"SHA-256 mismatch for '{name}': expected {model.sha256}, got {digest}")
        return model


def resolve_model(name: str, registry: ModelRegistry | None = None) -> ModelEntry:
    """Resolve a model entry by name using the default registry file when needed."""
    if registry is None:
        registry = ModelRegistry("models/registry.yaml")
    return registry.get(name)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Support the repository's compact registry format without requiring PyYAML."""
    data: dict[str, Any] = {}
    list_buffer: list[dict[str, Any]] | None = None
    current: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        if line.startswith("default_embedding:"):
            data["default_embedding"] = line.split(":", 1)[1].strip().strip("\"'")
            continue

        if line.startswith("models:"):
            list_buffer = []
            data["models"] = list_buffer
            continue

        if line.startswith("  - ") and list_buffer is not None:
            if current is not None:
                list_buffer.append(current)
            current = {}
            remainder = line[4:].strip()
            if remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = _yaml_scalar(value.strip())
            continue

        if line.startswith("    ") and current is not None:
            key, value = line.strip().split(":", 1)
            current[key] = _yaml_scalar(value.strip())
            continue

        if line.startswith("  ") and not line.startswith("    ") and list_buffer is not None:
            if current is not None:
                list_buffer.append(current)
            current = None

    if current is not None and list_buffer is not None:
        list_buffer.append(current)

    return data


def _yaml_scalar(value: str) -> Any:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith("\"") and value.endswith("\""):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value
