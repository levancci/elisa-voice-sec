"""Create and optionally record the fixed Phase 2 voice evaluation protocol.

The default operation is offline and only creates a JSONL plan. Recording is
opt-in and requires the local ``sounddevice`` package. Audio is written under
the ignored ``data/`` directory and is never uploaded by this tool.
"""

from __future__ import annotations

import argparse
import json
import time
import wave
from pathlib import Path
from random import Random
from typing import Any


DEFAULT_ENROLLMENT_PROMPTS = ("0123", "4567", "8901", "2345", "6789")


def _random_digits(generator: Random, count: int = 4) -> str:
    return "".join(str(generator.randrange(10)) for _ in range(count))


def build_plan(seed: int, verification_count: int = 10) -> list[dict[str, Any]]:
    """Build a reproducible plan with disjoint verification prompts."""
    if verification_count < 1:
        raise ValueError("verification_count must be positive")
    generator = Random(seed)
    plan: list[dict[str, Any]] = []
    for condition in ("quiet", "noisy"):
        for index, digits in enumerate(DEFAULT_ENROLLMENT_PROMPTS, 1):
            plan.append(
                {
                    "kind": "enrollment",
                    "condition": condition,
                    "index": index,
                    "digits": digits,
                    "label": 1,
                }
            )
        for index in range(1, verification_count + 1):
            plan.append(
                {
                    "kind": "verification",
                    "condition": condition,
                    "index": index,
                    "digits": _random_digits(generator),
                    "label": 1,
                }
            )
    return plan


def write_plan(
    plan: list[dict[str, Any]],
    output: Path,
    participant_id: str,
    session_metadata: dict[str, str] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        for item in plan:
            record = {"participant_id": participant_id, **(session_metadata or {}), **item}
            record.setdefault("room_type", item["condition"])
            stream.write(json.dumps(record, sort_keys=True) + "\n")


def _record_wav(path: Path, seconds: float, sample_rate: int = 16_000) -> None:
    try:
        import sounddevice as sd
    except ImportError as error:
        raise SystemExit(
            "Recording requires the optional local package sounddevice. "
            "Install it in the project environment, then rerun --record."
        ) from error

    print(f"Recording {seconds:.1f}s ...", flush=True)
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(audio.tobytes())


def record_plan(
    plan: list[dict[str, Any]],
    data_root: Path,
    participant_id: str,
    session_metadata: dict[str, str],
) -> None:
    """Record each genuine item after an explicit local confirmation."""
    for number, item in enumerate(plan, 1):
        relative = (
            Path(participant_id)
            / item["condition"]
            / item["kind"]
            / f'{item["index"]:02d}_{item["digits"]}.wav'
        )
        target = data_root / relative
        print(f"[{number}/{len(plan)}] Say: {' '.join(item['digits'])}")
        print("Press Enter to record, or Ctrl+C to stop.", end=" ", flush=True)
        input()
        _record_wav(target, seconds=4.0)
        item["audio_path"] = str(relative).replace("\\", "/")
        item["recorded_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--participant", required=True, help="Pseudonymous ID, not a real name")
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--verification-count", type=int, default=10)
    parser.add_argument("--output", type=Path, help="Plan JSONL path")
    parser.add_argument("--data-root", type=Path, default=Path("data/phase2"))
    parser.add_argument("--record", action="store_true", help="Capture local WAV files")
    parser.add_argument("--device-model", default="unspecified", help="Recording device model for this session")
    parser.add_argument("--microphone-model", default="unspecified", help="Microphone model for this session")
    parser.add_argument("--environment-note", default="", help="Free-text room/setup note for this session")
    parser.add_argument(
        "--consent-confirmed",
        action="store_true",
        help="Confirm written consent was obtained before recording",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.record and not args.consent_confirmed:
        raise SystemExit("Refusing to record: obtain and document consent first")
    plan = build_plan(args.seed, args.verification_count)
    output = args.output or args.data_root / args.participant / "protocol.jsonl"
    session_metadata = {
        "session_started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device_model": args.device_model,
        "microphone_model": args.microphone_model,
        "environment_note": args.environment_note,
    }
    if args.record:
        record_plan(plan, args.data_root, args.participant, session_metadata)
    write_plan(plan, output, args.participant, session_metadata)
    print(f"Wrote {len(plan)} protocol records to {output}")


if __name__ == "__main__":
    main()