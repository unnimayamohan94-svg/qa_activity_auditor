from datetime import date
from app.models import QAActivity, ActivityAudit, ValidationResult, WeeklyPeriod
from app.classification import classify_activity
from app.dates import calculate_period, date_in_period
from app.eligibility import evaluate_eligibility
from app.validation import (
    validate_common,
    validate_activity,
    validate_ongoing_qa,
    validate_overall_uat,
    validate_qa_backlog,
    validate_adhoc,
    validate_overall_active,
    R,
)

QUERY_SECTIONS = {
    "4c08bd11-c5c2-4f3f-bd9b-c4a1a2d87878": "QA Activities – Last Week",
    "745a86ba-5357-469c-8445-32cbca78e6c7": "Ongoing tasks in QA bucket",
    "11a5f228-fad2-46f8-ba11-2a9eade62b31": "Overall UAT Items",
    "53d95ee3-fb4a-4761-958b-e384fc206db7": "QA Backlog",
    "5acb4e49-2218-414a-8be6-0e14e0b9cbc1": "Overall Adhoc task",
    "0030e8cb-0251-49e6-8ea3-06377e9e197c": "Overall active",
}

SECTION_QUERY_IDS = {v: k for k, v in QUERY_SECTIONS.items()}


def audit_activity(a: QAActivity, extraction_date: date):
    """Backward-compatible audit for QA Activities – Last Week."""
    return audit_section_activity(
        a, "QA Activities – Last Week", extraction_date
    )


def audit_section_activity(
    a: QAActivity,
    section: str,
    extraction_date: date,
):
    p = calculate_period(extraction_date)
    a.section = section

    # Activity type is useful for activity-specific rules and display.
    a.activity_type = classify_activity(a.title)

    # ---------------------------------------------------------
    # QA Activities – Last Week
    # ---------------------------------------------------------
    if section == "QA Activities – Last Week":
        if not a.activity_type:
            return ActivityAudit(
                work_item_id=a.work_item_id,
                title=a.title,
                activity_type=None,
                section=section,
                assignee=a.assignee,
                state=a.state,
                completion_percentage=a.completion_percentage,
                eligible=True,
                results=[
                    R(
                        a,
                        "CLASS-001",
                        "Title",
                        "FAIL",
                        "HIGH",
                        a.title,
                        "One of the four QA activity types",
                        "Activity type could not be determined uniquely from the title.",
                    )
                ],
            )

        eligible, ongoing, reason = evaluate_eligibility(a, p)

        if not eligible:
            return ActivityAudit(
                work_item_id=a.work_item_id,
                title=a.title,
                activity_type=a.activity_type,
                section=section,
                assignee=a.assignee,
                state=a.state,
                completion_percentage=a.completion_percentage,
                eligible=False,
                ongoing=False,
                results=[
                    ValidationResult(
                        work_item_id=a.work_item_id,
                        rule_id="ELIG-001",
                        field_name="Actual Start/End Date",
                        status="EXCLUDE",
                        severity="INFO",
                        actual_value=f"{a.actual_start_date} / {a.actual_end_date}",
                        expected_value=f"{p.period_start} to {p.period_end}",
                        message=reason,
                    )
                ],
            )

        results = validate_common(a, p, ongoing) + validate_activity(a)

        return ActivityAudit(
            work_item_id=a.work_item_id,
            title=a.title,
            activity_type=a.activity_type,
            section=section,
            assignee=a.assignee,
            state=a.state,
            completion_percentage=a.completion_percentage,
            eligible=True,
            ongoing=ongoing,
            results=results,
        )

    # ---------------------------------------------------------
    # Other five sections
    # ---------------------------------------------------------
    validators = {
        "Ongoing tasks in QA bucket": validate_ongoing_qa,
        "Overall UAT Items": validate_overall_uat,
        "QA Backlog": validate_qa_backlog,
        "Overall Adhoc task": validate_adhoc,
        "Overall active": validate_overall_active,
    }

    validator = validators.get(section)
    if validator is None:
        return ActivityAudit(
            work_item_id=a.work_item_id,
            title=a.title,
            activity_type=a.activity_type,
            section=section,
            assignee=a.assignee,
            state=a.state,
            completion_percentage=a.completion_percentage,
            eligible=False,
            results=[
                R(
                    a,
                    "SECTION-001",
                    "Section",
                    "FAIL",
                    "HIGH",
                    section,
                    "Configured section",
                    "Unknown audit section.",
                )
            ],
        )

    results = validator(a, p)

    return ActivityAudit(
        work_item_id=a.work_item_id,
        title=a.title,
        activity_type=a.activity_type,
        section=section,
        assignee=a.assignee,
        state=a.state,
        completion_percentage=a.completion_percentage,
        eligible=True,
        ongoing="ongoingtask" in a.tag_set,
        results=results,
    )
