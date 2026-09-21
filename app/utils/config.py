import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT_DIR = Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class Settings:
    database_path: str
    model_dir: str
    prompt_dir: str
    openai_api_key: str
    openai_model: str
    mock_llm: bool
    api_base_url: str
    secret_key: str
    token_ttl_seconds: int
    max_content_length: int
    rate_limit_per_minute: int
    log_level: str

    @classmethod
    def from_env(cls):
        return cls(
            database_path=os.getenv("DATABASE_PATH", str(ROOT_DIR / "data" / "support.db")),
            model_dir=os.getenv("MODEL_DIR", str(ROOT_DIR / "models")),
            prompt_dir=os.getenv("PROMPT_DIR", str(ROOT_DIR / "app" / "prompts")),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            mock_llm=os.getenv("MOCK_LLM", "true").lower() in {"1", "true", "yes", "on"},
            api_base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:5000"),
            secret_key=os.getenv("SECRET_KEY", "development-only-change-me"),
            token_ttl_seconds=int(os.getenv("TOKEN_TTL_SECONDS", "3600")),
            max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", "16384")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
