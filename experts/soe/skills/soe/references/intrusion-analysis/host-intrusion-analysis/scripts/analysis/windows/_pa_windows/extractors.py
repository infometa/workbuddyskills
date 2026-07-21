"""Phase 2.5: ExtractorMixin — 15 个数据精简提取方法 + 质量校验 + 摘要构建。

以 Mixin 类形式提供，由 PreAnalyzer 继承使用。
方法通过 self.lines / self.sections / self.meta 访问日志数据。
"""

import re
import sys
from collections import defaultdict
from datetime import datetime

from .constants import (
    AUTO_START_SERVICE_WHITELIST_LOWER,
    BOOT_CYCLE_THRESHOLD_SEC,
    BOOT_PROCESS_WHITELIST,
    IIS_ATTACK_PATTERNS,
    PROCESS_WHITELIST,
    RE_KV,
    RE_SECTION,
    RE_SUB,
    RE_WHOAMI_TABLE_SEP,
    REGISTRY_STARTUP_WHITELIST,
    SECURITY_HYGIENE_DROP_FIELDS,
    SUB_AUTO_START_SERVICES,
    SUB_BROWSER_EXTENSIONS,
    SUB_REGISTRY_STARTUP,
    SUB_SCHEDULED_TASKS,
    SUB_WMI_STARTUP,
    WMI_STARTUP_WHITELIST_COMMANDS,
)
from .parsers import (
    parse_table_row_wide,
    extract_event_data,
    extract_kv_data,
    parse_fixed_width_columns,
    parse_fixed_width_table,
    parse_table_row,
)


