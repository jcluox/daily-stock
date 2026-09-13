from __future__ import annotations

import re
from io import StringIO
from typing import Literal

import pandas as pd

from morning.fetch.http import get

_URL_TEMPLATE = "https://mopsov.twse.com.tw/nas/t21/{market}/t21sc03_{roc_year}_{month}_0.html"

_COLUMN_RENAME = {
    "公司 代號": "code",
    "公司名稱": "name",
    "當月營收": "revenue_this_month",
    "上月營收": "revenue_last_month",
    "去年當月營收": "revenue_last_year_same_month",
    "上月比較 增減(%)": "mom_pct",
    "去年同月 增減(%)": "yoy_pct",
    "當月累計營收": "revenue_cum_this_year",
    "去年累計營收": "revenue_cum_last_year",
    "前期比較 增減(%)": "cum_pct",
    "備註": "note",
}

_CODE_PATTERN = re.compile(r"^\d+$")


def fetch_revenue_month(market: Literal["sii", "otc"], roc_year: int, month: int) -> pd.DataFrame | None:
    """Monthly revenue for all companies in one market for one ROC year/month.

    Returns a DataFrame with columns [roc_year, month, code, name,
    revenue_this_month, ...], or None if the month isn't published yet.
    """
    url = _URL_TEMPLATE.format(market=market, roc_year=roc_year, month=month)
    resp = get(url)
    if resp is None:
        return None
    html = resp.content.decode("big5", errors="replace")
    if "查無資料" in html:
        return None

    tables = pd.read_html(StringIO(html))
    frames = [t for t in tables if t.shape[1] == len(_COLUMN_RENAME)]
    if not frames:
        return None

    rows = []
    for t in frames:
        t = t.copy()
        t.columns = [col[1] if isinstance(col, tuple) else col for col in t.columns]
        t = t.rename(columns=_COLUMN_RENAME)
        rows.append(t)

    df = pd.concat(rows, ignore_index=True)
    df = df[df["code"].astype(str).str.match(_CODE_PATTERN)].copy()
    df["roc_year"] = roc_year
    df["month"] = month
    numeric_cols = [
        "revenue_this_month",
        "revenue_last_month",
        "revenue_last_year_same_month",
        "mom_pct",
        "yoy_pct",
        "revenue_cum_this_year",
        "revenue_cum_last_year",
        "cum_pct",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[["roc_year", "month", "code", "name", *numeric_cols]].reset_index(drop=True)
