"""Score local Phase 2 recordings with the WeSpeaker ONNX model."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import kaldi_native_fbank as kaldi_fbank
import onnxruntime as ort
import soundfile as sf


def _mel_filterbank(sample_rate: int, fft_size: int, bins: int) -> np.ndarray:
    def hz_to_mel(value: float) -> float:
        return 2595.0 * np.log10(1.0 + value / 700.0)

    def mel_to_hz(value: float) -> float:
        return 700.0 * (10.0 ** (value / 2595.0) - 1.0)

    frequencies = np.linspace(hz_to_mel(20.0), hz_to_mel(sample_rate / 2), bins + 2)
    bins_hz = np.floor((fft_size + 1) * mel_to_hz(frequencies) / sample_rate).astype(int)
    filters = np.zeros((bins, fft_size // 2 + 1), dtype=np.float32)
    for index in range(bins):
        left, center, right = bins_hz[index : index + 3]
        if center > left:
            filters[index, left:center] = np.arange(center - left) / (center - left)
        if right > center:
            filters[index, center:right] = np.arange(right - center, 0, -1) / (right - center)
    return filters


def waveform_to_features(waveform: np.ndarray, sample_rate: int = 16_000) -> np.ndarray:
    options = kaldi_fbank.FbankOptions()
    options.frame_opts.samp_freq = sample_rate
    options.frame_opts.frame_length_ms = 25
    options.frame_opts.frame_shift_ms = 10
    options.frame_opts.dither = 0
    options.mel_opts.num_bins = 80
    extractor = kaldi_fbank.OnlineFbank(options)
    extractor.accept_waveform(sample_rate, waveform.astype(np.float32))
    extractor.input_finished()
    features = np.stack(
        [np.asarray(extractor.get_frame(index), dtype=np.float32) for index in range(extractor.num_frames_ready)]
    )
    # WeSpeaker's published pipeline applies mean-only CMVN after Kaldi fbank.
    return features - features.mean(axis=0, keepdims=True)


def load_embedding(session: ort.InferenceSession, path: Path) -> np.ndarray:
    waveform, sample_rate = sf.read(path, dtype="float32")
    if waveform.ndim != 1 or sample_rate != 16_000:
        raise ValueError(f"{path}: expected mono 16 kHz WAV, got {waveform.shape} at {sample_rate} Hz")
    features = waveform_to_features(waveform)
    input_spec = session.get_inputs()[0]
    if len(input_spec.shape) == 3 and input_spec.shape[1] == 80:
        features = features.T
    inputs = {input_spec.name: features[None, :, :]}
    if len(session.get_inputs()) > 1:
        length_input = session.get_inputs()[1]
        inputs[length_input.name] = np.asarray([features.shape[-1]], dtype=np.int64)
    output_name = next(
        (output.name for output in session.get_outputs() if output.name.lower().startswith("emb")),
        session.get_outputs()[0].name,
    )
    embedding = session.run([output_name], inputs)[0][0]
    return embedding / max(float(np.linalg.norm(embedding)), 1e-12)


def _protocol_records(root: Path, participant: str) -> list[dict[str, str]]:
    manifest = root / participant / "protocol.jsonl"
    records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    for record in records:
        record["path"] = str(root / record["audio_path"])
    return records


def _score_split(root: Path, participants: list[str], model: Path) -> list[dict[str, object]]:
    session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    records = {participant: _protocol_records(root, participant) for participant in participants}
    profiles: dict[str, np.ndarray] = {}
    for participant, participant_records in records.items():
        enrollment = [
            load_embedding(session, Path(record["path"]))
            for record in participant_records
            if record["kind"] == "enrollment" and record["condition"] == "quiet"
        ]
        if len(enrollment) != 5:
            raise ValueError(f"{participant}: expected 5 quiet enrollment recordings")
        profile = np.mean(enrollment, axis=0)
        profiles[participant] = profile / np.linalg.norm(profile)

    trials: list[dict[str, object]] = []
    for claimed_participant, participant_records in records.items():
        attempts = [record for record in participant_records if record["kind"] == "verification"]
        for attempt in attempts:
            start = time.perf_counter()
            embedding = load_embedding(session, Path(attempt["path"]))
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
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--participants", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    trials = _score_split(args.data_root, args.participants, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(trial, sort_keys=True) for trial in trials) + "\n", encoding="utf-8")
    print(f"Wrote {len(trials)} trials to {args.output}")


if __name__ == "__main__":
    main()