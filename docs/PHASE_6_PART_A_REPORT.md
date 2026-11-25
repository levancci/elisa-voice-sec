# Phase 6 Part A report

- **Done:** Added `tools/evaluate_phase6.py` with reproducible enrollment-count
  studies for 3, 4, and 5 samples, threshold/FAR/FRR sweeps, wrong-speaker
  trials, replay-against-a-different-challenge trials, and an optional attack
  manifest boundary for future splicing recordings. The EER schema now stores
  `eer_rate`, `eer_threshold`, `eer_far`, and `eer_frr` as separate fields.
- **Scoring/preprocessing audit:** The harness now uses the same shared
  `aggregate_voiceprint` and `cosine_similarity` helpers as `/verify`. Every
  attempt WAV is passed through `decode_audio`, including mono conversion,
  resampling to 16 kHz, duration checks, and silence rejection, before either
  embedding or Vosk inference.
- **Dry-run evidence:** Ran the harness with real ECAPA int8 and Vosk models on
  `p02` through `p06`. Each enrollment count produced 500 trials: 100 genuine
  and 400 impostor. After correcting the ECAPA frontend, the descriptive
  trend is:

  | Enrollment samples | EER rate | EER threshold | EER FAR | EER FRR |
  |---:|---:|---:|---:|---:|
  | 3 | 0.2312 | 0.4891 | 0.2325 | 0.2300 |
  | 4 | 0.2388 | 0.4806 | 0.2375 | 0.2400 |
  | 5 | 0.2400 | 0.4953 | 0.2400 | 0.2400 |

  The run produced 200 wrong-speaker trials and 50 replay trials. Splicing
  reported `fixture-unavailable` with zero trials because the current data has
  no individual-digit recordings.
- **Output:** `data/phase6/part_a_dry_run.json`.
- **Interpretation constraint:** These are tooling dry-run numbers only. They
  are not CP6 results and must not select a threshold, embedding model, or
  go/no-go outcome. The participant set is incomplete and the attack fixtures
  are incomplete. The corrected per-count trend is roughly flat, but no
  conclusion about enrollment benefit is made from this sample.
- **Part B status:** Held. No final threshold, embedding choice, or go/no-go
  decision has been made.

## ECAPA pipeline audit

The original Part A result was invalid for model-quality interpretation. The
Phase 6 harness and active ONNX adapter were feeding the ECAPA graph with the
WeSpeaker frontend from `tools/score_embedding.py`: 398 frames and feature
standard deviation about 3.70 on a representative utterance. The saved
SpeechBrain ECAPA configuration requires SpeechBrain Fbank plus sentence mean
normalization: 401 frames and feature standard deviation about 15.95 on that
same utterance. This was a preprocessing mismatch, not evidence that ECAPA
embeddings are intrinsically non-discriminative.

The adapter and harness now use `backend/app/ecapa_frontend.py`, and the
harness uses the same `decode_audio` preprocessing and shared scoring helpers
as `/verify`. The old 0.7388-0.7523 values were thresholds mislabeled as EER;
they are superseded by the corrected artifact below.

### Corrected score distributions, five-sample profiles

Values are mean +/- population standard deviation over the 100 genuine and
400 impostor trials in each condition. FP32 ONNX matches native Torch exactly
for these metrics.

| Path | Quiet genuine | Quiet impostor | Noisy genuine | Noisy impostor |
|---|---:|---:|---:|---:|
| SpeechBrain Torch | 0.6213 +/- 0.1049 | 0.3637 +/- 0.1792 | 0.5595 +/- 0.0980 | 0.3496 +/- 0.1680 |
| ECAPA FP32 ONNX | 0.6213 +/- 0.1049 | 0.3637 +/- 0.1792 | 0.5595 +/- 0.0980 | 0.3496 +/- 0.1680 |
| ECAPA int8 ONNX | 0.6201 +/- 0.1047 | 0.3589 +/- 0.1811 | 0.5550 +/- 0.0989 | 0.3414 +/- 0.1689 |

### Corrected per-pair EER, five-sample profiles

Each unordered pair combines both genuine self-comparisons and both
cross-speaker directions. The full trial structure is 20 directional speaker
pairs x 20 verification utterances: 100 genuine and 400 impostor trials.

| Speaker pair | Torch | FP32 ONNX | int8 ONNX |
|---|---:|---:|---:|
| p02-p03 | 0.475 | 0.475 | 0.500 |
| p02-p04 | 0.400 | 0.400 | 0.425 |
| p02-p05 | 0.100 | 0.100 | 0.125 |
| p02-p06 | 0.000 | 0.000 | 0.000 |
| p03-p04 | 0.425 | 0.425 | 0.425 |
| p03-p05 | 0.150 | 0.150 | 0.150 |
| p03-p06 | 0.000 | 0.000 | 0.000 |
| p04-p05 | 0.175 | 0.175 | 0.175 |
| p04-p06 | 0.000 | 0.000 | 0.000 |
| p05-p06 | 0.000 | 0.000 | 0.000 |

### Native and quantized parity

On the same 150 utterances, native SpeechBrain Torch versus FP32 ONNX
embedding cosine was mean `1.000000`, standard deviation `0`, minimum
`1.000000`. FP32 ONNX versus corrected int8 ONNX was mean `0.991592`, standard
deviation `0.006033`, minimum `0.925980`. The earlier Phase 2 parity check used
SpeechBrain's native Fbank and sentence mean normalization, so it was a valid
frontend-matched comparison; the original 0.223 result was the separate
normalization-path quantization bug.

The complete machine-readable result is
`data/phase6/ecapa_path_analysis.json`. These corrected measurements remain
Part A dry-run evidence only; no Part B threshold, model, or go/no-go decision
has been made.

The evaluator now accepts `--splicing-manifest` with JSONL records containing
`claimed_participant`, `enrolled_participant`, `digits`, and four
`digit_audio_paths`. Missing paths are reported as `fixtures-pending` instead
of being silently skipped. `data/phase6/splicing_manifest.example.jsonl` is a
placeholder for the individual-digit recordings to be collected later.

## p06 recording metadata check

The protocol manifests do not record device, microphone, room/environment, or
session identifiers. They contain only participant/protocol labels and UTC
timestamps. The WAV headers are identical for p02, p03, p04, and p06: mono,
16 kHz, PCM16, 4.0 seconds. Signal-level ranges overlap substantially, so the
available files do not show a definitive device or format change.

p02-p04 were recorded in one continuous block from 15:32 to 15:46 UTC. p06
was recorded in a separate block from 23:37 to 23:41 UTC, roughly eight hours
later. That makes a session or channel change plausible, but it cannot be
distinguished from genuine voice confusability using the current metadata.
The p06 separation is therefore a participant/session confound to preserve in
the report, not evidence that the model is uniformly 23% weak. The corrected
23-24% aggregate EER remains a real open concern against the approximate 1%
literature range, and needs the remaining participants and controlled
recording metadata before causal interpretation.