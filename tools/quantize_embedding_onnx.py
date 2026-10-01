"""Quantize an embedding ONNX graph while preserving normalization paths."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import soundfile as sf
from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.score_embedding import waveform_to_features


class SpeechCalibrationReader(CalibrationDataReader):
    def __init__(self, session: ort.InferenceSession, paths: list[Path]) -> None:
        self.input_spec = session.get_inputs()
        self.records = []
        for path in paths:
            waveform, sample_rate = sf.read(path, dtype="float32")
            if sample_rate != 16_000 or waveform.ndim != 1:
                continue
            features = waveform_to_features(waveform)
            if self.input_spec[0].shape[1] == 80:
                features = features.T
            record = {self.input_spec[0].name: features[None, :, :].astype("float32")}
            if len(self.input_spec) > 1:
                record[self.input_spec[1].name] = np.asarray([features.shape[-1]], dtype=np.int64)
            self.records.append(record)
        self.index = 0

    def get_next(self) -> dict[str, object] | None:
        if self.index >= len(self.records):
            return None
        record = self.records[self.index]
        self.index += 1
        return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    session = ort.InferenceSession(str(args.input), providers=["CPUExecutionProvider"])
    paths = sorted(Path("data/phase2").glob("p0[2-5]/*/verification/*.wav"))
    conv_nodes = [node.name for node in onnx.load(args.input).graph.node if node.op_type == "Conv"]
    quantize_static(
        str(args.input),
        str(args.output),
        SpeechCalibrationReader(session, paths),
        quant_format=QuantFormat.QDQ,
        activation_type=QuantType.QUInt8,
        weight_type=QuantType.QInt8,
        per_channel=True,
        nodes_to_quantize=conv_nodes,
    )
    print(f"Quantized {args.input} to {args.output}; convolution nodes={len(conv_nodes)}")


if __name__ == "__main__":
    main()