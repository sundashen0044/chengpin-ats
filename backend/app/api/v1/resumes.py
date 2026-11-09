from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.core.database import get_db
from app.models.models import Resume, JobPosition
from app.schemas.schemas import ResumeOut
from app.services.resume_service import parse_resume

router = APIRouter()
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    position_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """上传简历，解析为结构化 JSON 存入数据库。"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(400, "仅支持 PDF / DOCX / TXT")
    if position_id is not None and not db.get(JobPosition, position_id):
        raise HTTPException(404, "岗位不存在")

    save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "简历不能超过 10 MB")
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        parsed = await parse_resume(save_path)
    except Exception as exc:
        os.remove(save_path)
        raise HTTPException(422, "简历解析失败，请检查文件内容") from exc
    resume = Resume(
        position_id=position_id,
        candidate_name=parsed.get("candidate_name", ""),
        email=parsed.get("email", ""),
        phone=parsed.get("phone", ""),
        raw_text=parsed.get("raw_text", ""),
        parsed=parsed,
        file_path=save_path,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=List[ResumeOut])
def list_resumes(
    position_id: Optional[int] = None,
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(Resume)
    if position_id is not None:
        query = query.filter(Resume.position_id == position_id)
    term = search.strip()
    if term:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.filter(or_(
            Resume.candidate_name.ilike(pattern, escape="\\"),
            Resume.email.ilike(pattern, escape="\\"),
            Resume.raw_text.ilike(pattern, escape="\\"),
        ))
    return query.order_by(Resume.created_at.desc()).limit(200).all()


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    r = db.query(Resume).get(resume_id)
    if not r:
        raise HTTPException(404, "简历不存在")
    return r
