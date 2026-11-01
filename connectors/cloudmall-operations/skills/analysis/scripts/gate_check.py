"""
gate_check.py — Gate Check 自动化校验
ecommerce-data-analyst skill 工具层 (Phase 2a)

执行 G1-G4 四项校验，返回 GateCheckResult。

G1  漏斗自洽（上游 UV ≥ 下游 UV）
G2  率值合理（rate/ratio/率 字段 ≤ 1.0，pct/占比 字段 ≤ 100.0）
G3  非零校验（关键指标不全为 0）
G4  组件输出完整性（recipe 中必选组件均有输出）
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------


@dataclass
class CheckItem:
    id: str
    name: str
    passed: bool
    detail: str


@dataclass
class GateCheckResult:
    passed: bool
    checks: list[CheckItem] = field(default_factory=list)
    report_text: str = ""
    retry_count: int = 0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "retry_count": self.retry_count,
            "checks": [
                {
                    "id": c.id,
                    "name": c.name,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
            "report_text": self.report_text,
        }


# ---------------------------------------------------------------------------
# 校验器
# ---------------------------------------------------------------------------


class GateChecker:
    """Gate Check 自动化校验器。

    用法：
        result = GateChecker().run(
            domain_config={
                "funnel_pairs": [("browse_uv", "click_uv"), ("click_uv", "pay_uv")],
                "critical_metrics": ["gmv", "pay_uv"],
                "required_components": ["C01", "C02"],
            },
            component_outputs=[...],   # list[ComponentOutput] 或 list[dict]
        )
        print(result.report_text)
    """

    # ---------------------------------------------------------------------------
    # 主入口
    # ---------------------------------------------------------------------------

    def run(
        self,
        domain_config: dict,
        component_outputs: list = None,
        _retry_count: int = 0,
    ) -> GateCheckResult:
        """执行全部 Gate Check 项，返回 GateCheckResult。

        Args:
            domain_config:     域配置 dict，支持以下 key：
                                 funnel_pairs      list G1 漏斗对 [(上游uv, 下游uv), ...]
                                                       每对为 key 名称，从 facts 中查找
                                 critical_metrics  list G3 关键指标 key 名列表
                                 required_components list G4 必须存在的组件 ID 列表
            component_outputs: ComponentOutput 列表（dataclass 或 dict 皆可），用于 G4
            _retry_count:      内部重试计数（由调用方递增传入）
        """
        checks: list[CheckItem] = []

        # G1：漏斗自洽
        checks.append(self._check_g1(component_outputs or [], domain_config))

        # G2：率值合理
        checks.append(self._check_g2(component_outputs or []))

        # G3：非零校验
        checks.append(self._check_g3(component_outputs or [], domain_config))

        # G4：组件输出完整性
        checks.append(self._check_g4(component_outputs or [], domain_config))

        return self._build_result(checks, _retry_count)

    # ---------------------------------------------------------------------------
    # 各检查项实现
    # ---------------------------------------------------------------------------

    def _check_g1(self, outputs: list, domain_config: dict) -> CheckItem:
        """G1 漏斗自洽：domain_config 中 funnel_pairs 为上下游 UV key 对列表。"""
        funnel_pairs = domain_config.get("funnel_pairs", [])
        if not funnel_pairs or not outputs:
            return CheckItem(
                id="G1",
                name="漏斗自洽",
                passed=True,
                detail="未配置漏斗对或无组件输出，跳过",
            )

        # 从所有 output_data 中收集 facts 指标
        flat: dict = {}
        for o in outputs:
            data = o.output_data if hasattr(o, "output_data") else o.get("output_data", {})
            if isinstance(data, dict):
                flat.update(data)

        violations = []
        for upstream_key, downstream_key in funnel_pairs:
            up_val = flat.get(upstream_key)
            dn_val = flat.get(downstream_key)
            if up_val is not None and dn_val is not None:
                try:
                    if float(up_val) < float(dn_val):
                        violations.append(
                            f"{upstream_key}({up_val}) < {downstream_key}({dn_val})"
                        )
                except (TypeError, ValueError):
                    pass

        passed = len(violations) == 0
        return CheckItem(
            id="G1",
            name="漏斗自洽",
            passed=passed,
            detail="漏斗顺序正常" if passed else f"漏斗倒置：{violations}",
        )

    def _check_g2(self, outputs: list) -> CheckItem:
        """G2 率值合理：rate/ratio 字段 ≤ 1.0，pct/占比 字段 ≤ 100.0。

        区分两种存储约定：
          - rate / ratio / 率：小数制（0~1.0）
          - pct / 占比：百分制（0~100.0）
        """
        violations = []
        for o in outputs:
            data = o.output_data if hasattr(o, "output_data") else o.get("output_data", {})
            if not isinstance(data, dict):
                continue
            for k, v in data.items():
                k_lower = k.lower()
                is_pct = "pct" in k_lower or "占比" in k_lower
                is_rate = any(tok in k_lower for tok in ("rate", "ratio", "率"))
                if not is_pct and not is_rate:
                    continue
                try:
                    fv = float(v)
                    # pct/占比字段按百分制校验（≤ 100.0），rate/ratio 按小数制（≤ 1.0）
                    threshold = 100.0 if is_pct else 1.0
                    if fv > threshold:
                        cid = getattr(o, "component_id", o.get("component_id", "?"))
                        violations.append(f"{cid}.{k}={fv:.4f}（阈值 {threshold}）")
                except (TypeError, ValueError):
                    pass

        passed = len(violations) == 0
        return CheckItem(
            id="G2",
            name="率值合理",
            passed=passed,
            detail="所有率值正常" if passed else f"率值超限：{violations}",
        )

    def _check_g3(self, outputs: list, domain_config: dict) -> CheckItem:
        """G3 非零校验：关键指标不能全为 0。"""
        critical_metrics = domain_config.get("critical_metrics", [])
        if not critical_metrics or not outputs:
            return CheckItem(
                id="G3",
                name="关键指标非零",
                passed=True,
                detail="未配置关键指标或无组件输出，跳过",
            )

        flat: dict = {}
        for o in outputs:
            data = o.output_data if hasattr(o, "output_data") else o.get("output_data", {})
            if isinstance(data, dict):
                flat.update(data)

        all_zero = [
            m for m in critical_metrics if flat.get(m) in (0, 0.0, None, "0", "")
        ]
        passed = len(all_zero) == 0
        return CheckItem(
            id="G3",
            name="关键指标非零",
            passed=passed,
            detail="关键指标均有效" if passed else f"以下指标为零/空：{all_zero}",
        )

    def _check_g4(self, outputs: list, domain_config: dict) -> CheckItem:
        """G4 组件输出完整性：必选组件是否都有输出。"""
        required_components = domain_config.get("required_components", [])
        if not required_components:
            return CheckItem(
                id="G4",
                name="组件输出完整性",
                passed=True,
                detail="未配置必选组件列表，跳过",
            )

        actual_ids = set()
        for o in outputs:
            cid = getattr(o, "component_id", None) or o.get("component_id") or o.get("id")
            if cid:
                actual_ids.add(cid)

        missing = [c for c in required_components if c not in actual_ids]
        passed = len(missing) == 0
        return CheckItem(
            id="G4",
            name="组件输出完整性",
            passed=passed,
            detail=f"必选组件全部输出" if passed else f"缺少组件输出：{missing}",
        )

    # ---------------------------------------------------------------------------
    # 内部工具
    # ---------------------------------------------------------------------------

    def _build_result(self, checks: list[CheckItem], retry_count: int) -> GateCheckResult:
        passed = all(c.passed for c in checks)
        report = self._render_report(checks, passed)
        return GateCheckResult(
            passed=passed,
            checks=checks,
            report_text=report,
            retry_count=retry_count,
        )

    def _render_report(self, checks: list[CheckItem], passed: bool) -> str:
        lines = [
            "━━━ Gate Check 报告 ━━━",
            f"整体状态：{'✅ 通过' if passed else '❌ 未通过'}",
            "",
        ]
        for c in checks:
            icon = "✅" if c.passed else "❌"
            lines.append(f"{icon} [{c.id}] {c.name}")
            lines.append(f"   {c.detail}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
