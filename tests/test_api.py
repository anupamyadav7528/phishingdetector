from fastapi.testclient import TestClient
from phishing_detector.api import app
client=TestClient(app)
def test_health():
    assert client.get("/health").status_code==200
def test_validation():
    assert client.post("/detect",json={}).status_code==422
def test_detect_without_artifacts_is_graceful():
    r=client.post("/detect",json={"url":"http://192.0.2.1/verify"}); assert r.status_code==200 and "risk_score" in r.json()
