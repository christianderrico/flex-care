# script da eseguire una volta: test/data/fixtures/fetch_fixtures.py
import requests
from pathlib import Path

BASE = "https://hl7.org/fhir/R4"
OUT  = Path(__file__).parent

pages = {
    "patient-examples.html":    f"{BASE}/patient-examples.html",
    "patient-definitions.html": f"{BASE}/patient-definitions.html",
    "patient.html":             f"{BASE}/patient.html",
}

for filename, url in pages.items():
    content = requests.get(url).text
    (OUT / filename).write_text(content, encoding="utf-8")
    print(f"Saved {filename}")