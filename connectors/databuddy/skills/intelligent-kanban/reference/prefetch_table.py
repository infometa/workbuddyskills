#!/usr/bin/env python3
"""
看板专用：表名解析（支持中文/英文/三段式）+ 同步拉 schema + 后台预取 CSV。

协议总览
--------
1) 找表（语义召回）：wedatacli search 双通道（wildcard + match）；
   决策成功后透出 (full_name, connection_type, connection_id)，并跑单源闸门。
   三段式快路径：仍调一次 search（按 full_name 精确匹配）补全路由，避免 OLAP
   表被错误默认到 lakehouse SqlType=1。
2) Schema：内联客户端调 wedatacli get columns（fallback get table）—— 与
   lakehouse/OLAP 元数据接口同协议；ThreadPoolExecutor 并行 N 张表，3 张
   表 ~2s（原串行 ~6s）。
3) 取数：wedatacli query-sql CLI 入口，lakehouse 走 SqlType=1，
   OLAP 走 SqlType=3 + DataSourceId；CLI 内部承接提交、轮询和 CSV 下载闭环。

依赖：仅依赖 plugin 自身的 l0-cli/wedatacli.sh（基础设施层）；
      不直接调用 DataclawToolService HTTP 接口，不依赖其它 skill 脚本。

主线程时序：找表 (~1s) → schema 并行 (~2s) → 立即 print JSON 给 LLM；
后台 fork：N 张表整体并行 wedatacli query-sql → 落 /tmp/wedata_kanban_cache/<key>.meta.json，
runner 端通过 (table, where='', limit) 寻址命中。
"""

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════════════════════════════
# 路径解析
# ═══════════════════════════════════════════════════════════════

