import datetime as dt

ROC_OFFSET = 1911


def ad_year_to_roc(year: int) -> int:
    return year - ROC_OFFSET


def roc_year_to_ad(roc_year: int) -> int:
    return roc_year + ROC_OFFSET


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    total = (year * 12 + (month - 1)) + delta
    return total // 12, total % 12 + 1


def months_between(year_a: int, month_a: int, year_b: int, month_b: int) -> int:
    """Number of months from (year_a, month_a) to (year_b, month_b), always >= 0."""
    return abs((year_b * 12 + month_b) - (year_a * 12 + month_a))


REVENUE_PUBLISH_DAY = 12  # approximation: MOPS requires disclosure by the 10th of the following month


def revenue_known_date(roc_year: int, month: int) -> dt.date:
    """Approximate date by which a given month's revenue is publicly known."""
    ad_year, next_month = add_months(roc_year_to_ad(roc_year), month, 1)
    return dt.date(ad_year, next_month, REVENUE_PUBLISH_DAY)


def now_taipei() -> dt.datetime:
    return dt.datetime.utcnow() + dt.timedelta(hours=8)


def today_taipei() -> dt.date:
    return now_taipei().date()
