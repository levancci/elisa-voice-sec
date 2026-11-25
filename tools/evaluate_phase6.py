"""Run Phase 6 Part A studies without making a CP6 decision.

This harness produces descriptive dry-run evidence only. Thresholds are swept
and reported, never selected as the production threshold. Attack manifests are
optional because the current p02-p06 data has no individual-digit recordings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.config import load_config
from backend.app.audio import decode_audio
from backend.app.models import OnnxEmbeddingModel, VoskDigitModel
from backend.app.scoring import aggregate_voiceprint, cosine_similarity


def protocol_records(root: Path, participant: str) -> list[dict[str, Any]]:
    manifest = root / participant / "protocol.jsonl"
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    for record in records:
        record["path"] = str(root / record["audio_path"])
    return records


def profile_for(records: list[dict[str, Any]], count: int, embedder: OnnxEmbeddingModel, config) -> np.ndarray:
    enrollment = [record for record in records if record["kind"] == "enrollment" and record["condition"] == "quiet"][:count]
    if len(enrollment) != count:
        raise ValueError(f"requested {count} enrollment samples, found {len(enrollment)}")
    vectors = [embedder.embed(_read_audio(Path(record["path"]), config)) for record in enrollment]
    return aggregate_voiceprint(vectors)


def _read_audio(path: Path, config) -> np.ndarray:
    return decode_audio(path.read_bytes(), config)


def build_trials(records_by_participant: dict[str, list[dict[str, Any]]], count: int, embedder: OnnxEmbeddingModel, config) -> list[dict[str, Any]]:
    profiles = {participant: profile_for(records, count, embedder, config) for participant, records in records_by_participant.items()}
    trials: list[dict[str, Any]] = []
    for claimed, records in records_by_participant.items():
        for attempt in (record for record in records if record["kind"] == "verification"):
            embedding = embedder.embed(_read_audio(Path(attempt["path"]), config))
            for enrolled, profile in profiles.items():
                trials.append({
                    "label": int(claimed == enrolled),
                    "score": cosine_similarity(embedding, profile),
                    "claimed_participant": claimed,
                    "enrolled_participant": enrolled,
                    "condition": attempt["condition"],
                    "digits": attempt["digits"],
                    "audio_path": attempt["path"],
                    "enrollment_count": count,
                })
    return trials


def threshold_sweep(trials: list[dict[str, Any]]) -> dict[str, Any]:
    genuine = [trial["score"] for trial in trials if trial["label"] == 1]
    impostor = [trial["score"] for trial in trials if trial["label"] == 0]
    rows = []
    for threshold in sorted({trial["score"] for trial in trials}, reverse=True):
        frr = sum(score < threshold for score in genuine) / len(genuine)
        far = sum(score >= threshold for score in impostor) / len(impostor)
        rows.append({"threshold": threshold, "far": far, "frr": frr})
    eer_row = min(rows, key=lambda row: abs(row["far"] - row["frr"]))
    return {
        "trials": len(trials),
        "genuine": len(genuine),
        "impostor": len(impostor),
        "eer_rate": (eer_row["far"] + eer_row["frr"]) / 2,
        "eer_threshold": eer_row["threshold"],
        "eer_far": eer_row["far"],
        "eer_frr": eer_row["frr"],
        "sweep": rows,
    }


def _load_splicing_manifest(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def splicing_report(manifest_path: Path | None, profiles: dict[str, np.ndarray], embedder: OnnxEmbeddingModel, digit_model: VoskDigitModel, config) -> dict[str, Any]:
    if manifest_path is None:
        return {"status": "fixture-unavailable", "trials": 0, "reason": "No splicing manifest was supplied."}
    records = _load_splicing_manifest(manifest_path)
    if not records:
        return {"status": "manifest-empty", "trials": 0, "manifest": str(manifest_path)}

    missing = []
    trials = []
    for record in records:
        paths = [Path(path) for path in record["digit_audio_paths"]]
        paths = [path if path.is_absolute() else manifest_path.parent / path for path in paths]
        missing.extend(str(path) for path in paths if not path.is_file())
        if any(not path.is_file() for path in paths):
            continue
        waveform = np.concatenate([_read_audio(path, config) for path in paths])
        embedding = embedder.embed(waveform)
        recognized = digit_model.recognize(waveform, config.sample_rate_hz)
        enrolled = record["enrolled_participant"]
        trials.append({
            "claimed_participant": record["claimed_participant"],
            "enrolled_participant": enrolled,
            "target_digits": record["digits"],
            "recognized_digits": recognized,
            "digit_match": recognized == record["digits"],
            "speaker_score": cosine_similarity(embedding, profiles[enrolled]),
        })
    report = {"status": "ready" if trials else "fixtures-pending", "trials": len(trials), "records": trials, "manifest": str(manifest_path)}
    if missing:
        report["missing_audio_paths"] = sorted(set(missing))
    return report


def attack_report(records_by_participant: dict[str, list[dict[str, Any]]], profiles: dict[str, np.ndarray], embedder: OnnxEmbeddingModel, digit_model: VoskDigitModel, config, splicing_manifest: Path | None = None) -> dict[str, Any]:
    wrong_speaker = []
    replay = []
    for claimed, records in records_by_participant.items():
        attempts = [record for record in records if record["kind"] == "verification" and record["condition"] == "quiet"]
        for attempt in attempts:
            waveform = _read_audio(Path(attempt["path"]), config)
            embedding = embedder.embed(waveform)
            recognized = digit_model.recognize(waveform, config.sample_rate_hz)
            for enrolled, profile in profiles.items():
                if enrolled != claimed:
                    wrong_speaker.append({"claimed_participant": claimed, "enrolled_participant": enrolled, "score": cosine_similarity(embedding, profile), "digit_match": recognized == attempt["digits"]})
            alternate = next(candidate for candidate in attempts if candidate["digits"] != attempt["digits"])
            replay.append({"claimed_participant": claimed, "enrolled_participant": claimed, "source_audio": attempt["path"], "new_challenge_digits": alternate["digits"], "recognized_digits": recognized, "digit_match": recognized == alternate["digits"], "speaker_score": cosine_similarity(embedding, profiles[claimed])})
    return {"wrong_speaker": {"trials": len(wrong_speaker), "records": wrong_speaker}, "replay": {"trials": len(replay), "records": replay}, "splicing": splicing_report(splicing_manifest, profiles, embedder, digit_model, config)}


def run(data_root: Path, participants: list[str], output: Path, splicing_manifest: Path | None = None) -> dict[str, Any]:
    config = load_config()
    embedder = OnnxEmbeddingModel.from_config(config)
    digit_model = VoskDigitModel.from_config(config)
    records = {participant: protocol_records(data_root, participant) for participant in participants}
    enrollment_studies = {}
    for count in (3, 4, 5):
        trials = build_trials(records, count, embedder, config)
        enrollment_studies[str(count)] = threshold_sweep(trials)
    profiles = {participant: profile_for(items, 5, embedder, config) for participant, items in records.items()}
    report = {"status": "dry-run-only", "participants": participants, "enrollment_count_study": enrollment_studies, "attacks": attack_report(records, profiles, embedder, digit_model, config, splicing_manifest)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/phase2"))
    parser.add_argument("--participants", nargs="+", default=["p02", "p03", "p04", "p05", "p06"])
    parser.add_argument("--output", type=Path, default=Path("data/phase6/part_a_dry_run.json"))
    parser.add_argument("--splicing-manifest", type=Path, help="Optional JSONL manifest with digit_audio_paths for splicing trials.")
    args = parser.parse_args()
    report = run(args.data_root, args.participants, args.output, args.splicing_manifest)
    print(json.dumps({"status": report["status"], "output": str(args.output), "enrollment_counts": list(report["enrollment_count_study"]), "attack_trials": {name: value["trials"] for name, value in report["attacks"].items()}}, indent=2))


if __name__ == "__main__":
    main()
