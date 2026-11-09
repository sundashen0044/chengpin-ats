from fastapi import APIRouter

from app.api.v1 import jobs, resumes, screening, interviews

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(screening.router, prefix="/screening", tags=["screening"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
