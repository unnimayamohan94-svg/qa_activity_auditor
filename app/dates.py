from datetime import date, timedelta
from app.models import WeeklyPeriod

def previous_sunday(d: date) -> date:
    current_sunday = d - timedelta(days=(d.weekday() + 1) % 7)
    return current_sunday - timedelta(days=7)

def calculate_period(extraction_date: date) -> WeeklyPeriod:
    start = previous_sunday(extraction_date)
    return WeeklyPeriod(extraction_date=extraction_date, period_start=start, period_end=start + timedelta(days=4))

def date_in_period(value, period: WeeklyPeriod) -> bool:
    if value is None: return False
    d = value.date() if hasattr(value, "date") else value
    return period.period_start <= d <= period.period_end
