from __future__ import annotations

import argparse
import datetime as dt
import sys

from morning.cache.store import save_daily, save_revenue_month
from morning.config import REVENUE_HISTORY_START_ROC_YEAR
from morning.dateutil_roc import ad_year_to_roc, today_taipei
from morning.fetch.mops_revenue import fetch_revenue_month
from morning.fetch.tpex import fetch_tpex_daily
from morning.fetch.twse import fetch_twse_daily
from morning.report.render import render_report
from morning.screening.pipeline import run as run_pipeline


def fetch_today(date: dt.date) -> None:
    twse_df = fetch_twse_daily(date)
    if twse_df is None or twse_df.empty:
        print(f"[twse] no data for {date} (non-trading day?)")
    else:
        save_daily("twse", date, twse_df)
        print(f"[twse] saved {len(twse_df)} rows for {date}")

    try:
        tpex_df = fetch_tpex_daily()
    except Exception as exc:  # noqa: BLE001 - known-flaky external source, don't fail the whole run
        print(f"[tpex] fetch failed, skipping today's OTC data: {exc}", file=sys.stderr)
    else:
        if tpex_df is None or tpex_df.empty:
            print("[tpex] no data returned")
        else:
            save_daily("tpex", date, tpex_df)
            print(f"[tpex] saved {len(tpex_df)} rows")


def fetch_latest_revenue(date: dt.date) -> None:
    roc_year = ad_year_to_roc(date.year)
    for market in ("sii", "otc"):
        for y, m in ((roc_year, date.month), (roc_year, date.month - 1) if date.month > 1 else (roc_year - 1, 12)):
            df = fetch_revenue_month(market, y, m)
            if df is None or df.empty:
                print(f"[revenue] {market} {y}/{m} not published yet")
                continue
            save_revenue_month(market, y, m, df)
            print(f"[revenue] {market} {y}/{m} saved {len(df)} rows")


def backfill_revenue(since_roc_year: int) -> None:
    current = today_taipei()
    current_roc_year = ad_year_to_roc(current.year)
    for year in range(since_roc_year, current_roc_year + 1):
        for month in range(1, 13):
            if year == current_roc_year and month > current.month:
                break
            for market in ("sii", "otc"):
                df = fetch_revenue_month(market, year, month)
                if df is None or df.empty:
                    continue
                save_revenue_month(market, year, month, df)
                print(f"[backfill] {market} {year}/{month} saved {len(df)} rows")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill-revenue", action="store_true", help="Backfill full monthly revenue history once")
    parser.add_argument(
        "--since-roc-year", type=int, default=REVENUE_HISTORY_START_ROC_YEAR, help="Backfill starting ROC year"
    )
    args = parser.parse_args()

    if args.backfill_revenue:
        backfill_revenue(args.since_roc_year)
        return 0

    date = today_taipei()
    fetch_today(date)
    fetch_latest_revenue(date)

    results = run_pipeline()
    render_report(results, generated_at=dt.datetime.now())
    print("[report] rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
