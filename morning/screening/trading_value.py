from __future__ import annotations

import pandas as pd

from morning.config import TOP_N


def compute_top_n(window_days: int, history: pd.DataFrame) -> pd.DataFrame:
    """Rank stocks by average trading value over the last `window_days` trading days.

    `history` must already be limited to the last `window_days` known trading
    days (see cache.store.load_trading_value_history). Returns the top TOP_N
    stocks with columns [code, name, avg_trading_value, days_available,
    insufficient_history, rank].
    """
    if history.empty:
        return pd.DataFrame(
            columns=["code", "name", "avg_trading_value", "days_available", "insufficient_history", "rank"]
        )

    grouped = history.groupby("code").agg(
        avg_trading_value=("trading_value", "mean"),
        days_available=("date", "nunique"),
        name=("name", "first"),
    )
    grouped["insufficient_history"] = grouped["days_available"] < window_days
    grouped = grouped.sort_values("avg_trading_value", ascending=False).reset_index()
    grouped["rank"] = range(1, len(grouped) + 1)
    return grouped.head(TOP_N)
