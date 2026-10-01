# Phase 2 data-quality and quantization diagnosis

## Trial counts

The current benchmark is intentionally not a ranking dataset. Each split has
only two distinct speakers:

| Split | Speakers | Genuine pairs | Impostor pairs |
|---|---:|---:|---:|
| Tuning (`p02/p03`) | 2 | 40 | 40 |
| Held out (`p04/p05`) | 2 | 40 | 40 |

The EER gap between the splits is treated as small-sample instability, not
evidence of a model ranking. A larger recording set is required before
ranking candidates or selecting thresholds.

## minDCF audit

The implementation computes `DCF = 0.01 * FRR + 0.99 * FAR`.

On held-out ECAPA data, raw minDCF `0.007` corresponds to normalized minDCF
`0.70`, FAR `0%`, and FRR `70%`. On tuning data, raw `0.00975` corresponds to
normalized `0.975`, FAR `0%`, and FRR `97.5%`. These are degenerate operating
points, not useful balanced decisions.

## ECAPA int8 diagnosis

The FP32 Torch model and FP32 ONNX export agree at cosine approximately `1.0`
on identical preprocessed features, isolating the original error to
quantization rather than export or preprocessing.

The first static QDQ attempt used per-channel weights but quantized activation
paths around normalization. It produced mean FP32/int8 cosine `0.223` on 12
real utterances. The corrected attempt keeps all 31 BatchNorm nodes in FP32,
quantizes only the 38 convolution nodes, uses per-channel int8 weights, and
calibrates with 80 real quiet/noisy verification utterances.

The corrected graph produces mean cosine `0.991`, minimum `0.985`, across 12
real utterances. Its measured size is 21,805,725 bytes; single-thread CPU
latency is 233.37 ms p50 and 357.73 ms p95. This is a valid quantized
candidate, pending combined-size and broader held-out accuracy checks.