from __future__ import annotations

import datetime as dt

from morning.config import TWSE_DIR


def known_trading_days(upto_date: dt.date | None = None) -> list[dt.date]:
    """Trading days we already have TWSE data for, oldest first.

    `upto_date`, when given, excludes any later days — used by the backtest
    to reconstruct "what was known as of this historical date" without
    leaking future data.
    """
    if not TWSE_DIR.exists():
        return []
    days = []
    for f in TWSE_DIR.glob("*.csv"):
        try:
            days.append(dt.datetime.strptime(f.stem, "%Y%m%d").date())
        except ValueError:
            continue
    if upto_date is not None:
        days = [d for d in days if d <= upto_date]
    return sorted(days)
