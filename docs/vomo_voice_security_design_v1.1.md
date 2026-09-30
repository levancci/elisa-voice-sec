# Vomo: Voice Biometric Security Step
## Prototype Design & Backend Spec (v1.1)

### Changes from v1.0
- **Digit check corrected.** v1.0 said a keyword-spotting (KWS) model trained on Speech Commands would verify the digit challenge. That doesn't hold: Speech Commands is isolated one-second words, while the challenge is a connected four-digit string spoken in one utterance. Section 3.2 now defines the requirement and three candidate methods. The method is chosen by benchmark (build brief, Phase 3), not assumed.
- **"Well under 1 MB" removed** for the digit model. Size depends on the method chosen; the budget check is in 3.2.
- **Challenge is now single-use and expiring** (3.3). v1.0 only said "randomize later".
- **Enrollment now checks digit correctness too**, and the enrollment prompt set must cover all ten digits (3.4).
- **Known residual risks added** (Section 5), including the splicing gap and voice-cloning exposure.

---

## 1. Scope

Only the standalone voice-security mechanism: enrollment plus challenge-response verification. Not the full Vomo app, which already exists.

Purpose: validate the models and logic, and demo the mechanism to teammates. It must still be built to a bar where it can plug into the real app later.

Backend first. The minimal frontend comes after the models are validated.

## 2. Demo Flow (2 screens)

1. **Speak Digits (sign-in).** Mic capture screen with two modes:
   - **Enrollment mode:** first-time setup. Records 3 (floor) to 5 (recommended) digit-string samples, builds and stores the reference voiceprint.
   - **Verification mode:** the actual sign-in test. The system speaks a fresh 4-digit challenge, the user repeats it, and one utterance is checked against the stored profile.
2. **Verification Result.** Unlock ✅ / Denied ❌, driven entirely by the backend decision. Also shows the underlying values (digit match, recognized digits, speaker similarity, threshold, model versions) so teammates can see what is happening, not just pass/fail.

## 3. Backend Architecture

**Pipeline:**
audio in → preprocessing (decode, resample to 16 kHz mono, VAD, normalize) → in parallel: **[digit recognizer]** and **[speaker embedding vs. stored profile]** → decision → response

### 3.1 Speaker embedding
- **Primary candidate:** CAM++. Benchmark against ECAPA-TDNN, WeSpeaker ResNet34 and TitaNet-Small before locking in.
- Exported to ONNX, int8-quantized where accuracy holds.
- Scoring: cosine similarity between the attempt embedding and the enrolled voiceprint. Threshold is a config value.
- Utterances are short (about 2 to 4 seconds of speech). Short-utterance accuracy is a specific thing to measure, because most published numbers use longer clips.

### 3.2 Digit verification (revised)

**Requirement:** given the challenge string (for example `4 7 1 9`) and one recorded utterance, decide whether the user said exactly that sequence, in order. Offline, English digits only, small enough to fit the budget.

**Why a plain KWS classifier is not enough:** a classifier trained on isolated words answers "which single word is in this clip". It does not verify a sequence of four words spoken together, where boundaries blur and digits repeat.

**Candidate methods** (decided in Phase 3 by benchmark):

| | Method | Pros | Cons |
|---|---|---|---|
| A | Tiny custom CTC digit recognizer (vocabulary: 10 digits plus blank) | Smallest footprint (roughly a few MB), fast, purpose-built | Needs connected-digit training data and a training pipeline. Isolated-word datasets need synthetic concatenation, which lacks natural co-articulation. Accent coverage is a risk. |
| B | Small pretrained offline ASR with digit-restricted decoding (grammar or vocabulary constraint) | No training, handles connected speech, broad training data helps with accents | Larger (tens of MB), so it eats budget. Needs confirmation that a restricted grammar is supported and works well. |
| C | KWS with sliding window and segmentation | Fastest to stand up | Likely weakest on connected speech. Include as a baseline only. |

**Working assumption:** B is the fastest credible baseline (nothing to train); A is the size-optimized alternative if B misses on size, latency or accuracy. This is an assumption to be tested, not a decision.

