from __future__ import annotations

from io import BytesIO
from typing import Literal

import pandas as pd

from morning.fetch.http import get

_URLS = {
    "sii": "https://mopsfin.twse.com.tw/opendata/t187ap17_L.csv",
    "otc": "https://mopsfin.twse.com.tw/opendata/t187ap17_O.csv",
}

_RENAME = {
    "公司代號": "code",
    "公司名稱": "name",
    "年度": "roc_year",
    "季別": "quarter",
    "毛利率(%)(營業毛利)/(營業收入)": "gross_margin_pct",
}


def fetch_gross_margin(market: Literal["sii", "otc"]) -> pd.DataFrame | None:
    """Latest disclosed quarter's gross margin for all companies in one market.

    This TWSE open-data endpoint always reflects whatever the most recently
    disclosed quarter is (it isn't queryable by date), so there's no history
    to track — just the current snapshot. Returns columns
    [code, name, roc_year, quarter, gross_margin_pct], or None if unavailable.
    """
    resp = get(_URLS[market])
    if resp is None:
        return None
    df = pd.read_csv(BytesIO(resp.content), encoding="utf-8-sig", dtype={"公司代號": str})
    df = df.rename(columns=_RENAME)
    df["gross_margin_pct"] = pd.to_numeric(df["gross_margin_pct"], errors="coerce")
    return df[["code", "name", "roc_year", "quarter", "gross_margin_pct"]]
