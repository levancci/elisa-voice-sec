# Phase 3 digit method benchmark

## Status

Phase 3 has started with Vosk Method B and a Method A feasibility review. No
model training or fine-tuning is performed in v1.

## Method B: Vosk restricted decoding

The approved `vosk-model-small-en-us-0.15` archive is 41,205,931 bytes and
unpacks to 70,898,967 bytes. The benchmark passes the eleven allowed digit
words to `KaldiRecognizer` through its grammar argument; it does not use the
default unrestricted recognizer graph. Grammar mode still requires the model's
acoustic and i-vector files plus `graph/HCLr.fst` and `graph/Gr.fst`. Those
graph files total 46,430,789 bytes, and removing them from a temporary copy
caused model loading to fail. Therefore the grammar-mode runtime package is
the full 70,898,967-byte extracted model, not just the 24,468,178-byte
non-graph subset. The model documentation also reports roughly 300 MB runtime
memory for typical small models; this is separate from the shipped-file size
and needs a backend measurement later.

The benchmark uses that digit-only grammar and exact four-digit matching. It
recognizes the current verification recordings for `p02` through `p06` locally
and writes per-record recognized digits, exact-match status, condition, and
latency.

On 100 verification recordings from five speakers, exact-string accuracy was
86% overall: 90% quiet and 82% noisy. Latency was 118.88 ms p50 and 151.94 ms
p95 quiet, and 110.67 ms p50 and 160.27 ms p95 noisy. This is provisional
small-sample evidence, with the same caveat as Phase 2: it is not ranking
evidence and is re-evaluated at CP6 with the full participant set.

The combined unpacked size with the provisional ECAPA int8 embedding model is
approximately 92.7 MB, above the 30-80 MB target. The compressed Vosk archive
plus ECAPA int8 is approximately 63.0 MB, but deployment size must use actual
runtime files, not the archive. The correct combined budget table for the
quantized/corrected embedding candidates reviewed so far is:

| Embedding candidate | Embedding size | + Vosk 70.9 MB | Total | Fits 30-80 MB? |
|---|---:|---:|---:|---|
| ECAPA int8 | 21.8 MB | 70.9 MB | 92.7 MB | No |
| WeSpeaker CAM++ VoxCeleb int8 | 8.7 MB | 70.9 MB | 79.6 MB | Yes, at the upper bound |
| TitaNet-Small mirror int8 | 27.4 MB | 70.9 MB | 98.3 MB | No |
| ModelScope CAM++ (once quantized) | not finalized in the current Phase 3 record | 70.9 MB | not yet claimable without the artifact size | Not yet decided; no fit claim without a measured size |

Only the WeSpeaker CAM++ VoxCeleb int8 + Vosk pairing fits the deployed size
budget at approximately 79.6 MB. The ECAPA + Vosk pairing exceeds it, and the
TitaNet-Small mirror + Vosk pairing also exceeds it. The Vosk budget claim is
not universal; it is true only for selected pairings, not for all embedding
candidates.

## Method A: pretrained ASR candidates

Method A is a sourcing question, not a training task, and this phase now has a
final negative decision: no viable offline pretrained Method A candidate remains
within the combined 30-80 MB budget. The following existing pretrained
checkpoints were checked for offline use, size, licensing, and constrained
decoding support:

| Candidate | Published size | License | Constrained digit decoding | Phase 3 conclusion |
|---|---:|---|---|---|
| OpenAI `whisper-tiny.en` | 151 MB safetensors; 608 MB Hub repository including alternate formats | Apache-2.0 on the Hugging Face checkpoint | Hugging Face generation exposes `prefix_allowed_tokens_fn`, so a custom token-prefix trie can constrain output. It is not a native word grammar, and exact digit-word tokenization must be verified. | Not viable within budget; the model alone exceeds the 80 MB full budget and no pairing fits. |
| Moonshine `moonshine-tiny` | 108 MB weights; 110 MB Hub repository | MIT | Transformers generation can be customized, but the model card documents no native grammar or vocabulary constraint. A custom constrained generation path would need validation. | Not viable within budget; the model alone exceeds the 80 MB full budget and no pairing fits. |
| NVIDIA `parakeet-ctc-0.6b` | 2.44 GB checkpoint; 4.87 GB Hub repository | CC-BY-4.0 | CTC decoding can theoretically use a custom lexicon/grammar decoder, but the published usage is greedy CTC decoding and does not provide a turnkey grammar API. | Not practical for the design or size target. |
| NVIDIA `parakeet-tdt-0.6b-v2` | Approximately 600M parameters; model card requires at least 2 GB RAM | CC-BY-4.0 | Published usage is TDT transcription with greedy decoding; no digit grammar API is documented. | Not practical for the design or size target. |

This closes Method A as a decided finding for v1: no offline pretrained
candidate in the reviewed set is small enough to fit the full 30-80 MB budget
without a separate approval path or a custom training effort. Custom tiny CTC
training is therefore moved to a post-v1 backlog item requiring separate future
approval. It is not a CP3 blocking question, and it is not in scope for the
current v1 Phase 3 decision.

No Method A accuracy result is claimed in this phase. The offline pretrained
candidates were reviewed for feasibility and budget fit only; a fair accuracy
comparison would still require owner approval, a reproducible offline
implementation, and evaluation on the same recordings, but those are not part of
this v1 close-out.

## Additional recordings

The existing quiet/noisy connected four-digit recordings are sufficient for
this baseline. Additional accented-English digit strings are recommended for
the later evaluation, especially from the seven new participants requested for
the 12-speaker study. They should follow the existing protocol and be labeled
with accent/device metadata.

## CP3 status

CP3 evidence now confirms that Vosk used restricted grammar decoding, but its
runtime package remains 70.9 MB unpacked and its 86% result is provisional.
Vosk is neither ruled in nor ruled out on that result alone. Method A is not
impossible, but no currently reviewed candidate is both within the size target
and ready for a fair constrained-decoding benchmark. Final method selection
remains open pending the CP3 owner decision and CP6 re-evaluation.