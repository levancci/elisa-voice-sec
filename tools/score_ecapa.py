"""Score Phase 2 recordings with a local SpeechBrain ECAPA checkpoint."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from speechbrain.inference.speaker import EncoderClassifier


def load_embedding(classifier: EncoderClassifier, path: Path) -> np.ndarray:
    waveform, sample_rate = sf.read(path, dtype="float32")
    if waveform.ndim != 1 or sample_rate != 16_000:
        raise ValueError(f"{path}: expected mono 16 kHz WAV, got {waveform.shape} at {sample_rate} Hz")
    with torch.no_grad():
        embedding = classifier.encode_batch(torch.from_numpy(waveform).unsqueeze(0))[0, 0].cpu().numpy()
    return embedding / max(float(np.linalg.norm(embedding)), 1e-12)


def protocol_records(root: Path, participant: str) -> list[dict[str, str]]:
    manifest = root / participant / "protocol.jsonl"
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    for record in records:
        record["path"] = str(root / record["audio_path"])
    return records


def score_participants(root: Path, participants: list[str], source: Path) -> list[dict[str, object]]:
    classifier = EncoderClassifier.from_hparams(
        source=str(source),
        savedir=str(source.parent / "ecapa-cache"),
        run_opts={"device": "cpu"},
    )
    records = {participant: protocol_records(root, participant) for participant in participants}
    profiles: dict[str, np.ndarray] = {}
    for participant, participant_records in records.items():
        enrollment = [
            load_embedding(classifier, Path(record["path"]))
            for record in participant_records
            if record["kind"] == "enrollment" and record["condition"] == "quiet"
        ]
        if len(enrollment) != 5:
            raise ValueError(f"{participant}: expected 5 quiet enrollment recordings")
        profile = np.mean(enrollment, axis=0)
        profiles[participant] = profile / np.linalg.norm(profile)

    trials: list[dict[str, object]] = []
    for claimed_participant, participant_records in records.items():
        for attempt in (record for record in participant_records if record["kind"] == "verification"):
            start = time.perf_counter()
            embedding = load_embedding(classifier, Path(attempt["path"]))
            latency_ms = (time.perf_counter() - start) * 1000
            for enrolled_participant, profile in profiles.items():
                trials.append(
                    {
                        "label": int(claimed_participant == enrolled_participant),
                        "score": float(np.dot(embedding, profile)),
                        "claimed_participant": claimed_participant,
                        "enrolled_participant": enrolled_participant,
                        "condition": attempt["condition"],
                        "digits": attempt["digits"],
                        "latency_ms": latency_ms,
                    }
                )
    return trials


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/phase2"))
    parser.add_argument("--source", type=Path, default=Path("models/weights/ecapa"))
    parser.add_argument("--participants", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    trials = score_participants(args.data_root, args.participants, args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(trial, sort_keys=True) for trial in trials) + "\n", encoding="utf-8")
    print(f"Wrote {len(trials)} trials to {args.output}")


if __name__ == "__main__":
    main()