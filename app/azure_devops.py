import base64
import httpx

from app.config import settings


class AzureDevOpsClient:

    def __init__(self):
        self.base = (
            f"https://dev.azure.com/"
            f"{settings.azdo_organization}/"
            f"{settings.azdo_project}"
        )

        token = base64.b64encode(
            f":{settings.azdo_pat}".encode()
        ).decode()

        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    async def get_query(self):

        url = (
            f"{self.base}/_apis/wit/queries/"
            f"{settings.azdo_query_id}?api-version=7.1"
        )

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.get(
                url,
                headers=self.headers,
            )

            if response.status_code != 200:

                raise Exception(
                    f"Azure DevOps query request failed. "
                    f"Status={response.status_code}, "
                    f"URL={url}, "
                    f"Response={response.text}"
                )

            return response.json()

    async def get_query_by_id(self, query_id):

        url = (
            f"{self.base}/_apis/wit/queries/"
            f"{query_id}?$expand=wiql&api-version=7.1"
        )

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.get(
                url,
                headers=self.headers,
            )

            if response.status_code != 200:

                raise Exception(
                    f"Azure DevOps query request failed. "
                    f"Status={response.status_code}, "
                    f"URL={url}, "
                    f"Response={response.text}"
                )

            return response.json()

    async def execute_wiql(self, wiql):

        url = (
            f"{self.base}/_apis/wit/wiql"
            f"?api-version=7.1"
        )

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.post(
                url,
                headers=self.headers,
                json={
                    "query": wiql
                },
            )

            response.raise_for_status()

            return [
                item["id"]
                for item in response.json().get("workItems", [])
            ]

    async def get_work_items(self, ids):

        if not ids:
            return []

        url = (
            f"{self.base}/_apis/wit/workitemsbatch"
            f"?api-version=7.1"
        )

        async with httpx.AsyncClient(timeout=60) as client:

            response = await client.post(
                url,
                headers=self.headers,
                json={
                    "ids": ids,
                    "errorPolicy": "Omit",
                },
            )

            response.raise_for_status()

            return response.json().get("value", [])