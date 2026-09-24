from __future__ import annotations

import ipaddress
import re
from urllib.parse import parse_qsl, urlparse

from bs4 import BeautifulSoup

SUSPICIOUS_WORDS = {
    "login", "verify", "account", "secure", "update", "bonus", "winner",
    "urgent", "password", "wallet", "payment", "invoice", "gift", "claim",
}


def url_features(url: str) -> dict[str, float]:
    value = (url or "").strip()
    parsed = urlparse(value if re.match(r"^[a-z]+://", value, re.I) else "http://" + value)
    host = parsed.hostname or ""
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    try:
        is_ip = float(ipaddress.ip_address(host) is not None)
    except ValueError:
        is_ip = 0.0
    suspicious = sum(token in SUSPICIOUS_WORDS for token in tokens)
    return {
        "url_length": float(len(value)), "host_length": float(len(host)),
        "path_length": float(len(parsed.path)), "query_length": float(len(parsed.query)),
        "dot_count": float(value.count(".")), "hyphen_count": float(value.count("-")),
        "slash_count": float(value.count("/")), "at_count": float(value.count("@")),
        "digit_count": float(sum(character.isdigit() for character in value)),
        "subdomain_count": float(max(0, len(host.split(".")) - 2)),
        "query_param_count": float(len(parse_qsl(parsed.query, keep_blank_values=True))),
        "has_ip": is_ip, "has_https": float(parsed.scheme.lower() == "https"),
        "has_punycode": float("xn--" in host.lower()),
        "special_char_count": float(sum(character in "@?=&%" for character in value)),
        "suspicious_token_count": float(suspicious),
        "long_token_count": float(sum(len(token) >= 20 for token in tokens)),
        "encoded_char_count": float(value.lower().count("%")),
        "path_suspicious_count": float(sum(word in (parsed.path + "?" + parsed.query).lower()
                                           for word in SUSPICIOUS_WORDS)),
    }


def text_features(text: str) -> dict[str, float]:
    value = text or ""
    words = re.findall(r"[a-z0-9']+", value.lower())
    alpha_count = sum(character.isalpha() for character in value)
    return {
        "text_length": float(len(value)), "word_count": float(len(words)),
        "unique_word_ratio": float(len(set(words)) / max(1, len(words))),
        "exclamation_count": float(value.count("!")),
        "uppercase_ratio": float(sum(c.isupper() for c in value) / max(1, alpha_count)),
        "digit_count": float(sum(c.isdigit() for c in value)),
        "url_count": float(len(re.findall(r"https?://\S+|www\.\S+", value, re.I))),
        "urgent_word_count": float(sum(word in SUSPICIOUS_WORDS for word in words)),
        "money_symbol_count": float(sum(value.count(symbol) for symbol in ("$", "€", "£"))),
        "question_count": float(value.count("?")),
        "has_phone_like": float(bool(re.search(r"\b\d{7,}\b", value))),
    }


def html_features(html: str) -> dict[str, float]:
    """Extract metadata only; never execute scripts or fetch referenced resources."""
    value = html or ""
    soup = BeautifulSoup(value, "html.parser")
    links = soup.find_all("a")
    hrefs = [link.get("href", "") for link in links]
    text = soup.get_text(" ", strip=True).lower()
    return {
        "html_length": float(len(value)), "tag_count": float(len(soup.find_all())),
        "link_count": float(len(links)),
        "external_link_ratio": float(sum(bool(re.match(r"https?://", href, re.I))
                                         for href in hrefs) / max(1, len(links))),
        "form_count": float(len(soup.find_all("form"))),
        "password_input_count": float(len(soup.select('input[type="password"]'))),
        "script_count": float(len(soup.find_all("script"))),
        "iframe_count": float(len(soup.find_all("iframe"))),
        "image_count": float(len(soup.find_all("img"))),
        "hidden_element_count": float(len(soup.select(
            '[type="hidden"], [style*="display:none"], [style*="visibility:hidden"]'))),
        "has_meta_refresh": float(bool(soup.find("meta", attrs={
            "http-equiv": re.compile("refresh", re.I)}))),
        "suspicious_word_count": float(sum(word in SUSPICIOUS_WORDS
                                            for word in re.findall(r"[a-z]+", text))),
    }
