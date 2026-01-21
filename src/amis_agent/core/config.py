from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    send_daily_limit: int = Field(default=5, alias="SEND_DAILY_LIMIT")
    send_domain_daily_limit: int = Field(default=2, alias="SEND_DOMAIN_DAILY_LIMIT")
    send_error_spike_limit: int = Field(default=5, alias="SEND_ERROR_SPIKE_LIMIT")
    send_error_window_s: int = Field(default=3600, alias="SEND_ERROR_WINDOW_S")
    send_queue_name: str = Field(default="send", alias="SEND_QUEUE_NAME")

    llm_base_url: str = Field(default="https://api.openai.com", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o", alias="LLM_MODEL")
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    llm_max_tokens: int = Field(default=400, alias="LLM_MAX_TOKENS")

    email_from: str = Field(alias="EMAIL_FROM")
    email_display_name: str = Field(alias="EMAIL_DISPLAY_NAME")
    company_name: str = Field(alias="COMPANY_NAME")
    footer_address: str = Field(alias="FOOTER_ADDRESS")
    footer_text: str | None = Field(default=None, alias="FOOTER_TEXT")

    region_policy_us: str = Field(default="auto_send", alias="REGION_POLICY_US")
    region_policy_eu: str = Field(default="opt_in_only", alias="REGION_POLICY_EU")

    google_credentials_file: str = Field(alias="GOOGLE_CREDENTIALS_FILE")
    google_token_file: str = Field(alias="GOOGLE_TOKEN_FILE")
    google_scopes: str = Field(
        default="https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.readonly",
        alias="GOOGLE_SCOPES",
    )
    google_redirect_uri: str = Field(default="http://localhost:8080/", alias="GOOGLE_REDIRECT_URI")
    gmail_sender: str = Field(alias="GMAIL_SENDER")
    google_oauth_mode: str | None = Field(default=None, alias="GOOGLE_OAUTH_MODE")

    scrape_user_agent: str = Field(default="AMISAgentBot/1.0", alias="SCRAPE_USER_AGENT")
    scrape_timeout_s: int = Field(default=20, alias="SCRAPE_TIMEOUT_S")
    scrape_rate_limit_per_host: int = Field(default=1, alias="SCRAPE_RATE_LIMIT_PER_HOST")
    scrape_allowed_domains: str = Field(default="", alias="SCRAPE_ALLOWED_DOMAINS")

    qualify_allowed_sources: str = Field(default="", alias="QUALIFY_ALLOWED_SOURCES")
    qualify_allowed_domains: str = Field(default="", alias="QUALIFY_ALLOWED_DOMAINS")
    enrich_allowed_domains: str = Field(default="", alias="ENRICH_ALLOWED_DOMAINS")


@lru_cache
def get_settings() -> Settings:
    return Settings()

