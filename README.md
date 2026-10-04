# QA Activity Auditor — starter

Weekly Azure DevOps QA activity data-quality auditor.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

The starter includes:
- Azure DevOps REST client
- title-based activity classification
- Sunday–Thursday eligibility engine
- common and activity-specific rules
- HTML description cleaning
- sample audit endpoint based on work item 127989

Next implementation work: query execution, batch extraction, persistent database, Sunday scheduler, full reporting, and AI semantic analysis.

Never commit `.env` or a PAT.
