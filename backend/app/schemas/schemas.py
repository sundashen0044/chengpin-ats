from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any


# ---------- 岗位 ----------
class JobPositionCreate(BaseModel):
    title: str
    department: Optional[str] = None
    role_key: Optional[str] = None
    jd_text: Optional[str] = None


class JobPositionOut(BaseModel):
    id: int
    title: str
    department: Optional[str]
    role_key: Optional[str]
    jd_text: Optional[str]
    structured: Optional[Dict[str, Any]]
    screening_criteria: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# ---------- 简历 ----------
class ResumeOut(BaseModel):
    id: int
    position_id: Optional[int]
    candidate_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    parsed: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# ---------- 筛选 ----------
class ScreeningCriteria(BaseModel):
    """可勾选的筛选条件（仅含合规中性字段）。"""
    model_config = ConfigDict(extra="forbid")
    min_years_experience: Optional[int] = None
    required_skills: List[str] = Field(default_factory=list)
    education_level: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    salary_expectation_max: Optional[int] = None


class ScreeningRequest(BaseModel):
    position_id: int
    criteria: ScreeningCriteria
    # 前端传来的字段列表，用于合规守卫校验
    criteria_fields: List[str] = []


# ---------- 匹配结果 ----------
class MatchDimension(BaseModel):
    name: str
    score: float
    evidence: str  # 引用简历原文作为依据，保证可解释


class MatchResultOut(BaseModel):
    resume_id: int
    total_score: float
    passed: bool
    dimensions: List[MatchDimension]

    class Config:
        from_attributes = True


# ---------- 面试 ----------
class InterviewCreate(BaseModel):
    resume_id: int
    round_name: str
    scorecard: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None
    interviewer: Optional[str] = None


class InterviewOut(BaseModel):
    id: int
    resume_id: int
    round_name: str
    status: str
    scorecard: Optional[Dict[str, Any]]
    feedback: Optional[str]
    interviewer: Optional[str]

    class Config:
        from_attributes = True
