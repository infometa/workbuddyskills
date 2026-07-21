"""资产解析器 - 把腾讯 CVM 资产 CSV 关联到告警 IP (含 vpcid/appid 联合查询)

关联键 (按产品不同):
  - 御界 yujie:  (asset_ip, gre.vpcid)  → tenant CSV: (内网地址IP, 网络字段里的 vpcid)
  - 主机安全 cwp: (hostip, appid)        → tenant CSV: (内网地址IP, AppID)
  - 通用兜底:    (ip,)                   → tenant/platform CSV: (IP地址/内网地址IP)

设计原则:
  - 不同租户的私有网段可能有相同内网 IP (如 租户A 的 10.0.0.4 ≠ 租户B 的 10.0.0.4)
  - 必须用 (IP + appid) 或 (IP + vpcid) 联合查询, 才能精确匹配
  - 资产 CSV 的"网络"字段格式: "网络名(vpcid)", 如 "tsf-default(67334)"
"""
from __future__ import annotations
import csv
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Asset:
    """统一资产模型 (跨 platform / tenant)"""
    asset_id: str = ""                  # platform: 主机ID, tenant: UUID
    hostname: str = ""
    instance_id: str = ""               # tenant 独有 (ins-xxx)
    layer: str = ""                     # "platform" / "tenant"
    ip: str = ""                        # 主 IP (内网)
    public_ip: str = ""
    ipv6: str = ""
    host_ip: str = ""                   # 宿主机内网 IP
    zone: str = ""                      # 可用区
    network: str = ""                   # 网络 (业务网段, 如 "172-VCP(66586)")
    vpcid: int = 0                      # 从 network 字段提取的 VPC ID (如 66586)
    vpc_name: str = ""                  # VPC 名称 (如 "172-VCP")
    os: str = ""                        # 操作系统 / 镜像
    image_id: str = ""
    cpu: int = 0
    memory: int = 0                     # GB
    system_disk: str = ""
    data_disk: str = ""
    owner: str = ""                     # 创建者账号ID
    appid: str = ""                     # 租户 AppID (tenant 独有)
    status: str = ""
    create_time: str = ""

    # 推断字段
    asset_type: str = ""
    importance: str = ""
    business_system: str = ""

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "hostname": self.hostname,
            "instance_id": self.instance_id,
            "layer": self.layer,
            "ip": self.ip,
            "public_ip": self.public_ip,
            "zone": self.zone,
            "network": self.network,
            "vpcid": self.vpcid,
            "vpc_name": self.vpc_name,
            "os": self.os,
            "cpu": self.cpu,
            "memory": self.memory,
            "owner": self.owner,
            "appid": self.appid,
            "status": self.status,
            "asset_type": self.asset_type,
            "importance": self.importance,
            "business_system": self.business_system,
        }


# 主机名 → 资产类型 / 重要性 推断规则
HOSTNAME_RULES = [
    (r"堡垒机|bhsaas|bh-saas", "security_device", "critical", "堡垒机"),
    (r"honeypot|蜜罐", "security_device", "medium", "蜜罐"),
    (r"natgw|underlay_natgw", "network_device", "high", "NAT 网关"),
    (r"tgw|tgwipv6", "network_device", "high", "TGW 网关"),
    (r"sxgw|sxgw_dpdk", "network_device", "high", "SX 网关"),
    (r"dsaudit|数据安全审计", "security_device", "high", "数据安全审计"),
    (r"cfw|云防火墙", "security_device", "high", "云防火墙"),
    (r"yum|镜像源", "infra_service", "medium", "镜像源"),
    (r"test|测试|demo", "test_machine", "low", "测试环境"),
    (r"prod|生产", "business_server", "high", "生产业务"),
    (r"dev|开发", "business_server", "low", "开发环境"),
    (r"tke|k8s|etcd", "business_server", "high", "TKE/K8s 集群"),
    (r"cfs|文件存储", "infra_service", "medium", "文件存储"),
]


def infer_asset_meta(hostname: str, network: str = "") -> tuple[str, str, str]:
    if not hostname:
        return "unknown", "low", "未知"
    for pattern, atype, imp, biz in HOSTNAME_RULES:
        if re.search(pattern, hostname, re.IGNORECASE):
            return atype, imp, biz
    if network:
        if "VCP" in network or "vpc" in network.lower():
            return "business_server", "medium", "业务服务器"
        if "堡垒机" in network:
            return "security_device", "critical", "堡垒机"
    return "business_server", "medium", "通用业务"


