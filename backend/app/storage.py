"""SQLite storage behind the backend persistence boundary."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class ChallengeRecord:
    challenge_id: str
    user_id: str
    digits: str
    expires_at: float
    used: bool


class SQLiteStorage:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS enrollments (
                    user_id TEXT PRIMARY KEY,
                    model_version TEXT NOT NULL,
                    model_hash TEXT NOT NULL,
                    embeddings BLOB NOT NULL,
                    voiceprint BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS challenges (
                    challenge_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    digits TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save_enrollment(self, user_id: str, embeddings: np.ndarray, voiceprint: np.ndarray, version: str, sha256: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO enrollments VALUES (?, ?, ?, ?, ?)",
                (user_id, version, sha256, embeddings.astype(np.float32).tobytes(), voiceprint.astype(np.float32).tobytes()),
            )

    def get_enrollment(self, user_id: str) -> tuple[np.ndarray, str, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT voiceprint, model_version, model_hash FROM enrollments WHERE user_id = ?", (user_id,)
            ).fetchone()
        if row is None:
            return None
        return np.frombuffer(row[0], dtype=np.float32), str(row[1]), str(row[2])

    def save_challenge(self, record: ChallengeRecord) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("INSERT INTO challenges VALUES (?, ?, ?, ?, ?)", (record.challenge_id, record.user_id, record.digits, record.expires_at, int(record.used)))

    def get_challenge(self, challenge_id: str) -> ChallengeRecord | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM challenges WHERE challenge_id = ?", (challenge_id,)).fetchone()
        return ChallengeRecord(row[0], row[1], row[2], row[3], bool(row[4])) if row else None

    def mark_challenge_used(self, challenge_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute("UPDATE challenges SET used = 1 WHERE challenge_id = ? AND used = 0", (challenge_id,))
            return cursor.rowcount == 1

    def log_attempt(self, created_at: float, payload: dict[str, object]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("INSERT INTO attempts (created_at, payload) VALUES (?, ?)", (created_at, json.dumps(payload, sort_keys=True)))