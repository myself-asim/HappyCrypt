from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from backend.schemas import AnalyzeRequest, GeneratorRequest
from backend.security.session import enforce_local_origin
from backend.services.password_analyzer import analyze_password
from backend.services.password_generator import generate_password

router = APIRouter(prefix="/api/generator", tags=["generator"])


@router.post("/generate")
def generate(payload: GeneratorRequest, request: Request):
    # Generator can be used before login, but still enforce local origin
    enforce_local_origin(request)
    try:
        pwd = generate_password(
            length=payload.length,
            uppercase=payload.uppercase,
            lowercase=payload.lowercase,
            numbers=payload.numbers,
            special=payload.special,
            exclude_ambiguous=payload.exclude_ambiguous,
        )
        return {"password": pwd, "analysis": analyze_password(pwd)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze")
def analyze(payload: AnalyzeRequest, request: Request):
    enforce_local_origin(request)
    return analyze_password(payload.password)