def parse_vpcid_from_network(network: str) -> tuple[int, str]:
    """从网络字段提取 vpcid 和 vpc_name

    格式: "网络名(vpcid)" → (vpcid, 网络名)
    例: "tsf-default(67334)" → (67334, "tsf-default")
        "172-VCP(66586)"    → (66586, "172-VCP")

    Returns:
        (vpcid, vpc_name), 没匹配返回 (0, network)
    """
    if not network:
        return 0, ""
    m = re.search(r"^(.+?)\((\d+)\)$", network.strip())
    if m:
        return int(m.group(2)), m.group(1)
    return 0, network


class AssetResolver:
    """资产解析器 - 多索引联合查询"""

    def __init__(self):
        # 单字段索引
        self._by_ip: dict[str, list[Asset]] = {}  # IP 可能重复 (多租户)
        self._by_hostname: dict[str, Asset] = {}
        self._by_instance_id: dict[str, Asset] = {}
        self._by_asset_id: dict[str, Asset] = {}

        # 联合索引 (精确匹配)
        self._by_ip_appid: dict[tuple[str, str], Asset] = {}   # (ip, appid) → Asset
        self._by_ip_vpcid: dict[tuple[str, int], Asset] = {}   # (ip, vpcid) → Asset

        # 单维度索引 (用于联合查询时缩小范围)
        self._by_appid: dict[str, list[Asset]] = {}
        self._by_vpcid: dict[int, list[Asset]] = {}

        self._loaded_files: list[str] = []

    # ========== 加载 ==========

    def load_csv(self, csv_path: Path, layer: str = "tenant") -> int:
        if not csv_path.exists():
            raise FileNotFoundError(f"资产 CSV 不存在: {csv_path}")

        n = 0
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                asset = self._parse_row(row, layer)
                if not asset:
                    continue
                self._register(asset)
                n += 1

        self._loaded_files.append(f"{layer}:{csv_path.name}")
        return n

    def _parse_row(self, row: dict, layer: str) -> Asset | None:
        asset = Asset(layer=layer)

        if layer == "platform":
            asset.asset_id = (row.get("主机ID") or "").strip()
            asset.hostname = (row.get("主机名") or "").strip()
            asset.ip = (row.get("IP地址") or "").strip()
            asset.host_ip = (row.get("宿主机内网IP") or "").strip()
            asset.zone = (row.get("可用区") or "").strip()
            asset.network = (row.get("上联网络设备") or "").strip()
            asset.os = (row.get("操作系统名称") or "").strip()
            asset.image_id = (row.get("镜像ID") or "").strip()
            asset.cpu = _to_int(row.get("CPU"))
            asset.memory = _to_int(row.get("内存(GB)"))
            asset.system_disk = (row.get("系统盘（类型#大小GB）") or "").strip()
            asset.data_disk = (row.get("数据盘（类型#大小GB）") or "").strip()
            asset.owner = (row.get("创建者账号ID") or "").strip()
            asset.status = (row.get("状态") or "").strip()
            asset.create_time = (row.get("创建时间") or "").strip()
            # platform 没有 appid, 网络字段格式也不同
            asset.vpcid, asset.vpc_name = parse_vpcid_from_network(asset.network)
        else:
            asset.asset_id = (row.get("UUID") or "").strip()
            asset.hostname = (row.get("主机名") or "").strip()
            asset.instance_id = (row.get("实例ID") or "").strip()
            asset.owner = (row.get("创建者账号ID") or "").strip()
            asset.appid = (row.get("AppID") or "").strip()
            asset.status = (row.get("状态") or "").strip()
            asset.ip = (row.get("内网地址IP") or "").strip()
            asset.public_ip = (row.get("公网IP地址") or "").strip()
            asset.ipv6 = (row.get("IPv6地址") or "").strip()
            asset.host_ip = (row.get("宿主机内网IP") or "").strip()
            asset.zone = (row.get("可用区") or "").strip()
            asset.network = (row.get("网络") or "").strip()
            asset.os = (row.get("镜像名称") or "").strip()
            asset.image_id = (row.get("镜像ID") or "").strip()
            asset.cpu = _to_int(row.get("CPU（核）"))
            asset.memory = _to_int(row.get("内存（GB）"))
            asset.system_disk = (row.get("系统盘（类型#大小GB）") or "").strip()
            asset.data_disk = (row.get("数据盘（类型#大小GB）") or "").strip()
            asset.create_time = (row.get("创建时间") or "").strip()
            # tenant 网络字段格式: "网络名(vpcid)"
            asset.vpcid, asset.vpc_name = parse_vpcid_from_network(asset.network)

        # 推断资产类型
        asset.asset_type, asset.importance, asset.business_system = infer_asset_meta(
            asset.hostname, asset.network
        )

        if not asset.asset_id and not asset.ip and not asset.hostname:
            return None
        return asset

    def _register(self, asset: Asset):
        """注册到各索引 (注意 IP 可能跨租户重复, 用 list)"""
        # 单字段索引 (IP 用 list, 其他用单值)
        if asset.ip:
            self._by_ip.setdefault(asset.ip, []).append(asset)
        if asset.hostname:
            self._by_hostname[asset.hostname] = asset
        if asset.instance_id:
            self._by_instance_id[asset.instance_id] = asset
        if asset.asset_id:
            self._by_asset_id[asset.asset_id] = asset

        # 联合索引
        if asset.ip and asset.appid:
            self._by_ip_appid[(asset.ip, asset.appid)] = asset
        if asset.ip and asset.vpcid:
            self._by_ip_vpcid[(asset.ip, asset.vpcid)] = asset

        # 单维度索引 (用于联合查询缩小范围)
        if asset.appid:
            self._by_appid.setdefault(asset.appid, []).append(asset)
        if asset.vpcid:
            self._by_vpcid.setdefault(asset.vpcid, []).append(asset)

    # ========== 单字段查询 ==========

    def lookup(self, ip: str) -> Asset | None:
        """按 IP 查资产 (返回第一个, 多个时需用联合查询)"""
        if not ip:
            return None
        assets = self._by_ip.get(ip)
        return assets[0] if assets else None

    def lookup_all_by_ip(self, ip: str) -> list[Asset]:
        """按 IP 查所有匹配资产 (跨租户可能有多个)"""
        if not ip:
            return []
        return self._by_ip.get(ip, [])

    def lookup_by_hostname(self, hostname: str) -> Asset | None:
        if not hostname:
            return None
        return self._by_hostname.get(hostname)

    # ========== 联合查询 (精确匹配) ==========

    def lookup_by_ip_and_appid(self, ip: str, appid: str) -> Asset | None:
        """按 (IP, appid) 联合查询 - 主机安全专用"""
        if not ip or not appid:
            return None
        # 优先用联合索引
        asset = self._by_ip_appid.get((ip, appid))
        if asset:
            return asset
        # 兜底: 遍历 appid 下的主机找 IP
        for a in self._by_appid.get(appid, []):
            if a.ip == ip:
                return a
        return None

    def lookup_by_ip_and_vpcid(self, ip: str, vpcid: int) -> Asset | None:
        """按 (IP, vpcid) 联合查询 - 御界专用"""
        if not ip or not vpcid:
            return None
        # 优先用联合索引
        asset = self._by_ip_vpcid.get((ip, vpcid))
        if asset:
            return asset
        # 兜底: 遍历 vpcid 下的主机找 IP
        for a in self._by_vpcid.get(vpcid, []):
            if a.ip == ip:
                return a
        return None

    def list_by_appid(self, appid: str) -> list[Asset]:
        """列出某租户的所有资产"""
        return self._by_appid.get(appid, [])

    def list_by_vpcid(self, vpcid: int) -> list[Asset]:
        """列出某 VPC 的所有资产"""
        return self._by_vpcid.get(vpcid, [])

    def _build_vpcid_placeholder(self, vpcid: int, victim_ip: str | None) -> Asset | None:
        """御界受害 IP 在资产库没匹配上时, 用 vpcid 反查该 VPC 下机器构造占位 Asset

        目的: 即便 IP 查不到, 也告诉用户 "这个 VPC 是哪个 AppID, VPC 下有哪些机器"
        占位特征: hostname 形如 "⚠️ IP未匹配, VPC{xxxx}下有N台(样例: aaa,bbb,ccc)"
        """
        vpc_assets = self.list_by_vpcid(vpcid)
        if not vpc_assets:
            return None
        # 取第一台作为字段来源
        first = vpc_assets[0]
        # 汇总 hostname 样例 (最多 3 个非空)
        sample_hosts = [a.hostname for a in vpc_assets if a.hostname][:3]
        sample_str = ",".join(sample_hosts) if sample_hosts else "(无主机名)"
        # 多 AppID 时, 列出所有
        appids_in_vpc = sorted(set(a.appid for a in vpc_assets if a.appid))
        if len(appids_in_vpc) == 1:
            appid_hint = appids_in_vpc[0]
        elif len(appids_in_vpc) > 1:
            appid_hint = ",".join(appids_in_vpc)
        else:
            appid_hint = first.appid or ""
        hostname_placeholder = (
            f"⚠️ IP未匹配 (VPC{vpcid}下{len(vpc_assets)}台, AppID={appid_hint}, "
            f"样例: {sample_str})"
        )
        # 构造占位 Asset, ip 保留受害 IP (让用户知道告警 IP 是什么)
        return Asset(
            asset_id=first.asset_id,
            layer=first.layer,
            ip=victim_ip or "",  # 保留受害 IP
            hostname=hostname_placeholder,
            instance_id=first.instance_id,
            public_ip=first.public_ip,
            zone=first.zone,
            network=first.network,
            vpcid=vpcid,
            vpc_name=first.vpc_name,
            os=first.os,
            image_id=first.image_id,
            cpu=first.cpu,
            memory=first.memory,
            owner=first.owner,
            appid=first.appid,  # 第一台机器的 AppID (该 VPC 通常属同一租户)
            status=first.status,
            create_time=first.create_time,
            asset_type="unknown",
            importance="unknown",
            business_system="占位-VPC反查",
        )

    # ========== 事件关联 ==========

    def enrich_event(self, parsed: dict, product: str = "") -> dict:
        """给 L0 parsed 加 asset 字段, 按产品走不同关联逻辑

        关联键:
          - yujie: (real_victim_ip / asset_ip, gre.vpcid) → tenant CSV (ip, vpcid)
          - cwp:   (host_ip, _raw_kv.appid)              → tenant CSV (ip, appid)
          - 通用:  (real_attacker_ip / src_ip, ...)      → 任意 CSV (ip,)

        Returns:
            {
                "src_asset": {...} | None,
                "victim_asset": {...} | None,
                "dst_asset": {...} | None,
                "asset_match_summary": "matched=X/3",
                "match_method": "ip_appid" / "ip_vpcid" / "ip_only" / "none",
            }
        """
        result = {
            "src_asset": None,
            "victim_asset": None,
            "dst_asset": None,
            "match_method": "none",
        }

        # 提取 parsed 里的关联键
        # yujie: gre.vpcid + asset_ip / real_victim_ip
        gre = parsed.get("encapsulation", {}).get("gre") or {}
        gre_vpcid = gre.get("vpcid") if isinstance(gre, dict) else None
        asset_ip_raw = parsed.get("asset_ip")  # 可能是 list 字符串 "['172.16.114.119']"
        asset_ip = self._normalize_asset_ip(asset_ip_raw)
        real_victim = parsed.get("real_victim_ip")
        real_attacker = parsed.get("real_attacker_ip")
        src_ip = parsed.get("src_ip")
        dst_ip = parsed.get("dst_ip")
        host_ip = parsed.get("host_ip")
        hostname = parsed.get("hostname")

        # cwp: appid + host_ip
        raw_kv = parsed.get("_raw_kv", {}) or {}
        appid = parsed.get("appid") or raw_kv.get("appid")

        # === 1. 受害资产 (核心) ===
        victim_asset = None
        match_method = "none"

        if product == "yujie" or gre_vpcid:
            # 御界: 必须用 (ip, vpcid) 联合查询, 不 fallback ip_only (避免跨租户误匹配)
            for ip in [asset_ip, real_victim, dst_ip]:
                if not ip:
                    continue
                if gre_vpcid:
                    a = self.lookup_by_ip_and_vpcid(ip, gre_vpcid)
                    if a:
                        victim_asset = a
                        match_method = "ip_vpcid"
                        break
            # vpcid 联合查询失败 → fallback 用 vpcid-only 反查该 VPC 下任意一台机器作为占位
            #   目的: 即便受害 IP 没匹配上, 也能看到 "这个 VPC 是哪个 AppID 的、VPC 下有哪些机器"
            #   标记 match_method="vpcid_only" 让下游区分真实匹配 vs 占位
            if not victim_asset and gre_vpcid:
                placeholder = self._build_vpcid_placeholder(gre_vpcid, real_victim or asset_ip or dst_ip)
                if placeholder:
                    victim_asset = placeholder
                    match_method = "vpcid_only"
            # vpcid 没匹配上, 不 fallback (避免跨 VPC 误匹配)
            # 但如果 raw_log 里没 vpcid, 才用 ip_only 兜底
            if not victim_asset and not gre_vpcid:
                for ip in [asset_ip, real_victim, dst_ip]:
                    if ip:
                        a = self.lookup(ip)
                        if a:
                            victim_asset = a
                            match_method = "ip_only"
                            break

        elif product == "cwp" or appid:
            # 主机安全: 必须用 (ip, appid) 联合查询, 不 fallback ip_only (避免跨租户误匹配)
            for ip in [host_ip, dst_ip, real_victim]:
                if not ip:
                    continue
                if appid:
                    a = self.lookup_by_ip_and_appid(ip, appid)
                    if a:
                        victim_asset = a
                        match_method = "ip_appid"
                        break
            # appid 没匹配上, 不 fallback (避免跨租户误匹配)
            # 但如果 raw_log 里没 appid, 才用 ip_only 兜底
            if not victim_asset and not appid:
                for ip in [host_ip, dst_ip, real_victim]:
                    if ip:
                        a = self.lookup(ip)
                        if a:
                            victim_asset = a
                            match_method = "ip_only"
                            break

        else:
            # 通用兜底: 没有 product 信息时才用 ip_only
            for ip in [real_victim, host_ip, dst_ip]:
                if ip:
                    a = self.lookup(ip)
                    if a:
                        victim_asset = a
                        match_method = "ip_only"
                        break

        if victim_asset:
            result["victim_asset"] = victim_asset.to_dict()

        # === 2. 攻击者资产 ===
        # 攻击者通常是公网 IP, 查不到是正常的
        for ip in [real_attacker, src_ip]:
            if not ip:
                continue
            # 公网 IP 不查 (性能优化)
            if self._is_public_ip(ip):
                break
            a = self.lookup(ip)
            if a:
                result["src_asset"] = a.to_dict()
                break

        # === 3. 目的资产 (与 victim 重叠时不重复) ===
        if dst_ip and dst_ip != real_victim and dst_ip != host_ip:
            a = self.lookup(dst_ip)
            if a:
                result["dst_asset"] = a.to_dict()

        # === 4. hostname 兜底 (主机类) ===
        if hostname and hostname != "-" and not result["victim_asset"]:
            a = self.lookup_by_hostname(hostname)
            if a:
                result["victim_asset"] = a.to_dict()
                if match_method == "none":
                    match_method = "hostname"

        # === 5. 统计 ===
        matched = sum(1 for v in [result["src_asset"], result["victim_asset"], result["dst_asset"]] if v)
        result["asset_match_summary"] = f"matched={matched}/3"
        result["match_method"] = match_method

        return result

    @staticmethod
    def _normalize_asset_ip(raw) -> str | None:
        """规范化 asset_ip 字段 (御界 raw_log 里是 list 字符串 "['1.2.3.4']")"""
        if not raw:
            return None
        if isinstance(raw, list):
            return raw[0] if raw else None
        s = str(raw).strip()
        # 去掉 ['...'] 包装
        m = re.match(r"^\['?([^'\]]+)'?\]$", s)
        if m:
            return m.group(1)
        return s if s else None

    @staticmethod
    def _is_public_ip(ip: str) -> bool:
        """判断是否公网 IP (粗略, 用于跳过攻击者资产查询)"""
        if not ip:
            return False
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_global and not ip_obj.is_private
        except (ValueError, TypeError):
            return False

    # ========== 统计 ==========

    def stats(self) -> dict:
        all_assets = set()
        for assets in self._by_ip.values():
            for a in assets:
                all_assets.add(id(a))
        return {
            "total": len(all_assets),
            "by_ip": len(self._by_ip),
            "by_hostname": len(self._by_hostname),
            "by_instance_id": len(self._by_instance_id),
            "by_appid": len(self._by_appid),
            "by_vpcid": len(self._by_vpcid),
            "by_ip_appid": len(self._by_ip_appid),
            "by_ip_vpcid": len(self._by_ip_vpcid),
            "loaded_files": self._loaded_files,
            "by_layer": self._count_by_layer(),
            "by_type": self._count_by_type(),
            "by_importance": self._count_by_importance(),
        }

    def _count_by_layer(self) -> dict:
        out = {}
        seen = set()
        for assets in self._by_ip.values():
            for a in assets:
                if id(a) in seen:
                    continue
                seen.add(id(a))
                out[a.layer] = out.get(a.layer, 0) + 1
        return out

    def _count_by_type(self) -> dict:
        out = {}
        seen = set()
        for assets in self._by_ip.values():
            for a in assets:
                if id(a) in seen:
                    continue
                seen.add(id(a))
                out[a.asset_type] = out.get(a.asset_type, 0) + 1
        return out

    def _count_by_importance(self) -> dict:
        out = {}
        seen = set()
        for assets in self._by_ip.values():
            for a in assets:
                if id(a) in seen:
                    continue
                seen.add(id(a))
                out[a.importance] = out.get(a.importance, 0) + 1
        return out


