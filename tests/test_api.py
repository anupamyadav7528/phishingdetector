from fastapi.testclient import TestClient
from phishing_detector.api import app
client=TestClient(app)
def test_health():
    assert client.get("/health").status_code==200
def test_validation():
    assert client.post("/detect",json={}).status_code==422
def test_detect_without_artifacts_is_graceful():
    r=client.post("/detect",json={"url":"http://192.0.2.1/verify"}); assert r.status_code==200 and "risk_score" in r.json()

def test_representative_inputs_get_meaningful_risk_scores():
    suspicious = client.post("/detect", json={
        "text": "URGENT: Your PayPal account is suspended. Click now to verify your password and pay the fee."
    }).json()
    benign = client.post("/detect", json={
        "text": "The team meeting is scheduled for tomorrow at 10 AM."
    }).json()
    assert suspicious["risk_score"] > benign["risk_score"]
    assert suspicious["label"] == "suspicious"
