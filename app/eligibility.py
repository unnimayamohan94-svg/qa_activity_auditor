from app.models import QAActivity, WeeklyPeriod
from app.dates import date_in_period


def evaluate_eligibility(a: QAActivity, p: WeeklyPeriod):
    """Eligibility for QA Activities – Last Week only."""
    if date_in_period(a.actual_start_date, p):
        return True, False, "Actual Start Date falls within weekly period."

    if date_in_period(a.actual_end_date, p):
        return True, False, "Actual End Date falls within weekly period."

    if a.actual_end_date is None:
        return True, True, "Actual End Date is empty; task is treated as ongoing."

    if a.actual_end_date.date() > p.period_end:
        return True, True, "Actual End Date is after weekly period; task is treated as ongoing."

    if a.actual_end_date.date() < p.period_start:
        return False, False, "Task ended before the weekly period."

    return False, False, "Task does not meet weekly period eligibility criteria."
