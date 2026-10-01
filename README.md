 # Elisa voice security prototype

This repository is the backend-first prototype for an offline voice-biometric
security step. Runtime inference will use local model files only; model
downloads and benchmarking are development-time activities.

## Phase 0

The supported Python range is 3.11 through 3.13. Run the setup checks with:

```powershell
python -m pytest
python -m ruff check .
python main.py
```

See `docs/RUNBOOK.md` for the current setup notes and `docs/DECISIONS.md` for
recorded implementation decisions.
