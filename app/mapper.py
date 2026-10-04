from datetime import datetime
from app.models import QAActivity


def dt(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


def map_work_item(item: dict, section: str | None = None) -> QAActivity:
    f = item.get("fields", {})
    assigned = f.get("System.AssignedTo")
    tags = [
        x.strip()
        for x in (f.get("System.Tags") or "").split(";")
        if x.strip()
    ]

    # Azure data has appeared with both Totaltestcase and TotalTestCase.
    total_testcase = f.get("Custom.TotalTestCase")
    if total_testcase is None:
        total_testcase = f.get("Custom.Totaltestcase")

    return QAActivity(
        work_item_id=item["id"],
        title=f.get("System.Title", ""),
        section=section,
        assignee=assigned.get("displayName") if isinstance(assigned, dict) else assigned,
        state=f.get("System.State"),
        channel_name=f.get("Custom.ChannelName"),
        detailed_description=f.get("Custom.DetailedDescription"),
        target_start_date=dt(f.get("Custom.TargetStartDate")),
        target_end_date=dt(f.get("Custom.TargetEndDate")),
        actual_start_date=dt(f.get("Custom.ActualStartDate")),
        actual_end_date=dt(f.get("Custom.ActualEndDate")),
        completion_percentage=f.get("Custom.CompletionPercentage"),
        total_testcase=total_testcase,
        qa_defect_count=f.get("Custom.QADefectsCount"),
        uat_start_date=dt(f.get("Custom.UATStartDate")),
        uat_end_date=dt(f.get("Custom.UATEndDate")),
        uat_completion_percentage=f.get("Custom.UATCompletionPercentage"),
        overall_uat_bugs=f.get("Custom.OverallUATBugs"),
        integration_build=f.get("Microsoft.VSTS.Build.IntegrationBuild"),
        tags=tags,
    )
