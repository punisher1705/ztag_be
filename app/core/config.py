
"""
Centralized, validated application configuration.
 
Design principle (Single Responsibility + Dependency Inversion):
No other module in this codebase should call `os.getenv` directly.
Every setting is declared, typed, and validated exactly once, here.
If a required variable is missing or malformed, the app fails to
start rather than failing silently at request time — this is the
"fail fast" pattern.
"""

from functools import lru_cache
from typing import Dict

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )

    app_env: str = Field(default="development")
    app_name: str = Field(default="zero-trust-gateway")
    app_debug: bool = Field(default=False)
    app_secret_key: str = Field(..., min_length=16)
    log_level: str = Field(default="INFO")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5001)
 
    # --- Database ---
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str
 
    # --- Redis ---
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
 
    # --- JWT ---
    jwt_secret_key: str = Field(..., min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 15
    jwt_refresh_token_expires_days: int = 7
    jwt_issuer: str = "zero-trust-gateway"
 
    # --- Rate limiting ---
    rate_limit_default: str = "100/minute"
    rate_limit_storage_url: str = "redis://redis:6379/1"
 
    # --- Anomaly detection / LLM ---
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    anomaly_check_enabled: bool = True
    anomaly_check_window_minutes: int = 5
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
 
    # --- Observability ---
    otel_exporter_otlp_endpoint: str = "http://tempo:4317"
    otel_service_name: str = "zero-trust-gateway"
    prometheus_metrics_path: str = "/metrics"
 
    # --- Downstream services ---
    downstream_services: str = ""

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        print(v)
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got '{v}'")
        return v
 
    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
 
    @property
    def downstream_registry(self) -> Dict[str, str]:
        """Parses 'name:url,name2:url2' into a dict. Empty-safe."""
        registry: Dict[str, str] = {}
        if not self.downstream_services:
            return registry
        for pair in self.downstream_services.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            name, _, url = pair.partition(":")
            registry[name.strip()] = url.strip()
        return registry
    
@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - loaded once per process"""
    return Settings()

