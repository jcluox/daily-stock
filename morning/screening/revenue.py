from __future__ import annotations

import pandas as pd

from morning.config import ONE_YEAR_MONTHS
from morning.dateutil_roc import months_between


def _company_series(code: str, revenue_history: pd.DataFrame) -> pd.DataFrame:
    return revenue_history[revenue_history["code"] == code].sort_values(["roc_year", "month"]).reset_index(drop=True)


def latest_published_revenue(code: str, revenue_history: pd.DataFrame) -> pd.Series | None:
    series = _company_series(code, revenue_history)
    if series.empty:
        return None
    return series.iloc[-1]


def is_one_year_high(code: str, revenue_history: pd.DataFrame) -> bool:
    series = _company_series(code, revenue_history)
    if len(series) < 2:
        return False
    current = series.iloc[-1]["revenue_this_month"]
    prior = series.iloc[max(0, len(series) - 1 - ONE_YEAR_MONTHS) : -1]
    if prior.empty:
        return False
    return bool((current > prior["revenue_this_month"]).all())


def record_high_label(code: str, revenue_history: pd.DataFrame) -> tuple[str, float | None]:
    """Returns (label, pct_above_prior_record).

    label is "史上新高" if no earlier month in the retained history reaches
    the current month's revenue, otherwise "X年新高" where X is the number
    of years since the most recent earlier month that was >= current.
    pct_above_prior_record compares current against the highest point
    within the window it just broke (the record it actually surpassed).
    """
    series = _company_series(code, revenue_history)
    current_row = series.iloc[-1]
    current = current_row["revenue_this_month"]
    earlier = series.iloc[:-1]

    if earlier.empty:
        return "史上新高", None

    boundary_idx = None
    for idx in range(len(earlier) - 1, -1, -1):
        if earlier.iloc[idx]["revenue_this_month"] >= current:
            boundary_idx = idx
            break

    if boundary_idx is None:
        prior_max = earlier["revenue_this_month"].max()
        pct = (current - prior_max) / prior_max * 100 if prior_max else None
        return "史上新高", pct

    window = earlier.iloc[boundary_idx + 1 :]
    boundary_row = earlier.iloc[boundary_idx]
    prior_record = window["revenue_this_month"].max() if not window.empty else boundary_row["revenue_this_month"]
    pct = (current - prior_record) / prior_record * 100 if prior_record else None

    gap_months = months_between(
        int(boundary_row["roc_year"]), int(boundary_row["month"]), int(current_row["roc_year"]), int(current_row["month"])
    )
    gap_years = max(1, gap_months // 12)
    return f"{gap_years}年新高", pct
