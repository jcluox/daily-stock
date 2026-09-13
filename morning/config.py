from pathlib import Path

WINDOWS = [1, 2, 5, 10, 15, 30]
TOP_N = 30
ONE_YEAR_MONTHS = 11  # compare against the prior 11 months to judge a 1-year high

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
TWSE_DIR = RAW_DIR / "twse"
TPEX_DIR = RAW_DIR / "tpex"
REVENUE_DIR = RAW_DIR / "revenue"

BUILD_DIR = ROOT_DIR / "build"
REPORT_FILE = BUILD_DIR / "index.html"

REVENUE_HISTORY_START_ROC_YEAR = 99  # MOPS bulk report 404s before this (2010)

REQUEST_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 15
