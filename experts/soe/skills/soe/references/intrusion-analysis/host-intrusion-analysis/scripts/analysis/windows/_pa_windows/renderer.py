"""Phase 5: Markdown 渲染器。

将预分析结果字典渲染为紧凑 Markdown 文本输出到 stdout。
"""

# ---------------------------------------------------------------------------
# 渲染层截断常量（控制输出体积，数据层不受影响）
# ---------------------------------------------------------------------------
_MAX_DISTRIBUTION_TOP = 5        # 分布表只展示 Top N 项


class MdRenderer:
    """将预分析结果字典渲染为紧凑 Markdown 文本。

    渲染策略:
    ┌──────────────────────────────────────────────────────────┐
    │  A. KV 列表    — 少量标量字段，每行一个 key: value       │
    │  B. MD 表格    — 记录数组 list[dict]，1 行 = 1 记录     │
    │  C. 混合       — heading 分层 + A/B 组合                 │
    │  空数据        — 直接 (无数据)，不展开空结构              │
    │  status=error  — **错误**: {msg}                          │
    └──────────────────────────────────────────────────────────┘
    """

    def __init__(self, data: dict):
        self.d = data
        self.lines: list[str] = []

    def render(self) -> str:
        """渲染完整 Markdown 文本。"""
        self._render_meta()
        self._render_summary()
        self._render_threat_score()
        self._render_brute_force()
        self._render_active_connections()
        self._render_4104_filter()
        self._render_rdp()
        self._render_usn_ransomware()
        self._render_system_info()
        # 4672 特权登录：零引用，不再渲染（数据仍在 output 中保留）
        self._render_simple_events("events_4720_account_created", "账户创建 (4720)")
        self._render_4688()
        self._render_simple_events("events_4657_registry", "注册表变更 (4657)")
        self._render_7045_service_install()
        self._render_simple_events("events_7040_service_change", "服务启动类型变更 (7040)")
        self._render_start_stop()
        self._render_simple_events("events_4103_powershell_module", "PowerShell 模块日志 (4103)")
        self._render_processes()
        self._render_iis_logs()
        self._render_startup_items()
        self._render_signature_check()
        self._render_psreadline()
        self._render_data_quality()
        self._w()
        self._w("# 预分析结束")
        return "\n".join(self.lines) + "\n"

    # --- helpers ---

    def _w(self, line: str = ""):
        """写入一行。"""
        self.lines.append(line)

    @staticmethod
    def _esc(val) -> str:
        """转义 MD 表格单元格中的特殊字符。"""
        s = str(val) if val is not None else ""
        return s.replace("|", "\\|").replace("\n", " ").replace("\r", "")

    def _table(self, records: list[dict], columns: list[str] | None = None):
        """渲染 MD 表格。columns 为 None 时自动从第一条记录取键。"""
        if not records:
            self._w("(无数据)")
            return
        if columns is None:
            columns = list(records[0].keys())
        # header
        self._w("| " + " | ".join(columns) + " |")
        self._w("| " + " | ".join(["---"] * len(columns)) + " |")
        for rec in records:
            vals = [self._esc(rec.get(c, "")) for c in columns]
            self._w("| " + " | ".join(vals) + " |")

    def _section_status(self, key: str) -> str | None:
        """检查模块 status，返回 None 表示正常，否则返回跳过原因文本。"""
        data = self.d.get(key)
        if data is None:
            return "(段落缺失)"
        if isinstance(data, dict):
            st = data.get("status", "ok")
            if st == "not_found":
                return "(段落缺失)"
            if st == "error":
                return f"**错误**: {data.get('error', '未知')}"
        return None

    # --- 各模块渲染 ---

    def _render_top_distribution(
        self, dist: dict, key_col: str, val_col: str,
    ):
        """渲染分布表格，只展示 Top N 项，其余聚合为「其他」。"""
        sorted_items = sorted(dist.items(), key=lambda x: x[1], reverse=True)
        top = sorted_items[:_MAX_DISTRIBUTION_TOP]
        rest = sorted_items[_MAX_DISTRIBUTION_TOP:]
        rows = [{key_col: k, val_col: v} for k, v in top]
        if rest:
            rest_total = sum(v for _, v in rest)
            rows.append({key_col: f"(其他 {len(rest)} 项)", val_col: rest_total})
        self._table(rows, [key_col, val_col])

    def _render_meta(self):
        m = self.d.get("meta", {})
        self._w("# 预分析报告")
        self._w()
        # 统一头部元数据格式（与 Linux 对齐）
        self._w(
            f"platform: Windows | "
            f"template: templates/analysis_report_template.md | "
            f"preanalyze_version: {m.get('script_version', '?')} | "
            f"host: {m.get('hostname', '?')}"
        )
        self._w(
            f"log: {m.get('log_file', '?')} | "
            f"采集: {m.get('collection_time', '?')} | "
            f"分析: {m.get('analysis_time', '?')} | "
            f"原始: {m.get('total_lines', '?')} 行 | "
            f"耗时: {m.get('analysis_elapsed_seconds', '?')}s"
        )

    def _render_summary(self):
        self._w()
        self._w("## 摘要")
        for line in self.d.get("summary", []):
            self._w(f"- {line}")

    def _render_threat_score(self):
        """渲染威胁评分表格（预分析自动计算）。"""
        self._w()
        self._w("## 威胁评分（预分析自动计算）")
        ts = self.d.get("threat_score")
        if not ts:
            self._w("(未计算)")
            return
        self._w()
        self._w(f"**{ts['risk_label']}** — 最终得分: **{ts['final_score']}/100**")
        self._w()
        self._w("| 维度 | 满分 | 得分 | 触发条件 |")
        self._w("| --- | --- | --- | --- |")
        for dim in ts.get("dimensions", []):
            triggers = "; ".join(dim["triggers"]) if dim["triggers"] else "—"
            self._w(
                f"| {dim['id']}. {dim['name']} | {dim['max']} "
                f"| {dim['score']} | {self._esc(triggers)} |"
            )
        self._w(
            f"| **原始总计** | **100** | **{ts['raw_total']}** | |"
        )
        # 压倒性规则
        for rule in ts.get("override_rules", []):
            status = "✅ 触发" if rule["applied"] else "—"
            self._w(
                f"| **{self._esc(rule['rule'])}** | — "
                f"| {status} | 下限={rule['floor']} |"
            )
        self._w(
            f"| **最终得分** | **100** | **{ts['final_score']}** "
            f"| {ts['risk_label']} |"
        )
        self._w()
        self._w(
            "> ⚠️ 此评分由预分析脚本自动计算，基于确定性数据指标。"
            "AI 分析师可在「风险评估结论」中补充定性判断。"
        )

    def _render_brute_force(self):
        self._w()
        self._w("## 暴力破解交叉验证")
        skip = self._section_status("brute_force_cross_check")
        if skip:
            self._w(skip)
            return
        bf = self.d["brute_force_cross_check"]
        self._w(f"攻击IP: {bf['total_attack_ips']} | 总尝试: {bf['total_attempts']}")
        ips = bf.get("attack_ips", [])
        if not ips:
            self._w("(无攻击记录)")
            return
        self._w()
        self._table(ips, [
            "ip", "attempts", "first_attempt", "last_attempt",
            "target_usernames", "found_in_4624", "login_count",
        ])

    def _render_active_connections(self):
        self._w()
        self._w("## 活跃连接交叉验证")
        skip = self._section_status("active_connection_cross_check")
        if skip:
            self._w(skip)
            return
        ac = self.d["active_connection_cross_check"]
        sm = ac.get("summary", {})
        self._w(
            f"总连接: {ac.get('total_connections', 0)} | "
            f"外部Established: {sm.get('total_external_established', 0)} | "
            f"关联暴力破解: {sm.get('linked_to_bruteforce', 0)} | "
            f"关联成功登录: {sm.get('linked_to_success_login', 0)}"
        )
        ext = ac.get("external_established", [])
        if ext:
            self._w()
            self._table(ext, [
                "remote_ip", "remote_port", "local_port", "process_id",
                "creation_time", "threat_level",
            ])

    def _render_4104_filter(self):
        self._w()
        self._w("## PowerShell 4104 过滤")
        skip = self._section_status("powershell_4104_filter")
        if skip:
            self._w(skip)
            return
        ps = self.d["powershell_4104_filter"]
        total_susp = ps.get("remaining_suspicious_total", len(ps.get("remaining_suspicious", [])))
        fs = ps.get("filter_stats", {})
        self._w(
            f"总计: {ps['total']} | "
            f"过滤系统: {ps['filtered_system']} "
            f"(路径白名单: {fs.get('by_path_whitelist', 0)}, "
            f"内容特征: {fs.get('by_content_pattern', 0)}) | "
            f"可疑: {total_susp}"
        )
        # 仅输出高风险可疑项（含 Invoke-Expression/EncodedCommand/DownloadString 等），
        # 不再输出完整的可疑脚本块表格以节省输出空间
        high_risk = ps.get("high_risk_suspicious", [])
        if high_risk:
            self._w()
            self._w(f"### 高风险可疑项 ({len(high_risk)})")
            self._table(high_risk, ["row_num", "time", "path", "snippet"])

    def _render_rdp(self):
        self._w()
        self._w("## RDP 交叉验证")
        skip = self._section_status("rdp_cross_check")
        if skip:
            self._w(skip)
            return
        rdp = self.d["rdp_cross_check"]
        ips = rdp.get("rdp_ips", [])
        if not ips:
            self._w("(无 RDP 相关 IP)")
            return
        self._w(f"相关IP: {len(ips)}")
        for ip_info in ips:
            self._w()
            self._w(
                f"### {ip_info['ip']} ({ip_info.get('ip_type', '?')}) "
                f"— 证据源: {ip_info.get('evidence_sources', 0)} "
                f"({ip_info.get('completeness', '?')})"
            )
            ev = ip_info.get("evidence", {})
            for ev_key, ev_label in [
                ("4624_type10", "4624 Type10 RDP登录"),
                ("4624_type7", "4624 Type7 解锁"),
                ("1149", "1149 RDP连接"),
                ("21_25", "21/25 RDP会话"),
                ("tcp_3389", "TCP 3389"),
            ]:
                items = ev.get(ev_key, [])
                if items:
                    self._w(f"- **{ev_label}** ({len(items)}条):")
                    for item in items[:5]:
                        parts = [f"{k}={v}" for k, v in item.items() if v]
                        self._w(f"  - {', '.join(parts)}")
                    if len(items) > 5:
                        self._w(f"  - ...及另外 {len(items)-5} 条")
        # 空 IP 事件
        empty = rdp.get("events_with_empty_ip")
        if empty:
            has_data = any(empty.get(k) for k in ("1149", "21_25"))
            if has_data:
                self._w()
                self._w("### IP为空的事件")
                for k in ("1149", "21_25"):
                    items = empty.get(k, [])
                    if items:
                        self._w(f"- {k}: {len(items)} 条")

    def _render_usn_ransomware(self):
        self._w()
        self._w("## USN 勒索特征扫描")
        skip = self._section_status("usn_ransomware_scan")
        if skip:
            self._w(skip)
            return
        usn = self.d["usn_ransomware_scan"]
        ri = usn.get("risk_indicators", {})
        self._w(f"USN记录: {usn['total_usn_records']} | 风险评分: **{ri.get('risk_score', 0)}/100**")
        self._w(
            f"加密文件: {usn['encrypted_files']['count']} | "
            f"勒索信: {usn['ransom_notes']['count']} | "
            f"Defender变更: {usn['defender_changes']['count']}"
        )
        flags = []
        for k, label in [
            ("has_ransomware_extensions", "勒索后缀"),
            ("has_ransom_notes", "勒索信"),
            ("has_mass_encryption", "大量加密(≥10)"),
            ("has_defender_changes", "Defender变更"),
            ("encryption_in_short_window", "短窗口集中加密"),
        ]:
            if ri.get(k):
                flags.append(f"**{label}**")
        if flags:
            self._w(f"触发指标: {' / '.join(flags)}")
        tw = usn.get("time_window", {})
        if tw.get("earliest"):
            self._w(f"时间窗口: {tw['earliest']} ~ {tw['latest']} ({tw.get('duration_seconds', '?')}s)")
        ext_dist = usn["encrypted_files"].get("extension_distribution", {})
        if ext_dist:
            self._w()
            self._w("### 加密后缀分布")
            self._render_top_distribution(ext_dist, "后缀", "数量")
        orig_dist = usn["encrypted_files"].get("original_extension_distribution", {})
        if orig_dist:
            self._w()
            self._w("### 被加密前原始后缀分布")
            self._render_top_distribution(orig_dist, "后缀", "数量")
        path_dist = usn.get("path_distribution", {})
        if path_dist:
            self._w()
            self._w("### 路径分布")
            self._render_top_distribution(path_dist, "目录", "数量")
        # 加密文件样本表格已移除 — 后缀分布 + 路径分布已覆盖报告需求
        notes = usn["ransom_notes"].get("by_name", {})
        if notes:
            self._w()
            self._w("### 勒索信详情")
            for fname, info in notes.items():
                paths_str = ", ".join(info.get("sample_paths", [])[:3])
                tr = info.get("time_range", {})
                self._w(
                    f"- **{fname}** × {info['count']} "
                    f"({tr.get('earliest', '?')} ~ {tr.get('latest', '?')}) "
                    f"路径: {paths_str}"
                )
        defender = usn.get("defender_changes", {})
        if defender.get("count", 0) > 0:
            self._w()
            self._w("### Defender 变更")
            self._table(defender.get("files", []), ["name", "path", "time"])

    def _render_system_info(self):
        self._w()
        self._w("## 系统画像")
        skip = self._section_status("system_info")
        if skip:
            self._w(skip)
            return
        si = self.d["system_info"]
        sinfo = si.get("systeminfo")
        if sinfo:
            self._w()
            self._w("### 系统信息")
            for k, v in sinfo.items():
                self._w(f"- {k}: {v}")
        hygiene = si.get("security_hygiene")
        if hygiene:
            self._w()
            self._w("### 安全卫生")
            for k, v in hygiene.items():
                if k == "Firewall_Profiles" and isinstance(v, list):
                    self._w(f"- {k}:")
                    if v:
                        for fw in v:
                            self._w(f"  - {fw.get('Name', '?')}: Enabled={fw.get('Enabled', '?')}")
                    else:
                        self._w("  - (无数据)")
                else:
                    self._w(f"- {k}: {v}")
        # users / administrators / smb_shares / whoami: 不再渲染（报告未引用）

    def _render_simple_events(self, key: str, title: str):
        """渲染简单事件表格模块。"""
        self._w()
        self._w(f"## {title}")
        skip = self._section_status(key)
        if skip:
            self._w(skip)
            return
        data = self.d[key]
        records = data.get("records", [])
        if not records:
            self._w("(无数据)")
            return
        self._table(records)

    def _render_7045_service_install(self):
        """渲染服务安装 (7045)，去重同名服务并限制条数。"""
        _MAX_7045_SERVICE_INSTALL = 10
        self._w()
        self._w("## 服务安装 (7045)")
        skip = self._section_status("events_7045_service_install")
        if skip:
            self._w(skip)
            return
        data = self.d["events_7045_service_install"]
        records = data.get("records", [])
        if not records:
            self._w("(无数据)")
            return
        # 同名服务去重：只保留最后一条（时间最新的）
        seen: dict[str, dict] = {}
        for rec in records:
            name = rec.get("ServiceName", rec.get("service_name", ""))
            seen[name] = rec  # 后出现的覆盖前面的
        deduped = list(seen.values())
        total = len(records)
        dedup_count = total - len(deduped)
        # 限制条数
        top = deduped[:_MAX_7045_SERVICE_INSTALL]
        self._table(top)
        notes = []
        if dedup_count > 0:
            notes.append(f"去重 {dedup_count} 条同名服务")
        if len(deduped) > _MAX_7045_SERVICE_INSTALL:
            notes.append(f"省略 {len(deduped) - _MAX_7045_SERVICE_INSTALL} 条")
        if notes:
            self._w(f"({', '.join(notes)})")

    def _render_4688(self):
        self._w()
        self._w("## 进程创建 (4688)")
        skip = self._section_status("events_4688_process_creation")
        if skip:
            self._w(skip)
            return
        data = self.d["events_4688_process_creation"]
        non_boot = data.get("non_boot_processes", [])
        if non_boot:
            # 仅在有非启动进程（可疑）时才输出详情
            self._w(f"原始记录: {data.get('total_raw_records', 0)}")
            self._w()
            self._w("### 非启动进程")
            self._table(non_boot)
        else:
            # 无异常：一行摘要，不展示启动周期详情
            total = data.get("total_raw_records", 0)
            bc_count = data.get("boot_cycles", {}).get("count", 0)
            self._w(f"原始记录: {total} / 均为启动进程({bc_count}个周期) / 无异常")

    def _render_start_stop(self):
        self._w()
        self._w("## 系统启停")
        skip = self._section_status("events_system_start_stop")
        if skip:
            self._w(skip)
            return
        data = self.d["events_system_start_stop"]
        summary = data.get("summary", "")
        if summary:
            self._w(summary)
        timeline = data.get("timeline", [])
        if timeline:
            self._table(timeline, ["event", "time"])

    def _render_processes(self):
        self._w()
        self._w("## 进程快照")
        skip = self._section_status("processes")
        if skip:
            self._w(skip)
            return
        proc = self.d["processes"]
        total = proc.get("total", 0)
        svchost = proc.get("svchost_count", 0)
        filtered = proc.get("filtered_standard_count", 0)
        non_std = proc.get("non_standard", [])
        self._w(
            f"总计: {total} | svchost: {svchost} | "
            f"标准系统进程已过滤: {filtered} | "
            f"非标准: {len(non_std)}"
        )
        if non_std:
            self._w()
            self._w("### 非标准进程")
            self._table(non_std)

    def _render_iis_logs(self):
        self._w()
        self._w("## IIS 日志")
        skip = self._section_status("iis_logs")
        if skip:
            self._w(skip)
            return
        iis = self.d["iis_logs"]
        parts = []
        if iis.get("log_path"):
            parts.append(f"路径: {iis['log_path']}")
        if iis.get("log_size"):
            parts.append(f"大小: {iis['log_size']}")
        if iis.get("log_last_write"):
            parts.append(f"最后写入: {iis['log_last_write']}")
        parts.append(f"总请求: {iis.get('total_entries', 0)}")
        self._w(" | ".join(parts))
        if iis.get("raw_content"):
            self._w()
            self._w("```")
            self._w(iis["raw_content"])
            self._w("```")
            return
        ip_sum = iis.get("ip_summary", [])
        if ip_sum:
            self._w()
            # 只输出有攻击行为的 IP 或 Top 5（按请求数降序）
            attack_ips = [ip for ip in ip_sum if ip.get("attack_patterns")]
            non_attack_ips = [ip for ip in ip_sum if not ip.get("attack_patterns")]

            display_ips = attack_ips  # 所有攻击 IP 都输出
            # 非攻击 IP 只取 Top 5（若攻击 IP 不足 5 个则补充）
            remaining_slots = max(0, 5 - len(attack_ips))
            display_ips += non_attack_ips[:remaining_slots]
            omitted = len(ip_sum) - len(display_ips)

            rows = []
            for ip in display_ips:
                rows.append({
                    "ip": ip["ip"],
                    "count": ip["count"],
                    "first_seen": ip.get("first_seen", ""),
                    "last_seen": ip.get("last_seen", ""),
                    "ports": ",".join(str(p) for p in ip.get("target_ports", [])),
                    "status_codes": " ".join(
                        f"{k}:{v}" for k, v in ip.get("status_codes", {}).items()
                    ),
                    "attacks": ",".join(ip.get("attack_patterns", [])),
                    "samples": " | ".join(ip.get("samples", [])),
                })
            self._table(rows, [
                "ip", "count", "first_seen", "last_seen",
                "ports", "status_codes", "attacks", "samples",
            ])
            if omitted > 0:
                other_count = sum(ip["count"] for ip in non_attack_ips[remaining_slots:])
                self._w(f"其余 {omitted} 个 IP 共 {other_count} 次请求（无攻击特征）")

    def _render_startup_items(self):
        self._w()
        self._w("## 启动项")
        skip = self._section_status("startup_items")
        if skip:
            self._w(skip)
            return
        si = self.d["startup_items"]

        # WMI 启动命令（仅非标准项）
        wmi = si.get("wmi_startup_commands")
        if wmi is not None:
            wmi_filtered = si.get("wmi_filtered_standard_count", 0)
            self._w()
            self._w(f"### WMI 启动命令 (非标准: {len(wmi)}, 已过滤标准: {wmi_filtered})")
            if wmi:
                self._table(wmi)
            else:
                self._w("(均为标准项)")

        # 自动启动服务（仅非标准项 + 总数摘要）
        svcs = si.get("auto_start_services")
        if svcs is not None:
            total = si.get("auto_start_services_total", 0)
            filtered = si.get("auto_start_services_filtered", 0)
            self._w()
            self._w(f"### 自动启动服务 (总计: {total}, 非标准: {len(svcs)}, 已过滤标准: {filtered})")
            if svcs:
                self._w(", ".join(svcs))
            else:
                self._w("(均为标准服务)")

        # 注册表启动项（仅非标准项）
        reg = si.get("registry_startup")
        if reg is not None:
            reg_filtered = si.get("registry_filtered_standard_count", 0)
            self._w()
            self._w(f"### 注册表启动项 (非标准: {len(reg)}, 已过滤标准: {reg_filtered})")
            if reg:
                self._table(reg)
            else:
                self._w("(均为标准配置)")

        # 浏览器扩展已砍掉

        # 计划任务
        sched = si.get("scheduled_tasks")
        if sched is not None:
            self._w()
            self._w("### 计划任务")
            non_std = sched.get("non_standard", [])
            filtered = sched.get("filtered_standard_count", 0)
            self._w(f"非标准: {len(non_std)} | 已过滤标准任务: {filtered}")
            if non_std:
                self._table(non_std)

    def _render_signature_check(self):
        """签名校验：仅当存在异常签名时输出详情，全部正常只输出一行摘要。"""
        self._w()
        self._w("## 签名校验")
        skip = self._section_status("check_signature")
        if skip:
            self._w(skip)
            return
        data = self.d["check_signature"]
        records = data.get("records", [])
        if not records:
            self._w("(无数据)")
            return
        # 筛选异常签名（非 Valid / 非 NotSigned）
        abnormal = [
            r for r in records
            if r.get("Status", "").strip() not in ("Valid", "NotSigned", "")
        ]
        if abnormal:
            self._w(f"共 {len(records)} 文件，**{len(abnormal)} 个异常**：")
            self._table(abnormal)
        else:
            self._w(f"{len(records)} 文件 / 均正常")

    def _render_psreadline(self):
        self._w()
        self._w("## 命令历史 (PSReadLine)")
        skip = self._section_status("psreadline_history")
        if skip:
            self._w(skip)
            return
        ps = self.d["psreadline_history"]
        raw_count = ps.get("raw_count", ps.get("total_lines", 0))
        cmds = ps.get("commands", [])
        self._w(
            f"用户: {ps.get('user', '?')} | "
            f"原始行数: {raw_count} | 去重后: {len(cmds)}"
        )
        if cmds:
            self._w()
            for cmd in cmds:
                self._w(cmd)

    def _render_data_quality(self):
        warnings = self.d.get("data_quality_warnings", [])
        if not warnings:
            return
        self._w()
        self._w("## 数据质量告警")
        self._table(warnings, ["severity", "source", "value", "expected", "note"])
