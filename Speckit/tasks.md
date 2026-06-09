# The Market-Efficient Transfer Matrix — Tasks

## Status Key
- [ ] Not started
- [~] In progress
- [x] Done
- [!] Blocked

---

## Epic 1: Data Pipeline

### 1.1 Data Acquisition
- [ ] Download FBref Standard Stats CSV (2024–25, Big 5 leagues)
- [ ] Download FBref Passing CSV (2024–25, Big 5 leagues)
- [ ] Download FBref Advanced GK CSV (2024–25, Big 5 leagues)
- [ ] Download FBref Possession CSV (2024–25, Big 5 leagues)
- [ ] Store raw CSVs in `data/raw/`

### 1.2 Pipeline Script (`pipeline.py`)
- [ ] Ingest all CSVs using Pandas
- [ ] Standardise column names (map FBref headers to internal schema)
- [ ] Merge CSVs on `player_id` (FBref uses `player` + `squad` as key)
- [ ] Filter: minimum 900 minutes played
- [ ] Filter: positions to GK, CM, CDM, CAM only
- [ ] Convert counting stats to per-90 equivalents
- [ ] Handle missing values (median fill per position group)
- [ ] Z-score normalise all features within position groups
- [ ] Add mock market value from `mock_market_values.json`
- [ ] Export to `data/players_clean.csv`
- [ ] Export to `data/players.json` (for frontend mock during dev)

### 1.3 Validation
- [ ] Assert no NaN values in final output
- [ ] Assert all position groups have > 50 players
- [ ] Spot-check Maignan row manually for sanity

---

## Epic 2: ML Engine

### 2.1 PCA Module (`ml/pca.py`)
- [ ] Load `players_clean.csv`
- [ ] Split into position-group feature matrices (GK, CM/CDM, CAM)
- [ ] Fit PCA per group (default `n_components=8`)
- [ ] Log explained variance ratio — assert > 85%
- [ ] Persist fitted PCA objects with `joblib` to `models/`
- [ ] Write `transform(player_id)` function → returns PCA vector

### 2.2 Similarity Module (`ml/similarity.py`)
- [ ] Implement `cosine_similarity_matrix(group_matrix)` using sklearn
- [ ] Implement `get_top_n(player_id, n=5)` → sorted list of matches
- [ ] Include similarity score (0–1) in output
- [ ] Exclude same-club players from results
- [ ] Unit test: same player vs. self should return 1.0

### 2.3 Financial Filter (`ml/financial.py`)
- [ ] Load market values from `mock_market_values.json`
- [ ] Implement `filter_by_budget(matches, budget_ceiling_m)` 
- [ ] Implement `flag_value_anomaly(target, match)` 
  → True if similarity > 0.85 AND match_value < 0.4 * target_value
- [ ] Add `estimated_saving_m` field to each filtered match
- [ ] Unit test: player above budget ceiling should be excluded

---

## Epic 3: FastAPI Backend

### 3.1 Setup (`main.py`)
- [ ] Initialise FastAPI app
- [ ] Add CORS middleware (allow localhost:3000)
- [ ] Add startup event: load PCA models + player data into memory
- [ ] Add `/health` endpoint

### 3.2 Endpoints
- [ ] `GET /players` — return all players (id, name, club, position,
      market_value) for search dropdown
- [ ] `GET /player/{player_id}` — return full stat card for one player
- [ ] `GET /match?player_id={id}&budget={m}&n={n}` — run PCA +
      cosine similarity + financial filter, return top-N matches
- [ ] `GET /positions` — return available position filter values

### 3.3 Response Schemas (Pydantic)
- [ ] `PlayerSummary` schema (id, name, club, league, position, value)
- [ ] `PlayerDetail` schema (+ full stats dict for radar chart)
- [ ] `MatchResult` schema (player, similarity_score, value_anomaly,
      estimated_saving_m, stats)
- [ ] `MatchResponse` schema (target: PlayerDetail, matches: list[MatchResult])

---

## Epic 4: Frontend

### 4.1 Project Setup
- [ ] `npx create-next-app` with TypeScript + Tailwind
- [ ] Install Recharts: `npm install recharts`
- [ ] Set up dark theme in `tailwind.config.ts`
- [ ] Create `types/player.ts` with TypeScript interfaces
- [ ] Create `lib/api.ts` with typed fetch wrappers for all endpoints

### 4.2 Components
- [ ] `components/PlayerSearch.tsx`
  - Searchable dropdown (`/players` endpoint)
  - Position filter tabs (GK / CM / CAM)
  - On select: triggers match query
- [ ] `components/StatCard.tsx`
  - Target player card: name, club, league, market value
  - Key stat summary (3–4 headline numbers)
- [ ] `components/RadarChart.tsx`
  - 8-axis Recharts `RadarChart`
  - Two overlaid `Radar` fills (target in Chelsea blue, match in amber)
  - Configurable axis labels from stat names
- [ ] `components/SimilarityCard.tsx`
  - Similarity score badge (colour-coded: green > 85%, amber 70–85%)
  - Market value delta vs. target
  - PSR saving label (green highlight if value anomaly flagged)
  - Expand to show RadarChart on click
- [ ] `components/ScatterPlot.tsx`
  - Recharts `ScatterChart`: x = similarity score, y = market value
  - Budget ceiling drawn as `ReferenceLine`
  - Each point labelled with player surname on hover
  - Target player highlighted separately

### 4.3 Pages
- [ ] `app/page.tsx` — main dashboard layout
  - Left panel: `PlayerSearch` + `StatCard`
  - Right panel: top `SimilarityCard` with expanded `RadarChart`
  - Bottom panel: `ScatterPlot` of all candidates
- [ ] `app/loading.tsx` — skeleton states for all panels
- [ ] Responsive layout (stacked on < 768px for mobile demo)

### 4.4 State Management
- [ ] `useState` for selected target player
- [ ] `useState` for budget ceiling (slider: £5M–£100M)
- [ ] `useState` for selected match (which `SimilarityCard` is expanded)
- [ ] `useEffect` to re-fetch `/match` when budget slider changes

---

## Epic 5: Polish & Demo Prep

- [ ] Dark theme with Chelsea blue (`#034694`) accent colour
- [ ] Hardcode Maignan as default player on page load
- [ ] Add "PSR Headroom Saved" banner when value anomaly is found
- [ ] Write `DEMO.md` with exact click-by-click pitch script
- [ ] Rehearse demo end-to-end (target: under 3 minutes)
- [ ] Prepare 1-slide summary: concept + results for Maignan case

---

## Dependency Order

```
1.1 → 1.2 → 1.3
            ↓
          2.1 → 2.2 → 2.3
                        ↓
                      3.1 → 3.2 → 3.3
                                    ↓
                    4.1 → 4.2 → 4.3 → 4.4
                                          ↓
                                        5.*
```

Frontend (4.1 → 4.2) can begin in parallel with Epic 2 using
`data/players.json` as a mock. Unblock Epic 4 from Epic 3 dependency
until Day 2 afternoon API integration step.
