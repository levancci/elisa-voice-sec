from pathlib import Path

from backend.app.api import create_api
from backend.app.config import load_config
from backend.app.models import OnnxEmbeddingModel, VoskDigitModel
from backend.app.service import VoiceSecurityService
from backend.app.storage import SQLiteStorage


def create_app(config_path: str | Path = "config/default.yaml", storage_path: str | Path | None = None):
    config = load_config(config_path)
    if storage_path is not None:
        from dataclasses import replace

        config = replace(config, sqlite_path=Path(storage_path))
    embedding = OnnxEmbeddingModel.from_config(config)
    digits = VoskDigitModel.from_config(config)
    return create_api(VoiceSecurityService(config, embedding, digits, SQLiteStorage(config.sqlite_path)))


app = create_app()


def main() -> None:
    print("Elisa voice security prototype")


if __name__ == "__main__":
    main()
