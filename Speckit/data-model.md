# The Market-Efficient Transfer Matrix — Data Model

## Overview

Three data layers:
1. **Raw** — FBref CSVs as downloaded, untouched
2. **Processed** — Cleaned, merged, normalised CSV used by the ML engine
3. **API** — Pydantic-typed JSON contracts between backend and frontend

---

## Layer 1: Raw FBref CSV Sources

### `raw/fbref_standard_stats.csv`
Core playing time and goal contribution stats for all outfield players.

| FBref Column     | Internal Name     | Type    | Notes                          |
|------------------|-------------------|---------|--------------------------------|
| Player           | player_name       | string  | Full name                      |
| Squad            | club              | string  | Club name                      |
| Comp             | league            | string  | e.g. "Premier League"          |
| Pos              | position_raw      | string  | e.g. "MF,FW" — needs parsing  |
| Age              | age               | integer | At time of export               |
| 90s              | nineties_played   | float   | Total 90-min blocks played     |
| Gls              | goals             | integer | Goals scored                   |
| Ast              | assists           | integer | Assists                        |
| xG               | xg                | float   | Expected goals                 |
| xAG              | xag               | float   | Expected assisted goals        |
| PrgC             | progressive_carries | integer | Progressive carries           |
| PrgP             | progressive_passes | integer | Progressive passes            |

---

### `raw/fbref_passing.csv`
Detailed passing metrics. Merged on `player_name` + `club`.

| FBref Column     | Internal Name         | Type  | Notes                        |
|------------------|-----------------------|-------|------------------------------|
| Att              | passes_attempted      | int   | Total passes attempted       |
| Cmp%             | pass_completion_pct   | float | Pass completion %            |
| TotDist          | pass_total_distance   | int   | Total passing distance (yds) |
| PrgDist          | pass_progressive_dist | int   | Progressive passing distance |
| Att (Short)      | passes_short_att      | int   | Short passes attempted       |
| Cmp% (Short)     | passes_short_cmp_pct  | float |                              |
| Att (Medium)     | passes_medium_att     | int   |                              |
| Cmp% (Medium)    | passes_medium_cmp_pct | float |                              |
| Att (Long)       | passes_long_att       | int   |                              |
| Cmp% (Long)      | passes_long_cmp_pct   | float |                              |
| KP               | key_passes            | int   | Passes leading to shot       |
| 1/3              | passes_final_third    | int   | Passes into final third      |
| PPA              | passes_penalty_area   | int   | Passes into penalty area     |
| CrsPA            | crosses_penalty_area  | int   | Crosses into penalty area    |
| PrgP             | progressive_passes    | int   | (duplicate — use for verify) |

---

### `raw/fbref_gk_advanced.csv`
Goalkeeper-specific sweeping and shot-stopping metrics.

| FBref Column | Internal Name          | Type  | Notes                          |
|--------------|------------------------|-------|--------------------------------|
| GA90         | goals_against_per90    | float | Goals allowed per 90           |
| Save%        | save_pct               | float | Save percentage                |
| PSxG         | post_shot_xg           | float | Post-shot xG faced             |
| PSxG+/-      | psxg_diff              | float | PSxG vs goals — skill metric   |
| Launch%      | launched_pass_pct      | float | % passes launched (>40yds)     |
| AvgLen       | avg_pass_length        | float | Average pass length (yds)      |
| Opp          | crosses_faced          | int   | Crosses faced                  |
| Stp%         | crosses_stopped_pct    | float | % crosses claimed              |
| #OPA         | sweeper_actions        | int   | Defensive actions outside box  |
| AvgDist      | avg_sweeper_distance   | float | Avg distance from goal (yds)   |

---

## Layer 2: Processed Data Model

### `data/players_clean.csv`

One row per player. All numeric features are:
- Converted to **per-90** where they are counting stats
- **Z-score normalised** within position group

| Column              | Type   | Source         | Notes                                 |
|---------------------|--------|----------------|---------------------------------------|
| player_id           | string | generated      | `{player_name}_{club}` slugified      |
| player_name         | string | standard       |                                       |
| club                | string | standard       |                                       |
| league              | string | standard       |                                       |
| position_group      | string | derived        | GK / CM / CAM (simplified)            |
| age                 | int    | standard       |                                       |
| nineties_played     | float  | standard       | Not normalised — used for min filter  |
| market_value_m      | float  | mock_values    | £M, from mock_market_values.json      |
| **GK Features** (only if position_group == GK)                          |
| save_pct            | float  | gk_advanced    | normalised                            |
| psxg_diff           | float  | gk_advanced    | normalised                            |
| launched_pass_pct   | float  | gk_advanced    | normalised                            |
| avg_pass_length     | float  | gk_advanced    | normalised                            |
| crosses_stopped_pct | float  | gk_advanced    | normalised                            |
| sweeper_actions_p90 | float  | gk_advanced    | normalised                            |
| avg_sweeper_dist    | float  | gk_advanced    | normalised                            |
| goals_against_p90   | float  | gk_advanced    | normalised                            |
| **CM/CDM Features** (only if position_group == CM)                      |
| pass_completion_pct | float  | passing        | normalised                            |
| passes_progressive_p90 | float | passing      | normalised                            |
| pass_progressive_dist_p90 | float | passing   | normalised                            |
| key_passes_p90      | float  | passing        | normalised                            |
| passes_final_third_p90 | float | passing      | normalised                            |
| progressive_carries_p90 | float | standard    | normalised                            |
| xag_p90             | float  | standard       | normalised                            |
| passes_long_cmp_pct | float  | passing        | normalised                            |

