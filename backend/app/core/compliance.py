"""
合规守卫（Compliance Guard）
职责：在筛选条件进入查询/评分前，拦截受保护属性的自动过滤。

设计原则：
1. 默认禁止将 gender / age / birth_year / marital_status / ethnicity
   作为自动过滤或排序依据。
2. 即使管理员打开 ALLOW_PROTECTED_ATTRIBUTE_FILTERING，
   也必须在法务白名单岗位 (PROTECTED_ATTR_WHITELIST_ROLES) 内，
   且所有命中都会写入审计日志 (audit_log)。
3. 本模块是"硬约束"，路由层调用它而不是各自判断，避免漏检。
"""
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings, PROTECTED_ATTRIBUTES


class ComplianceViolation(Exception):
    """当筛选条件触犯合规红线时抛出。"""

    def __init__(self, fields: List[str], message: str = ""):
        self.fields = fields
        self.message = message or (
            f"以下字段属于受保护属性，禁止用于自动筛选：{', '.join(fields)}"
        )
        super().__init__(self.message)


@dataclass
class ComplianceResult:
    allowed: bool
    blocked_fields: List[str]
    requires_audit: bool
    reason: str = ""


def check_filter_criteria(
    criteria_fields: List[str],
    role_key: Optional[str] = None,
) -> ComplianceResult:
    """
    校验一批筛选条件字段是否合规。

    :param criteria_fields: 本次筛选涉及的字段名集合
    :param role_key: 目标岗位标识，用于法务白名单判定
    :return: ComplianceResult
    :raises ComplianceViolation: 当严格合规模式下出现受保护字段
    """
    touched = [f for f in criteria_fields if f in PROTECTED_ATTRIBUTES]

    if not touched:
        return ComplianceResult(
            allowed=True, blocked_fields=[], requires_audit=False
        )

    # 严格合规模式：直接拦截
    if not settings.ALLOW_PROTECTED_ATTRIBUTE_FILTERING:
        raise ComplianceViolation(touched)

    # 宽松模式仍需法务白名单岗位 + 审计留痕
    if role_key and role_key in settings.PROTECTED_ATTR_WHITELIST_ROLES:
        return ComplianceResult(
            allowed=True,
            blocked_fields=[],
            requires_audit=True,
            reason="法务白名单岗位，需记录审计日志",
        )

    raise ComplianceViolation(
        touched,
        message="受保护属性筛选仅在法务白名单岗位可用，且会记录审计日志。",
    )


def sanitize_ranking_fields(fields: List[str]) -> List[str]:
    """从排序/评分字段中剔除受保护属性，保证永不参与排序。"""
    return [f for f in fields if f not in PROTECTED_ATTRIBUTES]
