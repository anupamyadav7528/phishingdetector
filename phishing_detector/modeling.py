from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np

from .features import html_features, text_features, url_features


def load_bundle(model_dir: str | Path = "artifacts") -> dict:
    root = Path(model_dir)
    bundle = {}
    for kind in ("url", "text", "html"):
        model_path = root / f"{kind}_model.joblib"
        metadata_path = root / f"{kind}_metadata.json"
        if model_path.exists() and metadata_path.exists():
            bundle[kind] = {
                "model": joblib.load(model_path),
                "metadata": json.loads(metadata_path.read_text(encoding="utf-8")),
            }
    return bundle


def predict(kind: str, value: str, bundle: dict) -> tuple[float, list[str]]:
    item = bundle.get(kind)
    if not item:
        return 0.0, ["No trained model is available; prediction is unavailable."]
    extractor = {"url": url_features, "text": text_features, "html": html_features}[kind]
    features = extractor(value)
    model = item["model"]
    if kind == "text" and isinstance(model, tuple):
        vectorizer, model = model
        inputs = vectorizer.transform([value])
    else:
        names = item["metadata"]["feature_names"]
        inputs = np.array([[features.get(name, 0.0) for name in names]], dtype=float)
    score = float(model.predict_proba(inputs)[0, 1])
    reasons = [
        f"{name.replace('_', ' ')}={features[name]:.0f}"
        for name in item["metadata"].get("feature_names", [])
        if features.get(name, 0) > item["metadata"].get("reason_thresholds", {}).get(name, 1)
    ]
    return score, reasons[:5] or ["No strong lexical indicators exceeded the explanation threshold."]
