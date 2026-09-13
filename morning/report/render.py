from __future__ import annotations

import datetime as dt
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from morning.config import BUILD_DIR, REPORT_FILE, WINDOWS

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_report(
    results: dict[int, list[dict]], generated_at: dt.datetime, earliest_revenue_roc_year: int | None
) -> None:
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    template = env.get_template("report.html.j2")
    html = template.render(
        windows=WINDOWS,
        results=results,
        generated_at=generated_at,
        earliest_revenue_roc_year=earliest_revenue_roc_year,
    )

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(html, encoding="utf-8")
