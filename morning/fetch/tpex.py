from __future__ import annotations

import pandas as pd

from morning.fetch.http import get

_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"


def fetch_tpex_daily() -> pd.DataFrame | None:
    """Today's TPEx (OTC) trading data for all stocks.

    NOTE: TPEx's historical date query parameters do not work (verified
    2026-09) — this endpoint only ever returns the latest trading day, so
    it must only be used for the daily incremental fetch, never backfill.

    Returns a DataFrame with columns [code, name, trading_value], or None
    if the response is empty/unavailable.
    """
    resp = get(_URL, params={"l": "zh-tw"})
    if resp is None:
        return None
    records = resp.json()
    if not records:
        return None

    rows = []
    for rec in records:
        try:
            trading_value = int(rec["TransactionAmount"])
        except (ValueError, KeyError, TypeError):
            continue
        rows.append(
            {
                "code": rec["SecuritiesCompanyCode"],
                "name": rec["CompanyName"],
                "trading_value": trading_value,
            }
        )

    return pd.DataFrame(rows, columns=["code", "name", "trading_value"])
