from phishing_detector.features import html_features, text_features, url_features
def test_url_features():
    x=url_features("http://192.0.2.1/verify-login?x=1"); assert x["has_ip"]==1 and x["suspicious_token_count"]>=1
def test_text_features():
    assert text_features("URGENT! login now")["urgent_word_count"] >= 1
def test_html_is_safe_and_structured():
    x=html_features('<form><input type="password"></form><script>alert(1)</script>'); assert x["form_count"]==1 and x["password_input_count"]==1
