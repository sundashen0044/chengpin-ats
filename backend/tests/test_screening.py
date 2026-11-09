import os
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.models import JobPosition, Resume
from app.services.llm_service import score_resume


class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            job = JobPosition(title="工程师", structured={"required_skills": ["Python"]})
            db.add(job)
            db.flush()
            self.job_id = job.id
            db.add(Resume(
                position_id=job.id, candidate_name="测试候选人",
                raw_text="负责 Python API 开发",
                parsed={"candidate_name": "测试候选人", "skills": ["Python"], "raw_text": "负责 Python API 开发"},
            ))
            db.commit()

        def session():
            with Session(self.engine) as db:
                yield db
        app.dependency_overrides[get_db] = session
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_protected_attribute_is_rejected(self):
        response = self.client.post("/api/v1/screening/run", json={
            "position_id": self.job_id,
            "criteria": {"required_skills": ["Python"], "gender": "male"},
            "criteria_fields": ["gender"],
        })
        self.assertEqual(response.status_code, 422)

    def test_screening_uses_real_candidate_without_identity_in_prompt(self):
        async def fake_score(job, candidate, source):
            self.assertNotIn("candidate_name", candidate)
            self.assertNotIn("raw_text", candidate)
            self.assertEqual(source, "负责 Python API 开发")
            return {"total_score": 82, "passed": True, "dimensions": [
                {"name": "技能", "score": 82, "evidence": "Python API 开发"}
            ]}
        with patch("app.api.v1.screening.score_resume", fake_score):
            response = self.client.post("/api/v1/screening/run", json={
                "position_id": self.job_id,
                "criteria": {"required_skills": ["Python"]},
                "criteria_fields": ["required_skills"],
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["total_score"], 82)

    def test_fabricated_evidence_cannot_keep_a_high_score(self):
        fake = '{"total_score":95,"passed":true,"dimensions":[{"name":"技能","score":95,"evidence":"并不存在的经历"}]}'
        with patch("app.services.llm_service._chat", new=AsyncMock(return_value=fake)):
            result = asyncio.run(score_resume({}, {"skills": ["Python"]}, "负责 Python API 开发"))
        self.assertEqual(result["total_score"], 0)
        self.assertFalse(result["passed"])
        self.assertEqual(result["dimensions"][0]["evidence"], "")

    def test_resume_search_is_limited_to_selected_job(self):
        with Session(self.engine) as db:
            other = JobPosition(title="其他岗位")
            db.add(other)
            db.flush()
            db.add(Resume(
                position_id=other.id, candidate_name="隔离候选人",
                raw_text="Python", parsed={"skills": ["Python"]},
            ))
            db.commit()
        response = self.client.get(
            "/api/v1/resumes",
            params={"position_id": self.job_id, "search": "Python"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["candidate_name"], "测试候选人")


if __name__ == "__main__":
    unittest.main()
