#!/usr/bin/env python3
"""
project-index SQLite 数据库管理工具

跨平台：Python3 内置 sqlite3 模块，macOS / Windows / Linux 通用，零外部依赖。

用途：
  1. init         — 初始化本次扫描的索引数据库
  2. write        — 写入索引数据（支持增量追加）
  3. query        — 结构化查询（供下游 Agent 按需读取）
  4. memory-sync  — 将本次扫描结果同步到长期记忆库（含项目结构快照）
  5. update-sinks — 将 AST 精化结果回写到 sinks 表
  6. save-preferences — 保存扫描配置到长期记忆库

存储位置：
  - 本次扫描索引：.codebuddy/security-scan/runs/{batch}/project-index.db
  - 长期记忆库：  .codebuddy/security-scan/memory/project-memory.db
    含：项目结构缓存、已知 Sink/防御/findings、扫描历史、用户偏好

设计原则：
  - 替代 project-index.json，解决大 JSON 文件的全量读写问题
  - 增量写入原子性（SQLite 事务保障）
  - 按需查询（Agent 只查自己需要的表/字段，节省 token）
  - 长期记忆跨扫描复用（已知 Sink、历史 findings、项目元数据）
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import (
    get_memory_db_path,
    get_legacy_memory_db_path,
    resolve_project_root_from_batch_dir,
)


# ─── Schema 定义 ───────────────────────────────────────────

SCHEMA_VERSION = "3.2"

# 本次扫描的索引数据库 Schema
INDEX_SCHEMA = """
-- 项目元数据
CREATE TABLE IF NOT EXISTS project_meta (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 源文件清单
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT NOT NULL UNIQUE,
    language    TEXT,
    lines       INTEGER DEFAULT 0,
    is_entry    INTEGER DEFAULT 0,       -- 1=入口点文件
    is_large    INTEGER DEFAULT 0,       -- 1=大文件(>500行)
    category    TEXT                      -- controller/service/dao/config/test/other
);

-- 端点（API endpoint）
CREATE TABLE IF NOT EXISTS endpoints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path   TEXT NOT NULL,
    method      TEXT,                    -- GET/POST/PUT/DELETE
    path        TEXT,                    -- URL path
    handler     TEXT,                    -- handler函数名
    line        INTEGER,
    auth_type   TEXT,                    -- none/basic/token/session/oauth
    permissions TEXT,                    -- JSON array of permission annotations
    priority    TEXT DEFAULT 'P2'        -- P0/P1/P2/P3
);

-- Sink 位置（危险操作点）
CREATE TABLE IF NOT EXISTS sinks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,
    line            INTEGER NOT NULL,
    type            TEXT NOT NULL,        -- sql-injection/command-injection/ssrf/...
    severity_level  INTEGER DEFAULT 2,    -- 1=critical, 2=high, 3=medium, 4=low
    code_snippet    TEXT,
    incoming_callers TEXT,                -- JSON array (LSP Phase 2 填充)
    defense_status  TEXT DEFAULT 'unknown', -- unknown/defended/undefended
    trace_status    TEXT DEFAULT 'pending', -- pending/traced/skipped
    -- AST 精化字段（indexer-步骤2 refine-sinks 回写）
    ast_verified    INTEGER DEFAULT NULL,  -- 0/1：AST 确认为真 Sink
    enclosing_func  TEXT,                  -- 包围函数名
    func_range_start INTEGER,              -- 函数起始行
    func_range_end  INTEGER,               -- 函数结束行
    call_expression TEXT,                  -- 完整调用表达式
    param_variables TEXT,                  -- 可控参数变量名（CSV）
    parser_engine   TEXT,                  -- tree-sitter / regex-fallback
    -- v3.2 脚本预筛 ledger（Fast 模式 prescreen-sinks 子命令回写）
    disposition     TEXT DEFAULT 'pending', -- pending / escalated / not_applicable
    disposition_reason TEXT                 -- test_path / literal_arg / inline_parameterized
);
-- 调用图边（caller → callee）
CREATE TABLE IF NOT EXISTS call_graph (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_file TEXT NOT NULL,
    caller_func TEXT NOT NULL,
    caller_line INTEGER,
    callee_file TEXT NOT NULL,
    callee_func TEXT NOT NULL,
    callee_line INTEGER,
    depth       INTEGER DEFAULT 1,
    source      TEXT DEFAULT 'lsp'       -- lsp/grep/inferred
);

-- 攻击面映射
CREATE TABLE IF NOT EXISTS attack_surface (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,            -- file-upload/websocket/cron/mq/rpc/graphql
    file_path   TEXT NOT NULL,
    line        INTEGER,
    detail      TEXT
);

-- 防御映射
CREATE TABLE IF NOT EXISTS defenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,            -- framework/global-filter/infrastructure/local
    name        TEXT NOT NULL,
    file_path   TEXT,
    line        INTEGER,
    scope       TEXT,                     -- global/package/file/method
    detail      TEXT
);

-- 框架桥接映射
CREATE TABLE IF NOT EXISTS framework_bridges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,            -- mybatis-xml/aop/mq/dynamic-proxy
    source_file TEXT,
    target_file TEXT,
    detail      TEXT                      -- JSON: namespace/pointcut/channel 等
);

-- 依赖列表
CREATE TABLE IF NOT EXISTS dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    version         TEXT,
    dep_file        TEXT,                 -- pom.xml/package.json/go.mod/...
    is_security     INTEGER DEFAULT 0,    -- 安全相关依赖
    has_known_cve   INTEGER DEFAULT 0
);

-- 发现（secrets/config/cve，indexer Phase 1 附带产出）
CREATE TABLE IF NOT EXISTS indexer_findings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,            -- secret/config/cve
    severity    TEXT NOT NULL,            -- critical/high/medium/low
    file_path   TEXT,
    line        INTEGER,
    title       TEXT NOT NULL,
    detail      TEXT,
    evidence    TEXT
);

-- 框架行为检测
CREATE TABLE IF NOT EXISTS framework_behaviors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    behavior    TEXT NOT NULL UNIQUE,     -- aop/dynamic-proxy/reflection/mybatis-xml/template-engine/mq
    detected    INTEGER DEFAULT 0,
    files       TEXT                      -- JSON array of file paths
);

-- 阶段状态追踪
CREATE TABLE IF NOT EXISTS phase_status (
    phase       TEXT PRIMARY KEY,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending/in_progress/completed/partial/failed
    started_at  TEXT,
    completed_at TEXT,
    detail      TEXT
);

-- 写入计数器
CREATE TABLE IF NOT EXISTS write_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now')),
    phase       TEXT,
    tables_affected TEXT,                 -- JSON array
    rows_written INTEGER DEFAULT 0
);

-- AST 函数/方法签名（Phase 1.5 ts_parser.py persist 产出，schema 与 ts_parser.py AST_CACHE_SCHEMA 保持一致）
CREATE TABLE IF NOT EXISTS ast_functions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,
    name            TEXT NOT NULL,
    class_name      TEXT,
    params          TEXT,
    return_type     TEXT,
    modifiers       TEXT,
    annotations     TEXT,
    start_line      INTEGER NOT NULL,
    end_line        INTEGER NOT NULL,
    parser_engine   TEXT NOT NULL,
    
    -- 风险信号（供 Sink 优先级排序）
    risk_signals    TEXT,               -- JSON: {"hasDbOp": true, "hasFileOp": true, "hasAuthCheck": false, ...}
    
    UNIQUE(file_path, name, start_line)
);

-- AST 调用表达式（Phase 1.5 ts_parser.py persist 产出，schema 与 ts_parser.py AST_CACHE_SCHEMA 保持一致）
CREATE TABLE IF NOT EXISTS ast_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,
    callee          TEXT NOT NULL,
    receiver        TEXT,
    args            TEXT,
    line            INTEGER NOT NULL,
    full_expression TEXT,
    parser_engine   TEXT NOT NULL,
    UNIQUE(file_path, callee, line)
);

-- AST Sink 精定位结果（Phase 1.5 ts_parser.py refine-sinks 产出，schema 与 ts_parser.py AST_CACHE_SCHEMA 保持一致）
CREATE TABLE IF NOT EXISTS ast_refined_sinks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,
    line            INTEGER NOT NULL,
    ast_verified    INTEGER NOT NULL DEFAULT 0,
    reason          TEXT,
    enclosing_func  TEXT,
    func_range_start INTEGER,
    func_range_end  INTEGER,
    call_expression TEXT,
    param_variables TEXT,
    parser_engine   TEXT NOT NULL,
    UNIQUE(file_path, line)
);

-- AST 文件解析元数据（hash 增量，避免重复解析，schema 与 ts_parser.py AST_CACHE_SCHEMA 保持一致）
CREATE TABLE IF NOT EXISTS ast_parse_meta (
    file_path       TEXT PRIMARY KEY,
    language        TEXT NOT NULL,
    parser_engine   TEXT NOT NULL,
    function_count  INTEGER DEFAULT 0,
    call_count      INTEGER DEFAULT 0,
    parsed_at       TEXT NOT NULL,
    file_hash       TEXT
);

-- 云资源访问流（pattern_grep.py grep-cloud-resource-flow 产出）
-- 用于检测「用户可控资源描述符 + CAM/COS sink + 分支级 STS 缺失」三元组
-- 每条记录代表一个 CAM/COS sink callsite + 其 ±15 行窗口的信号汇总
CREATE TABLE IF NOT EXISTS cloud_resource_flow (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path           TEXT NOT NULL,
    line                INTEGER NOT NULL,
    sink_type           TEXT NOT NULL,           -- e.g. "cam_sig_auth" / "cos_object_op" / "ci_internal_forward"
    sink_snippet        TEXT,                    -- sink 行原文（截断 200）
    has_controllable    INTEGER NOT NULL DEFAULT 0,  -- 1=窗口内出现 controllable_signals.param_names ∩ source_markers
    controllable_hits   TEXT,                    -- 命中关键字 JSON 数组
    has_branch_sts      INTEGER NOT NULL DEFAULT 0,  -- 1=窗口内出现 sts_signals.defense_keywords
    branch_sts_hits     TEXT,                    -- 命中关键字 JSON 数组
    has_resource_scope  INTEGER NOT NULL DEFAULT 0,  -- 1=窗口内出现 sts_signals.resource_scope_patterns
    resource_scope_hits TEXT,                    -- 命中关键字 JSON 数组
    has_config_family   INTEGER NOT NULL DEFAULT 0,  -- 1=同文件出现 sts_signals.defense_config_families（文件级而非窗口级）
    config_family_hits  TEXT,                    -- 命中配置族 JSON 数组
    window_start        INTEGER,                 -- 窗口起始行（max(1, line-15)）
    window_end          INTEGER,                 -- 窗口结束行（line+15）
    -- v3.4 分支级判定字段（旧 batch 由 pattern_grep ALTER 兼容）
    branch_kind         TEXT,
    branch_anchor_line  INTEGER,
    branch_anchor_text  TEXT,
    branch_lower        INTEGER,
    branch_upper        INTEGER,
    is_branch_only_auth_no_sts INTEGER NOT NULL DEFAULT 0,
    -- v3.6 auth-element-incomplete 字段
    has_signature_func        INTEGER NOT NULL DEFAULT 0,
    signature_func_hits       TEXT,
    has_auth_identity_missing INTEGER NOT NULL DEFAULT 0,
    auth_identity_hits        TEXT,
    auth_signed_material_hits TEXT,
    auth_header_source_hits   TEXT,
    has_auth_defense          INTEGER NOT NULL DEFAULT 0,
    auth_defense_hits         TEXT,
    is_auth_element_incomplete INTEGER NOT NULL DEFAULT 0,
    UNIQUE(file_path, line, sink_type)
);

