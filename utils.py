from datetime import date, datetime, timedelta

def parse_positive_int(value, field="Quantity"):
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a whole number.")
    if n <= 0:
        raise ValueError(f"{field} must be greater than zero.")
    return n

def alert_dates():
    today = date.today()
    return today.isoformat(), (today + timedelta(days=15)).isoformat()

def valid_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValueError("Please enter a valid date (YYYY-MM-DD).")
