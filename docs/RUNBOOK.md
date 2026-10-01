# Runbook

## Phase 0 environment

- OS: Windows (PowerShell)
- Python: 3.13.5 (`C:\Python313\python.exe`)
- Supported project range: Python 3.11 through 3.13
- Internet: available for development-time source and model downloads
- Runtime network isolation: not yet tested; required before CP4

From the repository root:

```powershell
python -m pytest
python -m ruff check .
python main.py
```

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