# Decisions

## D-0001: Start with a backend-first Python scaffold

- **Status:** accepted
- **Decision:** Keep runtime dependencies empty during Phase 0 and establish
  the package, configuration, test, and documentation boundaries first.
- **Reason:** The brief requires model and license evidence before selecting
  runtime inference dependencies.
- **Date:** 2026-09-30

## D-0002: CP1 benchmarking approvals and license tiers

- **Status:** accepted for benchmarking; production approval pending
- **Decision:** Benchmark CAM++, WeSpeaker ResNet34, SpeechBrain ECAPA, and
  TitaNet-S. Benchmark Vosk only alongside Method A in Phase 3. Treat CC-BY-4.0
  weights as an acceptable weaker benchmarking/prototype tier because they
  require attribution; Apache-2.0, MIT, and BSD remain preferred.
- **Reason:** The owner approved comparative evidence before any production
  decision and requested a real size/accuracy comparison for the digit methods.
- **License caveat:** VoxCeleb's official metadata statement says CC-BY-SA 4.0,
  while a secondary source describes academic-only use and separate commercial
  permission. The conflict is unresolved and requires legal review before
  production approval.
- **Date:** 2026-09-30

## D-0003: Preserve normalization during ECAPA quantization

- **Status:** accepted for benchmarking
- **Decision:** Use static QDQ per-channel int8 quantization for ECAPA
  convolution nodes only. Keep BatchNorm and normalization paths in FP32 and
  calibrate on real recorded verification utterances.
- **Reason:** The initial graph quantized activation paths around normalization
  and produced 0.223 mean FP32/int8 cosine. The corrected graph produced 0.991
  mean cosine on the same real-speech check.
- **Constraint:** This is not a model ranking decision. The current dataset has
  only two speakers per split and is insufficient for candidate ranking.
- **Date:** 2026-09-30

## D-0004: Provisional ECAPA development default

- **Status:** provisional; final model deferred to CP6
- **Decision:** Use the corrected ECAPA int8 ONNX artifact as the swappable
  development default. Keep model loading behind the registry so another
  candidate can replace it without application-code changes.
- **Reason:** It is the only candidate with a parity-verified ONNX path in the
  current prototype. This is not a ranking or production decision.
- **Re-enrollment:** Changing the embedding model requires re-enrollment
  because stored voiceprints are model-version-specific.
- **Final gate:** Choose the final model at CP6 using the 12-speaker
  evaluation. TitaNet-Small remains open; its direct NeMo and ONNX results
  differ and that discrepancy is logged as an unresolved bug.
- **Date:** 2026-10-01

## D-0005: Phase 3 digit benchmark scope

- **Status:** accepted; close-out decision
- **Decision:** Benchmark Vosk with digit-restricted decoding and proceed with it
  as the provisional digit method into Phase 4. Do not train or fine-tune
  Method A in v1. Method A is closed as a negative finding for the v1 scope:
  no reviewed offline pretrained candidate fits the combined 30-80 MB budget,
  and any custom tiny CTC training is deferred to a post-v1 backlog item that
  requires separate future approval.
- **Reason:** Vosk is executable offline and is the only reviewed digit model
  that is both feasible in this phase and small enough for one valid pairing
  within the budget. Whisper tiny.en and Moonshine tiny are additional
  pretrained candidates, but each exceeds the full 80 MB budget alone and no
  reviewed pairing fits the combined design target. The brief still prohibits
  training/fine-tuning in v1.
- **Measured constraint:** Vosk exact-string accuracy is 86% overall (90%
  quiet, 82% noisy). The valid WeSpeaker CAM++ VoxCeleb int8 + Vosk pairing
  totals approximately 79.6 MB and fits the 30-80 MB target; ECAPA int8 +
  Vosk is 92.7 MB and exceeds it; TitaNet-Small mirror int8 + Vosk is 98.3
  MB and exceeds it. This remains provisional evidence from 100 recordings and
  five speakers and will be re-evaluated at CP6.
- **Budget headroom note:** 79.6 MB leaves only about 0.4 MB of headroom under
  the 80 MB ceiling. The design doc defines the budget as embedding plus any
  future anti-spoofing/liveness model combined, not just embedding plus the
  digit check. No third model is in the v1 pipeline, but this leaves almost no
  room for a future addition if that feature is later introduced.
- **Date:** 2026-10-01

## D-0006: Phase 4 prototype storage

- **Status:** accepted for prototype; revisit at real-app integration
- **Decision:** Use SQLite behind a storage interface for the Phase 4 backend
  prototype. Keep the persistence boundary independent of the API and model
  adapters so it can be replaced with Postgres/pgvector later.
- **Reason:** The backend needs a runnable local enroll/challenge/verify cycle
  without introducing a database service or account before the owner chooses
  the production storage target.
- **Constraint:** SQLite is a prototype storage choice, not a production
  approval or a decision against Postgres/pgvector. Revisit it when this
  integrates with the real application.
- **Date:** 2026-10-01

## D-0007: Track FastAPI test-client deprecation

- **Status:** accepted; tech debt
- **Decision:** Keep the current Starlette `TestClient` path for Phase 4 and
  track its warning about the active `httpx` compatibility path. Do not change
  the test transport during CP4.
- **Reason:** The tests pass and the warning is tooling debt, not a backend
  behavior failure. Revisit when upgrading the FastAPI/Starlette test stack.
- **Date:** 2026-10-01