-- 创建常用索引
CREATE INDEX IF NOT EXISTS idx_sinks_type ON sinks(type);
CREATE INDEX IF NOT EXISTS idx_sinks_severity ON sinks(severity_level);
CREATE INDEX IF NOT EXISTS idx_sinks_trace ON sinks(trace_status);
CREATE INDEX IF NOT EXISTS idx_files_entry ON files(is_entry);
CREATE INDEX IF NOT EXISTS idx_endpoints_auth ON endpoints(auth_type);
CREATE INDEX IF NOT EXISTS idx_endpoints_priority ON endpoints(priority);
CREATE INDEX IF NOT EXISTS idx_call_graph_caller ON call_graph(caller_file, caller_func);
CREATE INDEX IF NOT EXISTS idx_call_graph_callee ON call_graph(callee_file, callee_func);
CREATE INDEX IF NOT EXISTS idx_defenses_type ON defenses(type);
CREATE INDEX IF NOT EXISTS idx_indexer_findings_type ON indexer_findings(type);
CREATE INDEX IF NOT EXISTS idx_ast_functions_file ON ast_functions(file_path);
CREATE INDEX IF NOT EXISTS idx_ast_calls_file ON ast_calls(file_path);
CREATE INDEX IF NOT EXISTS idx_ast_calls_callee ON ast_calls(callee);
CREATE INDEX IF NOT EXISTS idx_ast_refined_sinks_file ON ast_refined_sinks(file_path);
CREATE INDEX IF NOT EXISTS idx_cloud_flow_file ON cloud_resource_flow(file_path);
CREATE INDEX IF NOT EXISTS idx_cloud_flow_orphan ON cloud_resource_flow(has_controllable, has_branch_sts, has_resource_scope);
"""

# 长期记忆库 Schema
MEMORY_SCHEMA = """
-- 项目指纹（识别同一项目的不同扫描）
CREATE TABLE IF NOT EXISTS project_fingerprint (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    framework       TEXT,
    file_count      INTEGER,
    total_lines     INTEGER,
    first_scan_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_scan_at    TEXT NOT NULL DEFAULT (datetime('now')),
    scan_count      INTEGER DEFAULT 1
);

-- 历史扫描记录
CREATE TABLE IF NOT EXISTS scan_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id        TEXT NOT NULL UNIQUE,
    project_path    TEXT NOT NULL,
    scan_mode       TEXT,                 -- deep/light/fast
    started_at      TEXT NOT NULL,
    completed_at    TEXT,
    total_findings  INTEGER DEFAULT 0,
    by_severity     TEXT,                 -- JSON: {critical:n, high:n, ...}
    status          TEXT DEFAULT 'in_progress',
    index_db_path   TEXT                  -- 指向本次扫描的 project-index.db
);

-- 已知 Sink 历史（跨扫描复用，加速索引构建）
CREATE TABLE IF NOT EXISTS known_sinks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    line            INTEGER NOT NULL,
    type            TEXT NOT NULL,
    severity_level  INTEGER DEFAULT 2,
    first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),
    times_seen      INTEGER DEFAULT 1,
    last_status     TEXT DEFAULT 'unknown', -- unknown/defended/undefended/false_positive
    -- AST 精化字段（v3.1 新增，跨扫描复用避免重复精化）
    ast_verified    INTEGER,              -- 0/1：AST 确认为真 Sink
    enclosing_func  TEXT,                 -- 包围函数名
    func_range_start INTEGER,             -- 函数起始行
    func_range_end  INTEGER,              -- 函数结束行
    call_expression TEXT,                 -- 完整调用表达式
    param_variables TEXT,                 -- 可控参数变量名（CSV）
    parser_engine   TEXT,                 -- tree-sitter / regex-fallback
    content_hash    TEXT,                 -- 关联文件 hash（判断精化结果是否过期）
    stale           INTEGER DEFAULT 0,    -- 1=上次扫描未确认（文件可能已删除）
    UNIQUE(project_path, file_path, line, type)
);

-- 已知防御模式（跨扫描复用）
CREATE TABLE IF NOT EXISTS known_defenses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    type            TEXT NOT NULL,
    name            TEXT NOT NULL,
    scope           TEXT,
    first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),
    last_confirmed  TEXT,                  -- 最后一次被当前扫描确认存在的时间，NULL 表示上次扫描未确认
    stale           INTEGER DEFAULT 0,     -- 1=上次扫描未确认（可能已被删除）
    UNIQUE(project_path, type, name)
);

-- 历史 findings（高置信度的真实漏洞，供后续扫描参考）
CREATE TABLE IF NOT EXISTS known_findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    batch_id        TEXT NOT NULL,
    finding_type    TEXT NOT NULL,
    severity        TEXT NOT NULL,
    file_path       TEXT,
    line            INTEGER,
    title           TEXT NOT NULL,
    confidence      INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'open',  -- open/fixed/false_positive/accepted
    first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),
    times_seen      INTEGER DEFAULT 1,
    UNIQUE(project_path, finding_type, file_path, line)
);

-- 项目结构快照（跨扫描复用，加速步骤 1 枚举）
CREATE TABLE IF NOT EXISTS project_structure (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    language        TEXT,
    lines           INTEGER DEFAULT 0,
    is_entry        INTEGER DEFAULT 0,
    category        TEXT,
    content_hash    TEXT,                 -- 文件内容 SHA256（增量判断）
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_path, file_path)
);

-- 项目结构元数据（技术栈、框架、构建工具等）
CREATE TABLE IF NOT EXISTS project_structure_meta (
    project_path    TEXT NOT NULL,
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY(project_path, key)
);

-- 用户扫描偏好（排除目录、默认模式等）
CREATE TABLE IF NOT EXISTS user_preferences (
    project_path    TEXT NOT NULL,
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY(project_path, key)
);

-- 跨扫描 AST 函数签名缓存
CREATE TABLE IF NOT EXISTS cached_ast_functions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    name            TEXT NOT NULL,
    class_name      TEXT,
    params          TEXT,
    return_type     TEXT,
    modifiers       TEXT,
    annotations     TEXT,
    start_line      INTEGER,
    end_line        INTEGER,
    parser_engine   TEXT,
    risk_signals    TEXT,
    UNIQUE(project_path, file_path, name, start_line)
);

-- 跨扫描 AST 调用表达式缓存
CREATE TABLE IF NOT EXISTS cached_ast_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    callee          TEXT NOT NULL,
    receiver        TEXT,
    args            TEXT,
    line            INTEGER,
    full_expression TEXT,
    parser_engine   TEXT,
    UNIQUE(project_path, file_path, callee, line)
);

-- 跨扫描端点缓存
CREATE TABLE IF NOT EXISTS cached_endpoints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    method          TEXT,
    path            TEXT,
    handler         TEXT,
    line            INTEGER,
    auth_type       TEXT,
    permissions     TEXT,
    priority        TEXT,
    UNIQUE(project_path, file_path, handler)
);

-- 跨扫描调用图缓存
CREATE TABLE IF NOT EXISTS cached_call_graph (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    caller_file     TEXT NOT NULL,
    caller_file_hash TEXT NOT NULL,
    caller_func     TEXT NOT NULL,
    callee_file     TEXT NOT NULL,
    callee_func     TEXT NOT NULL,
    depth           INTEGER,
    source          TEXT DEFAULT 'lsp',
    UNIQUE(project_path, caller_file, caller_func, callee_file, callee_func)
);

-- 跨扫描 AST Sink 精化结果缓存（v3.1 新增）
CREATE TABLE IF NOT EXISTS cached_ast_refined_sinks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    line            INTEGER NOT NULL,
    ast_verified    INTEGER NOT NULL DEFAULT 0,
    reason          TEXT,
    enclosing_func  TEXT,
    func_range_start INTEGER,
    func_range_end  INTEGER,
    call_expression TEXT,
    param_variables TEXT,
    parser_engine   TEXT NOT NULL,
    UNIQUE(project_path, file_path, line)
);

-- 项目技术栈（v3.1 新增，结构化存储多框架/多语言信息）
CREATE TABLE IF NOT EXISTS project_tech_stack (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path    TEXT NOT NULL,
    category        TEXT NOT NULL,        -- framework/language/build_tool
    name            TEXT NOT NULL,         -- spring-boot/java/maven
    version         TEXT,                  -- 检测到的版本（如有）
    is_primary      INTEGER DEFAULT 0,    -- 1=主要技术栈
    confidence      TEXT DEFAULT 'high',  -- high/medium/low
    detected_by     TEXT,                  -- marker-file/content-pattern/dependency
    first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(project_path, category, name)
);

