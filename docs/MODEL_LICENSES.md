# Model License Audit

Phase 1 audit date: 2026-09-30; updated after CP1 approval on 2026-09-30. No model weights are committed to this
repository. Downloaded artifacts remain in the git-ignored `models/weights/`
directory.

Verdicts use the brief's categories: `OK`, `needs owner approval`, and
`rejected`. A permissive code repository does not by itself establish rights
for pretrained weights or their training data.

Benchmarking approval does not imply production approval. CC-BY-4.0 weights
are an accepted weaker benchmarking/prototype tier because they require
attribution; Apache-2.0, MIT, and BSD remain the preferred tier.

## Speaker embedding candidates

| Candidate / artifact | Official source | Download / account | Code license | Weights license | Training-data terms | Size | SHA-256 | Verdict / status | Fallback |
|---|---|---|---|---|---|---:|---|---|---|
| CAM++ `iic/speech_campplus_sv_zh-cn_16k-common` | [3D-Speaker](https://github.com/modelscope/3D-Speaker), [ModelScope card](https://www.modelscope.cn/models/iic/speech_campplus_sv_zh-cn_16k-common) | Downloaded through official ModelScope SDK without a token | Apache-2.0 | Apache-2.0 in model card | Model card says large Chinese-speaker training set; training-data terms unverified | `campplus_cn_common.bin`: 28,036,335 bytes | `3388CF5FD3493C9AC9C69851D8E7A8BADCFB4F3DC631020C4961371646D5ADA8` | approved for benchmarking only; not production-approved | WeSpeaker VoxCeleb CAM++ |
| WeSpeaker CAM++ VoxCeleb | [Model card](https://huggingface.co/Wespeaker/wespeaker-voxceleb-campplus), [WeSpeaker](https://github.com/wenet-e2e/wespeaker) | Public Hugging Face download; no token used | Apache-2.0 repository/model-card listing | Apache-2.0 model-card listing | VoxCeleb training terms conflict is recorded below; unresolved | FP32 ONNX 29,292,449 bytes; corrected int8 8,703,948 bytes | FP32 `B50810498B5BCF5773D086F6993D344476BD0C88B566A41E8D801AAF8461EFAD`; int8 `0BCD0B81B24AB64CA1CCACC9DD3CC940B8ED23EF8E014C356EC79EAAD7CBC7A7` | approved for benchmarking only; not production-approved | ModelScope CAM++ |
| WeSpeaker ResNet34 LM | [WeSpeaker](https://github.com/wenet-e2e/wespeaker), [model card](https://huggingface.co/Wespeaker/wespeaker-voxceleb-resnet34-LM) | Hugging Face download; no API key indicated | Apache-2.0 | CC-BY-4.0 on model card; weaker attribution tier | VoxCeleb2 Dev terms conflict is recorded below; unresolved | 26,530,309 bytes for downloaded ONNX; 6.63M parameters reported | `7BB2F06E9DF17CDF1EF14EE8A15AB08ED28E8D0EF5054EE135741560DF2EC068` | approved for benchmarking only; not production-approved | SpeechBrain ECAPA or CAM++ |
| SpeechBrain ECAPA-TDNN `spkrec-ecapa-voxceleb` | [SpeechBrain](https://github.com/speechbrain/speechbrain), [model card](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb) | Hugging Face download; no API key indicated | Apache-2.0 | Apache-2.0 on model card | VoxCeleb 1+2 terms conflict is recorded below; unresolved for production | Embedding checkpoint 83,316,686 bytes; classifier 5,534,328 bytes; 88,851,014 bytes combined, plus small companion files | `embedding_model.ckpt`: `0575CB64845E6B9A10DB9BCB74D5AC32B326B8DC90352671D345E2EE3D0126A2`; `classifier.ckpt`: `FD9E3634FE68BD0A427C95E354C0C677374F62B3F434E45B78599950D860D535`; normalization/config hashes recorded in Phase 2 report | approved for benchmarking only; executed locally with Torch/SpeechBrain; exceeds the combined 30-80 MB model budget before companion models | WeSpeaker ResNet34 |
| NVIDIA TitaNet-S (`titanet_small`) | [NVIDIA NGC model page](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemo/models/titanet_small), [NeMo repository](https://github.com/NVIDIA-NeMo/Speech) | Official artifact still requires authenticated NGC download; no token used | Apache-2.0 for NeMo toolkit | NeMo toolkit license per official NGC page; artifact terms require confirmation | Composite VoxCeleb 1/2, RIR noise, Fisher, Switchboard, and LibriSpeech; VoxCeleb conflict recorded below | NGC reports 35.77 MB compressed; exact official file/hash pending | unverified | official benchmark pending manual download; third-party mirror benchmark is separate and provisional | SpeechBrain ECAPA |
| TitaNet-Small third-party ONNX mirror | [Hugging Face card](https://huggingface.co/FluffyBunnies/titanet-small-onnx) | Public download; no token used | Unverified | CC-BY-4.0 on card; provenance to NVIDIA artifact not independently verified | Training-data terms unverified | FP32 40,257,283 bytes; corrected int8 27,362,803 bytes | FP32 `AD4A1802485D8B34C722D2A9D04249662F2ECE5D28A7A039063CA22F515A789E`; int8 `EAB9B8031CD7C44FF72973BA675C118756D507348A7AEAC762125E518DD2C537` | provisional benchmarking only; not a substitute for official NGC artifact | Official NGC TitaNet-Small |

For the authoritative TitaNet-Small comparison, the manual target is the
[NVIDIA NGC TitaNet-S model page](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemo/models/titanet_small),
model version `1.19.0`, package `titanet_small`. Download that model package
only after signing in to NGC; do not enter credentials or tokens into the
repository or shell history. Record the package filename and SHA-256 after
download.

## Digit verification candidates

| Candidate / artifact | Official source | Download / account | Code license | Weights license | Training-data terms | Size | SHA-256 | Verdict / status | Fallback |
|---|---|---|---|---|---|---:|---|---|---|
| Vosk `vosk-model-small-en-us-0.15` (Method B baseline) | [Vosk model list](https://alphacephei.com/vosk/models), [Vosk API](https://github.com/alphacep/vosk-api) | Direct model download; no account or key indicated | Apache-2.0 | Apache-2.0 in official model list | Training-data terms not stated on the model list; unverified | 41,205,931 bytes downloaded (40 MB listed) | `30F26242C4EB449F948E42CB302DD7A686CB29A3423A8367F99FF41780942498` | approved for Phase 3 benchmarking only, alongside Method A; not production-approved | Tiny CTC digit recognizer, if trained data is approved |
| OpenAI `whisper-tiny.en` (Method A candidate) | [Hugging Face checkpoint](https://huggingface.co/openai/whisper-tiny.en), [OpenAI repository](https://github.com/openai/whisper) | Direct Hub download; no key indicated | MIT repository; checkpoint card lists Apache-2.0 | Apache-2.0 on checkpoint card | Trained on 680k hours of weakly supervised internet audio; provenance/terms require review | 151 MB safetensors; 608 MB repository including alternate formats | unverified | candidate only; custom token-prefix constraint is possible, but not benchmarked and exceeds the size target | Vosk constrained-decoding baseline |
| Moonshine `moonshine-tiny` (Method A candidate) | [Hugging Face checkpoint](https://huggingface.co/moonshine-ai/moonshine-tiny), [Moonshine repository](https://github.com/moonshine-ai/moonshine) | Direct Hub download; no key indicated | MIT | MIT for current English models | Training-data terms require review | 108 MB weights; 110 MB repository | unverified | candidate only; offline generation is available but no native grammar API is documented, and it exceeds the size target | Vosk constrained-decoding baseline |
| NVIDIA `parakeet-ctc-0.6b` / `parakeet-tdt-0.6b-v2` (Method A candidates) | [Parakeet CTC](https://huggingface.co/nvidia/parakeet-ctc-0.6b), [Parakeet TDT](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) | Direct Hub download; no key indicated | Apache-2.0 NeMo code | CC-BY-4.0 | Model cards describe large mixed/private and public training sources; review required | CTC: 2.44 GB checkpoint; TDT: approximately 600M parameters and at least 2 GB RAM | unverified | not practical for this size target; no turnkey digit grammar API documented | Vosk constrained-decoding baseline |

## License conflicts requiring legal review

- **VoxCeleb:** the official VoxCeleb pages state that provided metadata is
  licensed CC-BY-SA 4.0. A secondary source reviewed by the owner describes
  VoxCeleb as academic-use-only and says commercial use requires a separate
  agreement. These statements conflict and are intentionally unresolved; this
  audit does not decide which interpretation controls. The conflict must be
  resolved by qualified legal review before any production decision.
- **Training-derived weights:** WeSpeaker and TitaNet weights are accepted for
  benchmarking and prototype use under the owner's CP1 decision, but remain a
  weaker CC-BY/attribution tier than Apache/MIT/BSD and are not production
  approved. SpeechBrain and CAM++ remain subject to their training-data review.
- **English/VoxCeleb CAM++:** The official WeSpeaker Hugging Face catalog has
  `wespeaker-voxceleb-campplus` and `wespeaker-voxceleb-campplus-LM`, both listed
  Apache-2.0. No English CAM++ artifact was found in the IIC ModelScope catalog.
- **Budget trade-off note:** The only currently budget-fitting pair is WeSpeaker
  CAM++ VoxCeleb int8 + Vosk at approximately 79.6 MB. That same pairing is
  also the one most exposed to the unresolved VoxCeleb licensing conflict. Do
  not default to it on size alone at CP6; size fit is necessary but not
  sufficient, and the license risk must remain visible in the final decision.
- **ModelScope CAM++ follow-up:** Quantize the Chinese-trained ModelScope CAM++
  with the same corrected int8 policy used for the WeSpeaker CAM++ artifact and
  add it to the size-comparison table before CP6. It is the one reviewed
  candidate that could plausibly match WeSpeaker CAM++ on footprint without the
  open VoxCeleb conflict, but it is not yet measured under the same policy.

## Excluded or not yet eligible

- TIDIGITS: not pursued because the brief identifies its paid/restricted
  licensing as unavailable without owner approval.
- KWS-only Speech Commands approach: not selected as the primary method because
  the design explicitly says isolated-word KWS does not verify a connected
  four-digit utterance. It may be measured only as a baseline in Phase 3.
- No tokens, API keys, paid services, or license agreements were used for the
  ModelScope or Hugging Face downloads. ModelScope SDK download succeeded
  unauthenticated. NGC authentication remains required for the official
  TitaNet-Small artifact.

## Download status and CP1 decision

One official Vosk archive was downloaded for source verification and hash
capture. It is ignored by Git and has not been loaded by the service. The
official sources expose candidate metadata, but the required training-data and
artifact-level commercial terms remain incomplete for the candidates above.
No candidate is approved for runtime use until the owner resolves those terms.

CP1 approval covers CAM++, WeSpeaker ResNet34, SpeechBrain ECAPA, and
TitaNet-S for benchmarking only, plus Vosk for Phase 3 benchmarking alongside
Method A. Production approval remains separate and depends on resolving the
training-data and VoxCeleb licensing questions. Selected artifacts will be
downloaded, load-tested, measured, and recorded with exact size and SHA-256 as
Phase 2 and Phase 3 proceed.