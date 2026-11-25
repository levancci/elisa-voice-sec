"""Download the two model files Elisa needs and check them against models/registry.yaml.

Usage (from the repo root):

    uv run python tools/download_models.py

Both files land in models/weights/ (git-ignored). Each one is checked against
the SHA-256 in the registry, so a corrupted or swapped file fails loudly.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
import zipfile
from pathlib import Path

import yaml

# Prebuilt ECAPA int8 ONNX file, attached to the repo's GitHub Release.
# Maintainer: replace <your-username> with your GitHub username after you upload the file.
ECAPA_URL = "https://github.com/<your-username>/elisa/releases/download/v0.1.0/ecapa.int8.onnx"
VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

REGISTRY = Path("models/registry.yaml")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def expected_hash(name: str) -> str:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    for entry in registry["models"]:
        if entry["name"] == name:
            return str(entry["sha256"]).upper()
    raise KeyError(f"'{name}' is not in {REGISTRY}")


def download(url: str, target: Path) -> None:
    if "<your-username>" in url:
        sys.exit(
            "The ECAPA download link still has a placeholder in it.\n"
            "Pass the real link with --ecapa-url, or ask the repo owner."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url}")
    temp = target.with_suffix(target.suffix + ".part")
    urllib.request.urlretrieve(url, temp)
    temp.replace(target)


def fetch(name: str, url: str, target: Path) -> None:
    want = expected_hash(name)
    if target.is_file() and sha256(target) == want:
        print(f"[ok] {target} already present")
        return
    download(url, target)
    got = sha256(target)
    if got != want:
        sys.exit(f"[fail] SHA-256 mismatch for {target}\n  expected {want}\n  got      {got}")
    print(f"[ok] {target} verified")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ecapa-url", default=ECAPA_URL, help="Override the ECAPA int8 download link.")
    args = parser.parse_args()

    if not REGISTRY.is_file():
        sys.exit("Run this from the repo root (the folder with main.py in it).")

    weights = Path("models/weights")
    fetch("ecapa-int8", args.ecapa_url, weights / "ecapa.int8.onnx")

    vosk_zip = weights / "vosk-model-small-en-us-0.15.zip"
    fetch("vosk-small-en-us", VOSK_URL, vosk_zip)
    vosk_dir = weights / "vosk-model-small-en-us-0.15"
    if not vosk_dir.is_dir():
        print(f"Unzipping {vosk_zip.name}")
        with zipfile.ZipFile(vosk_zip) as archive:
            archive.extractall(weights)
    print("[ok] Models ready. Start the app with: uv run uvicorn main:app --port 8000")


if __name__ == "__main__":
    main()
