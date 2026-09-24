"""Generate clearly marked synthetic data for smoke tests only; never use for claims."""
from pathlib import Path
import csv
OUT=Path("data"); OUT.mkdir(exist_ok=True)
rows=[("https://example.com/welcome",0),("http://192.168.1.5/verify-login",1),("https://docs.python.org",0),("http://secure-account.example/urgent-update",1)]
with (OUT/"urls_synthetic_smoke.csv").open("w",newline="",encoding="utf8") as f:
    w=csv.writer(f); w.writerow(["url","label","dataset_note"]); w.writerows([(u,l,"SYNTHETIC SMOKE DATA - NOT FOR RESEARCH") for u,l in rows])
txt=[("Thanks for your meeting tomorrow.",0),("URGENT! Verify your account and claim your prize at http://bad.test",1),("Your receipt is attached for your records.",0),("Your wallet password expired, login now!",1)]
with (OUT/"text_synthetic_smoke.csv").open("w",newline="",encoding="utf8") as f:
    w=csv.writer(f); w.writerow(["text","label","dataset_note"]); w.writerows([(u,l,"SYNTHETIC SMOKE DATA - NOT FOR RESEARCH") for u,l in txt])
html=[("<html><body><h1>Welcome</h1><p>About our team</p></body></html>",0),
      ('<form><input type="password"><script>/* redirect */</script><a href="http://bad.test/verify">Verify</a></form>',1),
      ("<html><body><h1>Documentation</h1><a href='/help'>Help</a></body></html>",0),
      ('<meta http-equiv="refresh" content="0"><form><input type="password"></form>',1)]
with (OUT/"html_synthetic_smoke.csv").open("w",newline="",encoding="utf8") as f:
    w=csv.writer(f); w.writerow(["html","label","dataset_note"]); w.writerows([(u,l,"SYNTHETIC SMOKE DATA - NOT FOR RESEARCH") for u,l in html])
