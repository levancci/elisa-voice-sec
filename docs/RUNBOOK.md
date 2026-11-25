# Runbook

## Phase 0 environment

- OS: Windows (PowerShell)
- Python: 3.13.5 (`C:\Python313\python.exe`)
- Supported project range: Python 3.11 through 3.13
- Internet: available for development-time source and model downloads
- Runtime network isolation: Phase 4 test blocks non-loopback sockets during a
	real ECAPA/Vosk enroll and verify cycle

From the repository root:

```powershell
python -m pytest
python -m ruff check .
python main.py
```

## Phase 4 backend

The API is exposed by `main:app` and loads the hashed local ECAPA int8 and
Vosk artifacts from `models/registry.yaml` at startup. Run it locally with:

```powershell
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

The backend uses SQLite at `data/runtime/elisa.sqlite3` for the prototype;
the storage boundary is ready for the CP4 decision about Postgres/pgvector.
The Phase 4 integration tests exercise enroll, challenge, verify, challenge
rejection paths, pre-inference rejection, and a non-loopback network guard with
both deterministic adapters and the real ECAPA/Vosk models:

```powershell
python -m pytest backend/tests/test_phase4_api.py
```

## Phase 5 teammate gate

Before CP5 can close, a teammate must run the browser flow cold using this
RunBook only. Record a screenshot or short screen recording showing five
enrollment samples, a fresh challenge, and the result screen. Also record any
step that was confusing or did not match the page. Do not treat the agent's
own smoke test as CP5 evidence.

Model artifacts and all voice recordings belong under ignored local paths.
Never commit them.

## Phase 2 recordings

Follow `docs/RECORDING_PROTOCOL.md`. The short version is:

```powershell
python tools/record_protocol.py --participant p01
python tools/record_protocol.py --participant p01 --record --consent-confirmed
```

The second command requires explicit consent confirmation and an optional
local `sounddevice` installation. Keep tuning and held-out participants
separate; do not upload recordings or use held-out data to choose thresholds.

## Phase 6 Part A dry run

The evaluation harness is intentionally descriptive until the remaining
participants and attack recordings are complete:

```powershell
python tools/evaluate_phase6.py --participants p02 p03 p04 p05 p06 `
	--output data/phase6/part_a_dry_run.json
```

This runs the 3/4/5 enrollment-count study, threshold sweep, wrong-speaker
and replay dry runs. Splicing remains unavailable until individual-digit
recordings are collected. Do not use this output to choose the final
threshold or model.