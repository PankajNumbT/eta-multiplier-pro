"""Optional service. Run this file with Sage's Python environment."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Ramanujan Laboratory Sage Bridge", version="1.0")

try:
    from sage.all import Gamma0, ModularForms, CuspForms
    SAGE_AVAILABLE = True
except Exception:
    SAGE_AVAILABLE = False


class DimensionRequest(BaseModel):
    level: int = Field(..., ge=1)
    weight: int = Field(..., ge=1)


@app.get("/health")
def health():
    return {"status": "ok" if SAGE_AVAILABLE else "sage-unavailable", "sage_available": SAGE_AVAILABLE}


@app.post("/modular/dimension")
def dimension(request: DimensionRequest):
    if not SAGE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Run this service inside a SageMath Python environment.")
    try:
        group = Gamma0(request.level)
        modular = ModularForms(group, request.weight)
        cusp = CuspForms(group, request.weight)
        return {
            "level": request.level,
            "weight": request.weight,
            "dimension_M": int(modular.dimension()),
            "dimension_S": int(cusp.dimension()),
            "sturm_bound": int(modular.sturm_bound()),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
