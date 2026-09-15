from __future__ import annotations

import datetime as dt

import pandas as pd

from morning.cache.store import load_all_revenue_history, load_margin, load_trading_value_history
from morning.config import WINDOWS
from morning.screening.revenue import is_one_year_high, latest_published_revenue, record_high_label
from morning.screening.trading_value import compute_top_n


def select_for_window(window: int, revenue_history: pd.DataFrame, upto_date: dt.date | None = None) -> list[dict]:
    """Run the two-stage screen (trading value top-N -> revenue new-high) for one window.

    Shared by the daily report (upto_date=None, i.e. "as of now") and the
    backtest (upto_date=some historical date), so both use identical logic.
    """
    history = load_trading_value_history(window, upto_date=upto_date)
    candidates = compute_top_n(window, history)

    latest_ohlc = (
        history.sort_values("date").groupby("code").last()[["open_price", "high_price", "low_price", "close_price"]]
        if not history.empty and "open_price" in history.columns
        else pd.DataFrame()
    )

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
                "total_trading_value": row.total_trading_value,
                "insufficient_history": row.insufficient_history,
                "days_available": row.days_available,
                "revenue_label": label,
                "pct_above_prior_record": pct,
                "yoy_pct": None if pd.isna(yoy_pct) else yoy_pct,
                "revenue_month": f"{int(rev['roc_year'])}/{int(rev['month']):02d}",
                "candle": _latest_candle(row.code, latest_ohlc),
            }
        )
    return passed


def _latest_candle(code: str, latest_ohlc: pd.DataFrame) -> dict | None:
    """Latest trading day's OHLC for one stock, for drawing a candlestick — display only."""
    if latest_ohlc.empty or code not in latest_ohlc.index:
        return None
    o, h, l, c = latest_ohlc.loc[code, ["open_price", "high_price", "low_price", "close_price"]]
    if pd.isna(o) or pd.isna(h) or pd.isna(l) or pd.isna(c):
        return None
    return {"open": o, "high": h, "low": l, "close": c, "is_red": c >= o}


def run() -> tuple[dict[int, list[dict]], int | None]:
    revenue_history = load_all_revenue_history()
    earliest_revenue_roc_year = int(revenue_history["roc_year"].min()) if not revenue_history.empty else None

    results: dict[int, list[dict]] = {window: select_for_window(window, revenue_history) for window in WINDOWS}

    # Gross margin is display-only (added after screening) — it does not affect
    # which companies are selected, only what's shown about them.
    margin_by_code = load_margin().set_index("code")["gross_margin_pct"].to_dict()
    for rows in results.values():
        for row in rows:
            margin = margin_by_code.get(row["code"])
            row["gross_margin_pct"] = None if pd.isna(margin) else margin

    on_windows_by_code: dict[str, list[int]] = {}
    for window, rows in results.items():
        for row in rows:
            on_windows_by_code.setdefault(row["code"], []).append(window)
    for rows in results.values():
        for row in rows:
            row["on_windows"] = on_windows_by_code[row["code"]]

    return results, earliest_revenue_roc_year
