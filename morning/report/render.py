from __future__ import annotations

import datetime as dt
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from morning.config import BUILD_DIR, REPORT_FILE, WINDOWS

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _format_yi(value: float) -> str:
    """Format a NT-dollar amount as 億 (hundred millions), floored to 1 decimal place."""
    floored = (int(value) // 10_000_000) / 10
    return f"{floored:.1f}"


_CANDLE_HEIGHT = 40
_CANDLE_MARGIN = 3


def _candle_svg(candle: dict | None) -> dict | None:
    """Map OHLC prices to y-coordinates for a small inline SVG candlestick."""
    if candle is None:
        return None
    o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]

    def to_y(price: float) -> float:
        if h == l:
            return _CANDLE_HEIGHT / 2
        scale = (_CANDLE_HEIGHT - 2 * _CANDLE_MARGIN) / (h - l)
        return _CANDLE_MARGIN + (h - price) * scale

    body_top, body_bottom = to_y(max(o, c)), to_y(min(o, c))
    return {
        "wick_top": to_y(h),
        "wick_bottom": to_y(l),
        "body_top": body_top,
        "body_bottom": max(body_bottom, body_top + 1),  # ensure a visible sliver on doji days
        "is_red": candle["is_red"],
    }


def render_report(
    results: dict[int, list[dict]], generated_at: dt.datetime, earliest_revenue_roc_year: int | None
) -> None:
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    env.filters["yi"] = _format_yi
    env.filters["candle_svg"] = _candle_svg
    template = env.get_template("report.html.j2")
    html = template.render(
        windows=WINDOWS,
        results=results,
        generated_at=generated_at,
        earliest_revenue_roc_year=earliest_revenue_roc_year,
    )

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(html, encoding="utf-8")
