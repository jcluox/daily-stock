from __future__ import annotations

import datetime as dt

import pandas as pd

from morning.cache.trading_calendar import known_trading_days
from morning.config import REVENUE_DIR, TPEX_DIR, TWSE_DIR


def save_daily(market: str, date: dt.date, df: pd.DataFrame) -> None:
    directory = TWSE_DIR if market == "twse" else TPEX_DIR
    directory.mkdir(parents=True, exist_ok=True)
    df.to_csv(directory / f"{date.strftime('%Y%m%d')}.csv", index=False)


def save_revenue_month(market: str, roc_year: int, month: int, df: pd.DataFrame) -> None:
    REVENUE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(REVENUE_DIR / f"{market}_{roc_year}_{month}.csv", index=False)


def load_trading_value_history(window_days: int) -> pd.DataFrame:
    """Concat the most recent `window_days` known trading days of TWSE+TPEx data."""
    days = known_trading_days()[-window_days:]
    frames = []
    for date in days:
        for market, directory in (("twse", TWSE_DIR), ("tpex", TPEX_DIR)):
            path = directory / f"{date.strftime('%Y%m%d')}.csv"
            if path.exists():
                df = pd.read_csv(path, dtype={"code": str})
                df["date"] = date
                df["market"] = market
                frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["code", "name", "trading_value", "date", "market"])
    return pd.concat(frames, ignore_index=True)


def load_all_revenue_history() -> pd.DataFrame:
    if not REVENUE_DIR.exists():
        return pd.DataFrame()
    frames = [pd.read_csv(f, dtype={"code": str}) for f in REVENUE_DIR.glob("*.csv")]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(["code", "roc_year", "month"]).reset_index(drop=True)
