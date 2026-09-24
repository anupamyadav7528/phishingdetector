from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from .modeling import load_bundle, predict

app = FastAPI(title="Undergraduate AI Phishing/Scam Detector", version="1.0.0")
MODEL_DIR = os.getenv("MODEL_DIR", "artifacts")
STATIC = Path(__file__).parent / "static"


class DetectRequest(BaseModel):
    url: str | None = Field(default=None, max_length=4096)
    text: str | None = Field(default=None, max_length=100000)
    html: str | None = Field(default=None, max_length=500000)

    @model_validator(mode="after")
    def has_input(self):
        if not any((self.url, self.text, self.html)):
            raise ValueError("Provide at least one of url, text, or html")
        return self


@app.get("/health")
def health():
    bundle = load_bundle(MODEL_DIR)
    return {"status": "ok", "models": sorted(bundle), "artifacts_available": bool(bundle)}


@app.post("/detect")
def detect(request: DetectRequest):
    bundle = load_bundle(MODEL_DIR)
    components, risks, explanations = {}, [], []
    for kind, value in (("url", request.url), ("text", request.text), ("html", request.html)):
        if value:
            score, reasons = predict(kind, value, bundle)
            components[kind] = {
                "risk_score": round(score, 4),
                "label": "suspicious" if score >= 0.5 else "likely_safe",
                "explanations": reasons,
            }
            risks.append(score)
            explanations.extend(f"{kind}: {reason}" for reason in reasons)
    score = max(risks, default=0.0)
    return {
        "risk_score": round(score, 4),
        "label": "suspicious" if score >= 0.5 else "likely_safe",
        "components": components,
        "explanations": explanations[:10],
        "models_available": sorted(bundle),
        "disclaimer": "Heuristic model output; verify independently.",
    }


@app.get("/")
def dashboard():
    return FileResponse(STATIC / "index.html")
