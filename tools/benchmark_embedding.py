"""Evaluate speaker-verification trial scores and inventory model artifacts.

Model-specific inference adapters write JSONL trial records. Keeping score
evaluation separate makes threshold selection reproducible and prevents tuning
the evaluator on a model's internal implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _load_trials(path: Path) -> list[dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("label") not in {0, 1, False, True}:
            raise ValueError(f"line {line_number}: label must be 0 or 1")
        record["score"] = float(record["score"])
        record["label"] = int(record["label"])
        trials.append(record)
    if not trials:
        raise ValueError("trial manifest contains no records")
    if not any(trial["label"] == 1 for trial in trials):
        raise ValueError("trial manifest contains no genuine trials")
    if not any(trial["label"] == 0 for trial in trials):
        raise ValueError("trial manifest contains no impostor trials")
    return trials


def _metrics(trials: list[dict[str, Any]]) -> dict[str, float]:
    genuine = [trial["score"] for trial in trials if trial["label"] == 1]
    impostor = [trial["score"] for trial in trials if trial["label"] == 0]
    thresholds = sorted({trial["score"] for trial in trials}, reverse=True)
    best = {
        "eer": 1.0,
        "eer_threshold": thresholds[-1],
        "min_dcf": 1.0,
        "min_dcf_normalized": 1.0,
        "min_dcf_threshold": thresholds[-1],
        "min_dcf_far": 1.0,
        "min_dcf_frr": 1.0,
    }
    best_eer_gap = float("inf")
    for threshold in thresholds:
        false_reject_rate = sum(score < threshold for score in genuine) / len(genuine)
        false_accept_rate = sum(score >= threshold for score in impostor) / len(impostor)
        dcf = 0.01 * false_reject_rate + 0.99 * false_accept_rate
        eer_gap = abs(false_reject_rate - false_accept_rate)
        if eer_gap < best_eer_gap:
            best["eer"] = (false_reject_rate + false_accept_rate) / 2
            best["eer_threshold"] = threshold
            best_eer_gap = eer_gap
        if dcf < best["min_dcf"]:
            best["min_dcf"] = dcf
            best["min_dcf_normalized"] = dcf / 0.01
            best["min_dcf_threshold"] = threshold
            best["min_dcf_far"] = false_accept_rate
            best["min_dcf_frr"] = false_reject_rate
    return best | {
        "genuine_trials": float(len(genuine)),
        "impostor_trials": float(len(impostor)),
        "distinct_claimed_speakers": float(
            len({trial["claimed_participant"] for trial in trials if "claimed_participant" in trial})
        ),
        "distinct_enrolled_speakers": float(
            len({trial["enrolled_participant"] for trial in trials if "enrolled_participant" in trial})
        ),
    }


def _inventory(paths: list[Path]) -> list[dict[str, Any]]:
    inventory = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        inventory.append({"path": str(path), "bytes": path.stat().st_size, "sha256": digest})
    return inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="JSONL trial-score manifest")
    parser.add_argument("--artifact", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = {"metrics": _metrics(_load_trials(args.manifest))}
    report["artifacts"] = _inventory(args.artifact)
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()