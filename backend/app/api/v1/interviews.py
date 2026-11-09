from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.models import Interview
from app.schemas.schemas import InterviewCreate, InterviewOut

router = APIRouter()


@router.post("", response_model=InterviewOut)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db)):
    """记录一轮面试（一面/二面/终面）及其评分卡。"""
    iv = Interview(
        resume_id=payload.resume_id,
        round_name=payload.round_name,
        scorecard=payload.scorecard,
        feedback=payload.feedback,
        interviewer=payload.interviewer,
        status="pending",
    )
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return iv


@router.get("/resume/{resume_id}", response_model=List[InterviewOut])
def list_interviews(resume_id: int, db: Session = Depends(get_db)):
    """获取某候选人的全部面试轮次，按时间线展示。"""
    return (
        db.query(Interview)
        .filter(Interview.resume_id == resume_id)
        .order_by(Interview.created_at.asc())
        .all()
    )


@router.patch("/{interview_id}/status")
def update_status(interview_id: int, status: str, db: Session = Depends(get_db)):
    iv = db.query(Interview).get(interview_id)
    if not iv:
        raise HTTPException(404, "面试记录不存在")
    if status not in {"pending", "pass", "fail"}:
        raise HTTPException(400, "非法状态")
    iv.status = status
    db.commit()
    return {"id": iv.id, "status": iv.status}
