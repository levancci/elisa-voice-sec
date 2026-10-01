# Phase 3 digit method benchmark

## Status

Phase 3 has started with Vosk Method B and a Method A feasibility review. No
model training or fine-tuning is performed in v1.

## Method B: Vosk restricted decoding

The approved `vosk-model-small-en-us-0.15` archive is 41,205,931 bytes and
unpacks to 70,898,967 bytes. The benchmark uses a digit-only grammar and exact
four-digit matching. It recognizes the current verification recordings for
`p02` through `p06` locally and writes per-record recognized digits, exact-match
status, condition, and latency.

On 100 verification recordings, exact-string accuracy was 86% overall: 90%
quiet and 82% noisy. Latency was 118.88 ms p50 and 151.94 ms p95 quiet, and
110.67 ms p50 and 160.27 ms p95 noisy.

The combined unpacked size with the provisional ECAPA int8 embedding model is
approximately 92.7 MB, above the 30-80 MB target. The compressed Vosk archive
plus ECAPA int8 is approximately 63.0 MB, but deployment size must use actual
runtime files, not the archive.

## Method A: tiny CTC digit recognizer

No approved pretrained connected-digit CTC checkpoint is available. TIDIGITS
is excluded by the brief unless separately approved, and training a model on
the local recordings would violate the v1 no-training/fine-tuning scope. The
repository therefore reports Method A as **not accuracy-benchmarkable** in
this phase rather than creating an untrained model and presenting meaningless
accuracy.

Method A remains the size-optimized fallback. A real comparison requires an
approved pretrained checkpoint or an explicit scope/license decision for a
training corpus and pipeline.

## Additional recordings

The existing quiet/noisy connected four-digit recordings are sufficient for
this baseline. Additional accented-English digit strings are recommended for
the later evaluation, especially from the seven new participants requested for
the 12-speaker study. They should follow the existing protocol and be labeled
with accent/device metadata.

## CP3 status

CP3 is blocked on a fair Method A accuracy result and the combined deployment
size decision. Vosk alone is not selected because the brief requires comparing
it alongside Method A.