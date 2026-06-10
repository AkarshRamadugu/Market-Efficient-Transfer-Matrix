"""
financial.py
------------
Applies the PSR financial constraints filter on top of similarity results.

Takes the raw list from similarity.get_top_matches() and:
  1. Filters out players above the budget ceiling
  2. Flags "value anomalies" (high similarity, low cost = PSR steal)
  3. Adds estimated_saving_m field
  4. Returns the final top N results

Usage:
    from ml.financial import apply_financial_filter
    filtered = apply_financial_filter(matches, target, budget_ceiling_m=25.0, n=5)
"""


# ── Thresholds ─────────────────────────────────────────────────────────────────
# These are the two conditions that trigger a "value anomaly" (PSR steal) badge.

ANOMALY_SIMILARITY_THRESHOLD = 0.80   # similarity_score must be above this
ANOMALY_VALUE_RATIO           = 0.50  # match market value must be below this
                                       # fraction of the target's market value
                                       # e.g. 0.50 = less than 50% of target cost


def apply_financial_filter(
    matches: list[dict],
    target: dict,
    budget_ceiling_m: float,
    n: int = 5,
) -> list[dict]:
    """
    Filter and annotate similarity matches with financial data.

    Parameters
    ----------
    matches : list[dict]
        Raw output from similarity.get_top_matches() — already sorted by
        similarity descending, may contain up to n*4 candidates.
    target : dict
        The target player's detail dict (from similarity.get_player_detail()).
        Must contain 'market_value_m'.
    budget_ceiling_m : float
        Maximum transfer fee the club can spend (in £M).
        Players above this are excluded from results.
    n : int
        Maximum number of results to return after filtering (default 5).

    Returns
    -------
    List of annotated match dicts, each with extra fields:
        {
          ...all fields from similarity.get_top_matches()...,
          "value_anomaly":      True/False,
          "estimated_saving_m": 52.1,   ← target_value - match_value
          "anomaly_reason":     "89% similarity at 24% of target cost"
                                 (only present if value_anomaly=True)
        }
    """

    target_value = target.get("market_value_m", 0.0)
    filtered = []

    for match in matches:
        match_value = match.get("market_value_m", 0.0)

        # ── Budget gate ───────────────────────────────────────────────────────
        # Hard exclusion — if the player costs more than the budget, skip them.
        if match_value > budget_ceiling_m:
            continue

        # ── Value anomaly detection ───────────────────────────────────────────
        # A "PSR steal" is a player who is statistically very close to the
        # target but costs a fraction of the price.
        similarity = match["similarity_score"]
        is_anomaly = (
            similarity >= ANOMALY_SIMILARITY_THRESHOLD
            and target_value > 0
            and match_value <= target_value * ANOMALY_VALUE_RATIO
        )

        saving = round(target_value - match_value, 1)

        annotated = {
            **match,
            "value_anomaly":      is_anomaly,
            "estimated_saving_m": saving,
        }

        if is_anomaly:
            cost_pct = int(round((match_value / target_value) * 100))
            annotated["anomaly_reason"] = (
                f"{match['similarity_pct']}% similarity "
                f"at {cost_pct}% of target cost"
            )

        filtered.append(annotated)

        # Stop once we have enough results
        if len(filtered) >= n:
            break

    return filtered


def build_match_response(
    target: dict,
    all_candidates: list[dict],
    filtered_matches: list[dict],
    budget_ceiling_m: float,
) -> dict:
    """
    Assembles the final JSON response object returned by GET /match.

    Parameters
    ----------
    target           : full player detail dict for the search target
    all_candidates   : unfiltered matches list (used for total_candidates count)
    filtered_matches : output of apply_financial_filter()
    budget_ceiling_m : the budget ceiling used for this query

    Returns
    -------
    {
      "target":           { ...PlayerDetail... },
      "budget_ceiling_m": 25.0,
      "matches":          [ ...MatchResult... ],
      "total_candidates": 18,
      "filtered_count":   5,
    }
    """
    return {
        "target":           target,
        "budget_ceiling_m": budget_ceiling_m,
        "matches":          filtered_matches,
        "total_candidates": len(all_candidates),
        "filtered_count":   len(filtered_matches),
    }
