from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.compliance import check_filter_criteria
from app.models.models import JobPosition, AuditLog
from app.schemas.schemas import JobPositionCreate, JobPositionOut
from app.services.llm_service import generate_jd

router = APIRouter()


@router.post("/generate", response_model=JobPositionOut)
async def create_job_with_generated_jd(
    payload: JobPositionCreate, db: Session = Depends(get_db)
):
    """LLM 自动生成 JD 与可勾选筛选条件。"""
    jd = await generate_jd(payload.title, payload.jd_text or "")
    job = JobPosition(
        title=jd.get("title", payload.title),
        department=payload.department,
        role_key=payload.role_key,
        jd_text=payload.jd_text or jd.get("summary", ""),
        structured=jd,
        screening_criteria=jd.get("screening_criteria", {}),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=List[JobPositionOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobPosition).order_by(JobPosition.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobPositionOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPosition).get(job_id)
    if not job:
        raise HTTPException(404, "岗位不存在")
    return job
