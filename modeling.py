"""Artifact loading and prediction helpers."""
from pathlib import Path
import json, os
import joblib
from .features import html_features, text_features, url_features, vectorize

def load_bundle(model_dir: str | Path = "artifacts") -> dict:
    root = Path(model_dir)
    bundle = {}
    for kind in ("url", "text", "html"):
        path = root / f"{kind}_model.joblib"
        meta = root / f"{kind}_metadata.json"
        if path.exists() and meta.exists():
            bundle[kind] = {"model": joblib.load(path), "metadata": json.loads(meta.read_text(encoding="utf-8"))}
    return bundle

def predict(kind: str, value: str, bundle: dict) -> tuple[float, list[str]]:
    item = bundle.get(kind)
    if not item:
        return 0.0, ["No trained model is available; prediction is unavailable."]
    extractor = {"url": url_features, "text": text_features, "html": html_features}[kind]
    model = item["model"]
    if kind == "text" and isinstance(model, tuple):
        vectorizer, model = model
        x = vectorizer.transform([value])
        features = text_features(value)
    else:
        features = extractor(value)
        x = vectorize(features, item["metadata"]["feature_names"])
    probability = float(model.predict_proba(x)[0, 1]) if hasattr(model, "predict_proba") else float(model.predict(x)[0])
    reasons = [f"{name.replace('_', ' ')}={features[name]:.0f}" for name in item["metadata"]["feature_names"]
               if features.get(name, 0) > item["metadata"].get("reason_thresholds", {}).get(name, 1)]
    if kind == "text" and not reasons:
        reasons = [f"message contains {word}" for word in ("urgent", "verify", "login", "account")
                   if word in value.lower()][:5]
    return probability, reasons[:5]
