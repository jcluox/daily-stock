from __future__ import annotations

import pandas as pd

from morning.cache.store import load_all_revenue_history, load_trading_value_history
from morning.config import WINDOWS
from morning.screening.revenue import is_one_year_high, latest_published_revenue, record_high_label
from morning.screening.trading_value import compute_top_n


def run() -> dict[int, list[dict]]:
    revenue_history = load_all_revenue_history()
    results: dict[int, list[dict]] = {}

    for window in WINDOWS:
        history = load_trading_value_history(window)
        candidates = compute_top_n(window, history)

        passed = []
        for row in candidates.itertuples():
            rev = latest_published_revenue(row.code, revenue_history)
            if rev is None:
                continue
            if not is_one_year_high(row.code, revenue_history):
                continue
            label, pct = record_high_label(row.code, revenue_history)
            yoy_pct = rev["yoy_pct"]
            passed.append(
                {
                    "rank": row.rank,
                    "code": row.code,
                    "name": row.name,
                    "avg_trading_value": row.avg_trading_value,
                    "insufficient_history": row.insufficient_history,
                    "days_available": row.days_available,
                    "revenue_label": label,
                    "pct_above_prior_record": pct,
                    "yoy_pct": None if pd.isna(yoy_pct) else yoy_pct,
                    "revenue_month": f"{int(rev['roc_year'])}/{int(rev['month']):02d}",
                }
            )
        results[window] = passed

    return results
