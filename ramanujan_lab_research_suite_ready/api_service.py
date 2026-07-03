"""FastAPI companion service for Ramanujan Laboratory Pro."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api_core import expand, serialize_coefficients, dissect, check_congruence

app = FastAPI(title="Ramanujan Laboratory API", version="5.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ExpansionRequest(BaseModel):
    formula: str = Field(..., min_length=1, max_length=4000)
    limit: int = Field(100, ge=0, le=200000)


class DissectionRequest(ExpansionRequest):
    p: int = Field(2, ge=2, le=101)


class CongruenceRequest(ExpansionRequest):
    step: int = Field(..., ge=1)
    residue: int = Field(..., ge=0)
    modulus: int = Field(..., ge=2)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ramanujan-api", "version": "5.0"}


@app.post("/expand")
def expansion(request: ExpansionRequest):
    try:
        return {"formula": request.formula, "limit": request.limit, "coefficients": serialize_coefficients(expand(request.formula, request.limit))}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/dissect")
def p_dissection(request: DissectionRequest):
    try:
        return {"formula": request.formula, "p": request.p, "components": dissect(request.formula, request.p, request.limit)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/congruence/check")
def congruence(request: CongruenceRequest):
    if request.residue >= request.step:
        raise HTTPException(status_code=400, detail="residue must be smaller than step")
    try:
        return check_congruence(request.formula, request.step, request.residue, request.modulus, request.limit)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
