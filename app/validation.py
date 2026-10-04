from app.models import QAActivity, WeeklyPeriod, ValidationResult
from app.description import html_to_text, contains_extraction_date, contains_progress_status
from app.dates import date_in_period
import re


def R(a, rule, field, status, severity, actual=None, expected=None, message="", source="RULE"):
    return ValidationResult(
        work_item_id=a.work_item_id,
        rule_id=rule,
        field_name=field,
        status=status,
        severity=severity,
        actual_value=actual,
        expected_value=expected,
        message=message,
        source=source,
    )


def nonnegative(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0


def percentage(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 100


def add_required(out, a, rule, field, value):
    ok = value is not None and value != ""
    out.append(R(
        a, rule, field, "PASS" if ok else "FAIL", "HIGH", value,
        "Populated",
        f"{field} is populated." if ok else f"{field} is missing."
    ))


def validate_common(a: QAActivity, p: WeeklyPeriod, ongoing: bool):
    out = []

    add_required(out, a, "COM-001", "Assignee", a.assignee)
    add_required(out, a, "COM-002", "Channel Name", a.channel_name)

    text = html_to_text(a.detailed_description)

    ok = contains_extraction_date(text, p.extraction_date)
    out.append(R(
        a, "COM-003", "Detailed Description", "PASS" if ok else "FAIL", "HIGH",
        text, p.extraction_date.isoformat(),
        "Extraction Date is present." if ok
        else "Detailed Description does not contain the Extraction Date."
    ))

    ok = contains_progress_status(text)
    out.append(R(
        a, "COM-004", "Detailed Description", "PASS" if ok else "FAIL", "MEDIUM",
        text, "Status/progress present",
        "Detailed Description contains status/progress information." if ok
        else "Detailed Description does not contain meaningful status/progress information."
    ))

    add_required(out, a, "COM-005A", "Target Start Date", a.target_start_date)
    add_required(out, a, "COM-005B", "Target End Date", a.target_end_date)
    if a.target_start_date and a.target_end_date:
        ok = a.target_start_date <= a.target_end_date
        out.append(R(
            a, "COM-005", "Target Start/End", "PASS" if ok else "FAIL", "HIGH",
            f"{a.target_start_date} / {a.target_end_date}", "Start <= End",
            "Target date relationship is valid." if ok
            else "Target Start Date cannot be after Target End Date."
        ))

    add_required(out, a, "COM-006A", "Actual Start Date", a.actual_start_date)

    # Actual End Date is optional while the task is In QA or In UAT.
    # It is required for other states, such as Closed.
    current_state = (a.state or "").strip().lower()

    if current_state in ("in qa", "in uat"):
        out.append(R(
            a, "COM-006B", "Actual End Date", "PASS", "HIGH",
            a.actual_end_date,
            "Optional when State is In QA or In UAT",
            "Actual End Date is optional while the task is In QA or In UAT."
        ))
    else:
        add_required(out, a, "COM-006B", "Actual End Date", a.actual_end_date)

    if a.actual_start_date and a.actual_end_date:
        ok = a.actual_start_date <= a.actual_end_date
        out.append(R(
            a, "COM-006", "Actual Start/End", "PASS" if ok else "FAIL", "HIGH",
            f"{a.actual_start_date} / {a.actual_end_date}", "Start <= End",
            "Actual date relationship is valid." if ok
            else "Actual Start Date cannot be after Actual End Date."
        ))

    ok = percentage(a.completion_percentage)
    out.append(R(
        a, "COM-007", "Completion Percentage", "PASS" if ok else "FAIL", "HIGH",
        a.completion_percentage, "Numeric 0–100",
        "Completion Percentage is valid." if ok
        else "Completion Percentage must be numeric and between 0 and 100."
    ))

    if ongoing:
        ok = "ongoingtask" in a.tag_set
        out.append(R(
            a, "COM-009", "Tags", "PASS" if ok else "FAIL", "HIGH", a.tags,
            "OngoingTask required",
            "OngoingTask tag is present." if ok
            else "OngoingTask tag is missing for an ongoing task."
        ))

    # If OngoingTask is present on a task that ended before last week,
    # eligibility handles the exclusion; this rule is also useful for
    # sections where eligibility is not used.
    if "ongoingtask" in a.tag_set and a.actual_end_date:
        if a.actual_end_date.date() < p.period_start:
            out.append(R(
                a, "COM-011", "Tags / Actual End", "FAIL", "HIGH",
                a.actual_end_date.isoformat(),
                f"Actual End >= {p.period_start}",
                "OngoingTask is present but Actual End is before the weekly period."
            ))

    return out


def validate_activity(a: QAActivity):
    out = []
    cp = a.completion_percentage
    prefixes = {
        "Requirement Analysis": "RA",
        "Testcase Preparation": "TCP",
        "Testcase Execution": "TCE",
        "UAT Support": "UAT",
    }

    if a.activity_type in prefixes:
        actual_state = (a.state or "").strip().lower()
        if a.activity_type == "UAT Support":
            uat_cp = a.uat_completion_percentage
            expected = "Closed" if uat_cp == 100 else "In UAT"
        else:
            expected = "Closed" if cp == 100 else "In QA"

        # Incomplete QA activities use the "In QA" state.
        ok = actual_state == expected.lower()
        out.append(R(
            a, prefixes[a.activity_type] + "-001", "State",
            "PASS" if ok else "FAIL", "HIGH", a.state, expected,
            "State matches the expected workflow state." if ok
            else f"State should be '{expected}' for Completion Percentage {cp}."
        ))

    if a.activity_type == "Requirement Analysis":
        ok = a.total_testcase == 0
        out.append(R(
            a, "RA-006", "Total Testcase", "PASS" if ok else "FAIL", "HIGH",
            a.total_testcase, "0",
            "Requirement Analysis Total Testcase is 0." if ok
            else "Requirement Analysis Total Testcase must be 0."
        ))

    elif a.activity_type == "Testcase Preparation":
        ok = nonnegative(a.total_testcase)
        out.append(R(
            a, "TCP-006", "Total Testcase", "PASS" if ok else "FAIL", "HIGH",
            a.total_testcase, "Numeric >= 0",
            "Total Testcase is valid." if ok
            else "Total Testcase must be a numeric value from 0 upward."
        ))

    elif a.activity_type == "Testcase Execution":
        ok = a.total_testcase is None or nonnegative(a.total_testcase)

        out.append(R(
            a, "TCE-006", "Total Testcase",
            "PASS" if ok else "FAIL",
            "HIGH",
            a.total_testcase,
            "Numeric >= 0 or blank",
            "Total Testcase is valid or blank." if ok
            else "Total Testcase must be numeric and >= 0 when provided."
        ))

        ok = nonnegative(a.qa_defect_count)
        out.append(R(
            a, "TCE-007", "QA Defect Count", "PASS" if ok else "FAIL", "HIGH",
            a.qa_defect_count, "Numeric >= 0",
            "QA Defect Count is valid." if ok
            else "QA Defect Count must be a numeric value from 0 upward."
        ))

    elif a.activity_type == "UAT Support":
        ok = percentage(a.uat_completion_percentage)
        out.append(R(
            a, "UAT-006", "UAT Completion Percentage",
            "PASS" if ok else "FAIL", "HIGH",
            a.uat_completion_percentage, "Numeric 0–100",
            "UAT Completion Percentage is valid." if ok
            else "UAT Completion Percentage must be numeric and between 0 and 100."
        ))

        ok = nonnegative(a.overall_uat_bugs)
        out.append(R(
            a, "UAT-007", "Overall UAT Bugs",
            "PASS" if ok else "FAIL", "HIGH",
            a.overall_uat_bugs, "Numeric >= 0",
            "Overall UAT Bugs is valid." if ok
            else "Overall UAT Bugs must be a numeric value from 0 upward."
        ))

        ok = "ongoingtask" in a.tag_set
        out.append(R(
            a, "UAT-008", "Tags", "PASS" if ok else "FAIL", "HIGH",
            a.tags, "OngoingTask required",
            "OngoingTask tag is present." if ok
            else "OngoingTask tag is mandatory for UAT Support."
        ))

        if a.uat_start_date is None:
            add_required(out, a, "UAT-011A", "UAT Start Date", None)

        # UAT End Date is optional while the task is In UAT.
        if a.uat_end_date is None:
            current_state = (a.state or "").strip().lower()
            if current_state == "in uat":
                out.append(R(
                    a, "UAT-011B", "UAT End Date", "PASS", "HIGH",
                    None, "Optional when State is In UAT",
                    "UAT End Date is optional while the task is In UAT."
                ))
            else:
                add_required(out, a, "UAT-011B", "UAT End Date", None)

        if a.uat_start_date and a.uat_end_date:
            ok = a.uat_start_date <= a.uat_end_date
            out.append(R(
                a, "UAT-011", "UAT Start/End",
                "PASS" if ok else "FAIL", "HIGH",
                f"{a.uat_start_date} / {a.uat_end_date}", "Start <= End",
                "UAT date relationship is valid." if ok
                else "UAT Start Date cannot be after UAT End Date."
            ))

    return out


# ---------------------------------------------------------------------
# Section-specific validation
# ---------------------------------------------------------------------

def validate_ongoing_qa(a: QAActivity, p: WeeklyPeriod):
    out = []

    add_required(out, a, "OQA-001", "State", a.state)
    out.append(R(a, "OQA-001S", "State",
                 "PASS" if (a.state or "").strip().lower() == "in qa" else "FAIL",
                 "HIGH", a.state, "In QA",
                 "State is In QA." if (a.state or "").strip().lower() == "in qa"
                 else "State must be 'In QA'."))

    add_required(out, a, "OQA-002", "Channel Name", a.channel_name)
    text = html_to_text(a.detailed_description)

    for rule, field, value in [
        ("OQA-003", "Detailed Description", text),
    ]:
        ok = bool(value)
        out.append(R(a, rule, field, "PASS" if ok else "FAIL", "HIGH",
                     value, "Not blank",
                     "Detailed Description is available." if ok
                     else "Detailed Description is blank."))

    ok = contains_extraction_date(text, p.extraction_date)
    out.append(R(a, "OQA-004", "Detailed Description", "PASS" if ok else "FAIL",
                 "HIGH", text, p.extraction_date.isoformat(),
                 "Extraction Date is present." if ok
                 else "Detailed Description does not contain the Extraction Date."))

    ok = contains_progress_status(text)
    out.append(R(a, "OQA-005", "Detailed Description", "PASS" if ok else "FAIL",
                 "MEDIUM", text, "Status/progress present",
                 "Status/progress is present." if ok
                 else "Detailed Description does not contain meaningful status/progress."))

    for rule, field, value in [
        ("OQA-006A", "Target Start Date", a.target_start_date),
        ("OQA-006B", "Target End Date", a.target_end_date),
        ("OQA-007", "Actual Start Date", a.actual_start_date),
    ]:
        add_required(out, a, rule, field, value)

    # Target Start OR Target End must fall within last week.
    # Both dates do NOT need to be within the period.

    if a.target_start_date and a.target_end_date:
        start_in_week = date_in_period(a.target_start_date, p)
        end_in_week = date_in_period(a.target_end_date, p)

        has_ongoing_tag = "ongoingtask" in a.tag_set

        if has_ongoing_tag:
            ok = True
            expected = "OngoingTask allows target dates outside last week"
            message = "OngoingTask is present; target dates may belong to an older or future period."
        else:
            ok = start_in_week or end_in_week
            expected = f"Target Start OR Target End within {p.period_start} to {p.period_end}"
            message = (
                "At least one Target Date is within last week."
                if ok
                else "At least one of Target Start Date or Target End Date must fall within last week."
            )

        out.append(R(
            a,
            "OQA-008",
            "Target Start/End",
            "PASS" if ok else "FAIL",
            "HIGH",
            f"{a.target_start_date} / {a.target_end_date}",
            expected,
            message
        ))

    if a.target_start_date and a.target_end_date:
        ok = a.target_start_date <= a.target_end_date
        out.append(R(a, "OQA-010", "Target Start/End", "PASS" if ok else "FAIL",
                     "HIGH", f"{a.target_start_date} / {a.target_end_date}",
                     "Start <= End",
                     "Target date relationship is valid." if ok
                     else "Target Start cannot be after Target End."))

    if a.actual_start_date:
        in_week = date_in_period(a.actual_start_date, p)
        has_tag = "ongoingtask" in a.tag_set
        ok = in_week or has_tag
        out.append(R(
            a, "OQA-011", "Actual Start Date / Tags",
            "PASS" if ok else "FAIL", "HIGH",
            f"{a.actual_start_date} / {a.tags}",
            "Actual Start in last week OR OngoingTask",
            "Actual Start is within last week or OngoingTask is present." if ok
            else "Actual Start is outside last week and OngoingTask is missing."
        ))

    ok = percentage(a.completion_percentage) and a.completion_percentage < 100
    out.append(R(a, "OQA-012", "Completion Percentage", "PASS" if ok else "FAIL",
                 "HIGH", a.completion_percentage, "< 100",
                 "Completion Percentage is below 100." if ok
                 else "Completion Percentage must be present and below 100."))

    # QA defects: TCE must have numeric >=0; others must be 0 or blank.
    if a.activity_type == "Testcase Execution":
        ok = nonnegative(a.qa_defect_count)
        expected = "Numeric >= 0"
    else:
        ok = a.qa_defect_count is None or a.qa_defect_count == 0
        expected = "0 or blank"
    out.append(R(a, "OQA-013", "QA Defect Count", "PASS" if ok else "FAIL",
                 "HIGH", a.qa_defect_count, expected,
                 "QA Defect Count is valid." if ok
                 else "QA Defect Count is invalid for this activity type."))

    if a.activity_type == "Testcase Preparation":
        ok = nonnegative(a.total_testcase)
        expected = "Numeric >= 0"
    elif a.activity_type == "Testcase Execution":
        ok = a.total_testcase is None or nonnegative(a.total_testcase)
        expected = "Numeric >= 0 or blank"
    else:
        ok = a.total_testcase is None or a.total_testcase == 0
        expected = "0 or blank"
    out.append(R(a, "OQA-014", "Total Testcase", "PASS" if ok else "FAIL",
                 "HIGH", a.total_testcase, expected,
                 "Total Testcase is valid." if ok
                 else "Total Testcase is invalid for this activity type."))

    # If the description explicitly states a completion percentage, compare it.
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if m and a.completion_percentage is not None:
        described = float(m.group(1))
        ok = described == a.completion_percentage
        out.append(R(a, "OQA-015", "Completion Percentage",
                     "PASS" if ok else "FAIL", "MEDIUM",
                     a.completion_percentage, described,
                     "Description completion matches the field." if ok
                     else "Completion Percentage in description does not match the field."))

    return out


def validate_overall_uat(a: QAActivity, p: WeeklyPeriod):
    out = []

    ok = bool(re.search(r"(?<![A-Za-z0-9])UAT(?![A-Za-z0-9])", a.title or "", re.I))
    out.append(R(a, "OUAT-001", "Title", "PASS" if ok else "FAIL", "HIGH",
                 a.title, "Title contains UAT",
                 "Title contains UAT." if ok else "Task title must contain UAT."))

    expected_state = "Closed" if a.uat_completion_percentage == 100 else "In UAT"
    actual_state = (a.state or "").strip().lower()
    ok = actual_state == expected_state.lower()
    out.append(R(
        a, "OUAT-002", "State",
        "PASS" if ok else "FAIL",
        "HIGH",
        a.state,
        expected_state,
        "State matches the expected UAT workflow state." if ok
        else f"State should be '{expected_state}' for UAT Completion Percentage {a.uat_completion_percentage}."
    ))

    add_required(out, a, "OUAT-003", "Channel Name", a.channel_name)
    text = html_to_text(a.detailed_description)
    add_required(out, a, "OUAT-004", "Detailed Description", text)

    ok = contains_extraction_date(text, p.extraction_date)
    out.append(R(a, "OUAT-005", "Detailed Description", "PASS" if ok else "FAIL",
                 "HIGH", text, p.extraction_date.isoformat(),
                 "Extraction Date is present." if ok
                 else "Detailed Description does not contain the Extraction Date."))

    ok = contains_progress_status(text)
    out.append(R(a, "OUAT-006", "Detailed Description", "PASS" if ok else "FAIL",
                 "MEDIUM", text, "Status/progress present",
                 "Status/progress is present." if ok
                 else "Detailed Description does not contain meaningful status/progress."))

    add_required(out, a, "OUAT-007", "UAT Start Date", a.uat_start_date)

    current_state = (a.state or "").strip().lower()

    if current_state == "in uat":
        out.append(R(
            a, "OUAT-008", "UAT End Date", "PASS", "HIGH",
            a.uat_end_date,
            "Optional when State is In UAT",
            "UAT End Date is optional while the task is In UAT."
        ))
    else:
        add_required(out, a, "OUAT-008", "UAT End Date", a.uat_end_date)

    if a.uat_end_date:
        ok = a.uat_end_date.date() >= p.extraction_date
        out.append(R(
            a, "OUAT-009", "UAT End Date",
            "PASS" if ok else "FAIL",
            "HIGH",
            a.uat_end_date.isoformat(),
            f">= {p.extraction_date}",
            "UAT End Date is on/after Extraction Date." if ok
            else "UAT End Date must not be before Extraction Date."
        ))

    ok = percentage(a.uat_completion_percentage) and a.uat_completion_percentage < 100
    out.append(R(a, "OUAT-010", "UAT Completion Percentage",
                 "PASS" if ok else "FAIL", "HIGH",
                 a.uat_completion_percentage, "< 100",
                 "UAT Completion Percentage is below 100." if ok
                 else "UAT Completion Percentage must be present and below 100."))

    ok = nonnegative(a.overall_uat_bugs)
    out.append(R(a, "OUAT-011", "Overall UAT Bugs",
                 "PASS" if ok else "FAIL", "HIGH",
                 a.overall_uat_bugs, "Numeric >= 0",
                 "Overall UAT Bugs is valid." if ok
                 else "Overall UAT Bugs must be present and numeric >= 0."))

    return out


def validate_qa_backlog(a: QAActivity, p: WeeklyPeriod):
    out = []

    ok = (a.state or "").strip().lower() == "new"
    out.append(R(a, "QB-001", "State", "PASS" if ok else "FAIL", "HIGH",
                 a.state, "New",
                 "State is New." if ok else "State must be 'New'."))

    title = a.title or ""

    approved_keywords = [
        "KE",
        "KIB",
        "Mfloos",
        "MF",
        "KJ",
        "Kuraimi Jawal",
        "DB Optimization",
    ]

    ok = any(
        re.search(
            rf"(?<![A-Za-z0-9]){re.escape(keyword)}(?![A-Za-z0-9])",
            title,
            re.I,
        )
        for keyword in approved_keywords
    )
    out.append(R(a, "QB-002", "Title", "PASS" if ok else "FAIL", "MEDIUM",
                 a.title, "Approved QA keyword",
                 "Title contains an approved keyword." if ok
                 else "Title does not contain an approved QA keyword."))

    add_required(out, a, "QB-003", "Channel Name", a.channel_name)
    text = html_to_text(a.detailed_description)
    add_required(out, a, "QB-004", "Detailed Description", text)

    ok = contains_extraction_date(text, p.extraction_date)
    out.append(R(a, "QB-005", "Detailed Description", "PASS" if ok else "FAIL",
                 "HIGH", text, p.extraction_date.isoformat(),
                 "Extraction Date is present." if ok
                 else "Detailed Description does not contain the Extraction Date."))

    ok = contains_progress_status(text)
    out.append(R(a, "QB-006", "Detailed Description", "PASS" if ok else "FAIL",
                 "MEDIUM", text, "Status/progress present",
                 "Status/progress is present." if ok
                 else "Detailed Description does not contain meaningful status/progress."))

    return out


def validate_adhoc(a: QAActivity, p: WeeklyPeriod):
    out = []
    text = html_to_text(a.detailed_description)

    if (a.state or "").strip().lower() == "in qa":
        ok = contains_extraction_date(text, p.extraction_date)
        out.append(R(a, "ADHOC-001", "Detailed Description",
                     "PASS" if ok else "FAIL", "HIGH", text,
                     p.extraction_date.isoformat(),
                     "Extraction Date is present." if ok
                     else "Detailed Description does not contain the Extraction Date."))

        ok = contains_progress_status(text)
        out.append(R(a, "ADHOC-002", "Detailed Description",
                     "PASS" if ok else "FAIL", "MEDIUM", text,
                     "Status/progress present",
                     "Status/progress is present." if ok
                     else "Detailed Description does not contain meaningful status/progress."))
    else:
        ok = bool(text.strip())
        out.append(R(a, "ADHOC-001", "Detailed Description",
                     "PASS" if ok else "FAIL", "HIGH", text,
                     "Not blank",
                     "Detailed Description is available." if ok
                     else "Detailed Description is blank."))

    ok = (a.integration_build or "").strip().lower() == "adhoc"
    out.append(R(a, "ADHOC-003", "Integrated in Build",
                 "PASS" if ok else "FAIL", "HIGH",
                 a.integration_build, "adhoc",
                 "Integrated in Build is adhoc." if ok
                 else "Integrated in Build must be 'adhoc'."))
    return out


def validate_overall_active(a: QAActivity, p: WeeklyPeriod):
    out = []
    text = html_to_text(a.detailed_description)

    ok = contains_extraction_date(text, p.extraction_date)
    out.append(R(a, "OA-001", "Detailed Description",
                 "PASS" if ok else "FAIL", "HIGH", text,
                 p.extraction_date.isoformat(),
                 "Extraction Date is present." if ok
                 else "Detailed Description does not contain the Extraction Date."))

    ok = contains_progress_status(text)
    out.append(R(a, "OA-002", "Detailed Description",
                 "PASS" if ok else "FAIL", "MEDIUM", text,
                 "Status/progress present",
                 "Status/progress is present." if ok
                 else "Detailed Description does not contain meaningful status/progress."))

    return out
