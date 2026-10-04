from datetime import date
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.mapper import map_work_item
from app.auditor import (
    audit_activity,
    audit_section_activity,
    QUERY_SECTIONS,
)
from app.azure_devops import AzureDevOpsClient

app = FastAPI(title="QA Activity Auditor", version="0.2.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
    )


@app.post("/audit/sample")
def audit_sample(extraction_date: date = date(2026, 9, 6)):
    item = {
        "id": 127989,
        "fields": {
            "System.Title": "UAT_KE : Enhance KE Reports (Central Bank Requirement) Test Execution",
            "System.State": "In UAT",
            "System.AssignedTo": {"displayName": "Muqaddas Muneeb"},
            "Custom.ChannelName": "KE - Enhance KE reports (Central Bank Requirement)",
            "Custom.ActualStartDate": "2026-08-16T20:00:00Z",
            "Custom.ActualEndDate": "2026-08-23T20:00:00Z",
            "Custom.TargetStartDate": "2026-08-18T20:00:00Z",
            "Custom.TargetEndDate": "2026-08-23T20:00:00Z",
            "Custom.UATStartDate": "2026-08-17T13:08:00Z",
            "Custom.UATEndDate": "2026-08-23T20:00:00Z",
            "Custom.UATCompletionPercentage": 100,
            "Custom.OverallUATBugs": 1,
            "Custom.CompletionPercentage": 100,
            "Custom.DetailedDescription": "6th Sept 2026 - UAT Testing Completed. Approved in CAB",
            "System.Tags": "In UAT; OngoingTask",
        },
    }
    return audit_activity(
        map_work_item(item),
        extraction_date,
    ).model_dump(mode="json")


async def fetch_section(client, query_id, section, extraction_date):
    query = await client.get_query_by_id(query_id)
    wiql = query.get("wiql")

    if not wiql:
        raise HTTPException(
            status_code=500,
            detail=f"WIQL was not returned for section '{section}'.",
        )

    work_item_ids = await client.execute_wiql(wiql)
    work_items = await client.get_work_items(work_item_ids)

    audits = [
        audit_section_activity(
            map_work_item(item, section=section),
            section,
            extraction_date,
        )
        for item in work_items
    ]

    return {
        "query_id": query.get("id"),
        "query_name": query.get("name"),
        "query_path": query.get("path"),
        "query_type": query.get("queryType"),
        "count": len(audits),
        "audits": audits,
    }


@app.get("/azure-devops/test")
async def test_azure_devops():
    client = AzureDevOpsClient()
    # Test the configured primary query.
    query = await client.get_query()

    return {
        "connected": True,
        "query_id": query.get("id"),
        "query_name": query.get("name"),
        "query_path": query.get("path"),
        "query_type": query.get("queryType"),
        "wiql": query.get("wiql"),
    }


@app.get("/azure-devops/query")
async def get_azure_devops_query():
    client = AzureDevOpsClient()
    query = await client.get_query()
    wiql = query.get("wiql")

    if not wiql:
        raise HTTPException(status_code=500, detail="WIQL was not returned from Azure DevOps.")

    work_item_ids = await client.execute_wiql(wiql)
    work_items = await client.get_work_items(work_item_ids)

    return {
        "query_id": query.get("id"),
        "query_name": query.get("name"),
        "query_path": query.get("path"),
        "query_type": query.get("queryType"),
        "count": len(work_items),
        "tasks": work_items,
    }


@app.get("/azure-devops/query/{query_id}")
async def get_specific_azure_devops_query(query_id: str):
    if query_id not in QUERY_SECTIONS:
        raise HTTPException(status_code=404, detail="Query ID is not configured.")

    client = AzureDevOpsClient()
    query = await client.get_query_by_id(query_id)
    wiql = query.get("wiql")

    if not wiql:
        raise HTTPException(status_code=500, detail="WIQL was not returned from Azure DevOps.")

    work_item_ids = await client.execute_wiql(wiql)
    work_items = await client.get_work_items(work_item_ids)

    return {
        "query_id": query.get("id"),
        "query_name": query.get("name"),
        "query_path": query.get("path"),
        "query_type": query.get("queryType"),
        "section": QUERY_SECTIONS[query_id],
        "count": len(work_items),
        "tasks": work_items,
    }


@app.get("/azure-devops/audit")
async def audit_azure_devops(extraction_date: date | None = None):
    if extraction_date is None:
        extraction_date = date.today()

    client = AzureDevOpsClient()
    all_audits = []
    sections = []

    for query_id, section in QUERY_SECTIONS.items():
        result = await fetch_section(
            client,
            query_id,
            section,
            extraction_date,
        )
        sections.append({
            "query_id": result["query_id"],
            "query_name": result["query_name"],
            "query_path": result["query_path"],
            "section": section,
            "count": result["count"],
        })
        all_audits.extend(
            audit.model_dump(mode="json")
            for audit in result["audits"]
        )

    return {
        "extraction_date": extraction_date,
        "section_count": len(sections),
        "sections": sections,
        "count": len(all_audits),
        "audits": all_audits,
    }


@app.get("/azure-devops/audit/{query_id}")
async def audit_specific_section(
    query_id: str,
    extraction_date: date | None = None,
):
    if query_id not in QUERY_SECTIONS:
        raise HTTPException(status_code=404, detail="Query ID is not configured.")

    if extraction_date is None:
        extraction_date = date.today()

    client = AzureDevOpsClient()
    result = await fetch_section(
        client,
        query_id,
        QUERY_SECTIONS[query_id],
        extraction_date,
    )

    return {
        "extraction_date": extraction_date,
        "section": QUERY_SECTIONS[query_id],
        "query_id": result["query_id"],
        "query_name": result["query_name"],
        "query_path": result["query_path"],
        "count": result["count"],
        "audits": [
            audit.model_dump(mode="json")
            for audit in result["audits"]
        ],
    }
