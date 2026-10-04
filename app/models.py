from datetime import datetime, date
from typing import Any, Optional
from pydantic import BaseModel, Field


class QAActivity(BaseModel):
    work_item_id: int
    title: str
    activity_type: Optional[str] = None
    section: Optional[str] = None
    assignee: Optional[str] = None
    state: Optional[str] = None
    channel_name: Optional[str] = None
    detailed_description: Optional[str] = None
    target_start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    completion_percentage: Optional[float] = None
    total_testcase: Optional[float] = None
    qa_defect_count: Optional[float] = None
    uat_start_date: Optional[datetime] = None
    uat_end_date: Optional[datetime] = None
    uat_completion_percentage: Optional[float] = None
    overall_uat_bugs: Optional[float] = None
    integration_build: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    @property
    def tag_set(self) -> set[str]:
        return {x.strip().lower() for x in self.tags if x.strip()}


class WeeklyPeriod(BaseModel):
    extraction_date: date
    period_start: date
    period_end: date


class ValidationResult(BaseModel):
    work_item_id: int
    rule_id: str
    field_name: str
    status: str
    severity: str
    actual_value: Any = None
    expected_value: Any = None
    message: str
    source: str = "RULE"


class ActivityAudit(BaseModel):
    work_item_id: int
    title: str
    activity_type: Optional[str]
    section: Optional[str] = None
    assignee: Optional[str] = None
    state: Optional[str] = None
    completion_percentage: Optional[float] = None
    eligible: bool = True
    ongoing: bool = False
    results: list[ValidationResult] = Field(default_factory=list)
