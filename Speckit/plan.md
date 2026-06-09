# The Market-Efficient Transfer Matrix — Plan

## Timeline: 2-Day Hackathon Sprint

---

## Day 1 — Data & Backend (8–10 hours)

### Morning Block (0–4h): Data Pipeline
**Goal:** Clean, normalised player dataset ready for ML input.

| Hour | Work |
|------|------|
| 0–1  | Download FBref CSVs: Standard Stats, Passing, GK Advanced |
| 1–3  | Write `pipeline.py`: ingest, clean, merge, per-90 normalise |
| 3–4  | Validate output, write `players.json` snapshot for frontend dev |

**Deliverable:** `data/players_clean.csv` with ~500 rows, ~40 features

**Risks:**
- FBref column naming is inconsistent across position CSVs → budget
  30 mins extra for column mapping
- Missing values for low-minute players → drop players under 900 mins

---

### Afternoon Block (4–8h): ML Engine + FastAPI

| Hour | Work |
|------|------|
| 4–5  | Write `ml/pca.py`: fit PCA on position-grouped feature matrices |
| 5–6  | Write `ml/similarity.py`: cosine similarity, top-N ranking |
| 6–7  | Write `ml/financial.py`: market value filter + value anomaly flag |
| 7–8  | Wire all three into FastAPI: `GET /match?player_id=&budget=` |

**Deliverable:** API returning JSON with 5 matched players + scores

**Risks:**
- PCA component count needs tuning — start with 8, adjust by
  explained variance (target: 85%+)
- Cosine similarity on raw stats (not per-90) gives wrong results →
  enforce normalisation before fitting PCA

---

### Evening Buffer (8–10h): Integration Test + Mock Data

| Hour | Work |
|------|------|
| 8–9  | Test API end-to-end with Maignan as target player |
| 9–10 | Build `mock_market_values.json` (Transfermarkt estimates) |

---

## Day 2 — Frontend & Polish (8–10 hours)

### Morning Block (0–4h): Core UI

| Hour | Work |
|------|------|
| 0–1  | Scaffold Next.js app, install Tailwind + Recharts |
| 1–2  | Build `PlayerSearch` component (searchable dropdown) |
| 2–3  | Build `RadarChart` component (8-axis, two-player overlay) |
| 3–4  | Build `SimilarityCard` component (score badge + value delta) |

**Deliverable:** Static UI rendering with mock JSON data

---

### Afternoon Block (4–7h): API Integration + Scatter Plot

| Hour | Work |
|------|------|
| 4–5  | Connect frontend to FastAPI (`/match` endpoint) |
| 5–6  | Build `ScatterPlot` component (similarity vs. market value) |
| 6–7  | Add budget ceiling slider → triggers new API call |

**Deliverable:** Fully wired, interactive dashboard

---

### Evening Block (7–10h): Demo Polish

| Hour | Work |
|------|------|
| 7–8  | Visual polish: dark theme, Chelsea blue accents, clean typography |
| 8–9  | Hardcode Maignan demo path for pitch reliability |
| 9–10 | Write pitch talking points, rehearse 3-minute demo flow |

---

## Architecture Overview

```
FBref CSVs
    │
    ▼
pipeline.py          ← clean, merge, normalise, per-90
    │
    ▼
players_clean.csv
    │
    ▼
FastAPI (main.py)
  ├── /players        ← list all players (for search dropdown)
  ├── /match          ← PCA + cosine similarity + financial filter
  └── /player/{id}    ← single player stat card
    │
    ▼
Next.js Frontend
  ├── PlayerSearch
  ├── StatCard
  ├── RadarChart       ← Recharts RadarChart
  ├── SimilarityCard
  └── ScatterPlot      ← Recharts ScatterChart
```

---

## Key Decisions

### Why PCA before cosine similarity?
Raw feature vectors contain highly correlated stats (e.g., passes
attempted vs. passes completed). PCA decorrelates them, giving each
dimension independent meaning. Cosine similarity on correlated vectors
overfits to whichever cluster of correlated stats happens to be largest.

### Why cosine similarity over Euclidean distance?
Playing style (the ratio/shape of stats) matters more than volume.
A player with 40 passes per game and 85% accuracy is more similar to
one with 35 passes at 87% than one with 40 passes at 60%. Cosine
captures angular distance (shape), not magnitude.

### Why position-group the PCA fit?
A goalkeeper's save% has no meaning in the midfielder feature space.
Fitting separate PCAs per position group ensures the reduced dimensions
are meaningful within each role.

### Why mock market values?
Transfermarkt scraping is brittle and slow. For a hackathon demo,
a well-researched static JSON file (sourced from Transfermarkt manually
for ~100 key players) is more reliable and pitchable.

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| FBref CSV format changes | Medium | Download and snapshot CSVs on Day 1 morning |
| API CORS issues | Low | Add FastAPI CORS middleware from the start |
| Radar chart misaligned axes | Medium | Test with 2 hardcoded players before wiring API |
| PCA variance too low | Low | Increase n_components until 85% variance explained |
| Demo player not in dataset | Medium | Pre-verify Maignan + 3 backup targets exist in data |
