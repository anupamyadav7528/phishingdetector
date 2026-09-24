# Undergraduate AI phishing/scam detector

Local-first reference project combining explainable URL lexical features, message/email text preprocessing, and **non-executing** HTML parsing. It is an educational aid, not a security guarantee. Never paste credentials, access tokens, private customer data, or malware into it.

## Windows quick start

In PowerShell:

```powershell
.\setup.ps1
.\.venv\Scripts\Activate.ps1
```

The setup script creates the virtual environment, installs dependencies, and generates synthetic smoke CSVs. To run manually instead:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py scripts\generate_smoke_data.py
py -m pytest
uvicorn phishing_detector.api:app --reload
```

Open http://127.0.0.1:8000. `GET /health` reports missing artifacts safely; the dashboard still runs.

## Training and CSV schemas

Use a local, legally obtained dataset only. Every CSV needs a binary `label` column (`1` phishing/scam, `0` benign), plus one input column:

* URL: `url,label`
* text/email: `text,label`
* HTML: `html,label`

Train independently: `py scripts\train.py --kind url --csv data\urls.csv`, or `text`/`html`. Artifacts and evaluation metadata (accuracy, precision, recall, F1, ROC-AUC, PR-AUC when defined, confusion matrix) go to `artifacts/`. The included `*_synthetic_smoke.csv` files are clearly marked synthetic and are only for pipeline smoke testing, not performance claims. Use representative train/test splits and report dataset provenance, class balance, and limitations in real work.

## API

`POST /detect` accepts one or more of `url`, `text`, and `html` (bounded request sizes), and returns calibrated-style probability scores when a model exists, labels, component scores, and simple explanations. Missing model files result in a valid response with an explanation rather than a server error. `GET /health` reports loaded model kinds.

## Security, privacy, and extension outline

HTML is parsed as text: scripts are never run and links/resources are never fetched. Keep the service bound to localhost, authenticate and rate-limit before network exposure, validate uploads, and keep logs free of user content. A future browser extension should use a least-privilege content script, send only the current URL (or explicit user selection) to a local API, display uncertainty and explanations, and provide a clear opt-out; do not silently collect browsing history.

No paid service, secret, or external API is required. `.env.example` documents optional local settings.

## Optional Render deployment

`render.yaml` defines a free web service. Create a Render Blueprint from this repository and deploy it; Render supplies `PORT` automatically. During every Render build, the service generates the clearly marked synthetic smoke CSVs and trains URL, text, and HTML demo models into `artifacts/`. These models are demo-only and must not be used for security decisions or performance claims. No API credential is required by this project. A redeploy is required after changing `render.yaml`; the build log should show all three training commands and `/health` should list `html`, `text`, and `url`.
