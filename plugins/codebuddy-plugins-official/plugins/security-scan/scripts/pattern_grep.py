#!/usr/bin/env python3
"""
批量模式匹配工具 — 从 YAML 模式文件读取 Grep 模式，执行匹配，结果直接写入 project-index.db

跨平台：Python3 内置模块 + pyyaml（可选降级到正则解析），零编译依赖。

子命令：
  1. grep-sinks          — 批量 Sink grep → sinks 表
  2. grep-entries         — 入口点检测 → files(is_entry=1)
  3. grep-defenses        — 防御模式检测 → defenses 表
  4. grep-secrets         — 敏感信息检测 → indexer_findings 表
  5. grep-attack-surface  — 攻击面检测 → attack_surface 表
  6. prescreen-sinks      — 脚本预筛 ledger（v3.2，Fast 模式确定性过滤）

设计原则：
  - 替代 Agent 中的手动 Grep 循环，确保一致性
  - 结果直接写入 DB（INSERT OR IGNORE 避免重复）
  - stdout 输出 JSON 统计摘要，供 Agent 日志记录
  - 支持 ripgrep (rg) 加速，降级到 grep -rn
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ─── YAML 解析（零依赖降级） ─────────────────────────────────

def _load_yaml(path):
    """加载 YAML 文件，优先用 pyyaml，降级到简单解析"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        return _parse_yaml_simple(path)


def _parse_yaml_simple(path):
    """简单 YAML 解析器（仅支持本项目的 sink-patterns.yaml 格式）"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    result = {"sink_types": []}
    current_type = None
    current_patterns = []

    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("- type:"):
            if current_type:
                result["sink_types"].append({"type": current_type, "patterns": current_patterns})
            current_type = stripped.split(":", 1)[1].strip().strip("'\"")
            current_patterns = []
        elif stripped.startswith("- '") or stripped.startswith('- "'):
            pattern = stripped[2:].strip().strip("'\"")
            current_patterns.append(pattern)

    if current_type:
        result["sink_types"].append({"type": current_type, "patterns": current_patterns})

    return result


# ─── Grep 执行引擎 ───────────────────────────────────────────

_grep_tool_cache = None


def _detect_grep_tool():
    """检测可用的 grep 工具（结果缓存，同进程内只探测一次）"""
    global _grep_tool_cache
    if _grep_tool_cache is not None:
        return _grep_tool_cache if _grep_tool_cache != '' else None
    for tool in ["rg", "grep"]:
        try:
            subprocess.run([tool, "--version"], capture_output=True, timeout=5)
            _grep_tool_cache = tool
            return tool
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    _grep_tool_cache = ''  # 标记已探测但未找到
    return None


def _run_grep(pattern, project_path, grep_tool, file_globs=None):
    """执行 grep，返回 [(file, line_num, matched_text), ...]"""
    results = []

    if grep_tool == "rg":
        cmd = ["rg", "-n", "--no-heading", "--no-filename", "-e", pattern]
        if file_globs:
            for g in file_globs:
                cmd.extend(["--glob", g])
        cmd.append(str(project_path))
        # rg 使用 --no-filename 会影响输出，改用带文件名格式
        cmd = ["rg", "-n", "--no-heading", "-e", pattern]
        if file_globs:
            for g in file_globs:
                cmd.extend(["--glob", g])
        cmd.append(str(project_path))
    else:
        cmd = ["grep", "-rn", "-E", pattern, str(project_path)]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            env={**os.environ, "LANG": "C"}
        )
        for line in proc.stdout.split("\n"):
            if not line.strip():
                continue
            # 格式: file:line:text
            parts = line.split(":", 2)
            if len(parts) >= 3:
                filepath = parts[0]
                try:
                    line_num = int(parts[1])
                except ValueError:
                    continue
                text = parts[2].strip()
                # 过滤测试/构建产物
                if _should_skip_file(filepath):
                    continue
                results.append((filepath, line_num, text))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return results


def _should_skip_file(filepath):
    """过滤非源代码文件、测试文件和构建产物"""
    skip_patterns = [
        "/test/", "/tests/", "/spec/", "/__test__/",
        "/node_modules/", "/vendor/", "/target/", "/build/", "/dist/",
        "/.git/", "/.mvn/", "/.gradle/",
        "/security-scan-output/", "/.codebuddy/security-scan/runs/",
        "Test.java", "Tests.java", "Spec.js", ".test.", ".spec.",
        "package-lock.json", "yarn.lock", ".min.js", ".min.css",
    ]
    if any(p in filepath for p in skip_patterns):
        return True
    # 仅保留源代码文件，排除配置/构建/脚本等非代码文件
    _SOURCE_CODE_EXTENSIONS = {
        ".java", ".kt", ".kts", ".scala", ".groovy",
        ".py", ".pyx",
        ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte",
        ".go",
        ".rb", ".erb",
        ".php",
        ".cs",
        ".rs",
        ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
        ".swift", ".m", ".mm",
        ".lua", ".pl", ".pm", ".r", ".R",
    }
    ext = os.path.splitext(filepath)[1].lower()
    if not ext or ext not in _SOURCE_CODE_EXTENSIONS:
        return True
    return False


def _make_relative(filepath, project_path):
    """将绝对路径转为项目相对路径"""
    try:
        return str(Path(filepath).relative_to(project_path))
    except ValueError:
        return filepath


# ─── DB 连接 ─────────────────────────────────────────────────

def _connect_db(batch_dir):
    """连接 project-index.db，带重试机制"""
    db_path = str(Path(batch_dir) / "project-index.db")
    if not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found: {db_path}"}))
        sys.exit(1)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=15000")
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            raise


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── Sink 类型 → severity_level 映射 ─────────────────────────

SINK_SEVERITY = {
    "SQL 注入": 1, "命令注入": 1, "反序列化": 1, "代码执行": 1,
    "JNDI": 1, "表达式注入": 1,
    "SSRF": 2, "文件操作": 2, "模板注入": 2, "XSS": 2,
    "开放重定向": 2, "NoSQL 注入": 2, "LDAP 注入": 2, "原型链污染": 2,
    "支付/金额": 2, "密码存储": 2,
    "COS/万象 STS 鉴权缺失": 1,
    "CRLF 注入": 3, "日志注入": 3, "Session 固定": 3,
    "Mass Assignment": 3, "不安全随机数": 3, "Cookie 安全属性缺失": 3,
    "弱哈希算法（密码存储）": 3, "CSV 注入": 3,
    "拒绝服务": 3, "PostMessage": 3, "WebSocket": 3,
}


# ─── 命令: grep-sinks ────────────────────────────────────────

def cmd_grep_sinks(args):
    """从 sink-patterns.yaml 读取模式，批量 grep 写入 sinks 表"""
    patterns_data = _load_yaml(args.patterns_file)
    sink_types = patterns_data.get("sink_types", [])
    grep_tool = _detect_grep_tool()
    project_path = Path(args.project_path).resolve()

    if not grep_tool:
        print(json.dumps({"error": "No grep tool found (rg or grep)"}))
        sys.exit(1)

    conn = _connect_db(args.batch_dir)
    total_found = 0
    by_type = {}
    by_severity = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}

    try:
        for sink_type_def in sink_types:
            type_name = sink_type_def["type"]
            patterns = sink_type_def.get("patterns", [])
            severity = SINK_SEVERITY.get(type_name, 3)
            type_count = 0

            for pattern in patterns:
                matches = _run_grep(pattern, str(project_path), grep_tool)
                for filepath, line_num, snippet in matches:
                    rel_path = _make_relative(filepath, str(project_path))
                    # 截断 snippet 到 200 字符
                    snippet_trimmed = snippet[:200] if snippet else ""

                    conn.execute("""
                        INSERT OR IGNORE INTO sinks
                        (file_path, line, type, severity_level, code_snippet, defense_status, trace_status)
                        VALUES (?, ?, ?, ?, ?, 'unknown', 'pending')
                    """, (rel_path, line_num, type_name, severity, snippet_trimmed))
                    type_count += 1

            total_found += type_count
            if type_count > 0:
                by_type[type_name] = type_count
                sev_key = f"S{severity}" if severity <= 4 else "S4"
                by_severity[sev_key] = by_severity.get(sev_key, 0) + type_count

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()

    result = {
        "status": "completed",
        "command": "grep-sinks",
        "total_sinks_found": total_found,
        "by_type": by_type,
        "by_severity": by_severity,
        "grep_tool": grep_tool,
        "patterns_file": args.patterns_file
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: grep-entries ──────────────────────────────────────

# 入口点模式（按框架分类）
ENTRY_PATTERNS = {
    "java-spring": [
        r"@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)",
        r"@(WebServlet|WebFilter|WebListener)",
        r"@(MessageMapping|SubscribeMapping)",
        r"@(Scheduled|EventListener)",
    ],
    "java-servlet": [
        r"extends\s+HttpServlet",
        r"implements\s+Filter\b",
        r"implements\s+ServletContextListener",
    ],
    "python-django": [
        r"urlpatterns\s*=",
        r"class\s+\w+View\(",
        r"def\s+(get|post|put|delete|patch)\s*\(",
    ],
    "python-flask": [
        r"@app\.(route|get|post|put|delete)\(",
        r"@blueprint\.\w+\(",
    ],
    "python-fastapi": [
        r"@app\.(get|post|put|delete|patch)\(",
        r"@router\.(get|post|put|delete|patch)\(",
    ],
    "node-express": [
        r"(app|router)\.(get|post|put|delete|patch|all|use)\s*\(",
    ],
    "go": [
        r"(HandleFunc|Handle|Get|Post|Put|Delete)\s*\(",
        r"func\s+\w+Handler\(",
    ],
}


def cmd_grep_entries(args):
    """检测入口点文件，更新 files.is_entry=1"""
    grep_tool = _detect_grep_tool()
    project_path = Path(args.project_path).resolve()

    if not grep_tool:
        print(json.dumps({"error": "No grep tool found"}))
        sys.exit(1)

    conn = _connect_db(args.batch_dir)
    entry_files = set()

    try:
        for framework, patterns in ENTRY_PATTERNS.items():
            for pattern in patterns:
                matches = _run_grep(pattern, str(project_path), grep_tool)
                for filepath, _, _ in matches:
                    rel_path = _make_relative(filepath, str(project_path))
                    entry_files.add(rel_path)

        # 更新 files 表
        updated = 0
        for rel_path in entry_files:
            cursor = conn.execute(
                "UPDATE files SET is_entry = 1 WHERE path = ?", (rel_path,)
            )
            if cursor.rowcount > 0:
                updated += 1
            else:
                # 文件不在 files 表中，可能还没被枚举；跳过不插入
                pass

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()

    result = {
        "status": "completed",
        "command": "grep-entries",
        "entry_files_detected": len(entry_files),
        "files_updated": updated,
        "entry_files": sorted(entry_files)[:50],  # 最多返回 50 个
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: grep-defenses ─────────────────────────────────────

DEFENSE_PATTERNS = {
    "global-filter": {
        "patterns": [
            r"@EnableWebSecurity",
            r"FilterRegistrationBean",
            r"OncePerRequestFilter",
            r"CsrfFilter",
            r"XssFilter",
            r"helmet\(",
            r"csrf\(\)",
            r"cors\(\)",
        ],
        "scope": "global",
    },
    "framework": {
        "patterns": [
            r"@PreAuthorize\(",
            r"@Secured\(",
            r"@RolesAllowed\(",
            r"hasRole\(",
            r"hasAuthority\(",
            r"@RequiresPermissions\(",
            r"@RequiresRoles\(",
            r"@Valid\b",
            r"@Validated\b",
            r"@Pattern\(",
            r"@Size\(",
            r"@NotBlank",
            r"@NotNull",
        ],
        "scope": "method",
    },
    "parameterization": {
        "patterns": [
            r"PreparedStatement",
            r"setString\(",
            r"setInt\(",
            r"setParameter\(",
            r"createQuery\(",
            r"@Param\(",
            r"#\{[^}]+\}",  # MyBatis parameterized
        ],
        "scope": "method",
    },
    "encoding": {
        "patterns": [
            r"HtmlUtils\.htmlEscape",
            r"StringEscapeUtils\.",
            r"URLEncoder\.encode",
            r"encodeURIComponent\(",
            r"escape\(",
            r"sanitize",
        ],
        "scope": "method",
    },
    "rate-limiting": {
        "patterns": [
            r"@RateLimiter",
            r"RateLimiter\.",
            r"rateLimit\(",
            r"throttle\(",
            r"Bucket4j",
        ],
        "scope": "method",
    },
    "url_validation": {
        "patterns": [
            r"NewSafeClient\(",
            r"new Scurl\(",
            r"Scurl\(\)\.hook\(",
            r"scurl\.hook\(",
            r"checkurl\.",
            r"CheckUrl\(",
            r"@tencent/scurl",
            r"sec-api.*scurl",
        ],
        "scope": "method",
    },
}


def cmd_grep_defenses(args):
    """检测防御模式，写入 defenses 表"""
    grep_tool = _detect_grep_tool()
    project_path = Path(args.project_path).resolve()

    if not grep_tool:
        print(json.dumps({"error": "No grep tool found"}))
        sys.exit(1)

    conn = _connect_db(args.batch_dir)
    total_found = 0
    by_type = {}

    try:
        for defense_type, config in DEFENSE_PATTERNS.items():
            scope = config["scope"]
            type_count = 0

            for pattern in config["patterns"]:
                matches = _run_grep(pattern, str(project_path), grep_tool)
                for filepath, line_num, snippet in matches:
                    rel_path = _make_relative(filepath, str(project_path))
                    # 从 snippet 提取防御名称
                    defense_name = _extract_defense_name(snippet, pattern)

                    conn.execute("""
                        INSERT OR IGNORE INTO defenses
                        (type, name, file_path, line, scope, detail)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (defense_type, defense_name, rel_path, line_num, scope, snippet[:200]))
                    type_count += 1

            total_found += type_count
            if type_count > 0:
                by_type[defense_type] = type_count

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()

    result = {
        "status": "completed",
        "command": "grep-defenses",
        "total_defenses_found": total_found,
        "by_type": by_type,
    }
    print(json.dumps(result, ensure_ascii=False))


