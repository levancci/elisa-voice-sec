# Phase 3 report

- **Done:** Added the Vosk digit-restricted decoding benchmark at
  `tools/benchmark_digits.py`, extracted the approved Vosk model, and ran it
  on 100 connected four-digit verification recordings from `p02` through
  `p06`.
- **Gate evidence:** The benchmark uses Vosk's digit-word grammar API, not the
  default general-vocabulary graph. Grammar mode requires `am/`, `ivector/`,
  configuration files, and both `graph/HCLr.fst` and `graph/Gr.fst`; removing
  those graph files prevents model loading. The actual grammar-mode package is
  therefore 70,898,967 bytes unpacked. Vosk exact-string accuracy was 86%
  overall, 90% quiet and 82% noisy. Latency was 118.88 ms p50 / 151.94 ms p95
  quiet and 110.67 ms p50 / 160.27 ms p95 noisy.
- **Combined-size table (selected embedding candidates):**
  | Embedding candidate | Size | + Vosk 70.9 MB | Total | Fits 30-80 MB? |
  |---|---:|---:|---:|---|
  | ECAPA int8 | 21.8 MB | 70.9 MB | 92.7 MB | No |
  | WeSpeaker CAM++ VoxCeleb int8 | 8.7 MB | 70.9 MB | 79.6 MB | Yes, at the upper bound |
  | TitaNet-Small mirror int8 | 27.4 MB | 70.9 MB | 98.3 MB | No |
  | ModelScope CAM++ (once quantized) | not finalized in the current Phase 3 record | 70.9 MB | not yet claimable without the artifact size | Not yet decided |
  The "Vosk exceeds budget" statement is therefore false as a universal
  claim. It is only true for the ECAPA pairing and the TitaNet-Small mirror
  pairing; the WeSpeaker CAM++ VoxCeleb int8 + Vosk pairing fits at roughly
  79.6 MB.
- **Method A conclusion:** Closed as a decided negative finding for v1. Whisper
  tiny.en (151 MB weights) and Moonshine tiny (108 MB weights) each exceed the
  full 80 MB budget alone, and no reviewed offline pretrained Method A
  candidate fits within the combined 30-80 MB target. Parakeet CTC/TDT are also
  not practical for this design because they are multi-GB or 600M+ parameter
  artifacts with no turnkey digit grammar API. Custom tiny CTC training is
  moved to a post-v1 backlog item requiring separate future approval; it is not
  a CP3 waiting item.
- **Decision status:** CP3 closes with Vosk as the provisional digit method for
  Phase 4. Final embedding pairing remains provisional until the 12-speaker
  CP6 evaluation and may still change the final viability judgment for Vosk's
  size budget. Vosk's 86% accuracy and the chosen embedding pairing remain
  provisional evidence until CP6.
- **Decisions made:** D-0004 establishes ECAPA int8 as the provisional,
  swappable development embedding default; final model choice remains CP6.
  TitaNet's NeMo/ONNX discrepancy remains an open bug and was not pursued in
  Phase 3. D-0005 is accepted as the Phase 3 scope decision: Vosk proceeds as
  the provisional digit method, and Method A is closed as no viable offline
  pretrained candidate within the budget.
- **Surprises / assumptions broken:** Vosk was already grammar-restricted, but
  grammar mode does not remove its shipped graph files. Its current score is
  below the proposed 95% clean / 85% noisy bars, and the budget is not a
  universal failure. The key result is that Vosk is viable for the provisional
  design only when paired with the correct embedding model, and final CP6
  evaluation remains decisive.
- **Owner note:** Accented-English strings remain recommended for final
  evaluation, and the seven upcoming participants are still the right next step
  for the 12-speaker study.
- **Proposed next step:** Proceed with Vosk into Phase 4 as the provisional
  digit backend while keeping the final embedding choice and any size-driven
  Vosk re-evaluation explicitly deferred to CP6.