**Match rule:** exact string match on all four digits, no partial credit. Normalize spoken variants before comparing (for example "oh" and "zero" both map to 0).

**Budget check:** embedding model plus digit model must total 30 to 80 MB. With an embedding model at roughly 7 to 26 MB, method B is expected to fit but must be confirmed with real file sizes.

**Accent check:** the digit recognizer must be evaluated on Ghanaian-accented English digits, not just on standard corpora.

### 3.3 Endpoints

- `POST /enroll`: `{user_id, audio_samples[]}`. Validates each sample (length, speech present, digits match the enrollment prompt), extracts embeddings, aggregates, persists the voiceprint.
- `POST /challenge`: `{user_id}`. Returns `{challenge_id, digits, expires_at}`. Digits come from a cryptographically secure RNG. The challenge is bound to the user, single-use, and expires (default 60 s, config value).
- `POST /verify`: `{user_id, challenge_id, audio}`. Rejects unknown, expired, reused or mismatched-user challenges. Then runs both checks and returns `{digit_match, recognized_digits, speaker_score, threshold, decision, reason_codes[], model_versions}`.

Decision rule: **pass only if digit match is exact AND speaker score is at or above threshold.**

### 3.4 Enrollment design
- 3 samples minimum, 4 to 5 recommended. This is a literature-sourced assumption from older prompted-digit systems, to be validated on real voices with the chosen model (Phase 6).
- Enrollment digit strings are independent of the strings used in live verification; they don't need to match.
- The enrollment prompt set must **cover all ten digits** across the samples (3 samples of 4 digits gives 12 slots, enough for full coverage).
- Each enrollment sample must also pass the digit check, so a mumbled or wrong sample doesn't silently poison the voiceprint.
- Store the individual embeddings and the aggregated voiceprint (mean of L2-normalized embeddings, re-normalized), tagged with the model version. A model swap means re-enrolling from retained enrollment audio.

### 3.5 Storage
FastAPI backend. Postgres with `pgvector` for voiceprints and attempt logs is preferred. SQLite or flat files behind a storage interface is acceptable for a first pass and can be swapped later.

## 4. Reliability bar (even at prototype stage)

- Reject audio that is too short or silent **before** running inference.
- Match threshold and all other tunables are config values, never hardcoded.
- Log on every attempt: digit match, recognized digits, speaker score, threshold, decision, reason codes, latency. Not just pass/fail.
- Pin and log the model version and hash used per attempt.
- No raw audio retained past the inference call, except enrollment samples.
- No network calls at inference time. Models load from local files.

## 5. Known residual risks (accepted for v1, tracked)

1. **Splicing.** A random challenge blocks replay of one recording. It does not stop someone who holds many recordings of the victim saying individual digits and stitches the requested sequence. A relative with old voice notes is a plausible attacker. Phase 6 measures how well the system resists this; the outcome informs whether longer challenges or a passive continuity check is needed later.
2. **Synthetic or cloned voice.** A real-time cloned voice reading the challenge can defeat a digit-echo design. The dedicated anti-spoofing model is out of scope for v1 (Section 6) but stays on the roadmap.
3. **Short-utterance accuracy.** Four digits is little audio. Expect noisier scores than the benchmark papers report.
4. **Microphone and channel mismatch.** A browser mic in the demo differs from a low-end Android phone in a noisy market. Demo numbers are indicative, not final.
5. **PIN fallback is not present in this prototype.** A failed verification here simply returns Denied.

## 6. Explicitly out of scope

- Recipient and amount capture, and the full transaction flow (already in the app)
- PIN/tap fallback state machine (separate pass)
- Mobile port (ONNX Runtime Mobile); this prototype runs backend-side first
- A dedicated anti-spoofing model; the digit challenge is the anti-replay mechanism for now
- Fine-tuning or training the speaker embedding model
- Twi speech handling; the security step is English digits only

## 7. Next steps

The phased plan, gates and approval checkpoints are in the **Agent Build Brief**. In short: license audit and model sourcing, embedding benchmark, digit-method benchmark, backend, minimal frontend, evaluation.
