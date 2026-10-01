# Phase 3 report

- **Done:** Added the Vosk digit-restricted decoding benchmark at
  `tools/benchmark_digits.py`, extracted the approved Vosk model, and ran it
  on 100 connected four-digit verification recordings from `p02` through
  `p06`.
- **Gate evidence:** Vosk exact-string accuracy was 86% overall, 90% quiet and
  82% noisy. Latency was 118.88 ms p50 / 151.94 ms p95 quiet and 110.67 ms
  p50 / 160.27 ms p95 noisy. The unpacked Vosk model is 70,898,967 bytes;
  combined with ECAPA int8 at 21,805,725 bytes it is approximately 92.7 MB,
  above the 30-80 MB target.
- **Method A status:** No approved pretrained tiny CTC connected-digit
  checkpoint was found. Training or fine-tuning one is explicitly out of scope
  for v1, and TIDIGITS remains unavailable without separate approval. Method A
  therefore has no honest accuracy result in this phase.
- **Decisions made:** D-0004 establishes ECAPA int8 as the provisional,
  swappable development embedding default; final model choice remains CP6.
  TitaNet's NeMo/ONNX discrepancy remains an open bug and was not pursued in
  Phase 3.
- **Surprises / assumptions broken:** Vosk meets the offline execution
  requirement but misses the proposed 95% clean / 85% noisy digit bars on this
  current set and exceeds the unpacked combined model-size budget.
- **Open questions for owner:** Approve an eligible pretrained Method A CTC
  checkpoint, or explicitly accept that Method A cannot be benchmarked under
  the no-training/no-fine-tuning v1 scope. No additional recording type is
  required to run this baseline; accented-English strings are recommended for
  final evaluation and the seven upcoming participants.
- **Proposed next step:** Stop at CP3 pending the Method A decision and the
  combined-size/method selection decision.