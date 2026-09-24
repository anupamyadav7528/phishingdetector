from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np

from .features import html_features, text_features, url_features


def heuristic_score(kind: str, value: str, features: dict[str, float]) -> tuple[float, list[str]]:
    """Conservative, explainable baseline that remains useful with tiny datasets."""
    points: list[tuple[float, str]] = []
    if kind == "url":
        checks = (
            ("has_ip", 0.32, "uses a raw IP address"),
            ("has_punycode", 0.25, "uses punycode in the hostname"),
            ("at_count", 0.18, "contains an @ symbol"),
            ("suspicious_token_count", 0.12, "contains phishing-related words"),
            ("path_suspicious_count", 0.10, "has a suspicious path or query"),
            ("encoded_char_count", 0.08, "contains encoded characters"),
            ("long_token_count", 0.08, "contains an unusually long token"),
        )
        for name, weight, reason in checks:
            if features.get(name, 0) > 0:
                points.append((weight, reason))
        if features.get("has_https", 0) == 0:
            points.append((0.08, "does not use HTTPS"))
        if features.get("subdomain_count", 0) >= 3:
            points.append((0.10, "has several subdomains"))
    elif kind == "text":
        checks = (
            ("urgency_count", 0.16, "uses urgency or pressure"),
            ("request_count", 0.14, "asks you to click, verify, or act"),
            ("credential_count", 0.20, "mentions passwords, OTPs, or credentials"),
            ("impersonation_count", 0.14, "mentions a commonly impersonated brand or agency"),
            ("money_request_count", 0.14, "mentions money, prizes, refunds, or fees"),
            ("url_count", 0.12, "contains a link"),
            ("uppercase_ratio", 0.06, "uses unusual capitalization"),
            ("exclamation_count", 0.04, "uses repeated exclamation marks"),
        )
        for name, weight, reason in checks:
            if features.get(name, 0) > (0.15 if name == "uppercase_ratio" else 0):
                points.append((weight, reason))
    else:
        checks = (
            ("password_input_count", 0.30, "collects a password"),
            ("form_count", 0.15, "contains a submission form"),
            ("external_link_ratio", 0.12, "contains external links"),
            ("has_meta_refresh", 0.20, "uses a meta refresh"),
            ("iframe_count", 0.12, "embeds an iframe"),
            ("hidden_element_count", 0.08, "contains hidden elements"),
            ("suspicious_word_count", 0.12, "contains phishing-related words"),
        )
        for name, weight, reason in checks:
            if features.get(name, 0) > 0:
                points.append((weight, reason))
    total = min(0.98, sum(weight for weight, _ in points))
    return total, [reason for _, reason in sorted(points, reverse=True)]


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
    extractor = {"url": url_features, "text": text_features, "html": html_features}[kind]
    features = extractor(value)
    baseline, baseline_reasons = heuristic_score(kind, value, features)
    if not item:
        return baseline, baseline_reasons or ["No strong indicators were detected."]
    model = item["model"]
    if kind == "text" and isinstance(model, tuple):
        vectorizer, model = model
        inputs = vectorizer.transform([value])
    else:
        names = item["metadata"]["feature_names"]
        inputs = np.array([[features.get(name, 0.0) for name in names]], dtype=float)
    model_score = float(model.predict_proba(inputs)[0, 1])
    score = min(0.99, max(0.01, 0.65 * baseline + 0.35 * model_score))
    reasons = [
        f"{name.replace('_', ' ')}={features[name]:.0f}"
        for name in item["metadata"].get("feature_names", [])
        if features.get(name, 0) > item["metadata"].get("reason_thresholds", {}).get(name, 1)
    ]
    return score, (baseline_reasons + reasons)[:6] or ["No strong indicators were detected."]
