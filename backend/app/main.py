from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.api_router import api_router

# 启动时建表（生产建议用 Alembic 迁移）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI 简历筛选系统（严格合规版）：LLM 生成 JD → 结构化筛选 → 可解释评分 → 面试流转",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "compliance_strict": not settings.ALLOW_PROTECTED_ATTRIBUTE_FILTERING}