---

### `data/mock_market_values.json`

```json
{
  "mike-maignan_ac-milan": 78.0,
  "alisson-becker_liverpool": 45.0,
  "ederson-moraes_manchester-city": 40.0,
  "...": "..."
}
```

Key format: `{player_id}` (same slugified format as `players_clean.csv`)
Value: estimated market value in £M (sourced from Transfermarkt, June 2025)

---

### `models/`

Persisted scikit-learn objects (joblib):

| File                  | Contents                              |
|-----------------------|---------------------------------------|
| `pca_gk.joblib`       | Fitted PCA for GK position group      |
| `pca_cm.joblib`       | Fitted PCA for CM/CDM position group  |
| `pca_cam.joblib`      | Fitted PCA for CAM position group     |
| `scaler_gk.joblib`    | StandardScaler fit for GK group       |
| `scaler_cm.joblib`    | StandardScaler fit for CM group       |
| `scaler_cam.joblib`   | StandardScaler fit for CAM group      |

---

## Layer 3: API Schemas (Pydantic / TypeScript)

### `PlayerSummary`
Used in search dropdown results and `SimilarityCard` header.

```typescript
interface PlayerSummary {
  player_id: string;           // "mike-maignan_ac-milan"
  player_name: string;         // "Mike Maignan"
  club: string;                // "AC Milan"
  league: string;              // "Serie A"
  position_group: string;      // "GK"
  age: number;                 // 29
  market_value_m: number;      // 78.0
}
```

---

### `PlayerDetail`
Extends `PlayerSummary` — includes stats dict for radar chart rendering.

```typescript
interface PlayerDetail extends PlayerSummary {
  stats: Record<string, number>;
  // e.g. { save_pct: 74.2, psxg_diff: 8.1, sweeper_actions_p90: 1.3, ... }
  // Values are RAW (un-normalised) for display purposes
  stat_labels: Record<string, string>;
  // e.g. { save_pct: "Save %", psxg_diff: "PSxG +/-", ... }
}
```

---

### `MatchResult`
One matched player returned by the `/match` endpoint.

```typescript
interface MatchResult {
  player: PlayerDetail;
  similarity_score: number;      // 0.0 – 1.0
  similarity_pct: number;        // 0 – 100 (rounded, for display)
  value_anomaly: boolean;        // sim > 0.85 AND value < 0.4 * target
  estimated_saving_m: number;    // target.market_value_m - player.market_value_m
}
```

---

### `MatchResponse`
Full response from `GET /match`.

```typescript
interface MatchResponse {
  target: PlayerDetail;
  budget_ceiling_m: number;
  matches: MatchResult[];        // Sorted by similarity_score DESC, max 5
  total_candidates: number;      // Count before budget filter
  filtered_count: number;        // Count after budget filter
}
```

---

## Radar Chart Axis Definitions

The 8 axes rendered in the `RadarChart` component, per position group:

### GK Axes
```
1. Save %              (save_pct)
2. PSxG +/-            (psxg_diff)
3. Sweeper Actions/90  (sweeper_actions_p90)
4. Avg Sweeper Dist    (avg_sweeper_dist)
5. Crosses Stopped %   (crosses_stopped_pct)
6. Launch Pass %       (launched_pass_pct)
7. Avg Pass Length     (avg_pass_length)
8. Goals Against/90    (goals_against_p90) [inverted — lower is better]
```

### CM/CDM Axes
```
1. Pass Completion %   (pass_completion_pct)
2. Progressive Passes/90 (passes_progressive_p90)
3. Key Passes/90       (key_passes_p90)
4. Passes Final 3rd/90 (passes_final_third_p90)
5. Progressive Carries/90 (progressive_carries_p90)
6. xAG/90             (xag_p90)
7. Long Pass Cmp %    (passes_long_cmp_pct)
8. Prog. Pass Dist/90 (pass_progressive_dist_p90)
```

> Note: For radar chart rendering, all values are re-scaled to 0–100
> using percentile rank within position group (not z-score), so the
> chart is interpretable without data science background.
