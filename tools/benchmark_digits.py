"""Benchmark Vosk digit-restricted decoding and report Method A status."""

from __future__ import annotations

import argparse
import json
import time
import wave
from pathlib import Path

from vosk import KaldiRecognizer, Model


DIGIT_WORDS = {
    "zero": "0",
    "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}


def normalize(text: str) -> str:
    return "".join(DIGIT_WORDS.get(word.lower(), "") for word in text.split())


def recognize(model: Model, path: Path, expected: str) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        if audio.getnchannels() != 1 or audio.getframerate() != 16_000:
            raise ValueError(f"{path}: expected mono 16 kHz WAV")
        grammar = json.dumps(["zero", "oh", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"])
        recognizer = KaldiRecognizer(model, audio.getframerate(), grammar)
        start = time.perf_counter()
        while chunk := audio.readframes(4000):
            recognizer.AcceptWaveform(chunk)
        result = json.loads(recognizer.FinalResult())
    recognized = normalize(result.get("text", ""))
    return {
        "expected_digits": expected,
        "recognized_digits": recognized,
        "exact_match": recognized == expected,
        "path": str(path),
        "latency_ms": (time.perf_counter() - start) * 1000,
    }


def records(root: Path, participants: list[str]) -> list[dict[str, object]]:
    output = []
    model = Model(str(root.parent.parent / "models" / "weights" / "vosk-model-small-en-us-0.15"))
    for participant in participants:
        manifest = root / participant / "protocol.jsonl"
        for line in manifest.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["kind"] != "verification":
                continue
            result = recognize(model, root / item["audio_path"], item["digits"])
            output.append({"participant_id": participant, "condition": item["condition"], **result})
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/phase2"))
    parser.add_argument("--participants", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = records(args.data_root, args.participants)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(item, sort_keys=True) for item in output) + "\n", encoding="utf-8")
    print(f"Wrote {len(output)} digit records to {args.output}")


if __name__ == "__main__":
    main()