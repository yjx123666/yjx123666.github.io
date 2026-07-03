"""应用配置"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "地图标注系统 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库（默认 SQLite，可通过环境变量切换 PostgreSQL）
    DATABASE_URL: str = "sqlite:///./data/map_annotations.db"

    # CORS（生产环境只允许前端域名）
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
