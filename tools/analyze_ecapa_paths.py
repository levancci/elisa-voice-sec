"""Compare native SpeechBrain, FP32 ONNX, and int8 ECAPA paths on one split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from speechbrain.inference.speaker import EncoderClassifier

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.audio import decode_audio
from backend.app.config import load_config
from backend.app.models import ModelEntry, OnnxEmbeddingModel
from backend.app.scoring import aggregate_voiceprint, cosine_similarity, normalize_embedding


def records(root: Path, participants: list[str]) -> list[dict[str, Any]]:
    result = []
    for participant in participants:
        manifest = root / participant / "protocol.jsonl"
        for line in manifest.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            item["participant"] = participant
            item["path"] = str(root / item["audio_path"])
            result.append(item)
    return result


def load_native(classifier: EncoderClassifier, waveform: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        embedding = classifier.encode_batch(torch.from_numpy(waveform).unsqueeze(0))[0, 0].cpu().numpy()
    return normalize_embedding(embedding)


def eer(trials: list[dict[str, Any]]) -> dict[str, float]:
    genuine = [trial["score"] for trial in trials if trial["label"] == 1]
    impostor = [trial["score"] for trial in trials if trial["label"] == 0]
    rows = []
    for threshold in sorted({trial["score"] for trial in trials}, reverse=True):
        frr = sum(score < threshold for score in genuine) / len(genuine)
        far = sum(score >= threshold for score in impostor) / len(impostor)
        rows.append((abs(far - frr), threshold, far, frr))
    _, threshold, far, frr = min(rows)
    return {"eer_rate": (far + frr) / 2, "eer_threshold": threshold, "eer_far": far, "eer_frr": frr}


def score_path(embeddings: dict[str, np.ndarray], items: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    profiles = {}
    for participant in sorted({item["participant"] for item in items}):
        selected = [item for item in items if item["participant"] == participant and item["kind"] == "enrollment" and item["condition"] == "quiet"][:count]
        profiles[participant] = aggregate_voiceprint([embeddings[item["path"]] for item in selected])
    trials = []
    for item in items:
        if item["kind"] != "verification":
            continue
        for enrolled, profile in profiles.items():
            trials.append({"label": int(item["participant"] == enrolled), "score": cosine_similarity(embeddings[item["path"]], profile), "claimed": item["participant"], "enrolled": enrolled, "condition": item["condition"]})
    return trials


def score_summary(trials: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"all": eer(trials)}
    for condition in ("quiet", "noisy"):
        subset = [trial for trial in trials if trial["condition"] == condition]
        for label, name in ((1, "genuine"), (0, "impostor")):
            values = np.asarray([trial["score"] for trial in subset if trial["label"] == label], dtype=np.float64)
            summary[f"{condition}_{name}"] = {"count": int(values.size), "mean": float(values.mean()), "std": float(values.std())}
    return summary


def pair_summary(trials: list[dict[str, Any]]) -> dict[str, Any]:
    participants = sorted({trial["claimed"] for trial in trials})
    result = {}
    for index, first in enumerate(participants):
        for second in participants[index + 1 :]:
            pair = {first, second}
            subset = [trial for trial in trials if trial["claimed"] in pair and trial["enrolled"] in pair]
            result[f"{first}-{second}"] = {"trials": len(subset), **eer(subset)}
    return result


def parity_summary(reference: dict[str, np.ndarray], candidate: dict[str, np.ndarray]) -> dict[str, float]:
    values = [cosine_similarity(candidate[path], reference[path]) for path in reference]
    return {"count": len(values), "mean_cosine": float(np.mean(values)), "std_cosine": float(np.std(values)), "minimum_cosine": float(np.min(values))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/phase2"))
    parser.add_argument("--participants", nargs="+", default=["p02", "p03", "p04", "p05", "p06"])
    parser.add_argument("--output", type=Path, default=Path("data/phase6/ecapa_path_analysis.json"))
    args = parser.parse_args()
    config = load_config()
    items = records(args.data_root, args.participants)
    waveforms = {item["path"]: decode_audio(Path(item["path"]).read_bytes(), config) for item in items}
    classifier = EncoderClassifier.from_hparams(source="models/weights/ecapa", savedir="models/weights/ecapa/ecapa-cache", run_opts={"device": "cpu"})
    int8 = OnnxEmbeddingModel.from_config(config)
    fp32 = OnnxEmbeddingModel(ModelEntry("ecapa-fp32", "speaker-embedding", "local-onnx-fp32", "models/weights/ecapa.onnx", "", "analysis"))
    embedding_sets = {
        "speechbrain_torch": {path: load_native(classifier, waveform) for path, waveform in waveforms.items()},
        "onnx_fp32": {path: int8.frontend(waveform) for path, waveform in waveforms.items()},
    }
    embedding_sets["onnx_fp32"] = {path: normalize_embedding(fp32.session.run([fp32.session.get_outputs()[0].name], {fp32.session.get_inputs()[0].name: features[None, :, :], fp32.session.get_inputs()[1].name: np.asarray([1.0], dtype=np.float32)})[0]) for path, features in embedding_sets["onnx_fp32"].items()}
    embedding_sets["onnx_int8"] = {path: int8.embed(waveform) for path, waveform in waveforms.items()}
    report = {
        "participants": args.participants,
        "preprocessing": "decode_audio + EcapaFrontend (SpeechBrain Fbank, sentence mean normalization)",
        "parity": {
            "onnx_fp32_vs_speechbrain_torch": parity_summary(embedding_sets["speechbrain_torch"], embedding_sets["onnx_fp32"]),
            "onnx_int8_vs_onnx_fp32": parity_summary(embedding_sets["onnx_fp32"], embedding_sets["onnx_int8"]),
        },
        "paths": {},
    }
    for name, embeddings in embedding_sets.items():
        by_count = {}
        for count in (3, 4, 5):
            trials = score_path(embeddings, items, count)
            by_count[str(count)] = {"score_summary": score_summary(trials), "pair_eer": pair_summary(trials)}
        report["paths"][name] = by_count
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
