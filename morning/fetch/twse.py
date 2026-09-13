from __future__ import annotations

import datetime as dt

import pandas as pd

from morning.config import REQUEST_DELAY_SECONDS
from morning.fetch.http import get

_URL = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
_TAIEX_NAME = "發行量加權股價指數"


def _find_table(tables: list[dict], required_fields: list[str]) -> dict | None:
    for table in tables:
        fields = table.get("fields") or []
        if all(f in fields for f in required_fields):
            return table
    return None


def _parse_taiex_close(tables: list[dict]) -> float | None:
    table = _find_table(tables, ["指數", "收盤指數"])
    if table is None:
        return None
    fields = table["fields"]
    name_idx = fields.index("指數")
    close_idx = fields.index("收盤指數")
    for row in table["data"]:
        if row[name_idx] == _TAIEX_NAME:
            try:
                return float(row[close_idx].replace(",", ""))
            except (ValueError, AttributeError):
                return None
    return None


def fetch_twse_daily(date: dt.date, delay: float = REQUEST_DELAY_SECONDS) -> tuple[pd.DataFrame | None, float | None]:
    """All TWSE-listed stocks' trading data for one date, plus the TAIEX close.

    Returns (stocks_df, taiex_close). stocks_df has columns
    [code, name, trading_value, close_price], or is None if the date has no
    data (non-trading day). taiex_close is the 發行量加權股價指數 close for
    that date, or None if unavailable. `delay` lets bulk backfills use a
    gentler pace than the daily job's 1-2 calls (see fetch/http.py — this
    endpoint rate-limits bursts with HTTP 428).
    """
    resp = get(_URL, params={"response": "json", "date": date.strftime("%Y%m%d"), "type": "ALLBUT0999"}, delay=delay)
    if resp is None:
        return None, None
    payload = resp.json()
    if payload.get("stat") != "OK":
        return None, None

    tables = payload.get("tables", [])
    taiex_close = _parse_taiex_close(tables)

    target = _find_table(tables, ["證券代號", "成交金額", "收盤價"])
    if target is None:
        return None, taiex_close

    fields = target["fields"]
    code_idx = fields.index("證券代號")
    name_idx = fields.index("證券名稱")
    value_idx = fields.index("成交金額")
    close_idx = fields.index("收盤價")

    rows = []
    for row in target["data"]:
        try:
            trading_value = int(row[value_idx].replace(",", ""))
        except (ValueError, AttributeError):
            continue
        try:
            close_price = float(row[close_idx].replace(",", ""))
        except (ValueError, AttributeError):
            close_price = None
        rows.append(
            {"code": row[code_idx], "name": row[name_idx], "trading_value": trading_value, "close_price": close_price}
        )

    return pd.DataFrame(rows, columns=["code", "name", "trading_value", "close_price"]), taiex_close
