# Phase 4 report

- **Done:** Implemented the offline FastAPI backend with `/health`, `/enroll`,
  `/challenge`, and `/verify`. Audio is decoded, downmixed, resampled to 16
  kHz, length-checked, and silence-rejected before inference. Enrollment checks
  prompt coverage and digit correctness, stores normalized sample embeddings
  and the aggregate voiceprint, and binds it to the active model version/hash.
- **Gate evidence:** The API integration tests in
  `backend/tests/test_phase4_api.py` cover the full fake-adapter contract,
  wrong-speaker rejection, wrong-digit rejection, expired challenge, reused
  challenge, wrong-user challenge, and reject-before-inference behavior. A
  separate test uses `create_app` with the registry-verified real ECAPA int8
  and Vosk models, five actual `p02` enrollment WAVs, and the actual `7634`
  verification WAV while blocking non-loopback sockets. That real enroll and
  verify cycle passed.
- **Storage:** SQLite is accepted for the prototype behind `SQLiteStorage`;
  Postgres/pgvector is deferred until real-app integration.
- **Decisions made:** D-0004 remains the active ECAPA int8 model default and
  D-0005 remains the active Vosk digit method. D-0006 records the accepted
  SQLite choice. D-0007 tracks the Starlette/httpx test-client warning.
- **Surprises / assumptions broken:** The first FastAPI dependency declaration
  was interpreted as a required query parameter under the active dependency
  versions; the route boundary now uses the compatible `Depends` form.
- **Open questions for owner:** Production model and licensing approval remain
  deferred to CP6 and later legal review.
- **Proposed next step:** CP4 is approved. Begin Phase 5 frontend work.