CREATE INDEX IF NOT EXISTS idx_known_sinks_project ON known_sinks(project_path);
CREATE INDEX IF NOT EXISTS idx_known_sinks_stale ON known_sinks(project_path, stale);
CREATE INDEX IF NOT EXISTS idx_scan_history_project ON scan_history(project_path);
CREATE INDEX IF NOT EXISTS idx_known_findings_project ON known_findings(project_path);
CREATE INDEX IF NOT EXISTS idx_project_structure_project ON project_structure(project_path);
CREATE INDEX IF NOT EXISTS idx_project_structure_entry ON project_structure(project_path, is_entry);
CREATE INDEX IF NOT EXISTS idx_cached_ast_functions_hash ON cached_ast_functions(project_path, file_hash);
CREATE INDEX IF NOT EXISTS idx_cached_ast_calls_hash ON cached_ast_calls(project_path, file_hash);
CREATE INDEX IF NOT EXISTS idx_cached_endpoints_hash ON cached_endpoints(project_path, file_hash);
CREATE INDEX IF NOT EXISTS idx_cached_call_graph_project ON cached_call_graph(project_path, caller_file);
CREATE INDEX IF NOT EXISTS idx_cached_refined_sinks_hash ON cached_ast_refined_sinks(project_path, file_hash);
CREATE INDEX IF NOT EXISTS idx_tech_stack_project ON project_tech_stack(project_path);
"""


# ─── 工具函数 ───────────────────────────────────────────────

def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect(db_path, readonly=False):
    """创建数据库连接，设置 WAL 模式提高并发性能"""
    if readonly and not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found: {db_path}"}))
        sys.exit(1)
    
    uri = f"file:{db_path}"
    if readonly:
        uri += "?mode=ro"
    
    conn = sqlite3.connect(uri if readonly else db_path, uri=readonly)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def _log_write(conn, phase, tables, row_count):
    """记录写入日志"""
    conn.execute(
        "INSERT INTO write_log (timestamp, phase, tables_affected, rows_written) VALUES (?, ?, ?, ?)",
        (_now_iso(), phase, json.dumps(tables), row_count)
    )


def _migrate_memory_schema(conn):
    """Schema 迁移：为旧版 DB 增加 v3.1 新增字段/表/索引（幂等，多次调用安全）"""
    # known_sinks 新增字段
    _add_column_if_missing(conn, "known_sinks", "ast_verified", "INTEGER")
    _add_column_if_missing(conn, "known_sinks", "enclosing_func", "TEXT")
    _add_column_if_missing(conn, "known_sinks", "func_range_start", "INTEGER")
    _add_column_if_missing(conn, "known_sinks", "func_range_end", "INTEGER")
    _add_column_if_missing(conn, "known_sinks", "call_expression", "TEXT")
    _add_column_if_missing(conn, "known_sinks", "param_variables", "TEXT")
    _add_column_if_missing(conn, "known_sinks", "parser_engine", "TEXT")
    _add_column_if_missing(conn, "known_sinks", "content_hash", "TEXT")
    _add_column_if_missing(conn, "known_sinks", "stale", "INTEGER DEFAULT 0")
    
    # v3.1 新增表（IF NOT EXISTS 保证幂等）
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cached_ast_refined_sinks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_path    TEXT NOT NULL,
            file_path       TEXT NOT NULL,
            file_hash       TEXT NOT NULL,
            line            INTEGER NOT NULL,
            ast_verified    INTEGER NOT NULL DEFAULT 0,
            reason          TEXT,
            enclosing_func  TEXT,
            func_range_start INTEGER,
            func_range_end  INTEGER,
            call_expression TEXT,
            param_variables TEXT,
            parser_engine   TEXT NOT NULL,
            UNIQUE(project_path, file_path, line)
        );
        
        CREATE TABLE IF NOT EXISTS project_tech_stack (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_path    TEXT NOT NULL,
            category        TEXT NOT NULL,
            name            TEXT NOT NULL,
            version         TEXT,
            is_primary      INTEGER DEFAULT 0,
            confidence      TEXT DEFAULT 'high',
            detected_by     TEXT,
            first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
            last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(project_path, category, name)
        );
        
        CREATE INDEX IF NOT EXISTS idx_known_sinks_stale ON known_sinks(project_path, stale);
        CREATE INDEX IF NOT EXISTS idx_cached_refined_sinks_hash ON cached_ast_refined_sinks(project_path, file_hash);
        CREATE INDEX IF NOT EXISTS idx_tech_stack_project ON project_tech_stack(project_path);
    """)


