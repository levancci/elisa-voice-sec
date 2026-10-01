# Expanded Phase 2 report

## Data used

Five complete participants are now available: `p02` through `p06`. `p01`
remains excluded as partial/dry-run data. The expanded descriptive split uses
`p02/p03/p04` for tuning and `p05/p06` held out. The tuning split has 3
speakers, 60 genuine pairs, and 120 impostor pairs. The held-out split has 2
speakers, 40 genuine pairs, and 40 impostor pairs.

These counts are still too small for ranking or threshold selection. The
results below are evidence for pipeline behavior only.

## Official TitaNet-Small

- Source: local official NVIDIA NGC package `titanet-s.nemo`.
- Size: 37,505,605 bytes.
- SHA-256: `C9D82E1BFFB53B240F2CA33C1EFF23867869BEBADB3AB0F834CC11BE83A73FFE`.
- Direct NeMo embedding benchmark: tuning EER 38.33% (60 genuine, 120
  impostor); held-out EER 12.5% (40 genuine, 40 impostor).
- Direct NeMo CPU embedding latency: 226.64 ms p50 / 244.76 ms p95 tuning;
  251.74 ms p50 / 304.97 ms p95 held out.

The official model was exported to ONNX (40,256,383 bytes, SHA-256
`67079D9DCDD01726B7009B63D7B89A4E090A5B52311CE70D390F564DFCA70FEB`) and
quantized with the shared real-speech, convolution-only QDQ policy. The int8
graph is 27,361,579 bytes with SHA-256
`ABA9CD47638E52A29324CFC3118883A380053F85744A6DAC79719AA0B30B43A1`. On the
same ONNX frontend, FP32 and int8 held-out EER were both 42.5%; real-speech
embedding cosine averaged 0.921, minimum 0.907. This ONNX result is not
interchangeable with the direct NeMo result because the frontend paths differ;
that discrepancy requires a dedicated parity check before deployment use.

## Ranking status

No candidate ranking or production recommendation is made. The held-out set
still contains only two speakers. The existing recording protocol remains the
same; seven additional participants are recommended to reach 12 total and
support a six-speaker tuning / six-speaker held-out study.