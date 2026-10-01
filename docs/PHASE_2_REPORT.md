# Phase 2 report

- **Done:** Added the reproducible speaker-score evaluator at
  `tools/benchmark_embedding.py`, including EER, minDCF, trial-count, and
  artifact hash/size reporting. Added a local ONNX scoring adapter using the
  published WeSpeaker 80-bin Kaldi fbank and mean-only CMVN pipeline. Added
  regression coverage for threshold selection and feature extraction.
- **Gate evidence:** `python -m pytest` reports `6 passed`; Ruff reports
  `All checks passed`. Four complete participants (`p02` through `p05`) were
  structurally validated: 120 WAVs, all 16 kHz mono 16-bit, with 30 files per
  participant. The WeSpeaker artifact is 26,530,309 bytes with SHA-256
  `7BB2F06E9DF17CDF1EF14EE8A15AB08ED28E8D0EF5054EE135741560DF2EC068`.
  Each split has 2 distinct speakers, 40 genuine pairs, and 40 impostor pairs.
  On the held-out split, WeSpeaker EER was 22.5%, normalized minDCF was 0.800
  (raw cost 0.00800), and the EER threshold was 0.4881. SpeechBrain ECAPA had
  held-out EER 17.5%, normalized minDCF 0.700 (raw cost 0.00700), tuning EER
  47.5%, and held-out latency 673.09 ms p50 / 709.91 ms p95. At ECAPA's
  held-out minDCF point, FAR was 0% and FRR was 70%, so that low raw cost is
  not a useful balanced operating point. Full tables are in
  `docs/BENCHMARK_EMBEDDING.md`.
- **Decisions made:** CP1 approvals and the CC-BY attribution tier are
  recorded as D-0002 in `docs/DECISIONS.md`. No production approval was made.
- **Surprises / assumptions broken:** The recordings are now available, but
  WeSpeaker performance is weak and split-sensitive. The first approximate
  frontend produced a 45.0% held-out EER; aligning to the published
  mean-only-CMVN frontend reduced it to 22.5%, confirming preprocessing matters.
  This remains insufficient for a primary-model recommendation. ECAPA's
  PyTorch checkpoint was 83,316,686 bytes; exported FP32 ONNX was 83,475,144
  bytes, while executable QDQ int8 was 21,885,824 bytes. Single-thread ONNX
  latency was 855.77 ms p50 / 1,350.65 ms p95 for FP32 and 302.36 ms p50 /
  568.55 ms p95 for int8. The first int8 attempt quantized activation paths
  around normalization and produced only 0.223 mean cosine on 12 real
  utterances. After restricting static QDQ per-channel quantization to the 38
  convolution nodes, keeping all 31 BatchNorm nodes FP32, and calibrating on
  80 real verification utterances, corrected FP32/int8 cosine averaged 0.991
  (minimum 0.985). Corrected int8 size was 21,805,725 bytes, with 233.37 ms
  p50 / 357.73 ms p95 single-thread latency. This corrected int8 artifact is
  the valid quantized candidate; combined size with a digit model remains
  pending.
- **Open questions for owner:** No additional participants or recordings are
  needed for this first comparison. ECAPA now runs locally and has been
  benchmarked. The remaining work is to obtain executable artifacts for CAM++
  and TitaNet-S. No account was created and no restricted download was
  accepted. Official ModelScope SDK download succeeded without a token. An
  official WeSpeaker VoxCeleb CAM++ ONNX mirror was also downloaded and run.
  The official NVIDIA TitaNet-S NGC artifact still requires manual
  authenticated retrieval; a third-party Hugging Face mirror was benchmarked
  provisionally and is not authoritative.
- **Proposed next step:** Continue Phase 2 with CAM++ and TitaNet-S only if an
  official public artifact route is found or the owner explicitly creates the
  required account. CP2 remains open until the comparison table includes the
  approved candidates and reports latency, memory, fp32/int8 size, and
  accuracy change.