from __future__ import annotations

import datetime as dt

import pandas as pd

from morning.cache.trading_calendar import known_trading_days
from morning.config import DATA_DIR, REVENUE_DIR, TPEX_DIR, TWSE_DIR
from morning.dateutil_roc import revenue_known_date

INDEX_FILE = DATA_DIR / "raw" / "index" / "taiex.csv"


def save_daily(market: str, date: dt.date, df: pd.DataFrame) -> None:
    directory = TWSE_DIR if market == "twse" else TPEX_DIR
    directory.mkdir(parents=True, exist_ok=True)
    df.to_csv(directory / f"{date.strftime('%Y%m%d')}.csv", index=False)


def save_revenue_month(market: str, roc_year: int, month: int, df: pd.DataFrame) -> None:
    REVENUE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(REVENUE_DIR / f"{market}_{roc_year}_{month}.csv", index=False)


def save_index_point(date: dt.date, close: float) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = load_index_history()
    existing = existing[existing["date"] != date.isoformat()]
    new_row = pd.DataFrame([{"date": date.isoformat(), "close": close}])
    updated = new_row if existing.empty else pd.concat([existing, new_row], ignore_index=True)
    updated = updated.sort_values("date")
    updated.to_csv(INDEX_FILE, index=False)


def load_index_history() -> pd.DataFrame:
    if not INDEX_FILE.exists():
        return pd.DataFrame(columns=["date", "close"])
    return pd.read_csv(INDEX_FILE)


def load_trading_value_history(window_days: int, upto_date: dt.date | None = None) -> pd.DataFrame:
    """Concat the most recent `window_days` known trading days of TWSE+TPEx data.

    `upto_date`, when given, only considers trading days on or before it.
    """
    days = known_trading_days(upto_date)[-window_days:]
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


def load_all_revenue_history(upto_date: dt.date | None = None) -> pd.DataFrame:
    """All cached monthly revenue rows, oldest first.

    `upto_date`, when given, excludes any month not yet publicly known as of
    that date (see dateutil_roc.revenue_known_date) — used by the backtest to
    avoid leaking future revenue into a historical screening date.
    """
    if not REVENUE_DIR.exists():
        return pd.DataFrame()
    frames = [pd.read_csv(f, dtype={"code": str}) for f in REVENUE_DIR.glob("*.csv")]
    if not frames:
        return pd.DataFrame()
    history = pd.concat(frames, ignore_index=True).sort_values(["code", "roc_year", "month"]).reset_index(drop=True)
    if upto_date is not None:
        known_mask = history.apply(
            lambda row: revenue_known_date(int(row["roc_year"]), int(row["month"])) <= upto_date, axis=1
        )
        history = history[known_mask].reset_index(drop=True)
    return history