def _extract_defense_name(snippet, pattern):
    """从匹配行提取防御名称"""
    # 尝试提取注解名或函数名
    m = re.search(r"@(\w+)", snippet)
    if m:
        return m.group(1)
    m = re.search(r"(\w+(?:Filter|Security|Limiter|Validator|Sanitizer))", snippet)
    if m:
        return m.group(1)
    # 降级：使用 snippet 的前 30 字符
    return snippet[:30].strip()


# ─── 命令: grep-secrets ──────────────────────────────────────

SECRET_PATTERNS = [
    {
        "pattern": r"(password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        "type": "secret",
        "severity": "high",
        "title": "硬编码凭证",
    },
    {
        "pattern": r"(AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[0-9A-Z]{16}",
        "type": "secret",
        "severity": "critical",
        "title": "AWS Access Key",
    },
    {
        "pattern": r"ghp_[0-9a-zA-Z]{36}",
        "type": "secret",
        "severity": "critical",
        "title": "GitHub Personal Access Token",
    },
    {
        "pattern": r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
        "type": "secret",
        "severity": "critical",
        "title": "Private Key",
    },
    {
        "pattern": r"(jdbc|mysql|postgresql|mongodb)://\w+:\w+@",
        "type": "config",
        "severity": "high",
        "title": "数据库连接串含凭证",
    },
    {
        "pattern": r"(http\.csrf\(\)\.disable|csrf\s*=\s*false|csrf_enabled.*false)",
        "type": "config",
        "severity": "medium",
        "title": "CSRF 保护已禁用",
    },
    {
        "pattern": r"(allowedOrigins\(\"\*\"|Access-Control-Allow-Origin.*\*|cors.*origin.*\*)",
        "type": "config",
        "severity": "medium",
        "title": "CORS 配置为通配符",
    },
]


