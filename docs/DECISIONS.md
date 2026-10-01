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

- **Status:** pending CP3 approval
- **Decision:** Benchmark Vosk with digit-restricted decoding. Do not train or
  fine-tune Method A in v1. Method A remains pending an approved pretrained
  connected-digit CTC checkpoint.
- **Reason:** Vosk is executable offline, while no eligible Method A checkpoint
  was identified and the brief prohibits training/fine-tuning.
- **Measured constraint:** Vosk exact-string accuracy is 86% overall (90%
  quiet, 82% noisy) and its unpacked model plus ECAPA int8 is approximately
  92.7 MB, above the 30-80 MB target.
- **Date:** 2026-10-01