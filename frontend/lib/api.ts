// 与后端 FastAPI 通信的轻量客户端
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function req(path: string, options: RequestInit = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  // 岗位
  generateJob: (title: string, jd?: string) =>
    req("/jobs/generate", { method: "POST", body: JSON.stringify({ title, jd_text: jd }) }),
  listJobs: () => req("/jobs"),

  // 简历
  listResumes: (positionId?: number, search?: string) => {
    const params = new URLSearchParams();
    if (positionId) params.set("position_id", String(positionId));
    if (search?.trim()) params.set("search", search.trim());
    return req(`/resumes?${params.toString()}`);
  },
  uploadResume: async (file: File, positionId: number) => {
    const body = new FormData();
    body.append("file", file);
    body.append("position_id", String(positionId));
    const response = await fetch(`${BASE}/resumes/upload`, { method: "POST", body });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  // 筛选
  runScreening: (positionId: number, criteria: any, fields: string[]) =>
    req("/screening/run", {
      method: "POST",
      body: JSON.stringify({ position_id: positionId, criteria, criteria_fields: fields }),
    }),

  // 面试
  listInterviews: (resumeId: number) => req(`/interviews/resume/${resumeId}`),
  createInterview: (data: {resume_id: number; round_name: string; interviewer: string; feedback: string; scorecard: Record<string, number>}) =>
    req("/interviews", { method: "POST", body: JSON.stringify(data) }),
  updateInterviewStatus: (id: number, status: string) =>
    req(`/interviews/${id}/status?status=${status}`, { method: "PATCH" }),
};
