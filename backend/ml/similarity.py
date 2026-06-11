"""
similarity.py
-------------
Cosine similarity matching on PCA-reduced vectors.
Supports all 5 position groups: GK, CM, CAM, FWD, WNG.
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib  # noqa: F401

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH  = os.path.join(BASE_DIR, "..", "data", "processed", "players_clean.csv")

# ── Feature columns per position (for stats dict / radar chart) ───────────────
POSITION_FEATURES = {
    "GK": [
        "save_pct", "psxg_diff", "launched_pass_pct", "avg_pass_length",
        "crosses_stopped_pct", "sweeper_actions_p90", "avg_sweeper_dist",
        "goals_against_p90",
    ],
    "CM": [
        "pass_completion_pct", "passes_progressive_p90", "pass_progressive_dist_p90",
        "key_passes_p90", "passes_final_third_p90", "progressive_carries_p90",
        "xag_p90", "passes_long_cmp_pct",
    ],
    "CAM": [
        "cam_key_passes_p90", "cam_xag_p90", "cam_progressive_passes_p90",
        "cam_passes_penalty_area_p90", "cam_progressive_carries_p90",
        "cam_shot_creating_actions_p90", "cam_pass_completion_pct",
        "cam_final_third_passes_p90",
    ],
    "FWD": [
        "goals_p90", "xg_p90", "shots_on_target_p90", "shot_creating_actions_p90",
        "xg_per_shot", "aerial_win_pct", "touches_att_pen_p90", "npxg_p90",
    ],
    "WNG": [
        "wng_goals_p90", "wng_assists_p90", "wng_xag_p90",
        "successful_dribbles_p90", "progressive_carries_p90_wng",
        "crosses_p90", "wng_touches_att_third_p90", "wng_shot_creating_p90",
    ],
}

# Human-readable axis labels for the radar chart
STAT_LABELS = {
    # GK
    "save_pct": "Save %", "psxg_diff": "PSxG +/-", "launched_pass_pct": "Launch Pass %",
    "avg_pass_length": "Avg Pass Len", "crosses_stopped_pct": "Crosses Stopped %",
    "sweeper_actions_p90": "Sweeper Actions", "avg_sweeper_dist": "Sweeper Distance",
    "goals_against_p90": "Goals Against/90",
    # CM
    "pass_completion_pct": "Pass Completion %", "passes_progressive_p90": "Progressive Passes",
    "pass_progressive_dist_p90": "Prog. Pass Dist", "key_passes_p90": "Key Passes",
    "passes_final_third_p90": "Final Third Passes", "progressive_carries_p90": "Prog. Carries",
    "xag_p90": "xAG/90", "passes_long_cmp_pct": "Long Pass Cmp %",
    # CAM
    "cam_key_passes_p90": "Key Passes", "cam_xag_p90": "xAG/90",
    "cam_progressive_passes_p90": "Progressive Passes", "cam_passes_penalty_area_p90": "Passes into Box",
    "cam_progressive_carries_p90": "Prog. Carries", "cam_shot_creating_actions_p90": "Shot Creating Actions",
    "cam_pass_completion_pct": "Pass Completion %", "cam_final_third_passes_p90": "Final Third Passes",
    # FWD
    "goals_p90": "Goals/90", "xg_p90": "xG/90", "shots_on_target_p90": "Shots on Target",
    "shot_creating_actions_p90": "Shot Creating Actions", "xg_per_shot": "xG per Shot",
    "aerial_win_pct": "Aerial Win %", "touches_att_pen_p90": "Touches in Box", "npxg_p90": "npxG/90",
    # WNG
    "wng_goals_p90": "Goals/90", "wng_assists_p90": "Assists/90", "wng_xag_p90": "xAG/90",
    "successful_dribbles_p90": "Dribbles/90", "progressive_carries_p90_wng": "Prog. Carries",
    "crosses_p90": "Crosses/90", "wng_touches_att_third_p90": "Att. Third Touches",
    "wng_shot_creating_p90": "Shot Creating Actions",
}

_cache: dict = {}


def _load(position: str) -> dict:
    pos = position.upper()
    if pos in _cache:
        return _cache[pos]
    p = pos.lower()
    _cache[pos] = {
        "vectors":    np.load(os.path.join(MODELS_DIR, f"vectors_{p}.npy")),
        "player_ids": json.load(open(os.path.join(MODELS_DIR, f"player_ids_{p}.json"))),
        "df":         pd.read_csv(DATA_PATH),
    }
    return _cache[pos]


def get_top_matches(target_player_id: str, n: int = 5) -> list[dict]:
    df_all = pd.read_csv(DATA_PATH)
    target_row = df_all[df_all["player_id"] == target_player_id]
    if target_row.empty:
        raise ValueError(f"Player '{target_player_id}' not found.")

    target_row  = target_row.iloc[0]
    position    = target_row["position_group"]
    target_club = target_row["club"]

    cache      = _load(position)
    vectors    = cache["vectors"]
    player_ids = cache["player_ids"]

    if target_player_id not in player_ids:
        raise ValueError(f"Player '{target_player_id}' was excluded from PCA (NaN stats?).")

    target_vec = vectors[player_ids.index(target_player_id)].reshape(1, -1)
    sims       = cosine_similarity(target_vec, vectors)[0]
    ranked     = np.argsort(sims)[::-1]

    results = []
    for idx in ranked:
        pid = player_ids[idx]
        if pid == target_player_id:
            continue
        row = df_all[df_all["player_id"] == pid]
        if row.empty:
            continue
        row = row.iloc[0]
        if row["club"] == target_club:
            continue

        score = float(sims[idx])
        results.append({
            "player_id":       pid,
            "player_name":     row["player_name"],
            "club":            row["club"],
            "league":          row["league"],
            "position_group":  position,
            "age":             int(row["age"]),
            "minutes_played":  int(row["minutes_played"]),
            "market_value_m":  float(row["market_value_m"]),
            "similarity_score": round(score, 4),
            "similarity_pct":   int(round(score * 100)),
            "stats":            _build_stats_dict(row, position),
            "stat_labels":      {k: STAT_LABELS.get(k, k) for k in POSITION_FEATURES[position]},
        })
        if len(results) >= n * 4:
            break

    return results


def get_player_detail(player_id: str) -> dict:
    df_all = pd.read_csv(DATA_PATH)
    row = df_all[df_all["player_id"] == player_id]
    if row.empty:
        raise ValueError(f"Player '{player_id}' not found.")
    row = row.iloc[0]
    position = row["position_group"]
    return {
        "player_id":      player_id,
        "player_name":    row["player_name"],
        "club":           row["club"],
        "league":         row["league"],
        "position_group": position,
        "age":            int(row["age"]),
        "minutes_played": int(row["minutes_played"]),
        "market_value_m": float(row["market_value_m"]),
        "stats":          _build_stats_dict(row, position),
        "stat_labels":    {k: STAT_LABELS.get(k, k) for k in POSITION_FEATURES[position]},
    }


def get_all_players() -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    return df[["player_id","player_name","club","league","position_group","age","market_value_m"]]\
             .sort_values("player_name")\
             .to_dict(orient="records")


def _build_stats_dict(row: pd.Series, position: str) -> dict:
    return {
        k: (round(float(row[k]), 3) if pd.notna(row[k]) else 0.0)
        for k in POSITION_FEATURES[position]
    }
