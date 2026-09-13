from __future__ import annotations

import datetime as dt

from morning.config import TWSE_DIR


def known_trading_days() -> list[dt.date]:
    """Trading days we already have TWSE data for, oldest first."""
    if not TWSE_DIR.exists():
        return []
    days = []
    for f in TWSE_DIR.glob("*.csv"):
        try:
            days.append(dt.datetime.strptime(f.stem, "%Y%m%d").date())
        except ValueError:
            continue
    return sorted(days)
