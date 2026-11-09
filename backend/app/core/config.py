"""
应用配置（严格合规版）
- 默认关闭任何受保护属性的自动筛选能力
- 通过环境变量覆盖，便于私有化部署
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "澄聘"
    API_V1_PREFIX: str = "/api/v1"

    # 数据库：默认 SQLite，生产可切 Postgres
    DATABASE_URL: str = "sqlite:///./smartscreener.db"

    # LLM 提供商：openai | ollama（本地优先，隐私友好）
    LLM_PROVIDER: str = "ollama"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # 合规开关：受保护属性（性别/年龄/婚育等）是否允许作为筛选条件
    # 严格合规版默认 False，且代码层面对这类字段做了白名单拦截
    ALLOW_PROTECTED_ATTRIBUTE_FILTERING: bool = False
    # 即使合规开关开启，也只允许法务白名单内的真实职业资格场景
    PROTECTED_ATTR_WHITELIST_ROLES: List[str] = []

    # 评分温度固定为 0，保证同一简历多次评分结果稳定
    LLM_TEMPERATURE: float = 0.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 受保护属性字段：这些字段严禁用于自动过滤/排序
PROTECTED_ATTRIBUTES = {"gender", "birth_year", "age", "marital_status", "ethnicity"}
