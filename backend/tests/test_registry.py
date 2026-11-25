from pathlib import Path

from backend.app.registry import ModelRegistry, resolve_model


def test_registry_uses_ecapa_int8_as_default() -> None:
    registry = ModelRegistry(Path("models/registry.yaml"))

    default_model = registry.default_embedding()
    assert default_model.name == "ecapa-int8"
    assert default_model.kind == "speaker-embedding"
    assert default_model.path.endswith("ecapa.int8.onnx")

    resolved = resolve_model("ecapa-int8", registry)
    assert resolved.name == "ecapa-int8"
    assert resolved.status == "provisional-development-default"