def _resolve_plugin_root() -> str:
    """定位 plugin 根目录（含 l0-cli/wedatacli.sh 的目录）。

    优先级：
    1. `CODEBUDDY_PLUGIN_ROOT` 环境变量（若指向真实目录）
    2. 从 __file__ 向上爬升，找到含 `l0-cli/wedatacli.sh` 的最近祖先
       —— 兼容新布局 `<root>/scenarios/data-analysis/skills/intelligent-kanban/reference/`
       与老布局 `<root>/l3-skill-scenario/intelligent-kanban/reference/`
    3. 兜底：`<script_dir>/../../..`（对老布局仍等价）
    """
    env_root = os.environ.get("CODEBUDDY_PLUGIN_ROOT", "").strip()
    if env_root and os.path.isdir(env_root):
        return os.path.normpath(env_root)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cur = script_dir
    for _ in range(8):  # 最多向上 8 层，防止无限循环
        if os.path.isfile(os.path.join(cur, "l0-cli", "wedatacli.sh")):
            return os.path.normpath(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.normpath(os.path.join(script_dir, "..", "..", ".."))


PLUGIN_ROOT = _resolve_plugin_root()
# wedatacli.sh 标准位置：<plugin_root>/l0-cli/wedatacli.sh（与 plugin manifest 一致）
WEDATACLI_SH = os.path.join(PLUGIN_ROOT, "l0-cli", "wedatacli.sh")

# 缓存目录与 runner 端 _SQL_CACHE_DIR 字节级一致
# 解析优先级：KANBAN_SQL_CACHE_DIR > WEDATA_WORKSPACE_FOLDER/tmp/wedata_kanban_cache > /tmp/wedata_kanban_cache
def _resolve_sql_cache_dir():
    explicit = os.environ.get("KANBAN_SQL_CACHE_DIR", "").strip()
    if explicit:
        return explicit
    workspace_folder = os.environ.get("WEDATA_WORKSPACE_FOLDER", "").strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        return os.path.join(workspace_folder, "tmp", "wedata_kanban_cache")
    return "/tmp/wedata_kanban_cache"


SQL_CACHE_DIR = _resolve_sql_cache_dir()


def _resolve_workspace_tmp_dir():
    """临时文件目录：WEDATA_WORKSPACE_FOLDER/tmp > 系统默认（None 让 tempfile 自选）。"""
    workspace_folder = os.environ.get("WEDATA_WORKSPACE_FOLDER", "").strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        tmp_dir = os.path.join(workspace_folder, "tmp")
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            return tmp_dir
        except OSError:
            return None
    return None
# 【DEFAULT_LIMIT 契约】此值必须与 kanban_dsl.py:Source.limit 默认值 / SKILL.md DSL 速查
#   / kanban_spec_example.py 中的 limit 参数**四处同步**。
#   看板端 duckdb 视图做聚合 + top_k 硬截断，1w 行的样本对图表精度影响可忽略；
#   服务端 sql.query 预算 5min，10 000 行对绝大多数 lakehouse/OLAP 数据源均可
#   在 2s 内完成，避免踩线全表 500k 触发全量扫描 + COS 上传。
#   如需更大样本，请用户在 spec 里显式覆盖 Source(limit=...)，不要改这里的默认值。
DEFAULT_LIMIT = 10_000
SCHEMA_TIMEOUT = 30        # schema 单表 wedatacli 调用最长等 30s（并行后总耗时 ≈ max(单表)）
FETCH_TOTAL_TIMEOUT = 600  # 单表 wedatacli query-sql 总取数最长 10 分钟
# 【常量对齐锚点】此值必须与 kanban_runner.py:_QUERY_SQL_CLI_TIMEOUT_BUFFER 同步。
#   两处均为「Python subprocess.wait 相对 CLI 自身 --timeout 的额外收尾/落盘缓冲」，
#   偏离会导致：值过小 → subprocess 先超时杀 CLI，落盘信封不完整；
#             值过大 → 用户观察到超时后仍需继续等 60s+，体感差。
QUERY_SQL_CLI_TIMEOUT_BUFFER = 60  # 若调整此值，请同步 kanban_runner.py 端

# resolve 阶段
SEARCH_TIMEOUT = 30
SEARCH_TOP_K = 10

# wedatacli 双通道决策阈值（详见 _decide_one）
MATCH_FLOOR = 2.5
MATCH_RATIO = 2.0
WILDCARD_TOP = 5
DISAMBIGUATION_TOP = 5
EXIT_DISAMBIGUATION = 2
EXIT_NOT_FOUND = 3

# 看板单次最多预取 3 张表（对话体验 + 取数效率双优化）
MAX_TABLES = 3

# 语义召回阶段命中的 fields.columns 缓存（key=full_name），
# schema 阶段作为 fast-path 消费，避免对同一表再多打一次 wedatacli get columns。
# 命中要求：columns 是非空 list，每列至少有 name（type 缺失允许，schema 里降级为空串）。
# 缺失或字段不完整 → schema 阶段回落到原先的 get columns / get table 双路兜底。
_SEARCH_COLUMNS_CACHE: dict = {}


def _extract_columns_from_search_item(it: dict) -> list:
    """从 wedatacli search 返回项抽 columns fast-path 数据。

    支持两种协议：
      1) fields.columns 为 list[{name,type,...}]（新协议，见 t_user 样例）
      2) fields.metadata 为 JSON 字符串，含 columns 数组（老协议兜底）
    输出结构与 _fetch_one_table_schema 对齐。任一列缺 name → 视为脏数据，返回 []。
    """
    if not it:
        return []
    fields = it.get("fields") or {}
    raw_cols = fields.get("columns")
    if not isinstance(raw_cols, list) or not raw_cols:
        meta_str = fields.get("metadata")
        if isinstance(meta_str, str) and meta_str:
            try:
                meta_obj = json.loads(meta_str)
                if isinstance(meta_obj, dict):
                    raw_cols = meta_obj.get("columns")
            except Exception:
                raw_cols = None
    if not isinstance(raw_cols, list) or not raw_cols:
        return []
    out = []
    for c in raw_cols:
        if not isinstance(c, dict):
            return []
        name = str(c.get("name") or c.get("Name") or "").strip()
        if not name:
            return []
        out.append({
            "name": name,
            "type": str(c.get("type") or c.get("Type") or "").strip(),
            "comment": str(c.get("comment") or c.get("Comment") or ""),
            "is_partition": bool(c.get("is_partition") or c.get("IsPartition") or False),
        })
    return out


def _remember_search_columns(full_name: str, it: dict) -> None:
    """将命中项 columns 缓存到 _SEARCH_COLUMNS_CACHE，供 schema 阶段 fast-path 消费。
    幂等：非空覆盖，空值不覆盖已有值。"""
    if not full_name or not it:
        return
    cols = _extract_columns_from_search_item(it)
    if cols:
        _SEARCH_COLUMNS_CACHE[full_name] = cols


# ═══════════════════════════════════════════════════════════════
# 缓存层（与 runner 端 _SQL_CACHE_DIR / _data_cache_key / meta 协议字节对齐）
# ─────────────────────────────────────────────────────────────
# cache key = sha1(table || where='' || limit)；prefetch 永远以 where='' 全量写入。
# runner 端按 spec.source 的 (table, where, limit) 寻址；列子集校验由 runner 做。
# ═══════════════════════════════════════════════════════════════

def _normalize_table_for_cache_key(table: str) -> str:
    """双端 cache key 归一：取尾两段（catalog.db.table → db.table）。

    动机：spec.source.table 由 LLM 按方言规约填写：
      - lakehouse/StarRocks/Doris → 三段式；MySQL/PG/GaussDB → 两段式。
    prefetch 内部一律用完整 full_name（三段式）跑取数，直接算 hash 会与 runner 端
    两段式 key 不一致 → runner 100% miss → 走同步兜底 → 服务端要 computeResource。
    统一裁到尾两段后，双端天然一致，SPARK/StarRocks/Doris 的三段式经归一裁到两段
    仍等价（同 hash 空间），零回归。runner 端已同步落地同一份归一。
    """
    name = (table or "").strip()
    if not name or "." not in name:
        return name
    parts = [p for p in name.split(".") if p]
    if len(parts) <= 2:
        return name
    return ".".join(parts[-2:])


def _data_cache_key(table: str, where: str, limit: int) -> str:
    norm_table = _normalize_table_for_cache_key(table)
    norm_where = re.sub(r"\s+", " ", (where or "").strip())
    payload = f"{norm_table}||{norm_where}||{int(limit)}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _build_fetch_sql(table: str, conn_type: str = "", limit: int = DEFAULT_LIMIT) -> str:
    """整轮看板单表只取一次数 → 固定 `SELECT * FROM <table> LIMIT N`。

    取数端已有限流保护；这里不做 schema 列裁剪、不做分阶段取数。
    外部数据源按方言裁剪表名段数，避免 MySQL/PostgreSQL/GaussDB 收到
    Spark 风格 catalog.schema.table 后报 unknown database/table。
    """
    query_table = _project_table_name_for_sql(table, conn_type)
    return f"SELECT *\n FROM {query_table}\n LIMIT {int(limit)}"


def _cache_already_hit(table: str, limit: int = DEFAULT_LIMIT) -> bool:
    try:
        ttl = int(os.environ.get("KANBAN_SQL_CACHE_TTL", str(6 * 3600)))
    except ValueError:
        ttl = 6 * 3600
    if ttl <= 0 or not table:
        return False
    key = _data_cache_key(table, "", limit)
    meta_path = os.path.join(SQL_CACHE_DIR, f"{key}.meta.json")
    if not os.path.isfile(meta_path):
        return False
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        csv_path = meta.get("csv_path", "")
        created_at = float(meta.get("created_at", 0))
        return bool(csv_path and os.path.isfile(csv_path) and (time.time() - created_at) <= ttl)
    except Exception:
        return False


def _pending_path(table: str, limit: int = DEFAULT_LIMIT) -> str:
    key = _data_cache_key(table, "", limit)
    return os.path.join(SQL_CACHE_DIR, f"{key}.pending.json")


def _write_pending(table: str, limit: int = DEFAULT_LIMIT) -> None:
    if not table:
        return
    try:
        os.makedirs(SQL_CACHE_DIR, exist_ok=True)
        with open(_pending_path(table, limit), "w", encoding="utf-8") as f:
            json.dump({
                "table": table,
                "where": "",
                "limit_used": int(limit),
                "started_at": time.time(),
                "pid": os.getpid(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


def _clear_pending(table: str, limit: int = DEFAULT_LIMIT) -> None:
    try:
        path = _pending_path(table, limit)
        if os.path.isfile(path):
            os.unlink(path)
    except Exception:
        pass


def _store_cache(table: str, csv_path: str, sql: str, limit: int,
                 conn_type: str, conn_id: str, sql_type: int,
                 job_id: str, resource_id: str = "") -> None:
    """写 meta.json：runner 端同时消费 CSV 缓存与路由信息。

    协议字段（runner 端字节级对齐）：
      - resource_id：真实执行资源 ID，供看板 PREVIEW 入库 UpdateAiKanBan.ExecuteResourceId 使用；
        不得用 query-sql JobId/TaskId 兜底，否则 lakehouse 刷新会把任务 ID 当计算资源。
      - connection_type / connection_id：runner 同步 miss 兜底直接复用，无需重查 wedatacli
      - sql_type：1=lakehouse / 3=OLAP，与 wedatacli query-sql 协议一致
      - job_id：query-sql 落盘 quant.JobId（追日志用）
    """
    if not table or not csv_path:
        return
    try:
        os.makedirs(SQL_CACHE_DIR, exist_ok=True)
        key = _data_cache_key(table, "", limit)
        meta_path = os.path.join(SQL_CACHE_DIR, f"{key}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "csv_path": csv_path,
                "resource_id": resource_id or "",
                "created_at": time.time(),
                "sql_preview": (sql or "").strip()[:200],
                "table": table,
                "where": "",
                "limit_used": int(limit),
                "prefetched": True,
                "route_only": False,
                "connection_type": conn_type or "",
                "connection_id": conn_id or "",
                "sql_type": int(sql_type),
                "job_id": job_id or "",
                "route_updated_at": time.time(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


def _store_route_meta(table: str, conn_type: str, conn_id: str,
                      sql_type: int, data_source_id: str,
                      limit: int = DEFAULT_LIMIT) -> None:
    """先写 route-only meta，保证 runner 即使没等到 CSV 也能正确走 OLAP 同步兜底。

    若已存在可用 CSV meta，则只补充路由字段，不刷新 created_at，避免延长旧数据缓存 TTL。
    """
    if not table:
        return
    try:
        os.makedirs(SQL_CACHE_DIR, exist_ok=True)
        key = _data_cache_key(table, "", limit)
        meta_path = os.path.join(SQL_CACHE_DIR, f"{key}.meta.json")
        meta = {}
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    old = json.load(f) or {}
                if isinstance(old, dict):
                    meta = old
            except Exception:
                meta = {}

        csv_path = (meta.get("csv_path") or "").strip()
        has_csv = bool(csv_path and os.path.isfile(csv_path))
        if not has_csv:
            meta.update({
                "csv_path": "",
                "resource_id": meta.get("resource_id") or "",
                "created_at": time.time(),
                "sql_preview": _build_fetch_sql(table, conn_type, limit).strip()[:200],
                "table": table,
                "where": "",
                "limit_used": int(limit),
                "prefetched": False,
                "route_only": True,
            })
        else:
            meta["route_only"] = False

        meta.update({
            "table": table,
            "connection_type": conn_type or "",
            "connection_id": conn_id or "",
            "sql_type": int(sql_type),
            "data_source_id": data_source_id or "",
            "route_updated_at": time.time(),
        })
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
    except Exception:
        pass


def _resolve_plugin_env() -> str:
    env_path = os.environ.get("WEDATA_PLUGIN_ENV", "").strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    default_path = os.path.expanduser("~/.wedata/plugin-env")
    if os.path.isfile(default_path):
        return default_path
    return ""


def _workspace_folder_extra_args() -> list:
    """从 env WEDATA_WORKSPACE_FOLDER 读取工作空间目录，非空则返回 ['--workspace_folder', <path>]。

    - DataBuddy 沙箱场景：env 未设置 → 返回 [] → CLI argv 不变。
    - WorkBuddy 连接器场景：intelligent-kanban SKILL.md 已在 Step B/D 前置 export，
      追加到 argv 后满足 WorkBuddy 严格模式（runtimeMode=workbuddy）对 --workspace_folder 的强制要求。
    """
    wf = os.environ.get("WEDATA_WORKSPACE_FOLDER", "").strip()
    if wf:
        return ["--workspace_folder", wf]
    return []


# ═══════════════════════════════════════════════════════════════
# Resolve 阶段：自然语言/中文表名 → catalog.db.table + 路由信息
# ─────────────────────────────────────────────────────────────
# 决策树（强证据优先；弱证据一律不接受）：
#   ① wildcard total==1            → 表名字面唯一精确包含，零歧义直采
#   ② wildcard total>=2            → 字面多解，消歧 wildcard 候选
#   ③ match Top1.score≥FLOOR ∧
#      (同名 ∨ N=1 ∨ ratio≥RATIO)  → BM25 高置信直采
#   ④ match Top1.score≥FLOOR ∧
#      ratio<RATIO                 → 真歧义，消歧 match 候选
#   ⑤ 其它                          → not_found（不接受 fuzzy 兜底）
# ═══════════════════════════════════════════════════════════════

_THREE_SEG_RE = re.compile(r"^[A-Za-z_][\w$]*\.[A-Za-z_][\w$]*\.[A-Za-z_][\w$]*$")
_INTENT_SPLIT_RE = re.compile(r"[、，,]|以及|和|与")


def _is_three_segment(s: str) -> bool:
    return bool(_THREE_SEG_RE.match(s.strip()))


def _split_intents(raw: str) -> list:
    """显式并列分隔符切意图；切完后任一段 <2 字符则整体保留（防误切「共和国」）。"""
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in _INTENT_SPLIT_RE.split(raw) if p and p.strip()]
    if not parts:
        return [raw]
    if any(len(p) < 2 for p in parts):
        return [raw]
    return parts


def _it_field(it: dict, key: str) -> str:
    """wedatacli search 双协议字段读取（嵌套 verbose 优先，回退顶级 compact）。

    特殊键 'table'：compact 协议没有顶级 table 字段，回退顶级 name；
    特殊键 'connection_type' / 'connection_id'：兼容大小写 + 下划线/驼峰。
    """
    if not it:
        return ""
    f = it.get("fields") or {}
    v = f.get(key)
    if v is None or v == "":
        v = it.get(key)
    if (v is None or v == "") and key == "table":
        v = it.get("name")
    if (v is None or v == "") and key in ("connection_type", "connection_id"):
        # 兼容驼峰命名（后端 trpc_client.go 透出 ConnectionType/ConnectionId）
        camel = "ConnectionType" if key == "connection_type" else "ConnectionId"
        v = f.get(camel) or it.get(camel)
    return str(v).strip() if v is not None else ""


def _it_acl_masked(it: dict) -> bool:
    if not it:
        return False
    f = it.get("fields") or {}
    if f.get("_acl_masked"):
        return True
    if it.get("acl_masked"):
        return True
    # compact legacy: catalog/schema 被打码成 "***"（旧协议）
    cat = (it.get("catalog") or "").strip()
    sch = (it.get("schema") or "").strip()
    return cat == "***" or sch == "***"


def _wedatacli_search_one(query: str, mode: str, field: str = "") -> list:
    qspec = {"query": query, "mode": mode}
    if field:
        qspec["field"] = field
    payload = json.dumps(
        {"resource": "table", "queries": [qspec], "top_k": SEARCH_TOP_K},
        ensure_ascii=False,
    )
    wf_suffix = "".join(f" {shlex.quote(a)}" for a in _workspace_folder_extra_args())
    plugin_env = _resolve_plugin_env()
    if plugin_env:
        cmd = (
            f". {shlex.quote(plugin_env)} && "
            f'"$WEDATACLI_PATH" search {shlex.quote(payload)}{wf_suffix}'
        )
    elif os.path.isfile(WEDATACLI_SH):
        _ensure_wedatacli_executable()
        cmd = f"{shlex.quote(WEDATACLI_SH)} search {shlex.quote(payload)}{wf_suffix}"
    else:
        cmd = f"wedatacli search {shlex.quote(payload)}{wf_suffix}"
    try:
        res = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace", timeout=SEARCH_TIMEOUT,
        )
    except Exception:
        return []
    if res.returncode != 0:
        return []
    try:
        data = json.loads(res.stdout)
    except Exception:
        return []
    # wedatacli stdout > 16KB 自动截断为 {truncated, file, ...}，回读文件
    if data.get("truncated") and data.get("file"):
        file_path = data.get("file") or ""
        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                return []
    items = data.get("items", []) or []
    return [it for it in items if not _it_acl_masked(it)]


def _wedatacli_search(query: str) -> dict:
    """单意图双通道并行（wildcard + match）。两通道独立无依赖，并行节省约 45% 单意图耗时。"""
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_wc = ex.submit(_wedatacli_search_one, f"*{query}*", "wildcard", "table")
        fut_mc = ex.submit(_wedatacli_search_one, query, "match")
        return {"wildcard": fut_wc.result(), "match": fut_mc.result()}


def _extract_full_name(it: dict) -> str:
    """从 item 抽三段式：full_name → knowledge_id → catalog.schema.table 拼接。"""
    if not it:
        return ""
    full = _it_field(it, "full_name")
    if full and full.count(".") >= 2:
        return full
    kid = _it_field(it, "knowledge_id")
    if kid and kid.count(".") >= 2:
        return kid
    cat = _it_field(it, "catalog")
    sch = _it_field(it, "schema")
    tab = _it_field(it, "table")
    if cat and sch and tab:
        return f"{cat}.{sch}.{tab}"
    return ""


def _extract_route(it: dict) -> tuple:
    """从 item 抽路由信息：(connection_type, connection_id)。

    后端 TableInfoHit 已带 ConnectionType/ConnectionId（knowledge.go:72-73），
    wedatacli search 透传时按 _it_field 双协议读取。未透出 → ('','') → 默认 lakehouse。
    """
    return (
        _it_field(it, "connection_type"),
        _it_field(it, "connection_id"),
    )


def _candidate_brief(it: dict) -> dict:
    comment = (
        _it_field(it, "comment")
        or _it_field(it, "description")
        or _it_field(it, "desc")
    )
    return {
        "full_name": _extract_full_name(it),
        "table": _it_field(it, "table"),
        "schema": _it_field(it, "schema"),
        "catalog": _it_field(it, "catalog"),
        "comment": comment,
        "score": it.get("score", 0),
    }


def _route_fallback_from_match(full_name: str, mc: list) -> tuple:
    """wildcard 通道 field=table 限制了字段返回，可能拿不到 connection_type/connection_id。
    从 match 通道（无 field 限制）按 full_name 精确匹配兜底取路由。"""
    if not full_name or not mc:
        return "", ""
    for it in mc:
        if _extract_full_name(it) == full_name:
            return _extract_route(it)
    return "", ""


def _decide_one(query: str, buckets: dict):
    """单意图双通道决策。返回 (full_name, conn_type, conn_id, ambiguous_candidates, not_found)。
    额外副作用：命中项若带 fields.columns 则写入 _SEARCH_COLUMNS_CACHE，
    schema 阶段可 fast-path 复用，避免重复 get columns。"""
    wc = buckets.get("wildcard", []) or []
    mc = buckets.get("match", []) or []

    # ① wildcard 唯一命中 → 直采（路由缺失时从 match 通道兜底）
    if len(wc) == 1:
        full = _extract_full_name(wc[0])
        if full:
            ct, ci = _extract_route(wc[0])
            if not ct and not ci:
                # wildcard field=table 没透 connection_*，match 通道兜底
                ct, ci = _route_fallback_from_match(full, mc)
            # wildcard field=table 通道通常不带 columns，优先用 match 通道同 full_name 命中项补齐
            _remember_search_columns(full, wc[0])
            for _mit in mc:
                if _extract_full_name(_mit) == full:
                    _remember_search_columns(full, _mit)
                    break
            return full, ct, ci, [], False

    # ② wildcard 多命中 → 消歧
    if len(wc) >= 2:
        return "", "", "", [_candidate_brief(it) for it in wc[:WILDCARD_TOP]], False

    # ③ ④ match 通道判真伪
    if mc:
        s1 = float(mc[0].get("score", 0) or 0)
        if s1 >= MATCH_FLOOR:
            same = [it for it in mc if _it_field(it, "table").lower() == query.lower()]
            if len(same) == 1:
                full = _extract_full_name(same[0])
                if full:
                    ct, ci = _extract_route(same[0])
                    _remember_search_columns(full, same[0])
                    return full, ct, ci, [], False
            elif len(same) >= 2:
                return "", "", "", [_candidate_brief(it) for it in same[:DISAMBIGUATION_TOP]], False

            if len(mc) == 1:
                full = _extract_full_name(mc[0])
                if full:
                    ct, ci = _extract_route(mc[0])
                    _remember_search_columns(full, mc[0])
                    return full, ct, ci, [], False

            s2 = float(mc[1].get("score", 0) or 0)
            if s2 > 0 and s1 / s2 >= MATCH_RATIO:
                full = _extract_full_name(mc[0])
                if full:
                    ct, ci = _extract_route(mc[0])
                    _remember_search_columns(full, mc[0])
                    return full, ct, ci, [], False

            return "", "", "", [_candidate_brief(it) for it in mc[:DISAMBIGUATION_TOP]], False

    # ⑤ not_found
    return "", "", "", [], True


# ═══════════════════════════════════════════════════════════════
# 单源闸门：与 nl2sql_datasource.go::canonicalConnectionType 字节对齐
# ═══════════════════════════════════════════════════════════════

_CANONICAL_MAP = {
    "": "SPARK", "SPARK": "SPARK", "HIVE": "SPARK", "LAKEHOUSE": "SPARK", "DLC": "SPARK",
    "MYSQL": "MYSQL",
    "STARROCKS": "STARROCKS", "STAR_ROCKS": "STARROCKS", "EMR_STARROCKS": "STARROCKS",
    "GAUSSDB": "GAUSSDB", "OPENGAUSS": "GAUSSDB", "OPEN_GAUSS": "GAUSSDB",
    "DORIS": "DORIS", "APACHE_DORIS": "DORIS", "TCHOUSE_D": "DORIS",
    "POSTGRESQL": "POSTGRESQL", "POSTGRES": "POSTGRESQL", "PGSQL": "POSTGRESQL", "PG": "POSTGRESQL",
}


def _canonical_conn_type(raw: str) -> str:
    s = (raw or "").strip().upper().replace("-", "_").replace(" ", "_")
    return _CANONICAL_MAP.get(s, s)  # 未知类型透传，单源闸门会拦下


def _build_route(conn_type: str, conn_id: str) -> dict:
    """与 nl2sql_datasource.go::buildExecutionRoute 对齐。
    返回 {sql_type, data_source_id, mode}。"""
    raw_type = (conn_type or "").strip()
    raw_id = (conn_id or "").strip()
    canon = _canonical_conn_type(raw_type)
    if canon == "SPARK":
        if not raw_type and raw_id:
            raise RuntimeError("empty ConnectionType with non-empty ConnectionId")
        return {"sql_type": 1, "data_source_id": "", "mode": "lakehouse"}
    if canon in ("MYSQL", "STARROCKS", "GAUSSDB", "DORIS", "POSTGRESQL"):
        if not raw_id:
            raise RuntimeError(f"OLAP {canon} 缺 ConnectionId（语义召回未透出）")
        return {"sql_type": 3, "data_source_id": raw_id, "mode": "olap"}
    raise RuntimeError(f"unsupported connection_type: {conn_type}")


def _table_name_segments_for_conn(conn_type: str) -> int:
    """返回该数据源 SQL 可接受的表名最大段数，与 nl2sql_dialect.go 对齐。"""
    canon = _canonical_conn_type(conn_type)
    if canon in ("SPARK", "STARROCKS", "DORIS"):
        return 3
    if canon in ("MYSQL", "GAUSSDB", "POSTGRESQL"):
        return 2
    return 2


def _project_table_name_for_sql(table: str, conn_type: str) -> str:
    """按 OLAP 方言裁剪表名段数；不加引号、不改列，避免引入额外方言差异。"""
    name = (table or "").strip()
    if not name or "." not in name:
        return name
    parts = name.split(".")
    max_segments = _table_name_segments_for_conn(conn_type)
    if max_segments <= 0 or len(parts) <= max_segments:
        return name
    return ".".join(parts[-max_segments:])


def _mask_id(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    if len(s) <= 8:
        return "****"
    return s[:4] + "****" + s[-4:]


def _enforce_single_source(triples: list) -> list:
    """单源闸门：所有 resolved 表必须 (canonical_conn_type, conn_id) 一致。
    跨源 → exit 2 提示用户拆批。返回 [(full_name, conn_type, conn_id), ...]。"""
    if len(triples) <= 1:
        return triples
    keys = set()
    for full_name, ct, ci in triples:
        canon = _canonical_conn_type(ct)
        keys.add((canon, ci if canon != "SPARK" else ""))
    if len(keys) > 1:
        out = {
            "status": "cross_source_not_allowed",
            "groups": [
                {"conn_type": k[0], "conn_id_masked": _mask_id(k[1])}
                for k in sorted(keys)
            ],
            "hint": "单次看板不支持跨数据源混用，请按数据源拆分诉求重试",
        }
        print(json.dumps(out, ensure_ascii=False))
        sys.stdout.flush()
        sys.exit(EXIT_DISAMBIGUATION)
    return triples


def _lookup_route_by_full_name(full_name: str) -> tuple:
    """按 full_name 精确反查 (connection_type, connection_id)。

    用于三段式快路径：用户给了精确表名，仍需要拿路由信息才能正确分发到 OLAP/lakehouse；
    走 match 通道单查（不消歧），失败返回 ('','') 让调用方走默认 lakehouse 兜底。
    命中项若带 fields.columns，同步写入 _SEARCH_COLUMNS_CACHE，schema 阶段可复用。
    """
    if not full_name or not _is_three_segment(full_name):
        return "", ""
    table = full_name.split(".")[-1]
    items = _wedatacli_search_one(table, "match")
    if not items:
        return "", ""
    # 仅接受 full_name 完全匹配（catalog.schema.table 三段全等）；
    # 不再按裸表名 Top1 兜底 —— 同名跨 catalog/schema 的表按 Top1 绑路由会导致
    # OLAP 表被误识别成 Spark（或反之）、schema fast-path 复用错误 columns。
    # 找不到完全匹配 → 返回空路由，由 main() 按 lakehouse(SPARK) 静默兜底。
    for it in items:
        if _extract_full_name(it) == full_name:
            _remember_search_columns(full_name, it)
            return _extract_route(it)
    return "", ""


def _resolve_tables(raw_input: str) -> list:
    """把用户原始输入解析为 [(full_name, conn_type, conn_id), ...]。
    不可解时通过 sys.exit(2/3) 终止。"""
    raw = (raw_input or "").strip()
    if not raw:
        sys.stderr.write("--tables 参数为空\n")
        sys.exit(2)

    # 快路径：用户已给三段式（单表或逗号分隔多表）
    # 仍跑一次 wedatacli search 按 full_name 精确反查路由；查不到则视为 lakehouse（保守兜底）
    direct = [t.strip() for t in raw.split(",") if t.strip()]
    if direct and all(_is_three_segment(t) for t in direct):
        unique_tables = []
        seen = set()
        for t in direct:
            if t not in seen:
                seen.add(t)
                unique_tables.append(t)
        unique_tables = unique_tables[:MAX_TABLES]
        # 并行反查路由（每张表 1 次 search RPC，~0.5s）
        if len(unique_tables) == 1:
            ct, ci = _lookup_route_by_full_name(unique_tables[0])
            out = [(unique_tables[0], ct, ci)]
        else:
            with ThreadPoolExecutor(max_workers=min(len(unique_tables), 4)) as ex:
                futs = {ex.submit(_lookup_route_by_full_name, t): t for t in unique_tables}
                tmp = {}
                for fut in futs:
                    t = futs[fut]
                    try:
                        tmp[t] = fut.result()
                    except Exception:
                        tmp[t] = ("", "")
            out = [(t, tmp[t][0], tmp[t][1]) for t in unique_tables]
        return _enforce_single_source(out)

    # 慢路径：多意图切分 + 并行召回
    intents = _split_intents(raw)
    resolved, ambiguous, missing = [], [], []

    nl_intents = [(i, q) for i, q in enumerate(intents) if not _is_three_segment(q)]
    buckets_map = {}
    if nl_intents:
        max_workers = min(len(nl_intents), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_idx = {ex.submit(_wedatacli_search, q): i for i, q in nl_intents}
            for fut in future_to_idx:
                idx = future_to_idx[fut]
                try:
                    buckets_map[idx] = fut.result()
                except Exception:
                    buckets_map[idx] = {"wildcard": [], "match": []}

    # 三段式与自然语言混合输入：三段式段落同样反查路由（不再默认 lakehouse）
    three_seg_routes = {}
    three_seg_list = [q for q in intents if _is_three_segment(q)]
    if three_seg_list:
        with ThreadPoolExecutor(max_workers=min(len(three_seg_list), 4)) as ex:
            futs = {ex.submit(_lookup_route_by_full_name, t): t for t in three_seg_list}
            for fut in futs:
                t = futs[fut]
                try:
                    three_seg_routes[t] = fut.result()
                except Exception:
                    three_seg_routes[t] = ("", "")

    for i, q in enumerate(intents):
        if _is_three_segment(q):
            ct, ci = three_seg_routes.get(q, ("", ""))
            resolved.append((q, ct, ci))
            continue
        buckets = buckets_map.get(i, {"wildcard": [], "match": []})
        full, ct, ci, cands, not_found = _decide_one(q, buckets)
        if not_found:
            missing.append(q)
        elif full:
            resolved.append((full, ct, ci))
        else:
            ambiguous.append({"query": q, "candidates": cands})

    # 去重保序
    seen_r, resolved_unique = set(), []
    for triple in resolved:
        if triple[0] and triple[0] not in seen_r:
            seen_r.add(triple[0])
            resolved_unique.append(triple)

    # 选表收敛：≥MAX_TABLES 即满足，丢弃剩余 ambiguous/missing
    if len(resolved_unique) >= MAX_TABLES:
        return _enforce_single_source(resolved_unique[:MAX_TABLES])

    if missing:
        out = {"status": "not_found", "missing": missing}
        if resolved_unique:
            out["resolved"] = [t[0] for t in resolved_unique]
        if ambiguous:
            out["ambiguous"] = ambiguous
        print(json.dumps(out, ensure_ascii=False))
        sys.stdout.flush()
        sys.exit(EXIT_NOT_FOUND)

    if ambiguous:
        out = {"status": "need_disambiguation", "ambiguous": ambiguous}
        if resolved_unique:
            out["resolved"] = [t[0] for t in resolved_unique]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.stdout.flush()
        sys.exit(EXIT_DISAMBIGUATION)

    if not resolved_unique:
        sys.stderr.write("表名解析后为空\n")
        sys.exit(2)
    return _enforce_single_source(resolved_unique[:MAX_TABLES])


# ═══════════════════════════════════════════════════════════════
# Schema 同步获取（内联 wedatacli get columns，元数据接口，OLAP/lakehouse 同协议）
# ─────────────────────────────────────────────────────────────
# 设计要点：
#   1) 完全内联，不依赖其它 skill 脚本
#   2) ThreadPoolExecutor 并行 N 张表 → 总耗时 ≈ max(单表)，3 张表从 ~6s → ~2s
#   3) 优先 wedatacli get columns（更干净）→ fallback wedatacli get table（兼容老桶）
#   4) wedatacli.sh 首次执行权限自检（marketplace 分发可能丢 +x 位）
#   5) 输出 schema JSON 协议：
#      {"tables":[{"full_name","catalog","schema","table","columns":[{"name","type","comment","is_partition"}],"column_count"}],"total"}
# ═══════════════════════════════════════════════════════════════

_WEDATACLI_BIN_CHECKED = False


def _ensure_wedatacli_executable() -> None:
    """补齐 wedatacli.sh 与同目录二进制的执行权限。失败静默（首次会被运行时报错暴露）。"""
    global _WEDATACLI_BIN_CHECKED
    if _WEDATACLI_BIN_CHECKED:
        return
    _WEDATACLI_BIN_CHECKED = True
    try:
        if os.path.isfile(WEDATACLI_SH) and not os.access(WEDATACLI_SH, os.X_OK):
            os.chmod(WEDATACLI_SH, 0o755)
        # 同目录的 wedatacli-<os>-<arch> 二进制
        cli_dir = os.path.dirname(WEDATACLI_SH)
        if os.path.isdir(cli_dir):
            for name in os.listdir(cli_dir):
                if name.startswith("wedatacli-"):
                    p = os.path.join(cli_dir, name)
                    if os.path.isfile(p) and not os.access(p, os.X_OK):
                        os.chmod(p, 0o755)
    except Exception:
        pass


def _wedatacli_call(args: list, timeout: int = SCHEMA_TIMEOUT) -> dict:
    """调用 wedatacli 并返回解析后的 JSON。失败抛 RuntimeError。

    三段兜底（与 _wedatacli_search_one / _run_wedatacli 对齐）：
      ① $WEDATA_PLUGIN_ENV 或 ~/.wedata/plugin-env → source && "$WEDATACLI_PATH" <args>
      ② <plugin_root>/l0-cli/wedatacli.sh          → 直接执行 wrapper
      ③ shutil.which("wedatacli")                   → PATH（WorkBuddy 场景走这条）
    """
    if not args:
        raise RuntimeError("wedatacli args 为空")
    str_args = [str(a) for a in args] + _workspace_folder_extra_args()

    plugin_env = _resolve_plugin_env()
    try:
        if plugin_env:
            quoted_args = " ".join(shlex.quote(a) for a in str_args)
            cmd = f". {shlex.quote(plugin_env)} && \"$WEDATACLI_PATH\" {quoted_args}"
            result = subprocess.run(
                cmd, shell=True,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
        elif os.path.isfile(WEDATACLI_SH):
            _ensure_wedatacli_executable()
            result = subprocess.run(
                [WEDATACLI_SH] + str_args,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
        else:
            exe = shutil.which("wedatacli")
            if not exe:
                raise RuntimeError(
                    "wedatacli 不可用（plugin-env / l0-cli/wedatacli.sh / PATH 均未找到）"
                )
            result = subprocess.run(
                [exe] + str_args,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
    except subprocess.TimeoutExpired as ex:
        raise RuntimeError(f"wedatacli 调用超时（{timeout}s）: {' '.join(str_args[:3])}") from ex

    if result.returncode != 0:
        stderr = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"wedatacli 返回错误 (code={result.returncode}): {stderr[:300]}")
    stdout = (result.stdout or "").strip()
    if not stdout:
        raise RuntimeError("wedatacli 输出为空")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as ex:
        raise RuntimeError(f"wedatacli 输出非 JSON: {stdout[:500]}") from ex
    # 兼容 wrapper 的大响应截断信封 {truncated, file, ...}
    if isinstance(data, dict) and data.get("truncated") and data.get("file"):
        file_path = data.get("file") or ""
        if file_path and os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
    return data


def _parse_full_name(full_name: str) -> tuple:
    """解析 catalog.schema.table；非三段式抛 RuntimeError。"""
    parts = (full_name or "").strip().split(".")
    if len(parts) != 3 or not all(p for p in parts):
        raise RuntimeError(f"表名格式错误: '{full_name}'，期望 catalog.schema.table 三段式")
    return parts[0], parts[1], parts[2]


def _extract_columns_from_get_table(resp: dict) -> list:
    """从 wedatacli get table --output json 提取列；兼容旧 search 形信封。"""
    columns = []
    data_cols = (resp.get("data") or {}).get("columns") or []
    if isinstance(data_cols, list) and data_cols:
        for c in data_cols:
            if isinstance(c, dict):
                columns.append({
                    "name": c.get("name", c.get("Name", "")),
                    "type": c.get("type", c.get("Type", "")),
                    "comment": c.get("comment", c.get("Comment", "")),
                    "is_partition": c.get("is_partition", False),
                })
        return columns

    items = resp.get("items", []) or []
    if not items:
        return columns
    fields = items[0].get("fields", {}) or {}

    # columns_summary 优先（可能是 JSON 字符串）
    cs = fields.get("columns_summary", "")
    if isinstance(cs, str) and cs:
        try:
            col_data = json.loads(cs)
            if isinstance(col_data, list):
                for c in col_data:
                    columns.append({
                        "name": c.get("name", c.get("Name", "")),
                        "type": c.get("type", c.get("Type", "")),
                        "comment": c.get("comment", c.get("Comment", "")),
                        "is_partition": c.get("is_partition", False),
                    })
                return columns
        except json.JSONDecodeError:
            pass

    # 直接 fields.columns
    cols = fields.get("columns", []) or []
    if isinstance(cols, list):
        for c in cols:
            if isinstance(c, dict):
                columns.append({
                    "name": c.get("name", c.get("Name", "")),
                    "type": c.get("type", c.get("Type", "")),
                    "comment": c.get("comment", c.get("Comment", "")),
                    "is_partition": c.get("is_partition", False),
                })
    return columns


def _fetch_one_table_schema(full_name: str) -> dict:
    """单表 schema 获取：优先命中 fast-path（search 缓存的 fields.columns）→
    路径 1 wedatacli get columns → 路径 2 wedatacli get table。
    任一失败返回 columns=[] 但记录 warning（不阻塞其他表）。"""
    try:
        catalog, schema, table = _parse_full_name(full_name)
    except RuntimeError as ex:
        return {
            "full_name": full_name, "catalog": "", "schema": "", "table": "",
            "columns": [], "column_count": 0, "warning": str(ex),
        }

    # 路径 0（fast-path）：语义召回阶段已经拿到 fields.columns → 直接复用，节省一次 RPC。
    #   要求列表非空且每列都有 name（_extract_columns_from_search_item 已保证）。
    hint = _SEARCH_COLUMNS_CACHE.get(full_name)
    if isinstance(hint, list) and hint:
        return {
            "full_name": full_name,
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "columns": [dict(c) for c in hint],
            "column_count": len(hint),
        }

    columns = []
    last_err = ""

    # 路径 1: wedatacli get columns（更干净）
    try:
        resp = _wedatacli_call([
            "get", "columns",
            "--catalog", catalog, "--schema", schema, "--table", table,
        ])
        for c in resp.get("items", []) or []:
            columns.append({
                "name": c.get("name", ""),
                "type": c.get("type", ""),
                "comment": c.get("comment", ""),
                "is_partition": c.get("is_partition", False),
            })
    except Exception as ex:
        last_err = str(ex)

    # 路径 2: fallback wedatacli get table（兼容老 catalog 桶）
    if not columns:
        try:
            resp = _wedatacli_call([
                "get", "table",
                "--catalog", catalog, "--schema", schema, "--table", table,
                "--output", "json",
            ])
            columns = _extract_columns_from_get_table(resp)
        except Exception as ex:
            last_err = str(ex) or last_err

    out = {
        "full_name": full_name,
        "catalog": catalog,
        "schema": schema,
        "table": table,
        "columns": columns,
        "column_count": len(columns),
    }
    if not columns and last_err:
        out["warning"] = f"获取列信息失败: {last_err[:200]}"
    return out


def _fetch_schema_sync(tables: list, top: int) -> dict:
    """并行获取 N 张表的 schema。总耗时 ≈ max(单表)。"""
    if not tables:
        raise RuntimeError("_fetch_schema_sync: 表名列表为空")

    target = tables[: max(int(top or 1), len(tables))]
    if not target:
        return {"tables": [], "total": 0}

    if len(target) == 1:
        results = [_fetch_one_table_schema(target[0])]
    else:
        max_workers = min(len(target), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_fetch_one_table_schema, t): t for t in target}
            # 保留输入顺序
            tmp = {}
            for fut in futures:
                t = futures[fut]
                try:
                    tmp[t] = fut.result()
                except Exception as e:
                    tmp[t] = {
                        "full_name": t, "catalog": "", "schema": "", "table": "",
                        "columns": [], "column_count": 0, "warning": str(e)[:200],
                    }
            results = [tmp[t] for t in target]

    return {"tables": results, "total": len(results)}


# ═══════════════════════════════════════════════════════════════
# wedatacli query-sql 客户端（lakehouse + OLAP 同入口）
# ─────────────────────────────────────────────────────────────
# 取数统一委托给 CLI：wedatacli query-sql --sql-file ...
# CLI 内部负责工具任务提交、轮询和 CSV 下载闭环；本脚本只消费
# 清洗后的 {Status, TaskId, CsvPath, Schema, CostMs}，并从 CLI 落盘信封补充
# quant 里的真实执行资源字段；JobId 只作排障字段，不能写入 ExecuteResourceId。
# ═══════════════════════════════════════════════════════════════

def _wedatacli_available() -> bool:
    if _resolve_plugin_env():
        return True
    if os.path.isfile(WEDATACLI_SH):
        return True
    return bool(shutil.which("wedatacli"))


def _run_wedatacli(args: list, timeout: int,
                   input_text: str = None) -> subprocess.CompletedProcess:
    """按 search 同优先级调用 wedatacli：plugin-env → l0-cli/wedatacli.sh → PATH。"""
    if not args:
        raise RuntimeError("wedatacli args 为空")
    str_args = [str(a) for a in args] + _workspace_folder_extra_args()
    plugin_env = _resolve_plugin_env()
    if plugin_env:
        quoted_args = " ".join(shlex.quote(a) for a in str_args)
        cmd = f". {shlex.quote(plugin_env)} && \"$WEDATACLI_PATH\" {quoted_args}"
        return subprocess.run(
            cmd, shell=True,
            input=input_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    if os.path.isfile(WEDATACLI_SH):
        _ensure_wedatacli_executable()
        return subprocess.run(
            [WEDATACLI_SH] + str_args,
            input=input_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    exe = shutil.which("wedatacli") or "wedatacli"
    return subprocess.run(
        [exe] + str_args,
        input=input_text,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def _read_cli_json_stdout(stdout: str) -> dict:
    stdout = (stdout or "").strip()
    if not stdout:
        raise RuntimeError("wedatacli 输出为空")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find("{")
        end = stdout.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError(f"wedatacli 输出非 JSON: {stdout[:500]}")
        try:
            data = json.loads(stdout[start:end + 1])
        except json.JSONDecodeError as ex:
            raise RuntimeError(f"wedatacli 输出非 JSON: {stdout[:500]}") from ex
    if isinstance(data, dict) and data.get("truncated") and data.get("file"):
        file_path = data.get("file") or ""
        if file_path and os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"wedatacli JSON 输出不是对象: {type(data).__name__}")
    return data


_DEFAULT_ANALYSIS_RESOURCE_ID = None
_DEFAULT_ANALYSIS_RESOURCE_LOADED = False


def _find_resource_id_in_obj(obj: dict) -> str:
    if not isinstance(obj, dict):
        return ""
    basic = obj.get("BasicInfo") if isinstance(obj.get("BasicInfo"), dict) else {}
    available = obj.get("AvailableStatus")
    if available not in (None, "", 1, "1"):
        return ""
    resource_type = basic.get("ResourceType") if isinstance(basic, dict) else None
    if resource_type not in (None, "", 3, "3"):
        return ""
    for key in ("ResourceId", "resourceId", "resource_id"):
        rid = str(basic.get(key) or obj.get(key) or "").strip()
        if rid:
            return rid
    return ""


def _extract_first_analysis_resource_id(data) -> str:
    if not isinstance(data, dict):
        return ""
    response = data.get("Response") if isinstance(data.get("Response"), dict) else data
    payload = response.get("Data") if isinstance(response.get("Data"), dict) else response
    resources = payload.get("Resources") if isinstance(payload, dict) else None
    if not isinstance(resources, list):
        return ""
    for item in resources:
        rid = _find_resource_id_in_obj(item)
        if not rid:
            continue
        basic = item.get("BasicInfo") if isinstance(item, dict) and isinstance(item.get("BasicInfo"), dict) else {}
        exec_available = basic.get("ExecAvailableStatus")
        if exec_available in (None, "", 1, "1"):
            return rid
    return ""


def _default_analysis_resource_id() -> str:
    """获取 lakehouse 默认数据分析计算资源 ID；失败返回空，避免把 JobId 误写为资源。"""
    global _DEFAULT_ANALYSIS_RESOURCE_ID, _DEFAULT_ANALYSIS_RESOURCE_LOADED
    if _DEFAULT_ANALYSIS_RESOURCE_LOADED:
        return _DEFAULT_ANALYSIS_RESOURCE_ID or ""
    _DEFAULT_ANALYSIS_RESOURCE_LOADED = True
    _DEFAULT_ANALYSIS_RESOURCE_ID = ""
    if not _wedatacli_available():
        return ""
    workspace_id = os.environ.get("TENCENTCLOUD_WORKSPACE_ID", "").strip()
    if not workspace_id:
        cfg_path = os.path.expanduser("~/.wedata/config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f) or {}
            workspace_id = str(cfg.get("defaultWorkspace") or "").strip()
        except Exception:
            workspace_id = ""
    if not workspace_id:
        return ""
    payload = {
        "WorkspaceId": workspace_id,
        "Page": {"PageNumber": 1, "PageSize": 100},
        "ResourceTypes": [3],
    }
    try:
        result = _run_wedatacli(
            ["ListComputeResourceOptions", "-"],
            timeout=30,
            input_text=json.dumps(payload, ensure_ascii=False),
        )
        if result.returncode != 0:
            return ""
        data = _read_cli_json_stdout(result.stdout or "")
        _DEFAULT_ANALYSIS_RESOURCE_ID = _extract_first_analysis_resource_id(data)
    except Exception:
        _DEFAULT_ANALYSIS_RESOURCE_ID = ""
    return _DEFAULT_ANALYSIS_RESOURCE_ID or ""


def _load_query_sql_quant(task_id: str) -> dict:
    """从 ~/.wedata/query-sql-results/<TaskId>.json 回读完整 findings.quant。"""
    task_id = (task_id or "").strip()
    if not task_id:
        return {}
    path = os.path.expanduser(os.path.join("~", ".wedata", "query-sql-results", f"{task_id}.json"))
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            env = json.load(f) or {}
        result = env.get("Result") or "{}"
        findings = json.loads(result) if isinstance(result, str) else (result or {})
        quant_raw = findings.get("quant") or "{}"
        quant = json.loads(quant_raw) if isinstance(quant_raw, str) else (quant_raw or {})
        return quant if isinstance(quant, dict) else {}
    except Exception:
        return {}


class _SqlQueryClient:
    """wedatacli query-sql 取数客户端。CLI 内部承接提交、轮询和 CSV 下载。"""

    def __init__(self):
        self.available = _wedatacli_available()

    def query(self, sql: str, sql_type: int, data_source_id: str = "",
              compute_resource: str = "", total_timeout: int = FETCH_TOTAL_TIMEOUT) -> dict:
        if not self.available:
            raise RuntimeError("wedatacli 不可用（plugin-env / l0-cli / PATH 均未找到）")
        sql = (sql or "").strip()
        if not sql:
            raise RuntimeError("query-sql SQL 为空")
        try:
            cli_timeout = max(1, int(total_timeout or FETCH_TOTAL_TIMEOUT))
        except (TypeError, ValueError):
            cli_timeout = FETCH_TOTAL_TIMEOUT
        process_timeout = cli_timeout + QUERY_SQL_CLI_TIMEOUT_BUFFER

        sql_file = ""
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", suffix=".sql", prefix="kanban_query_", delete=False,
                dir=_resolve_workspace_tmp_dir(),
            ) as f:
                f.write(sql)
                f.write("\n")
                sql_file = f.name

            args = [
                "query-sql",
                "--sql-file", sql_file,
                "--sql-type", str(int(sql_type)),
                "--timeout", f"{cli_timeout}s",
                "--no-progress",
                "--output", "json",
            ]
            if data_source_id:
                args.extend(["--data-source-id", data_source_id])
            if compute_resource:
                args.extend(["--compute-resource", compute_resource])

            try:
                result = _run_wedatacli(args, timeout=process_timeout)
            except subprocess.TimeoutExpired as ex:
                raise RuntimeError(f"wedatacli query-sql 调用超时（{process_timeout}s）") from ex
        finally:
            if sql_file:
                try:
                    os.unlink(sql_file)
                except OSError:
                    pass

        data = None
        parse_err = None
        if (result.stdout or "").strip():
            try:
                data = _read_cli_json_stdout(result.stdout)
            except Exception as ex:
                parse_err = ex
        if result.returncode != 0:
            msg = ""
            if isinstance(data, dict):
                msg = str(data.get("Message") or data.get("message") or "").strip()
            if not msg:
                msg = (result.stderr or result.stdout or str(parse_err or "")).strip()
            raise RuntimeError(f"wedatacli query-sql failed (code={result.returncode}): {msg[:500]}")
        if data is None:
            if parse_err:
                raise parse_err
            raise RuntimeError("wedatacli query-sql 未返回 JSON")

        status = str(data.get("Status") or "").upper()
        task_id = str(data.get("TaskId") or "").strip()
        if status != "SUCCESS":
            msg = str(data.get("Message") or "query-sql failed without message").strip()
            raise RuntimeError(f"wedatacli query-sql failed: task_id={task_id} msg={msg}")
        csv_path = str(data.get("CsvPath") or "").strip()
        if not csv_path or not os.path.isfile(csv_path):
            raise FileNotFoundError(f"wedatacli query-sql SUCCESS 但 CsvPath 不存在: {csv_path or '<empty>'}")

        quant = _load_query_sql_quant(task_id)
        job_id = str(quant.get("JobId") or "").strip()
        resource_id = str(
            quant.get("ExecuteResourceId")
            or quant.get("ResourceId")
            or quant.get("ComputeResource")
            or quant.get("ComputeResourceId")
            or compute_resource
            or ""
        ).strip()
        return {
            "task_id": task_id,
            "csv_path": csv_path,
            "schema": data.get("Schema") or [],
            "cost_ms": data.get("CostMs") or 0,
            "job_id": job_id,
            "resource_id": resource_id,
            "quant": quant,
        }


# ═══════════════════════════════════════════════════════════════
# 后台进程：N 张表整体并行 wedatacli query-sql → 写缓存
# ═══════════════════════════════════════════════════════════════

def _bg_fetch_one(table: str, conn_type: str, conn_id: str, client: _SqlQueryClient) -> None:
    """对单张表执行 wedatacli query-sql → 写缓存。
    任何失败静默吞掉（runner 端 _wait_for_prefetch + 同步 miss 兜底）。"""
    try:
        route = _build_route(conn_type, conn_id)
    except Exception:
        # 路由不合法：主进程已在 main 阶段落 route-only meta，此处直接放弃取数；
        # 主进程已写的 pending 需要清掉，避免 runner _wait_for_prefetch 空转到超时。
        _clear_pending(table, DEFAULT_LIMIT)
        return
    sql = _build_fetch_sql(table, conn_type, DEFAULT_LIMIT)
    if _cache_already_hit(table, DEFAULT_LIMIT):
        _store_route_meta(
            table, conn_type, conn_id,
            route["sql_type"], route["data_source_id"], DEFAULT_LIMIT,
        )
        # 主进程已在 main 阶段写了 pending 占位（消除 fork 竞态），
        # 缓存命中后必须清掉，否则 runner _wait_for_prefetch 会一直短轮询到超时。
        _clear_pending(table, DEFAULT_LIMIT)
        return

    _write_pending(table, DEFAULT_LIMIT)
    try:
        compute_resource = _default_analysis_resource_id() if int(route.get("sql_type") or 1) != 3 else ""
        got = client.query(
            sql,
            route["sql_type"],
            route["data_source_id"],
            compute_resource=compute_resource,
            total_timeout=FETCH_TOTAL_TIMEOUT,
        )
        csv_path = got.get("csv_path") or ""
        if csv_path:
            _store_cache(
                table=table,
                csv_path=csv_path,
                sql=sql,
                limit=DEFAULT_LIMIT,
                conn_type=conn_type,
                conn_id=conn_id,
                sql_type=route["sql_type"],
                job_id=got.get("job_id") or got.get("task_id") or "",
                resource_id=got.get("resource_id") or "",
            )
    except Exception:
        return
    finally:
        _clear_pending(table, DEFAULT_LIMIT)


def _bg_fetch_all(triples: list) -> None:
    """N 张表整体并行预取。triples = [(full_name, conn_type, conn_id), ...]"""
    valid = [(t, ct, ci) for t, ct, ci in triples if t]
    if not valid:
        return

    client = _SqlQueryClient()
    # wedatacli 不可用时直接放弃 —— runner 端会同步兜底；同时清理主进程预写 pending，避免空等。
    if not client.available:
        for t, _ct, _ci in valid:
            _clear_pending(t, DEFAULT_LIMIT)
        return

    if len(valid) == 1:
        try:
            _bg_fetch_one(valid[0][0], valid[0][1], valid[0][2], client)
        except Exception:
            pass
        return

    max_workers = min(len(valid), 4)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_bg_fetch_one, t, ct, ci, client) for t, ct, ci in valid]
        for f in futs:
            try:
                f.result()
            except Exception:
                continue


def _spawn_background(triples: list) -> None:
    """double-fork 让后台进程脱离当前会话。主进程立即返回。

    ⚠️ fd 重定向必须在**一代子进程**中先做，而不是等孙进程再做，否则会
    出现"IDE 对话卡住"：主进程 return 后，孙进程仍然继承着从主进程带下
    来的 fd 1（IDE 管道写端副本）；只要孙进程在调用 dup2 之前有任何耗时
    （比如 _bg_fetch_all → _SqlQueryClient() 探测、subprocess.run 起
    wedatacli query-sql 等），IDE 侧 read() 就一直等不到 EOF，用户会看到
    命令一直"没有返回"。本地实测：孙进程 dup2 前 sleep 3s → IDE 卡 3s；
    换成一代子先 dup2 → IDE 立即 EOF。
    """
    if not triples:
        return

    # 主进程：flush 缓冲区，防止 fork 后 double-write（保险，非致命）
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass

    if os.fork() != 0:
        return  # 主进程立即返回

    # === 一代子进程 ===
    # ⭐ 立刻切断 IDE 管道 —— 一代子仍持有从主进程继承的 fd 0/1/2 副本，
    # 若拖到孙进程再 dup2，IDE 会因管道未 EOF 而挂等（详见函数 docstring）。
    try:
        _dn_r = os.open(os.devnull, os.O_RDONLY)
        _dn_w = os.open(os.devnull, os.O_WRONLY)
        os.dup2(_dn_r, 0)
        os.dup2(_dn_w, 1)
        os.dup2(_dn_w, 2)
        if _dn_r > 2:
            os.close(_dn_r)
        if _dn_w > 2:
            os.close(_dn_w)
    except Exception:
        # dup2 失败必须立即退出，否则一代子仍持有 IDE fd →
        # fork 出的孙进程也会继承 → 卡住主对话。
        os._exit(1)

    try:
        os.setsid()
    except Exception:
        pass

    if os.fork() != 0:
        os._exit(0)  # 让孙进程被 init 收养

    # === 孙进程 ===
    # fd 0/1/2 已从一代子继承为 /dev/null，无需再重定向；也无需再关心 IDE 管道
    try:
        _bg_fetch_all(triples)
    except Exception:
        pass
    finally:
        os._exit(0)


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="表名解析 + Schema 同步获取 + 后台预取 CSV（wedatacli query-sql，lakehouse + OLAP 双路径）",
    )
    parser.add_argument(
        "--tables", required=True,
        help="支持三段式 catalog.schema.table / 中文表名 / 英文裸名 / 多意图（、，,和与以及 分隔）",
    )
    parser.add_argument(
        "--top", type=int, default=1,
        help="最多获取前 N 张表（默认 1）",
    )
    parser.add_argument(
        "--bg-prefetch", action="store_true", default=True,
        help="同步打印 schema 后，后台 fork 跑 wedatacli query-sql 取数写入缓存（默认开启）",
    )
    parser.add_argument(
        "--no-bg-prefetch", action="store_false", dest="bg_prefetch",
        help="禁用后台预取（仅打印 schema）",
    )
    args = parser.parse_args()

    # ① 解析表名 → [(full_name, conn_type, conn_id), ...]，跑过单源闸门
    triples = _resolve_tables(args.tables)
    table_names = [t[0] for t in triples]

    # ① bis. 路由硬校验：主进程直接暴露不可执行路由，避免后台吞错后 runner 误走 lakehouse。
    route_errors = []
    routes = {}
    for fn, ct, ci in triples:
        try:
            route = _build_route(ct, ci)
            routes[fn] = route
        except Exception as ex:
            route_errors.append({
                "table": fn,
                "conn_type": _canonical_conn_type(ct),
                "error": str(ex),
            })
    if route_errors:
        print(json.dumps({
            "status": "route_invalid",
            "tables": route_errors,
            "hint": "表路由信息不可执行；请确认表已在 WeData 数据源中正确注册",
        }, ensure_ascii=False))
        sys.stdout.flush()
        sys.exit(EXIT_DISAMBIGUATION)

    # ① ter. 先落 route-only meta：即使后台预取失败/未完成，runner 同步兜底也能正确走 OLAP。
    for fn, ct, ci in triples:
        route = routes.get(fn) or _build_route(ct, ci)
        _store_route_meta(
            fn, ct, ci,
            route["sql_type"], route["data_source_id"], DEFAULT_LIMIT,
        )

    # ② 同步拉 schema（并行 N 张表，~max(单表)耗时）
    effective_top = max(int(args.top or 1), len(table_names))
    schema = _fetch_schema_sync(table_names, effective_top)

    # ②bis. 追加 route_hint 到 schema JSON：
    #   - LLM 必看，见 SKILL.md P0-15 与 Step B「数据源路由」小节
    #   - sql_type=1 lakehouse：LLM 无感知，走原 DSL 流程
    #   - sql_type=3 OLAP    ：LLM 必须走 raw_sql + 目标方言，禁 spark_safe_* / percentile_approx / 三段式表名
    # 单源约束下所有表同源，取任一 triple 的路由即可代表整个 schema。
    try:
        _first_ct = triples[0][1] if triples else ''
        _first_ci = triples[0][2] if triples else ''
        _first_route = routes.get(triples[0][0]) if triples else None
        if _first_route is None and triples:
            _first_route = _build_route(_first_ct, _first_ci)
        if _first_route:
            schema["route_hint"] = {
                "sql_type": int(_first_route.get("sql_type") or 1),
                "connection_type": (_first_ct or "").upper() or "SPARK",
            }
    except Exception:
        # route_hint 是增量提示；解析失败静默降级为 lakehouse 语义（LLM 走原路径）
        schema["route_hint"] = {"sql_type": 1, "connection_type": "SPARK"}

    print(json.dumps(schema, ensure_ascii=False, indent=2))
    sys.stdout.flush()

    # ④ 主进程内**先**写 pending 占位（消除"LLM 写 spec 太快、prefetch 还没 fork 完"竞态），
    #    再 double-fork 让后台 wedatacli query-sql 整体并行；
    #    若 wedatacli 不可用则只跳过后台预取，route-only meta 已保证 runner 同步兜底可用。
    if args.bg_prefetch:
        try:
            probe = _SqlQueryClient()
            if probe.available:
                for tbl, _ct, _ci in triples:
                    if not _cache_already_hit(tbl, DEFAULT_LIMIT):
                        _write_pending(tbl, DEFAULT_LIMIT)
                _spawn_background(triples)
        except Exception:
            pass


if __name__ == "__main__":
    main()