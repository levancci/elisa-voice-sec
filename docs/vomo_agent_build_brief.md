# Vomo Voice Security Step: Agent Build Brief

**Read this together with `vomo_voice_security_design_v1.1.md`.**
The design doc says *what* to build and why. This brief says *how to work*: phases, gates, when to stop and ask, and what "done" means. If the two conflict, stop and ask. Don't pick one silently.

---

## 1. Mission

Build a standalone, offline voice-biometric security step for a mobile-money app, as a backend-first prototype with a minimal 2-screen web frontend. It must be reliable enough to integrate into the real app later.

The mechanism: the system speaks a fresh random 4-digit challenge, the user repeats it, and one utterance is checked two ways: **did they say the right digits** and **is this the enrolled speaker**. Both must pass.

You are working autonomously. You decide implementation details. You stop and ask at the checkpoints in Section 4 and whenever a trigger in Section 3.3 fires.

## 2. Definition of done (whole project)

All of these are true, with evidence in the repo:

1. **Enroll, challenge, verify** work end to end through the API and through the web frontend (enrollment mode and verification mode, plus the result screen with scores).
2. Speaker embedding model and digit-verification method are chosen, with the choice backed by benchmark reports and approved at checkpoints CP2 and CP3.
3. Every model used has a completed license audit entry (code, weights, and training-data terms) and is permissively licensed or explicitly approved by the owner.
4. **No network access at inference.** Verified by running the service with networking disabled (or blocked) and completing a full enroll and verify cycle.
5. Combined on-device model size is within 30 to 80 MB, measured from actual files.
6. All tunables (thresholds, challenge length, TTL, min speech duration, enrollment count) are in config. Nothing hardcoded.
7. Every attempt is logged with both scores, recognized digits, decision, reason codes, latency, and model versions and hashes.
8. Automated tests pass (unit tests plus an API integration test using recorded fixtures).
9. `docs/EVALUATION.md` reports FAR/FRR/EER, the enrollment-count study, the threshold recommendation, and results for replay, splicing, wrong-speaker, and noisy conditions. Failures and weak results are reported plainly.
10. A fresh clone can be set up and run following `docs/RUNBOOK.md` alone.
11. `docs/DECISIONS.md` records every non-trivial decision with its reason.

## 3. Rules of engagement

### 3.1 Hard constraints
- **Offline at inference.** No cloud APIs, no license-key checks, no telemetry, no remote calls of any kind once the service is running. Downloading models and packages during development is allowed; runtime is not.
- **Permissive licenses only** for code dependencies and model weights (Apache 2.0, MIT, BSD, or equivalent). Non-commercial or research-only terms are not acceptable without explicit owner approval.
- **No paid services, no new accounts, no API keys** without asking first (see 3.3).
- **Raw audio:** not retained after inference. Enrollment samples are the only exception. Any test or evaluation audio stays in a git-ignored `data/` folder and is never committed.
- **No secrets in the repo.**
- **Runtime dependencies stay light.** PyTorch and similar heavy frameworks may be used for export and benchmarking as dev dependencies, but the service should run on ONNX Runtime.
- **Reproducibility.** Pin dependency versions, record model file hashes, fix random seeds in evaluations.

### 3.2 Scope discipline
Do **not** build: the PIN/tap fallback, the mobile port, an anti-spoofing model, model fine-tuning, or anything about recipient/amount capture. If you think one of these is needed, write it up at the relevant checkpoint and let the owner decide.

