"""
LLM 服务：JD 自动生成 + 简历评分。
支持 OpenAI 兼容 API 与本地 Ollama，温度固定 0 保证稳定。
"""
import json
import re
from typing import Dict, Any, Optional

import httpx

from app.core.config import settings


async def _chat(messages, temperature: float = None) -> str:
    temperature = settings.LLM_TEMPERATURE if temperature is None else temperature

    if settings.LLM_PROVIDER == "ollama":
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    # OpenAI 兼容
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": settings.OPENAI_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """从 LLM 输出中稳健提取 JSON。"""
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


JD_PROMPT = """你是资深 HRBP。基于岗位标题和补充信息，生成一份结构化岗位需求。
只输出 JSON，字段：
title, summary, required_skills(数组), nice_to_have(数组),
min_years_experience(数字), education_level, responsibilities(数组),
screening_criteria(对象：min_years_experience, required_skills, education_level, locations)。
岗位标题：{title}
补充信息：{extra}
注意：screening_criteria 不得包含性别、年龄、婚育等受保护属性。"""


async def generate_jd(title: str, extra: str = "") -> Dict[str, Any]:
    content = await _chat([
        {"role": "user", "content": JD_PROMPT.format(title=title, extra=extra)}
    ])
    data = _extract_json(content)
    return data or {"title": title, "summary": content}


SCORE_PROMPT = """你是资深招聘评估专家。对照岗位结构化要求，评估简历匹配度。
只输出 JSON：
{{
  "total_score": 0-100,
  "passed": true/false,
  "dimensions": [
    {{"name": "技能匹配", "score": 0-100, "evidence": "引用简历原文片段作为依据"}},
    {{"name": "经验年限", "score": 0-100, "evidence": "..."}},
    {{"name": "教育背景", "score": 0-100, "evidence": "..."}},
    {{"name": "项目相关度", "score": 0-100, "evidence": "..."}}
  ]
}}
评分必须给出简历原文证据，做到可解释。
岗位要求：{jd}
简历结构化信息：{resume}"""


async def score_resume(jd_structured: Dict[str, Any], resume_parsed: Dict[str, Any], source_text: str = "") -> Dict[str, Any]:
    content = await _chat([
        {"role": "user", "content": SCORE_PROMPT.format(
            jd=json.dumps(jd_structured, ensure_ascii=False),
            resume=json.dumps(resume_parsed, ensure_ascii=False),
        )}
    ])
    data = _extract_json(content)
    if not isinstance(data, dict):
        return {"total_score": 0, "passed": False, "dimensions": []}
    dimensions = []
    for item in data.get("dimensions", []):
        if not isinstance(item, dict):
            continue
        evidence = str(item.get("evidence") or "").strip()
        # 模型生成的证据必须能在简历原文中找到，否则不呈现为事实。
        if not source_text or evidence not in source_text:
            evidence = ""
        dimensions.append({
            "name": str(item.get("name") or "未命名维度")[:80],
            "score": max(0, min(100, float(item.get("score") or 0))),
            "evidence": evidence,
        })
    score = max(0, min(100, float(data.get("total_score") or 0)))
    if not any(d["evidence"] for d in dimensions):
        score = 0
    return {"total_score": score, "passed": bool(data.get("passed")) and score > 0, "dimensions": dimensions}
