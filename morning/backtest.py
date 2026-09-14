from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from morning.cache.store import load_all_revenue_history, load_index_history, load_trading_value_history
from morning.cache.trading_calendar import known_trading_days
from morning.config import BACKTEST_HORIZONS, BACKTEST_REPORT_FILE, BACKTEST_RESULTS_FILE, BACKTEST_YEARS, WINDOWS
from morning.dateutil_roc import now_taipei, revenue_known_date, today_taipei
from morning.main import fill_missing_twse_days
from morning.screening.revenue import is_one_year_high, latest_published_revenue, record_high_label
from morning.screening.trading_value import compute_top_n

# The backtest re-evaluates the same screen (compute_top_n + revenue.py
# functions) at hundreds of historical dates, so unlike the daily report it
# pre-loads everything into memory once and slices in-memory, rather than
# re-reading CSVs per date/window like cache.store does for the single daily
# run — that would mean tens of thousands of disk reads here.


def _group_price_by_date(price_history: pd.DataFrame) -> dict[dt.date, pd.DataFrame]:
    return {date: sub for date, sub in price_history.groupby("date")}


def _group_revenue_by_code(revenue_history: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {code: sub for code, sub in revenue_history.groupby("code")}


def run_backtest(years: int, horizons: list[int]) -> pd.DataFrame:
    today = today_taipei()
    since_date = today - dt.timedelta(days=int(years * 365.25))
    print(f"[backtest] ensuring TWSE cache covers {since_date} .. {today} (first run may take a while — rate-limited)")
    fill_missing_twse_days(today, since_date=since_date, delay=3.0)

    trading_days = known_trading_days()
    max_window = max(WINDOWS)
    max_horizon = max(horizons)
    if len(trading_days) <= max_window + max_horizon:
        raise SystemExit("Not enough cached trading days for a meaningful backtest yet.")

    price_history = load_trading_value_history(window_days=len(trading_days))
    if "close_price" not in price_history.columns or price_history["close_price"].isna().all():
        raise SystemExit("No close_price data cached yet — re-run the daily fetch to populate it.")
    by_date = _group_price_by_date(price_history)

    revenue_history = load_all_revenue_history()
    revenue_history["known_date"] = revenue_history.apply(
        lambda row: revenue_known_date(int(row["roc_year"]), int(row["month"])), axis=1
    )
    by_code = _group_revenue_by_code(revenue_history)

    index_history = load_index_history()
    index_by_date = dict(zip(index_history["date"], index_history["close"]))

    close_lookup: dict[tuple[str, dt.date], float] = {
        (row.code, row.date): row.close_price for row in price_history.itertuples() if pd.notna(row.close_price)
    }

    records = []
    total = len(trading_days) - max_window - max_horizon
    for d_idx in range(max_window, len(trading_days) - max_horizon):
        d = trading_days[d_idx]

        for window in WINDOWS:
            window_dates = trading_days[d_idx - window + 1 : d_idx + 1]
            frames = [by_date[dd] for dd in window_dates if dd in by_date]
            if not frames:
                continue
            window_df = pd.concat(frames, ignore_index=True)
            candidates = compute_top_n(window, window_df)

            for cand in candidates.itertuples():
                code_hist = by_code.get(cand.code)
                if code_hist is None:
                    continue
                visible = code_hist[code_hist["known_date"] <= d]
                if visible.empty:
                    continue
                rev = latest_published_revenue(cand.code, visible)
                if rev is None or not is_one_year_high(cand.code, visible):
                    continue
                label, _pct = record_high_label(cand.code, visible)

                entry_close = close_lookup.get((cand.code, d))
                if entry_close is None:
                    continue

                for h in horizons:
                    exit_date = trading_days[d_idx + h]
                    exit_close = close_lookup.get((cand.code, exit_date))
                    if exit_close is None:
                        continue
                    stock_return = exit_close / entry_close - 1

                    entry_index = index_by_date.get(d.isoformat())
                    exit_index = index_by_date.get(exit_date.isoformat())
                    excess_return = None
                    if entry_index is not None and exit_index is not None:
                        excess_return = stock_return - (exit_index / entry_index - 1)

                    records.append(
                        {
                            "date": d.isoformat(),
                            "window": window,
                            "horizon": h,
                            "code": cand.code,
                            "name": cand.name,
                            "revenue_label": label,
                            "return": stock_return,
                            "excess_return": excess_return,
                        }
                    )

        done = d_idx - max_window + 1
        if done % 50 == 0 or done == total:
            print(f"[backtest] processed {done}/{total} screening days")

    return pd.DataFrame(records)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    return results.groupby(["window", "horizon"]).agg(
        n_picks=("return", "count"),
        win_rate=("return", lambda s: (s > 0).mean()),
        avg_return=("return", "mean"),
        avg_excess_return=("excess_return", "mean"),
        median_excess_return=("excess_return", "median"),
    )


def render_backtest_report(results: pd.DataFrame, summary: pd.DataFrame, years: float) -> None:
    template_dir = Path(__file__).parent / "report" / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("backtest_report.html.j2")
    rows = summary.reset_index().to_dict("records")
    html = template.render(rows=rows, generated_at=now_taipei(), years=years, n_picks_total=len(results))
    BACKTEST_REPORT_FILE.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=float, default=BACKTEST_YEARS, help="How many years of history to backtest")
    parser.add_argument(
        "--horizons", type=str, default=",".join(str(h) for h in BACKTEST_HORIZONS), help="Comma-separated trading-day forward-return horizons"
    )
    args = parser.parse_args()
    horizons = [int(h) for h in args.horizons.split(",")]

    results = run_backtest(args.years, horizons)
    if results.empty:
        print("[backtest] no picks were generated in this range.")
        return 0

    results.to_csv(BACKTEST_RESULTS_FILE, index=False)
    print(f"[backtest] wrote {len(results)} rows to {BACKTEST_RESULTS_FILE}")

    summary = summarize(results)
    pd.set_option("display.float_format", lambda v: f"{v:.4f}")
    print(summary)

    render_backtest_report(results, summary, args.years)
    print(f"[backtest] wrote report to {BACKTEST_REPORT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
