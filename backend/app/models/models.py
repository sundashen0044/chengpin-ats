from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class JobPosition(Base):
    """岗位需求（可由 LLM 自动生成）。"""
    __tablename__ = "job_positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    department = Column(String(100))
    role_key = Column(String(100), index=True)  # 用于法务白名单判定
    jd_text = Column(Text)                      # 完整 JD 原文
    structured = Column(JSON)                   # LLM 解析出的结构化要求
    screening_criteria = Column(JSON)           # 可勾选的筛选条件（合规字段）
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="position")


class Resume(Base):
    """简历（存储于数据库，可筛选/查看/比较）。"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("job_positions.id"), nullable=True)
    candidate_name = Column(String(120))
    email = Column(String(200))
    phone = Column(String(50))
    raw_text = Column(Text)          # 解析后的纯文本
    parsed = Column(JSON)            # 结构化：教育/工作/技能/年限/项目
    file_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    position = relationship("JobPosition", back_populates="resumes")
    matches = relationship("MatchResult", back_populates="resume")
    interviews = relationship("Interview", back_populates="resume")


class MatchResult(Base):
    """简历-岗位匹配打分结果（可解释）。"""
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("job_positions.id"), nullable=False)
    total_score = Column(Float)
    passed = Column(Boolean)
    dimensions = Column(JSON)   # 各维度得分 + 依据证据原文
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="matches")


class Interview(Base):
    """面试记录（一面/二面/终面），含结构化评分卡。"""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    round_name = Column(String(50), nullable=False)  # 一面 / 二面 / 终面
    status = Column(String(30), default="pending")   # pending/pass/fail
    scorecard = Column(JSON)      # 评分卡：维度-分数-评语
    feedback = Column(Text)
    interviewer = Column(String(120))
    scheduled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="interviews")


class AuditLog(Base):
    """审计日志：记录每次合规相关的筛选动作，谁在何时用了什么条件。"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(120))
    action = Column(String(100))
    fields_used = Column(JSON)
    role_key = Column(String(100))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
