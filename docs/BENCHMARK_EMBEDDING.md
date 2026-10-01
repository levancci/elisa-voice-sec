# Speaker Embedding Benchmark

## Phase 2 status

Benchmarking is approved for CAM++, WeSpeaker ResNet34, SpeechBrain ECAPA,
and TitaNet-S. Production approval is out of scope for this phase and remains
blocked on training-data and VoxCeleb license review.

The repository currently has approved artifacts for multiple executed
benchmarks. The results below remain descriptive only; no model ranking is
made from the two-speaker splits.

| Model | Artifact | Size | SHA-256 | Execution status |
|---|---|---:|---|---|
| WeSpeaker ResNet34 LM | `models/weights/wespeaker-voxceleb-resnet34-LM.onnx` | 26,530,309 bytes | `7BB2F06E9DF17CDF1EF14EE8A15AB08ED28E8D0EF5054EE135741560DF2EC068` | Executed locally with ONNX Runtime CPU |
| SpeechBrain ECAPA-TDNN | `models/weights/speechbrain-embedding_model.ckpt` plus companion files | 88,851,014 bytes for embedding + classifier; exact companion inventory below | Hashes below | Executed locally with Torch/SpeechBrain CPU |
| CAM++ VoxCeleb | `models/weights/campplus-voxceleb/voxceleb_CAM++.onnx` | 29,292,449 bytes; corrected int8 8,703,948 bytes | Hashes in MODEL_LICENSES | Executed FP32 and corrected int8 |
| TitaNet-Small official | Not captured | NGC page reports 35.77 MB compressed | unverified | Official download still requires authenticated manual retrieval |
| TitaNet-Small third-party mirror | `models/weights/titanet-small-thirdparty.onnx` | 40,257,283 bytes; corrected int8 27,362,803 bytes | Hashes in MODEL_LICENSES | Provisional only; provenance not verified |

SpeechBrain captured artifact hashes:

- `embedding_model.ckpt`: `0575CB64845E6B9A10DB9BCB74D5AC32B326B8DC90352671D345E2EE3D0126A2`
- `classifier.ckpt`: `FD9E3634FE68BD0A427C95E354C0C677374F62B3F434E45B78599950D860D535`
- `mean_var_norm_emb.ckpt`: `CD70225B05B37BE64FC5A95E24395D804231D43F74B2E1E5A513DB7B69B34C33`
- `hyperparams.yaml`: `6F78854FA04BA59E761437B76A2575D3ABA5E5016DE3E9B69F0C9A5077FB1A41`
- `config.json`: `15FF7AFAD09ADEC0936C31493A7397C13F855914F4579A8393FE82649778A664`

The current measurements use five complete participants (`p02` through
`p06`). `p01` is a dry-run/partial set and was not used. Each complete
participant has 30 four-second WAVs, all 16 kHz mono
16-bit. The five quiet enrollment recordings form each participant profile;
verification attempts are scored in quiet and noisy conditions. The expanded
split uses `p02/p03/p04` for tuning and `p05/p06` held out.

| Split | Speakers | Genuine trials | Impostor trials | EER | EER threshold | normalized minDCF ($P_{target}=0.01$) |
|---|---:|---:|---:|---:|---:|---:|
| Tuning (`p02/p03`) | 2 | 40 | 40 | 55.0% | 0.6861 | 0.975 (raw 0.00975) |
| Held out (`p04/p05`) | 2 | 40 | 40 | 22.5% | 0.4881 | 0.800 (raw 0.00800) |

There are only two distinct speakers in each split, with 40 genuine and 40
impostor trial pairs. These results are weak and unstable across the two small
splits. WeSpeaker is
not recommended as the primary model from this evidence alone. Latency and
memory measurements still need to be summarized. CAM++ and a provisional
TitaNet-Small mirror have now been run on the same split, but the official
TitaNet-Small artifact is still pending authenticated NGC retrieval.

On this CPU run with ONNX Runtime, per-utterance embedding latency was 151.21
ms p50 and 181.48 ms p95 on tuning, and 153.98 ms p50 and 190.88 ms p95 on
held-out trials. These are environment-specific measurements, not a mobile
device proxy.

SpeechBrain ECAPA-TDNN on the same protocol produced:

| Split | Speakers | Genuine trials | Impostor trials | EER | EER threshold | normalized minDCF ($P_{target}=0.01$) |
|---|---:|---:|---:|---:|---:|---:|
| Tuning (`p02/p03`) | 2 | 40 | 40 | 47.5% | 0.6416 | 0.975 (raw 0.00975) |
| Held out (`p04/p05`) | 2 | 40 | 40 | 17.5% | 0.4204 | 0.700 (raw 0.00700) |

ECAPA CPU embedding latency was 673.09 ms p50 and 709.91 ms p95 on held-out
trials. At the raw minDCF operating point, held-out FAR was 0% and FRR was 70%;
the low raw cost therefore does not represent a useful balanced operating
point. The PyTorch checkpoint was 83,316,686 bytes, the exported FP32 ONNX
graph is 83,475,144 bytes, and the corrected executable QDQ int8 graph is
21,805,725 bytes. With one CPU thread, FP32 ONNX latency was 731.70 ms p50
and 997.88 ms p95; corrected int8 latency was 233.37 ms p50 and 357.73 ms
p95. The int8 graph is
within the embedding portion of the 30-80 MB budget. The first int8 attempt
quantized activation paths around normalization and produced poor agreement.
The corrected export uses static QDQ quantization, per-channel int8 weights,
80 real recorded verification utterances for calibration, and quantizes only
the 38 convolution nodes. All 31 BatchNorm nodes remain FP32. On 12 real
recorded utterances, corrected FP32 versus int8 embedding cosine averaged
0.991 (minimum 0.985). The corrected int8 graph is the valid quantized
candidate; combined size with the digit model remains to be measured.

CAM++ VoxCeleb FP32 and corrected int8 both produced 15.0% held-out EER on
the current two-speaker split. The int8 graph's real-speech FP32/int8 cosine
was 0.988 mean and 0.975 minimum. These are not ranking results.

The provisional third-party TitaNet-Small mirror produced 50.0% FP32 and
45.0% corrected int8 held-out EER. FP32/int8 cosine was 0.921 mean and 0.907
minimum. These results cannot substitute for the official NVIDIA NGC artifact.

## Reproducible evaluator

`tools/benchmark_embedding.py` consumes JSONL trial scores. Each record must
contain `label` (`1` for genuine, `0` for impostor) and `score`; optional model
and latency fields are preserved by upstream adapters. The evaluator reports
EER, the associated threshold, minDCF with $P_{target}=0.01$, trial counts,
and exact artifact sizes and hashes.

Example after an inference adapter produces `data/phase2/trials.jsonl`:

```powershell
python tools/benchmark_embedding.py `
  --manifest data/phase2/trials.jsonl `
  --artifact models/weights/wespeaker-voxceleb-resnet34-LM.onnx `
  --output data/phase2/wespeaker-report.json
```

## Required completion work

- Obtain consented team recordings using `tools/record_protocol.py` before
  using voices for evaluation.
- Add model-specific local inference adapters and export/quantize each
  surviving candidate to ONNX where supported.
- Run fp32 versus int8 comparisons with single-thread CPU latency and memory.
- Keep tuning and held-out evaluation speakers and utterances disjoint.
- Add CAM++, SpeechBrain ECAPA, and TitaNet-S artifact hashes after their
  approved downloads and load checks.