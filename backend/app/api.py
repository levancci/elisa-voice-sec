"""FastAPI transport for the voice security service."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

from .service import EnrollmentSample, ServiceError, VoiceSecurityService


class EnrollmentInput(BaseModel):
    user_id: str = Field(min_length=1)
    audio_samples: list[dict[str, str]]


class ChallengeInput(BaseModel):
    user_id: str = Field(min_length=1)


class VerifyInput(BaseModel):
    user_id: str = Field(min_length=1)
    challenge_id: str = Field(min_length=1)
    audio_base64: str


def create_api(service: VoiceSecurityService) -> FastAPI:
    app = FastAPI(title="Elisa Voice Security")

    def current_service() -> VoiceSecurityService:
        return service

    def handle_error(error: ServiceError) -> HTTPException:
        return HTTPException(status_code=error.status_code, detail={"reason_code": error.reason_code, "message": str(error)})

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "offline"}

    @app.post("/enroll")
    def enroll(payload: EnrollmentInput, backend: VoiceSecurityService = Depends(current_service)) -> dict[str, object]:
        try:
            samples = [EnrollmentSample(item["digits"], _decode(item["audio_base64"])) for item in payload.audio_samples]
            return backend.enroll(payload.user_id, samples)
        except (KeyError, binascii.Error, ValueError) as error:
            if isinstance(error, ServiceError):
                raise handle_error(error) from error
            raise HTTPException(status_code=400, detail={"reason_code": "invalid_request", "message": str(error)}) from error

    @app.post("/challenge")
    def challenge(payload: ChallengeInput, backend: VoiceSecurityService = Depends(current_service)) -> dict[str, object]:
        return backend.challenge(payload.user_id)

    @app.post("/verify")
    def verify(payload: VerifyInput, backend: VoiceSecurityService = Depends(current_service)) -> dict[str, object]:
        try:
            return backend.verify(payload.user_id, payload.challenge_id, _decode(payload.audio_base64))
        except ServiceError as error:
            raise handle_error(error) from error

    frontend = Path(__file__).resolve().parents[2] / "frontend"
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


def _decode(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("audio_base64 is not valid base64") from error