"""
简历解析服务：PDF/DOCX -> 结构化 JSON。
基础版使用文本抽取 + 规则/LLM 提炼，保证字段统一便于筛选。
"""
from typing import Dict, Any

from app.services.llm_service import _chat, _extract_json

PARSE_PROMPT = """从以下简历纯文本中提取结构化信息，只输出 JSON：
{
  "candidate_name": "",
  "email": "",
  "phone": "",
  "education": [{"school":"","major":"","degree":"","graduation_year":""}],
  "work_experience": [{"company":"","title":"","start":"","end":"","highlights":[]}],
  "skills": [],
  "total_years_experience": 0,
  "projects": [{"name":"","role":"","description":""}]
}
不要包含性别、年龄、婚育等与岗位能力无关的受保护属性，即使简历里有也忽略。
简历文本：
{resume_text}"""


def extract_text_from_pdf(path: str) -> str:
    import fitz  # PyMuPDF
    text = []
    with fitz.open(path) as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)


def extract_text_from_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(path)
    if lower.endswith(".docx"):
        return extract_text_from_docx(path)
    if lower.endswith(".txt"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"不支持的文件类型：{path}")


async def parse_resume(path: str) -> Dict[str, Any]:
    """返回结构化简历。LLM 不可用时降级为最小结构。"""
    raw = extract_text(path)
    try:
        content = await _chat([
            {"role": "user", "content": PARSE_PROMPT.format(resume_text=raw[:8000])}
        ])
        data = _extract_json(content)
        if data:
            data["raw_text"] = raw
            return data
    except Exception:
        pass
    return {"raw_text": raw, "candidate_name": "", "skills": [], "work_experience": []}