def cmd_grep_secrets(args):
    """检测硬编码凭证和危险配置，写入 indexer_findings 表"""
    grep_tool = _detect_grep_tool()
    project_path = Path(args.project_path).resolve()

    if not grep_tool:
        print(json.dumps({"error": "No grep tool found"}))
        sys.exit(1)

    conn = _connect_db(args.batch_dir)
    total_found = 0
    by_type = {}

    try:
        for secret_def in SECRET_PATTERNS:
            pattern = secret_def["pattern"]
            matches = _run_grep(pattern, str(project_path), grep_tool)

            for filepath, line_num, snippet in matches:
                rel_path = _make_relative(filepath, str(project_path))

                # 排除注释中的假阳性
                stripped = snippet.strip()
                if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("*"):
                    # 简单注释过滤（非 100% 准确，但减少噪音）
                    continue

                # 排除示例/文档文件
                if any(ext in rel_path.lower() for ext in [".md", ".txt", ".rst", ".example"]):
                    continue

                conn.execute("""
                    INSERT OR IGNORE INTO indexer_findings
                    (type, severity, file_path, line, title, detail, evidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    secret_def["type"],
                    secret_def["severity"],
                    rel_path,
                    line_num,
                    secret_def["title"],
                    f"Pattern: {pattern}",
                    snippet[:200],
                ))
                total_found += 1
                by_type[secret_def["type"]] = by_type.get(secret_def["type"], 0) + 1

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()

    result = {
        "status": "completed",
        "command": "grep-secrets",
        "total_findings": total_found,
        "by_type": by_type,
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: grep-attack-surface ───────────────────────────────

ATTACK_SURFACE_PATTERNS = {
    "file-upload": [
        r"MultipartFile",
        r"@RequestParam.*MultipartFile",
        r"multer\(",
        r"move_uploaded_file",
        r"FileUpload",
    ],
    "websocket": [
        r"@ServerEndpoint\(",
        r"WebSocketServer",
        r"ws\.on\(",
        r"@MessageMapping",
    ],
    "cron": [
        r"@Scheduled\(",
        r"CronTrigger",
        r"node-cron",
        r"schedule\.scheduleJob",
    ],
    "mq": [
        r"@RabbitListener",
        r"@KafkaListener",
        r"@JmsListener",
        r"amqplib",
        r"kafkajs",
    ],
    "rpc": [
        r"@GrpcService",
        r"@DubboService",
        r"Feign",
        r"@FeignClient",
    ],
    "graphql": [
        r"@QueryMapping",
        r"@MutationMapping",
        r"GraphQL",
        r"graphqlHTTP",
    ],
}


def cmd_grep_attack_surface(args):
    """检测攻击面，写入 attack_surface 表"""
    grep_tool = _detect_grep_tool()
    project_path = Path(args.project_path).resolve()

    if not grep_tool:
        print(json.dumps({"error": "No grep tool found"}))
        sys.exit(1)

    conn = _connect_db(args.batch_dir)
    total_found = 0
    by_type = {}

    try:
        for surface_type, patterns in ATTACK_SURFACE_PATTERNS.items():
            type_count = 0
            for pattern in patterns:
                matches = _run_grep(pattern, str(project_path), grep_tool)
                for filepath, line_num, snippet in matches:
                    rel_path = _make_relative(filepath, str(project_path))

                    conn.execute("""
                        INSERT OR IGNORE INTO attack_surface
                        (type, file_path, line, detail)
                        VALUES (?, ?, ?, ?)
                    """, (surface_type, rel_path, line_num, snippet[:200]))
                    type_count += 1

            total_found += type_count
            if type_count > 0:
                by_type[surface_type] = type_count

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()

    result = {
        "status": "completed",
        "command": "grep-attack-surface",
        "total_items": total_found,
        "by_type": by_type,
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: prescreen-sinks ──────────────────────────────────
#
# Fast 模式 v3.2 脚本预筛 Ledger（方案 A'-Δ）
#
# 用途：在 grep-sinks 完成后、LLM 三判扫描之前，对 sinks 表执行
#       确定性过滤规则，把"高度确信无需 LLM 判定"的 Sink 标记为
#       disposition='not_applicable'，附原因到 disposition_reason。
#       LLM 阶段 2 的 sinks-top-per-file preset 会自动跳过这些。
#
# 设计原则：保守白名单，宁可漏过不可误杀。五条规则：
#   R1 test_path             — 文件路径在测试目录
#   R2 literal_arg           — Sink 调用仅传字面量参数
#   R3 inline_parameterized  — Sink 同行/snippet 有参数化标记
#   R4 regex_literal         — Sink-pattern 定义本身被识别为 Sink（v3.2 P1 扩充）
#   R5 keyword_list          — 关键词字符串列表被识别为 Sink（v3.2 P1 扩充）
#
# 回滚开关：编排器读 SECURITY_SCAN_PRESCREEN=0 时不调用此命令，
#   sinks 表全部保持 disposition='pending'，行为与 v3.1 一致。

# 测试路径正则（含 Java/Python/JS/Go 常见测试目录与文件名）
_PRESCREEN_TEST_PATH_RE = re.compile(
    r'(^|/)(tests?|__tests__|spec|specs|fixtures?|mock|mocks|testdata|testdata)/'
    r'|_test\.(java|py|go|js|ts|rb|php|cs|kt|scala)$'
    r'|\.(test|spec)\.(js|ts|jsx|tsx|mjs|cjs)$'
    r'|Test\.java$|Tests\.java$|TestCase\.java$|Spec\.scala$',
    re.IGNORECASE,
)

# 单参数纯字面量调用：foo("...") / foo('...') / foo(123) / foo(MY_CONST)
# 严格要求括号内仅一个 token，避免误杀拼接调用
_PRESCREEN_LITERAL_ARG_RE = re.compile(
    r'\(\s*(?:'
    r'"[^"\\]*"|'                          # 双引号字符串字面量
    r"'[^'\\]*'|"                          # 单引号字符串字面量
    r'-?\d+(?:\.\d+)?[fFlLdD]?|'           # 数字字面量
    r'true|false|TRUE|FALSE|null|NULL|None|nil|'  # 布尔/空
    r'[A-Z_][A-Z0-9_]*'                    # 全大写常量（如 MY_QUERY）
    r')\s*\)\s*[;,]?\s*$'
)

# 同行参数化标记：PreparedStatement / NamedQuery / @Param / ? 占位符 / 强类型 enum 等
# 注意：? 占位符的检测需谨慎，避免误匹配 URL 查询字符串和拼接 SQL。
#   - SQL 占位符典型形态：" WHERE id = ?", ... 或 " WHERE id=?",
#   - 我们要求 ? 前面是空格/等号/左括号，后面是引号闭合并紧跟逗号
_PRESCREEN_PREPARED_RE = re.compile(
    r'PreparedStatement|prepareStatement|NamedParameterJdbcTemplate|'
    r'@Param\b|@NamedQuery|'
    r'[\s=(]\?["\']\s*,|'                  # SQL 占位符 ?", 在等号/空格/括号后
    r'\?\s*[,)]\s*$|'                       # 行尾的 ? 占位符
    r'%\([a-zA-Z_]\w*\)s\s*[,)]'           # Python psycopg2 命名占位符
)

# v3.2 P1 规则 4：正则字面量元数据
# 典型形态：
#   (r'ObjectInputStream|readObject\s*\(', "deserialization"),
#   r"MultipartFile",
#   r"@RequestParam.*MultipartFile",
# 关键限制：snippet 必须从行首就是 `r'` 或 `r"`（可选 `(` 包裹），
# 避免误杀真实代码 `cursor.execute(r"SELECT 1")`（开头是 cursor.execute）
_PRESCREEN_REGEX_LITERAL_RE = re.compile(
    r'^\s*\(?\s*r[\'"]'
)

# v3.2 P1 规则 5：关键词字符串列表
# 典型形态：
#   if any(kw in combined for kw in ['eval', 'rce', 'exec(']):
#   'request.getparameter', 'req.body', 'req.query', 'req.params',
# 关键限制：
#   - `for X in [` / `for X in (` （明确的迭代列表语法）
#   - `in [` 或 `in (` 后**紧跟字符串引号**（关键词列表特征，排除函数调用）
#   - 行开头是连续多个引号包裹字符串以逗号分隔（list 字面量元素）
_PRESCREEN_KEYWORD_LIST_RE = re.compile(
    r'\bfor\s+\w+\s+in\s*[\[\(]|'                       # for X in [ / (
    r'\bin\s*[\[\(]\s*["\']|'                            # in [ ' 或 in ( "
    r'^\s*["\'][^"\']+["\']\s*,\s*["\'][^"\']+["\']'    # 'a', 'b' 列表项
)


def cmd_prescreen_sinks(args):
    """对 sinks 表执行确定性预筛，标记 disposition + disposition_reason。

    输出：JSON 摘要 {"status": "completed", "by_disposition": {...}, "by_reason": {...}}
    回滚：编排器层不调用此命令即可（不需要修改本脚本）
    """
    conn = _connect_db(args.batch_dir)
    try:
        # 仅处理 disposition='pending' 的 Sink（首次运行所有都是 pending）
        # 已经被标记为 'escalated'/'not_applicable' 的不重新评估，保证幂等
        cursor = conn.execute(
            "SELECT id, file_path, code_snippet FROM sinks WHERE disposition='pending'"
        )

        by_disposition = {"escalated": 0, "not_applicable": 0}
        by_reason = {
            "test_path": 0,
            "literal_arg": 0,
            "inline_parameterized": 0,
            "regex_literal": 0,
            "keyword_list": 0,
        }
        total = 0

        updates = []  # (id, disposition, reason)
        for row in cursor.fetchall():
            total += 1
            sid = row["id"]
            fp = row["file_path"] or ""
            snippet = (row["code_snippet"] or "").strip()

            if _PRESCREEN_TEST_PATH_RE.search(fp):
                disposition, reason = "not_applicable", "test_path"
            elif _PRESCREEN_LITERAL_ARG_RE.search(snippet):
                disposition, reason = "not_applicable", "literal_arg"
            elif _PRESCREEN_PREPARED_RE.search(snippet):
                disposition, reason = "not_applicable", "inline_parameterized"
            elif _PRESCREEN_REGEX_LITERAL_RE.search(snippet):
                disposition, reason = "not_applicable", "regex_literal"
            elif _PRESCREEN_KEYWORD_LIST_RE.search(snippet):
                disposition, reason = "not_applicable", "keyword_list"
            else:
                disposition, reason = "escalated", None

            updates.append((sid, disposition, reason))
            by_disposition[disposition] = by_disposition.get(disposition, 0) + 1
            if reason:
                by_reason[reason] = by_reason.get(reason, 0) + 1

        # 批量更新（事务保障）
        conn.executemany(
            "UPDATE sinks SET disposition=?, disposition_reason=? WHERE id=?",
            [(disp, reason, sid) for sid, disp, reason in updates]
        )
        conn.commit()

        result = {
            "status": "completed",
            "command": "prescreen-sinks",
            "total_processed": total,
            "by_disposition": by_disposition,
            "by_reason": by_reason,
        }
        print(json.dumps(result, ensure_ascii=False))
    finally:
        conn.close()


# ─── 命令: grep-cloud-resource-flow ──────────────────────────
#
# 云资源访问流预筛（v3.3 CAM/COS STS 三元组检测）
#
# 用途：在 grep-sinks 完成后，对每个 CAM/COS sink 抽取 ±15 行窗口，
#       依据 tencent-cloud-security.yaml > sts_authorization_check 共享信号库，
#       命中下述四类信号并写入 cloud_resource_flow 表：
#         - has_controllable      ：窗口内 param_names ∩ source_markers
#         - has_branch_sts        ：窗口内 sts_signals.defense_keywords
#         - has_resource_scope    ：窗口内 sts_signals.resource_scope_patterns
#         - has_config_family     ：文件级出现 sts_signals.defense_config_families
#
#       消费方：scripts/index_db.py preset cloud-resource-orphans，过滤
#       has_controllable=1 AND has_branch_sts=0 AND has_resource_scope=0 给到
#       light-inline / fast 第 4 判 / logic-scan C3.X。
#
# 设计原则：
#   - 信号库来自 yaml，避免重复维护；本命令只做窗口抽取与命中累计。
#   - sink_type 三类：cos_object_op / ci_internal_forward / cam_sig_auth。
#   - 与 grep-sinks 关系：本命令独立扫描 CAM/COS positive_patterns（不复用
#     sinks 表，避免 grep-sinks 的 SINK_SEVERITY 单一类型粒度过粗）。
#   - UNIQUE(file_path, line, sink_type) 保证幂等。

# 三类 CAM/COS sink positive patterns（与 tencent-cloud-security.yaml 对齐）
_CLOUD_SINK_GROUPS = {
    "cos_object_op": [
        r'(putObject|uploadFile|sliceUploadFile|deleteObject|deleteMultipleObject|getObject|headObject|getObjectUrl|getSignedUrl|ciProcess|imageMogr2|ImageProcess)\s*\(',
        r'(COSClient|CosS3Client|cos\.NewClient|cos-js-sdk|cos-nodejs-sdk-v5|cos-python-sdk-v5|cos-go-sdk-v5|cos-sdk-v5)',
        r'(cos\.[a-z0-9-]+\.myqcloud\.com|\.file\.myqcloud\.com|ci\.[a-z0-9-]+\.myqcloud\.com)',
    ],
    "ci_internal_forward": [
        r'(X-CI-SIGN|GenerateCiKey|CIArgs|coscgi|CosCgi|CI_S3_|pic_process|imageMogr2)',
    ],
    "cam_sig_auth": [
        r'(logic\.cam\.sigAndAuth|ModeOnlyAuth|HTTP_X_CI_SECURITY_TOKEN|HTTP_X_COS_SECURITY_TOKEN)',
    ],
}

# 默认窗口半径（行）
_CLOUD_FLOW_WINDOW = 15

# 分支锚点：用于把 sink 所在 if/switch 分支与外层窗口隔离。
# CAM 鉴权常见反例：ModeOnlyAuth 分支只做账号鉴权，q-token 写在另一分支
# (ModeAuthSign/ModeOnlySign)；±15 行窗口会同时覆盖两段，导致脚本误判已防御。
# 检测方式：若 sink 所在行落在某个 *_AUTH_ONLY 分支锚点之内（向上回溯到最近
# 一个 if/switch case 起点），仅采用该分支局部窗口（下行 +radius_inner）作为
# has_branch_sts 的判定依据；外层 q-token 不视为本分支防御。
_BRANCH_ONLY_AUTH_ANCHORS = [
    r'ModeOnlyAuth',
    r'OnlyAuth\b',
    r'ONLY_AUTH',
    r'mode\s*==\s*[A-Z_]*ONLY[_]?AUTH',
]
_BRANCH_SIGN_ANCHORS = [
    r'ModeAuthSign',
    r'ModeOnlySign',
    r'AuthSign\b',
    r'OnlySign\b',
]
_BRANCH_BOUNDARY_PATTERN = re.compile(
    r'^\s*(\}|\belse\b|\bcase\b|\bdefault\s*:|\bif\s*\(|\bswitch\s*\()'
)
# 分支局部窗口半径（行）：在分支锚点内只看更小的窗口，避免被相邻分支污染
_BRANCH_INNER_RADIUS = 6


def _load_cloud_signals(knowledge_file):
    """从 tencent-cloud-security.yaml 加载 controllable_signals / sts_signals /
    auth_element_signals 子树。

    返回 dict：
      {
        "param_names": [...],
        "source_markers": [...],
        "defense_keywords": [...],
        "defense_config_families": [...],
        "resource_scope_patterns": [...],
        # auth-element-incomplete 共享信号（来自 cos_security.auth_element_completeness_check.auth_element_signals）
        "signed_material_keywords": [...],
        "required_identity_fields": [...],
        "signature_func_keywords": [...],
        "request_header_sources": [...],
        "auth_defense_keywords": [...],
        "auth_defense_config_families": [...],
      }
    若文件缺失或 pyyaml 不可用，使用内置 fallback（与 yaml 当前内容对齐）。
    """
    fallback = {
        "param_names": [
            "key", "Key", "objectKey", "cosKey", "fileKey",
            "fileName", "filename", "filePath", "filepath",
            "path", "prefix", "bucket", "resource",
            "fileid", "file_id", "srcUri", "destUri",
        ],
        "source_markers": [
            "HTTP_", "REQUEST_", "QUERY_STRING", "PATH_INFO",
            "parser_cgi_param", "http_get_env",
            "getParameter", "getHeader",
            r"req\.", r"ctx\.", r"query\.", r"body\.", r"params\.",
            "@RequestParam", "@PathVariable", "@RequestBody",
        ],
        "defense_keywords": [
            "q-token", "q_token", "x-cos-security-token",
            "XCosSecurityToken", "X_COS_SECURITY_TOKEN", "X_CI_SECURITY_TOKEN",
            "AssumeRole", "GetFederationToken", "GetSessionToken",
            "qcloud-cos-sts", "TmpSecretId", "TmpSecretKey",
            "SessionToken", "sessionToken",
            "CredentialProvider", "BasicSessionCredentials",
        ],
        "defense_config_families": [
            r"cam_tmp_token_auth\.", r"sts\.", r"tmp_token\.",
            r"temp[_-]?credential", r"federation_token\.",
        ],
        "resource_scope_patterns": [
            r"qcs::cos:[^\"']*:prefix/",
            r"qcs::cos:[^\"']*\$\{[^}]*(user|uid|uin|tenant|openId|account|business)",
            r"qcs::cos:[^\"']*/(uid|uin|tenant|openId|business)/",
        ],
        # ── auth-element-incomplete 共享信号 ─────────────────────────────
        "signed_material_keywords": [
            "stringToSign", "string_to_sign", "signedString", "signSource",
            "signMaterial", "payloadToSign", "sign_src", "toSign",
        ],
        "required_identity_fields": [
            "ownerUin", "owner_uin", "sub_uin", "subUin",
            "ownerAppid", "owner_appid", "appId", "appid",
            "Host", "host_header", "bucket", "region",
        ],
        "signature_func_keywords": [
            "CalcSign", "GenSign", "GenerateSign", "MakeSign",
            "signRequest", "verifySign", "checkSign", "VerifySignature",
            "HmacSha256", "HmacSHA1", "HmacMD5", "MD5Hex",
            "EVP_DigestSign", "EVP_DigestVerify",
            # 低层散列原语
            "Util::md5", "Util::sha1", "Util::sha256", "Util::hmac",
            r"\bmd5\s*\(", r"\bsha1\s*\(", r"\bsha256\s*\(", r"\bhmac\s*\(",
            "MD5_Init", "MD5_Update", "MD5_Final",
            "SHA1_Init", "SHA256_Init", "HMAC_Init",
            # COS / CI 自研签名领域 token
            "plainMd5", "authMd5", "plainText.append",
            "XCosCiKey", "X-COS-CI-KEY", "cosCiKey", "CI_KEY",
            "inner_key", "authPathInfo", "authTime",
        ],
        "request_header_sources": [
            "X-COS-CI-ARGS", "X_COS_CI_ARGS", "X-CI-ARGS",
            "X-Cos-Owner-Uin", "X-Cos-Sub-Uin",
            "base64_decode", "Base64Decode", r"absl::Base64Unescape",
            "ParseFromArray", "ParseFromString",
            "getHeader", "parser_cgi_param", "http_get_env",
        ],
        "auth_defense_keywords": [
            r"append.*Host", r"append.*ownerUin",
            r"stringToSign.*ownerUin", r"stringToSign.*Host",
            r"sign_src.*owner", r"verifySign.*Host",
            r"HmacSha256.*ownerUin",
        ],
        "auth_defense_config_families": [
            r"sign_v[123]_with_identity", r"cos_sign_full_material",
            r"auth_full_binding",
        ],
    }

    if not knowledge_file or not os.path.exists(knowledge_file):
        return fallback

    try:
        import yaml
        with open(knowledge_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        sts_block = (
            data.get("cos_security", {})
                .get("sts_authorization_check", {})
        )
        ctrl = sts_block.get("controllable_signals", {}) or {}
        sts = sts_block.get("sts_signals", {}) or {}
        auth_block = (
            data.get("cos_security", {})
                .get("auth_element_completeness_check", {})
        )
        auth_sig = auth_block.get("auth_element_signals", {}) or {}
        return {
            "param_names": list(ctrl.get("param_names") or fallback["param_names"]),
            "source_markers": list(ctrl.get("source_markers") or fallback["source_markers"]),
            "defense_keywords": list(sts.get("defense_keywords") or fallback["defense_keywords"]),
            "defense_config_families": list(sts.get("defense_config_families") or fallback["defense_config_families"]),
            "resource_scope_patterns": list(sts.get("resource_scope_patterns") or fallback["resource_scope_patterns"]),
            # auth-element-incomplete 共享信号
            "signed_material_keywords":     list(auth_sig.get("signed_material_keywords")     or fallback["signed_material_keywords"]),
            "required_identity_fields":     list(auth_sig.get("required_identity_fields")     or fallback["required_identity_fields"]),
            "signature_func_keywords":      list(auth_sig.get("signature_func_keywords")      or fallback["signature_func_keywords"]),
            "request_header_sources":       list(auth_sig.get("request_header_sources")       or fallback["request_header_sources"]),
            "auth_defense_keywords":        list(auth_sig.get("defense_keywords")             or fallback["auth_defense_keywords"]),
            "auth_defense_config_families": list(auth_sig.get("defense_config_families")      or fallback["auth_defense_config_families"]),
        }
    except Exception:
        return fallback


def _read_window(file_path, line, radius):
    """读取 file_path 的 [line-radius, line+radius] 窗口，返回 (start, end, text)。

    line 为 1-based。读失败返回 (line, line, '')。
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except (OSError, IOError):
        return (line, line, "")
    total = len(all_lines)
    start = max(1, line - radius)
    end = min(total, line + radius)
    text = "".join(all_lines[start - 1:end])
    return (start, end, text)


def _scan_keywords(text, keywords):
    """返回 text 中命中的 keyword 列表（按 keyword 顺序去重）。

    keyword 视为 regex；若编译失败则降级为字面量子串匹配。
    """
    hits = []
    seen = set()
    for kw in keywords:
        if kw in seen:
            continue
        try:
            if re.search(kw, text):
                hits.append(kw)
                seen.add(kw)
                continue
        except re.error:
            pass
        # 降级：字面量
        if kw in text:
            hits.append(kw)
            seen.add(kw)
    return hits


def _detect_branch_context(file_lines, sink_line_1based, max_back=80):
    """从 sink 行向上回溯，识别 sink 所在的 if/switch 分支锚点。

    返回 dict:
        {
            "branch_kind": "only_auth" | "sign" | None,
            "branch_anchor_line": int | None,  # 锚点匹配的行号 (1-based)
            "branch_anchor_text": str,
            "branch_lower": int,               # 分支起点行（1-based, 含）
            "branch_upper": int,               # 分支终点估计行（1-based, 含；
                                                #   若无法确定则为 sink 行 + _BRANCH_INNER_RADIUS）
        }

    实现要点：
      - 仅向上回溯最多 max_back 行，命中 _BRANCH_ONLY_AUTH_ANCHORS 或
        _BRANCH_SIGN_ANCHORS 即认为 sink 处于该分支；
      - 若回溯途中先遇到 `}` / `else` / `case`/`default:`/ 顶层 `if(` / `switch(`
        且**先于**任何分支锚点出现，则视为 sink 不属于已识别分支（返回 None）。
      - 终点估计：从 sink 行向下扫描，遇到首个 _BRANCH_BOUNDARY_PATTERN 视为分支终点。
    """
    if not file_lines:
        return {
            "branch_kind": None,
            "branch_anchor_line": None,
            "branch_anchor_text": "",
            "branch_lower": sink_line_1based,
            "branch_upper": sink_line_1based + _BRANCH_INNER_RADIUS,
        }

    total = len(file_lines)
    only_auth_re = re.compile("|".join(_BRANCH_ONLY_AUTH_ANCHORS))
    sign_re = re.compile("|".join(_BRANCH_SIGN_ANCHORS))

    branch_kind = None
    anchor_line = None
    anchor_text = ""
    branch_lower = max(1, sink_line_1based - _BRANCH_INNER_RADIUS)

    # 1) 向上回溯
    upper_bound = max(1, sink_line_1based - max_back)
    for ln in range(sink_line_1based, upper_bound - 1, -1):
        line_text = file_lines[ln - 1]
        # 命中分支锚点 → 记录并停止
        if only_auth_re.search(line_text):
            branch_kind = "only_auth"
            anchor_line = ln
            anchor_text = line_text.strip()[:120]
            branch_lower = ln
            break
        if sign_re.search(line_text):
            branch_kind = "sign"
            anchor_line = ln
            anchor_text = line_text.strip()[:120]
            branch_lower = ln
            break
        # 命中分支边界（且不在 sink 行本身）→ 视为已离开本分支，停止识别
        # 注意：sink 行本身可能正好是 if(...) ModeOnlyAuth 的起始行，需排除
        if ln != sink_line_1based and _BRANCH_BOUNDARY_PATTERN.match(line_text):
            # 先遇到边界、未命中分支锚点 → 不识别分支
            break

    # 2) 向下估计分支终点
    branch_upper = min(total, sink_line_1based + _BRANCH_INNER_RADIUS)
    if branch_kind is not None:
        for ln in range(sink_line_1based + 1, min(total, sink_line_1based + max_back) + 1):
            line_text = file_lines[ln - 1]
            if _BRANCH_BOUNDARY_PATTERN.match(line_text):
                branch_upper = ln - 1
                break
            branch_upper = ln

    return {
        "branch_kind": branch_kind,
        "branch_anchor_line": anchor_line,
        "branch_anchor_text": anchor_text,
        "branch_lower": branch_lower,
        "branch_upper": branch_upper,
    }


def cmd_grep_cloud_resource_flow(args):
    """对 CAM/COS sink callsite 抽取 ±N 行窗口，写入 cloud_resource_flow 表。

    输出：JSON {"status":"completed", "total_sinks": N, "by_sink_type": {...},
                "orphan_count": N, "controllable_only": N, "fully_defended": N}
    """
    grep_tool = _detect_grep_tool()
    project_path = Path(args.project_path).resolve()
    radius = int(getattr(args, "window_radius", _CLOUD_FLOW_WINDOW))

    if not grep_tool:
        print(json.dumps({"error": "No grep tool found (rg or grep)"}))
        sys.exit(1)

    signals = _load_cloud_signals(getattr(args, "knowledge_file", None))
    param_names = signals["param_names"]
    source_markers = signals["source_markers"]
    defense_keywords = signals["defense_keywords"]
    defense_config_families = signals["defense_config_families"]
    resource_scope_patterns = signals["resource_scope_patterns"]
    # auth-element-incomplete 共享信号
    signed_material_keywords = signals.get("signed_material_keywords", [])
    required_identity_fields = signals.get("required_identity_fields", [])
    signature_func_keywords = signals.get("signature_func_keywords", [])
    request_header_sources = signals.get("request_header_sources", [])
    auth_defense_keywords = signals.get("auth_defense_keywords", [])

    conn = _connect_db(args.batch_dir)

    # 兼容旧 batch：如果 cloud_resource_flow 表缺少分支列，自动 ALTER 添加。
    # 旧扫描产物没有 branch_kind 等列；新列允许 NULL 不影响旧 batch 既有行。
    try:
        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(cloud_resource_flow)")}
        if existing_cols:
            for col_name, col_type in (
                ("branch_kind", "TEXT"),
                ("branch_anchor_line", "INTEGER"),
                ("branch_anchor_text", "TEXT"),
                ("branch_lower", "INTEGER"),
                ("branch_upper", "INTEGER"),
                ("is_branch_only_auth_no_sts", "INTEGER NOT NULL DEFAULT 0"),
                # ── auth-element-incomplete 列（v3.6+ 追加，向后兼容）──────
                ("has_signature_func",        "INTEGER NOT NULL DEFAULT 0"),
                ("signature_func_hits",       "TEXT"),
                ("has_auth_identity_missing", "INTEGER NOT NULL DEFAULT 0"),
                ("auth_identity_hits",        "TEXT"),
                ("auth_signed_material_hits", "TEXT"),
                ("auth_header_source_hits",   "TEXT"),
                ("has_auth_defense",          "INTEGER NOT NULL DEFAULT 0"),
                ("auth_defense_hits",         "TEXT"),
                ("is_auth_element_incomplete", "INTEGER NOT NULL DEFAULT 0"),
            ):
                if col_name not in existing_cols:
                    conn.execute(
                        f"ALTER TABLE cloud_resource_flow ADD COLUMN {col_name} {col_type}"
                    )
            conn.commit()
    except sqlite3.OperationalError:
        pass

    # 步骤 1：grep 三类 sink，去重为 (file, line, sink_type) → matched_text
    sinks_seen = {}  # (rel_path, line, sink_type) -> snippet
    by_sink_type = {}

    try:
        for sink_type, patterns in _CLOUD_SINK_GROUPS.items():
            type_count = 0
            for pattern in patterns:
                matches = _run_grep(pattern, str(project_path), grep_tool)
                for filepath, line_num, snippet in matches:
                    rel_path = _make_relative(filepath, str(project_path))
                    key = (rel_path, line_num, sink_type)
                    if key in sinks_seen:
                        continue
                    sinks_seen[key] = (filepath, snippet[:200])
                    type_count += 1
            if type_count > 0:
                by_sink_type[sink_type] = type_count

        # 步骤 2：对每个 sink callsite，抽窗口 + 命中累计
        # 文件级配置族 cache：同一文件只扫一次
        file_text_cache = {}     # filepath -> full text（用于 config family 文件级判定）
        file_config_hits = {}    # filepath -> [hits]

        orphan_count = 0
        controllable_only = 0
        fully_defended = 0
        branch_only_auth_no_sts_count = 0
        auth_element_incomplete_count = 0

        rows_to_insert = []

        for (rel_path, line_num, sink_type), (abs_path, snippet) in sinks_seen.items():
            # 抽窗口
            window_start, window_end, window_text = _read_window(abs_path, line_num, radius)

            # 读取整个文件的行数组（供分支识别使用；命中文件已在 file_text_cache 中）
            if abs_path not in file_text_cache:
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                        file_text_cache[abs_path] = f.read()
                except (OSError, IOError):
                    file_text_cache[abs_path] = ""
                file_config_hits[abs_path] = _scan_keywords(
                    file_text_cache[abs_path], defense_config_families
                )
            file_lines = file_text_cache[abs_path].splitlines() if file_text_cache[abs_path] else []

            # 分支识别：只对 cam_sig_auth / ci_internal_forward 类 sink 启用，
            # cos_object_op 通常没有 ModeOnlyAuth 这种 mode 分支语义，保留原窗口语义。
            branch_info = {
                "branch_kind": None,
                "branch_anchor_line": None,
                "branch_anchor_text": "",
                "branch_lower": window_start,
                "branch_upper": window_end,
            }
            branch_window_text = window_text
            if sink_type in ("cam_sig_auth", "ci_internal_forward"):
                branch_info = _detect_branch_context(file_lines, line_num)
                if branch_info["branch_kind"] is not None and file_lines:
                    lo = max(1, branch_info["branch_lower"])
                    hi = min(len(file_lines), branch_info["branch_upper"])
                    branch_window_text = "\n".join(file_lines[lo - 1:hi])

            # 可控判定：仍以外层 ±radius 窗口为准（来源往往在分支起点之前）
            ctrl_param_hits = _scan_keywords(window_text, param_names)
            ctrl_source_hits = _scan_keywords(window_text, source_markers)
            has_controllable = 1 if (ctrl_param_hits and ctrl_source_hits) else 0
            controllable_hits = ctrl_param_hits + ctrl_source_hits if has_controllable else []

            # STS 防御关键字：分支级判定
            #   - 已识别分支：仅在分支局部窗口内查找 q-token 等关键字；
            #     避免相邻 ModeAuthSign 分支的 q-token 被误算到 ModeOnlyAuth 分支。
            #   - 未识别分支：保持旧的 ±radius 窗口语义，避免影响其它仓库的检出。
            sts_hits = _scan_keywords(branch_window_text, defense_keywords)
            has_branch_sts = 1 if sts_hits else 0

            # Resource scope 收敛（沿用外层窗口；resource scope 通常出现在策略生成处）
            scope_hits = _scan_keywords(window_text, resource_scope_patterns)
            has_resource_scope = 1 if scope_hits else 0

            # 配置族文件级判定（已在 file_config_hits 中预先计算）
            cfg_hits = file_config_hits[abs_path]
            has_config_family = 1 if cfg_hits else 0

            # 分支级 OnlyAuth + 无 STS：CAM/CI 鉴权关键缺陷的强信号。
            # 即使外层窗口没有典型 source_markers（HTTP_/req. 等），只要
            # cam_sig_auth/ci_internal_forward sink 落在 ModeOnlyAuth 分支
            # 且分支内没有 q-token/sessionToken/AssumeRole，应当作为独立
            # orphan 候选输出，避免 cam_interface.cpp 这类样例漏识别。
            is_branch_only_auth_no_sts = 1 if (
                sink_type in ("cam_sig_auth", "ci_internal_forward")
                and branch_info.get("branch_kind") == "only_auth"
                and has_branch_sts == 0
            ) else 0

            # ─── auth-element-incomplete 判定 ───────────────────────────
            # 仅对 cam_sig_auth / ci_internal_forward 类 sink 启用；
            # cos_object_op 通常不直接做签名，跳过避免误报。
            sig_func_hits = []
            auth_identity_hits = []
            auth_signed_mat_hits = []
            auth_header_src_hits = []
            auth_def_hits = []
            has_signature_func = 0
            has_auth_identity_missing = 0
            has_auth_defense = 0
            is_auth_element_incomplete = 0

            if sink_type in ("cam_sig_auth", "ci_internal_forward"):
                # 1) 当前分支或函数级宽窗口出现签名/校验函数关键字
                #    签名材料组装通常位于函数入口，sink 在数十行后，因此用 ±60
                #    行宽窗口扫签名原语，避免漏报（如 Util::md5(plainText...) ）。
                sig_func_hits = _scan_keywords(branch_window_text, signature_func_keywords)
                if not sig_func_hits:
                    sig_func_hits = _scan_keywords(window_text, signature_func_keywords)
                if not sig_func_hits and file_lines:
                    _sig_lo = max(1, line_num - 60)
                    _sig_hi = min(len(file_lines), line_num + 60)
                    _sig_window_text = "\n".join(file_lines[_sig_lo - 1:_sig_hi])
                    sig_func_hits = _scan_keywords(_sig_window_text, signature_func_keywords)
                has_signature_func = 1 if sig_func_hits else 0

                # 2) 同窗口（外层 ±radius 行 + 函数级宽窗口）出现 required_identity_fields 与
                #    request_header_sources 共现 → 身份字段被「事后」消费。
                #    身份字段的解析点同样可能远离 sink（如 ParseFromArray 在函数中段、
                #    sink 在函数尾部 onlyAuth），因此对身份判定也使用函数级宽窗口。
                if file_lines:
                    _id_lo = max(1, line_num - 60)
                    _id_hi = min(len(file_lines), line_num + 60)
                    _id_window_text = "\n".join(file_lines[_id_lo - 1:_id_hi])
                else:
                    _id_window_text = window_text
                auth_identity_hits = _scan_keywords(_id_window_text, required_identity_fields)
                auth_header_src_hits = _scan_keywords(_id_window_text, request_header_sources)
                has_auth_identity_missing = 1 if (auth_identity_hits and auth_header_src_hits) else 0

                # 3) 防御：分支内或函数级窗口内 signed_material_keywords ∩ required_identity_fields 共现
                #    或匹配 auth_defense_keywords（如 stringToSign.*ownerUin）
                auth_signed_mat_hits = _scan_keywords(branch_window_text, signed_material_keywords)
                auth_def_hits = _scan_keywords(branch_window_text, auth_defense_keywords)
                # 强语义防御：signed_material 关键字与身份字段在同分支共现
                sm_id_co_occur = bool(auth_signed_mat_hits) and bool(
                    _scan_keywords(branch_window_text, required_identity_fields)
                )
                # 兜底：函数级宽窗口内若 signed_material 与身份字段共现也视为防御
                if not sm_id_co_occur and file_lines:
                    _wider_sm = _scan_keywords(_id_window_text, signed_material_keywords)
                    _wider_id = _scan_keywords(_id_window_text, required_identity_fields)
                    sm_id_co_occur = bool(_wider_sm) and bool(_wider_id)
                has_auth_defense = 1 if (auth_def_hits or sm_id_co_occur) else 0

                # 4) 触发条件：签名函数存在 + 身份字段事后消费 + 分支内无防御
                is_auth_element_incomplete = 1 if (
                    has_signature_func == 1
                    and has_auth_identity_missing == 1
                    and has_auth_defense == 0
                ) else 0

            # 统计
            if has_controllable and not has_branch_sts and not has_resource_scope:
                orphan_count += 1
            elif has_controllable and (has_branch_sts or has_resource_scope):
                fully_defended += 1
            elif has_controllable:
                controllable_only += 1
            if is_branch_only_auth_no_sts:
                branch_only_auth_no_sts_count += 1
            if is_auth_element_incomplete:
                auth_element_incomplete_count += 1

            rows_to_insert.append((
                rel_path, line_num, sink_type, snippet,
                has_controllable, json.dumps(controllable_hits, ensure_ascii=False),
                has_branch_sts, json.dumps(sts_hits, ensure_ascii=False),
                has_resource_scope, json.dumps(scope_hits, ensure_ascii=False),
                has_config_family, json.dumps(cfg_hits, ensure_ascii=False),
                window_start, window_end,
                branch_info["branch_kind"],
                branch_info["branch_anchor_line"],
                branch_info["branch_anchor_text"],
                branch_info["branch_lower"],
                branch_info["branch_upper"],
                is_branch_only_auth_no_sts,
                has_signature_func, json.dumps(sig_func_hits, ensure_ascii=False),
                has_auth_identity_missing, json.dumps(auth_identity_hits, ensure_ascii=False),
                json.dumps(auth_signed_mat_hits, ensure_ascii=False),
                json.dumps(auth_header_src_hits, ensure_ascii=False),
                has_auth_defense, json.dumps(auth_def_hits, ensure_ascii=False),
                is_auth_element_incomplete,
            ))

        # 步骤 3：批量写入（INSERT OR IGNORE 保证幂等）
        conn.executemany("""
            INSERT OR IGNORE INTO cloud_resource_flow
            (file_path, line, sink_type, sink_snippet,
             has_controllable, controllable_hits,
             has_branch_sts, branch_sts_hits,
             has_resource_scope, resource_scope_hits,
             has_config_family, config_family_hits,
             window_start, window_end,
             branch_kind, branch_anchor_line, branch_anchor_text,
             branch_lower, branch_upper,
             is_branch_only_auth_no_sts,
             has_signature_func, signature_func_hits,
             has_auth_identity_missing, auth_identity_hits,
             auth_signed_material_hits, auth_header_source_hits,
             has_auth_defense, auth_defense_hits,
             is_auth_element_incomplete)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_to_insert)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()

    result = {
        "status": "completed",
        "command": "grep-cloud-resource-flow",
        "total_sinks": len(sinks_seen),
        "by_sink_type": by_sink_type,
        "orphan_count": orphan_count,
        "controllable_only_count": controllable_only,
        "fully_defended_count": fully_defended,
        "branch_only_auth_no_sts_count": branch_only_auth_no_sts_count,
        "auth_element_incomplete_count": auth_element_incomplete_count,
        "window_radius": radius,
        "grep_tool": grep_tool,
        "knowledge_file": getattr(args, "knowledge_file", None),
    }
    print(json.dumps(result, ensure_ascii=False))


# ─── 命令: grep-all ──────────────────────────────────────────
#
# Fast 模式一键预筛（v3.5.5 性能优化）
#
# 用途：一次 Bash 调用串行执行所有 grep 子命令 + prescreen-sinks，
#       减少 LLM 往返次数。等价于原来 6 条 pattern_grep.py 串行调用。
#       _detect_grep_tool() 已缓存，同进程内只探测一次。

def cmd_grep_all(args):
    """一次性运行所有 grep 子命令 + prescreen（Fast 模式专用）。

    输出：聚合 JSON {"status":"completed", "commands": {...}, "total_time_ms": N}
    任一子命令失败不中断其余，error 记录在对应 command 的结果中。
    """
    import io
    import contextlib
    import time

    t0 = time.monotonic()

    # 构造各子命令的 mock args（用简单 namespace 替代 argparse.Namespace）
    _Ns = type('Args', (), {})
    base_kw = {'batch_dir': args.batch_dir, 'project_path': args.project_path}

    sub_commands = [
        ('grep-sinks', cmd_grep_sinks, {**base_kw, 'patterns_file': args.patterns_file}),
        ('grep-entries', cmd_grep_entries, dict(base_kw)),
        ('grep-defenses', cmd_grep_defenses, dict(base_kw)),
        ('grep-secrets', cmd_grep_secrets, dict(base_kw)),
        ('grep-attack-surface', cmd_grep_attack_surface, dict(base_kw)),
        ('grep-cloud-resource-flow', cmd_grep_cloud_resource_flow, {
            **base_kw,
            'knowledge_file': getattr(args, 'knowledge_file', None),
            'window_radius': getattr(args, 'window_radius', _CLOUD_FLOW_WINDOW),
        }),
    ]
    if not args.skip_prescreen:
        sub_commands.append(('prescreen-sinks', cmd_prescreen_sinks, {'batch_dir': args.batch_dir}))

    results = {}
    for name, fn, kw in sub_commands:
        mock_args = _Ns()
        for k, v in kw.items():
            setattr(mock_args, k, v)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                fn(mock_args)
            captured = buf.getvalue().strip()
            # 尝试解析子命令的 JSON 输出
            try:
                results[name] = json.loads(captured)
            except (json.JSONDecodeError, ValueError):
                results[name] = {"status": "completed", "raw": captured[:500]}
        except SystemExit:
            results[name] = {"status": "error", "error": "SystemExit"}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    output = {
        "status": "completed",
        "command": "grep-all",
        "commands": results,
        "total_time_ms": elapsed_ms,
    }
    print(json.dumps(output, ensure_ascii=False))


# ─── CLI 入口 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="批量模式匹配工具 — Sink/入口点/防御/敏感信息/攻击面检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 批量 Sink grep
  %(prog)s grep-sinks \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --patterns-file resource/scan-data/sink-patterns.yaml \\
    --project-path .

  # 入口点检测
  %(prog)s grep-entries \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --project-path .

  # 防御模式检测
  %(prog)s grep-defenses \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --project-path .

  # 敏感信息检测
  %(prog)s grep-secrets \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --project-path .

  # 攻击面检测
  %(prog)s grep-attack-surface \\
    --batch-dir .codebuddy/security-scan/runs/project-deep-xxx \\
    --project-path .
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # grep-sinks
    p_sinks = subparsers.add_parser("grep-sinks", help="批量 Sink grep")
    p_sinks.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_sinks.add_argument("--patterns-file", required=True, help="sink-patterns.yaml 路径")
    p_sinks.add_argument("--project-path", required=True, help="项目根目录")

    # grep-entries
    p_entries = subparsers.add_parser("grep-entries", help="入口点检测")
    p_entries.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_entries.add_argument("--project-path", required=True, help="项目根目录")

    # grep-defenses
    p_defenses = subparsers.add_parser("grep-defenses", help="防御模式检测")
    p_defenses.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_defenses.add_argument("--project-path", required=True, help="项目根目录")

    # grep-secrets
    p_secrets = subparsers.add_parser("grep-secrets", help="敏感信息检测")
    p_secrets.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_secrets.add_argument("--project-path", required=True, help="项目根目录")

    # grep-attack-surface
    p_surface = subparsers.add_parser("grep-attack-surface", help="攻击面检测")
    p_surface.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_surface.add_argument("--project-path", required=True, help="项目根目录")

    # prescreen-sinks（v3.2 脚本预筛 Ledger）
    p_prescreen = subparsers.add_parser(
        "prescreen-sinks",
        help="对 sinks 表执行确定性预筛（v3.2 Fast 模式 Ledger）"
    )
    p_prescreen.add_argument("--batch-dir", required=True, help="扫描批次目录")

    # grep-cloud-resource-flow（v3.3 CAM/COS STS 三元组检测）
    p_cloud = subparsers.add_parser(
        "grep-cloud-resource-flow",
        help="CAM/COS sink ±15 行窗口抽取，写 cloud_resource_flow 表"
    )
    p_cloud.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_cloud.add_argument("--project-path", required=True, help="项目根目录")
    p_cloud.add_argument(
        "--knowledge-file", default=None,
        help="tencent-cloud-security.yaml 路径（可选；缺省时使用内置 fallback 信号库）"
    )
    p_cloud.add_argument(
        "--window-radius", type=int, default=_CLOUD_FLOW_WINDOW,
        help=f"窗口半径行数（默认 {_CLOUD_FLOW_WINDOW}）"
    )

    # grep-all（v3.5.5 Fast 模式一键预筛）
    p_all = subparsers.add_parser(
        "grep-all",
        help="一次性运行所有 grep + prescreen（Fast 模式专用，减少 LLM 往返）"
    )
    p_all.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p_all.add_argument("--project-path", required=True, help="项目根目录")
    p_all.add_argument("--patterns-file", required=True, help="sink-patterns.yaml 路径")
    p_all.add_argument("--skip-prescreen", action="store_true",
                        help="跳过 prescreen-sinks（等价于 SECURITY_SCAN_PRESCREEN=0）")
    p_all.add_argument(
        "--knowledge-file", default=None,
        help="tencent-cloud-security.yaml 路径（可选；用于 grep-cloud-resource-flow）"
    )
    p_all.add_argument(
        "--window-radius", type=int, default=_CLOUD_FLOW_WINDOW,
        help=f"cloud-resource-flow 窗口半径行数（默认 {_CLOUD_FLOW_WINDOW}）"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "grep-sinks": cmd_grep_sinks,
        "grep-entries": cmd_grep_entries,
        "grep-defenses": cmd_grep_defenses,
        "grep-secrets": cmd_grep_secrets,
        "grep-attack-surface": cmd_grep_attack_surface,
        "grep-cloud-resource-flow": cmd_grep_cloud_resource_flow,
        "prescreen-sinks": cmd_prescreen_sinks,
        "grep-all": cmd_grep_all,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
