from __future__ import annotations

import datetime as dt

import pandas as pd

from morning.fetch.http import get

_URL = "https://www.twse.com.tw/exchangeReport/MI_INDEX"


def fetch_twse_daily(date: dt.date) -> pd.DataFrame | None:
    """All TWSE-listed stocks' trading data for one date.

    Returns a DataFrame with columns [code, name, trading_value], or None
    if the date has no data (non-trading day).
    """
    resp = get(_URL, params={"response": "json", "date": date.strftime("%Y%m%d"), "type": "ALLBUT0999"})
    if resp is None:
        return None
    payload = resp.json()
    if payload.get("stat") != "OK":
        return None

    target = None
    for table in payload.get("tables", []):
        fields = table.get("fields") or []
        if "證券代號" in fields and "成交金額" in fields:
            target = table
            break
    if target is None:
        return None

    fields = target["fields"]
    code_idx = fields.index("證券代號")
    name_idx = fields.index("證券名稱")
    value_idx = fields.index("成交金額")

    rows = []
    for row in target["data"]:
        try:
            trading_value = int(row[value_idx].replace(",", ""))
        except (ValueError, AttributeError):
            continue
        rows.append({"code": row[code_idx], "name": row[name_idx], "trading_value": trading_value})

    return pd.DataFrame(rows, columns=["code", "name", "trading_value"])