### 3.3 Stop and ask (any time, not just at checkpoints)
- Anything that costs money, needs an account, sign-up, or API key, or needs a license agreement accepted.
- A model or dataset whose license is unclear, restrictive, or that you can't verify.
- A download that fails and has no fallback in this brief.
- A need to send any data over the network at runtime.
- A finding that breaks a design assumption (for example: the size budget can't hold, accuracy is far below expectations, a design-doc claim turns out wrong).
- A plan to change scope, storage choice, or the decision rule.
- Anything destructive (deleting data, rewriting history).

### 3.4 Honesty and evidence
- Verify license terms by reading the actual license text and the model card. Cite the URL. If you can't verify something, write "unverified" instead of guessing.
- Numbers in the design doc and any earlier research are directional. Don't copy them into reports as facts. Measure.
- **Don't tune on your test data.** Keep a held-out evaluation set separate from data used to choose thresholds. Say how you split it.
- Report bad results as clearly as good ones.

### 3.5 Working style
- Small, reviewable commits with clear messages.
- After each phase, write a short **phase report** (template in Section 6) and stop at the checkpoint if one is due.
- Keep `docs/DECISIONS.md` current as you go, not at the end.

## 4. Approval checkpoints

| ID | After | Agent brings | Owner decides |
|---|---|---|---|
| **CP1** | Phase 1 | License audit table, model shortlist with download status, fallbacks | Which models proceed to benchmarking; any restricted-license exceptions; any account sign-ups needed |
| **CP2** | Phase 2 | Embedding benchmark report, recommendation | Primary embedding model; target accuracy and latency bar |
| **CP3** | Phase 3 | Digit-method benchmark report, recommendation, combined size check | Digit method; digit accuracy bar |
| **CP4** | Phase 4 | Working backend (API demo via curl and tests), storage choice used | Accept backend; decide on Postgres/pgvector vs. SQLite |
| **CP5** | Phase 5 | Working frontend demo, screenshots or recording | Accept UI; any UX changes |
| **CP6** | Phase 6 | Full evaluation report, threshold and enrollment-count recommendation | Final threshold, enrollment count, go/no-go for the mobile port |

At each checkpoint: stop, present, wait. Do not start the next phase until the owner replies.

## 5. Phases and gates

A phase is done only when every gate item is satisfied **with evidence** (file, test output, or measured number).

### Phase 0: Setup
**Do:**
- Create the repo skeleton (below), pin the Python version and dependencies, set up linting and pytest.
- Confirm your environment: OS, CPU, whether you have internet for downloads, whether you can run with networking disabled.
- Create `docs/DECISIONS.md` and `docs/RUNBOOK.md` stubs.

**Suggested structure:**
```
vomo-voice-security/
  README.md
  config/default.yaml
  docs/            DESIGN.md, DECISIONS.md, MODEL_LICENSES.md,
                   BENCHMARK_EMBEDDING.md, DIGIT_METHOD.md,
                   EVALUATION.md, RUNBOOK.md
  models/          registry.yaml (names, versions, sha256, source, license); weights git-ignored
  backend/app/     main.py, config.py, api/, audio/, models/, scoring/, storage/
  backend/tests/
  tools/           export_onnx.py, quantize.py, benchmark_embedding.py,
                   benchmark_digits.py, record_protocol.py, eval_run.py
  frontend/        index.html, app.js, audio-worklet.js, style.css
  data/            git-ignored (recordings, eval sets)
```
**Gate:** repo builds, tests run (even if trivial), environment notes written. No checkpoint.

### Phase 1: Model sourcing and license audit
**Do:** for each candidate, find the official source, download, record the sha256, and audit licenses.

Speaker embedding candidates:
- CAM++ (3D-Speaker toolkit; check ModelScope and any Hugging Face mirrors)
- WeSpeaker ResNet34 (ONNX)
- SpeechBrain ECAPA-TDNN (Hugging Face)
- NVIDIA TitaNet-Small (NeMo / NGC)

Digit-verification candidates (see design doc 3.2): find one or two concrete models for method B (small offline ASR that supports digit-restricted decoding) and the data or pretrained checkpoint options for method A. Note that some corpora, such as TIDIGITS, typically require a paid license; treat them as unavailable unless the owner says otherwise.

For **each** item record in `docs/MODEL_LICENSES.md`: name, version, source URL, download method, whether an account or key is needed, **code license, weights license, and training-data terms** (a repo can be Apache 2.0 while the weights carry different terms), file size, sha256, and a fallback if the download fails.

**Gate:**
- Every shortlisted model is downloaded and loadable, or has a documented reason it isn't.
- Every entry has a license verdict: OK, needs owner approval, or rejected, with the source URL.
- List of any accounts, sign-ups, or fees required (may be empty).

**Checkpoint CP1.**

### Phase 2: Speaker-embedding benchmark
**Do:**
- Export each surviving candidate to ONNX and int8 quantize; measure fp32 vs. int8 file size and accuracy change.
- Build the evaluation data:
  - **Team recordings** (best source; needs owner coordination). Build `tools/record_protocol.py` so teammates can record a fixed protocol: for example 5 enrollment strings and 10 random 4-digit verification strings each, in quiet and in noisy conditions, plus attack recordings (another person saying the digits; a phone speaker replaying a recording). Get explicit consent from each teammate, keep data local, delete on request.
  - **Public data** for sanity checks (for example LibriSpeech, or Common Voice which may require a free account: ask first). Note dataset terms.
- Evaluate on **short utterances (2 to 4 s)**, not just long clips.
- Measure: EER, minDCF, embedding latency on CPU (report thread count; include a single-thread run as a rough proxy for a weaker device, and say plainly that it's only a proxy), memory, model size.

**Gate:** `docs/BENCHMARK_EMBEDDING.md` with a comparison table, methodology, caveats, and a recommendation. Reproducible via `tools/benchmark_embedding.py`.

**Checkpoint CP2.**

### Phase 3: Digit verification
**Do:**
- Build an evaluation set of spoken 4-digit strings: team recordings first, plus any public digit data. Include noisy conditions and accented English. Include negative cases (wrong digit, missing digit, extra digit, reordered digits).
- Implement and benchmark candidates: **B (small ASR with digit-restricted decoding)** first as the baseline, **A (tiny CTC digit model)** if B misses the size, latency or accuracy bar, and **C (KWS sliding window)** as a baseline.
- Implement normalization ("oh" to 0, and similar variants) and the exact-match rule.
- Measure: exact-string accuracy on genuine attempts, wrong-digit acceptance rate, per-digit error, latency, model size, behavior in noise.
- Check the **combined** size of the embedding model (CP2 pick) plus the digit model against 30 to 80 MB.

**Starting proposals for bars (to be confirmed at CP3, not requirements):** exact-string accuracy of at least 95% on clean genuine attempts and at least 85% in noise; wrong-digit acceptance at or below 1%.

**Gate:** `docs/DIGIT_METHOD.md` with the comparison, chosen method, combined-size check, and known weaknesses. Reproducible via `tools/benchmark_digits.py`.

**Checkpoint CP3.**

### Phase 4: Backend
**Do:** implement per design doc 3.3 to 3.5 and Section 4.
- Endpoints `/enroll`, `/challenge`, `/verify` (plus `/health`).
- Preprocessing: decode any common audio format, resample to 16 kHz mono, VAD, minimum speech duration check, silence rejection **before** inference.
- Run digit check and embedding in parallel.
- Challenge: CSPRNG, single-use, TTL, bound to user; reject reuse, expiry, and user mismatch with distinct reason codes.
- Enrollment: validate each sample (length, speech, digit correctness against the enrollment prompt), enforce that the prompt set covers all ten digits, aggregate as specified, store per-sample embeddings and the voiceprint tagged with model version.
- Storage behind an interface. Default to Postgres with `pgvector` per the design; if that isn't practical in your environment, start with SQLite and tell the owner at CP4.
- Config file for all tunables. Structured logging of every attempt (design doc Section 4).
- Model registry that loads by name and version and verifies the sha256 at startup.
- Tests: unit tests for challenge lifecycle, scoring, normalization, and decision logic; an API integration test using recorded fixtures; a test proving no outbound network calls happen during a full cycle.

**Gate:**
- Full enroll, challenge, verify cycle runs with networking disabled.
- All tests pass.
- Documented reason codes for every rejection path.
- Reject-before-inference confirmed for short and silent audio.

**Checkpoint CP4.**

### Phase 5: Minimal frontend
**Do:** a static web page, no framework needed.
- **Screen 1:** mic capture. Mode switch for enrollment and verification. Enrollment shows the digit prompts, one at a time, and progress. Verification requests a challenge, speaks it aloud with the browser's built-in speech synthesis, then records the user's repetition.
- **Screen 2:** result. Large Unlock or Denied state, plus the digit match, recognized digits, speaker score, threshold, model versions, and reason codes.
- Capture raw PCM (AudioWorklet) and send WAV, rather than relying on compressed browser recordings that add codec artifacts. Use consistent mic constraints between enrollment and verification and log which ones were used.
- Start recording only after the spoken challenge has finished, so the synthesized voice isn't captured. Note that headphones are recommended for demos.
- Mic access needs HTTPS or localhost; document how to run it.

**Gate:** a teammate can enroll and verify from the browser using only the RunBook; screenshots or a short recording attached.

**Checkpoint CP5.**

### Phase 6: Evaluation
**Do:** run a structured evaluation on held-out data, with thresholds chosen on a separate tuning split.
- **Enrollment-count study:** compare 3, 4 and 5 enrollment samples on accuracy.
- **Threshold sweep:** FAR/FRR curve, EER, and a recommended threshold with the trade-off explained.
- **Attack tests:**
  - Wrong speaker (a teammate speaking the correct digits)
  - Replay of a previous genuine attempt against a new challenge
  - Replay of a recording of the victim reading the *current* challenge, if achievable
  - **Splicing:** concatenate the victim's individual digit recordings into the requested sequence. Report how often it passes. This is a known open risk.
- **Conditions:** quiet, background noise, at least two different microphones or devices.
- Latency: p50 and p95 for `/verify`.

**Gate:** `docs/EVALUATION.md` with methodology, split description, tables, attack results, limitations, and a plain-language summary. Include an honest "what this does not prove" section.

**Checkpoint CP6.**

## 6. Phase report template

Post this at the end of every phase:

```
Phase N report
- Done: (what was built or measured)
- Gate evidence: (file paths, test output, numbers)
- Decisions made: (with links to DECISIONS.md entries)
- Surprises / assumptions broken:
- Open questions for owner:
- Proposed next step:
```

## 7. First-message prompt (paste this to the agent)

```
You are building a standalone, offline voice-biometric security step for a
mobile-money app, working autonomously in this repo.

Attached / in the repo:
1. vomo_voice_security_design_v1.1.md - WHAT to build and why
2. vomo_agent_build_brief.md - HOW to work: phases, gates, checkpoints, rules

Read both fully before doing anything. If they conflict, or anything is unclear
or missing, ask me before proceeding.

Ground rules (details in the brief):
- Fully offline at inference: no cloud calls, license-key checks or telemetry.
- Permissive licenses only (Apache 2.0 / MIT / BSD); audit weights and training
  data terms, not just code licenses.
- Do not create accounts, use API keys, or spend money without asking me first.
- Do not build the PIN fallback, mobile port, anti-spoofing model, or any
  fine-tuning. Scope is the security step only.
- Measure everything; do not copy numbers from the design doc as facts. Say
  "unverified" when you cannot verify something.
- Stop and wait for my approval at each checkpoint (CP1 to CP6).

Your first task: complete Phase 0 (setup) and Phase 1 (model sourcing and
license audit). Then post a phase report and stop at CP1. Begin by replying with
a short summary of your understanding of the project, the phases, and any
questions you have.
```

## 8. Note for the owner (not for the agent)

Things you will likely need to do yourself: coordinate teammate recordings (with their consent) for Phases 2, 3 and 6; create any free accounts the agent flags at CP1; and approve at each checkpoint. Before real users' voices are used in production, check consent and data-protection requirements for biometric data with someone qualified.