def _migrate_index_schema(conn):
    """Schema 迁移：为旧版 index DB 补齐 v3.2 新增列/索引。"""
    _add_column_if_missing(conn, "sinks", "disposition", "TEXT DEFAULT 'pending'")
    _add_column_if_missing(conn, "sinks", "disposition_reason", "TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sinks_disposition ON sinks(disposition)")
    # v3.3：新增 cloud_resource_flow 表（CAM/COS STS 鉴权缺失三元组）
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS cloud_resource_flow (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path           TEXT NOT NULL,
        line                INTEGER NOT NULL,
        sink_type           TEXT NOT NULL,
        sink_snippet        TEXT,
        has_controllable    INTEGER NOT NULL DEFAULT 0,
        controllable_hits   TEXT,
        has_branch_sts      INTEGER NOT NULL DEFAULT 0,
        branch_sts_hits     TEXT,
        has_resource_scope  INTEGER NOT NULL DEFAULT 0,
        resource_scope_hits TEXT,
        has_config_family   INTEGER NOT NULL DEFAULT 0,
        config_family_hits  TEXT,
        window_start        INTEGER,
        window_end          INTEGER,
        UNIQUE(file_path, line, sink_type)
    );
    CREATE INDEX IF NOT EXISTS idx_cloud_flow_file ON cloud_resource_flow(file_path);
    CREATE INDEX IF NOT EXISTS idx_cloud_flow_orphan ON cloud_resource_flow(has_controllable, has_branch_sts, has_resource_scope);
    """)
    # v3.4 / v3.6 列迁移：旧 batch 通过 _add_column_if_missing 兼容
    for col_name, col_type in (
        ("branch_kind", "TEXT"),
        ("branch_anchor_line", "INTEGER"),
        ("branch_anchor_text", "TEXT"),
        ("branch_lower", "INTEGER"),
        ("branch_upper", "INTEGER"),
        ("is_branch_only_auth_no_sts", "INTEGER NOT NULL DEFAULT 0"),
        ("has_signature_func", "INTEGER NOT NULL DEFAULT 0"),
        ("signature_func_hits", "TEXT"),
        ("has_auth_identity_missing", "INTEGER NOT NULL DEFAULT 0"),
        ("auth_identity_hits", "TEXT"),
        ("auth_signed_material_hits", "TEXT"),
        ("auth_header_source_hits", "TEXT"),
        ("has_auth_defense", "INTEGER NOT NULL DEFAULT 0"),
        ("auth_defense_hits", "TEXT"),
        ("is_auth_element_incomplete", "INTEGER NOT NULL DEFAULT 0"),
    ):
        _add_column_if_missing(conn, "cloud_resource_flow", col_name, col_type)


def _add_column_if_missing(conn, table, column, col_type):
    """安全地为表添加列（如果列已存在则忽略）"""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass  # 列已存在，忽略


def _project_root_for_memory(args):
    project_path = getattr(args, "project_path", None)
    if project_path:
        return str(Path(project_path))
    return str(resolve_project_root_from_batch_dir(Path(args.batch_dir)))


def _memory_db_has_project_data(memory_db, project_path):
    """判断记忆库中是否已有当前项目数据。"""
    if not memory_db.exists():
        return False
    try:
        conn = _connect(str(memory_db), readonly=True)
        try:
            for table in (
                "scan_history",
                "known_sinks",
                "known_findings",
                "known_defenses",
                "project_structure",
                "project_tech_stack",
                "user_preferences",
            ):
                try:
                    count = conn.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE project_path=?",
                        (project_path,),
                    ).fetchone()[0]
                    if count:
                        return True
                except sqlite3.Error:
                    continue
        finally:
            conn.close()
    except sqlite3.Error:
        return False
    return False


def _memory_db_path(args, readonly=False):
    """返回长期记忆库路径；读路径保留旧库 fallback，写路径统一使用 .codebuddy。"""
    new_path = get_memory_db_path(_project_root_for_memory(args))
    if readonly:
        project_path = getattr(args, 'project_path', None) or os.getcwd()
        legacy_path = get_legacy_memory_db_path(args.batch_dir)
        if legacy_path.exists() and not _memory_db_has_project_data(new_path, project_path):
            return legacy_path
    return new_path


# ─── 命令: init ────────────────────────────────────────────

def cmd_init(args):
    """初始化索引数据库 + 长期记忆库"""
    batch_dir = Path(args.batch_dir)
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 初始化本次扫描的索引 DB
    index_db_path = batch_dir / "project-index.db"
    conn = _connect(str(index_db_path))
    conn.executescript(INDEX_SCHEMA)
    _migrate_index_schema(conn)
    
    # 写入版本信息
    conn.execute(
        "INSERT OR REPLACE INTO project_meta (key, value, updated_at) VALUES (?, ?, ?)",
        ("schema_version", SCHEMA_VERSION, _now_iso())
    )
    conn.execute(
        "INSERT OR REPLACE INTO project_meta (key, value, updated_at) VALUES (?, ?, ?)",
        ("batch_id", args.batch_id or batch_dir.name, _now_iso())
    )
    conn.execute(
        "INSERT OR REPLACE INTO project_meta (key, value, updated_at) VALUES (?, ?, ?)",
        ("created_at", _now_iso(), _now_iso())
    )
    
    # 初始化阶段状态
    for phase in ["phase1", "phase1_5", "phase2"]:
        conn.execute(
            "INSERT OR IGNORE INTO phase_status (phase, status) VALUES (?, 'pending')",
            (phase,)
        )
    
    conn.commit()
    conn.close()
    
    # 2. 初始化长期记忆库（在 .codebuddy/security-scan/memory/ 下）
    memory_db_path = _memory_db_path(args)
    memory_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    mem_conn = _connect(str(memory_db_path))
    mem_conn.executescript(MEMORY_SCHEMA)
    # Schema 迁移：为旧版 DB 增加 v3.1 新增字段（ALTER TABLE 幂等）
    _migrate_memory_schema(mem_conn)
    mem_conn.commit()
    mem_conn.close()
    
    result = {
        "status": "initialized",
        "index_db": str(index_db_path),
        "memory_db": str(memory_db_path),
        "schema_version": SCHEMA_VERSION
    }
    print(json.dumps(result))


# ─── 命令: write ───────────────────────────────────────────

def cmd_write(args):
    """
    增量写入索引数据。从 stdin 或 --data 读取 JSON。
    
    JSON 格式：
    {
      "phase": "phase1",              // 当前阶段
      "table": "sinks",               // 目标表名
      "rows": [{ ... }, { ... }],     // 要写入的行
      "meta": { "key": "value" }      // 可选：project_meta 更新
    }
    """
    db_path = _resolve_db_path(args.batch_dir)
    
    if args.data:
        data = json.loads(args.data)
    else:
        data = json.load(sys.stdin)
    
    conn = _connect(db_path)
    total_rows = 0
    tables_affected = []
    
    try:
        # 写入 project_meta
        if "meta" in data:
            for k, v in data["meta"].items():
                conn.execute(
                    "INSERT OR REPLACE INTO project_meta (key, value, updated_at) VALUES (?, ?, ?)",
                    (k, v if isinstance(v, str) else json.dumps(v), _now_iso())
                )
            tables_affected.append("project_meta")
        
        # 写入目标表
        table = data.get("table")
        rows = data.get("rows", [])
        
        if table and rows:
            tables_affected.append(table)
            total_rows = _insert_rows(conn, table, rows)
        
        # 批量写入多表
        if "tables" in data:
            for tbl_name, tbl_rows in data["tables"].items():
                if tbl_rows:
                    tables_affected.append(tbl_name)
                    total_rows += _insert_rows(conn, tbl_name, tbl_rows)
        
        # 更新阶段状态
        phase = data.get("phase")
        phase_status = data.get("phase_status", "in_progress")
        if phase:
            now = _now_iso()
            conn.execute("""
                INSERT OR REPLACE INTO phase_status (phase, status, started_at, completed_at)
                VALUES (?, ?, 
                    COALESCE((SELECT started_at FROM phase_status WHERE phase = ?), ?),
                    CASE WHEN ? IN ('completed', 'partial', 'failed') THEN ? ELSE NULL END
                )
            """, (phase, phase_status, phase, now, phase_status, now))
        
        _log_write(conn, phase or "unknown", tables_affected, total_rows)
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()
    
    result = {
        "status": "written",
        "tables": tables_affected,
        "rows_written": total_rows,
        "phase": phase,
        "phase_status": phase_status
    }
    print(json.dumps(result))


ALLOWED_TABLES = {
    "project_meta", "files", "endpoints", "sinks", "call_graph",
    "attack_surface", "defenses", "framework_bridges", "dependencies",
    "indexer_findings", "framework_behaviors", "phase_status", "write_log",
    "ast_functions", "ast_calls", "ast_refined_sinks", "ast_parse_meta",
    "cloud_resource_flow",
}


def _insert_rows(conn, table, rows):
    """通用行插入（INSERT OR REPLACE）"""
    if not rows:
        return 0
    
    # 白名单验证表名，防止 SQL 注入
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table}. Allowed: {', '.join(sorted(ALLOWED_TABLES))}")
    
    # 获取表的列名
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row["name"] for row in cursor.fetchall()]
    # 排除自增主键
    auto_pk = columns[0] if columns else None  # 通常是 id
    
    count = 0
    for row in rows:
        # 只用 row 中存在的且在表中有效的列
        row_cols = [c for c in columns if c in row]
        if not row_cols:
            continue
        
        placeholders = ", ".join(["?"] * len(row_cols))
        col_names = ", ".join(row_cols)
        values = [row[c] if not isinstance(row[c], (dict, list)) else json.dumps(row[c]) for c in row_cols]
        
        conn.execute(
            f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
            values
        )
        count += 1
    
    return count


# ─── 命令: query ───────────────────────────────────────────

def cmd_query(args):
    """
    结构化查询索引数据库。
    
    预定义查询（--preset）：
      summary          — 项目概况摘要（供编排器使用）
      sinks-by-severity — 按 severity_level 排序的 Sink 列表（供扫描 Agent）
      sinks-untraced   — 未追踪的 Sink（供扫描 Agent 增量扫描）
      sinks-top-per-file — 每文件 Top-K Sink（按 severity_level 裁剪；--limit 控制 K，默认 3；供 Fast 批量三判）
      endpoints-by-priority — 按优先级排序的端点（供扫描 Agent）
      endpoints-noauth — 无认证端点（供扫描 Agent）
      defenses         — 防御映射（供 verifier.py）
      call-graph       — 调用图（供扫描 Agent/verifier.py）
      attack-surface   — 攻击面映射（供扫描 Agent）
      framework-bridges — 框架桥接映射（供扫描 Agent）
      indexer-findings  — indexer 附带发现（供合并）
      defenses-for-file — 指定文件的防御映射（需 --filter-file）
      sinks-untraced-count — 按 severity 统计未追踪 Sink 数量
      phase-status      — 各阶段完成状态
      sinks-incremental — 增量 Sink 查询（id > --limit 值）
      memory-hints     — 长期记忆提示（供 indexer 参考历史）
      cached-structure — 项目结构缓存（供 indexer 跳过未变更文件的枚举）
    
    自定义查询（--sql）：
      直接执行 SQL（仅 SELECT）
    """
    db_path = _resolve_db_path(args.batch_dir)
    conn = _connect(db_path, readonly=True)
    
    try:
        if args.preset:
            result = _preset_query(conn, args.preset, args)
        elif args.sql:
            # 安全检查：仅允许 SELECT
            sql = args.sql.strip()
            if not sql.upper().startswith("SELECT"):
                print(json.dumps({"error": "Only SELECT queries allowed"}))
                sys.exit(1)
            cursor = conn.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()]
            result = {"rows": rows, "count": len(rows)}
        else:
            print(json.dumps({"error": "Specify --preset or --sql"}))
            sys.exit(1)
    finally:
        conn.close()
    
    print(json.dumps(result, ensure_ascii=False))


def _preset_query(conn, preset, args):
    """预定义查询"""
    
    if preset == "summary":
        meta = {}
        for row in conn.execute("SELECT key, value FROM project_meta"):
            meta[row["key"]] = row["value"]
        
        file_count = conn.execute("SELECT COUNT(*) as c FROM files").fetchone()["c"]
        total_lines = conn.execute("SELECT COALESCE(SUM(lines), 0) as s FROM files").fetchone()["s"]
        entry_count = conn.execute("SELECT COUNT(*) as c FROM files WHERE is_entry=1").fetchone()["c"]
        sink_count = conn.execute("SELECT COUNT(*) as c FROM sinks").fetchone()["c"]
        endpoint_count = conn.execute("SELECT COUNT(*) as c FROM endpoints").fetchone()["c"]
        finding_count = conn.execute("SELECT COUNT(*) as c FROM indexer_findings").fetchone()["c"]
        
        function_count = conn.execute("SELECT COUNT(*) as c FROM ast_functions").fetchone()["c"]
        
        phases = {}
        for row in conn.execute("SELECT phase, status FROM phase_status"):
            phases[row["phase"]] = row["status"]
        
        write_count = conn.execute("SELECT COUNT(*) as c FROM write_log").fetchone()["c"]
        
        return {
            "meta": meta,
            "fileCount": file_count,
            "totalLines": total_lines,
            "entryPointFiles": entry_count,
            "sinkCount": sink_count,
            "endpointCount": endpoint_count,
            "indexerFindings": finding_count,
            "functionCount": function_count,
            "phases": phases,
            "writeCount": write_count
        }
    
    elif preset in ("sinks-by-severity",):
        limit = getattr(args, 'limit', None) or 50
        rows = conn.execute(
            "SELECT * FROM sinks ORDER BY severity_level ASC, id ASC LIMIT ?", (limit,)
        ).fetchall()
        return {"sinks": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "sinks-untraced":
        limit = getattr(args, 'limit', None) or 30
        rows = conn.execute(
            "SELECT * FROM sinks WHERE trace_status='pending' ORDER BY severity_level ASC LIMIT ?", (limit,)
        ).fetchall()
        return {"sinks": [dict(r) for r in rows], "count": len(rows)}

    elif preset == "sinks-top-per-file":
        # Fast P0+：每文件 Top-K Sink 裁剪（按 severity_level 优先）
        # 用途：阶段 2 LLM 按 Sink 清单扫描时，避免同文件多个同类型 Sink 导致 LLM 重复 Read/判定
        # 默认 k=3；可通过 --limit 覆盖
        # 排序规则：外层按 file_path 聚合（同文件连续），文件内按 severity_level 优先再 line 升序，
        #   便于 LLM "Read 一个文件 → 对该文件所有 Sink 批量 verdict"
        # v3.2：disposition='not_applicable' 的 Sink（脚本预筛排除）不进 Top-K；
        #   未跑 prescreen-sinks 时所有 Sink 都是 'pending'，行为与旧版本一致
        k = getattr(args, 'limit', None) or 3
        rows = conn.execute("""
            WITH ranked AS (
                SELECT
                    id, file_path, line, type, severity_level, code_snippet,
                    incoming_callers, defense_status, trace_status,
                    ast_verified, enclosing_func, func_range_start, func_range_end,
                    call_expression, param_variables, parser_engine,
                    disposition, disposition_reason,
                    ROW_NUMBER() OVER (
                        PARTITION BY file_path
                        ORDER BY severity_level ASC, line ASC, id ASC
                    ) AS rn,
                    MIN(severity_level) OVER (PARTITION BY file_path) AS file_top_severity
                FROM sinks
                WHERE disposition IN ('pending', 'escalated')
            )
            SELECT
                id, file_path, line, type, severity_level, code_snippet,
                incoming_callers, defense_status, trace_status,
                ast_verified, enclosing_func, func_range_start, func_range_end,
                call_expression, param_variables, parser_engine,
                disposition, disposition_reason
            FROM ranked
            WHERE rn <= ?
            ORDER BY file_top_severity ASC, file_path ASC, severity_level ASC, line ASC
        """, (k,)).fetchall()
        return {"sinks": [dict(r) for r in rows], "count": len(rows), "k_per_file": k}
    
    elif preset == "endpoints-by-priority":
        rows = conn.execute(
            "SELECT * FROM endpoints ORDER BY priority ASC, id ASC"
        ).fetchall()
        return {"endpoints": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "endpoints-noauth":
        rows = conn.execute(
            "SELECT * FROM endpoints WHERE auth_type='none' OR auth_type IS NULL ORDER BY priority ASC"
        ).fetchall()
        return {"endpoints": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "defenses":
        rows = conn.execute("SELECT * FROM defenses ORDER BY scope DESC, type ASC").fetchall()
        return {"defenses": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "call-graph":
        caller = getattr(args, 'filter_file', None)
        if caller:
            rows = conn.execute(
                "SELECT * FROM call_graph WHERE caller_file=? OR callee_file=? ORDER BY depth ASC",
                (caller, caller)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM call_graph ORDER BY depth ASC").fetchall()
        return {"edges": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "indexer-findings":
        rows = conn.execute(
            "SELECT * FROM indexer_findings ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END"
        ).fetchall()
        return {"findings": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "attack-surface":
        rows = conn.execute(
            "SELECT * FROM attack_surface ORDER BY type ASC, id ASC"
        ).fetchall()
        return {"attackSurface": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "framework-bridges":
        rows = conn.execute(
            "SELECT * FROM framework_bridges ORDER BY type ASC, id ASC"
        ).fetchall()
        return {"bridges": [dict(r) for r in rows], "count": len(rows)}
    
    elif preset == "defenses-for-file":
        file_path = getattr(args, 'filter_file', None)
        if not file_path:
            return {"error": "--filter-file required for defenses-for-file"}
        # scope 白名单：当前 pattern_grep.py 写入 'global' / 'method' 两种（见 pattern_grep.py 的
        # defense config["scope"]）；其余 'package' / 'project' / 'framework' 预留给未来扩展——
        # schema 注释标注 scope TEXT -- global/package/file/method。如果 pattern_grep 扩展了新的
        # 全局类 scope，请同步更新此白名单和下面的 ORDER BY 分桶。
        rows = conn.execute("""
            SELECT * FROM defenses
            WHERE file_path = ?
               OR scope IN ('global', 'package', 'project', 'framework')
            ORDER BY
                CASE
                    WHEN file_path = ? THEN 1
                    WHEN scope IN ('package', 'project', 'framework') THEN 2
                    WHEN scope = 'global' THEN 3
                    ELSE 4
                END ASC,
                COALESCE(line, 0) ASC,
                id ASC
        """, (file_path, file_path)).fetchall()
        defenses = [dict(r) for r in rows]
        scope_count = {}
        for defense in defenses:
            scope = defense.get('scope') or 'unknown'
            scope_count[scope] = scope_count.get(scope, 0) + 1
        return {"defenses": defenses, "count": len(defenses), "scopeCount": scope_count}
    
    elif preset == "sinks-untraced-count":
        rows = conn.execute("""
            SELECT severity_level, COUNT(*) as count 
            FROM sinks WHERE trace_status = 'pending' 
            GROUP BY severity_level ORDER BY severity_level ASC
        """).fetchall()
        total = sum(r["count"] for r in rows)
        return {"by_severity": {f"S{r['severity_level']}": r["count"] for r in rows}, "total": total}
    
    elif preset == "phase-status":
        rows = conn.execute(
            "SELECT phase, status, started_at, completed_at, detail FROM phase_status ORDER BY phase"
        ).fetchall()
        return {"phases": {r["phase"]: {"status": r["status"], "started_at": r["started_at"], "completed_at": r["completed_at"]} for r in rows}}
    
    elif preset == "sinks-incremental":
        # 获取自上次查询后新增的 sink (通过 id > last_id)
        last_id = getattr(args, 'limit', None) or 0  # 复用 --limit 参数作为 last_id
        rows = conn.execute(
            "SELECT * FROM sinks WHERE id > ? ORDER BY severity_level ASC, id ASC",
            (last_id,)
        ).fetchall()
        max_id = max((r["id"] for r in rows), default=last_id)
        return {"sinks": [dict(r) for r in rows], "count": len(rows), "max_id": max_id}

    elif preset == "sinks-prescreened-ledger":
        # v3.2 脚本预筛 ledger：返回所有被脚本预筛排除的 Sink，供报告附录展示
        # 仅在执行过 pattern_grep.py prescreen-sinks 之后才会有数据
        rows = conn.execute("""
            SELECT file_path, line, type, severity_level, code_snippet,
                   disposition, disposition_reason
            FROM sinks
            WHERE disposition = 'not_applicable'
            ORDER BY disposition_reason ASC, file_path ASC, line ASC
        """).fetchall()
        # 按 reason 分组统计
        by_reason = {}
        for r in rows:
            reason = r["disposition_reason"] or "unknown"
            by_reason[reason] = by_reason.get(reason, 0) + 1
        return {
            "excluded": [dict(r) for r in rows],
            "count": len(rows),
            "byReason": by_reason,
        }
    
    elif preset == "memory-hints":
        return _memory_hints(args)
    
    elif preset == "cached-structure":
        return _cached_structure(args)
    
    elif preset == "tech-stack-summary":
        return _tech_stack_summary(args)

    elif preset == "cloud-resource-orphans":
        # CAM/COS STS 鉴权缺失检测：返回所有「用户可控 + 分支无 STS + 无资源 scope 收敛」的 sink
        # 由 pattern_grep.py grep-cloud-resource-flow 预筛产出
        # 消费方：light-inline / fast 第 4 判 / logic-scan C3.X 章节
        # 兼容：如果表不存在（旧 batch 未跑新预筛），返回空结果而非报错
        try:
            limit = getattr(args, 'limit', None) or 100
            file_path = getattr(args, 'filter_file', None)
            sql = """
                SELECT id, file_path, line, sink_type, sink_snippet,
                       has_controllable, controllable_hits,
                       has_branch_sts, branch_sts_hits,
                       has_resource_scope, resource_scope_hits,
                       has_config_family, config_family_hits,
                       window_start, window_end
                FROM cloud_resource_flow
                WHERE has_controllable = 1
                  AND has_branch_sts = 0
                  AND has_resource_scope = 0
            """
            params = []
            if file_path:
                sql += " AND file_path = ?"
                params.append(file_path)
            sql += " ORDER BY file_path ASC, line ASC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return {
                "orphans": [dict(r) for r in rows],
                "count": len(rows),
                "criteria": "has_controllable=1 AND has_branch_sts=0 AND has_resource_scope=0",
                "note": "config_family 仅作辅助参考；分支级 STS 缺失即足以触发风险，配置族在文件其他位置出现也不能反驳分支缺失",
            }
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                return {
                    "orphans": [], "count": 0,
                    "warning": "cloud_resource_flow table not present — run `pattern_grep.py grep-cloud-resource-flow` first",
                }
            raise

    elif preset == "auth-element-incomplete-candidates":
        # 认证要素缺失检测：返回所有「签名函数命中 + 身份字段事后消费 + 分支无防御」的 sink
        # 由 pattern_grep.py grep-cloud-resource-flow 预筛产出（is_auth_element_incomplete=1）
        # 消费方：light-inline 第 5 问 / fast 第 5 判 / logic-scan C3.6
        # 兼容：旧 batch 没有相应列时返回空结果（向后兼容）
        try:
            limit = getattr(args, 'limit', None) or 100
            file_path = getattr(args, 'filter_file', None)
            sql = """
                SELECT id, file_path, line, sink_type, sink_snippet,
                       has_controllable, controllable_hits,
                       has_signature_func, signature_func_hits,
                       has_auth_identity_missing, auth_identity_hits,
                       auth_signed_material_hits, auth_header_source_hits,
                       has_auth_defense, auth_defense_hits,
                       has_branch_sts, branch_sts_hits,
                       branch_kind, branch_anchor_line, branch_anchor_text,
                       window_start, window_end
                FROM cloud_resource_flow
                WHERE is_auth_element_incomplete = 1
            """
            params = []
            if file_path:
                sql += " AND file_path = ?"
                params.append(file_path)
            sql += " ORDER BY file_path ASC, line ASC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return {
                "candidates": [dict(r) for r in rows],
                "count": len(rows),
                "criteria": "is_auth_element_incomplete = 1 (签名函数命中 + 身份字段事后消费 + 分支无防御)",
                "note": "verifier 需进一步通过 replay/forge 验证跨租户可达性；确认后允许 severity 升至 critical",
            }
        except sqlite3.OperationalError as e:
            msg = str(e).lower()
            if "no such column" in msg or "no such table" in msg:
                return {
                    "candidates": [], "count": 0,
                    "warning": "is_auth_element_incomplete column not present — run `pattern_grep.py grep-cloud-resource-flow` (>=v3.6) first",
                }
            raise

    else:
        return {"error": f"Unknown preset: {preset}"}


def _tech_stack_summary(args):
    """从长期记忆库获取项目技术栈摘要"""
    memory_db = _memory_db_path(args, readonly=True)
    
    if not memory_db.exists():
        return {"cached": False, "message": "No memory database found"}
    
    project_path = getattr(args, 'project_path', None) or os.getcwd()
    mem_conn = _connect(str(memory_db), readonly=True)
    
    try:
        rows = mem_conn.execute(
            """SELECT category, name, version, is_primary, confidence, detected_by, first_seen_at, last_seen_at
               FROM project_tech_stack WHERE project_path=?
               ORDER BY is_primary DESC, category ASC, name ASC""",
            (project_path,)
        ).fetchall()
        
        if not rows:
            return {"cached": False, "message": "No tech stack data for this project"}
        
        # 按 category 分组
        by_category = {}
        for r in rows:
            cat = r["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(dict(r))
        
        primary_framework = None
        primary_language = None
        for r in rows:
            if r["is_primary"] and r["category"] == "framework":
                primary_framework = r["name"]
            if r["is_primary"] and r["category"] == "language":
                primary_language = r["name"]
        
        return {
            "cached": True,
            "primaryFramework": primary_framework,
            "primaryLanguage": primary_language,
            "byCategory": by_category,
            "totalItems": len(rows),
            "message": f"Tech stack: {primary_framework or 'unknown'} ({primary_language or 'unknown'}), {len(rows)} items"
        }
    finally:
        mem_conn.close()


def _memory_hints(args):
    """从长期记忆库获取历史提示"""
    memory_db = _memory_db_path(args, readonly=True)
    
    if not memory_db.exists():
        return {"hints": [], "message": "No memory database found"}
    
    project_path = getattr(args, 'project_path', None) or os.getcwd()
    mem_conn = _connect(str(memory_db), readonly=True)
    
    try:
        # 历史扫描记录
        scans = [dict(r) for r in mem_conn.execute(
            "SELECT batch_id, scan_mode, started_at, total_findings, status FROM scan_history WHERE project_path=? ORDER BY started_at DESC LIMIT 5",
            (project_path,)
        ).fetchall()]
        
        # 已知高危 Sink（上次扫描确认的，含 AST 精化字段 + stale 标记）
        known_sinks = [dict(r) for r in mem_conn.execute(
            """SELECT file_path, line, type, severity_level, last_status, times_seen,
                      ast_verified, enclosing_func, func_range_start, func_range_end,
                      call_expression, param_variables, parser_engine, content_hash, stale
               FROM known_sinks 
               WHERE project_path=? AND last_status != 'false_positive' 
               ORDER BY severity_level ASC LIMIT 30""",
            (project_path,)
        ).fetchall()]
        
        # 为过期 Sink 添加警告标注
        for s in known_sinks:
            if s.get("stale"):
                s["warning"] = "上次扫描未确认，文件可能已被删除或 Sink 已修复"
        
        # 已知防御（含过期标注）
        known_defs = [dict(r) for r in mem_conn.execute(
            "SELECT type, name, scope, stale FROM known_defenses WHERE project_path=? LIMIT 20",
            (project_path,)
        ).fetchall()]
        
        # 为过期防御添加警告标注
        for d in known_defs:
            if d.get("stale"):
                d["warning"] = "上次扫描未确认，可能已被移除"
        
        # 历史高置信度 findings
        known_findings = [dict(r) for r in mem_conn.execute(
            "SELECT finding_type, severity, file_path, line, title, confidence, status, times_seen FROM known_findings WHERE project_path=? AND confidence >= 70 ORDER BY confidence DESC LIMIT 15",
            (project_path,)
        ).fetchall()]
        
        # 技术栈摘要（v3.1 新增）
        tech_stack = [dict(r) for r in mem_conn.execute(
            "SELECT category, name, version, is_primary, confidence FROM project_tech_stack WHERE project_path=? ORDER BY is_primary DESC, category ASC",
            (project_path,)
        ).fetchall()]
        
        return {
            "previousScans": scans,
            "knownSinks": known_sinks,
            "knownDefenses": known_defs,
            "knownFindings": known_findings,
            "techStack": tech_stack if tech_stack else None,
            "message": f"Found {len(scans)} previous scans, {len(known_sinks)} known sinks, {len(tech_stack)} tech stack items"
        }
    finally:
        mem_conn.close()


def _cached_structure(args):
    """从长期记忆库获取项目结构缓存"""
    memory_db = _memory_db_path(args, readonly=True)
    
    if not memory_db.exists():
        return {"cached": False, "message": "No memory database found"}
    
    project_path = getattr(args, 'project_path', None) or os.getcwd()
    mem_conn = _connect(str(memory_db), readonly=True)
    
    try:
        # 项目结构元数据
        meta = {}
        for row in mem_conn.execute(
            "SELECT key, value FROM project_structure_meta WHERE project_path=?",
            (project_path,)
        ).fetchall():
            meta[row["key"]] = row["value"]
        
        if not meta:
            return {"cached": False, "message": "No cached structure for this project"}
        
        # 文件列表
        files = [dict(r) for r in mem_conn.execute(
            "SELECT file_path, language, lines, is_entry, category, content_hash, updated_at FROM project_structure WHERE project_path=? ORDER BY is_entry DESC, lines DESC",
            (project_path,)
        ).fetchall()]
        
        # 入口点文件
        entry_files = [f["file_path"] for f in files if f.get("is_entry")]
        
        # 上次扫描信息
        last_scan = mem_conn.execute(
            "SELECT batch_id, scan_mode, started_at, total_findings, status FROM scan_history WHERE project_path=? ORDER BY started_at DESC LIMIT 1",
            (project_path,)
        ).fetchone()
        
        # 缓存的 AST 函数签名
        cached_functions = [dict(r) for r in mem_conn.execute(
            "SELECT file_path, file_hash, name, class_name, params, return_type, start_line, end_line, parser_engine, risk_signals FROM cached_ast_functions WHERE project_path=?",
            (project_path,)
        ).fetchall()]
        
        # 缓存的端点
        cached_endpoints = [dict(r) for r in mem_conn.execute(
            "SELECT file_path, file_hash, method, path, handler, line, auth_type, permissions, priority FROM cached_endpoints WHERE project_path=?",
            (project_path,)
        ).fetchall()]
        
        # 缓存的调用图
        cached_call_graph = [dict(r) for r in mem_conn.execute(
            "SELECT caller_file, caller_file_hash, caller_func, callee_file, callee_func, depth, source FROM cached_call_graph WHERE project_path=?",
            (project_path,)
        ).fetchall()]
        
        # 缓存的 AST 调用表达式（v3.1 新增返回）
        cached_ast_calls = [dict(r) for r in mem_conn.execute(
            "SELECT file_path, file_hash, callee, receiver, args, line, full_expression, parser_engine FROM cached_ast_calls WHERE project_path=?",
            (project_path,)
        ).fetchall()]
        
        # 缓存的 AST Sink 精化结果（v3.1 新增返回）
        cached_refined_sinks = [dict(r) for r in mem_conn.execute(
            "SELECT file_path, file_hash, line, ast_verified, reason, enclosing_func, func_range_start, func_range_end, call_expression, param_variables, parser_engine FROM cached_ast_refined_sinks WHERE project_path=?",
            (project_path,)
        ).fetchall()]
        
        # 项目技术栈（v3.1 新增返回）
        tech_stack = [dict(r) for r in mem_conn.execute(
            "SELECT category, name, version, is_primary, confidence, detected_by FROM project_tech_stack WHERE project_path=? ORDER BY is_primary DESC, category ASC",
            (project_path,)
        ).fetchall()]
        
        # 用户偏好配置
        user_prefs = {}
        for row in mem_conn.execute(
            "SELECT key, value FROM user_preferences WHERE project_path=?",
            (project_path,)
        ).fetchall():
            user_prefs[row["key"]] = row["value"]
        
        return {
            "cached": True,
            "meta": meta,
            "fileCount": len(files),
            "totalLines": sum(f.get("lines", 0) for f in files),
            "entryPointFiles": entry_files,
            "entryPointCount": len(entry_files),
            "files": files,
            "lastScan": dict(last_scan) if last_scan else None,
            "cachedAstFunctions": cached_functions,
            "cachedAstFunctionCount": len(cached_functions),
            "cachedAstCalls": cached_ast_calls,
            "cachedAstCallCount": len(cached_ast_calls),
            "cachedAstRefinedSinks": cached_refined_sinks,
            "cachedAstRefinedSinkCount": len(cached_refined_sinks),
            "cachedEndpoints": cached_endpoints,
            "cachedEndpointCount": len(cached_endpoints),
            "cachedCallGraph": cached_call_graph,
            "cachedCallGraphEdges": len(cached_call_graph),
            "techStack": tech_stack if tech_stack else None,
            "userPreferences": user_prefs if user_prefs else None,
            "message": f"Cached structure: {len(files)} files, {len(entry_files)} entry points, {len(cached_functions)} functions, {len(cached_endpoints)} endpoints, {len(cached_refined_sinks)} refined sinks, {len(tech_stack)} tech stack items"
        }
    finally:
        mem_conn.close()


# ─── 命令: memory-sync ────────────────────────────────────

def cmd_memory_sync(args):
    """将本次扫描结果同步到长期记忆库"""
    db_path = _resolve_db_path(args.batch_dir)
    memory_db = _memory_db_path(args)
    
    # 确保记忆库存在
    if not memory_db.exists():
        memory_db.parent.mkdir(parents=True, exist_ok=True)
        mem_conn = _connect(str(memory_db))
        mem_conn.executescript(MEMORY_SCHEMA)
        mem_conn.commit()
        mem_conn.close()
    
    project_path = args.project_path or os.getcwd()
    batch_id = args.batch_id or Path(args.batch_dir).name
    now = _now_iso()
    
    # 读取索引库
    idx_conn = _connect(db_path, readonly=True)
    mem_conn = _connect(str(memory_db))
    
    # Schema 迁移：确保旧版 DB 也有 v3.1 新增字段/表
    _migrate_memory_schema(mem_conn)
    
    try:
        # 1. 更新项目指纹
        meta = {}
        for row in idx_conn.execute("SELECT key, value FROM project_meta"):
            meta[row["key"]] = row["value"]
        
        file_count = idx_conn.execute("SELECT COUNT(*) as c FROM files").fetchone()["c"]
        total_lines = idx_conn.execute("SELECT COALESCE(SUM(lines), 0) as s FROM files").fetchone()["s"]
        
        existing = mem_conn.execute(
            "SELECT id, scan_count FROM project_fingerprint WHERE project_path=?", (project_path,)
        ).fetchone()
        
        if existing:
            mem_conn.execute(
                "UPDATE project_fingerprint SET framework=?, file_count=?, total_lines=?, last_scan_at=?, scan_count=? WHERE id=?",
                (meta.get("framework", ""), file_count, total_lines, now, existing["scan_count"] + 1, existing["id"])
            )
        else:
            mem_conn.execute(
                "INSERT INTO project_fingerprint (project_path, framework, file_count, total_lines, first_scan_at, last_scan_at) VALUES (?, ?, ?, ?, ?, ?)",
                (project_path, meta.get("framework", ""), file_count, total_lines, now, now)
            )
        
        # 2. 记录扫描历史
        mem_conn.execute(
            "INSERT OR REPLACE INTO scan_history (batch_id, project_path, scan_mode, started_at, index_db_path) VALUES (?, ?, ?, ?, ?)",
            (batch_id, project_path, args.scan_mode or "deep", now, db_path)
        )
        
        # 预构建 file_path→file_hash 映射（供后续步骤3~12使用）
        file_hash_map = {}
        for row in idx_conn.execute("SELECT file_path, file_hash FROM ast_parse_meta WHERE file_hash IS NOT NULL"):
            file_hash_map[row["file_path"]] = row["file_hash"]
        
        # 3. 同步 Sink 到 known_sinks（含 AST 精化字段 + stale 标记）
        # 3a. 先将该项目所有已知 Sink 标记为 stale（本次扫描未确认）
        mem_conn.execute(
            "UPDATE known_sinks SET stale = 1 WHERE project_path = ?",
            (project_path,)
        )
        
        # 3b. 同步本次扫描检测到的 Sink，含 AST 精化字段，取消 stale 标记
        sinks_synced = 0
        for sink in idx_conn.execute("SELECT file_path, line, type, severity_level, defense_status, ast_verified, enclosing_func, func_range_start, func_range_end, call_expression, param_variables, parser_engine FROM sinks"):
            existing_sink = mem_conn.execute(
                "SELECT id, times_seen FROM known_sinks WHERE project_path=? AND file_path=? AND line=? AND type=?",
                (project_path, sink["file_path"], sink["line"], sink["type"])
            ).fetchone()
            
            # 获取文件 hash（关联 AST 精化结果版本）
            sink_file_hash = file_hash_map.get(sink["file_path"], "")
            
            if existing_sink:
                mem_conn.execute(
                    """UPDATE known_sinks SET severity_level=?, last_seen_at=?, times_seen=?, last_status=?,
                       ast_verified=?, enclosing_func=?, func_range_start=?, func_range_end=?,
                       call_expression=?, param_variables=?, parser_engine=?, content_hash=?, stale=0
                       WHERE id=?""",
                    (sink["severity_level"], now, existing_sink["times_seen"] + 1, sink["defense_status"],
                     sink["ast_verified"], sink["enclosing_func"], sink["func_range_start"], sink["func_range_end"],
                     sink["call_expression"], sink["param_variables"], sink["parser_engine"], sink_file_hash,
                     existing_sink["id"])
                )
            else:
                mem_conn.execute(
                    """INSERT INTO known_sinks (project_path, file_path, line, type, severity_level, last_status,
                       ast_verified, enclosing_func, func_range_start, func_range_end,
                       call_expression, param_variables, parser_engine, content_hash, stale)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                    (project_path, sink["file_path"], sink["line"], sink["type"], sink["severity_level"], sink["defense_status"],
                     sink["ast_verified"], sink["enclosing_func"], sink["func_range_start"], sink["func_range_end"],
                     sink["call_expression"], sink["param_variables"], sink["parser_engine"], sink_file_hash)
                )
            sinks_synced += 1
        
        # 3c. 统计过期 Sink 数量
        stale_sinks_count = mem_conn.execute(
            "SELECT COUNT(*) as c FROM known_sinks WHERE project_path = ? AND stale = 1",
            (project_path,)
        ).fetchone()["c"]
        
        # 4. 同步项目结构快照到 project_structure
        struct_synced = 0
        for f in idx_conn.execute("SELECT path, language, lines, is_entry, category FROM files"):
            mem_conn.execute(
                "INSERT OR REPLACE INTO project_structure (project_path, file_path, language, lines, is_entry, category, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project_path, f["path"], f["language"], f["lines"], f["is_entry"], f["category"], now)
            )
            struct_synced += 1
        
        # 5. 同步项目元数据到 project_structure_meta
        for k, v in meta.items():
            mem_conn.execute(
                "INSERT OR REPLACE INTO project_structure_meta (project_path, key, value, updated_at) VALUES (?, ?, ?, ?)",
                (project_path, k, v, now)
            )
        
        # 6. 同步防御到 known_defenses（含过期清理）
        # 6a. 先将该项目所有已知防御标记为 stale（本次扫描未确认）
        mem_conn.execute(
            "UPDATE known_defenses SET stale = 1 WHERE project_path = ?",
            (project_path,)
        )
        
        # 6b. 同步本次扫描检测到的防御，取消 stale 标记
        defs_synced = 0
        for d in idx_conn.execute("SELECT type, name, scope FROM defenses"):
            mem_conn.execute(
                "INSERT OR REPLACE INTO known_defenses (project_path, type, name, scope, last_seen_at, last_confirmed, stale) VALUES (?, ?, ?, ?, ?, ?, 0)",
                (project_path, d["type"], d["name"], d["scope"], now, now)
            )
            defs_synced += 1
        
        # 6c. 统计过期防御数量（本次扫描未确认的）
        stale_count = mem_conn.execute(
            "SELECT COUNT(*) as c FROM known_defenses WHERE project_path = ? AND stale = 1",
            (project_path,)
        ).fetchone()["c"]
        
        # 7. content_hash 回写：从 ast_parse_meta.file_hash 更新 project_structure.content_hash
        hash_synced = 0
        for ast_meta in idx_conn.execute("SELECT file_path, file_hash FROM ast_parse_meta WHERE file_hash IS NOT NULL"):
            mem_conn.execute(
                "UPDATE project_structure SET content_hash=?, updated_at=? WHERE project_path=? AND file_path=?",
                (ast_meta["file_hash"], now, project_path, ast_meta["file_path"])
            )
            hash_synced += 1
        
        # 8. ast_functions → cached_ast_functions
        ast_func_synced = 0
        
        for f in idx_conn.execute("SELECT * FROM ast_functions"):
            fh = file_hash_map.get(f["file_path"], "")
            mem_conn.execute(
                """INSERT OR REPLACE INTO cached_ast_functions 
                   (project_path, file_path, file_hash, name, class_name, params, return_type, 
                    modifiers, annotations, start_line, end_line, parser_engine, risk_signals)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_path, f["file_path"], fh, f["name"], f["class_name"], f["params"],
                 f["return_type"], f["modifiers"], f["annotations"], f["start_line"], f["end_line"],
                 f["parser_engine"], f["risk_signals"])
            )
            ast_func_synced += 1
        
        # 9. ast_calls → cached_ast_calls
        ast_call_synced = 0
        for c in idx_conn.execute("SELECT * FROM ast_calls"):
            fh = file_hash_map.get(c["file_path"], "")
            mem_conn.execute(
                """INSERT OR REPLACE INTO cached_ast_calls 
                   (project_path, file_path, file_hash, callee, receiver, args, line, full_expression, parser_engine)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_path, c["file_path"], fh, c["callee"], c["receiver"], c["args"],
                 c["line"], c["full_expression"], c["parser_engine"])
            )
            ast_call_synced += 1
        
        # 10. endpoints → cached_endpoints
        endpoint_synced = 0
        for ep in idx_conn.execute("SELECT * FROM endpoints"):
            fh = file_hash_map.get(ep["file_path"], "")
            mem_conn.execute(
                """INSERT OR REPLACE INTO cached_endpoints 
                   (project_path, file_path, file_hash, method, path, handler, line, auth_type, permissions, priority)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_path, ep["file_path"], fh, ep["method"], ep["path"], ep["handler"],
                 ep["line"], ep["auth_type"], ep["permissions"], ep["priority"])
            )
            endpoint_synced += 1
        
        # 11. call_graph → cached_call_graph
        cg_synced = 0
        for edge in idx_conn.execute("SELECT * FROM call_graph"):
            caller_fh = file_hash_map.get(edge["caller_file"], "")
            mem_conn.execute(
                """INSERT OR REPLACE INTO cached_call_graph 
                   (project_path, caller_file, caller_file_hash, caller_func, callee_file, callee_func, depth, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_path, edge["caller_file"], caller_fh, edge["caller_func"],
                 edge["callee_file"], edge["callee_func"], edge["depth"], edge["source"])
            )
            cg_synced += 1
        
        # 12. ast_refined_sinks → cached_ast_refined_sinks（跨扫描 AST Sink 精化缓存）
        refined_synced = 0
        for rs in idx_conn.execute("SELECT * FROM ast_refined_sinks"):
            fh = file_hash_map.get(rs["file_path"], "")
            mem_conn.execute(
                """INSERT OR REPLACE INTO cached_ast_refined_sinks 
                   (project_path, file_path, file_hash, line, ast_verified, reason,
                    enclosing_func, func_range_start, func_range_end, call_expression,
                    param_variables, parser_engine)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_path, rs["file_path"], fh, rs["line"], rs["ast_verified"], rs["reason"],
                 rs["enclosing_func"], rs["func_range_start"], rs["func_range_end"],
                 rs["call_expression"], rs["param_variables"], rs["parser_engine"])
            )
            refined_synced += 1
        
        # 13. 已删除文件级联清理
        #     对比 project_structure 中的文件 vs 本次扫描 files 表，
        #     不在本次扫描中的文件 → 从所有缓存表中删除对应记录
        files_deleted = 0
        current_files = set()
        for row in idx_conn.execute("SELECT path FROM files"):
            current_files.add(row["path"])
        
        if current_files:
            old_files = set()
            for row in mem_conn.execute(
                "SELECT file_path FROM project_structure WHERE project_path=?",
                (project_path,)
            ):
                old_files.add(row["file_path"])
            
            deleted_files = old_files - current_files
            if deleted_files:
                # 级联删除：project_structure, cached_ast_functions, cached_ast_calls,
                # cached_endpoints, cached_call_graph, known_sinks, cached_ast_refined_sinks
                cascade_tables_file_path = [
                    "project_structure", "cached_ast_functions", "cached_ast_calls",
                    "cached_endpoints", "cached_ast_refined_sinks", "known_sinks",
                ]
                for del_file in deleted_files:
                    for tbl in cascade_tables_file_path:
                        mem_conn.execute(
                            f"DELETE FROM {tbl} WHERE project_path=? AND file_path=?",
                            (project_path, del_file)
                        )
                    # cached_call_graph 使用 caller_file / callee_file 双列
                    mem_conn.execute(
                        "DELETE FROM cached_call_graph WHERE project_path=? AND (caller_file=? OR callee_file=?)",
                        (project_path, del_file, del_file)
                    )
                    files_deleted += 1
        
        # 14. 技术栈同步 → project_tech_stack
        #     从 project_meta 的 framework / language 字段解析，写入结构化记录
        tech_synced = 0
        framework_val = meta.get("framework", "")
        if framework_val and framework_val != "unknown":
            # 解析可能的多框架（逗号分隔，如 "spring-boot,spring-security"）
            for fw in framework_val.split(","):
                fw = fw.strip()
                if fw:
                    mem_conn.execute(
                        """INSERT OR REPLACE INTO project_tech_stack 
                           (project_path, category, name, is_primary, confidence, detected_by, last_seen_at)
                           VALUES (?, 'framework', ?, ?, 'high', 'marker-file', ?)""",
                        (project_path, fw, 1 if tech_synced == 0 else 0, now)
                    )
                    tech_synced += 1
        
        # 从 files 表推断语言分布
        lang_rows = idx_conn.execute(
            "SELECT language, COUNT(*) as cnt FROM files WHERE language IS NOT NULL GROUP BY language ORDER BY cnt DESC"
        ).fetchall()
        primary_lang = True
        for lr in lang_rows:
            lang = lr["language"]
            if lang:
                mem_conn.execute(
                    """INSERT OR REPLACE INTO project_tech_stack 
                       (project_path, category, name, is_primary, confidence, detected_by, last_seen_at)
                       VALUES (?, 'language', ?, ?, 'high', 'file-extension', ?)""",
                    (project_path, lang, 1 if primary_lang else 0, now)
                )
                tech_synced += 1
                primary_lang = False
        
        # 从 project_meta 读取构建工具（如果有）
        build_tool = meta.get("build_tool", "")
        if build_tool:
            for bt in build_tool.split(","):
                bt = bt.strip()
                if bt:
                    mem_conn.execute(
                        """INSERT OR REPLACE INTO project_tech_stack 
                           (project_path, category, name, confidence, detected_by, last_seen_at)
                           VALUES (?, 'build_tool', ?, 'high', 'marker-file', ?)""",
                        (project_path, bt, now)
                    )
                    tech_synced += 1
        
        mem_conn.commit()
        
    except Exception as e:
        mem_conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        idx_conn.close()
        mem_conn.close()
    
    result = {
        "status": "synced",
        "project_path": project_path,
        "batch_id": batch_id,
        "sinks_synced": sinks_synced,
        "stale_sinks": stale_sinks_count,
        "structure_synced": struct_synced,
        "defenses_synced": defs_synced,
        "stale_defenses": stale_count,
        "content_hash_synced": hash_synced,
        "ast_functions_cached": ast_func_synced,
        "ast_calls_cached": ast_call_synced,
        "endpoints_cached": endpoint_synced,
        "call_graph_cached": cg_synced,
        "refined_sinks_cached": refined_synced,
        "files_deleted": files_deleted,
        "tech_stack_synced": tech_synced,
        "memory_db": str(memory_db)
    }
    print(json.dumps(result))


# ─── 命令: update-findings ─────────────────────────────────

def cmd_update_findings(args):
    """
    将审计 Agent 的 findings 同步到长期记忆库。
    在审计完成后由编排器调用。
    """
    memory_db = _memory_db_path(args)
    
    if not memory_db.exists():
        print(json.dumps({"error": "Memory database not found"}))
        sys.exit(1)
    
    project_path = args.project_path or os.getcwd()
    batch_id = args.batch_id or Path(args.batch_dir).name
    now = _now_iso()
    
    # 读取 findings JSON
    if args.findings_file:
        with open(args.findings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)
    
    findings = data.get("findings", [])
    mem_conn = _connect(str(memory_db))
    
    try:
        synced = 0
        for f in findings:
            severity = f.get("severity", "medium")
            confidence = f.get("confidence", 0)
            
            # 统一 schema：camelCase + 必需字段
            finding_type = f.get("riskType") or "unknown"
            file_path = f.get("filePath") or ""
            line_number = f.get("lineNumber") or 0
            title = f.get("description") or ""
            
            # 仅同步有意义的 findings（排除 false_positive）
            verification = f.get("verification", {})
            if isinstance(verification, dict) and verification.get("verificationStatus") == "false_positive":
                continue
            
            existing = mem_conn.execute(
                "SELECT id, times_seen FROM known_findings WHERE project_path=? AND finding_type=? AND file_path=? AND line=?",
                (project_path, finding_type, file_path, line_number)
            ).fetchone()
            
            if existing:
                mem_conn.execute(
                    "UPDATE known_findings SET batch_id=?, severity=?, title=?, confidence=?, last_seen_at=?, times_seen=? WHERE id=?",
                    (batch_id, severity, title, confidence, now, existing["times_seen"] + 1, existing["id"])
                )
            else:
                mem_conn.execute(
                    "INSERT INTO known_findings (project_path, batch_id, finding_type, severity, file_path, line, title, confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (project_path, batch_id, finding_type, severity, file_path, line_number, title, confidence)
                )
            synced += 1
        
        # 更新扫描历史
        total_findings = len(findings)
        severity_counts = {}
        for f in findings:
            s = f.get("severity", "medium")
            severity_counts[s] = severity_counts.get(s, 0) + 1
        
        mem_conn.execute(
            "UPDATE scan_history SET total_findings=?, by_severity=?, completed_at=?, status='completed' WHERE batch_id=?",
            (total_findings, json.dumps(severity_counts), now, batch_id)
        )
        
        mem_conn.commit()
        
    except Exception as e:
        mem_conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        mem_conn.close()
    
    print(json.dumps({"status": "synced", "findings_synced": synced, "total_findings": total_findings}))


# ─── 命令: update-sinks ───────────────────────────────────

def cmd_update_sinks(args):
    """
    将 AST 精化结果批量回写到 sinks 表。
    从 stdin 读取 JSON 数组，每项包含 file_path, line 及 AST 精化字段。
    
    JSON 格式：
    [
      {
        "file_path": "src/Dao.kt",
        "line": 56,
        "ast_verified": 1,
        "enclosing_func": "queryDetail",
        "func_range_start": 40,
        "func_range_end": 60,
        "call_expression": "append(\"limit ${request.limit}\")",
        "param_variables": "request.limit,request.offset",
        "parser_engine": "tree-sitter"
      }
    ]
    """
    db_path = _resolve_db_path(args.batch_dir)
    
    if args.data:
        data = json.loads(args.data)
    else:
        data = json.load(sys.stdin)
    
    # 支持包装在对象中的格式 {"sinks": [...]}
    if isinstance(data, dict):
        data = data.get("sinks", data.get("rows", []))
    
    conn = _connect(db_path)
    updated = 0
    
    ast_fields = ("ast_verified", "enclosing_func", "func_range_start",
                  "func_range_end", "call_expression", "param_variables", "parser_engine")
    
    try:
        for sink in data:
            fp = sink.get("file_path") or sink.get("filePath")
            ln = sink.get("line") or sink.get("lineNumber")
            if not fp or ln is None:
                continue
            
            updates = {k: sink[k] for k in ast_fields if k in sink}
            if not updates:
                continue
            
            set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
            values = list(updates.values()) + [fp, ln]
            
            conn.execute(
                f"UPDATE sinks SET {set_clause} WHERE file_path=? AND line=?",
                values
            )
            updated += 1
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()
    
    print(json.dumps({"status": "updated", "rows_updated": updated}))


# ─── 命令: save-preferences ───────────────────────────────

def cmd_save_preferences(args):
    """
    将扫描配置保存到长期记忆库的 user_preferences 表。
    支持从 --data JSON 或命令行参数读取配置。
    """
    memory_db = _memory_db_path(args)
    
    if not memory_db.exists():
        print(json.dumps({"error": "Memory database not found. Run init first."}))
        sys.exit(1)
    
    project_path = args.project_path or os.getcwd()
    now = _now_iso()
    
    # 从 --data JSON 或单独的 CLI 参数收集配置
    if args.data:
        prefs = json.loads(args.data)
    else:
        prefs = {}
        for key in ("scan_mode", "lsp_status", "lsp_language", "parser_type",
                     "permissions_version", "framework", "plugin_root"):
            val = getattr(args, key, None)
            if val is not None:
                prefs[key] = val
    
    if not prefs:
        print(json.dumps({"error": "No preferences provided"}))
        sys.exit(1)
    
    mem_conn = _connect(str(memory_db))
    try:
        for k, v in prefs.items():
            if v is not None:
                mem_conn.execute(
                    "INSERT OR REPLACE INTO user_preferences (project_path, key, value, updated_at) VALUES (?, ?, ?, ?)",
                    (project_path, k, str(v), now)
                )
        mem_conn.commit()
    except Exception as e:
        mem_conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        mem_conn.close()
    
    print(json.dumps({"status": "saved", "preferences": prefs, "project_path": project_path}))


# ─── 辅助 ─────────────────────────────────────────────────

def _resolve_db_path(batch_dir):
    """解析 project-index.db 路径"""
    db_path = str(Path(batch_dir) / "project-index.db")
    if not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found: {db_path}"}))
        sys.exit(1)
    return db_path


# ─── CLI 入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="project-index SQLite 数据库管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 初始化数据库
  %(prog)s init --batch-dir .codebuddy/security-scan/runs/project-20260322 --batch-id project-20260322

  # 写入 Sink 数据
  echo '{"phase":"phase1","table":"sinks","rows":[{"file_path":"src/Dao.java","line":45,"type":"sql-injection","severity_level":1}]}' | %(prog)s write --batch-dir .codebuddy/security-scan/runs/project-20260322

  # 查询 Sink 列表（供扫描 Agent）
  %(prog)s query --batch-dir .codebuddy/security-scan/runs/project-20260322 --preset sinks-by-severity

  # 查询项目概况
  %(prog)s query --batch-dir .codebuddy/security-scan/runs/project-20260322 --preset summary

  # 同步到长期记忆
  %(prog)s memory-sync --batch-dir .codebuddy/security-scan/runs/project-20260322 --project-path /path/to/project

  # 查询长期记忆提示
  %(prog)s query --batch-dir .codebuddy/security-scan/runs/project-20260322 --preset memory-hints --project-path /path/to/project
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # init
    p_init = subparsers.add_parser("init", help="初始化索引数据库")
    p_init.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_init.add_argument("--batch-id", help="批次 ID（默认使用目录名）")
    p_init.add_argument("--project-path", help="项目根目录（自定义输出位置时显式传入；未传则从批次目录反推，用于定位长期记忆库）")
    
    # write
    p_write = subparsers.add_parser("write", help="增量写入索引数据")
    p_write.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_write.add_argument("--data", help="JSON 数据（或从 stdin 读取）")
    
    # query
    p_query = subparsers.add_parser("query", help="查询索引数据")
    p_query.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_query.add_argument("--preset", help="预定义查询名称")
    p_query.add_argument("--sql", help="自定义 SQL（仅 SELECT）")
    p_query.add_argument("--limit", type=int, help="结果数量限制")
    p_query.add_argument("--filter-file", help="按文件过滤")
    p_query.add_argument("--project-path", help="项目路径（memory-hints 用）")
    
    # memory-sync
    p_sync = subparsers.add_parser("memory-sync", help="同步到长期记忆库")
    p_sync.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_sync.add_argument("--batch-id", help="批次 ID")
    p_sync.add_argument("--project-path", help="项目路径")
    p_sync.add_argument("--scan-mode", help="扫描模式 (deep/light)")
    
    # update-findings
    p_findings = subparsers.add_parser("update-findings", help="同步审计 findings 到长期记忆")
    p_findings.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_findings.add_argument("--batch-id", help="批次 ID")
    p_findings.add_argument("--project-path", help="项目路径")
    p_findings.add_argument("--findings-file", help="findings JSON 文件路径（或从 stdin 读取）")
    
    # update-sinks
    p_usinks = subparsers.add_parser("update-sinks", help="将 AST 精化结果回写到 sinks 表")
    p_usinks.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_usinks.add_argument("--data", help="JSON 数据（或从 stdin 读取）")
    
    # save-preferences
    p_prefs = subparsers.add_parser("save-preferences", help="保存扫描配置到长期记忆")
    p_prefs.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_prefs.add_argument("--project-path", help="项目路径")
    p_prefs.add_argument("--data", help="JSON 格式的配置键值对")
    p_prefs.add_argument("--scan-mode", help="扫描模式 (deep/light)")
    p_prefs.add_argument("--lsp-status", dest="lsp_status", help="LSP 状态")
    p_prefs.add_argument("--lsp-language", dest="lsp_language", help="项目语言")
    p_prefs.add_argument("--parser-type", dest="parser_type", help="解析器类型")
    p_prefs.add_argument("--permissions-version", dest="permissions_version", help="权限白名单版本")
    p_prefs.add_argument("--framework", help="框架")
    p_prefs.add_argument("--plugin-root", dest="plugin_root", help="插件根路径")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        "init": cmd_init,
        "write": cmd_write,
        "query": cmd_query,
        "memory-sync": cmd_memory_sync,
        "update-findings": cmd_update_findings,
        "update-sinks": cmd_update_sinks,
        "save-preferences": cmd_save_preferences,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
