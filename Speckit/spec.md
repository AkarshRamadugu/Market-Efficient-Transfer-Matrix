# The Market-Efficient Transfer Matrix — Spec

## Overview

A scouting intelligence dashboard for sporting directors to identify
statistically similar, financially compliant alternatives to target
players. Built specifically around Chelsea FC's 2026 PSR crisis as the
demo narrative, but generalizable to any club operating under
Premier League Profit & Sustainability Rules.

---

## Problem Statement

Chelsea FC have accumulated ~£1.1B in transfer spend since 2022.
PSR rules cap allowable losses at £105M over a rolling 3-year window.
The club cannot simply buy the best player available — they must find
undervalued statistical equivalents at a fraction of the market price.

Current scouting tools (Wyscout, StatsBomb IQ) show similarity but
do not co-optimise for financial constraints. This tool does.

---

## Core Concept

Treat every player's season statistics as a high-dimensional vector.
Apply PCA to reduce dimensionality and remove correlated noise.
Use cosine similarity on the reduced space to find "statistical twins."
Filter results through a financial constraints engine using estimated
market values (Transfermarkt) to surface only PSR-compliant targets.

---

## Target Users

- Sporting Directors at Premier League clubs
- Head of Recruitment / Chief Scout
- Data Analytics department leads

---

## Scope (Hackathon MVP)

### In Scope
- Goalkeeper and Central Midfielder position profiles
- Top 5 European leagues (PL, La Liga, Serie A, Bundesliga, Ligue 1)
- One target player search at a time (e.g., Mike Maignan)
- Top 5 statistical twin results with similarity scores
- Market value ceiling filter (PSR compliance gate)
- Radar chart overlay: target player vs. recommended alternative
- Scatter plot: similarity score vs. estimated market value

### Out of Scope (Post-Hackathon)
- Real-time data feeds (API integrations with StatsBomb/Opta)
- Multi-player comparison (more than 1 target at a time)
- Contract length / wage bill modelling
- Agent fee and sell-on clause modelling
- Full squad PSR budget allocation tool

---

## Key Features

### 1. Player Search & Target Selection
- Searchable dropdown of all players in the dataset
- Position filter (GK, CM, CDM, AM)
- Display target player's full stat card on selection

### 2. AI Matching Engine
- PCA dimensionality reduction (configurable n_components, default: 8)
- Cosine similarity ranking across all players in same position group
- Returns top 5 matches with % similarity score
- Excludes players from same club as target

### 3. Financial Constraints Engine
- Input: Max transfer budget (£M) — defaults to £25M for demo
- Filters similarity results to only show players within budget
- Flags "value anomaly" if similarity > 85% and value < 40% of target
- Shows estimated saving vs. target player acquisition cost

### 4. Player Comparison Dashboard
- Radar chart: 8-axis overlay of target vs. recommended twin
- Similarity score badge (0–100%)
- Estimated market value vs. target player delta
- Estimated PSR saving label
- Scatter plot: all candidates plotted by similarity vs. market value
  with a budget ceiling line drawn across the chart

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Frontend    | Next.js 14 (App Router), TypeScript |
| Styling     | Tailwind CSS                      |
| Charts      | Recharts                          |
| Backend     | Python 3.11, FastAPI              |
| ML/Math     | Scikit-learn, NumPy, Pandas       |
| Data        | FBref / StatsBomb CSV exports     |
| Market Data | Transfermarkt (scraped / mocked)  |
| Dev         | Docker Compose (optional for demo)|

---

## Demo Narrative (Hackathon Pitch)

> "Chelsea paid £78M for Maignan. Here are three goalkeepers with
> 89%+ similarity scores, all available under £20M — saving the club
> £58M in PSR headroom."

The entire UI should be optimised to make this one story land clearly.

---

## Success Criteria

- [ ] Data pipeline ingests and cleans FBref CSV in under 5 seconds
- [ ] ML engine returns 5 similarity results in under 2 seconds
- [ ] Radar chart renders correctly for any GK or CM pairing
- [ ] Financial filter correctly excludes players above budget ceiling
- [ ] Demo narrative is deliverable end-to-end in under 3 minutes
