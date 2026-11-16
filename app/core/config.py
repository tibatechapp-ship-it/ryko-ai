"""إعدادات التطبيق عبر المتغيرات البيئية."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """إعدادات المنصة مع قيم افتراضية آمنة للتطوير."""

    app_name: str = "Ryko-AI"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    # مزود الذكاء الاصطناعي الافتراضي (DeepSeek API للـ MVP)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # الأمان
    jwt_secret: str = ""
    api_key: str = ""

    # الذاكرة (ChromaDB)
    database_url: str = "./data/chroma"

    # النموذج المحلي بعد التدريب
    local_model_path: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """إرجاع نسخة واحدة من الإعدادات أثناء عمر العملية."""
    return Settings()
