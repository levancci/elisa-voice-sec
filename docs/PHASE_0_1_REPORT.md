# Phase 0 and Phase 1 report

## Phase 0 report

- **Done:** Added the Python project skeleton, configuration scaffold, model
  registry, ignored local model/data paths, pytest and Ruff configuration, and
  setup documentation.
- **Gate evidence:** `python -m pytest` in `.venv`: `1 passed`; `python -m
  ruff check .`: `All checks passed`; `python main.py` prints the smoke
  message. Environment notes are in `docs/RUNBOOK.md`.
- **Decisions made:** D-0001 in `docs/DECISIONS.md` records the backend-first
  scaffold and intentionally empty runtime dependencies.
- **Surprises / assumptions broken:** The system Python was 3.13.5, while the
  repository virtual environment is Python 3.11.14. The project supports both
  within the declared 3.11 through 3.13 range.
- **Open questions for owner:** None for Phase 0.
- **Proposed next step:** CP1 review of the model audit.

## Phase 1 report

- **Done:** Audited the requested speaker and digit-method candidates against
  official repository/model-card sources and recorded code, weight, data,
  download, size, and hash status in `docs/MODEL_LICENSES.md`.
- **Gate evidence:** The audit contains official source links and explicit
  verdicts. No accounts, API keys, paid services, or license agreements were
  used. One Vosk archive was downloaded into the ignored weights directory;
  its size and SHA-256 are recorded in `docs/MODEL_LICENSES.md`, and it is not
  approved for runtime use.
- **Decisions made:** No model is approved for runtime or benchmarking yet;
  ambiguous training-data and artifact terms remain visible as
  `needs owner approval` or `unverified`.
- **Surprises / assumptions broken:** A permissive toolkit license did not
  establish permissive rights for every pretrained artifact or its training
  corpora. The Vosk model list gives Apache-2.0 and 40 MB for the small English
  model, but does not state the training-data terms. The downloaded archive
  measured 41,205,931 bytes.
- **Open questions for owner:**
  1. Approve which speaker candidates may be downloaded and benchmarked.
  2. Approve Vosk small English as the Method B digit baseline despite its
     training-data terms being unverified, or provide another eligible model.
  3. Approve any candidate whose weights are CC-BY-4.0 rather than Apache-2.0,
     MIT, or BSD.
- **Proposed next step:** Stop at CP1 pending owner decisions. After approval,
  download only the selected artifacts and complete exact hash/load evidence.