from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.compliance import check_filter_criteria, ComplianceViolation
from app.models.models import (
    Resume, JobPosition, MatchResult, AuditLog
)
from app.schemas.schemas import ScreeningRequest, MatchResultOut
from app.services.llm_service import score_resume

router = APIRouter()


@router.post("/run", response_model=List[MatchResultOut])
async def run_screening(payload: ScreeningRequest, db: Session = Depends(get_db)):
    """
    执行筛选：先用合规守卫校验条件字段，再对候选简历逐份评分。
    受保护属性（性别/年龄等）在此被硬拦截，命中会写入审计日志。
    """
    job = db.get(JobPosition, payload.position_id)
    if not job:
        raise HTTPException(404, "岗位不存在")

    # 合规守卫：拦截受保护属性
    actual_fields = list(set(payload.criteria_fields) | set(payload.criteria.model_dump(exclude_none=True)))
    try:
        result = check_filter_criteria(actual_fields, job.role_key)
    except ComplianceViolation as exc:
        raise HTTPException(422, exc.message) from exc
    if result.requires_audit:
        db.add(AuditLog(
            action="protected_attr_filter",
            fields_used=payload.criteria.dict(),
            role_key=job.role_key,
            detail=result.reason,
        ))
        db.commit()

    resumes = db.query(Resume).filter(Resume.position_id == payload.position_id).all()
    results = []
    for r in resumes:
        if not r.parsed:
            continue
        criteria = payload.criteria.model_dump(exclude_none=True)
        candidate = {k: v for k, v in (r.parsed or {}).items() if k not in {"candidate_name", "email", "phone", "raw_text", "gender", "age", "birth_year", "marital_status", "ethnicity"}}
        try:
            scored = await score_resume({"job": job.structured or {}, "selected_criteria": criteria}, candidate, r.raw_text or "")
        except Exception as exc:
            raise HTTPException(503, "评分服务暂不可用，请检查模型配置") from exc
        # 评分输入已在上方去除身份信息和受保护属性。
        mr = MatchResult(
            resume_id=r.id,
            position_id=job.id,
            total_score=scored.get("total_score", 0),
            passed=scored.get("passed", False),
            dimensions=scored.get("dimensions", []),
        )
        db.add(mr)
        results.append(MatchResultOut(
            resume_id=r.id,
            total_score=mr.total_score,
            passed=mr.passed,
            dimensions=[d for d in mr.dimensions],
        ))
    db.commit()
    results.sort(key=lambda x: x.total_score, reverse=True)
    return results
