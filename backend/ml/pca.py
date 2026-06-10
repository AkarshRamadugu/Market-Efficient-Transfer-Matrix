"""
pca.py
------
Fits and saves PCA + scaler models for all 5 position groups:
GK, CM, CAM, FWD, WNG

Run this once before starting the FastAPI server:
    python -m ml.pca
"""

import json
import os
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import joblib

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "..", "data", "processed", "players_clean.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# ── How many PCA components to keep ──────────────────────────────────────────
# 8 features → we try to keep enough components to explain 85%+ variance.
N_COMPONENTS = 6

# ── Feature columns per position group ───────────────────────────────────────
# These must exactly match the column names in players_clean.csv.
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


def fit_and_save(df: pd.DataFrame, position: str, features: list[str]) -> None:
    """
    For a given position group:
      1. Slice the relevant rows and columns
      2. Drop any rows still containing NaN
      3. Standardise with StandardScaler (mean=0, std=1)
      4. Fit PCA
      5. Transform the whole group into PCA space → save as .npy matrix
      6. Save player_id order as JSON 
      7. Persist scaler + pca objects with joblib
    """
    print(f"\n── {position} {'─'*40}")
    
    # 1 & 2. Filter to this position, select columns, and drop NaNs
    group = df[df["position_group"] == position].copy()
    X = group[features].dropna()
    valid_ids = group.loc[X.index, "player_id"].tolist()
    print(f"   Players: {len(X)}")

    # Defensive check: Ensure we have enough data to fit the requested components
    if len(X) < N_COMPONENTS + 1:
        raise ValueError(
            f"Not enough players in {position} group ({len(X)}) "
            f"to fit {N_COMPONENTS} components. Check data pipeline."
        )

    # 3. Standardise the data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 4. Fit the PCA
    pca = PCA(n_components=N_COMPONENTS, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    # Log the explained variance to ensure our math holds up
    cumulative = np.cumsum(pca.explained_variance_ratio_)
    for i, (ind, cum) in enumerate(zip(pca.explained_variance_ratio_, cumulative)):
        print(f"     PC{i+1}: {ind*100:5.1f}%  (cumulative: {cum*100:5.1f}%)")
    status = "✅" if cumulative[-1] >= 0.80 else "⚠️ "
    print(f"   {status} {cumulative[-1]*100:.1f}% variance explained")

    # 5. Save the mathematical vectors
    np.save(os.path.join(MODELS_DIR, f"vectors_{position.lower()}.npy"), X_pca)
    
    # 6. Save the ordered player IDs so we can decode the vectors later
    with open(os.path.join(MODELS_DIR, f"player_ids_{position.lower()}.json"), "w") as f:
        json.dump(valid_ids, f, indent=2)
        
    # 7. Save the mathematical models so the API can use them on the fly
    joblib.dump(scaler, os.path.join(MODELS_DIR, f"scaler_{position.lower()}.joblib"))
    joblib.dump(pca,    os.path.join(MODELS_DIR, f"pca_{position.lower()}.joblib"))
    print(f"   Saved → models/{position.lower()}.*")


def main():
    print("Loading players_clean.csv ...")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows across {df['position_group'].nunique()} position groups")
    
    # Loop through our expanded dictionary of 5 positions
    for position, features in POSITION_FEATURES.items():
        fit_and_save(df, position, features)
        
    print("\n✅ All models saved.")

if __name__ == "__main__":
    main()