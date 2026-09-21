from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://supportsense:supportsense@localhost:5432/supportsense"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    password_reset_token_expire_minutes: int = 30

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_requests_per_minute: int = 30
    groq_requests_per_day: int = 1000

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_requests_per_minute: int = 15
    gemini_requests_per_day: int = 500

    llm_max_response_tokens: int = 300
    llm_history_max_turns: int = 4
    llm_max_context_snippets: int = 3

    retrieval_top_k: int = 5
    kb_direct_similarity_threshold: float = 0.88
    conversation_summary_trigger_turns: int = 12

    semantic_cache_ttl_seconds: int = 3600
    semantic_cache_similarity_threshold: float = 0.92
    semantic_cache_max_entries: int = 500

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    tts_voice: str = "en-US-AriaNeural"
    voice_partial_transcribe_seconds: float = 2.0
    voice_max_utterance_seconds: float = 30.0

    cors_allowed_origins: str = "http://localhost:5173"

    rate_limit_default: str = "60/minute"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