def _to_int(v) -> int:
    if v is None or v == "":
        return 0
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return 0


def _find_asset_dir(workspace_root: Path) -> Path | None:
    """两级 fallback 定位资产目录

    1. $CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/ (用户数据, 最高优先级)
    2. <workspace_root>/host-资产/ (项目根自定义资产)
    3. 都不存在返回 None
    """
    # 第1级: CODEBUDDY_PLUGIN_DATA
    plugin_data = os.environ.get("CODEBUDDY_PLUGIN_DATA")
    if plugin_data:
        candidate = Path(os.path.expanduser(plugin_data)) / "soe-skill" / "asset-manager" / "assets"
        if candidate.exists():
            return candidate

    # 第2级: 项目根
    candidate = workspace_root / "host-资产"
    if candidate.exists():
        return candidate

    return None


def get_asset_data_dir() -> Path:
    """获取资产数据目录 (CODEBUDDY_PLUGIN_DATA 下)

    Returns:
        $CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/

    Raises:
        RuntimeError: CODEBUDDY_PLUGIN_DATA 环境变量未设置
    """
    plugin_data = os.environ.get("CODEBUDDY_PLUGIN_DATA")
    if not plugin_data:
        raise RuntimeError(
            "CODEBUDDY_PLUGIN_DATA 环境变量未设置."
        )
    d = Path(os.path.expanduser(plugin_data)) / "soe-skill" / "asset-manager" / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def import_assets(source_csv: Path, layer: str = "tenant") -> Path:
    """将资产 CSV 导入到 CODEBUDDY_PLUGIN_DATA 目录

    Args:
        source_csv: 源 CSV 文件路径
        layer: "platform" 或 "tenant"

    Returns:
        导入后的目标文件路径

    Raises:
        RuntimeError: CODEBUDDY_PLUGIN_DATA 环境变量未设置
        FileNotFoundError: 源文件不存在
    """
    source_csv = Path(source_csv)
    if not source_csv.exists():
        raise FileNotFoundError(f"源 CSV 文件不存在: {source_csv}")

    target_dir = get_asset_data_dir()
    filename = "platform_cvm_list.csv" if layer == "platform" else "tenant_cvm_list.csv"
    target = target_dir / filename
    shutil.copy2(source_csv, target)
    print(f"[INFO] 导入 {layer} 资产: {source_csv} → {target}", file=sys.stderr)
    return target


