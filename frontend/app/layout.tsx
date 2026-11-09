import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "澄聘 · AI 简历筛选",
  description: "LLM 生成岗位需求，结构化筛选简历，可解释评分与面试流转。",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
