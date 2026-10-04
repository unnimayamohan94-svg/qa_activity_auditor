import re
from bs4 import BeautifulSoup
from datetime import date


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    return re.sub(
        r"\s+",
        " ",
        BeautifulSoup(html, "html.parser").get_text(" ", strip=True),
    ).strip()


def contains_extraction_date(text: str, d: date) -> bool:
    """Check that the description contains the exact extraction date."""
    text = text or ""
    day = d.day
    month = d.month
    year = d.year

    months_full = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    months_short = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    full_month = months_full[month - 1]
    short_month = months_short[month - 1]
    short_month_pattern = r"(?:Sep|Sept)" if month == 9 else re.escape(short_month)

    patterns = [
        rf"(?<!\d)0?{day}(?:st|nd|rd|th)?\s+{re.escape(full_month)}(?![A-Za-z])",
        rf"(?<!\d)0?{day}(?:st|nd|rd|th)?\s+{short_month_pattern}(?![A-Za-z])",
        rf"(?<![A-Za-z]){re.escape(full_month)}\s+0?{day}(?:st|nd|rd|th)?(?!\d)",
        rf"(?<![A-Za-z]){short_month_pattern}\s+0?{day}(?:st|nd|rd|th)?(?!\d)",
        rf"(?<!\d)0?{day}/0?{month}/{year}(?!\d)",
        rf"(?<!\d)0?{day}-0?{month}-{year}(?!\d)",
    ]

    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def contains_progress_status(text: str) -> bool:
    if not text:
        return False

    low = text.lower()

    # "No update" / "No new update" are explicitly valid statuses.
    words = [
        "no update",
        "no new update",
        "completed",
        "complete",
        "in progress",
        "ongoing",
        "started",
        "targeting",
        "approved",
        "testing",
        "execution",
        "preparation",
        "analysis",
        "blocked",
        "pending",
        "ready",
        "moved",
        "provided",
        "validated",
        "failed",
        "completion",
        "on hold",
        "hold",
    ]

    return any(word in low for word in words)
