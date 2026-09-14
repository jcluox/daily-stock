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
MARGIN_DIR = RAW_DIR / "margin"

BUILD_DIR = ROOT_DIR / "build"
REPORT_FILE = BUILD_DIR / "index.html"

REVENUE_HISTORY_START_ROC_YEAR = 99  # earlier years return no data; actual earliest availability found was ROC 102 (2013)

REQUEST_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 15

BACKTEST_YEARS = 2
BACKTEST_HORIZONS = [5, 20]
BACKTEST_RESULTS_FILE = ROOT_DIR / "backtest_results.csv"
BACKTEST_REPORT_FILE = ROOT_DIR / "backtest_report.html"
