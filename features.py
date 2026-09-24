"""Explainable lexical, text, and safe HTML feature extraction."""
from __future__ import annotations
import ipaddress, re
from collections import Counter
from urllib.parse import parse_qsl, urlparse
import numpy as np
from bs4 import BeautifulSoup

SUSPICIOUS_WORDS = {"login", "verify", "account", "secure", "update", "bonus", "winner",
                    "urgent", "password", "wallet", "payment", "invoice", "gift", "claim"}

def url_features(url: str) -> dict[str, float]:
    value = (url or "").strip()
    candidate = value if re.match(r"^[a-z]+://", value, re.I) else "http://" + value
    p = urlparse(candidate)
    host = p.hostname or ""
    path_query = (p.path + "?" + p.query).lower()
    try:
        ipaddress.ip_address(host)
        is_ip = 1.0
    except ValueError:
        is_ip = 0.0
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return {
        "url_length": float(len(value)), "host_length": float(len(host)),
        "path_length": float(len(p.path)), "query_length": float(len(p.query)),
        "dot_count": float(value.count(".")), "hyphen_count": float(value.count("-")),
        "slash_count": float(value.count("/")), "at_count": float(value.count("@")),
        "digit_count": float(sum(c.isdigit() for c in value)),
        "subdomain_count": float(max(0, len(host.split(".")) - 2)),
        "query_param_count": float(len(parse_qsl(p.query, keep_blank_values=True))),
        "has_ip": is_ip, "has_https": float(p.scheme.lower() == "https"),
        "has_punycode": float("xn--" in host.lower()),
        "special_char_count": float(sum(c in "@?=&%" for c in value)),
        "suspicious_token_count": float(sum(t in SUSPICIOUS_WORDS for t in tokens)),
        "long_token_count": float(sum(len(t) >= 20 for t in tokens)),
        "encoded_char_count": float(value.lower().count("%")),
        "path_suspicious_count": float(sum(w in path_query for w in SUSPICIOUS_WORDS)),
    }

def text_features(text: str) -> dict[str, float]:
    value = text or ""
    low = value.lower()
    words = re.findall(r"[a-z0-9']+", low)
    return {
        "text_length": float(len(value)), "word_count": float(len(words)),
        "unique_word_ratio": float(len(set(words)) / max(1, len(words))),
        "exclamation_count": float(value.count("!")), "uppercase_ratio": float(sum(c.isupper() for c in value) / max(1, sum(c.isalpha() for c in value))),
        "digit_count": float(sum(c.isdigit() for c in value)),
        "url_count": float(len(re.findall(r"https?://\S+|www\.\S+", value, re.I))),
        "urgent_word_count": float(sum(w in SUSPICIOUS_WORDS for w in words)),
        "money_symbol_count": float(sum(value.count(x) for x in ("$", "€", "£"))),
        "question_count": float(value.count("?")),
        "has_phone_like": float(bool(re.search(r"\b\d{7,}\b", value))),
    }

def html_features(html: str) -> dict[str, float]:
    """Parse HTML without executing scripts or fetching remote resources."""
    soup = BeautifulSoup(html or "", "html.parser")
    links = soup.find_all("a")
    forms = soup.find_all("form")
    scripts = soup.find_all("script")
    imgs = soup.find_all("img")
    hrefs = [a.get("href", "") for a in links]
    external = sum(bool(re.match(r"https?://", h, re.I)) for h in hrefs)
    hidden = len(soup.select('[type="hidden"], [style*="display:none"], [style*="visibility:hidden"]'))
    return {
        "html_length": float(len(html or "")), "tag_count": float(len(soup.find_all())),
        "link_count": float(len(links)), "external_link_ratio": float(external / max(1, len(links))),
        "form_count": float(len(forms)), "password_input_count": float(len(soup.select('input[type="password"]'))),
        "script_count": float(len(scripts)), "iframe_count": float(len(soup.find_all("iframe"))),
        "image_count": float(len(imgs)), "hidden_element_count": float(hidden),
        "has_meta_refresh": float(bool(soup.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)}))),
        "suspicious_word_count": float(sum(w in SUSPICIOUS_WORDS for w in re.findall(r"[a-z]+", soup.get_text(" ", strip=True).lower()))),
    }

def vectorize(d: dict[str, float], names: list[str]) -> np.ndarray:
    return np.array([[float(d.get(name, 0.0)) for name in names]], dtype=float)