class ExtractorMixin:
    """Phase 2.5 数据精简提取方法集合（Mixin）。

    依赖宿主类提供:
      self.lines: list[str]
      self.sections: list[SectionIndex]
      self.meta: dict
    """

    # ------------------------------------------------------------------
    # Phase 2.5: Data Condensation Methods (v1.5.0)
    # ------------------------------------------------------------------
    # 【架构约束 (D4)】Phase 2.5 只读取新的数据段，不读取或修改
    # Phase 2 已提取的变量（events_4624/4625/4104/1149/21_25/tcp/usn）。
    # Phase 3 的交叉分析依赖 Phase 2 的变量，Phase 2.5 修改会影响结果。
    # ------------------------------------------------------------------

    def _sub_exists(self, sub_name: str) -> bool:
        """检查指定 SUB/EVENTS/SECTION 是否存在于日志结构中。

        同时搜索子章节（SUB/EVENTS/CATEGORY）和顶层 SECTION，
        与 extract_event_data() 的搜索范围一致。
        """
        for sec in self.sections:
            for sub in sec.subsections:
                if sub["name"] == sub_name:
                    return True
            if sec.name == sub_name:
                return True
        return False

    def _extract_simple_events(
        self, sub_name: str, drop_cols: list[str] | None = None
    ) -> dict:
        """通用事件表格提取。返回带 status 的结构。

        同时支持 SUB/EVENTS 子章节和顶层 SECTION（如 CheckSignature）。
        (D1) 不需要 section 参数，extract_event_data() 已同时搜索两者。
        """
        try:
            sub_exists = self._sub_exists(sub_name)
            if not sub_exists:
                return {"status": "not_found", "records": []}
            records = extract_event_data(self.lines, self.sections, sub_name)
            if drop_cols:
                for rec in records:
                    for col in drop_cols:
                        rec.pop(col, None)  # 容错去列 (B4)
            return {"status": "ok", "records": records}
        except Exception as e:
            return {"status": "error", "error": str(e), "records": []}

    # --- 模块 1: system_info — 系统画像 ---

    def _extract_system_info(self) -> dict:
        """提取 SystemInfo 段 6 个异构子段，按子段名分别处理 (B1)。

        子段级容错：缺失子段标记为 null，已成功子段正常输出。
        """
        result = {"status": "ok"}

        # --- whoami: 不再提取（报告未引用组成员信息和 SID）---
        result["whoami_groups"] = None

        # --- systeminfo (KV) ---
        # 报告实际只使用 OSName，其余字段（版本号/安装日期/内存/厂商型号）
        # 均未被引用，删除以节省输出空间
        _SYSTEMINFO_DROP_FIELDS = {
            "OSVersion", "InstallDate", "TotalMemoryGB",
            "Manufacturer", "Model",
        }
        try:
            if self._sub_exists("systeminfo"):
                kv = extract_kv_data(self.lines, self.sections, "systeminfo")
                for field in _SYSTEMINFO_DROP_FIELDS:
                    kv.pop(field, None)
                result["systeminfo"] = kv if kv else None
            else:
                result["systeminfo"] = None
        except Exception as e:
            print(f"[WARN] systeminfo 提取失败: {e}", file=sys.stderr)
            result["systeminfo"] = None

        # --- security_hygiene (KV + 嵌套 Firewall_Profiles 子表格) ---
        try:
            if self._sub_exists("security_hygiene"):
                kv = extract_kv_data(self.lines, self.sections, "security_hygiene")
                # 删除诊断字段
                for field_name in SECURITY_HYGIENE_DROP_FIELDS:
                    kv.pop(field_name, None)
                if "Firewall_Profiles_data" in kv:
                    fw_data = kv.pop("Firewall_Profiles_data")
                    for r in fw_data:
                        r.pop("#", None)
                    valid_fw_names = {"Domain", "Private", "Public"}
                    fw_data = [
                        r for r in fw_data if r.get("Name") in valid_fw_names
                    ]
                    kv["Firewall_Profiles"] = fw_data
                elif "Firewall_Profiles" in kv:
                    kv["Firewall_Profiles"] = []
                if "Firewall_AllEnabled" not in kv or "Firewall_AnyDisabled" not in kv:
                    raw_text = self._get_sub_raw_text("security_hygiene")
                    for line in raw_text.splitlines():
                        m = RE_KV.match(line)
                        if m:
                            key = m.group(2)
                            if key == "Firewall_AllEnabled" and key not in kv:
                                kv[key] = m.group(3).strip()
                            elif key == "Firewall_AnyDisabled" and key not in kv:
                                kv[key] = m.group(3).strip()
                result["security_hygiene"] = kv if kv else None
            else:
                result["security_hygiene"] = None
        except Exception as e:
            print(f"[WARN] security_hygiene 提取失败: {e}", file=sys.stderr)
            result["security_hygiene"] = None

        # --- users: 不再提取（报告未引用用户列表，暴力破解表中的 target_usernames 是独立数据）---
        result["users"] = None

        # --- smb_share: 不再提取（报告未引用 SMB 共享信息）---
        result["smb_shares"] = None

        # --- administrators: 不再提取（报告未引用管理员列表）---
        result["administrators"] = None

        # 如果全部子段都是 None，标记为 not_found
        data_keys = [
            "whoami_groups", "systeminfo", "security_hygiene",
            "users", "smb_shares", "administrators",
        ]
        if all(result.get(k) is None for k in data_keys):
            result["status"] = "not_found"

        return result

    def _extract_text_list(
        self, sub_name: str, pattern: str | None
    ) -> list[str]:
        """从子段中提取纯文本行列表。

        pattern 非空时用正则提取 group(1)，None 时直接按行读取非空文本。
        """
        text = self._get_sub_raw_text(sub_name)
        items = []
        regex = re.compile(pattern) if pattern else None
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if regex:
                m = regex.match(stripped)
                if m:
                    items.append(m.group(1).strip())
            else:
                items.append(stripped)
        return items

    def _get_sub_raw_text(self, sub_name: str) -> str:
        """获取指定子段的原始文本内容。"""
        for sec in self.sections:
            for sub in sec.subsections:
                if sub["name"] == sub_name:
                    start = sub["start_line"]  # 1-based → 0-based 跳过标记行
                    end = sub["end_line"]  # 1-based inclusive
                    return "\n".join(self.lines[start:end])
        return ""

    def _parse_whoami_table(self) -> list[dict]:
        """解析 whoami 子段的 = 分隔符表格 (E9)。

        whoami 格式:
            GROUP INFORMATION
            -----------------
            (空行)
            Group Name  Type  SID  Attributes
            ==========  ====  ===  ==========
            data...

        【P0 修复】中文宽字符使用 Unicode 显示宽度感知的列解析。
        """
        for sec in self.sections:
            for sub in sec.subsections:
                if sub["name"] == "whoami":
                    start = sub["start_line"]  # 1-based
                    end = sub["end_line"]

                    # 在子段范围内找 = 分隔行
                    for i in range(start, min(end, len(self.lines))):
                        if RE_WHOAMI_TABLE_SEP.match(self.lines[i]):
                            header_idx = i - 1
                            if header_idx < start:
                                return []

                            sep_line = self.lines[i]
                            display_cols = parse_fixed_width_columns(sep_line)
                            if not display_cols:
                                return []

                            headers = parse_table_row(
                                self.lines[header_idx], display_cols
                            )

                            records = []
                            j = i + 1
                            while j < min(end, len(self.lines)):
                                line = self.lines[j]
                                stripped = line.strip()
                                if stripped == "":
                                    j += 1
                                    break
                                if RE_SECTION.match(stripped) or RE_SUB.match(stripped):
                                    break
                                values = parse_table_row_wide(line, display_cols)
                                record = {}
                                for h, v in zip(headers, values):
                                    if h:
                                        record[h] = v
                                if any(v for v in record.values()):
                                    records.append(record)
                                j += 1
                            return records
        return []

    # --- 模块 4: events_4688_process_creation — 进程创建 ---

    def _extract_4688_process_creation(self) -> dict:
        """4688 进程创建：启动周期去重 + 仅保留非启动进程。

        白名单匹配同时检查全名和去 .exe 后缀 (C7)。
        时间解析容错：失败时保守归入 non_boot_processes。
        """
        try:
            if not self._sub_exists("process_creation_4688"):
                return {"status": "not_found", "total_raw_records": 0,
                        "boot_cycles": {"count": 0, "unique_processes": [], "cycles": []},
                        "non_boot_processes": []}

            records = extract_event_data(
                self.lines, self.sections, "process_creation_4688"
            )
            if not records:
                return {"status": "ok", "total_raw_records": 0,
                        "boot_cycles": {"count": 0, "unique_processes": [], "cycles": []},
                        "non_boot_processes": []}

            boot_records: list[tuple[datetime, dict]] = []
            non_boot: list[dict] = []

            for rec in records:
                rec.pop("#", None)
                proc_path = rec.get("NewProcessName", "")
                fname = proc_path.rsplit("\\", 1)[-1] if "\\" in proc_path else proc_path
                fname_lower = fname.lower()
                fname_no_ext = fname_lower.rsplit(".", 1)[0] if "." in fname_lower else fname_lower

                is_boot = (
                    fname_lower in BOOT_PROCESS_WHITELIST
                    or fname_no_ext in BOOT_PROCESS_WHITELIST
                )

                if is_boot:
                    ts = self._parse_time_safe(rec.get("TimeCreated", ""))
                    if ts:
                        boot_records.append((ts, rec))
                    else:
                        rec["_time_parse_error"] = True
                        non_boot.append(rec)
                else:
                    non_boot.append(rec)

            # 聚类为启动周期（相邻记录时间差 <30s）
            boot_records.sort(key=lambda x: x[0])
            cycles: list[dict] = []
            current_cycle: list[tuple[datetime, dict]] = []

            for ts, rec in boot_records:
                if current_cycle and (ts - current_cycle[-1][0]).total_seconds() > BOOT_CYCLE_THRESHOLD_SEC:
                    cycles.append(self._summarize_boot_cycle(current_cycle))
                    current_cycle = []
                current_cycle.append((ts, rec))

            if current_cycle:
                cycles.append(self._summarize_boot_cycle(current_cycle))

            unique_procs = set()
            for ts, rec in boot_records:
                proc_path = rec.get("NewProcessName", "")
                fname = proc_path.rsplit("\\", 1)[-1] if "\\" in proc_path else proc_path
                unique_procs.add(fname)

            return {
                "status": "ok",
                "total_raw_records": len(records),
                "boot_cycles": {
                    "count": len(cycles),
                    "unique_processes": sorted(unique_procs),
                    "cycles": cycles,
                },
                "non_boot_processes": non_boot,
            }
        except Exception as e:
            return {"status": "error", "error": str(e),
                    "total_raw_records": 0, "boot_cycles": {"count": 0, "unique_processes": [], "cycles": []},
                    "non_boot_processes": []}

    def _summarize_boot_cycle(
        self, cycle: list[tuple[datetime, dict]]
    ) -> dict:
        """将一组启动周期记录合并为摘要。"""
        first_ts = cycle[0][0].strftime("%Y-%m-%d %H:%M:%S")
        last_ts = cycle[-1][0].strftime("%H:%M:%S")
        return {
            "time": f"{first_ts} ~ {last_ts}",
            "records": len(cycle),
        }

    @staticmethod
    def _parse_time_safe(time_str: str) -> datetime | None:
        """安全解析时间字段，失败返回 None。"""
        if not time_str or time_str in ("(空)", "-"):
            return None
        try:
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    # --- 模块 8: events_system_start_stop — 系统启停时间线 ---

    def _extract_system_start_stop(self) -> dict:
        """系统启停事件聚合为启停周期时间线。

        EventID 语义：6005/6009→boot, 6006→shutdown, 6013→uptime_tick。
        (E11) 独立 6013 不入 timeline。(E21) Message 字段全空可丢弃。
        """
        try:
            if not self._sub_exists("system_start_stop"):
                return {"status": "not_found", "total_raw_records": 0,
                        "timeline": [], "summary": ""}

            records = extract_event_data(
                self.lines, self.sections, "system_start_stop"
            )
            if not records:
                return {"status": "ok", "total_raw_records": 0,
                        "timeline": [], "summary": "无启停事件"}

            events: list[tuple[datetime, str, str]] = []
            for rec in records:
                eid = rec.get("EventID", "")
                ts = self._parse_time_safe(rec.get("TimeCreated", ""))
                if not ts:
                    continue

                if eid in ("6005", "6009"):
                    events.append((ts, eid, "boot"))
                elif eid == "6006":
                    events.append((ts, eid, "shutdown"))
                elif eid == "6013":
                    events.append((ts, eid, "uptime_tick"))

            events.sort(key=lambda x: x[0])

            timeline: list[dict] = []
            seen_boot_times: set[str] = set()
            boot_count = 0
            shutdown_count = 0

            for ts, eid, etype in events:
                time_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                if etype == "boot":
                    if time_str not in seen_boot_times:
                        seen_boot_times.add(time_str)
                        timeline.append({"event": "boot", "time": time_str})
                        boot_count += 1
                elif etype == "shutdown":
                    timeline.append({"event": "shutdown", "time": time_str})
                    shutdown_count += 1

            last_boot = ""
            for item in reversed(timeline):
                if item["event"] == "boot":
                    last_boot = item["time"]
                    break

            summary = (
                f"{boot_count} 次启动 / {shutdown_count} 次关闭"
                + (f"，最后一次启动: {last_boot}" if last_boot else "")
            )

            return {
                "status": "ok",
                "total_raw_records": len(records),
                "timeline": timeline,
                "summary": summary,
            }
        except Exception as e:
            return {"status": "error", "error": str(e),
                    "total_raw_records": 0, "timeline": [], "summary": ""}

    # --- 模块 10: processes — 进程快照 ---

    def _extract_processes(self) -> dict:
        """进程快照：过滤 svchost 和标准系统进程，仅保留非标准/可疑进程。"""
        try:
            if not self._sub_exists("Processes"):
                return {"status": "not_found", "total": 0,
                        "svchost_count": 0, "filtered_standard_count": 0,
                        "non_standard": []}

            records = extract_event_data(
                self.lines, self.sections, "Processes"
            )
            if not records:
                return {"status": "ok", "total": 0,
                        "svchost_count": 0, "filtered_standard_count": 0,
                        "non_standard": []}

            svchost_count = 0
            filtered_standard_count = 0
            non_standard: list[dict] = []

            for rec in records:
                rec.pop("#", None)
                proc_name = rec.get("ProcessName", "")
                proc_lower = proc_name.lower()

                if proc_lower == "svchost":
                    svchost_count += 1
                    continue

                if proc_lower in PROCESS_WHITELIST:
                    filtered_standard_count += 1
                    continue

                # 非标准进程：保留
                rec.pop("PID", None)
                rec.pop("SessionId", None)
                cmd = rec.get("CommandLine", "")
                if cmd and len(cmd) > 150:
                    rec["CommandLine"] = cmd[:150] + "..."
                non_standard.append(rec)

            return {
                "status": "ok",
                "total": len(records),
                "svchost_count": svchost_count,
                "filtered_standard_count": filtered_standard_count,
                "non_standard": non_standard,
            }
        except Exception as e:
            return {"status": "error", "error": str(e),
                    "total": 0, "svchost_count": 0,
                    "filtered_standard_count": 0, "non_standard": []}

    # --- 模块 11: network_config — 网络配置 ---

    def _extract_network_config(self) -> dict:
        """网络配置：ipconfig/route/arp 三个标准表格 + 过滤噪声。"""
        try:
            has_any = any(
                self._sub_exists(s) for s in ("ipconfig", "route", "arp")
            )
            if not has_any:
                return {"status": "not_found", "ipconfig": [], "route": [], "arp": []}

            result: dict = {"status": "ok"}

            ipconfig_recs = extract_event_data(
                self.lines, self.sections, "ipconfig"
            )
            for r in ipconfig_recs:
                r.pop("#", None)
            result["ipconfig"] = ipconfig_recs

            local_ips = set()
            for r in ipconfig_recs:
                ip = r.get("IPAddress", "")
                if ip:
                    local_ips.add(ip)

            route_recs = extract_event_data(
                self.lines, self.sections, "route"
            )
            filtered_route = []
            for r in route_recs:
                r.pop("#", None)
                alias = r.get("InterfaceAlias", "")
                dest = r.get("DestinationPrefix", "")

                if "Loopback" in alias:
                    continue
                skip = False
                for lip in local_ips:
                    if dest == f"{lip}/32":
                        skip = True
                        break
                if skip:
                    continue
                filtered_route.append(r)
            result["route"] = filtered_route

            arp_recs = extract_event_data(
                self.lines, self.sections, "arp"
            )
            filtered_arp = []
            for r in arp_recs:
                r.pop("#", None)
                state = r.get("State", "")
                ip_addr = r.get("IPAddress", "")

                if state == "Permanent":
                    continue
                if ip_addr == "255.255.255.255":
                    continue
                filtered_arp.append(r)
            result["arp"] = filtered_arp

            return result
        except Exception as e:
            return {"status": "error", "error": str(e),
                    "ipconfig": [], "route": [], "arp": []}

    # --- 模块 12: iis_logs — IIS 日志精简 ---

    def _extract_iis_logs(self) -> dict:
        """IIS 日志精简：按 IP 聚合 + 攻击模式分类。"""
        try:
            if not self._sub_exists("IISLogs"):
                return {"status": "not_found"}

            iis_sec = None
            for sec in self.sections:
                if sec.name == "IISLogs":
                    iis_sec = sec
                    break
            if not iis_sec:
                return {"status": "not_found"}

            content_start = iis_sec.start_line + 2
            content_end = iis_sec.end_line

            log_meta: dict = {}
            fields_line = ""
            log_entries: list[str] = []

            for i in range(content_start, min(content_end, len(self.lines))):
                line = self.lines[i].strip()
                if not line:
                    continue

                kv_match = RE_KV.match(self.lines[i])
                if kv_match:
                    key = kv_match.group(2)
                    val = kv_match.group(3).strip()
                    if key == "LogPath":
                        log_meta["log_path"] = val
                    elif key == "LogSize":
                        log_meta["log_size"] = val
                    elif key == "LogLastWriteTime":
                        log_meta["log_last_write"] = val
                    continue

                if line.startswith("#Fields:"):
                    fields_line = line
                    continue

                if line.startswith("#"):
                    continue

                log_entries.append(line)

            if not fields_line:
                raw_text = "\n".join(
                    self.lines[content_start:min(content_end, len(self.lines))]
                )
                return {
                    "status": "ok",
                    **log_meta,
                    "total_entries": len(log_entries),
                    "raw_content": raw_text,
                    "parse_note": "no #Fields: header found, raw content preserved",
                }

            field_names = fields_line.replace("#Fields:", "").strip().split()

            ip_data: dict[str, dict] = defaultdict(lambda: {
                "count": 0,
                "first_seen": "",
                "last_seen": "",
                "target_ports": set(),
                "status_codes": defaultdict(int),
                "attack_patterns": set(),
                "valid_uris": [],
            })

            for entry_line in log_entries:
                tokens = entry_line.split()
                if len(tokens) != len(field_names):
                    continue

                row = dict(zip(field_names, tokens))

                c_ip = row.get("c-ip", "-")
                time_str = f"{row.get('date', '')} {row.get('time', '')}"
                s_port = row.get("s-port", "")
                sc_status = row.get("sc-status", "-")
                cs_method = row.get("cs-method", "-")
                cs_uri = row.get("cs-uri", "-")

                bucket = ip_data[c_ip]
                bucket["count"] += 1

                if not bucket["first_seen"] or time_str < bucket["first_seen"]:
                    bucket["first_seen"] = time_str
                if not bucket["last_seen"] or time_str > bucket["last_seen"]:
                    bucket["last_seen"] = time_str

                if s_port and s_port != "-":
                    try:
                        bucket["target_ports"].add(int(s_port))
                    except ValueError:
                        pass

                if sc_status and sc_status != "-":
                    bucket["status_codes"][sc_status] += 1

                if cs_method == "-" or cs_uri == "-":
                    continue

                matched_patterns: list[str] = []
                for pattern_name, pattern_re in IIS_ATTACK_PATTERNS.items():
                    if pattern_re.search(cs_uri):
                        matched_patterns.append(pattern_name)
                        bucket["attack_patterns"].add(pattern_name)

                if len(bucket["valid_uris"]) < 200:
                    bucket["valid_uris"].append((
                        cs_uri, cs_method, sc_status, time_str, len(matched_patterns)
                    ))

            ip_summary = []
            for ip, data in sorted(ip_data.items(), key=lambda x: x[1]["count"], reverse=True):
                valid = sorted(
                    data["valid_uris"],
                    key=lambda x: (-x[4], x[3]),
                )
                samples = []
                for uri, method, status, ts, _ in valid[:3]:
                    samples.append(f"{method} {uri} → {status}")

                ip_summary.append({
                    "ip": ip,
                    "count": data["count"],
                    "first_seen": data["first_seen"],
                    "last_seen": data["last_seen"],
                    "target_ports": sorted(data["target_ports"]),
                    "status_codes": dict(data["status_codes"]),
                    "attack_patterns": sorted(data["attack_patterns"]),
                    "samples": samples,
                })

            return {
                "status": "ok",
                **log_meta,
                "total_entries": sum(d["count"] for d in ip_data.values()),
                "ip_summary": ip_summary,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # --- 模块 13: startup_items — 启动项 ---

    def _extract_startup_items(self) -> dict:
        """启动项提取：5 个中文 SUB 子段分别处理，白名单过滤标准项。"""
        try:
            has_startup = any(
                sec.name == "Startup" for sec in self.sections
            )
            if not has_startup:
                return {"status": "not_found"}

            result: dict = {"status": "ok"}

            # --- WMI 启动命令（白名单过滤标准 Windows 组件）---
            try:
                if self._sub_exists(SUB_WMI_STARTUP):
                    recs = extract_event_data(
                        self.lines, self.sections, SUB_WMI_STARTUP
                    )
                    non_standard = []
                    filtered_count = 0
                    for r in recs:
                        r.pop("#", None)
                        cmd = r.get("Command", "").strip()
                        cmd_fname = cmd.rsplit("\\", 1)[-1].lower() if cmd else ""
                        if cmd_fname in WMI_STARTUP_WHITELIST_COMMANDS:
                            filtered_count += 1
                        else:
                            non_standard.append(r)
                    result["wmi_startup_commands"] = non_standard
                    result["wmi_filtered_standard_count"] = filtered_count
                else:
                    result["wmi_startup_commands"] = None
            except Exception as e:
                print(f"[WARN] wmi_startup_commands 提取失败: {e}", file=sys.stderr)
                result["wmi_startup_commands"] = None

            # --- 自动启动服务（只保留非标准服务名）---
            try:
                if self._sub_exists(SUB_AUTO_START_SERVICES):
                    text = self._get_sub_raw_text(SUB_AUTO_START_SERVICES)
                    text_stripped = text.strip()
                    if "," in text_stripped:
                        services = [
                            s.strip() for s in text_stripped.split(",") if s.strip()
                        ]
                    else:
                        services = [
                            line.strip()
                            for line in text_stripped.splitlines()
                            if line.strip()
                        ]
                    total_count = len(services)
                    non_standard = [
                        s for s in services
                        if s.lower() not in AUTO_START_SERVICE_WHITELIST_LOWER
                    ]
                    result["auto_start_services"] = non_standard
                    result["auto_start_services_total"] = total_count
                    result["auto_start_services_filtered"] = total_count - len(non_standard)
                else:
                    result["auto_start_services"] = None
            except Exception as e:
                print(f"[WARN] auto_start_services 提取失败: {e}", file=sys.stderr)
                result["auto_start_services"] = None

            # --- 注册表启动项（白名单过滤 Windows 默认值）---
            try:
                if self._sub_exists(SUB_REGISTRY_STARTUP):
                    recs = extract_event_data(
                        self.lines, self.sections, SUB_REGISTRY_STARTUP
                    )
                    non_standard = []
                    filtered_count = 0
                    for r in recs:
                        r.pop("#", None)
                        name = r.get("Name", "").strip().lower()
                        value = r.get("Value", "").strip().lower()
                        if (name, value) in REGISTRY_STARTUP_WHITELIST:
                            filtered_count += 1
                        else:
                            non_standard.append(r)
                    result["registry_startup"] = non_standard
                    result["registry_filtered_standard_count"] = filtered_count
                else:
                    result["registry_startup"] = None
            except Exception as e:
                print(f"[WARN] registry_startup 提取失败: {e}", file=sys.stderr)
                result["registry_startup"] = None

            # --- 浏览器扩展：砍掉（IEToEdge BHO 等标准组件无安全价值）---
            result["browser_extensions"] = None

            # --- 计划任务 ---
            try:
                if self._sub_exists(SUB_SCHEDULED_TASKS):
                    recs = extract_event_data(
                        self.lines, self.sections, SUB_SCHEDULED_TASKS
                    )
                    non_standard = []
                    filtered_count = 0
                    for r in recs:
                        r.pop("#", None)
                        task_path = r.get("TaskPath", "")
                        if task_path.startswith("\\Microsoft\\Windows\\"):
                            filtered_count += 1
                        else:
                            non_standard.append(r)
                    result["scheduled_tasks"] = {
                        "non_standard": non_standard,
                        "filtered_standard_count": filtered_count,
                        "filtered_standard_prefix": "\\Microsoft\\Windows\\",
                    }
                else:
                    result["scheduled_tasks"] = None
            except Exception as e:
                print(f"[WARN] scheduled_tasks 提取失败: {e}", file=sys.stderr)
                result["scheduled_tasks"] = None

            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # --- 模块 15: psreadline_history — PowerShell 命令历史 ---

    def _extract_psreadline(self) -> dict:
        """PSReadLineHistory：KV 元数据 + [N] 命令列表（去重 + 过滤输出行）。"""
        try:
            if not self._sub_exists("PSReadLineHistory"):
                return {"status": "not_found"}

            ps_sec = None
            for sec in self.sections:
                if sec.name == "PSReadLineHistory":
                    ps_sec = sec
                    break
            if not ps_sec:
                return {"status": "not_found"}

            content_start = ps_sec.start_line + 2
            content_end = ps_sec.end_line

            user = ""
            history_path = ""
            total_lines = 0
            raw_commands: list[str] = []

            for i in range(content_start, min(content_end, len(self.lines))):
                line = self.lines[i]
                stripped = line.strip()
                if not stripped:
                    continue

                kv_match = RE_KV.match(line)
                if kv_match:
                    key = kv_match.group(2)
                    val = kv_match.group(3).strip()
                    if key == "UserName":
                        user = val
                    elif key == "HistoryPath":
                        history_path = val
                    elif key == "TotalLines":
                        try:
                            total_lines = int(val)
                        except ValueError:
                            pass
                    continue

                if re.match(r"\s*\[\d+\]", line):
                    raw_commands.append(stripped)
                    continue

                if raw_commands:
                    raw_commands.append(stripped)

            # 过滤纯输出行（非命令）+ 去重连续重复
            commands = self._deduplicate_commands(raw_commands)

            return {
                "status": "ok",
                "user": user,
                "history_path": history_path,
                "total_lines": total_lines,
                "raw_count": len(raw_commands),
                "commands": commands,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _deduplicate_commands(raw_commands: list[str]) -> list[str]:
        """过滤纯输出行 + 去重连续重复命令。

        过滤规则：
        1. 去除不以 [N] 开头的纯输出行（如 "Connection reset by ::1 port 22"）
        2. 连续重复的命令只保留一次（附加 ×N 计数）
        """
        # 第一遍：只保留 [N] 开头的实际命令行
        cmd_pattern = re.compile(r"^\[(\d+)\]\s*(.*)")
        actual_commands: list[str] = []
        for line in raw_commands:
            m = cmd_pattern.match(line)
            if m:
                actual_commands.append(m.group(0))

        # 第二遍：去重连续重复（比较命令文本部分，忽略 [N] 编号）
        deduped: list[str] = []
        prev_text = ""
        repeat_count = 0
        for cmd in actual_commands:
            m = cmd_pattern.match(cmd)
            cmd_text = m.group(2) if m else cmd
            if cmd_text == prev_text:
                repeat_count += 1
            else:
                if repeat_count > 0 and deduped:
                    deduped[-1] += f" (×{repeat_count + 1})"
                deduped.append(cmd)
                prev_text = cmd_text
                repeat_count = 0
        if repeat_count > 0 and deduped:
            deduped[-1] += f" (×{repeat_count + 1})"

        return deduped

    # ------------------------------------------------------------------
    # Phase 4.5: Data Quality Check
    # ------------------------------------------------------------------

    def _check_data_quality(self, output: dict) -> list[dict]:
        """扫描输出数据中已知时间戳字段，校验格式完整性。

        发现截断时同时：
        1. 在 warnings 中记录（供 data_quality_alerts 章节展示）
        2. 就地将截断值改为 "(truncated:<原值>)"，让 AI 读原始字段时能直接识别
        """
        RE_TIMESTAMP = re.compile(
            r"^\d{4}-\d{2}-\d{2}(?:\s\d{2}:\d{2}:\d{2})?$"
        )
        EMPTY_VALUES = {"", "(空)", "-", None}

        warnings: list[dict] = []

        checks: list[tuple[str, str, list[str], list[str]]] = [
            (
                "brute_force_cross_check", "attack_ips",
                ["first_attempt", "last_attempt"],
                ["ip"],
            ),
            (
                "events_7040_service_change", "records",
                ["FirstChange", "LastChange"],
                ["ServiceName"],
            ),
            (
                "events_7045_service_install", "records",
                ["TimeCreated"],
                ["ServiceName"],
            ),
        ]

        for output_key, records_key, ts_fields, id_fields in checks:
            data = output.get(output_key)
            if not data:
                continue

            records = data.get(records_key, []) if isinstance(data, dict) else []
            if not records:
                continue

            for idx, rec in enumerate(records):
                for ts_field in ts_fields:
                    value = rec.get(ts_field, "")
                    if value in EMPTY_VALUES:
                        continue
                    if not RE_TIMESTAMP.match(str(value)):
                        id_parts = []
                        for idf in id_fields:
                            v = rec.get(idf, "")
                            if v:
                                id_parts.append(f"{idf}={v}")
                        id_str = ", ".join(id_parts) if id_parts else f"#{idx+1}"

                        warnings.append({
                            "severity": "truncated_timestamp",
                            "source": f"{output_key}.{records_key}[{id_str}].{ts_field}",
                            "value": str(value),
                            "expected": "YYYY-MM-DD HH:MM:SS",
                            "note": (
                                "疑似 PS1 固定宽度表格列宽不足导致截断，"
                                "原始值不可用。建议回查原始日志确认完整时间戳。"
                            ),
                        })

                        # 就地标记截断值，让 AI 直接从字段中识别
                        rec[ts_field] = f"(truncated:{value})"

        return warnings

    # ------------------------------------------------------------------
    # Phase 4: Summary Builder
    # ------------------------------------------------------------------

    def _build_summary(
        self,
        events_4624, events_4625, events_4104, events_1149,
        events_21_25, network_tcp, usn_records,
        brute_force, active_conn, ps_filter, rdp,
        usn_ransomware, elapsed,
        # Phase 2.5 新数据（v1.5.0）
        system_info=None, processes=None, startup_items=None,
        iis_logs=None, psreadline=None,
        # Phase 3.5
        stealth_intruders=None, threat_score=None,
    ) -> list[str]:
        """构建精简摘要数组，每个分析步骤用一句话概括。"""
        lines = []

        lines.append(
            f"读取 {len(self.lines)} 行日志, 解析 {len(self.sections)} 个章节"
        )

        lines.append(
            f"提取: 4624={len(events_4624)} 4625={len(events_4625)} "
            f"4104={len(events_4104)} 1149={len(events_1149)} "
            f"21/25={len(events_21_25)} TCP={len(network_tcp)} "
            f"USN={len(usn_records)}"
        )

        bf = brute_force
        penetrated = sum(1 for a in bf["attack_ips"] if a["found_in_4624"])
        lines.append(
            f"暴力破解: {bf['total_attack_ips']}攻击IP / "
            f"{bf['total_attempts']}次 / {penetrated}渗透成功"
        )

        # 低噪入侵者：由 run() 预计算后传入
        if stealth_intruders is None:
            stealth_intruders = []
        if stealth_intruders:
            lines.append(
                f"⚠️ 低噪入侵者(Type10成功但不在4625): {len(stealth_intruders)}个IP → "
                + ", ".join(stealth_intruders[:5])
            )
        else:
            lines.append("低噪入侵者: 无")

        ac = active_conn["summary"]
        lines.append(
            f"活跃连接: {ac['total_external_established']}外部 / "
            f"{ac['linked_to_bruteforce']}关联暴力破解"
        )

        ps = ps_filter
        suspicious_count = ps.get("remaining_suspicious_total", len(ps["remaining_suspicious"]))
        lines.append(
            f"4104: {ps['total']}总计 → "
            f"{ps['filtered_system']}系统 + "
            f"{suspicious_count}可疑"
        )

        lines.append(f"RDP: {len(rdp['rdp_ips'])}相关IP")

        usn = usn_ransomware
        enc = usn["encrypted_files"]["count"]
        notes = usn["ransom_notes"]["count"]
        score = usn["risk_indicators"]["risk_score"]
        lines.append(
            f"USN勒索: {enc}加密 / {notes}勒索信 / 风险{score}/100"
        )

        # --- v1.5.0 新增摘要行 ---

        if system_info and system_info.get("status") == "ok":
            si = system_info.get("systeminfo") or {}
            os_name = si.get("OSName", "未知")
            hygiene = system_info.get("security_hygiene") or {}
            fw_all = hygiene.get("Firewall_AllEnabled", "")
            fw_str = "全关" if fw_all == "False" else ("已启用" if fw_all == "True" else "未知")
            lines.append(f"系统: {os_name} / 防火墙{fw_str}")

        if processes and processes.get("status") == "ok":
            total_proc = processes.get("total", 0)
            svc_count = processes.get("svchost_count", 0)
            non_std_count = len(processes.get("non_standard", []))
            lines.append(f"进程: {total_proc}总 / {svc_count}svchost / {non_std_count}非标准")

        if startup_items and startup_items.get("status") == "ok":
            sched = startup_items.get("scheduled_tasks") or {}
            non_std = len(sched.get("non_standard", []))
            filtered = sched.get("filtered_standard_count", 0)
            lines.append(f"启动项: {non_std}非标准任务 / {filtered}标准已过滤")

        if iis_logs and iis_logs.get("status") == "ok":
            total_entries = iis_logs.get("total_entries", 0)
            ip_sum = iis_logs.get("ip_summary", [])
            attack_ips = sum(1 for ip in ip_sum if ip.get("attack_patterns"))
            lines.append(f"IIS: {total_entries}请求 / {attack_ips}攻击IP")
        elif not iis_logs or iis_logs.get("status") == "not_found":
            lines.append("IIS: 无")

        if psreadline and psreadline.get("status") == "ok":
            cmd_count = len(psreadline.get("commands", []))
            lines.append(f"命令历史: {cmd_count}条")
        elif not psreadline or psreadline.get("status") == "not_found":
            lines.append("命令历史: 无")

        # 威胁评分摘要
        if threat_score:
            lines.append(
                f"威胁评分: {threat_score['final_score']}/100 "
                f"({threat_score['risk_label']})"
            )

        lines.append(f"耗时 {elapsed:.1f}s")

        return lines
