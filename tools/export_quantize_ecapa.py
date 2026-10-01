"""Export and selectively static-int8-quantize the local ECAPA network."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import onnx
import soundfile as sf
import torch
from onnxruntime.quantization import (
    CalibrationDataReader,
    QuantFormat,
    QuantType,
    quantize_static,
)
from speechbrain.inference.speaker import EncoderClassifier


class EmbeddingWrapper(torch.nn.Module):
    def __init__(self, embedding_model: torch.nn.Module) -> None:
        super().__init__()
        self.embedding_model = embedding_model.eval()

    def forward(self, features: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        return self.embedding_model(features, lengths)


class CalibrationReader(CalibrationDataReader):
    def __init__(self, classifier: EncoderClassifier, input_names: list[str]) -> None:
        self._records = [
            {
                input_names[0]: self._features(classifier, path),
                input_names[1]: torch.ones(1, dtype=torch.float32).numpy(),
            }
            for path in sorted(Path("data/phase2").glob("p0[2-5]/*/verification/*.wav"))
        ]
        self._index = 0

    @staticmethod
    def _features(classifier: EncoderClassifier, path: Path) -> np.ndarray:
        waveform, sample_rate = sf.read(path, dtype="float32")
        with torch.no_grad():
            signal = torch.from_numpy(waveform).unsqueeze(0)
            features = classifier.mods.compute_features(signal)
            features = classifier.mods.mean_var_norm(features, torch.ones(1))
        return features.numpy().astype("float32")

    def get_next(self) -> dict[str, object] | None:
        if self._index >= len(self._records):
            return None
        record = self._records[self._index]
        self._index += 1
        return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("models/weights/ecapa"))
    parser.add_argument("--output", type=Path, default=Path("models/weights/ecapa.onnx"))
    parser.add_argument(
        "--quantized-output", type=Path, default=Path("models/weights/ecapa.int8.onnx")
    )
    args = parser.parse_args()

    classifier = EncoderClassifier.from_hparams(
        source=str(args.source),
        savedir=str(args.source.parent / "ecapa-cache"),
        run_opts={"device": "cpu"},
    )
    wrapper = EmbeddingWrapper(classifier.mods.embedding_model)
    features = torch.randn(1, 398, 80)
    lengths = torch.ones(1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        wrapper,
        (features, lengths),
        str(args.output),
        input_names=["features", "lengths"],
        output_names=["embedding"],
        dynamic_axes={"features": {1: "frames"}, "embedding": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )
    quantize_static(
        str(args.output),
        str(args.quantized_output),
        CalibrationReader(classifier, ["features", "lengths"]),
        quant_format=QuantFormat.QDQ,
        activation_type=QuantType.QUInt8,
        weight_type=QuantType.QInt8,
        per_channel=True,
        nodes_to_quantize=[node.name for node in onnx.load(args.output).graph.node if node.op_type == "Conv"],
    )
    print(f"Exported {args.output} and quantized {args.quantized_output}")


if __name__ == "__main__":
    main()