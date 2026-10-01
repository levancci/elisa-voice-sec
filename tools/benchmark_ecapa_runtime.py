"""Measure FP32 and int8 ECAPA ONNX graph size and CPU latency."""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort


def measure(path: Path, repeats: int) -> dict[str, float]:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])
    features = np.random.default_rng(7).standard_normal((1, 398, 80)).astype(np.float32)
    lengths = np.ones(1, dtype=np.float32)
    inputs = {"features": features, "lengths": lengths}
    for _ in range(5):
        session.run(None, inputs)
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        session.run(None, inputs)
        samples.append((time.perf_counter() - start) * 1000)
    samples.sort()
    return {
        "bytes": float(path.stat().st_size),
        "p50_ms": statistics.median(samples),
        "p95_ms": samples[max(0, int(len(samples) * 0.95) - 1)],
        "threads": 1.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--repeats", type=int, default=50)
    args = parser.parse_args()
    for path in args.paths:
        print(path, measure(path, args.repeats))


if __name__ == "__main__":
    main()