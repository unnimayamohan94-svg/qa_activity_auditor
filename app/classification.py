import re


ACTIVITY_TYPES = [
    "Requirement Analysis",
    "Testcase Preparation",
    "Testcase Execution",
    "UAT Support",
]


def classify_activity(title: str):
    if not title:
        return None

    # Normalize underscores and hyphens to spaces
    normalized_title = re.sub(r"[_\-]+", " ", title)
    normalized_title = re.sub(r"\s+", " ", normalized_title).strip()

    # =========================================================
    # UAT SUPPORT
    # =========================================================
    # Examples:
    # UAT_KIB_Blacklist
    # UAT_KIB_Delivery 3
    # UAT Testing
    # UAT Support
    #
    # Any title beginning with UAT should be treated as
    # UAT Support.
    # =========================================================

    if re.match(r"^UAT(?:\s|$)", normalized_title, re.IGNORECASE):
        return "UAT Support"


    # =========================================================
    # REQUIREMENT ANALYSIS
    # =========================================================

    if re.search(
        r"\bRequirement\s+Analysis\b",
        normalized_title,
        re.IGNORECASE
    ):
        return "Requirement Analysis"


    # =========================================================
    # TESTCASE PREPARATION
    # =========================================================
    # Examples:
    # Test Case Preparation
    # Testcase Preparation
    # Test Case Creation
    # Test_Case_Creation
    # =========================================================

    if re.search(
        r"\bTest\s*Case\s+(Preparation|Creation)\b",
        normalized_title,
        re.IGNORECASE
    ):
        return "Testcase Preparation"


    # =========================================================
    # TESTCASE EXECUTION
    # =========================================================
    # Examples:
    # Test Execution
    # Test_Execution
    # Test Case Execution
    # Testcase Execution
    # Something_Execution
    # =========================================================

    if re.search(
        r"\bTest\s*Case\s+Execution\b",
        normalized_title,
        re.IGNORECASE
    ):
        return "Testcase Execution"


    if re.search(
        r"\bTest\s+Execution\b",
        normalized_title,
        re.IGNORECASE
    ):
        return "Testcase Execution"


    if re.search(
        r"(?:^|\s)Execution(?:\s|$)",
        normalized_title,
        re.IGNORECASE
    ):
        return "Testcase Execution"


    if re.search(
        r"(?:^|\s)Test\s+Executions?(?:\s|$)",
        normalized_title,
        re.IGNORECASE
    ):
        return "Testcase Execution"


    # =========================================================
    # UNKNOWN / UNCLASSIFIED
    # =========================================================

    return None