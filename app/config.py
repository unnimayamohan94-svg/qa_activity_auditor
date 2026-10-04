from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    azdo_organization: str
    azdo_project: str
    azdo_query_id: str
    azdo_pat: str = ""
    reporting_timezone: str = "Asia/Dubai"
    use_mock_data: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

