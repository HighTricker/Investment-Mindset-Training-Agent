"""Pydantic Settings：从 backend/.env 读取运行时配置。"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    db_path: str = "../investment_data/portfolio.db"
    log_level: str = "INFO"

    # SMTP（P5 邮件发送，V2）
    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_user: str | None = None
    smtp_password: str | None = None

    # 定时任务（APScheduler，V2）
    report_schedule_cron: str = "0 9 1 * *"
    report_schedule_enabled: bool = False

    # AI 月度点评（P5 报告内 LLM 生成，V3）
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None  # 空则 OpenAI 官方；大陆用户可填 DeepSeek / 智谱 等 OpenAI-compatible 端点
    ai_commentary_enabled: bool = False

    @property
    def database_url(self) -> str:
        """把 db_path（相对 backend/）解析为 SQLAlchemy 绝对路径 URL。"""
        path = Path(self.db_path)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        return f"sqlite:///{path.resolve().as_posix()}"


settings = Settings()
