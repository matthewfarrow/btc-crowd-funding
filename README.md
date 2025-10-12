# CITADEL – Angor Crowdfunding Analytics

FastAPI dashboard that surfaces bitcoin-native crowdfunding campaigns from the [Angor](https://angor.io/) ecosystem.  
The app pulls live data from the public Angor indexer when it is reachable, falls back to a bundled offline dataset when it is not, and renders server-side analytics that highlight total capital raised, investor counts, and top campaigns.

## Features
- **Live Angor data** – queries the testnet Angor indexer API for every project, including amount raised, amounts spent, and investor counts.
- **Optional Nostr enrichment** – if `nostr-sdk` is installed and relays are reachable, project metadata is enriched with Nostr project events.
- **Offline-safe fallback** – ships with curated demo projects so the dashboard still works without network access.
- **Aggregated insights** – calculates funding totals, completion percentages, and daily funding tallies for visualisation in the UI.
- **JSON API** – `GET /api/projects` returns the same project feed used by the dashboard.

## Project structure
```
app/
 ├── main.py            # FastAPI application & routes
 ├── views.py           # Dashboard view
 ├── analytics.py       # Aggregation utilities
 ├── angor_adapter.py   # Indexer/Nostr/demo data sources
 └── ...
templates/
 └── index.html         # Single-page dashboard
static/
 ├── style.css
 └── favicon.svg
data/
 └── angor_demo.json    # Offline sample projects
tests/
 └── test_app.py
```

## Getting started
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then visit [http://localhost:8000](http://localhost:8000).  
If the Angor indexer is unavailable the dashboard will automatically display the bundled demo projects.

## Running tests
```bash
pytest -v
```
Tests focus on the analytics layer and data normalisation helpers.

## Configuration notes
- No `.env` file is required for demo usage; the application runs without external credentials.
- The static file mount requires `aiofiles`, already included in `requirements.txt`.
- `nostr-sdk` is optional. If it cannot be imported the adapter simply skips Nostr enrichment and logs a warning.

## Roadmap ideas
1. Render daily funding trend charts using the calculated `daily_totals`.
2. Persist snapshots in SQLite so the dashboard can show historical diffs.
3. Re-introduce BTCPay analytics behind a feature flag when the upstream API access is restored.

---
Built by bitcoiners for bitcoiners ⚡️