def load_default_assets(workspace_root: Path) -> AssetResolver:
    """从默认路径加载资产库 (两级 fallback)

    查找顺序:
        1. $CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/  (用户数据, 最高优先级)
        2. <workspace_root>/host-资产/                             (项目根自定义资产)
        3. 都不存在 → 空库 (下游可 --assets <dir> 手动指定或 --no-assets 跳过)

    Args:
        workspace_root: 工作区根目录 (项目根)

    Returns:
        加载好的 AssetResolver 实例 (可能为空)
    """
    resolver = AssetResolver()

    asset_dir = _find_asset_dir(workspace_root)
    if asset_dir is None:
        print("[INFO] 未找到资产库 (CODEBUDDY_PLUGIN_DATA 和项目根 host-资产/ 都不存在), "
              "跳过资产关联. 可用 --assets <dir> 手动指定或 --no-assets 跳过. "
              "导入资产可用 import_assets() 函数.",
              file=sys.stderr)
        return resolver

    platform_csv = asset_dir / "platform_cvm_list.csv"
    tenant_csv = asset_dir / "tenant_cvm_list.csv"

    if platform_csv.exists():
        n = resolver.load_csv(platform_csv, layer="platform")
        print(f"[INFO] 加载平台资产: {n} 台 (来源: {asset_dir})", file=sys.stderr)

    if tenant_csv.exists():
        n = resolver.load_csv(tenant_csv, layer="tenant")
        print(f"[INFO] 加载租户资产: {n} 台 (来源: {asset_dir})", file=sys.stderr)

    return resolver
