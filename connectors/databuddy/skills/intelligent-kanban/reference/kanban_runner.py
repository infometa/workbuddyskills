"""
看板 Runner —— Spec → 看板产物 的唯一执行入口。

LLM 永不触碰本文件。LLM 只编写 kanban_spec_*.py（约 80~120 行声明式），
调用 build_kanban(spec) 即完成全流程：
    1. 取数 SQL 生成 + wedatacli query-sql 执行（lakehouse + OLAP 双路径同入口）
    2. 时间字段解析（spark_safe_* helper，物理消除 H11/H12/H13）
    3. 编译 Spec → SLOT_DATA（19 类图统一处理，物理消除 H9/H10/H14/H15/H16）
    4. 编译 Spec → sqlSlots（同环比 WITH 双层结构，物理消除 H22/H32）
    5. 拼装 subtitle（数据源 + 更新时间；供 DSL page_title.description 使用）
    6. 调 builder.write_kanban_outputs（sqlSlots lint 兜底 H19/H21/H24/H27 等 + 准备 save_meta）
    7. 调 kanban_dsl_emitter.emit_dsl（DSL 落盘 + 一次性写入 kanban_save_params.json 的 HtmlContent/SqlSlots）
    8. 调 builder.update_to_kanban_list（UpdateAiKanBan 写 PREVIEW；三端统一入库权威源）

设计原则：
- **通用**：不假设任何业务领域；任何场景都能写 spec
- **零样板**：业务方零样板代码；DSL 字段直接映射数据/视觉意图
- **三端统一**：入库唯一权威源 = UpdateAiKanBan.HtmlContent(DSL) + UpdateAiKanBan.SqlSlots(Datasets)
- **可逃生**：复杂 SQL 走 raw_sql 旁路，仍走 builder 全 lint
"""

from __future__ import annotations

import os
import re
import sys
import glob
import json
import time
import shlex
import shutil
import hashlib
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from kanban_dsl import (
    Spec, Source, Dim, Metric, Chart, Compare,
)

# ============================================================
# 兼容常量：Python 3.11 之前 f-string 表达式内不允许出现反斜杠
# （PEP 701 落地于 3.12）。把所有 SQL 拼接里 ',\n  '.join(...) 通过
# 模块级常量在 f-string 外层使用，保证 runner 在 3.10 / 3.11 沙箱也能直接 import。
# ============================================================
_NL_INDENT = ',\n  '   # SELECT 列分隔（缩进对齐 SELECT 后两空格）

# ============================================================
# 0. 加载 builder（保留兼容，复用全部底层 API）
# ============================================================

def _load_builder() -> Dict[str, Any]:
    """exec 加载 builder.py 到独立命名空间，返回符号表。

    路径解析（first-wins，兼容多种部署布局）：
      1. runner 自身 __file__ 所在目录 —— 最强定位，reference/ 内部相对稳定
      2. CODEBUDDY_PLUGIN_ROOT 下按新→旧顺序探测：
         <root>/scenarios/data-analysis/skills/intelligent-kanban/reference/
         <root>/l3-skill-scenario/intelligent-kanban/reference/
      3. os.getcwd()/reference/ 兜底（本地开发）
    """
    candidates: List[str] = []
    try:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanban_builder.py'))
    except NameError:
        pass
    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '').strip()
    if plugin_root:
        candidates.append(os.path.join(
            plugin_root, 'scenarios', 'data-analysis', 'skills',
            'intelligent-kanban', 'reference', 'kanban_builder.py',
        ))
        candidates.append(os.path.join(
            plugin_root, 'l3-skill-scenario', 'intelligent-kanban',
            'reference', 'kanban_builder.py',
        ))
    candidates.append(os.path.join(os.getcwd(), 'reference', 'kanban_builder.py'))

    builder_path = next((p for p in candidates if p and os.path.isfile(p)), '')
    if not builder_path:
        raise FileNotFoundError(
            '[Runner] kanban_builder.py 未找到；尝试路径：\n  - ' + '\n  - '.join(candidates)
        )

    ns: Dict[str, Any] = {'__name__': 'kanban_builder', '__file__': builder_path}
    with open(builder_path, 'r', encoding='utf-8') as f:
        exec(compile(f.read(), builder_path, 'exec'), ns)
    return ns


_B = _load_builder()


# ============================================================
# 1. 取数 SQL 构造 + 执行
# ============================================================

def _build_fetch_sql(src: Source, route_meta: Optional[dict] = None) -> str:
    """生成远端取数 SQL：只做 `SELECT * + LIMIT`，永不下推 WHERE。

    设计契约（与 prefetch_table.py:_build_fetch_sql 对齐）：
      - 表的取数接口端已有行数保护；这里不做 schema 列裁剪、不做分阶段取数
      - spec.source.where 由 DuckDB _kb_src 视图本地过滤，零远端二次开销
      - cache key 固化为 (table, where='', limit)，prefetch 写入与 runner 命中共用同一把 key
      - 外部数据源按方言裁剪表名段数，避免 MySQL/PostgreSQL/GaussDB 收到三段式
    """
    conn_type = (route_meta or {}).get('connection_type') or ''
    query_table = _runner_project_table_name_for_sql(src.table, conn_type)
    return f'SELECT *\n FROM {query_table}\n LIMIT {int(src.limit)}'


# ============================================================
# 1bis. wedatacli query-sql 客户端（lakehouse + OLAP 双路径同入口）
# ────────────────────────────────────────────────────────────
# Runner 不再直接调用工具任务 HTTP 接口；统一走与 search 相同的
# wedatacli 入口。CLI 内部承接提交、轮询、CSV 下载和结果落盘，本处只消费
# 清洗后的 {Status, TaskId, CsvPath, Schema, CostMs}，并从落盘信封补充
# quant 里的真实执行资源字段；JobId 只作排障字段，不能写入 ExecuteResourceId。
# ============================================================

# 【常量对齐锚点】此值必须与 prefetch_table.py:QUERY_SQL_CLI_TIMEOUT_BUFFER 同步。
#   两处均为「Python subprocess.wait 相对 CLI 自身 --timeout 的额外收尾/落盘缓冲」，
#   偏离会导致：值过小 → subprocess 先超时杀 CLI，落盘信封不完整；
#             值过大 → 用户观察到超时后仍需继续等 60s+，体感差。
_QUERY_SQL_CLI_TIMEOUT_BUFFER = 60  # 若调整此值，请同步 prefetch_table.py 端

# 【聚合打印累加器】sqlSlots 方言段数裁剪的命中统计，Step C 结束时统一聚合打印。
#   避免 KPI + 30 chart 场景下 30+ 行「已裁剪 xxx」刷屏。
#   由 _project_slot_sql_table_segments 增量累加、_flush_slot_projection_summary 消费清零。
_slot_projection_stats: Dict[str, int] = {}


def _resolve_runner_plugin_root() -> str:
    """定位 plugin 根目录（含 l0-cli/wedatacli.sh 的目录）。

    与 prefetch_table.py::_resolve_plugin_root 策略一致：
    env 优先 → __file__ 向上爬升找 l0-cli/wedatacli.sh → ../../.. 兜底。
    """
    env_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '').strip()
    if env_root and os.path.isdir(env_root):
        return os.path.normpath(env_root)
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.path.join(os.getcwd(), 'reference')
    cur = here
    for _ in range(8):
        if os.path.isfile(os.path.join(cur, 'l0-cli', 'wedatacli.sh')):
            return os.path.normpath(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.normpath(os.path.join(here, '..', '..', '..'))


_RUNNER_PLUGIN_ROOT = _resolve_runner_plugin_root()
_RUNNER_WEDATACLI_SH = os.path.join(_RUNNER_PLUGIN_ROOT, 'l0-cli', 'wedatacli.sh')
_RUNNER_WEDATACLI_BIN_CHECKED = False


def _resolve_runner_plugin_env() -> str:
    env_path = os.environ.get('WEDATA_PLUGIN_ENV', '').strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    default_path = os.path.expanduser('~/.wedata/plugin-env')
    if os.path.isfile(default_path):
        return default_path
    return ''


def _runner_workspace_folder_extra_args() -> list:
    """从 env WEDATA_WORKSPACE_FOLDER 读取工作空间目录，非空则返回 ['--workspace_folder', <path>]。

    - DataBuddy 沙箱场景：env 未设置 → 返回 [] → CLI argv 不变。
    - WorkBuddy 连接器场景：intelligent-kanban SKILL.md 已在 Step B/D 前置 export，
      追加到 argv 后满足 WorkBuddy 严格模式（runtimeMode=workbuddy）对 --workspace_folder 的强制要求。
    """
    wf = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if wf:
        return ['--workspace_folder', wf]
    return []


def _ensure_runner_wedatacli_executable() -> None:
    global _RUNNER_WEDATACLI_BIN_CHECKED
    if _RUNNER_WEDATACLI_BIN_CHECKED:
        return
    _RUNNER_WEDATACLI_BIN_CHECKED = True
    try:
        if os.path.isfile(_RUNNER_WEDATACLI_SH) and not os.access(_RUNNER_WEDATACLI_SH, os.X_OK):
            os.chmod(_RUNNER_WEDATACLI_SH, 0o755)
        cli_dir = os.path.dirname(_RUNNER_WEDATACLI_SH)
        if os.path.isdir(cli_dir):
            for name in os.listdir(cli_dir):
                if name.startswith('wedatacli-'):
                    p = os.path.join(cli_dir, name)
                    if os.path.isfile(p) and not os.access(p, os.X_OK):
                        os.chmod(p, 0o755)
    except Exception:
        pass


def _runner_wedatacli_available() -> bool:
    if _resolve_runner_plugin_env():
        return True
    if os.path.isfile(_RUNNER_WEDATACLI_SH):
        return True
    return bool(shutil.which('wedatacli'))


def _runner_wedatacli(args: List[str], timeout: int,
                      input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    if not args:
        raise RuntimeError('[Runner] wedatacli args 为空')
    str_args = [str(a) for a in args] + _runner_workspace_folder_extra_args()
    plugin_env = _resolve_runner_plugin_env()
    if plugin_env:
        quoted_args = ' '.join(shlex.quote(a) for a in str_args)
        cmd = f'. {shlex.quote(plugin_env)} && "$WEDATACLI_PATH" {quoted_args}'
        return subprocess.run(
            cmd, shell=True,
            input=input_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace', timeout=timeout,
        )
    if os.path.isfile(_RUNNER_WEDATACLI_SH):
        _ensure_runner_wedatacli_executable()
        return subprocess.run(
            [_RUNNER_WEDATACLI_SH] + str_args,
            input=input_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace', timeout=timeout,
        )
    exe = shutil.which('wedatacli') or 'wedatacli'
    return subprocess.run(
        [exe] + str_args,
        input=input_text,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace', timeout=timeout,
    )


def _runner_read_cli_json_stdout(stdout: str) -> Dict[str, Any]:
    stdout = (stdout or '').strip()
    if not stdout:
        raise RuntimeError('[Runner] wedatacli 输出为空')
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find('{')
        end = stdout.rfind('}')
        if start < 0 or end <= start:
            raise RuntimeError(f'[Runner] wedatacli 输出非 JSON: {stdout[:500]}')
        try:
            data = json.loads(stdout[start:end + 1])
        except json.JSONDecodeError as ex:
            raise RuntimeError(f'[Runner] wedatacli 输出非 JSON: {stdout[:500]}') from ex
    if isinstance(data, dict) and data.get('truncated') and data.get('file'):
        file_path = data.get('file') or ''
        if file_path and os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f'[Runner] wedatacli JSON 输出不是对象: {type(data).__name__}')
    return data


_RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID: Optional[str] = None
_RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED = False


def _runner_find_resource_id_in_obj(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ''
    basic = obj.get('BasicInfo') if isinstance(obj.get('BasicInfo'), dict) else {}
    available = obj.get('AvailableStatus')
    if available not in (None, '', 1, '1'):
        return ''
    resource_type = basic.get('ResourceType') if isinstance(basic, dict) else None
    if resource_type not in (None, '', 3, '3'):
        return ''
    for key in ('ResourceId', 'resourceId', 'resource_id'):
        rid = str(basic.get(key) or obj.get(key) or '').strip()
        if rid:
            return rid
    return ''


def _runner_extract_first_analysis_resource_id(data: Any) -> str:
    if not isinstance(data, dict):
        return ''
    response = data.get('Response') if isinstance(data.get('Response'), dict) else data
    payload = response.get('Data') if isinstance(response.get('Data'), dict) else response
    resources = payload.get('Resources') if isinstance(payload, dict) else None
    if not isinstance(resources, list):
        return ''
    for item in resources:
        rid = _runner_find_resource_id_in_obj(item)
        if not rid:
            continue
        basic = item.get('BasicInfo') if isinstance(item, dict) and isinstance(item.get('BasicInfo'), dict) else {}
        exec_available = basic.get('ExecAvailableStatus')
        if exec_available in (None, '', 1, '1'):
            return rid
    return ''


def _runner_default_analysis_resource_id() -> str:
    """获取 lakehouse 默认数据分析计算资源 ID；失败返回空，避免把 JobId 误写为资源。"""
    global _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID, _RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED
    if _RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED:
        return _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID or ''
    _RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED = True
    _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID = ''
    if not _runner_wedatacli_available():
        return ''
    workspace_id = os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '').strip()
    if not workspace_id:
        cfg_path = os.path.expanduser('~/.wedata/config.json')
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f) or {}
            workspace_id = str(cfg.get('defaultWorkspace') or '').strip()
        except Exception:
            workspace_id = ''
    if not workspace_id:
        return ''
    payload = {
        'WorkspaceId': workspace_id,
        'Page': {'PageNumber': 1, 'PageSize': 100},
        'ResourceTypes': [3],
    }
    try:
        result = _runner_wedatacli(
            ['ListComputeResourceOptions', '-'],
            timeout=30,
            input_text=json.dumps(payload, ensure_ascii=False),
        )
        if result.returncode != 0:
            return ''
        data = _runner_read_cli_json_stdout(result.stdout or '')
        _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID = _runner_extract_first_analysis_resource_id(data)
    except Exception:
        _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID = ''
    return _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID or ''


def _runner_load_query_sql_quant(task_id: str) -> Dict[str, Any]:
    task_id = (task_id or '').strip()
    if not task_id:
        return {}
    path = os.path.expanduser(os.path.join('~', '.wedata', 'query-sql-results', f'{task_id}.json'))
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            env = json.load(f) or {}
        result = env.get('Result') or '{}'
        findings = json.loads(result) if isinstance(result, str) else (result or {})
        quant_raw = findings.get('quant') or '{}'
        quant = json.loads(quant_raw) if isinstance(quant_raw, str) else (quant_raw or {})
        return quant if isinstance(quant, dict) else {}
    except Exception:
        return {}


class _SqlQueryClient:
    """wedatacli query-sql 取数客户端。CLI 内部承接提交、轮询和 CSV 下载。"""

    def __init__(self):
        self.available = _runner_wedatacli_available()

    def query(self, sql: str, sql_type: int, data_source_id: str = '',
              compute_resource: str = '', total_timeout: int = 600) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError('[Runner] wedatacli 不可用（plugin-env / l0-cli / PATH 均未找到）')
        sql = (sql or '').strip()
        if not sql:
            raise RuntimeError('[Runner] query-sql SQL 为空')
        try:
            cli_timeout = max(1, int(total_timeout or 600))
        except (TypeError, ValueError):
            cli_timeout = 600
        process_timeout = cli_timeout + _QUERY_SQL_CLI_TIMEOUT_BUFFER

        sql_file = ''
        try:
            with tempfile.NamedTemporaryFile(
                'w', encoding='utf-8', suffix='.sql', prefix='kanban_runner_query_', delete=False,
                dir=_resolve_workspace_tmp_dir(),
            ) as f:
                f.write(sql)
                f.write('\n')
                sql_file = f.name

            args = [
                'query-sql',
                '--sql-file', sql_file,
                '--sql-type', str(int(sql_type)),
                '--timeout', f'{cli_timeout}s',
                '--no-progress',
                '--output', 'json',
            ]
            if data_source_id:
                args.extend(['--data-source-id', data_source_id])
            if compute_resource:
                args.extend(['--compute-resource', compute_resource])

            try:
                result = _runner_wedatacli(args, timeout=process_timeout)
            except subprocess.TimeoutExpired as ex:
                raise RuntimeError(f'[Runner] wedatacli query-sql 调用超时（{process_timeout}s）') from ex
        finally:
            if sql_file:
                try:
                    os.unlink(sql_file)
                except OSError:
                    pass

        data = None
        parse_err = None
        if (result.stdout or '').strip():
            try:
                data = _runner_read_cli_json_stdout(result.stdout)
            except Exception as ex:
                parse_err = ex
        if result.returncode != 0:
            msg = ''
            if isinstance(data, dict):
                msg = str(data.get('Message') or data.get('message') or '').strip()
            if not msg:
                msg = (result.stderr or result.stdout or str(parse_err or '')).strip()
            raise RuntimeError(f'[Runner] wedatacli query-sql failed (code={result.returncode}): {msg[:500]}')
        if data is None:
            if parse_err:
                raise parse_err
            raise RuntimeError('[Runner] wedatacli query-sql 未返回 JSON')

        status = str(data.get('Status') or '').upper()
        task_id = str(data.get('TaskId') or '').strip()
        if status != 'SUCCESS':
            msg = str(data.get('Message') or 'query-sql failed without message').strip()
            raise RuntimeError(f'[Runner] wedatacli query-sql failed: task_id={task_id} msg={msg}')
        csv_path = str(data.get('CsvPath') or '').strip()
        if not csv_path or not os.path.isfile(csv_path):
            raise FileNotFoundError(f'[Runner] wedatacli query-sql SUCCESS 但 CsvPath 不存在: {csv_path or "<empty>"}')

        quant = _runner_load_query_sql_quant(task_id)
        job_id = str(quant.get('JobId') or '').strip()
        resource_id = str(
            quant.get('ExecuteResourceId')
            or quant.get('ResourceId')
            or quant.get('ComputeResource')
            or quant.get('ComputeResourceId')
            or compute_resource
            or ''
        ).strip()
        return {
            'task_id': task_id,
            'csv_path': csv_path,
            'schema': data.get('Schema') or [],
            'cost_ms': data.get('CostMs') or 0,
            'job_id': job_id,
            'resource_id': resource_id,
            'quant': quant,
        }


# ── 取数结果 CSV 缓存（按"数据物理形态"复用：table+limit）──
# 设计动机：Spec 重写时，LLM 抄写的字面格式漂移会导致 sha1(SQL) 全部 miss。
#         改为锁定"数据物理形态"后：
#           - cache key = sha1(table+where='' + limit)：列变更 / SQL 空白差异不再 miss
#           - 远端取数统一 SELECT * + LIMIT，不做 schema 列裁剪或分阶段取数
#           - spec.where 由 DuckDB 本地过滤，远端永远只取一次同一物理表样本
# 安全护栏：
#   1) limit 不同 → 严格 miss（不串数据）；表名按精确字面对齐
#   2) TTL 默认 21600s（6 小时），可通过 KANBAN_SQL_CACHE_TTL 调整
#   3) KANBAN_SQL_CACHE_DISABLE=1 一键关闭
#   4) 缓存目录：KANBAN_SQL_CACHE_DIR > WEDATA_WORKSPACE_FOLDER/tmp/wedata_kanban_cache > /tmp/wedata_kanban_cache
def _resolve_sql_cache_dir():
    explicit = os.environ.get('KANBAN_SQL_CACHE_DIR', '').strip()
    if explicit:
        return explicit
    workspace_folder = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        return os.path.join(workspace_folder, 'tmp', 'wedata_kanban_cache')
    return '/tmp/wedata_kanban_cache'


_SQL_CACHE_DIR = _resolve_sql_cache_dir()
_SQL_CACHE_DEFAULT_TTL = 6 * 3600  # 6 小时


def _resolve_workspace_tmp_dir():
    """临时文件目录：WEDATA_WORKSPACE_FOLDER/tmp > 系统默认（None 让 tempfile 自选）。"""
    workspace_folder = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        tmp_dir = os.path.join(workspace_folder, 'tmp')
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            return tmp_dir
        except OSError:
            return None
    return None


def _normalize_table_for_cache_key(table: str) -> str:
    """把表名归一到"最短稳定形态"作为 cache key 输入。

    问题：prefetch 用完整三段式 full_name 写 cache（如 gsdb_catalog.public.t_user），
    runner 端 spec.source.table 由 LLM 按 SKILL.md 规约填写：
      - lakehouse/StarRocks/Doris → 三段式（写盘 = 读取，天然一致）
      - MySQL/PG/GaussDB          → 两段式 db.table（与 prefetch 三段式**不一致**）
    结果：MySQL/PG/GaussDB 场景 100% cache miss → runner 走同步 query-sql 兜底
         → 服务端要 computeResource → 报 `computeResource is blank`。

    修复：统一取"尾两段"（catalog.db.table → db.table；db.table → db.table），
    双端算 hash 前都做同一次归一。SPARK/StarRocks/Doris 三段式经归一裁到两段仍等价
    （二者也因该归一天然一致，零回归）。
    """
    name = (table or '').strip()
    if not name or '.' not in name:
        return name
    parts = [p for p in name.split('.') if p]
    if len(parts) <= 2:
        return name
    return '.'.join(parts[-2:])


def _data_cache_key(table: str, where: str, limit: int) -> str:
    """对"数据物理形态"取 sha1 前 16 位作为缓存 key。

    与 SQL 字面解耦：列序、字面空白差异都不影响 key —— 这是消除 LLM
    重写 spec 导致缓存 miss 的核心。table 归一到尾两段（跨方言双端一致，
    详见 _normalize_table_for_cache_key），where 折叠连续空白，limit 强转 int。
    """
    norm_table = _normalize_table_for_cache_key(table)
    norm_where = re.sub(r'\s+', ' ', (where or '').strip())
    payload = f'{norm_table}||{norm_where}||{int(limit)}'
    return hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]


def _load_cache_meta(key: str, ttl: int) -> Optional[Dict[str, Any]]:
    """读取并校验单个 CSV 缓存 meta：文件存在 + csv 存在 + 未过期。任何异常 → None。"""
    meta_path = os.path.join(_SQL_CACHE_DIR, f'{key}.meta.json')
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception:
        return None
    csv_path = (meta.get('csv_path') or '').strip()
    created_at = float(meta.get('created_at') or 0)
    if not csv_path or not os.path.isfile(csv_path):
        return None
    if ttl > 0 and (time.time() - created_at) > ttl:
        return None
    return meta


def _load_route_meta(key: str) -> Optional[Dict[str, Any]]:
    """读取 route-only/CSV meta 中的路由字段；不要求 CSV 已落盘。"""
    meta_path = os.path.join(_SQL_CACHE_DIR, f'{key}.meta.json')
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f) or {}
    except Exception:
        return None
    if not isinstance(meta, dict):
        return None
    has_route = any(
        meta.get(k) not in (None, '')
        for k in ('connection_type', 'connection_id', 'sql_type', 'data_source_id')
    )
    return meta if has_route else None


def _route_meta_from_src(src) -> dict:
    """从 prefetch 预写的 meta 中读取路由；失败返回空 dict。"""
    if src is None:
        return {}
    try:
        table = (getattr(src, 'table', '') or '').strip()
        limit = int(getattr(src, 'limit', 0) or 0)
        if not table or limit <= 0:
            return {}
        meta = _load_route_meta(_data_cache_key(table, '', limit))
        if not meta:
            return {}
        return {
            'connection_type': meta.get('connection_type') or '',
            'connection_id': meta.get('connection_id') or meta.get('data_source_id') or '',
            'sql_type': int(meta.get('sql_type') or 1),
            'data_source_id': meta.get('data_source_id') or meta.get('connection_id') or '',
            'job_id': meta.get('job_id') or '',
        }
    except Exception:
        return {}


def _sql_cache_lookup(src) -> Tuple[str, str, dict]:
    """按 spec.source 的物理数据形态查询 prefetch 缓存。

    设计契约（与 _build_fetch_sql 配套）：
      - 远端取数 SQL 永不带 WHERE，cache key 固化为 sha1(table, where='', limit)
      - 取数统一 SELECT *，不做 schema 列裁剪；spec.columns 的列投影在 DuckDB 本地完成
      - 任一异常都视为未命中（缓存绝不能影响主流程）

    返回 (csv_path, resource_id, route_meta)；未命中返回 ('', '', route_meta或{})。
    route_meta 含：connection_type / connection_id / sql_type / job_id（runner miss
    兜底同步取数直接复用，无需重查 wedatacli search 路由信息）。
    """
    route_meta = _route_meta_from_src(src)
    if os.environ.get('KANBAN_SQL_CACHE_DISABLE', '').strip() in ('1', 'true', 'True'):
        return '', '', route_meta
    try:
        ttl = int(os.environ.get('KANBAN_SQL_CACHE_TTL', _SQL_CACHE_DEFAULT_TTL))
    except ValueError:
        ttl = _SQL_CACHE_DEFAULT_TTL
    if ttl <= 0 or not src:
        return '', '', route_meta

    try:
        table = (getattr(src, 'table', '') or '').strip()
        limit = int(getattr(src, 'limit', 0) or 0)
    except Exception:
        return '', '', route_meta
    if not table or limit <= 0:
        return '', '', route_meta

    meta = _load_cache_meta(_data_cache_key(table, '', limit), ttl)
    if not meta:
        return '', '', route_meta
    route_meta = {
        'connection_type': meta.get('connection_type') or route_meta.get('connection_type', ''),
        'connection_id': meta.get('connection_id') or meta.get('data_source_id') or route_meta.get('connection_id', ''),
        'sql_type': int(meta.get('sql_type') or route_meta.get('sql_type') or 1),
        'data_source_id': meta.get('data_source_id') or meta.get('connection_id') or route_meta.get('data_source_id', ''),
        'job_id': meta.get('job_id') or route_meta.get('job_id', ''),
    }
    resource_id = str(meta.get('resource_id') or '').strip()
    if not resource_id and int(route_meta.get('sql_type') or 1) != 3:
        resource_id = _runner_default_analysis_resource_id()
    return meta['csv_path'], resource_id, route_meta


# ── prefetch pending 等待（治本：消除"LLM 写 spec 太快 → prefetch 没跑完 → runner miss"竞态）──
# 协议（与 prefetch_table.py 的 _write_pending/_clear_pending 对齐）：
#   <SQL_CACHE_DIR>/<sha1(table||""||limit)>.pending.json
#   - prefetch 主进程在 fork 前写下：表示该表预取已启动
#   - 子进程跑完 wedatacli query-sql 终态（成功/失败/超时）后清除
#   - runner 在 _sql_cache_lookup miss 时，若发现 pending 存在 → 短轮询等子进程落 CSV meta，
#     等到了就走缓存命中路径，没等到再退化到同步 wedatacli query-sql 取数
# 安全护栏：
#   1) 仅当 pending 文件最近修改时间 < KANBAN_PREFETCH_PENDING_STALE_SEC（默认 600s）才相信
#   2) 等待总时长 ≤ KANBAN_PREFETCH_WAIT_SEC（默认 200s），到点即放弃
#   3) KANBAN_PREFETCH_WAIT_SEC=0 关闭整个等待机制（回到旧行为）
def _wait_for_prefetch(src) -> Tuple[str, str, dict]:
    """若发现该 (table, where='', limit) 的 prefetch 仍在跑（pending 占位存在），
    短轮询等待其落 meta；命中后返回 (csv_path, resource_id, route_meta)，否则返回 ('','', {})。

    无副作用：调用方在 miss 后才进入本函数；本函数本身不写文件、不杀进程。
    """
    if not src:
        return '', '', {}
    try:
        wait_total = int(os.environ.get('KANBAN_PREFETCH_WAIT_SEC', '200'))
    except ValueError:
        wait_total = 200
    if wait_total <= 0:
        return '', '', {}
    try:
        stale_sec = int(os.environ.get('KANBAN_PREFETCH_PENDING_STALE_SEC', '600'))
    except ValueError:
        stale_sec = 600

    try:
        table = (getattr(src, 'table', '') or '').strip()
        limit = int(getattr(src, 'limit', 0) or 0)
    except Exception:
        return '', '', {}
    if not table or limit <= 0:
        return '', '', {}

    route_meta = _route_meta_from_src(src)
    pending_path = os.path.join(
        _SQL_CACHE_DIR, f'{_data_cache_key(table, "", limit)}.pending.json'
    )
    if not os.path.isfile(pending_path):
        return '', '', route_meta
    # 旧 pending（≥ stale_sec 没动）视为僵尸，直接放弃等待 —— 大概率是上一轮 prefetch
    # 进程异常崩溃没走 finally 清理。
    try:
        if (time.time() - os.path.getmtime(pending_path)) > stale_sec:
            return '', '', route_meta
    except OSError:
        return '', '', route_meta

    print(f'⏳ 检测到 prefetch 正在预取 {os.path.basename(table)}，最长等待 {wait_total}s...')
    deadline = time.time() + wait_total
    poll_interval = 0.5
    while time.time() < deadline:
        # 优先尝试命中（ttl 校验内置在 _sql_cache_lookup 里）
        csv_path, rid, route_meta = _sql_cache_lookup(src)
        if csv_path:
            elapsed = wait_total - max(0, deadline - time.time())
            print(f'⚡ prefetch 已就绪（等待 {elapsed:.1f}s）：{os.path.basename(csv_path)}')
            return csv_path, rid, route_meta
        # pending 在等待途中被清掉（说明子进程已退出但没成功写 CSV meta，比如 query-sql 失败）→ 立即放弃
        if not os.path.isfile(pending_path):
            return '', '', _route_meta_from_src(src)
        time.sleep(poll_interval)
    print(f'⌛ prefetch 等待超时（{wait_total}s），回退到同步取数')
    return '', '', _route_meta_from_src(src)



def _sql_cache_store(src, sql: str, csv_path: str, resource_id: str,
                    route_meta: Optional[dict] = None,
                    job_id: str = '') -> None:
    """按 src 物理形态写入缓存。失败静默（绝不影响主流程）。

    与 prefetch_table.py:_store_cache 字段对齐：
      - resource_id：真实执行资源 ID，供看板 PREVIEW 入库 UpdateAiKanBan.ExecuteResourceId 使用；
        不得用 query-sql JobId/TaskId 兜底，否则 lakehouse 刷新会把任务 ID 当计算资源。
      - connection_type / connection_id / sql_type：runner 同步 miss 兜底复用路由
      - job_id：query-sql 落盘 quant.JobId（追日志用）
    """
    if not src or not csv_path:
        return
    try:
        os.makedirs(_SQL_CACHE_DIR, exist_ok=True)
        table = (getattr(src, 'table', '') or '').strip()
        limit = int(getattr(src, 'limit', 0) or 0)
        if not table or limit <= 0:
            return
        key = _data_cache_key(table, '', limit)
        meta_path = os.path.join(_SQL_CACHE_DIR, f'{key}.meta.json')
        rm = route_meta or {}
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({
                'csv_path': csv_path,
                'resource_id': resource_id or '',
                'created_at': time.time(),
                'sql_preview': sql.strip()[:200],
                'table': table,
                'where': '',
                'limit_used': limit,
                'prefetched': False,
                'route_only': False,
                'connection_type': rm.get('connection_type') or '',
                'connection_id': rm.get('connection_id') or rm.get('data_source_id') or '',
                'sql_type': int(rm.get('sql_type') or 1),
                'data_source_id': rm.get('data_source_id') or rm.get('connection_id') or '',
                'job_id': job_id or '',
                'route_updated_at': time.time(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


# OLAP 路由：与 nl2sql_datasource.go::canonicalConnectionType 对齐
_RUNNER_CANONICAL_MAP = {
    '': 'SPARK', 'SPARK': 'SPARK', 'HIVE': 'SPARK', 'LAKEHOUSE': 'SPARK', 'DLC': 'SPARK',
    'MYSQL': 'MYSQL',
    'STARROCKS': 'STARROCKS', 'STAR_ROCKS': 'STARROCKS', 'EMR_STARROCKS': 'STARROCKS',
    'GAUSSDB': 'GAUSSDB', 'OPENGAUSS': 'GAUSSDB', 'OPEN_GAUSS': 'GAUSSDB',
    'DORIS': 'DORIS', 'APACHE_DORIS': 'DORIS', 'TCHOUSE_D': 'DORIS',
    'POSTGRESQL': 'POSTGRESQL', 'POSTGRES': 'POSTGRESQL', 'PGSQL': 'POSTGRESQL', 'PG': 'POSTGRESQL',
}


def _runner_canonical_conn_type(raw: str) -> str:
    s = (raw or '').strip().upper().replace('-', '_').replace(' ', '_')
    return _RUNNER_CANONICAL_MAP.get(s, s)


def _runner_build_route(conn_type: str, conn_id: str) -> Tuple[int, str]:
    """路由 (sql_type, data_source_id)。未知类型直接报错，避免 OLAP 误走 lakehouse。"""
    raw_type = (conn_type or '').strip()
    raw_id = (conn_id or '').strip()
    canon = _runner_canonical_conn_type(raw_type)
    if canon == 'SPARK':
        if not raw_type and raw_id:
            raise RuntimeError('[Runner] empty ConnectionType with non-empty ConnectionId')
        return 1, ''
    if canon in ('MYSQL', 'STARROCKS', 'GAUSSDB', 'DORIS', 'POSTGRESQL'):
        if not raw_id:
            raise RuntimeError(f'[Runner] OLAP {canon} 缺 ConnectionId（路由信息丢失）')
        return 3, raw_id
    raise RuntimeError(f'[Runner] unsupported connection_type: {conn_type}')


def _runner_table_name_segments_for_conn(conn_type: str) -> int:
    """返回该数据源 SQL 可接受的表名最大段数，与 nl2sql_dialect.go 对齐。"""
    canon = _runner_canonical_conn_type(conn_type)
    if canon in ('SPARK', 'STARROCKS', 'DORIS'):
        return 3
    if canon in ('MYSQL', 'GAUSSDB', 'POSTGRESQL'):
        return 2
    return 2


def _runner_project_table_name_for_sql(table: str, conn_type: str) -> str:
    """按 OLAP 方言裁剪表名段数；不加引号、不改列，避免额外方言差异。"""
    name = (table or '').strip()
    if not name or '.' not in name:
        return name
    parts = name.split('.')
    max_segments = _runner_table_name_segments_for_conn(conn_type)
    if max_segments <= 0 or len(parts) <= max_segments:
        return name
    return '.'.join(parts[-max_segments:])


def _fetch_table_csv(sql: str, src=None) -> Tuple[str, str]:
    """通过 wedatacli query-sql 取数 —— lakehouse + OLAP 双路径同入口。

    Args:
        sql:      初始取数 SQL；拿到路由后会按数据源方言重建为 SELECT * + LIMIT。
        src:      Spec.source 实例（用于缓存按"数据物理形态"寻址）。**必传**：
                  缺省时缓存层会保守 miss，等价于禁用缓存。

    返回 (csv_path, resource_id)：
      - csv_path：取数结果 csv 最新路径（失败抛错）
      - resource_id：看板 PREVIEW 入库用 ExecuteResourceId，来自 CLI 落盘 quant 中的真实资源字段，
                     或 lakehouse 默认数据分析资源；JobId/TaskId 只用于排障，不能当作执行资源回填。

    缓存语义（详见 _sql_cache_lookup）：
      - cache key = sha1(src.table + where='' + src.limit)
      - 远端取数统一 SELECT * + LIMIT，不做 schema 列裁剪或分阶段取数
      - 默认 TTL 21600s（6 小时）；KANBAN_SQL_CACHE_DISABLE=1 关闭

    路由信息复用：
      - 优先从 prefetch 写入的 route-only/CSV meta 读取 (connection_type/connection_id/sql_type)
      - 缓存缺失但有 route-only meta → 同步 wedatacli query-sql 仍可正确走 OLAP
      - 无路由信息才按 SPARK/lakehouse 兼容历史三段式表
    """
    # ── 缓存命中：直接返回 ──
    cached_csv, cached_rid, route_meta = _sql_cache_lookup(src) if src is not None else ('', '', {})
    if cached_csv:
        print(f'⚡ 命中取数缓存（跳过 wedatacli query-sql）：{os.path.basename(cached_csv)}')
        return cached_csv, cached_rid

    # ── 缓存未命中但 prefetch 仍在跑：短轮询等待落 CSV meta（消除 LLM 写 spec 太快竞态）──
    waited_csv, waited_rid, waited_route = _wait_for_prefetch(src) if src is not None else ('', '', {})
    if waited_route:
        route_meta = waited_route
    if waited_csv:
        return waited_csv, waited_rid

    # ── 同步 wedatacli query-sql 兜底取数 ──
    # 路由信息优先复用 prefetch 写入的 route-only/CSV meta；缺失才按 lakehouse 兼容历史三段式。
    if not route_meta:
        route_meta = _route_meta_from_src(src)

    sql_type, data_source_id = _runner_build_route(
        route_meta.get('connection_type', ''),
        route_meta.get('connection_id') or route_meta.get('data_source_id') or '',
    )
    if src is not None:
        sql = _build_fetch_sql(src, route_meta)

    try:
        _total_timeout = int(os.environ.get('KANBAN_SQL_TIMEOUT', '600'))
    except (TypeError, ValueError):
        _total_timeout = 600
    if _total_timeout <= 0:
        _total_timeout = 600

    compute_resource = _runner_default_analysis_resource_id() if int(sql_type or 1) != 3 else ''
    print('📊 执行取数 SQL（wedatacli query-sql）...')
    got = _SqlQueryClient().query(
        sql.strip(),
        sql_type=sql_type,
        data_source_id=data_source_id,
        compute_resource=compute_resource,
        total_timeout=_total_timeout,
    )
    csv_path = str(got.get('csv_path') or '').strip()
    if not csv_path or not os.path.isfile(csv_path):
        raise FileNotFoundError(f'[Runner] wedatacli query-sql 成功但 CsvPath 不存在: {csv_path or "<empty>"}')

    job_id = str(got.get('job_id') or got.get('task_id') or '').strip()
    resource_id = str(got.get('resource_id') or '').strip()

    # 写入缓存（失败静默）—— 同步路径写入的 meta 与 prefetch 协议字节级对齐
    if not route_meta:
        route_meta = {'connection_type': '', 'connection_id': '', 'sql_type': sql_type}
    route_meta.setdefault('data_source_id', data_source_id)
    _sql_cache_store(src, sql, csv_path, resource_id, route_meta=route_meta, job_id=job_id)
    return csv_path, resource_id


# ============================================================
# 2. 时间维度 / 表达式工具（_spark_time_expr 定义见下文 §2quater，
#    与 _dim_sql 紧邻；DuckDB 本地引擎 §2bis 不依赖该函数，故先定义引擎、
#    再在 §2quater 集中给出维度 SQL 生成器，避免一处函数双份定义的协议漂移）
# ============================================================


# ============================================================
# 2bis. DuckDB 本地引擎（取代 pandas 双套语义模拟器）
# ------------------------------------------------------------
# 设计：spec → 1 段 SQL → DuckDB 本地执行 → DataFrame → slot_data。
# 平台保存后 Spark 跑同一段 SQL，本地与远端"同源同语义"，无差异。
# 兼容性桥（Spark → DuckDB）：通过 macro 注入。
# ============================================================

# duckdb 是 runner 唯一的"非纯标准库"硬依赖。沙箱里若未预装，裸 `import duckdb`
# 会抛 ModuleNotFoundError，进而被 LLM 解读成"需要 pip install duckdb"并把
# "需要安装依赖 / 已安装 / 重新执行"等过程性文字写进 Step D 输出，污染面向用户的
# 看板创建回执。这里在 runner 自身收敛该兜底：缺失 → 静默 pip install 钉版 → 再 import。
# 钉版 1.5.3：当前实测稳定版（macro / read_csv(columns=) / strftime 字面量行为一致）。
def _ensure_duckdb(pinned: str = '1.5.3'):
    """沙箱无 duckdb 时静默安装钉版。stdout/stderr 全部吃掉，避免污染 Step D 输出。"""
    try:
        import duckdb as _d  # type: ignore
        return _d
    except ImportError:
        import subprocess as _sp
        import sys as _sys
        try:
            _sp.run(
                [_sys.executable, '-m', 'pip', 'install', '--quiet',
                 '--disable-pip-version-check', '--no-input',
                 f'duckdb=={pinned}'],
                check=True,
                stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
            )
        except Exception:
            # 钉版装不上时退回不钉版本（沙箱可能有 mirror 缓存约束），仍然静默
            _sp.run(
                [_sys.executable, '-m', 'pip', 'install', '--quiet',
                 '--disable-pip-version-check', '--no-input', 'duckdb'],
                check=True,
                stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
            )
        import duckdb as _d  # type: ignore  # noqa: E402
        return _d

duckdb = _ensure_duckdb()  # noqa: E402  顶部已有所有 import，但 duckdb 是新增依赖，集中放此节首部

_LOCAL_VIEW = '_kb_src'


def _spec_type_to_duck(t: str) -> Optional[str]:
    """Spec.source.columns 里的 type → DuckDB 类型字符串。

    覆盖 prefetch_table.py schema JSON 的 Spark/Hive 类型集合：
      string/varchar/char            → VARCHAR
      int/integer/bigint/smallint/tinyint → BIGINT（统一 BIGINT 防溢出）
      double/float/real/decimal(.,.) → DOUBLE
      boolean/bool                   → BOOLEAN
      date                           → DATE
      timestamp / timestamp_tz / timestamp_ltz / timestamp_ntz / timestamp(p)
                                     → VARCHAR（统一交给 spark_safe_to_timestamp 宏处理）
      其它（array/map/struct/未知）→ None（让 DuckDB 自己推断）

    设计取舍（为何 timestamp 系列降级 VARCHAR 而非 TIMESTAMP/TIMESTAMPTZ）：
      ① CSV 形态多样（`2024-01-15 08:30:00` / `...+08:00` / `...Z` / `2024/01/15`），
         DuckDB read_csv 的内置 sniffer 对 timestamp_tz 后缀解析不稳定，会引发
         "Could not convert string to TIMESTAMP" 类告警；
      ② 若映射为 TIMESTAMPTZ，下游 strftime 输出依赖 session timezone，
         与 Spark 端基于 session tz 的归一化基准不一致，会导致天/周/月分桶
         偏移一天（数据失真，比告警严重得多）；
      ③ 走 VARCHAR + spark_safe_to_timestamp 宏（已在宏内剥时区后缀再 TRY_CAST）
         能确定性消化所有 timestamp 变体，且与 Spark try_to_timestamp 行为对齐。
    """
    if not t:
        return None
    s = str(t).strip().lower()
    if s in ('string', 'varchar', 'char', 'text', 'clob', 'bpchar') or s.startswith(('varchar', 'char')):
        return 'VARCHAR'
    if s in (
        'int', 'integer', 'bigint', 'long', 'smallint', 'tinyint',
        # PostgreSQL/GaussDB 原生（未经 wedatacli 类型归一时会直接透出）
        'int2', 'int4', 'int8',
        'serial', 'bigserial', 'smallserial',
    ):
        return 'BIGINT'
    if (
        s in ('double', 'float', 'real', 'float4', 'float8', 'money')
        or s.startswith('decimal')
        or s.startswith('numeric')
    ):
        return 'DOUBLE'
    if s in ('boolean', 'bool'):
        return 'BOOLEAN'
    if s == 'date':
        return 'DATE'
    # timestamp 系列（含 timestamp_tz/_ltz/_ntz、带精度括号、
    # PG/GaussDB 的 `timestamp with[out] time zone`、MySQL 的 `datetime`）
    # 一律降级 VARCHAR，让 spark_safe_to_timestamp 统一吃掉时区/格式差异。
    if s.startswith('timestamp') or s in ('datetime', 'timetz', 'time'):
        return 'VARCHAR'
    return None  # 未知类型让 DuckDB 自己 sniff


def _csv_columns_dict(src) -> Optional[Dict[str, str]]:
    """从 Spec.source 派生 read_csv 的 columns={col:type} 显式声明。

    返回 None 表示无法精确映射（让 DuckDB 走自动推断兜底）。
    """
    if not src or not getattr(src, 'columns', None):
        return None
    out: Dict[str, str] = {}
    has_any_typed = False
    for c in src.columns:
        if isinstance(c, dict):
            name = c.get('name')
            t = c.get('type')
            if not name:
                continue
            duck_t = _spec_type_to_duck(t) if t else None
            if duck_t:
                out[name] = duck_t
                has_any_typed = True
            else:
                out[name] = 'VARCHAR'  # 兜底走字符串，spark_safe_* 宏可正常转
        elif isinstance(c, str):
            out[c] = 'VARCHAR'
    return out if has_any_typed else None


def _open_duck(source, *, columns=None, src=None):
    """开 DuckDB 内存连接 → 注册 _kb_src 视图 → 安装 Spark 兼容宏。

    Args:
        source: CSV 路径（str）或 pandas DataFrame。CSV 路径优先（无需 pyarrow）。
        columns: 列名列表（兼容老调用方，已忽略，由 src.columns 派生类型）。
        src:     Source 实例（含 columns 类型声明 + where 谓词）。强烈建议传入：
                 ① 使 read_csv 走显式类型而非启发式推断（消除 VARCHAR 聚合返工）；
                 ② spec.source.where 在本地 _kb_src 视图层应用（远端永不下推 WHERE，
                    保证同一物理表的远端取数全局唯一，由 prefetch 缓存承接）。
    """
    con = duckdb.connect(database=':memory:')
    # spec.source.where 本地下沉到 _kb_src 视图层（远端 fetch_sql 不带 WHERE）
    where_clause = ''
    try:
        _where = (getattr(src, 'where', '') or '').strip() if src is not None else ''
        if _where:
            where_clause = f' WHERE {_where}'
    except Exception:
        where_clause = ''
    if isinstance(source, str) and os.path.isfile(source):
        # 路径 1：DuckDB 原生 read_csv（零第三方依赖，最快）
        # 关键修复（防返工）：
        #   1) 显式 columns={col:type} 让 DuckDB 按 spec.source.columns 声明读取，
        #      避免把整数列当 VARCHAR、对其 AVG/SUM 时报 'No function matches' 的返工。
        #   2) nullstr 把 'null'/'NULL'/空串都当 NULL，避免 CAST('null' AS BIGINT) 炸。
        #   3) header=true + sample_size=-1：保留 header 但不用 sniff 类型（已显式给出）。
        col_types = _csv_columns_dict(src)
        if col_types:
            cols_sql = ', '.join(f"'{k}': '{v}'" for k, v in col_types.items())
            _explicit_load_sql = (
                f"CREATE OR REPLACE VIEW {_LOCAL_VIEW} AS "
                f"SELECT * FROM read_csv('{source}', "
                f"header=true, columns={{{cols_sql}}}, "
                # P0 修复（2026-09-14）：wedatacli query-sql 落盘 CSV 每个字段被双引号
                # 包裹（RFC4180 pandas to_csv(quoting=QUOTE_MINIMAL/ALL) 默认行为），
                # DuckDB 1.5.3 用 columns={} 时不会 sniff quote，默认 quote='\''（单引号），
                # 导致 CAST '\"2023\"' AS BIGINT / '\"0.0000\"' AS DOUBLE 全部失败，
                # ignore_errors=true 又把所有 CAST 失败的 cell 静默置 NULL，
                # 度量列/数值维度列 100% 变 NULL → SUM(...) 全 NULL → 8/8 slot 空看板。
                # 修法：显式声明 quote='\"' + escape='\"'（RFC4180 引号内 ""→"，同一符号）。
                f"quote='\"', escape='\"', "
                f"nullstr=['null','NULL','None','\\\\N','','NaT','nan','NaN'], "
                f"ignore_errors=true){where_clause}"
            )
            try:
                con.execute(_explicit_load_sql)
            except Exception as _ex:
                # 兜底降级（P0 通用性修复）：spec.columns 与 CSV 实际列数不匹配时，
                # DuckDB sniffer 会拒绝构建 view（Error when sniffing file... does not match
                # the number of columns）。此时 fallback 到 read_csv_auto + auto_type_candidates
                # 白名单，让 DuckDB 用自身列检测（避开 TIMESTAMPTZ 触发 pytz 崩溃），
                # 并 stderr 提示用户 spec.source.columns 应与远端 schema 完整对齐。
                import sys as _sys
                _err_snip = str(_ex).split('\n', 1)[0][:180]
                print(
                    f"⚠️  [Runner][软告警] spec.source.columns 与 CSV 列不匹配 "
                    f"(sniffer: {_err_snip})；已 fallback 到自动类型推断加载。\n"
                    f"    修法：让 spec.source.columns 与远端 schema 一一对应 "
                    f"(可以从 Step B prefetch_table.py 返回的 columns 完整抄入)。",
                    file=_sys.stderr,
                )
                con.execute(
                    f"CREATE OR REPLACE VIEW {_LOCAL_VIEW} AS "
                    f"SELECT * FROM read_csv_auto('{source}', header=true, sample_size=-1, "
                    # 与主路径一致：显式 quote='\"' 让 DuckDB 剥掉 CSV 字段外双引号。
                    # read_csv_auto 虽会 sniff quote，但显式传更稳（配合 --v1.5.3 极端脏数据）。
                    f"quote='\"', escape='\"', "
                    f"nullstr=['null','NULL','None','\\\\N','','NaT','nan','NaN'], "
                    f"auto_type_candidates=['BIGINT','DOUBLE','VARCHAR','DATE','TIMESTAMP','BOOLEAN']){where_clause}"
                )
        else:
            # 退路：无类型声明时仍走 read_csv_auto，但补 nullstr 兜底空值字面量
            # （含 pandas to_csv 默认序列化产生的 NaT/nan）
            # 关键防崩（P0）：auto_type_candidates 白名单排除 TIMESTAMPTZ / TIMESTAMP_NS 等
            # 需要 pytz 的类型 —— ISO 时区字符串（'2024-01-15T10:00:00.000+08:00'）会被
            # DuckDB 自动识别成 TIMESTAMPTZ，任何 SELECT 都触发 "Required module 'pytz' failed
            # to import"，用户环境无 pytz 时（macOS 默认 python3）整个 build_kanban 崩溃。
            # 白名单外的类型会自动 fallback 到 VARCHAR，交给 spark_safe_to_timestamp 宏统一
            # 剥时区后缀再解析（宏内已 TRY_CAST AS TIMESTAMP naive，零 pytz 依赖）。
            con.execute(
                f"CREATE OR REPLACE VIEW {_LOCAL_VIEW} AS "
                f"SELECT * FROM read_csv_auto('{source}', header=true, sample_size=-1, "
                # 与主路径一致：显式 quote='\"' 让 DuckDB 剥掉 CSV 字段外双引号
                # （wedatacli query-sql 落盘的 RFC4180 CSV 字段被双引号包裹）。
                f"quote='\"', escape='\"', "
                f"nullstr=['null','NULL','None','\\\\N','','NaT','nan','NaN'], "
                f"auto_type_candidates=['BIGINT','DOUBLE','VARCHAR','DATE','TIMESTAMP','BOOLEAN']){where_clause}"
            )
    else:
        # 路径 2：DataFrame（dry_run / 测试用）。DuckDB 1.5+ 在新版 pandas 下默认走 Arrow C Stream，
        # 环境无 pyarrow 时回退 PyRelation。这里先解包 builder 的 _TimeParseResult。
        df = source
        if hasattr(df, '_df'):  # builder._TimeParseResult 包装
            df = df._df
        # DataFrame 路径同样需要承接 where：先注册为底层 relation，再叠加 WHERE 视图
        _RAW_VIEW = f'{_LOCAL_VIEW}__raw'
        try:
            con.register(_RAW_VIEW, df)
        except Exception:
            rel = con.from_df(df)
            rel.create_view(_RAW_VIEW, replace=True)
        con.execute(
            f"CREATE OR REPLACE VIEW {_LOCAL_VIEW} AS "
            f"SELECT * FROM {_RAW_VIEW}{where_clause}"
        )
    _install_spark_macros(con)
    # 绑定连接方言（用于 _to_local_sql 里 OLAP → DuckDB 方言翻译）。
    # 未拿到 route_meta 时静默跳过，保持 lakehouse 语义零回归。
    try:
        _rm = _route_meta_from_src(src) if src is not None else {}
        _ct = (_rm or {}).get('connection_type') or ''
        if _ct:
            _set_conn_type(con, _ct)
    except Exception:
        pass
    return con


def _install_spark_macros(con):
    """让 spec 中写的 Spark 风格 SQL 在 DuckDB 上原样可跑。

    覆盖 builder.py 暴露的 spark_safe_* 函数族 + percentile_approx，
    与远端 Spark 行为对齐（含 ISO 周）。

    注意：DuckDB 的 strftime 要求 format 必须是常量字面量，因此 spark_safe_date_format
    用 CASE 分支映射常见 Spark 格式，覆盖业务实际使用的全部模式。
    """
    con.execute(
        """
        -- 兼容 Spark try_to_timestamp 的多形态输入：
        --   `2024-01-15 08:30:00`        → TRY_CAST 直通
        --   `2024-01-15T08:30:00+08:00`  → 剥掉 +HH:MM/+HHMM/Z 后缀再 TRY_CAST
        --   `2024-01-15T08:30:00Z`       → 同上
        -- 之所以剥时区而非保留 TIMESTAMPTZ：DuckDB session tz 与 Spark session tz
        -- 基准不一致时，分桶 strftime 会跨天偏移；剥时区后两端 naive timestamp 对齐。
        CREATE OR REPLACE MACRO spark_safe_to_timestamp(x) AS
            COALESCE(
                -- 主路径：剥时区后 TRY_CAST，覆盖标准 ISO / Hive / 带时区后缀
                TRY_CAST(
                    regexp_replace(CAST(x AS VARCHAR), '([+-][0-9]{2}:?[0-9]{2}|Z)$', '')
                    AS TIMESTAMP
                ),
                -- 低粒度兜底：'yyyy' / 'yyyy-MM' / 'yyyy/MM' / 'yyyy.MM' / 'yyyy-M' / 'yyyyMM'
                -- 严格用 regexp_full_match 锁形态，避免与完整日期/unix 时间戳冲突。
                CASE
                    WHEN regexp_full_match(CAST(x AS VARCHAR), '^[0-9]{4}([-/.][0-9]{1,2})?$')
                        THEN COALESCE(
                            try_strptime(regexp_replace(CAST(x AS VARCHAR), '[./]', '-', 'g'), '%Y-%m'),
                            try_strptime(CAST(x AS VARCHAR), '%Y')
                        )
                    WHEN regexp_full_match(CAST(x AS VARCHAR), '^[0-9]{6}$')
                        THEN try_strptime(CAST(x AS VARCHAR), '%Y%m')
                    ELSE NULL
                END,
                -- 月份英文缩写/全称兜底（BI 报表常见 'Jan 2025' / '25-Jan-2025' 等）
                -- 与 _try_to_timestamp_rewrite 候选格式列表保持同步；任一命中即返回 TIMESTAMP。
                -- 用 try_strptime（NULL-safe）逐个尝试，全 miss 返回 NULL，行为与 Spark 一致。
                COALESCE(
                    try_strptime(CAST(x AS VARCHAR), '%b %Y'),
                    try_strptime(CAST(x AS VARCHAR), '%B %Y'),
                    try_strptime(CAST(x AS VARCHAR), '%b-%Y'),
                    try_strptime(CAST(x AS VARCHAR), '%B-%Y'),
                    try_strptime(CAST(x AS VARCHAR), '%Y-%b'),
                    try_strptime(CAST(x AS VARCHAR), '%Y %b'),
                    try_strptime(CAST(x AS VARCHAR), '%d-%b-%Y'),
                    try_strptime(CAST(x AS VARCHAR), '%d %b %Y'),
                    try_strptime(CAST(x AS VARCHAR), '%d-%B-%Y'),
                    try_strptime(CAST(x AS VARCHAR), '%d %B %Y'),
                    try_strptime(CAST(x AS VARCHAR), '%b %d, %Y'),
                    try_strptime(CAST(x AS VARCHAR), '%B %d, %Y')
                )
            );

        CREATE OR REPLACE MACRO spark_safe_to_date(x) AS
            TRY_CAST(
                regexp_replace(CAST(x AS VARCHAR), '([+-][0-9]{2}:?[0-9]{2}|Z)$', '')
                AS DATE
            );

        CREATE OR REPLACE MACRO spark_safe_date_format(ts, fmt) AS
            CASE fmt
                WHEN 'yyyy-MM-dd'          THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%Y-%m-%d')
                WHEN 'yyyy-MM'             THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%Y-%m')
                WHEN 'yyyy'                THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%Y')
                WHEN 'yyyy-MM-dd HH:mm:ss' THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%Y-%m-%d %H:%M:%S')
                WHEN 'yyyy/MM/dd'          THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%Y/%m/%d')
                WHEN 'HH:mm:ss'            THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%H:%M:%S')
                WHEN 'yyyy-MM-dd HH'       THEN strftime(TRY_CAST(ts AS TIMESTAMP), '%Y-%m-%d %H')
                ELSE CAST(ts AS VARCHAR)
            END;

        CREATE OR REPLACE MACRO spark_safe_week_format(ts) AS
            strftime(TRY_CAST(ts AS TIMESTAMP), '%G-W%V');

        CREATE OR REPLACE MACRO percentile_approx(x, p) AS
            quantile_cont(x, p);

        -- ---------------- Spark 内置函数 → DuckDB 兼容 macro ----------------
        -- 这些函数在 Spark 端原生存在但 DuckDB 没有；spec / sqlSlots / spark_safe_to_timestamp_extended
        -- 展开后都可能引用它们。仅作本地预览兜底，远端入库时 sqlSlots 走 Spark 原生实现，行为不变。
        --
        -- ★ 保真性要求（与 Spark Asia/Shanghai 集群行为对齐）：
        --   1. 时区：from_unixtime 必须按 session tz 解释 epoch（用 to_timestamp + CAST 实现）
        --   2. NULL 容错：所有 macro NULL 输入返回 NULL（不报错），与 Spark 一致
        --   3. 数据类型：months_between 必须返回 DOUBLE（含小数月差，Spark 同义）
        --   4. 字符串容错：from_unixtime 遇到非数字字符串返回 NULL（Spark 同义）

        -- from_unixtime(秒) → TIMESTAMP（按 session 时区解释）
        -- DuckDB to_timestamp(epoch_sec) 返回 TIMESTAMPTZ；CAST 到 TIMESTAMP 时按 session tz 转换 →
        -- 在 Asia/Shanghai 集群上与 Spark `from_unixtime` 输出 yyyy-MM-dd HH:mm:ss 字符串一致。
        -- TRY_CAST(s AS BIGINT) 兜底字符串数字/非数字/NULL 三种形态。
        CREATE OR REPLACE MACRO from_unixtime(s) AS
            CASE
                WHEN s IS NULL OR TRY_CAST(s AS BIGINT) IS NULL THEN NULL
                ELSE CAST(to_timestamp(TRY_CAST(s AS BIGINT)) AS TIMESTAMP)
            END;

        -- unix_timestamp(x) → 秒级 epoch（BIGINT）
        -- 复用 spark_safe_to_timestamp 的多形态解析路径（剥时区后缀 + TRY_CAST），
        -- 兼容 'yyyy-MM-dd[ T]HH:mm:ss[+08:00|Z]' 等 Spark 默认 fmt 之外的常见输入；
        -- 解析失败时 epoch(NULL) 返回 NULL，与 Spark 一致。
        CREATE OR REPLACE MACRO unix_timestamp(x) AS
            CASE
                WHEN x IS NULL THEN NULL
                ELSE CAST(epoch(
                    TRY_CAST(regexp_replace(CAST(x AS VARCHAR), '([+-][0-9]{2}:?[0-9]{2}|Z)$', '') AS TIMESTAMP)
                ) AS BIGINT)
            END;

        -- nvl(a, b) ≡ COALESCE（Oracle/Spark 习惯写法）
        CREATE OR REPLACE MACRO nvl(a, b) AS COALESCE(a, b);

        -- locate(needle, haystack) [Spark 二参 1-based] → DuckDB strpos
        -- DuckDB strpos 同样 1-based，未找到返回 0；NULL 输入显式返回 NULL（与 Spark 一致）。
        -- Spark 三参 locate(substr, str, pos) 不在 macro 中支持（DuckDB macro 不支持可选参数），
        -- 业务实际很少使用三参形式；如遇到再走文本翻译路径补丁。
        CREATE OR REPLACE MACRO locate(needle, haystack) AS
            CASE
                WHEN needle IS NULL OR haystack IS NULL THEN NULL
                ELSE strpos(haystack, needle)
            END;

        -- add_months(date, n) → DATE + n 月
        -- DuckDB DATE + INTERVAL N MONTH 自动对齐月末（Jan 31 + 1 month → Feb 29），
        -- 与 Spark add_months 月末规则一致；负数 n 同样工作正常。
        CREATE OR REPLACE MACRO add_months(d, n) AS
            (CAST(d AS DATE) + (n * INTERVAL 1 MONTH));

        -- 辅助：判断日期是否为所在月最后一天
        CREATE OR REPLACE MACRO _is_last_day_of_month(d) AS
            (CAST(d AS DATE) = (date_trunc('month', CAST(d AS DATE)) + INTERVAL 1 MONTH - INTERVAL 1 DAY));

        -- months_between(end, start) → DOUBLE 月差（与 Spark 完全对齐）
        -- Spark 算法：
        --   diff = (year(a) - year(b)) * 12 + (month(a) - month(b))
        --   若 day(a) = day(b) 或两者都是月末 → 返回 diff（忽略时分秒）
        --   否则 → diff + ((day(a)-day(b))*86400 + time_of_day(a) - time_of_day(b)) / (31*86400)
        -- 整数月差通过 year/month 提取实现（不能用 date_diff('month', ...)，因为 DuckDB 取上界与 Spark 不同）。
        CREATE OR REPLACE MACRO months_between(a, b) AS
            CASE
                WHEN a IS NULL OR b IS NULL THEN NULL
                WHEN day(CAST(a AS DATE)) = day(CAST(b AS DATE))
                  OR (_is_last_day_of_month(a) AND _is_last_day_of_month(b))
                THEN CAST((year(CAST(a AS DATE)) - year(CAST(b AS DATE))) * 12
                        + (month(CAST(a AS DATE)) - month(CAST(b AS DATE))) AS DOUBLE)
                ELSE
                    CAST((year(CAST(a AS DATE)) - year(CAST(b AS DATE))) * 12
                        + (month(CAST(a AS DATE)) - month(CAST(b AS DATE))) AS DOUBLE)
                    + (
                        CAST(day(CAST(a AS DATE)) - day(CAST(b AS DATE)) AS DOUBLE) * 86400.0
                        + CAST(epoch(CAST(a AS TIMESTAMP)) - epoch(date_trunc('day', CAST(a AS TIMESTAMP))) AS DOUBLE)
                        - CAST(epoch(CAST(b AS TIMESTAMP)) - epoch(date_trunc('day', CAST(b AS TIMESTAMP))) AS DOUBLE)
                    ) / (31.0 * 86400.0)
            END;
        """
    )


# ============================================================
# 2bis-ext. 多表伴随视图（精简多表方案：raw_sql JOIN 友好支持）
# ------------------------------------------------------------
# 触发条件：prefetch_table.py 已为本次会话的多张表落了 cache（/tmp/wedata_kanban_cache/*.meta.json）。
# 工作机制：
#   ① 主 Spec.source 的 csv 注册为 _kb_src（既有逻辑不变，单源 spec 零回归）
#   ② 同时扫所有 fresh meta.json，为每张表额外注册一个 `<short_name>` 视图
#      （short_name = sql_preview 中 FROM 后表名的尾段，如 `tiny_orders`）
#   ③ 同时为完整三段式 `catalog.db.table` 也注册一个视图（带反引号兼容）
# 这样：
#   - LLM 写 raw_sql 用 `FROM tiny_orders JOIN tiny_product` 或完整三段式都能本地跑
#   - dry_run 编译期 EXPLAIN 立刻验证多表 JOIN 是否合法
#   - 入库到平台 Spark 时，sqlSlots 里 SQL 仍是真实三段式 → 远端原生执行
# 设计取舍：
#   - 不改 Spec/Source 多源契约 → 16 个 chart adapter 零修改、单源场景零回归
#   - 多表 JOIN 走 raw_sql 是合理的：DSL 里 chart 本就是单维度抽象，JOIN 后宽表语义最清晰
# ============================================================

def _attach_companion_views(con, primary_csv_path: str, primary_table: str) -> List[str]:
    """扫描 prefetch 缓存，为非主表的其他表也注册 DuckDB 视图。

    Args:
        con:                已打开的 DuckDB 连接（_kb_src 已就位）
        primary_csv_path:   主 Spec.source 的 csv（_kb_src），跳过避免重复注册
        primary_table:      主表三段式名（用于过滤）

    Returns:
        List[str]：成功注册的伴随视图名列表（仅短名，便于日志）
    """
    if not os.path.isdir(_SQL_CACHE_DIR):
        return []
    try:
        ttl = int(os.environ.get('KANBAN_SQL_CACHE_TTL', _SQL_CACHE_DEFAULT_TTL))
    except ValueError:
        ttl = _SQL_CACHE_DEFAULT_TTL

    attached: List[str] = []
    seen_short: set = set()
    primary_csv_real = os.path.realpath(primary_csv_path) if primary_csv_path else ''

    # 解析 sql_preview 中的 FROM <table> 抓三段式表名（prefetch 写入的 SQL 形如 SELECT ... FROM <table> LIMIT N）
    from_re = re.compile(r'\bFROM\s+([A-Za-z_][\w$.]*)', re.I)

    for meta_path in sorted(glob.glob(os.path.join(_SQL_CACHE_DIR, '*.meta.json'))):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            csv_path = (meta.get('csv_path') or '').strip()
            sql_prev = (meta.get('sql_preview') or '').strip()
            created_at = float(meta.get('created_at') or 0)
            # 优先信任 prefetch 显式写入的 table 字段（精确，零歧义）；
            # 旧版 cache 没有该字段时回退正则解析 sql_preview（受 200 字节截断风险）。
            full_name = (meta.get('table') or '').strip()
        except Exception:
            continue
        if not csv_path or not os.path.isfile(csv_path):
            continue
        if ttl > 0 and (time.time() - created_at) > ttl:
            continue
        # 跳过主 csv（已是 _kb_src）
        if primary_csv_real and os.path.realpath(csv_path) == primary_csv_real:
            continue

        if not full_name:
            m = from_re.search(sql_prev)
            if not m:
                continue
            full_name = m.group(1)
        # 防御：若 sql_preview 截断导致表名残缺（无两个 . 分隔），跳过
        if full_name.count('.') < 2:
            continue
        if full_name == primary_table:
            continue
        short_name = full_name.split('.')[-1]
        if not short_name or short_name in seen_short:
            continue
        seen_short.add(short_name)

        # 同名表（不同 catalog/db）冲突时，第一张胜出 + 打印告警
        try:
            # 与主表对齐策略（消除"主表 VARCHAR / 副表 TIMESTAMP"不一致）：
            #   - 时间/日期列：显式降级为 VARCHAR，统一交给 spark_safe_* 宏处理，
            #     避免主/副表时间列一个是 VARCHAR、一个是 TIMESTAMP 的本地差异。
            #   - 数值列：尽量保留为 BIGINT/DOUBLE/BOOLEAN，避免副表做 SUM/AVG 时
            #     必须手写 CAST（例如 SUM(total_revenue) on VARCHAR）。
            #   - 其他列：保守走 VARCHAR。
            #
            # 实现上先让 DuckDB sniff 一次 schema，再把 sniff 的结果规范化到受控类型集合，
            # 既保留数值聚合能力，又避免 timestamp/date 自动推断带来的跨表不一致。
            try:
                desc_rows = con.execute(
                    f"DESCRIBE SELECT * FROM read_csv_auto('{csv_path}', header=true, sample_size=-1, "
                    # 与主 CSV 路径一致：显式 quote='\"' 让 sniff 出的类型面向剥引号后的原值
                    f"quote='\"', escape='\"', "
                    f"nullstr=['null','NULL','None','\\\\N','','NaT','nan','NaN'], "
                    f"auto_type_candidates=['BIGINT','DOUBLE','VARCHAR','DATE','TIMESTAMP','BOOLEAN'])"
                ).fetchall() or []
            except Exception:
                desc_rows = []

            def _normalize_companion_duck_type(t: str) -> str:
                tt = (t or '').upper().strip()
                if not tt:
                    return 'VARCHAR'
                if any(x in tt for x in ('TIMESTAMP', 'DATE', 'TIME')):
                    return 'VARCHAR'
                if tt in ('BOOLEAN', 'BOOL'):
                    return 'BOOLEAN'
                if any(x in tt for x in ('DOUBLE', 'FLOAT', 'REAL', 'DECIMAL', 'NUMERIC')):
                    return 'DOUBLE'
                if any(x in tt for x in ('BIGINT', 'HUGEINT', 'UBIGINT')):
                    return 'BIGINT'
                if any(x in tt for x in ('INTEGER', 'INT', 'SMALLINT', 'TINYINT', 'USMALLINT', 'UTINYINT', 'UINTEGER')):
                    return 'BIGINT'
                return 'VARCHAR'

            col_names = [str(r[0]) for r in desc_rows if r and r[0]]
            if desc_rows:
                cols_decl = ', '.join([
                    f"'{str(r[0])}': '{_normalize_companion_duck_type(str(r[1]) if len(r) > 1 else '')}'"
                    for r in desc_rows if r and r[0]
                ])
                read_clause = (
                    f"read_csv('{csv_path}', header=true, sample_size=-1, "
                    # 与主 CSV 路径一致：显式 quote='\"' 让伴随表 CSV 双引号被正确剥离
                    f"quote='\"', escape='\"', "
                    f"nullstr=['null','NULL','None','\\\\N','','NaT','nan','NaN'], "
                    f"columns={{{cols_decl}}})"
                )
            else:
                read_clause = (
                    f"read_csv_auto('{csv_path}', header=true, sample_size=-1, "
                    f"quote='\"', escape='\"', "
                    f"nullstr=['null','NULL','None','\\\\N','','NaT','nan','NaN'], "
                    f"auto_type_candidates=['BIGINT','DOUBLE','VARCHAR','DATE','TIMESTAMP','BOOLEAN'])"
                )

            con.execute(
                f"CREATE OR REPLACE VIEW \"{short_name}\" AS SELECT * FROM {read_clause}"
            )
            # 同时注册完整三段式视图（用双引号包裹，DuckDB 标识符引号）
            con.execute(
                f"CREATE OR REPLACE VIEW \"{full_name}\" AS SELECT * FROM \"{short_name}\""
            )
            attached.append(short_name)
            _set_companion(con, full_name, short_name)
        except Exception as ex:
            print(f'⚠️ [多表] 注册伴随视图 {short_name} 失败（非致命）：{ex}')
            continue
    return attached


# ============================================================
# 2bis-ext2. 副表 CSV 落盘等待（强同步：消除 prefetch 竞态）
# ------------------------------------------------------------
# 问题：prefetch_table.py 用 double-fork 后台并行预取，副表 csv 可能略晚于
#       主表同步取数完成。原实现是"扫不到就跳过 + raw_sql 软告警"，会导致
#       首次 build_kanban 副表 chart 本地体检数据为空（虽然不阻断 PREVIEW 同步，但排障体验差）。
#
# 解决：build_kanban 进入 chart 编译前，**显式等齐所有依赖表的 csv 落盘**，
#       让 _attach_companion_views 一定能扫到全部 meta.json，副表 chart
#       从首次 build 起就有正确的本地体检数据。
#
# 依赖表识别（静态扫描，无需新增 DSL 字段）：
#   ① 主表：spec.source.table（已由主流程的同步取数拉取，不需等待）
#   ② 副表：扫描所有 Chart.raw_sql，正则抽出 FROM/JOIN <三段式> 表名
#
# 等待策略（优雅、通用、可降级）：
#   - 0 张副表 → 直接返回（单表 spec 零开销）
#   - 默认超时 90s，可通过 KANBAN_PREFETCH_WAIT_TIMEOUT 覆盖
#   - 250ms 轮询，每 10s 打一次进度日志（避免噪声）
#   - 超时未到齐 → 退化为软告警（保留旧路径行为，不阻断 build）
#   - KANBAN_SKIP_PREFETCH_WAIT=1 → 完全跳过等待（逃生口，与旧版同语义）
# ============================================================

# 形如 catalog.db.table 的三段式：每段独立支持反引号 / 双引号包裹（兼容 `default` / "order" 这类
# SQL 关键字库名的实际写法）。匹配后由 _normalize_three_seg 剥掉所有引号，得到与 prefetch
# meta.json.table 字段一致的纯字母形式（prefetch 写入时也是无引号的）。
_THREE_SEG_FROM_RE = re.compile(
    r'\b(?:FROM|JOIN)\s+'
    r'([`"]?[A-Za-z_][\w$]*[`"]?'
    r'\.[`"]?[A-Za-z_][\w$]*[`"]?'
    r'\.[`"]?[A-Za-z_][\w$]*[`"]?)',
    re.I,
)


def _normalize_three_seg(s: str) -> str:
    """把三段式表名中每段的反引号/双引号剥掉，与 prefetch meta.json.table 字段对齐。"""
    if not s:
        return ''
    return s.replace('`', '').replace('"', '').strip()


def _collect_dependent_tables(spec) -> List[str]:
    """静态扫描 Spec，收集所有副表三段式名（已剔除主表，去重保序）。

    扫描范围：
      - Chart.raw_sql（Compare 不支持 raw_sql；普通 chart 由 adapter 拼 SQL，全部走主表）
      - KPI Metric.from_sql（跨表 KPI 通过 from_sql 引用的副表也必须等就绪）

    归一化：
      - 主表与副表均剥掉反引号/双引号后比较，确保 `default` / "order" 这类 SQL 关键字
        库名能被正确剔除/匹配。
    返回：[纯字母三段式 catalog.db.table, ...]，与 prefetch meta.json.table 字段一致
    """
    primary = _normalize_three_seg(
        getattr(getattr(spec, 'source', None), 'table', '') or ''
    )
    seen, out = set(), []

    def _scan(text: str, *, is_from_sql: bool = False):
        if not text:
            return
        # KPI.from_sql 是裸 FROM 子句（如 `cat.db.t1` 或 `cat.db.t1 a JOIN cat.db.t2 b ON...`），
        # 没有 FROM/JOIN 前缀，直接扫描会漏掉首张表。前缀拼一个 'FROM ' 让正则统一命中。
        scan_text = ('FROM ' + text) if is_from_sql else text
        for m in _THREE_SEG_FROM_RE.finditer(scan_text):
            t = _normalize_three_seg(m.group(1))
            if not t or t == primary or t in seen:
                continue
            seen.add(t)
            out.append(t)

    for c in (getattr(spec, 'charts', None) or []):
        _scan(getattr(c, 'raw_sql', None))
    for k in (getattr(spec, 'kpis', None) or []):
        _scan(getattr(k, 'from_sql', None), is_from_sql=True)
    return out


def _is_table_csv_ready(table: str, ttl: int) -> bool:
    """检查 prefetch cache 中是否已有该表 fresh 的 csv（meta.json 含 table 字段、csv 存在、未过期）。"""
    if not os.path.isdir(_SQL_CACHE_DIR):
        return False
    try:
        for meta_path in glob.glob(os.path.join(_SQL_CACHE_DIR, '*.meta.json')):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except Exception:
                continue
            if (meta.get('table') or '').strip() != table:
                continue
            csv_path = (meta.get('csv_path') or '').strip()
            created_at = float(meta.get('created_at') or 0)
            if not csv_path or not os.path.isfile(csv_path):
                continue
            if ttl > 0 and (time.time() - created_at) > ttl:
                continue
            return True
    except Exception:
        return False
    return False


def _wait_for_companion_csvs(tables: List[str], timeout_s: float = 90.0,
                             poll_interval_s: float = 0.25) -> List[str]:
    """阻塞等待所有依赖副表的 csv 落盘。

    Returns:
        List[str]：超时仍未就绪的表名（空列表 = 全部就绪）
    """
    if not tables:
        return []
    if os.environ.get('KANBAN_SKIP_PREFETCH_WAIT', '').strip() in ('1', 'true', 'True'):
        print(f'⏭️  [副表等待] 已被 KANBAN_SKIP_PREFETCH_WAIT 跳过；缺失表将走软告警路径')
        return []

    try:
        ttl = int(os.environ.get('KANBAN_SQL_CACHE_TTL', _SQL_CACHE_DEFAULT_TTL))
    except ValueError:
        ttl = _SQL_CACHE_DEFAULT_TTL

    pending = list(tables)
    deadline = time.time() + max(0.0, float(timeout_s))
    last_log_at = 0.0
    print(f'⏳ [副表等待] 等待 {len(pending)} 张副表 csv 落盘：{", ".join(pending)}（timeout={int(timeout_s)}s）')

    while pending and time.time() < deadline:
        # 扫一轮，把已就绪的表从 pending 中剔除
        still = [t for t in pending if not _is_table_csv_ready(t, ttl)]
        if not still:
            pending = []
            break

        # 进度日志：每 10s 打一次，避免日志洗版
        now = time.time()
        if now - last_log_at >= 10.0:
            elapsed = int(timeout_s - (deadline - now))
            print(f'   ⌛ {elapsed}s 已过，待就绪：{", ".join(still)}')
            last_log_at = now

        pending = still
        time.sleep(poll_interval_s)

    # 退出循环后再做一次最终校验（避免 sleep 后边界态误报）
    pending = [t for t in pending if not _is_table_csv_ready(t, ttl)]
    if not pending:
        print(f'✅ [副表等待] 全部 {len(tables)} 张副表 csv 已就绪')
    return pending


def _to_local_sql(sql: str, source_table: str, con=None) -> str:
    """把入库 SQL（远端版）翻译为 DuckDB 本地版。

    1. 表名 source_table（含/不含反引号）→ _kb_src 视图
    2. 伴随表三段式裸名→双引号包裹的短名视图（多表场景）
    3. 反引号别名 `xx` → 双引号 "xx"（DuckDB 默认不识别反引号）
    4. **Spark→DuckDB 兼容层（P0 修复，源头收敛）**：
       a) 展开 spark_safe_*(...) 调用为底层 SQL 表达式
          （沿用 builder._SPARK_SAFE_REPLACEMENTS 的同一份规则，行为对齐 sqlSlots 修复路径）
       b) Spark 2 参数 DATEDIFF(end, start) → DuckDB 3 参数 datediff('day', start, end)
          DuckDB 的 datediff 第 1 参是单位字符串，第 2/3 参是 (start, end) 顺序与 Spark 相反；
          因此必须同时改"参数个数"+"参数顺序"，否则会得到符号相反的天数差。

    Args:
        con: 可选，传入后从 con._kb_companions 读伴随表表名映射。
             不传则跳过多表转译（单表场景零开销）。
    """
    if not sql:
        return sql
    local = sql
    # G3 补齐（方言归一后本地兼容）：ANSI 双引号方言（PG/GaussDB）经 sqlSlots 出口
    # 归一后表名会呈现为分段引号形态 `"public"."t_user"`。同时，OLAP 方言段数裁剪
    # 可能把原始三段 source_table='catalog.public.t_user' 裁成两段 `public.t_user`，
    # 因此本地回放必须同时识别：
    #   - 原始完整表名：catalog.public.t_user / `catalog.public.t_user` / "catalog"."public"."t_user"
    #   - OLAP 裁剪短表名：public.t_user / `public.t_user` / "public"."t_user"
    # 这样构建期 SQL 与已入库 sqlSlots 的本地复现都能稳定映射到 _LOCAL_VIEW。
    _st_bare = source_table.strip('`').strip('"')
    _parts = [seg for seg in _st_bare.split('.') if seg]
    _table_candidates: List[str] = []
    if _st_bare:
        _table_candidates.append(_st_bare)
    if len(_parts) > 2:
        _table_candidates.append('.'.join(_parts[-2:]))
    for _table_name in dict.fromkeys(_table_candidates):
        pat = re.escape(_table_name)
        local = re.sub(rf'`?{pat}`?', _LOCAL_VIEW, local)
        if '.' in _table_name:
            # 允许段间空白（re.escape 已把点转义），保守用 \s* 兼容归一格式
            _seg_pat = r'\s*\.\s*'.join(
                rf'"{re.escape(seg)}"' for seg in _table_name.split('.') if seg
            )
            local = re.sub(_seg_pat, _LOCAL_VIEW, local)
    # 伴随表表名归一化：让 raw_sql 用者写完整三段式也能本地跑
    if con is not None:
        comp = _get_companions(con)
        for full_name, short_name in comp.items():
            full_pat = re.escape(full_name)
            # 仅在 FROM/JOIN 后面替换（避免误伤列名与别名），可选反引号/双引号包裹
            local = re.sub(
                rf'(\b(?:FROM|JOIN)\s+)[`"]?{full_pat}[`"]?',
                lambda m, s=short_name: m.group(1) + f'"{s}"',
                local, flags=re.I,
            )
    local = local.replace('`', '"')
    # 4. Spark → DuckDB 兼容层（先展开 spark_safe_*，再翻 DATEDIFF）
    local = _spark_to_duckdb_compat(local)
    # 5. OLAP → DuckDB 兼容层（仅目标数据源为 MySQL/PG/GaussDB/StarRocks/Doris 时启用）：
    #    把 raw_sql 里 LLM 手写的目标方言函数（TO_CHAR/TIMESTAMPDIFF/DATE_TRUNC/x::type）
    #    翻译为 DuckDB 能识别的等价写法，避免本地 EXPLAIN 全部软告警、line/candlestick 本地体检为空。
    #    远端入库的 sqlSlots 不经此函数（_to_remote_sql 分支），零远端方言污染。
    local = _olap_to_duckdb_compat(local, _get_conn_type(con))
    return local


# ============================================================
# Spark → DuckDB 兼容转换（本地试算专用，不影响远端 sqlSlots）
# ============================================================

def _spark_to_duckdb_compat(sql: str) -> str:
    """把"远端 Spark 风格 SQL"转为 DuckDB 本地可跑的等价 SQL。

    覆盖范围（仅本地试算路径，不影响入库的 sqlSlots，远端依旧是 Spark SQL）：
      1. spark_safe_*(...) → 展开为底层等价表达式（与 builder 入库修复同源）
      2. try_to_timestamp(x) → COALESCE(try_strptime(x, fmt1), ...)（DuckDB 没有 try_to_timestamp）
      3. DATE_FORMAT(ts, 'yyyy-MM-dd') → strftime(ts, '%Y-%m-%d')（含 Spark→strftime 格式串映射）
      4. DATEDIFF(end, start) [2 参 Spark] → datediff('day', start, end) [3 参 DuckDB]
      5. CAST(... AS STRING) → CAST(... AS VARCHAR)
         （Spark 的 STRING 类型在 DuckDB 中名为 VARCHAR）

    任何步骤失败都打 stderr 软告警并返回最近一次成功的 SQL，绝不抛异常打断本地试算。
    """
    if not sql:
        return sql
    out = sql

    # ---- Step 1：展开 spark_safe_*（复用 builder 中已存在的同一份替换规则） ----
    try:
        replacements = _B.get('_SPARK_SAFE_REPLACEMENTS')
        call_re = _B.get('_SPARK_SAFE_CALL_RE')
        split_args = _B.get('_split_sql_args')
        if replacements and call_re and split_args:
            for _ in range(20):  # 最多 20 轮，防嵌套无限循环
                changed = {'v': False}
                def _expand(m):
                    func = m.group(1).lower()
                    args = split_args(m.group(2).strip())
                    fn = replacements.get(func)
                    if fn and args:
                        changed['v'] = True
                        return fn(args)
                    return m.group(0)
                new_out = call_re.sub(_expand, out)
                if not changed['v']:
                    break
                out = new_out
    except Exception as ex:
        print(f'⚠️ [runner] spark_safe_* 本地展开失败（已忽略）：{ex}', file=sys.stderr)

    # ---- Step 2：try_to_timestamp(x) → try_strptime 的多格式 COALESCE ----
    out = _rewrite_balanced_call(out, 'try_to_timestamp', _try_to_timestamp_rewrite)

    # ---- Step 3：DATE_FORMAT(ts, 'fmt') → strftime(ts, 'duckdb_fmt') ----
    out = _rewrite_balanced_call(out, 'DATE_FORMAT', _date_format_rewrite)

    # ---- Step 4：DATEDIFF(end, start) → datediff('day', start, end) ----
    out = _rewrite_balanced_call(out, 'DATEDIFF', _datediff_rewrite)

    # ---- Step 5：CAST(... AS STRING) → CAST(... AS VARCHAR) ----
    # 注意：用字符串感知的扫描，绕开字符串字面量，避免把 'AS STRING' 这种字面量误改为 'AS VARCHAR'。
    out = _replace_outside_strings(out, _AS_STRING_RE, 'AS VARCHAR')

    # ---- Step 6：regexp_replace(x, p, r) [3 参 Spark 默认全局] → regexp_replace(x, p, r, 'g') ----
    # DuckDB 的 regexp_replace 默认只替换第一处匹配，与 Spark 全局替换语义不一致；
    # spark_safe_to_timestamp 展开后的 regexp_replace(col, '[./]', '-') 必须全局替换
    # 才能把 '2017/10/2' 转为 '2017-10-2'。
    out = _rewrite_balanced_call(out, 'regexp_replace', _regexp_replace_global)

    # ---- Step 7：<expr> [NOT] RLIKE 'pattern' → [NOT] regexp_matches(<expr>, 'pattern') ----
    # RLIKE 是 Spark 关键字（非函数），DuckDB Parser 直接报错。spark_safe_to_timestamp_extended
    # 展开后必含 `col RLIKE '^[0-9]{10}$'`，是当前最高频的本地预览失败源。
    # 本翻译是字符串字面量感知的（通过逐字符扫描跳过 '...' 内部，避免误伤 'col RLIKE x' 这类字面量）。
    out = _translate_rlike(out)

    # ---- Step 8：DATE_SUB(d, n) [Spark 二参] → (CAST(d AS DATE) - n) ----
    # DuckDB 的 date_sub 二参签名与 Spark 不兼容（DuckDB 需要 INTERVAL 或负向 INTERVAL）。
    # date - INTEGER 在 DuckDB 表达式合法，等价于减去 n 天，与 Spark DATE_SUB 语义一致。
    # 三参 Presto 风格 DATE_SUB('day', n, end) 已是 DuckDB 兼容写法，保持原样。
    out = _rewrite_balanced_call(out, 'DATE_SUB', _date_sub_rewrite)

    # ---- Step 9：CURRENT_TIMESTAMP / CURRENT_TIMESTAMP() / NOW() → current_localtimestamp() ----
    # 三类来源都会落到这条 SQL：
    #   ① LLM 按 builder 报错文案改写 spark_safe_now → CURRENT_TIMESTAMP()（带括号，DuckDB 不识别）
    #   ② LLM 直接写 CURRENT_TIMESTAMP（关键字常量），但本机 DuckDB 缺 pytz 时一律抛 'pytz failed to import'
    #   ③ LLM 写 NOW()（Spark/MySQL 兼容写法）
    # 统一翻译为 current_localtimestamp()：DuckDB 原生提供、不依赖 pytz、不依赖 session tz。
    # 远端 Spark 走原文 CURRENT_TIMESTAMP/NOW()，行为不变。
    # 字符串字面量感知：'CURRENT_TIMESTAMP' / 'NOW()' 字面量不被改写。
    out = _replace_outside_strings(out, _CURRENT_TIMESTAMP_CALL_RE, 'current_localtimestamp()')
    out = _replace_outside_strings(out, _NOW_CALL_RE, 'current_localtimestamp()')
    out = _replace_outside_strings(out, _CURRENT_TIMESTAMP_KW_RE, 'current_localtimestamp()')

    return out


# ============================================================
# OLAP → DuckDB 兼容转换（本地体检专用，仅目标数据源为 OLAP 时启用）
# ============================================================
#
# 背景：
#   OLAP raw_sql 由 LLM 用目标数据源原生方言手写（P0-15）；本地 DuckDB 无法识别
#   PG/GaussDB 的 TO_CHAR / x::type、MySQL 的 TIMESTAMPDIFF、`::date` 等语法，
#   会导致 line/candlestick 图表本地体检为空（远端仍能正确入库）。
#
# 本层只做「构造语义等价的 DuckDB 表达式」，不影响 sqlSlots 出库（远端走原文）。
# 覆盖清单：
#   1. TO_CHAR(ts, 'YYYY-MM')            → strftime(CAST(ts AS TIMESTAMP), '%Y-%m')  [PG/GaussDB]
#   2. TIMESTAMPDIFF(unit, s, e)         → datediff('day'|'month'|..., s, e)         [MySQL/GaussDB]
#   3. STR_TO_DATE(x, '%Y-%m-%d')        → strptime(x, '%Y-%m-%d')                   [MySQL]
#   4. x::type / x :: type               → CAST(x AS type)                           [PG/GaussDB]
#   5. DATE_TRUNC('month', ts) 保持不变（DuckDB 原生支持）
# ============================================================

# PG/GaussDB TO_CHAR 格式串 → DuckDB strftime 格式串。
# 注意：先长后短（YYYY 必须先于 YY，MM 先于 MI 等），避免部分匹配错序。
_OLAP_TO_CHAR_FMT_TO_DUCKDB = (
    ('YYYY', '%Y'),
    ('YY', '%y'),
    ('MM', '%m'),
    ('DD', '%d'),
    ('HH24', '%H'),
    ('HH', '%I'),
    ('MI', '%M'),
    ('SS', '%S'),
)


def _olap_to_char_rewrite(args):
    """TO_CHAR(ts, 'YYYY-MM-DD HH24:MI:SS') → strftime(CAST(ts AS TIMESTAMP), '%Y-%m-%d %H:%M:%S')。

    - 单参 TO_CHAR(x)（数值转字符串）不重写，返回 None；DuckDB 有内置 CAST 兜底。
    - 第二参不是字符串字面量（形如 col）不重写。
    """
    if len(args) != 2:
        return None
    ts = args[0].strip()
    fmt_arg = args[1].strip()
    if not (len(fmt_arg) >= 2 and fmt_arg[0] == "'" and fmt_arg[-1] == "'"):
        return None
    fmt = fmt_arg[1:-1]
    for s_tok, d_tok in _OLAP_TO_CHAR_FMT_TO_DUCKDB:
        fmt = fmt.replace(s_tok, d_tok)
    return f"strftime(CAST({ts} AS TIMESTAMP), '{fmt}')"


# MySQL TIMESTAMPDIFF 单位 → DuckDB datediff 单位（DuckDB 支持 day/month/year/hour/minute/second/week）。
_OLAP_TIMESTAMPDIFF_UNIT = {
    'MICROSECOND': 'microsecond',
    'SECOND': 'second',
    'MINUTE': 'minute',
    'HOUR': 'hour',
    'DAY': 'day',
    'WEEK': 'week',
    'MONTH': 'month',
    'QUARTER': 'quarter',
    'YEAR': 'year',
}


def _olap_timestampdiff_rewrite(args):
    """TIMESTAMPDIFF(unit, start, end) → datediff('unit_lower', start, end)。

    与 DuckDB datediff(part, startdate, enddate) 参数顺序一致（Presto 风格），语义相同。
    unit 未知时不重写（返回 None），避免误伤自定义 UDF。
    """
    if len(args) != 3:
        return None
    raw_unit = args[0].strip().strip("'").strip('"').upper()
    unit = _OLAP_TIMESTAMPDIFF_UNIT.get(raw_unit)
    if not unit:
        return None
    start_arg = args[1].strip()
    end_arg = args[2].strip()
    return (
        f"datediff('{unit}', "
        f"CAST({start_arg} AS TIMESTAMP), CAST({end_arg} AS TIMESTAMP))"
    )


def _olap_str_to_date_rewrite(args):
    """MySQL STR_TO_DATE(x, '%Y-%m-%d') → DuckDB strptime(x, '%Y-%m-%d')。"""
    if len(args) != 2:
        return None
    x = args[0].strip()
    fmt = args[1].strip()
    if not (len(fmt) >= 2 and fmt[0] == "'" and fmt[-1] == "'"):
        return None
    return f"strptime({x}, {fmt})"


# PG/GaussDB `::type` cast 匹配：仅接受形如 `<ident_or_)>::<type>` 的短格式，
# 不处理 `::interval '1 day'` 等含空格类型（少见，遇到再补）。
_PG_CAST_RE = re.compile(
    r"::\s*"
    r"(int(?:eger)?|bigint|smallint|int2|int4|int8|serial|bigserial|"
    r"double\s+precision|double|float|real|numeric(?:\([^)]*\))?|decimal(?:\([^)]*\))?|"
    r"boolean|bool|"
    r"date|timestamp(?:tz)?(?:\s*without\s*time\s*zone|\s*with\s*time\s*zone)?|time(?:tz)?|"
    r"text|varchar(?:\([^)]*\))?|char(?:\([^)]*\))?)",
    re.IGNORECASE,
)

_PG_CAST_TYPE_MAP = {
    'INT': 'BIGINT', 'INTEGER': 'BIGINT', 'INT2': 'SMALLINT', 'INT4': 'INTEGER', 'INT8': 'BIGINT',
    'SERIAL': 'BIGINT', 'BIGSERIAL': 'BIGINT',
    'FLOAT4': 'FLOAT', 'FLOAT8': 'DOUBLE',
    'DOUBLE PRECISION': 'DOUBLE',
    'BOOL': 'BOOLEAN',
    'TEXT': 'VARCHAR',
}


def _translate_pg_cast(sql):
    """把 `<expr>::type` 翻译为 `CAST(<expr> AS type)`（字符串字面量感知）。

    <expr> 反扫复用 _scan_left_operand（同 RLIKE 的左值扫描），支持：
      - 平衡括号：(x + 1)::int → CAST((x + 1) AS int)
      - 引号标识符："col"::text
      - 反引号标识符：`col`::int
      - 普通标识符/数值：col::int, 1.5::numeric
    在字符串字面量内部完全跳过，避免误改 'a::b' 字面量。
    """
    if not sql or '::' not in sql:
        return sql
    out_parts = []
    code_buf = []
    in_str = None
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        if in_str:
            code_buf.append(ch) if False else None  # 保持结构一致
            out_parts.append(ch)
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ("'", '"'):
            # 遇字符串边界前，先把 code_buf 里累积的代码翻译写出
            if code_buf:
                out_parts.append(_apply_pg_cast_on_code(''.join(code_buf)))
                code_buf = []
            in_str = ch
            out_parts.append(ch)
            i += 1
            continue
        code_buf.append(ch)
        i += 1
    if code_buf:
        out_parts.append(_apply_pg_cast_on_code(''.join(code_buf)))
    return ''.join(out_parts)


def _apply_pg_cast_on_code(code):
    """在 `code`（保证不含引号字符串）里把所有 `<operand>::type` 翻译为 CAST。

    循环消费：每次匹配到一个 `::type`，反扫左侧 operand，用 CAST(...) 拼接后
    切回后续文本；直到再无匹配。防止无限循环用 hard cap = 200。
    """
    out = code
    for _ in range(200):
        m = _PG_CAST_RE.search(out)
        if not m:
            break
        cast_start = m.start()
        cast_end = m.end()
        # 反扫左操作数：从 cast_start-1 开始
        j = cast_start - 1
        while j >= 0 and out[j] in (' ', '\t', '\n', '\r'):
            j -= 1
        if j < 0:
            # 没左操作数，跳过本次匹配（把 :: 原样放回）
            out = out[:cast_end] + out[cast_end:]
            break
        op_start = _scan_left_operand(out, j)
        operand = out[op_start:j + 1]
        raw_type = m.group(1).strip().upper()
        # 折叠内部空白（DOUBLE  PRECISION → DOUBLE PRECISION 再映射）
        norm_type = re.sub(r'\s+', ' ', raw_type)
        duck_type = _PG_CAST_TYPE_MAP.get(norm_type, raw_type)
        # timestamp with[out] time zone → TIMESTAMP（DuckDB TIMESTAMP 是 naive）
        if norm_type.startswith('TIMESTAMP') and 'TIME ZONE' in norm_type:
            duck_type = 'TIMESTAMPTZ' if 'WITH TIME ZONE' in norm_type else 'TIMESTAMP'
        replacement = f'CAST({operand} AS {duck_type})'
        out = out[:op_start] + replacement + out[cast_end:]
    return out


def _olap_to_duckdb_compat(sql: str, conn_type: str) -> str:
    """把 OLAP raw_sql 里的目标方言函数翻译为 DuckDB 等价写法（本地体检专用）。

    - conn_type 为空 / lakehouse（SPARK）→ 原样返回（零回归）
    - MySQL / PostgreSQL / GaussDB / StarRocks / Doris → 依次跑翻译规则
    - 任何步骤失败：静默降级为最近一次成功的 SQL，不阻断本地试算
    """
    if not sql:
        return sql
    canon = _runner_canonical_conn_type(conn_type or '')
    if canon in ('', 'SPARK'):
        return sql
    out = sql
    try:
        # 1. TO_CHAR（PG/GaussDB 主要，MySQL 无该函数但其它 OLAP 也可能出现）
        out = _rewrite_balanced_call(out, 'TO_CHAR', _olap_to_char_rewrite)
        # 2. TIMESTAMPDIFF（MySQL/GaussDB/Doris 都支持这个 ANSI 函数名）
        out = _rewrite_balanced_call(out, 'TIMESTAMPDIFF', _olap_timestampdiff_rewrite)
        # 3. STR_TO_DATE（MySQL）
        out = _rewrite_balanced_call(out, 'STR_TO_DATE', _olap_str_to_date_rewrite)
        # 4. `x::type` cast（PG/GaussDB）
        if canon in ('POSTGRESQL', 'GAUSSDB'):
            out = _translate_pg_cast(out)
    except Exception as ex:
        print(f'⚠️ [runner] OLAP → DuckDB 兼容层出错（已忽略，回退原 SQL）：{ex}',
              file=sys.stderr)
        return sql
    return out


# `AS STRING`（大小写不敏感、单词边界）；不会替换 'STRING_AGG' 等列名/函数名。
_AS_STRING_RE = re.compile(r'\bAS\s+STRING\b', re.IGNORECASE)

# CURRENT_TIMESTAMP() / NOW() / CURRENT_TIMESTAMP（关键字常量）兼容映射。
# 必须先匹配带括号形式（避免 KW 正则误吃 CURRENT_TIMESTAMP() 的 CURRENT_TIMESTAMP 部分），
# KW 正则尾部加负向先行 (?!\s*\() 跳过带括号已被前一条吃掉的情形。
_CURRENT_TIMESTAMP_CALL_RE = re.compile(r'\bCURRENT_TIMESTAMP\s*\(\s*\)', re.IGNORECASE)
_NOW_CALL_RE = re.compile(r'\bNOW\s*\(\s*\)', re.IGNORECASE)
_CURRENT_TIMESTAMP_KW_RE = re.compile(r'\bCURRENT_TIMESTAMP\b(?!\s*\()', re.IGNORECASE)

# RLIKE / NOT RLIKE 后面紧跟一个单引号字符串字面量（Spark 文法要求 RLIKE 右值是字符串）。
# 用 (?:''|[^']) 兼容 SQL 标准的双单引号转义。
_RLIKE_RE = re.compile(r"\b(NOT\s+)?RLIKE\s+('(?:''|[^'])*')", re.IGNORECASE)


def _replace_outside_strings(sql: str, pattern: re.Pattern, repl: str) -> str:
    """对 sql 做 pattern 全局替换，但跳过单/双引号字符串字面量内部。

    用 token 流的方式扫描：在字符串里时仅原样输出，离开字符串后再对累积的"代码段"
    做正则替换，避免把 'AS STRING' 这类字面量误改写。
    """
    if not sql:
        return sql
    out_parts: List[str] = []
    code_buf: List[str] = []
    in_str: Optional[str] = None
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        if in_str:
            out_parts.append(ch)
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ("'", '"'):
            # 先把累积的代码段做替换，再切到字符串模式
            if code_buf:
                out_parts.append(pattern.sub(repl, ''.join(code_buf)))
                code_buf = []
            in_str = ch
            out_parts.append(ch)
            i += 1
            continue
        code_buf.append(ch)
        i += 1
    if code_buf:
        out_parts.append(pattern.sub(repl, ''.join(code_buf)))
    return ''.join(out_parts)


def _regexp_replace_global(args: List[str]) -> Optional[str]:
    """regexp_replace(x, p, r) → regexp_replace(x, p, r, 'g')。

    仅在恰好 3 参时改写；4+ 参（已显式给了 flags）保持原样。
    """
    if len(args) != 3:
        return None
    return f"regexp_replace({args[0].strip()}, {args[1].strip()}, {args[2].strip()}, 'g')"


# ------------------------------------------------------------
# 基于括号平衡的函数调用扫描器（任意深度嵌套都能正确切到参数）
# ------------------------------------------------------------

def _rewrite_balanced_call(sql: str, func_name: str, rewriter) -> str:
    """扫描 sql 中所有 `func_name(...)` 调用（大小写不敏感），按括号平衡切出整段，
    把括号内字符串按顶层逗号切分成参数列表，交给 rewriter(args:list[str]) → str 重写。

    rewriter 返回 None 表示"该次调用不重写"（保持原样）。
    支持任意深度嵌套（例如 DATEDIFF(try_strptime(regexp_replace(x,'a','b'),'fmt'), ...)）。

    **正确性保证**：外层扫描会跳过单/双引号字符串内部，避免把
    `SELECT 'I love DATEDIFF(a, b)'` 这类字符串字面量当作真函数调用来改写。
    """
    if not sql or not func_name:
        return sql
    name_lower = func_name.lower()
    name_len = len(func_name)
    out: List[str] = []
    i = 0
    n = len(sql)
    in_str: Optional[str] = None  # 顶层字符串状态（'/"），不包括括号内（括号内由内层平衡逻辑接管）
    while i < n:
        ch = sql[i]
        # —— 顶层字符串保护：在字符串里直接拷贝，不做任何匹配 ——
        if in_str:
            out.append(ch)
            if ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in ("'", '"'):
            in_str = ch
            out.append(ch)
            i += 1
            continue
        # —— 尝试匹配函数名（前置必须是非标识符字符；末尾要紧跟 '(' 可带空白）——
        if (ch.lower() == name_lower[0]
                and (i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == '_'))
                and i + name_len <= n
                and sql[i:i + name_len].lower() == name_lower):
            # 标识符边界：name 之后必须不是 [A-Za-z0-9_]
            tail = i + name_len
            # 跳过空白找左括号
            k = tail
            while k < n and sql[k] in (' ', '\t', '\n', '\r'):
                k += 1
            if k < n and sql[k] == '(' and (tail == n
                                            or not (sql[tail].isalnum() or sql[tail] == '_')):
                # 找到一个真函数调用，做内层括号平衡（同时跳过括号内字符串）
                lp = k
                depth = 0
                j = lp
                inner_str: Optional[str] = None
                while j < n:
                    cj = sql[j]
                    if inner_str:
                        if cj == inner_str:
                            inner_str = None
                        j += 1
                        continue
                    if cj in ("'", '"'):
                        inner_str = cj
                        j += 1
                        continue
                    if cj == '(':
                        depth += 1
                    elif cj == ')':
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if depth == 0 and j < n:
                    inside = sql[lp + 1:j]
                    args = _split_top_level_args(inside)
                    new_call = rewriter(args)
                    if new_call is None:
                        out.append(sql[i:j + 1])
                    else:
                        out.append(new_call)
                    i = j + 1
                    continue
                # 括号不平衡 → 不改写，原样吐出当前字符
        out.append(ch)
        i += 1
    return ''.join(out)


def _split_top_level_args(s: str) -> List[str]:
    """按顶层逗号切分（忽略括号内 / 字符串内的逗号）。"""
    parts: List[str] = []
    buf: List[str] = []
    depth = 0
    in_str = None
    for ch in s:
        if in_str:
            buf.append(ch)
            if ch == in_str:
                in_str = None
            continue
        if ch in ("'", '"'):
            in_str = ch
            buf.append(ch)
            continue
        if ch == '(':
            depth += 1
            buf.append(ch)
            continue
        if ch == ')':
            depth -= 1
            buf.append(ch)
            continue
        if ch == ',' and depth == 0:
            parts.append(''.join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append(''.join(buf).strip())
    return parts


# ------------------------------------------------------------
# 各 rewriter（输入：参数列表；输出：完整重写后的调用字符串 / None 表示不重写）
# ------------------------------------------------------------

def _try_to_timestamp_rewrite(args: List[str]) -> Optional[str]:
    """try_to_timestamp(x) → COALESCE(try_strptime(CAST(x AS VARCHAR), fmt1), ..., unix 兜底, try_cast(x AS TIMESTAMP))

    候选格式覆盖业务最常见的"中文系统导出"日期形态，覆盖范围与 builder
    `spark_safe_to_timestamp_extended` 对齐：
      - 标准 ISO：2017-10-02 10:56:00 / 2017-10-02
      - Spark hive 默认：2017-10-02T10:56:00
      - 国内业务系统：2017/10/2 10:56（无秒、月日不补零）等
      - 8/14 位纯数字：20171002 / 20171002105633
      - 10/13 位 unix 时间戳（秒/毫秒）
      - **带时区后缀**：2017-10-02 10:56:00+08:00 / ...Z（剥后缀再解析；
        Iceberg/Delta 表 timestamp_tz(6) 列导出 CSV 时常见此形态，
        若不剥时区，下面的 try_strptime 全部 miss、try_cast 也会因 "+" 失败 → NULL，
        引发"runner 本地预览对 timestamp 类型处理有兼容问题"类告警）。
    最后兜底用 try_cast(x AS TIMESTAMP)，DuckDB 的 CAST 对 ISO-like 字符串非常包容
    （连 '2017-10-2 10:56' 这种缺秒/月日不补零的形态也能识别）。
    任一命中即返回 TIMESTAMP，全失败返回 NULL，与 Spark try_to_timestamp 行为一致。
    """
    if len(args) != 1:
        return None
    arg = args[0].strip()

    # P0 健壮性增强（2026-06）：
    #   builder 端 _ts_of 会给裸列名套一层 regexp_replace(CAST(col AS STRING), '[./]', '-')，
    #   目的是把 '2017/10/02' 中的 '/' 改成 '-'。但这层 wrapper 会把
    #   '2017-10-02T10:56:33.000+08:00' 中的毫秒小数点 '.' 也替换为 '-'，得到
    #   '2017-10-02T10:56:33-000+08:00'，导致下面所有 try_strptime / try_cast 全部失败 → NULL。
    #   解决：识别这层 wrapper，把 inner_arg（真实列）剥出来直接用，
    #   既保留 '/' → '-' 的兼容（通过下面 stripped_slash 走一条专门路径），
    #   又彻底避免毫秒小数被破坏。
    inner_arg = None
    m = re.match(
        r"^regexp_replace\s*\(\s*CAST\s*\(\s*(.+?)\s+AS\s+STRING\s*\)\s*,\s*'\[\./\]'\s*,\s*'-'\s*\)\s*$",
        arg, re.IGNORECASE | re.DOTALL)
    if m:
        inner_arg = m.group(1).strip()

    # base：真正用来做时间解析的源表达式（剥掉 builder 包装后的原列名 / 子表达式）
    base = inner_arg if inner_arg else arg
    # DuckDB try_strptime 只接受 VARCHAR；DATE/TIMESTAMP 物理列也必须先 CAST，
    # 否则 time_dim(date,'week') 经 spark_safe_week_format → 本地展开后会触发
    # Binder Error: try_strptime(DATE, STRING_LITERAL)。
    base_varchar = f'CAST({base} AS VARCHAR)'
    # 兼容路径：把 '/' '.' 统一替换为 '-'（用于 '2017/10/02 ...' 这种业务系统格式）
    # 但仅在去掉时区/毫秒后做，避免破坏 ISO 毫秒。
    stripped_tz = (
        f"regexp_replace({base_varchar}, "
        f"'\\s*([+-][0-9]{{2}}:?[0-9]{{2}}|Z|UTC|GMT)\\s*$', '')"
    )
    stripped_full = (
        f"regexp_replace({stripped_tz}, '\\.[0-9]+$', '')"
    )
    # 把 '/' 替换为 '-' 后的形态（仅斜杠，不动小数点），用于 '2017/10/02' 这类业务格式
    stripped_slash = (
        f"regexp_replace({stripped_full}, '/', '-')"
    )
    fmts = (
        # 带秒
        "'%Y-%m-%d %H:%M:%S'",
        "'%Y-%m-%dT%H:%M:%S'",
        # 带毫秒（ISO 与 hive 风格，olist / Iceberg 时间戳列常见）
        "'%Y-%m-%d %H:%M:%S.%f'",
        "'%Y-%m-%dT%H:%M:%S.%f'",
        "'%Y/%m/%d %H:%M:%S'",
        # 不带秒（业务系统常见）
        "'%Y-%m-%d %H:%M'",
        "'%Y/%m/%d %H:%M'",
        # 仅日期
        "'%Y-%m-%d'",
        "'%Y/%m/%d'",
        # 纯数字（业务系统/数仓离线分区列常见）
        "'%Y%m%d%H%M%S'",
        "'%Y%m%d'",
        # —— 月份英文缩写/全称（BI 报表/数仓 ADS 常见，2026-06 增强）——
        # 业务背景：很多业务/财务报表导出列形如 'Jan 2025' / 'January 2025' /
        #   '25-Jan-2025' / '2025-Jan'，旧 fmts 全部 miss → 看板"无数据"。
        # DuckDB strptime 的 %b（月份缩写）/ %B（月份全称）原生支持英文 locale，
        # 兼容 'Jan'/'January' 大小写敏感；中文/法文等 locale 不在覆盖范围（默认 'en_US.UTF-8'）。
        # 刷除 2 位年候选（%y）：DuckDB 无 century pivot，'25' 会被误读为公元 25 年，
        # 与 Spark 默认行为（2000 pivot）不一致；如遇 'Jan-25' 列，则补全 4 位年后再入库。
        "'%b %Y'",          # Jan 2025
        "'%B %Y'",          # January 2025
        "'%b-%Y'",          # Jan-2025
        "'%B-%Y'",          # January-2025
        "'%Y-%b'",          # 2025-Jan
        "'%Y %b'",          # 2025 Jan
        "'%d-%b-%Y'",       # 25-Jan-2025（Oracle/SAS 常见）
        "'%d %b %Y'",       # 25 Jan 2025
        "'%d-%B-%Y'",       # 25-January-2025
        "'%d %B %Y'",       # 25 January 2025
        "'%b %d, %Y'",      # Jan 25, 2025（美式英文报表）
        "'%B %d, %Y'",      # January 25, 2025
    )
    parts = [f'try_strptime({base_varchar}, {f})' for f in fmts]
    # —— 带时区后缀的 ISO 形态（先剥时区再解析；放在 unix 兜底之前优先命中）——
    parts.extend([
        f"try_strptime({stripped_tz}, '%Y-%m-%d %H:%M:%S')",
        f"try_strptime({stripped_tz}, '%Y-%m-%dT%H:%M:%S')",
        f"try_strptime({stripped_tz}, '%Y-%m-%d %H:%M:%S.%f')",
        f"try_strptime({stripped_tz}, '%Y-%m-%dT%H:%M:%S.%f')",
        # 同时剥离毫秒小数（覆盖 '2017-09-13 08:59:02.123 +0000' 这种写法）
        f"try_strptime({stripped_full}, '%Y-%m-%d %H:%M:%S')",
        f"try_strptime({stripped_full}, '%Y-%m-%dT%H:%M:%S')",
        # 斜杠业务格式（剥时区/毫秒/斜杠后再解析）
        f"try_strptime({stripped_slash}, '%Y-%m-%d %H:%M:%S')",
        f"try_strptime({stripped_slash}, '%Y-%m-%d %H:%M')",
        f"try_strptime({stripped_slash}, '%Y-%m-%d')",
        f"try_cast({stripped_tz} AS TIMESTAMP)",
        f"try_cast({stripped_full} AS TIMESTAMP)",
    ])
    # —— 低粒度时间字符串智能补全（2026-06 增强）——
    # 数仓 ADS 层常见的"按月/按年聚合好的字符串列"：year_month='2017-01' /
    # stat_month='201701' / dt='2017' / 业务系统 '2017/01' / '2017.01' / '2017-1'。
    # 上面所有 try_strptime 候选都要求至少 yyyy-MM-dd，故对纯年/年月输入全部 miss；
    # 最后的 try_cast('2017-01' AS TIMESTAMP) 在 DuckDB 也返回 NULL，整条 COALESCE 失败 →
    # 外层 WHERE ... IS NOT NULL 过滤掉全部行，看板出现"无数据"。
    #
    # 修复策略（严格、零误判）：
    #   1) 用 regexp_full_match 锁形态：
    #        ^[0-9]{4}([-/.][0-9]{1,2})?$  匹配 'yyyy' / 'yyyy-MM' / 'yyyy/M' / 'yyyy.MM'
    #        ^[0-9]{6}$                    匹配 'yyyyMM'（与 yyyymmdd 8 位、unix 10/13 位严格隔离）
    #   2) 命中后归一化分隔符为 '-'，仅用 '%Y-%m' / '%Y' / '%Y%m' 严格 strptime；
    #   3) 月份非法（00 / 13+）、3 段日期（2017-1-15）、unix 数字等都不会命中，
    #      最终走原有兜底链路，行为不变。
    parts.append(
        f"CASE "
        f"WHEN regexp_full_match({base_varchar}, '^[0-9]{{4}}([-/.][0-9]{{1,2}})?$') "
        f"  THEN COALESCE("
        f"    try_strptime(regexp_replace({base_varchar}, '[./]', '-', 'g'), '%Y-%m'),"
        f"    try_strptime({base_varchar}, '%Y')"
        f"  ) "
        f"WHEN regexp_full_match({base_varchar}, '^[0-9]{{6}}$') "
        f"  THEN try_strptime({base_varchar}, '%Y%m') "
        f"ELSE NULL END"
    )
    # unix 时间戳兜底（10 位秒 / 13 位毫秒）
    # 用 regexp_matches + try_cast，全部失败则得 NULL（不抛异常）。
    parts.append(
        f"CASE "
        f"WHEN regexp_matches({base_varchar}, '^[0-9]{{10}}$') "
        f"  THEN try_cast(epoch_ms(try_cast({base} AS BIGINT) * 1000) AS TIMESTAMP) "
        f"WHEN regexp_matches({base_varchar}, '^[0-9]{{13}}$') "
        f"  THEN try_cast(epoch_ms(try_cast({base} AS BIGINT)) AS TIMESTAMP) "
        f"ELSE NULL END"
    )
    # 兜底：try_cast 对 ISO-like 极包容（DuckDB 内置容错），覆盖月日单数字等边缘格式
    parts.append(f'try_cast({base} AS TIMESTAMP)')
    return f'COALESCE({", ".join(parts)})'


# Spark 格式串 → DuckDB strftime 格式串的字段级映射
# 注意替换顺序：长 token 在前，避免 'yyyy' 被部分匹配为 'yy' 后再次替换。
_SPARK_FMT_TO_DUCKDB = (
    ('yyyy', '%Y'),
    ('yy', '%y'),
    ('MM', '%m'),
    ('dd', '%d'),
    ('HH', '%H'),
    ('mm', '%M'),
    ('ss', '%S'),
)


def _date_format_rewrite(args: List[str]) -> Optional[str]:
    """DATE_FORMAT(ts, 'yyyy-MM-dd') → strftime(CAST(ts AS TIMESTAMP), '%Y-%m-%d')。

    显式 CAST 的原因：
    - DuckDB strftime 仅接受 TIMESTAMP / DATE，对 TIMESTAMP_TZ / VARCHAR 会
      Binder Error: "Could not choose a best candidate function for strftime(VARCHAR, ...)"。
    - 远端 Spark 路径不经此函数（_spark_to_duckdb_compat 内部调用），故只影响本地预览，
      与 _datediff_rewrite 的 CAST({arg} AS TIMESTAMP) 风格保持一致。
    - 已是 TIMESTAMP 的字段会被 CAST 幂等通过；TIMESTAMP_TZ 在 DuckDB 内会自动剥时区
      （session timezone = UTC 时无偏移），与 Spark 端 DATE_FORMAT 行为对齐。
    """
    if len(args) != 2:
        return None
    ts = args[0].strip()
    fmt_arg = args[1].strip()
    # 第二个参数必须是字符串字面量（'...'），否则不动
    if not (len(fmt_arg) >= 2 and fmt_arg[0] == "'" and fmt_arg[-1] == "'"):
        return None
    fmt = fmt_arg[1:-1]
    for s_tok, d_tok in _SPARK_FMT_TO_DUCKDB:
        fmt = fmt.replace(s_tok, d_tok)
    return f"strftime(CAST({ts} AS TIMESTAMP), '{fmt}')"


def _datediff_rewrite(args: List[str]) -> Optional[str]:
    """DATEDIFF(end, start) [Spark 2 参] → datediff('day', start, end) [DuckDB 3 参]。

    DuckDB datediff(part, startdate, enddate) → BIGINT，与 Spark (end, start) 入参顺序相反，
    交换顺序后语义一致（end-start 的天数差，正负号一致）。
    三参数 Presto 风格 DATEDIFF('day', start, end) 已是 DuckDB 兼容写法，保持原样。
    """
    if len(args) != 2:
        return None
    end_arg, start_arg = args[0].strip(), args[1].strip()
    return f"datediff('day', CAST({start_arg} AS TIMESTAMP), CAST({end_arg} AS TIMESTAMP))"


def _date_sub_rewrite(args: List[str]) -> Optional[str]:
    """DATE_SUB(d, n) [Spark 二参] → (CAST(d AS DATE) - n) [DuckDB 兼容]。

    Spark DATE_SUB(date, days) 返回 date - days 天；DuckDB 二参 date_sub 签名不兼容
    （DuckDB 推荐 date - INTERVAL n DAY 或 date - n）。直接用整数减法在 DuckDB 上等价。
    三参 Presto 风格 DATE_SUB('day', n, end) 留给 DuckDB 原生 date_sub(part, ...) 处理。
    """
    if len(args) != 2:
        return None
    date_arg, n_arg = args[0].strip(), args[1].strip()
    return f"(CAST({date_arg} AS DATE) - ({n_arg}))"


def _scan_left_operand(sql: str, end_pos: int) -> int:
    """从 end_pos（包含）反扫一个完整的 SQL 操作数 token，返回操作数起点下标。

    支持的形态（覆盖 RLIKE 左侧实际可能出现的所有形式）：
      - 平衡括号子表达式 `(...)`（含其前面紧贴的函数名 `func(...)`）
      - 单引号字符串字面量 `'...'`
      - 双引号 / 反引号包裹的标识符 `"..."` / `` `...` ``
      - 普通标识符 / 数字（含 `tbl.col`、`schema.tbl.col` 形式）
    括号反扫时跳过字符串字面量内部，避免被字面量里的括号误判。
    """
    i = end_pos
    if i < 0:
        return 0
    ch = sql[i]
    if ch == ')':
        depth = 1
        j = i - 1
        while j >= 0 and depth > 0:
            c = sql[j]
            if c == "'":
                # 跳过字符串字面量
                j -= 1
                while j >= 0 and sql[j] != "'":
                    j -= 1
                j -= 1
                continue
            if c == ')':
                depth += 1
            elif c == '(':
                depth -= 1
            j -= 1
        start = j + 1
        # 吞掉前面紧贴的函数名（若有）
        while start > 0 and (sql[start - 1].isalnum() or sql[start - 1] == '_'):
            start -= 1
        return start
    if ch == "'":
        j = i - 1
        while j >= 0 and sql[j] != "'":
            j -= 1
        return max(j, 0)
    if ch in '"`':
        quote = ch
        j = i - 1
        while j >= 0 and sql[j] != quote:
            j -= 1
        return max(j, 0)
    j = i
    while j >= 0 and (sql[j].isalnum() or sql[j] in '_."`'):
        j -= 1
    return j + 1


def _translate_rlike(sql: str) -> str:
    """把 Spark `<expr> [NOT] RLIKE 'pattern'` 翻译为 DuckDB `[NOT] regexp_matches(<expr>, 'pattern')`。

    背景：spark_safe_to_timestamp_extended 展开后必含 RLIKE（CASE WHEN col RLIKE '^[0-9]{10}$'），
    DuckDB Parser 不识别该关键字。本函数为字符串字面量感知的整体翻译（一次扫描两端都顾及）：

      ① 扫描定位"代码区"中的 `RLIKE '...'` 出现位置（自动跳过 '...'/"..." 字面量内部）
      ② 反扫匹配位左侧、跨过空白、抓取一个完整操作数（标识符 / 字符串字面量 / 平衡括号子表达式）
      ③ 用 regexp_matches(<left>, '<pattern>') 整段替换；NOT RLIKE 前置 NOT
    """
    if not sql or 'RLIKE' not in sql.upper():
        return sql
    n = len(sql)
    out: List[str] = []
    i = 0
    while i < n:
        ch = sql[i]
        # —— 字符串字面量原样输出，跳过其内部的所有 RLIKE 关键字字面 ——
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            j = i + 1
            while j < n:
                if sql[j] == quote:
                    # SQL 标准 '' 转义（仅单引号）
                    if quote == "'" and j + 1 < n and sql[j + 1] == "'":
                        out.append("''")
                        j += 2
                        continue
                    out.append(sql[j])
                    j += 1
                    break
                out.append(sql[j])
                j += 1
            i = j
            continue
        # —— 代码区：检测 [NOT ]RLIKE '...' ——
        m = _RLIKE_RE.match(sql, i)
        if not m:
            out.append(ch)
            i += 1
            continue
        # 反扫已经写入 out 中的 left 操作数（基于已输出 buffer 的尾部进行回退）
        buf = ''.join(out)
        end_pos = len(buf) - 1
        while end_pos >= 0 and buf[end_pos] == ' ':
            end_pos -= 1
        if end_pos < 0:
            # 没有左操作数，原样保留（防御性）
            out.append(ch)
            i += 1
            continue
        start_left = _scan_left_operand(buf, end_pos)
        left = buf[start_left:end_pos + 1].strip()
        # 截断 out 至 start_left
        out = list(buf[:start_left])
        negate = m.group(1) is not None
        pattern = m.group(2)
        out.append(("NOT " if negate else "") + f"regexp_matches({left}, {pattern})")
        i = m.end()
    return ''.join(out)


# 已知的"本地占位表名"集合：spec / raw_sql 里若误用这些名字，
# 入库到平台 Spark 一定 TABLE_OR_VIEW_NOT_FOUND；_to_remote_sql 入库前统一反向归一化。
# 只收录"几乎不会与合法别名/CTE/列名冲突"的两个名字：
#   _kb_src     —— runner 本地 DuckDB 视图名（_LOCAL_VIEW），仅 dry_run 内部使用
#   main_data   —— 历史样例 / LLM 高频脑补名
# 不收录 src / __src__：它们在 raw_sql 中作为合法 CTE 名 / 表别名极常见，
# 无差别替换会破坏正确逻辑，得不偿失（如 `WITH src AS (...) SELECT * FROM src`）。
_REMOTE_PLACEHOLDER_NAMES: Tuple[str, ...] = (_LOCAL_VIEW, 'main_data')

# 多表伴随视图映射（按 con id 索引）。
# DuckDB Connection 不允许 setattr 自定义属性，改用模块级字典。
# key   = id(con) 进程内唯一
# value = {full_name: short_name}
_KB_COMPANIONS: Dict[int, Dict[str, str]] = {}

# 连接绑定的目标数据源方言（同 id(con) 索引，用于本地体检期方言翻译）。
# 由 _open_duck 从 spec.source 反查 route_meta 时写入；_to_local_sql 消费。
_KB_CONN_TYPES: Dict[int, str] = {}


def _get_companions(con) -> Dict[str, str]:
    return _KB_COMPANIONS.get(id(con), {})


def _set_companion(con, full_name: str, short_name: str) -> None:
    _KB_COMPANIONS.setdefault(id(con), {})[full_name] = short_name


def _get_conn_type(con) -> str:
    """读取当前 DuckDB 连接对应的目标数据源方言（大写规范化后的 canon）。

    未绑定/未知一律返回 ''，此时 _to_local_sql 走原语义（Spark/lakehouse 兼容），
    保持零回归。
    """
    if con is None:
        return ''
    return _KB_CONN_TYPES.get(id(con), '')


def _set_conn_type(con, conn_type: str) -> None:
    canon = _runner_canonical_conn_type(conn_type or '')
    if canon:
        _KB_CONN_TYPES[id(con)] = canon


# =============================================================
# 方言引号风格：反引号（Spark/MySQL/StarRocks/Doris）vs ANSI 双引号（PG/GaussDB）
# =============================================================
#
# 背景（G2 修复：sqlSlots 反引号在 GaussDB/PostgreSQL 被误当整体标识符）：
#   DSL 编译期（_compile_kpi / _compile_bar / _compile_line ... 数十处）广泛使用
#   反引号包裹列别名/维度别名/表别名（`create_time_month` / `_kpi_root.\`a\`` / ...），
#   这些反引号形态对 Spark/MySQL/StarRocks/Doris 都合规（都识别反引号=标识符），
#   但 PostgreSQL/GaussDB **只认 ANSI 双引号**，反引号会被驱动/DN 当作字面字符处理，
#   导致把 `public.t_user` 解析成 "public.t_user"（含点号的整体表名）而报
#   `relation "public.t_user" does not exist`。
#
# 治理策略：sqlSlots 入库出口（_build_slot_meta）统一走一次方言归一：
#   - 反引号方言（SPARK/MYSQL/STARROCKS/DORIS）：原样保留反引号（零回归）
#   - ANSI 双引号方言（POSTGRESQL/GAUSSDB）：把 `xxx` → "xxx"；`db.tbl` → "db"."tbl"
#
# 与既有 L2 OLAP 硬拦截（三段式检测 / spark_safe_* / percentile_approx）正交，不冲突。
def _dialect_backtick_style(conn_type: str) -> str:
    """判定目标数据源是否识别反引号标识符引号。

    Returns:
        'keep' —— 反引号原样保留（Spark/MySQL/StarRocks/Doris）
        'ansi' —— 反引号翻译为 ANSI 双引号（PostgreSQL/GaussDB）
    未知 conn_type 保守返回 'keep'，与历史 lakehouse 语义一致。
    """
    canon = _runner_canonical_conn_type(conn_type)
    if canon in ('POSTGRESQL', 'GAUSSDB'):
        return 'ansi'
    # SPARK / MYSQL / STARROCKS / DORIS / 未知 → 保留反引号
    return 'keep'


def _rewrite_backticks_to_ansi(sql: str) -> str:
    """字符串感知扫描：把反引号包裹的标识符翻译为 ANSI 双引号（PostgreSQL/GaussDB 专用）。

    翻译规则：
      - `foo`         → "foo"
      - `db.tbl`      → "db"."tbl"（含点号的表名按段拆开，PG 不支持整体带点标识符）
      - _kpi_root.`a` 场景：反引号在标识符外部（如 _kpi_root. 后紧跟一个反引号包裹的 a）
        由于 DSL 编译时点号在反引号外部，此处只对反引号内部内容做处理，
        整体会被翻译为 _kpi_root."a"（正确）。

    跳过场景（避免误伤）：
      - 单引号字符串字面量 '...' 内部（含 '' 转义）
      - ANSI 双引号字面量 "..." 内部（保守，虽 PG 双引号本身也是标识符引号）
      - 反引号内含字面量点号但不含合法标识符段（如 `100 * cnt`）：内容不匹配段拆规则，
        整体包成 "100 * cnt" ——但这不是合法 PG 标识符，实际上 DSL 从不这样用；
        兜底策略是"内容含空格/运算符 → 拆段失败 → 整体双引号包裹"，与旧行为一致。
    """
    if not sql or '`' not in sql:
        return sql
    out: List[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_dquote = False
    while i < n:
        ch = sql[i]
        if in_single:
            out.append(ch)
            if ch == "'":
                # 处理 '' 转义（SQL 标准的字符串字面量内嵌单引号）
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue
        if in_dquote:
            out.append(ch)
            if ch == '"':
                # ANSI SQL 中 "" 是双引号字面量转义，此处保守跳出
                if i + 1 < n and sql[i + 1] == '"':
                    out.append('"')
                    i += 2
                    continue
                in_dquote = False
            i += 1
            continue
        if ch == "'":
            in_single = True
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            in_dquote = True
            out.append(ch)
            i += 1
            continue
        if ch == '`':
            # 抓取整段 `...`（反引号内不支持转义 ``——DSL 编译从不产出此类形态）
            j = i + 1
            buf: List[str] = []
            closed = False
            while j < n:
                c2 = sql[j]
                if c2 == '`':
                    closed = True
                    j += 1
                    break
                buf.append(c2)
                j += 1
            if not closed:
                # 未闭合反引号：保守原样输出剩余内容，不动
                out.append(sql[i:])
                break
            content = ''.join(buf)
            # 段拆策略：仅当每段都是合法标识符字符（字母/数字/下划线/连字符）时按点拆开
            #   合规：`db.tbl` → "db"."tbl"
            #   不合规：`100 * cnt`（含空格/运算符）→ 保守整体包 "100 * cnt"
            segments = content.split('.')
            if all(seg and re.fullmatch(r'[A-Za-z_][\w\-]*', seg) for seg in segments):
                out.append('.'.join(f'"{seg}"' for seg in segments))
            else:
                # 内含双引号 → 转义为 ""；避免破坏输出的双引号字面量结构
                escaped = content.replace('"', '""')
                out.append(f'"{escaped}"')
            i = j
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _normalize_slot_sql_for_dialect(sql: str, conn_type: str) -> str:
    """sqlSlots 入库出口方言归一：按目标数据源翻译反引号标识符。

    行为契约：
      - conn_type 为空 / 未知 / 反引号方言（Spark/MySQL/StarRocks/Doris）→ 原样返回（零回归）
      - ANSI 双引号方言（PostgreSQL/GaussDB）→ 反引号 `xxx` 翻译为双引号 "xxx"，
        含点号的 `db.tbl` 拆为 "db"."tbl"（PG 不支持整体带点标识符）

    注意：
      - 该函数**词法级**处理，不解析 SQL 结构，因此对 raw_sql 的 CTE / 窗口 / 子查询完全透明；
      - 与 _project_slot_sql_table_segments（段数裁剪）、_to_remote_sql（占位名兜底）
        组合后，PG/GaussDB 场景下入库 SQL 就是完整合规形态；
      - Spark/MySQL 走 'keep' 分支，一次字符串检查即返回，性能开销可忽略。
    """
    if not sql or not conn_type:
        return sql
    style = _dialect_backtick_style(conn_type)
    if style == 'ansi':
        return _rewrite_backticks_to_ansi(sql)
    return sql


def _to_remote_sql(sql: str, source_table: str, conn_type: str = '') -> str:
    """sqlSlots 入库前的反向归一化：把已知本地占位表名替换为真实 `source.table`。

    与 _to_local_sql 形成对偶（local↔remote），让 raw_sql 即使误用 _kb_src/main_data
    也能在平台 Spark 正确执行，避免一次小笔误把整张图表打成 TABLE_OR_VIEW_NOT_FOUND。

    替换策略（**精准**，避免误伤）：
        仅匹配紧跟在 FROM / JOIN 关键字之后的占位名，支持可选反引号包裹；
        因此：
          - 字符串字面量内的占位名（'main_data'）不命中
          - 列名/CTE 别名/AS 别名（含恰好同名的 _kb_src 列）不命中
          - 反引号包裹的 `_kb_src` 也能正确替换
        替换发生时打 stdout 告警，方便回查 spec 里残留的占位名。

    Args:
        conn_type: 可选；目标数据源 connection_type。用于选定占位名替换后的引号形态：
            - 反引号方言（SPARK/MYSQL/STARROCKS/DORIS/未知）→ `db.table`（保留反引号，历史行为）
            - ANSI 双引号方言（POSTGRESQL/GAUSSDB）→ 裸写 db.table（此处不加双引号；
              段拆双引号由 _project_slot_sql_table_segments 或 _normalize_slot_sql_for_dialect 完成）
    """
    if not sql or not source_table:
        return sql
    out = sql
    hit: List[str] = []
    # 把 source_table 中可能已有的反引号脱掉再补，避免 ` `db.t` ` 双层包裹
    bare_table = source_table.strip('`')
    # 按方言选定包裹形态：反引号方言用反引号；ANSI 方言此处仅裸写，包引号由后续方言归一负责
    style = _dialect_backtick_style(conn_type)
    quoted = f'`{bare_table}`' if style == 'keep' else bare_table
    for ph in _REMOTE_PLACEHOLDER_NAMES:
        # 仅匹配 FROM/JOIN 之后的位置，支持可选反引号包裹
        # 形如：FROM _kb_src / FROM `_kb_src` / JOIN main_data / join `main_data`
        pattern = rf'(\b(?:FROM|JOIN)\s+)`?{re.escape(ph)}`?(?=\s|,|\)|$|;)'
        new_out, n = re.subn(pattern, lambda m: m.group(1) + quoted,
                             out, flags=re.IGNORECASE)
        if n > 0:
            out = new_out
            hit.append(f'{ph}×{n}')
    if hit:
        print(f'⚠️ [runner] sqlSlots 检出本地占位表名（{", ".join(hit)}），'
              f'已自动归一为 {quoted}，请回头修正 spec 中的 raw_sql')
    return out

def _project_slot_sql_table_segments(sql: str, source_table: str, conn_type: str) -> str:
    """sqlSlots 入库前的方言段数裁剪：把 SQL 中的完整 `source_table` 按 conn_type 归一。

    背景（与 _build_fetch_sql 段数裁剪对偶）：
      - `_build_fetch_sql` 已按 conn_type 把三段式 `catalog.db.table` 裁剪为两段 `db.table`
        （MySQL/PG/GaussDB），保证远端取数 SQL 合规；
      - 但 sqlSlots 入库路径（KPI/DSL chart/raw_sql）之前只做了 `_to_remote_sql` 的
        "占位名 → 真实 source_table"反向归一，未做段数裁剪；导致 spec.source.table 若为
        三段式（prefetch 拿到的都是三段），入库 SQL 就会带三段式，被 L2 OLAP 硬拦截 raise，
        且 KPI 通道无 raw_sql 逃生口，会阻塞整套构建。
      - 此函数只对紧跟在 FROM/JOIN 之后的 `source_table`（含反引号）做替换，与
        `_to_remote_sql` 相同的词法边界，避免误伤字符串字面量或列名。

    行为契约：
      - 反引号方言（SPARK/MYSQL/STARROCKS/DORIS）：
          · 段数已合规 → 原样返回；
          · 需裁剪 → 替换为 `` `db.table` ``（保持反引号包裹，历史形态）
      - ANSI 双引号方言（POSTGRESQL/GAUSSDB）：
          · 段数已合规 → 仍需去掉反引号，翻译为 "db"."table"（避免 `db.tbl` → "db.tbl" 整体解析）；
          · 需裁剪 → 同样按 "db"."table" 输出
      - conn_type 为空 → 兼容旧行为，不改写
    """
    if not sql or not source_table or not conn_type:
        return sql
    bare_table = source_table.strip('`')
    projected = _runner_project_table_name_for_sql(bare_table, conn_type)
    if not projected:
        return sql
    style = _dialect_backtick_style(conn_type)
    # 段数已合规 + 反引号方言：不改写（历史零回归行为）
    if projected == bare_table and style == 'keep':
        return sql
    # 生成目标形态的表名（保持与 _to_remote_sql 出口引号风格一致）
    if style == 'ansi':
        # PG/GaussDB：段独立双引号包裹
        quoted_short = '.'.join(f'"{seg}"' for seg in projected.split('.'))
    else:
        # 反引号方言：整体反引号包裹（与旧行为一致）
        quoted_short = f'`{projected}`'
    # 精准匹配 FROM/JOIN 后紧跟的完整表名（可选反引号/双引号包裹），避免命中字符串字面量/列名
    pattern = rf'(\b(?:FROM|JOIN)\s+)[`"]?{re.escape(bare_table)}[`"]?(?=\s|,|\)|$|;)'
    new_sql, n = re.subn(pattern, lambda m: m.group(1) + quoted_short,
                         sql, flags=re.IGNORECASE)
    if n > 0:
        # 累加到 module 级统计，由 Step C 结束时 _flush_slot_projection_summary 聚合打印。
        # 不在此处逐条打印，避免 KPI + 30 chart 场景下 30+ 行日志刷屏。
        key = f'`{bare_table}` → {quoted_short}（{conn_type}）'
        _slot_projection_stats[key] = _slot_projection_stats.get(key, 0) + n
        return new_sql
    return sql


def _flush_slot_projection_summary() -> None:
    """Step C 结束时聚合打印 sqlSlots 方言段数裁剪统计，并清空累加器。

    契约：
      - 累加器为空 → 静默不打印（lakehouse/StarRocks/Doris 场景零噪音）
      - 累加器非空 → 单行汇总所有 (原表名 → 短表名, 累计命中次数)
      - 打印后清零，保证同一进程内重复 build_kanban 不串扰
    """
    if not _slot_projection_stats:
        return
    total = sum(_slot_projection_stats.values())
    detail = '；'.join(f'{k}×{v}' for k, v in _slot_projection_stats.items())
    print(f'🔧 [runner] sqlSlots 方言段数裁剪聚合：共命中 {total} 处 —— {detail}')
    _slot_projection_stats.clear()

def _exec_local(con, sql: str, source_table: str):
    """运行 SQL，返回 DataFrame。失败抛 RuntimeError 由调用方决定降级或上抛。"""
    local_sql = _to_local_sql(sql, source_table, con=con)
    try:
        return con.execute(local_sql).fetchdf()
    except Exception as ex:
        raise RuntimeError(f'[DuckDB] 本地执行失败: {ex}\n--- SQL ---\n{local_sql}') from ex


def _validate_sql(con, sql: str, source_table: str) -> Tuple[bool, str]:
    """编译期 EXPLAIN 体检：暴露语法/列名/语义错误。返回 (ok, error_msg)。"""
    if not sql:
        return True, ''
    try:
        con.execute(f'EXPLAIN {_to_local_sql(sql, source_table, con=con)}')
        return True, ''
    except Exception as ex:
        return False, str(ex)


# ============================================================
# 2ter. 字段表达式工具（保留：_is_bare_col / _metric_alias）
# ============================================================

_BARE_COL_RE = re.compile(r'^[`"]?[A-Za-z_][\w]*[`"]?$')


def _is_bare_col(field: str) -> bool:
    return bool(field and _BARE_COL_RE.match(field.strip()))


def _metric_alias(expr: str) -> str:
    """从聚合表达式生成稳定且语义可读的别名。

    设计目标（解决后端 Spark HashMap 乱序 + 别名 30 字符截断噪音）：
      1) 简单聚合：SUM(sales) → sum_sales（保留旧行为）
      2) 比率/百分比表达式：解析每个聚合调用，按 `_per_` 拼接，含 *100 加 `_pct`：
         - SUM(gross_profit) * 100.0 / NULLIF(SUM(sales), 0)         → gross_profit_per_sales_pct
         - SUM(return_quantity) * 100.0 / NULLIF(SUM(sales_volume),0) → return_quantity_per_sales_volume_pct
         - SUM(sales) / NULLIF(SUM(sales_volume), 0)                  → sales_per_sales_volume
      3) 复杂 CASE/算术表达式：取首个聚合内字段 + 函数前缀作语义骨架；
         不再做 30 字符暴力截断，避免出现 `_100_0_null` 之类的尾部噪音。
      4) 任何分支输出均为合法 SQL 标识符（^[a-z][a-z0-9_]*$），且**全局唯一性由调用方保证**（_compile_kpi 等会做去重）。
    """
    s = (expr or '').strip()

    # ---- 分支 1：纯单聚合 ----
    m = re.match(
        r'^(?P<f>SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(\s*(?:DISTINCT\s+)?(?P<c>[^)]+?)\s*\)$',
        s, flags=re.IGNORECASE,
    )
    if m:
        f = m.group('f').lower()
        c = m.group('c').strip().strip('`').strip('"')
        if c == '*':
            return f'{f}_count'
        if _is_bare_col(c):
            distinct = bool(re.search(r'DISTINCT', s, re.IGNORECASE))
            return f'{f}_distinct_{c}' if distinct else f'{f}_{c}'

    # ---- 分支 2：解析表达式中的所有聚合调用，按出现顺序拼语义骨架 ----
    # 提取形如 SUM(col) / AVG(col) 的调用（仅取裸列名作语义片段；嵌套表达式跳过）
    agg_calls = re.findall(
        r'\b(SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(\s*(?:DISTINCT\s+)?([^()]+?)\s*\)',
        s, flags=re.IGNORECASE,
    )
    bare_parts: List[str] = []
    for f, c in agg_calls:
        c_clean = c.strip().strip('`').strip('"')
        if _is_bare_col(c_clean):
            bare_parts.append(c_clean.lower())

    if len(bare_parts) >= 2:
        # 比率 vs 差值/算术：仅当表达式含 `/`（真正的"占比"语义）才用 `_per_`，
        # 否则用 `_calc` 避免误导（如 `SUM(sales) - SUM(refund)` 不是占比）。
        is_ratio = '/' in s
        if is_ratio:
            skeleton = f'{bare_parts[0]}_per_{bare_parts[1]}'
        else:
            skeleton = f'{bare_parts[0]}_{bare_parts[1]}_calc'
        # 含 `*100` 视为百分比指标
        if re.search(r'\*\s*100(?:\.0+)?\b', s):
            skeleton += '_pct'
        return skeleton

    if len(bare_parts) == 1:
        # 单聚合 + 算术（如 SUM(sales) - SUM(refund)），取首字段 + `_calc` 区分
        skeleton = bare_parts[0]
        if re.search(r'\*\s*100(?:\.0+)?\b', s):
            return f'{skeleton}_pct'
        # 含 CASE WHEN：用 `_filtered` 标注
        if re.search(r'\bCASE\b', s, re.IGNORECASE):
            return f'{skeleton}_filtered'
        # 含 `-`/`+`：用 `_calc`
        if re.search(r'[+\-]', s):
            return f'{skeleton}_calc'
        return skeleton

    # ---- 分支 3：兜底（无聚合，纯表达式如 retail_price）----
    # 保持简短可读：snake_case 不截断，但去掉纯数字片段（100/0 等噪音）
    cleaned = re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')
    parts = [p for p in cleaned.split('_') if p and not p.isdigit()]
    return '_'.join(parts) or 'metric'


def _metric_alias_of(m: Metric) -> str:
    return m.alias or _metric_alias(m.expr)


def _to_native(v):
    """numpy/pandas 标量 → Python 原生（防 H10）。"""
    try:
        if hasattr(v, 'item'):
            v = v.item()
    except Exception:
        pass
    if isinstance(v, float):
        import math
        if math.isnan(v) or math.isinf(v):
            return 0
    return v


# ============================================================
# 2quater. 维度 SQL 生成（DuckDB 语义与平台 SQL 二合一）
# ============================================================

def _spark_time_expr(d: Dim) -> str:
    """生成时间分桶 SQL（Spark 风格 + 通过本地兼容层在 DuckDB 可跑）。

    设计要点（远端 Spark / 本地 DuckDB 二合一）：
      - col_type ∈ {date, timestamp}：day/month/year 直接用 Spark 原生 DATE_FORMAT。
        物理日期列无需走 string helper，避免旧版本地体检把 DATE 送入 try_strptime 的兼容问题。
      - col_type='string'：包一层 spark_safe_to_timestamp 把字符串归一化，再走 helper。
      - week/quarter 保留既有兼容路径：week 依赖 spark_safe_week_format 的 ISO 周实现；quarter
        需要把输入显式归一为 timestamp，避免 DuckDB year()/month() 吃到 VARCHAR。
    """
    is_native_time = d.col_type in ('date', 'timestamp')
    if is_native_time:
        col_expr = f'`{d.expr}`' if _is_bare_col(d.expr) else f'({d.expr})'
    else:
        inner = f'`{d.expr}`' if _is_bare_col(d.expr) else f'({d.expr})'
        col_expr = f'spark_safe_to_timestamp({inner})'
    g = d.granularity
    if g == 'day':
        return f"DATE_FORMAT({col_expr}, 'yyyy-MM-dd')" if is_native_time \
            else f"spark_safe_date_format({col_expr}, 'yyyy-MM-dd')"
    if g == 'week':
        return f'spark_safe_week_format({col_expr})'
    if g == 'month':
        return f"DATE_FORMAT({col_expr}, 'yyyy-MM')" if is_native_time \
            else f"spark_safe_date_format({col_expr}, 'yyyy-MM')"
    if g == 'quarter':
        # 显式归一为 timestamp 表达式，让本地 DuckDB 的 year()/month() 拿到 TIMESTAMP
        # 而非 VARCHAR；spark_safe_to_timestamp 对已经是 timestamp 的入参幂等。
        ts_expr = (
            col_expr
            if col_expr.lstrip().lower().startswith('spark_safe_to_timestamp(')
            else f'spark_safe_to_timestamp({col_expr})'
        )
        # CASE WHEN 守护：DuckDB 的 concat() 把 NULL 当空串拼接（产生 '-Q' 幽灵桶），
        # 而 Spark concat() 默认 NULL 传播；用 CASE WHEN 让两端行为一致返回 NULL，
        # 解析失败/空值的行不进入虚假分桶。
        return (
            f"CASE WHEN {ts_expr} IS NULL THEN NULL ELSE "
            f"concat(year({ts_expr}), '-Q', "
            f"cast(ceil(month({ts_expr})/3.0) AS int)) END"
        )
    if g == 'year':
        return f"DATE_FORMAT({col_expr}, 'yyyy')" if is_native_time \
            else f"spark_safe_date_format({col_expr}, 'yyyy')"
    raise ValueError(f'未知 granularity: {g}')


def _dim_sql(d: Dim) -> Tuple[str, str]:
    """返回 (dim_sql_expr, dim_alias)。"""
    if not isinstance(d, Dim):
        raise ValueError(f'[Runner] _dim_sql 需要 Dim 实例，得到: {type(d).__name__}')
    if d.is_time:
        sql_expr = _spark_time_expr(d)
        alias = d.alias or f'{d.expr.strip()}_{d.granularity}'
        return sql_expr, alias
    expr = d.expr.strip()
    if _is_bare_col(expr):
        col = expr.strip('`').strip('"')
        return f'`{col}`', d.alias or col
    return f'({expr})', d.alias or _metric_alias(expr)


# ============================================================
# 2quater-bis. GROUP BY 维度 NULL 过滤（数据保真硬契约）
# ------------------------------------------------------------
# 设计动机（消除 4 类静默失真）：
#   ① string 时间列 try_to_timestamp 解析失败 → DATE_FORMAT(NULL) → GROUP BY
#      产生 "[null, 0]" 尾节点 → 折线/同环比末尾陡降到 0、mom_rate=-100% 假象
#   ② 分类维（order_status / category 等）含 NULL → 饼图/柱图/雷达 多出空类目
#   ③ 同环比 LAG 对 NULL 期产生 -100% 假同比/环比
#   ④ 用户在 Spec.source.where 显式过滤是"双重负担"，runner 应当默认数据干净
#
# 实现策略（最小破坏面）：
#   - 仅过滤 GROUP BY 维度本身，不动 metrics（COUNT(*) / COUNT(case when) 语义保留）
#   - 使用 dim_sql 表达式而非裸列名 → 兼容 spark_safe_to_timestamp 包装/CASE 表达式
#   - 与 spec.source.where 用 AND 串联，不冲突
#   - 设计逃生口：`Dim(expr=..., description='__keep_null__')` 可显式保留 NULL 桶
# ============================================================

def _dim_null_filter(d: 'Dim') -> Optional[str]:
    """返回 "<dim_sql_expr> IS NOT NULL" 字符串，用于 WHERE 自动追加；
    若维度显式声明 description='__keep_null__' 则返回 None（逃生口）。
    """
    if d is None or not isinstance(d, Dim):
        return None
    if (d.description or '').strip() == '__keep_null__':
        return None
    sql_expr, _ = _dim_sql(d)
    return f'{sql_expr} IS NOT NULL'


def _merge_where(spec_where: Optional[str], *extra_clauses: str) -> str:
    """把 spec.source.where 与若干自动追加子句合并为 "WHERE ..."（带前导换行）。
    无任何条件返回空串。所有子句以 AND 连接，自动子句各加括号防止运算符优先级陷阱。
    """
    parts: List[str] = []
    if spec_where:
        parts.append(f'({spec_where})')
    for c0 in extra_clauses:
        if c0:
            parts.append(f'({c0})')
    if not parts:
        return ''
    return '\nWHERE ' + ' AND '.join(parts)


def _format_order_by(order_by: Optional[str], known_aliases: Optional[List[str]] = None,
                     default_dir: str = 'ASC') -> str:
    """统一 ORDER BY 子句格式化（消除 sankey/table 把 '-2' 当列名加反引号的返工）。

    支持四类输入：
      '-SUM(sales)' / 'SUM(sales) DESC'  → ORDER BY <expr> DESC
      'amount'      / 'amount DESC'      → ORDER BY `amount` <dir>（known_aliases 命中时）
      '-1' / '0'                          → ORDER BY <pos+1>（DuckDB 列位置语法，1-based）
      ''            / None                → ''
    """
    if not order_by:
        return ''
    ob = str(order_by).strip()
    if not ob:
        return ''

    # 提取方向
    if ob.startswith('-'):
        direction = 'DESC'
        key = ob[1:].strip()
    else:
        m_dir = re.search(r'\s+(ASC|DESC)\s*$', ob, re.I)
        if m_dir:
            direction = m_dir.group(1).upper()
            key = ob[:m_dir.start()].strip()
        else:
            direction = default_dir
            key = ob

    # 数字 → ORDER BY 位置
    if key.lstrip('+-').isdigit():
        pos = int(key.lstrip('+-')) + 1  # 用户从 0 开始；SQL 从 1 开始
        return f'ORDER BY {pos} {direction}'

    # 含聚合或括号 → 当作表达式（不加反引号）
    if re.search(r'\b(SUM|AVG|COUNT|MIN|MAX|PERCENTILE|STDDEV|VARIANCE)\s*\(', key, re.I) or '(' in key:
        return f'ORDER BY {key} {direction}'

    # 命中已知别名 → 加反引号
    if known_aliases and key in known_aliases:
        return f'ORDER BY `{key}` {direction}'

    # 默认：纯标识符当作列名（兜底加反引号）
    return f'ORDER BY `{key}` {direction}'


def _build_select_sql_v2(spec: Spec, dim_sql: str, dim_alias: str, metrics: List[Metric],
                         order_by: Optional[str] = None, limit: Optional[int] = None,
                         dim_obj: Optional['Dim'] = None) -> str:
    """生成单层聚合 SQL。order_by 走统一 _format_order_by 处理。

    数据保真：当 dim_obj 提供时，自动追加 `<dim_sql> IS NOT NULL` 到 WHERE，
    消除时间解析失败 / 分类列空值导致的尾部 [null, 0] 失真桶。
    """
    cols = [f'{dim_sql} AS `{dim_alias}`']
    aliases = [dim_alias]
    for m in metrics:
        alias = _metric_alias_of(m)
        cols.append(f'{m.expr} AS `{alias}`')
        aliases.append(alias)
    _joined = _NL_INDENT.join(cols)
    sql = f"SELECT\n  {_joined}\nFROM {spec.source.table}"
    null_filter = _dim_null_filter(dim_obj) if dim_obj is not None else None
    sql += _merge_where(spec.source.where, null_filter or '')
    sql += f'\nGROUP BY {dim_sql}'
    ob_clause = _format_order_by(order_by, known_aliases=aliases)
    if ob_clause:
        # _build_select_sql_v2 历史上还允许 'sum_sales' 反查 metric.expr → alias，
        # 这里保留：若 known_aliases 未命中但 expr 命中，做一次别名重写。
        if order_by and not order_by.lstrip('-+').lstrip().isdigit():
            raw_key = order_by.lstrip('-').rstrip()
            raw_key = re.sub(r'\s+(ASC|DESC)\s*$', '', raw_key, flags=re.I).strip()
            if raw_key not in aliases and '(' not in raw_key:
                for m in metrics:
                    if m.expr == raw_key:
                        rewritten = ('-' if order_by.startswith('-') else '') + _metric_alias_of(m)
                        ob_clause = _format_order_by(rewritten, known_aliases=aliases)
                        break
        sql += '\n' + ob_clause
    if limit:
        sql += f'\nLIMIT {int(limit)}'
    return sql


# ============================================================
# 2.5 CSV 维度画像 & 温和降级（方案 D / 温和降级 A）
# ------------------------------------------------------------
# 目的：在 CSV 已就位、DuckDB 视图已注册之后，B 阶段编译之前，
#       基于"真实数据"扫一遍 spec 涉及的 dim 列（NDV / 单一值 / 数值 range），
#       对必然退化的图表（NDV=1 单类目、scatter 跨度≈0）做最小破坏面降级：
#       仅前缀标题告警 + extras 留痕，不改 kind / dims / metrics 契约。
#
# 设计权衡：
#   - 不改 kind（pie→bar 这种）：避免触发 _CONTRACTS 二次校验失败、layout span 错位
#   - 不删图：spec 描述与产物保持 1:1，体感链路不变
#   - 标题加醒目 ⚠️：用户一眼看懂"为什么这张图只有一根柱子" → 不再是"数据失真"而是"诚实呈现"
# ============================================================

# 哪些 kind 的"分组维 NDV=1"是必然退化（单根柱、单瓣饼、单层 treemap...）
_DEGRADE_KINDS_FOR_SINGLE_DIM = {
    'bar', 'pie', 'funnel', 'radar', 'treemap', 'sunburst',
    'sankey', 'graph', 'heatmap', 'boxplot',
}

# scatter 数值跨度阈值（x 或 y 的 max-min 跨度小于此值视为"集中点云"）
_SCATTER_NARROW_RANGE = 1.0


def _extract_bare_columns(exprs) -> List[str]:
    """从一组表达式中粗略抽出"裸列名"（含聚合的不算）。

    仅识别 `^[a-zA-Z_][a-zA-Z0-9_]*$` 形态的纯标识符；
    `SUM(x)` / `CASE WHEN ...` / `geolocation_lat * 1.0` 等一律跳过。
    这是温和降级 A 的安全边界：扫不到的就不降级，避免误伤 LLM 的复杂表达式。
    """
    out = []
    for e in (exprs or []):
        s = (getattr(e, 'expr', None) or str(e) or '').strip().strip('`"')
        if s and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', s):
            out.append(s)
    return out


def _probe_string_time_columns(con, spec) -> List[Dict[str, Any]]:
    """嗅探 spec 中所有"被当时间维使用的 string 列"，对解析失败率高的列发软告警。

    P1-1 健壮性增强（2026-06）：解决 'Jan 2025' / 'Q1 2025' / '一月 2025' 等
    非标字符串时间格式导致 try_to_timestamp / spark_safe_to_timestamp 全 NULL，
    最终 GROUP BY 后空集 / 看板"无数据"的隐蔽根因。

    扫描范围（按优先级，按需取并集）：
      - spec.source.time_col（time_type 为 'string' 时纳入）
      - spec.charts[*].dims 中所有 Dim.is_time && col_type=='string' 的 expr
        （expr 是裸列名才嗅探；CASE/SQL 表达式跳过，避免误报）

    返回：[{col, sample_raw: List[str], parse_fail_ratio: float, total: int, hint: str}, ...]
    任何异常静默返回 [] —— 嗅探是优化路径，不影响主流程。

    上层使用：
      - 若返回非空 → print stderr 软告警（红字醒目，列出原始样本）
      - 同步写入 build_kanban 的 write_result['time_parse_failures']，让 LLM
        在 Step E 必抄、Agent 后续可程序化处理
    """
    out: List[Dict[str, Any]] = []
    try:
        # 1) 收集所有"string 时间列"候选（裸列名）
        # ────────────────────────────────────────────────────────────────
        # 精准触发门槛（2026-08 优化，消除 94% 假告警）：
        #   旧逻辑：只要 source.time_col + time_type='string' 就纳入嗅探，
        #           但 LLM 常声明 time_col='dt' 只为 spec 完整性，chart 内实际
        #           用 order_year || '-Q' || order_quarter 拼时间轴 → 旧逻辑
        #           打出 stime_fail 假告警（远端数据完整），误导 Agent Step E
        #           复述"远端极可能空集" → 用户体验受损。
        #   新逻辑：source.time_col 必须先被 charts[*] 的 time_dim/Compare.dim
        #           实际引用（作为 Dim.expr 裸列），才纳入嗅探候选。
        #   真实环境验证（346 spec × 5 模型，见 verify_new_probe_logic.py）：
        #     - 消除 50/53 假告警（94%）
        #     - 保留 4/4 真告警（0 漏报）
        #     - 0 误抑制
        # ────────────────────────────────────────────────────────────────
        candidates: set = set()

        # 1.1) charts[*].dims 里 is_time + col_type=='string' 的裸列
        #      Chart.dims + Compare.dim 都要扫（Compare 走 dim 单字段，非 dims 列表）
        chart_time_cols: set = set()
        for c in (getattr(spec, 'charts', None) or []):
            _dims_list = list(getattr(c, 'dims', None) or [])
            _cmp_dim = getattr(c, 'dim', None)  # Compare 实例的时间维
            if _cmp_dim is not None:
                _dims_list.append(_cmp_dim)
            for d in _dims_list:
                # Dim 实例（time_dim 工厂）
                try:
                    if hasattr(d, 'is_time') and d.is_time and \
                            getattr(d, 'col_type', 'string') == 'string':
                        expr = (getattr(d, 'expr', '') or '').strip()
                        if expr and re.match(r'^[A-Za-z_][\w$]*$', expr):
                            chart_time_cols.add(expr)
                except Exception:
                    continue
        candidates.update(chart_time_cols)

        # 1.2) source.time_col（收紧门槛：必须同时被 chart 引用才嗅探）
        # 若 chart 未实际引用该列（如 chart 用别列拼时间轴、或全走 raw_sql），
        # 则 source.time_col 只是声明，不影响远端数据 → 不发假告警。
        try:
            src = getattr(spec, 'source', None)
            if src is not None:
                _t_col = (getattr(src, 'time_col', '') or '').strip()
                _t_type = (getattr(src, 'time_type', 'string') or '').strip().lower()
                if _t_col and _t_type == 'string' and re.match(r'^[A-Za-z_][\w$]*$', _t_col):
                    # 关键约束：只有当 source.time_col 实际被 chart-level time_dim 引用时
                    # 才纳入嗅探（消除"声明未使用"的假告警）
                    if _t_col in chart_time_cols:
                        candidates.add(_t_col)
        except Exception:
            pass

        if not candidates:
            return []

        # 2) 限定到 csv 实际存在的列
        try:
            actual = {r[0] for r in con.execute(
                f'SELECT column_name FROM (DESCRIBE {_LOCAL_VIEW})'
            ).fetchall()}
        except Exception:
            actual = set()
        if actual:
            candidates = {c for c in candidates if c in actual}
        if not candidates:
            return []

        # 3) 单条 SQL 算解析失败率 + 原始样本
        # 用 spark_safe_to_timestamp 宏跑一遍：
        #   total      = COUNT(col IS NOT NULL)（剔除原始 NULL，只看可解析数据）
        #   parsed_ok  = COUNT(spark_safe_to_timestamp(col) IS NOT NULL)
        #   sample_raw = ARRAY_AGG 取 5 条非空原始值
        for col in sorted(candidates):
            q = f'"{col}"'
            try:
                # FIRST 5 distinct samples（更易暴露格式特征：避免重复值掩盖问题）
                row = con.execute(
                    f"SELECT "
                    f"COUNT(*) FILTER (WHERE {q} IS NOT NULL) AS total, "
                    f"COUNT(*) FILTER (WHERE spark_safe_to_timestamp({q}) IS NOT NULL) AS parsed_ok, "
                    f"(SELECT LIST(DISTINCT CAST({q} AS VARCHAR)) "
                    f"   FROM (SELECT {q} FROM {_LOCAL_VIEW} "
                    f"         WHERE {q} IS NOT NULL LIMIT 5)) AS samples "
                    f"FROM {_LOCAL_VIEW}"
                ).fetchone()
            except Exception:
                # 单列嗅探失败（如列名含特殊字符）→ 跳过该列继续其他列
                continue
            if not row:
                continue
            total = int(row[0] or 0)
            parsed_ok = int(row[1] or 0)
            samples_raw = row[2] or []
            if total == 0:
                continue  # 列全 NULL，无样本可看，避免误报
            fail_ratio = 1.0 - (parsed_ok / total)
            # 阈值：失败率 > 50% 即视为"该列大概率全图无数据"
            if fail_ratio > 0.5:
                # samples 转为 list[str]，限制单值长度（避免日志爆炸）
                samples = [str(s)[:64] for s in samples_raw if s is not None][:5]
                out.append({
                    'col': col,
                    'sample_raw': samples,
                    'parse_fail_ratio': round(fail_ratio, 3),
                    'parsed_ok': parsed_ok,
                    'total': total,
                    'hint': (
                        f"列 '{col}' 在本地预览中 {parsed_ok}/{total} 行可解析为 timestamp "
                        f"（失败率 {fail_ratio*100:.0f}%）。样本：{samples}。"
                        f"若样本是 'Jan 2025' / 'Q1 2025' / 中文月份等非标格式，"
                        f"且数据源含真正的 DATE/TIMESTAMP 列，请改用 time_col=该 DATE 列；"
                        f"否则在 spec 中显式包 spark_safe_to_timestamp({col})。"
                    ),
                })
        return out
    except Exception as exc:
        # 嗅探失败完全静默，主流程继续
        print(f'⚠️  [TimeProbe] 时间列样本嗅探失败（非致命，继续）：{exc}')
        return []


def _profile_csv_columns(con, spec) -> Dict[str, Dict[str, Any]]:
    """对 spec 涉及的 dim 列扫一次 NDV/range/单一值，DuckDB 单条 SQL 拿全。

    返回：{col_name: {'ndv': int, 'single_value': Optional[Any],
                      'min': Any, 'max': Any, 'range_span': Optional[float]}}
    任何失败都返回 {} —— 降级是优化路径，不影响主流程。
    """
    try:
        cols: set = set()
        for c in (getattr(spec, 'charts', None) or []):
            cols.update(_extract_bare_columns(getattr(c, 'dims', None)))
            # scatter 的 x/y 轴分别来自 dims[0] 和 metrics[0]，因此 y 度量也要扫描 range。
            if getattr(c, 'kind', '') == 'scatter':
                cols.update(_extract_bare_columns(getattr(c, 'metrics', None)))
        if not cols:
            return {}

        # 用 DuckDB 实际列做交集（避免 spec 写错列名整条 SQL 失败）
        try:
            actual = {r[0] for r in con.execute(
                f'SELECT column_name FROM (DESCRIBE {_LOCAL_VIEW})'
            ).fetchall()}
        except Exception:
            actual = set()
        if actual:
            cols = {c for c in cols if c in actual}
        if not cols:
            return {}

        # 一条 SQL 拿全（NDV + min + max + 单一值兜底）
        select_parts = []
        cols_sorted = sorted(cols)
        for col in cols_sorted:
            q = f'"{col}"'
            select_parts.append(f'COUNT(DISTINCT {q}) AS ndv__{col}')
            select_parts.append(f'MIN({q}) AS min__{col}')
            select_parts.append(f'MAX({q}) AS max__{col}')
        sql = f"SELECT {', '.join(select_parts)} FROM {_LOCAL_VIEW}"
        row = con.execute(sql).fetchone()
        if not row:
            return {}

        out: Dict[str, Dict[str, Any]] = {}
        idx = 0
        for col in cols_sorted:
            ndv = int(row[idx] or 0); idx += 1
            mn = row[idx]; idx += 1
            mx = row[idx]; idx += 1
            span = None
            try:
                if mn is not None and mx is not None:
                    span = float(mx) - float(mn)
            except (TypeError, ValueError):
                span = None
            out[col] = {
                'ndv': ndv,
                'single_value': mn if ndv == 1 else None,
                'min': mn,
                'max': mx,
                'range_span': span,
            }
        return out
    except Exception as exc:
        # 画像失败完全静默，主流程继续
        print(f'⚠️  [Profile] 维度画像扫描失败（非致命，继续）：{exc}')
        return {}


def _auto_degrade_charts(charts, profile: Dict[str, Dict[str, Any]]):
    """温和降级 A：仅打标 + extras 留痕，不改 kind/dims/metrics。

    规则：
      ① 任意 dim 列 NDV=1 且 kind ∈ _DEGRADE_KINDS_FOR_SINGLE_DIM
         → 标题前缀 `⚠️ 单一类目「{value}」: `；extras['_degraded']='single_category'
      ② kind=='scatter' 且 x/y 轴 range_span<阈值
         → 标题前缀 `⚠️ 数据点高度集中: `；extras['_degraded']='narrow_range'
      ③ 其他情况：print 软告警，不改 spec
    """
    if not profile or not charts:
        return charts

    for c in charts:
        try:
            kind = getattr(c, 'kind', '')
            title = getattr(c, 'title', '') or ''
            extras = getattr(c, 'extras', None)
            if extras is None:
                extras = {}
                try:
                    c.extras = extras
                except Exception:
                    pass

            # 已被打过标记（重入安全）
            if extras.get('_degraded'):
                continue

            # —— 规则 ① 单一类目分组维
            if kind in _DEGRADE_KINDS_FOR_SINGLE_DIM:
                hit_col = None
                hit_val = None
                for col in _extract_bare_columns(getattr(c, 'dims', None)):
                    info = profile.get(col)
                    if info and info.get('ndv') == 1:
                        hit_col, hit_val = col, info.get('single_value')
                        break
                if hit_col is not None:
                    val_str = '' if hit_val is None else str(hit_val)
                    if len(val_str) > 24:
                        val_str = val_str[:24] + '…'
                    prefix = f'⚠️ 单一类目「{val_str}」: ' if val_str else '⚠️ 单一类目: '
                    if not title.startswith('⚠️'):
                        c.title = prefix + title
                    extras['_degraded'] = 'single_category'
                    extras['_degraded_col'] = hit_col
                    print(
                        f'🔄 [自动降级] {kind} "{title}" 分组维 {hit_col} NDV=1 '
                        f'→ 标题打标"单一类目「{val_str}」"（kind 保持 {kind}）'
                    )
                    continue

            # —— 规则 ② scatter 跨度≈0
            if kind == 'scatter':
                axis_cols = (
                    _extract_bare_columns((getattr(c, 'dims', None) or [])[:1])
                    + _extract_bare_columns((getattr(c, 'metrics', None) or [])[:1])
                )
                narrow_axes = []
                for col in axis_cols:
                    info = profile.get(col)
                    if not info:
                        continue
                    span = info.get('range_span')
                    if span is not None and span < _SCATTER_NARROW_RANGE:
                        narrow_axes.append((col, span))
                if narrow_axes:
                    desc = ', '.join(f'{c_}跨度{s_:.3g}' for c_, s_ in narrow_axes)
                    if not title.startswith('⚠️'):
                        c.title = f'⚠️ 数据点高度集中: {title}'
                    extras['_degraded'] = 'narrow_range'
                    extras['_degraded_axes'] = [{'col': c_, 'span': s_} for c_, s_ in narrow_axes]
                    print(f'🔄 [自动降级] scatter "{title}" {desc} → 标题打标"数据点高度集中"')
                    continue

            # —— 规则 ③ 软告警（不改 spec）
            for col in _extract_bare_columns(getattr(c, 'dims', None)):
                info = profile.get(col)
                if info and 1 < info.get('ndv', 0) <= 2 and kind in {'radar', 'funnel'}:
                    print(
                        f'⚠️  [软告警] {kind} "{title}" 分组维 {col} NDV={info["ndv"]} '
                        f'< 3，{kind} 至少需要 3 个分组才有意义（保留原图，不降级）'
                    )
                    break

        except Exception as exc:
            print(f'⚠️  [自动降级] 处理 chart "{getattr(c, "title", "?")}" 失败（非致命）：{exc}')
            continue

    return charts


# ============================================================
# 3. KPI 编译（DuckDB 单引擎）
# ============================================================

def _compile_kpi(spec: Spec, con) -> Tuple[List[List[Any]], Dict[str, Any], str]:
    """编译 KPI：返回 (slot_data 2D, kpi_config, sql)。

    支持两种 expr 来源（per-Metric）：
      ① 默认：`{k.expr} AS alias`，从 `spec.source.table` 取数。
      ② 跨表：`Metric.from_sql` 非空 → 编译为**标量子查询** `(SELECT {expr} FROM {from_sql}) AS alias`。

    编译策略：
      - 纯主表 KPI：保持旧行为，直接 `SELECT ... FROM 主表`，一次扫描完成。
      - 混合 KPI（主表 + from_sql）：主表 KPI 先收敛成单行子查询 `_kpi_root`，
        跨表 KPI 继续走标量子查询，外层再按原始顺序拼回同一条 SELECT。
        这样既避免 `FROM (SELECT 1)` 下主表列缺失，也避免把主表 cross-join 放大。
      - 纯跨表 KPI：外层 `FROM (SELECT 1) AS _kpi_root` 占位，避免无意义主表扫描。
    """
    if not spec.kpis:
        return [], {}, ''

    # 别名生成 + 唯一性兜底：极少数情况下两个 KPI 表达式可能派生出相同别名，
    # 此时为后出现的别名加 `_2`/`_3`... 后缀，避免 SQL 重复列名 + 前端 field 冲突。
    raw_aliases = [_metric_alias_of(k) for k in spec.kpis]
    seen_count: Dict[str, int] = {}
    final_aliases: List[str] = []
    for a in raw_aliases:
        if a not in seen_count:
            seen_count[a] = 1
            final_aliases.append(a)
        else:
            seen_count[a] += 1
            final_aliases.append(f'{a}_{seen_count[a]}')

    aliases = list(zip(final_aliases, spec.kpis))

    def _kpi_select_item(alias: str, k) -> str:
        """单个 KPI 的 SELECT 项；带 from_sql 时编译为标量子查询。"""
        from_sql = (getattr(k, 'from_sql', None) or '').strip()
        if from_sql:
            # 标量子查询：用户传完整 from 子句（表名/JOIN 串/带括号子查询都支持）。
            # WHERE 仅作用于主表 KPI；跨表 KPI 的过滤条件由用户自行写进 from_sql。
            return f'(SELECT {k.expr} FROM {from_sql}) AS `{alias}`'
        return f'{k.expr} AS `{alias}`'

    primary_aliases = [
        (a, k) for a, k in aliases
        if not (getattr(k, 'from_sql', None) or '').strip()
    ]
    cross_aliases = [
        (a, k) for a, k in aliases
        if (getattr(k, 'from_sql', None) or '').strip()
    ]

    if not cross_aliases:
        select_items = [_kpi_select_item(a, k) for a, k in aliases]
        _joined = _NL_INDENT.join(select_items)
        sql = f"SELECT\n  {_joined}\nFROM {spec.source.table}"
        if spec.source.where:
            sql += f'\nWHERE {spec.source.where}'
    else:
        outer_select_items: List[str] = []
        for a, k in aliases:
            from_sql = (getattr(k, 'from_sql', None) or '').strip()
            if from_sql:
                outer_select_items.append(_kpi_select_item(a, k))
            else:
                outer_select_items.append(f'_kpi_root.`{a}` AS `{a}`')
        outer_joined = _NL_INDENT.join(outer_select_items)

        if primary_aliases:
            primary_select_items = [f'{k.expr} AS `{a}`' for a, k in primary_aliases]
            primary_joined = ',\n    '.join(primary_select_items)
            primary_sql = f"SELECT\n    {primary_joined}\n  FROM {spec.source.table}"
            if spec.source.where:
                primary_sql += f'\n  WHERE {spec.source.where}'
            primary_sql = primary_sql.replace('\n', '\n  ')
            sql = (
                f"SELECT\n  {outer_joined}\n"
                f"FROM (\n  {primary_sql}\n) AS _kpi_root"
            )
        else:
            sql = f"SELECT\n  {outer_joined}\nFROM (SELECT 1) AS _kpi_root"

    headers = [a for a, _ in aliases]
    try:
        df = _exec_local(con, sql, spec.source.table)
        if len(df) == 0:
            values = [0] * len(aliases)
        else:
            values = [_to_native(df.iloc[0][a]) for a in headers]
    except Exception as ex:
        # 整批失败 → 不再连坐归 0，逐条降级单 KPI 重试，
        # 仅把"真正不兼容/计算错"的那一条置 0，其他保持真实数值。
        print(f'⚠️ [KPI 本地执行失败，逐条降级重试] {ex}')
        values = []
        for a, k in aliases:
            from_sql_one = (getattr(k, 'from_sql', None) or '').strip()
            if from_sql_one:
                single_sql = f'SELECT {k.expr} AS `{a}`\nFROM {from_sql_one}'
            else:
                single_sql = f'SELECT {k.expr} AS `{a}`\nFROM {spec.source.table}'
                if spec.source.where:
                    single_sql += f'\nWHERE {spec.source.where}'
            try:
                df1 = _exec_local(con, single_sql, spec.source.table)
                if len(df1) == 0:
                    values.append(0)
                else:
                    values.append(_to_native(df1.iloc[0][a]))
            except Exception as ex_one:
                print(f'  ❌ KPI "{k.label}" 本地不可执行，置 0：{ex_one}'.split('\n')[0])
                values.append(0)

    slot_data = [headers, values]
    # items[*].field 是协议层修复（解决 Spark HashMap 乱序）：
    # 前端 renderKpi 优先按 field 在 headers 里查下标取 values，
    # 不再依赖"items 顺序 == values 顺序"，从此与 Spark 实际返回顺序解耦。
    kpi_config = {
        'items': [
            {
                'label': k.label,
                'field': a,
                'format': k.format,
                **({'prefix': k.prefix} if k.prefix else {}),
                **({'suffix': k.suffix} if k.suffix else {}),
            }
            for a, k in aliases
        ]
    }
    return slot_data, kpi_config, sql.strip()


# ============================================================
# 4. Chart 编译（DuckDB 单源 adapter）
# ============================================================

_ADAPTERS: Dict[str, Any] = {}


def _adapter(*names):
    def deco(fn):
        for n in names:
            _ADAPTERS[n] = fn
        return fn
    return deco


def _exec_for_chart(con, sql: str, source_table: str, title: str):
    """统一封装：执行 SQL，失败时打日志并返回空 DataFrame。"""
    import pandas as pd
    try:
        return _exec_local(con, sql, source_table)
    except Exception as ex:
        print(f'⚠️ [{title}] DuckDB 本地执行失败：{ex}')
        return pd.DataFrame()


def _generic_dim_metric(spec: Spec, c: Chart, con):
    if not c.dims or not c.metrics:
        raise ValueError(f'[Runner] {c.kind} 需要 dims + metrics（chart={c.title}）')
    d0 = c.dims[0]
    dim_sql_expr, dim_alias = _dim_sql(d0)
    # 远端一致性铁律：本地仅靠 pandas 排序无法约束远端 Spark，必须把排序写入 SQL。
    #   - 时间维：默认 `ORDER BY <time_dim> ASC`（line/bar 时间序列必须时序）
    #   - 非时间维 + pie：由 _ad_pie 自动补 `-<metric>` 默认 order_by（保证扇区一致）
    #   - 用户显式 order_by 优先（不覆盖）
    effective_order_by = c.order_by
    if not effective_order_by and d0.is_time:
        effective_order_by = dim_alias  # 升序时间
    sql = _build_select_sql_v2(spec, dim_sql_expr, dim_alias, c.metrics, effective_order_by, c.limit, dim_obj=d0)
    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    if d0.is_time and dim_alias in df.columns and len(df) > 0:
        # 兜底：若 DuckDB 返回未严格按 SQL ORDER BY 输出（极少见），再保险排序一次
        df = df.sort_values(dim_alias).reset_index(drop=True)
    if df.empty:
        slot_data = [[dim_alias] + [_metric_alias_of(m) for m in c.metrics]]
    else:
        slot_data = _B['df_to_slot_data'](df)
    return slot_data, sql


@_adapter('line')
def _ad_line(spec, c: Chart, con):
    slot_data, sql = _generic_dim_metric(spec, c, con)
    series_cfg = []
    for i, _ in enumerate(c.metrics or []):
        item = {'type': 'line', 'smooth': c.smooth}
        if i == 0:
            item['areaStyle'] = {'opacity': 0.3}
        if c.dual_axis and i in c.dual_axis:
            item['yAxisIndex'] = 1
        series_cfg.append(item)
    chart_config = {'chartType': 'line', 'series': series_cfg}
    if c.dual_axis:
        chart_config['yAxis'] = [{'name': '左轴'}, {'name': '右轴', 'position': 'right'}]
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('bar')
def _ad_bar(spec, c: Chart, con):
    slot_data, sql = _generic_dim_metric(spec, c, con)
    series_cfg = [
        {'type': 'bar', 'barMaxWidth': 40, **({'stack': 'total'} if c.stacked else {})}
        for _ in (c.metrics or [])
    ]
    chart_config = {'chartType': 'bar', 'series': series_cfg}
    if c.dual_axis:
        chart_config['yAxis'] = [{'name': '左轴'}, {'name': '右轴', 'position': 'right'}]
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('pie')
def _ad_pie(spec, c: Chart, con):
    if not c.dims or len(c.metrics) != 1:
        raise ValueError(f'[Runner] pie 需要 dims[0] + 单 metric（chart={c.title}）')
    # 远端一致性：未显式 order_by 时默认按指标降序，保证扇区分布与本地一致
    if not c.order_by:
        try:
            c.order_by = f'-{_metric_alias_of(c.metrics[0])}'
        except (AttributeError, TypeError):
            # Chart 是 dataclass(frozen=False)，可直接赋值；兜底用 dataclasses.replace
            import dataclasses as _dc
            c = _dc.replace(c, order_by=f'-{_metric_alias_of(c.metrics[0])}')
    slot_data, sql = _generic_dim_metric(spec, c, con)
    chart_config = {'chartType': 'pie', 'radius': ['35%', '65%']}
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('scatter')
def _ad_scatter(spec, c: Chart, con):
    """散点：dims[0]→x，metrics[0]→y，dims[1?]→category。"""
    if not c.dims or not c.metrics:
        raise ValueError(f'[Runner] scatter 需要 dims[0]=x, metrics[0]=y（chart={c.title}）')
    d_x = c.dims[0]
    m_y = c.metrics[0]
    d_g = c.dims[1] if len(c.dims) >= 2 else None

    x_sql, _ = _dim_sql(d_x)
    g_sql = None
    if d_g is not None:
        g_sql, _ = _dim_sql(d_g)

    is_agg = bool(re.search(
        r'\b(SUM|AVG|COUNT|MIN|MAX|FIRST|LAST|percentile_approx|median)\s*\(',
        m_y.expr, re.I))

    sql_cols = [f'{x_sql} AS `x`', f'({m_y.expr}) AS `y`']
    if d_g is not None:
        sql_cols.append(f'{g_sql} AS `category`')
    sql = f"SELECT {', '.join(sql_cols)}\nFROM {spec.source.table}"
    # 数据保真：聚合模式下，进 GROUP BY 的维度若为 NULL 会聚成"NULL 桶"，
    # 在 ECharts 散点上表现为 [null, null, 0] 尾节点（视觉异常 + 误导）。
    # 这里把所有 GROUP BY 维度自动追加 IS NOT NULL（与 _build_select_sql_v2 单维路径同语义），
    # 同时尊重 Dim(description='__keep_null__') 逃生口，并与 spec.source.where AND 共存。
    # 行级模式（is_agg=False）不在 SQL 层过滤——dropna(subset=['x','y']) 已在 DataFrame 层兜底。
    extra_clauses: List[str] = []
    if is_agg:
        for d_ in ([d_x] + ([d_g] if d_g is not None else [])):
            cl = _dim_null_filter(d_)
            if cl:
                extra_clauses.append(cl)
    sql += _merge_where(spec.source.where, *extra_clauses)
    if is_agg:
        gb = [x_sql] + ([g_sql] if d_g is not None else [])
        sql += f"\nGROUP BY {', '.join(gb)}"
    # 数据保真兜底（散点抽样失真）：
    #   ① 显式 limit → 按用户值（DSL 已硬约束 limit 必配 order_by）
    #   ② 行级 + 未显式 limit → 强制 ORDER BY y DESC LIMIT 500
    #      原因：行级 scatter 默认扫全表，50w 行送前端必爆；
    #            按 y 排序的 Top500 远比"无序 LIMIT 500"更有统计意义（保留极值）
    #   ③ 聚合（is_agg=True） → 不强加 limit，让 GROUP BY 自然收敛
    if c.order_by:
        # DSL 已校验 known aliases，这里直接套用
        ob_clause = _format_order_by(
            c.order_by,
            known_aliases=['x', 'y'] + (['category'] if d_g is not None else []),
        )
        if ob_clause:
            sql += '\n' + ob_clause
    elif not is_agg and c.limit is None:
        # 未显式 order_by 也未显式 limit → 行级模式自动按 y DESC 取 Top500
        sql += '\nORDER BY `y` DESC NULLS LAST'
    effective_limit = c.limit
    if effective_limit is None and not is_agg:
        effective_limit = 500
        print(f'⚠️ [Runner][软告警] scatter "{c.title}" 行级模式未设 limit，'
              f'已自动 ORDER BY y DESC LIMIT 500（保留极值的代表性样本）。'
              f'大数据量建议改用 CASE WHEN 分桶聚合。')
    if effective_limit:
        sql += f'\nLIMIT {int(effective_limit)}'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    if df.empty:
        slot_data = [['x', 'y'] + (['category'] if d_g is not None else [])]
    else:
        cols = ['x', 'y'] + (['category'] if d_g is not None and 'category' in df.columns else [])
        df = df[[c0 for c0 in cols if c0 in df.columns]].dropna(subset=['x', 'y'])
        slot_data = _B['df_to_slot_data'](df)

    chart_config = {'chartType': 'scatter'}
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('radar')
def _ad_radar(spec, c: Chart, con):
    """雷达：dims[0] 分组 + metrics 中每个 Metric 是一个轴。"""
    if not c.dims or not c.metrics:
        raise ValueError(f'[Runner] radar 需要 dims[0] + 至少 3 个 metrics（chart={c.title}）')
    if len(c.metrics) < 3:
        raise ValueError(f'[Runner] radar 至少 3 个 metrics 才有意义（chart={c.title}）')

    d0 = c.dims[0]
    dim_sql_expr, dim_alias = _dim_sql(d0)

    inner_select = [f'{dim_sql_expr} AS `{dim_alias}`']
    axis_aliases: List[str] = []
    for m in c.metrics:
        axis = m.label or _metric_alias_of(m)
        axis_aliases.append(axis)
        inner_select.append(f'{m.expr} AS `{axis}`')
    _inner_join = _NL_INDENT.join(inner_select)
    inner_sql = f"SELECT\n  {_inner_join}\nFROM {spec.source.table}"
    # 数据保真：消除 NULL 类目（通常是 status/category 列含 NULL 行，雷达图会多出"空类目"轴）
    inner_sql += _merge_where(spec.source.where, _dim_null_filter(d0) or '')
    inner_sql += f'\nGROUP BY {dim_sql_expr}'

    needs_norm = any(m.normalize == 'max-norm' for m in c.metrics)
    if needs_norm:
        outer_cols = [f'`{dim_alias}`']
        for m, axis in zip(c.metrics, axis_aliases):
            if m.normalize == 'max-norm':
                outer_cols.append(
                    f"`{axis}` * 100.0 / NULLIF(MAX(ABS(`{axis}`)) OVER (), 0) AS `{axis}`"
                )
            else:
                outer_cols.append(f'`{axis}`')
        sql = f"SELECT {', '.join(outer_cols)}\nFROM ({inner_sql}) t"
        if c.limit:
            sql += f'\nLIMIT {int(c.limit)}'
    else:
        sql = inner_sql + (f'\nLIMIT {int(c.limit)}' if c.limit else '')

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    if df.empty:
        slot_data = [[dim_alias] + axis_aliases]
    else:
        ordered_cols = [dim_alias] + [a for a in axis_aliases if a in df.columns]
        slot_data = _B['df_to_slot_data'](df[ordered_cols])
    chart_config = {'chartType': 'radar'}
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('funnel')
def _ad_funnel(spec, c: Chart, con):
    """漏斗：每个 metric 是一个阶段。

    远端一致性铁律：
      远端平台直接按 SQL 输出形态喂给前端 renderEcharts(rows)。
      原宽表 SQL `SELECT m1 AS stage_0, m2 AS stage_1, ...` 在远端会被前端
      `funnel` 分支转置为 [['stage_1', v1], ['stage_2', v2]]——
      丢掉 stage_0 那一段，且阶段名变成 stage_X 而非用户配置的 label。

    解决方案：直接生成长表 SQL（`UNION ALL`），列固定为 `[stage_name, value]`，
    与前端 funnel 标准合约 [['阶段','数值'], [label, v], ...] 完全一致，
    保证本地预览 + 远端渲染**同形态同顺序**。

    返回 4 元组 (slot_data, sql, chart_config, sql_columns)：
      - slot_data 与 sql_columns 列名/列数完全相同（均为 ['stage_name','value']）
    """
    if not c.metrics:
        raise ValueError(f'[Runner] funnel 需要 metrics（每项一个阶段）（chart={c.title}）')

    where = f'\nWHERE {spec.source.where}' if spec.source.where else ''
    # 单条 UNION ALL，每行 (stage_idx, stage_name, value) → 外层按 stage_idx 排序后裁剪
    union_parts = []
    labels: List[str] = []
    for i, m in enumerate(c.metrics):
        label = m.label or _metric_alias_of(m)
        labels.append(label)
        # 用 \' 转义防止 label 含单引号
        safe_label = label.replace("'", "''")
        union_parts.append(
            f"  SELECT {i} AS `_idx`, '{safe_label}' AS `stage_name`, "
            f"({m.expr}) AS `value` FROM {spec.source.table}{where}"
        )
    union_sql = '\n  UNION ALL\n'.join(union_parts)
    sql = (
        f"SELECT `stage_name`, `value`\nFROM (\n{union_sql}\n) t\nORDER BY `_idx`"
    )

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    rows: List[List[Any]] = [['stage_name', 'value']]
    if not df.empty and {'stage_name', 'value'}.issubset(set(df.columns)):
        for _, r in df.iterrows():
            rows.append([str(r['stage_name']), _to_native(r['value']) or 0])
    else:
        # SQL 失败兜底：仍按 spec 给出 0 行，保证 slot_data 形态合法
        for label in labels:
            rows.append([label, 0])

    chart_config = {'chartType': 'funnel', 'sort': 'descending', 'gap': 2,
                    'radius': ['10%', '60%']}
    chart_config.update(c.extras or {})
    return rows, sql, chart_config, ['stage_name', 'value']


@_adapter('gauge')
def _ad_gauge(spec, c: Chart, con):
    """仪表盘：metrics[0] 单值。"""
    if not c.metrics:
        raise ValueError(f'[Runner] gauge 需要 metrics[0]（chart={c.title}）')
    m = c.metrics[0]
    sql = f"SELECT '当前' AS `name`, {m.expr} AS `value`\nFROM {spec.source.table}"
    if spec.source.where:
        sql += f'\nWHERE {spec.source.where}'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    val = _to_native(df.iloc[0]['value']) if (not df.empty and 'value' in df.columns) else 0
    target = m.target if m.target is not None else max(float(val or 0) * 1.2, 100)
    rows = [['name', 'value'], ['当前', val]]

    chart_config = {'chartType': 'gauge', 'min': 0, 'max': target}
    if m.format:
        chart_config['format'] = m.format
    if m.suffix:
        chart_config['unit'] = m.suffix
    chart_config.update(c.extras or {})
    return rows, sql, chart_config


@_adapter('heatmap')
def _ad_heatmap(spec, c: Chart, con):
    """热力：dims[0]→x，dims[1]→y，metrics[0]→value。"""
    if len(c.dims) < 2 or not c.metrics:
        raise ValueError(f'[Runner] heatmap 需要 dims[0,1] + metrics[0]（chart={c.title}）')
    d_x, d_y = c.dims[0], c.dims[1]
    m = c.metrics[0]
    x_sql, x_alias = _dim_sql(d_x)
    y_sql, y_alias = _dim_sql(d_y)
    val_alias = _metric_alias_of(m)

    sql = (
        f"SELECT\n  {x_sql} AS `{x_alias}`,\n  {y_sql} AS `{y_alias}`,\n"
        f"  {m.expr} AS `{val_alias}`\nFROM {spec.source.table}"
    )
    # 数据保真：x/y 维度若为 NULL 会聚成 (NULL,NULL) 桶，在 ECharts heatmap 上表现为
    # `[null, null, 0]` 尾节点（视觉异常 + 误导）。这里把进 GROUP BY 的两维自动追加
    # IS NOT NULL，尊重 __keep_null__ 逃生口，与 spec.source.where AND 共存。
    extra_clauses: List[str] = []
    for d_ in (d_x, d_y):
        cl = _dim_null_filter(d_)
        if cl:
            extra_clauses.append(cl)
    sql += _merge_where(spec.source.where, *extra_clauses)
    sql += f'\nGROUP BY {x_sql}, {y_sql}'
    # 远端一致性：显式 ORDER BY 让本地与远端 hash 聚合输出顺序一致，
    #   X 轴/Y 轴 categories 的扫描顺序也稳定。
    #   时间维放后 → 优先按非时间维分组、再按时间维内升序。
    sql += f'\nORDER BY {x_sql}, {y_sql}'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    # 数据保真兜底（heatmap 基数爆炸）：X×Y > 900 时按各自 Top30 交叉截断
    #   设计动机：echarts heatmap 在 30×30 内可读性最佳；超过后单元格像素 < 1 不可见。
    #   截断策略：取 X 维 Top30（按总值）∩ Y 维 Top30 → 留下高频组合，剔除长尾稀疏点。
    if not df.empty and len(df) > 900:
        try:
            top_x = (df.groupby(x_alias)[val_alias].sum()
                       .sort_values(ascending=False).head(30).index.tolist())
            top_y = (df.groupby(y_alias)[val_alias].sum()
                       .sort_values(ascending=False).head(30).index.tolist())
            df_trim = df[df[x_alias].isin(top_x) & df[y_alias].isin(top_y)]
            print(f'⚠️ [Runner][软告警] heatmap "{c.title}" 单元格 {len(df)} > 900，'
                  f'已按 X/Y 维各自 Top30 交叉截断到 {len(df_trim)} 行。'
                  f'建议改用更粗维度（如时间从天→月、地域从城市→州）。')
            df = df_trim
        except Exception:
            # 截断失败不阻断主流程（极端情况下 groupby 类型异常）
            pass
    if df.empty:
        slot_data = [[x_alias, y_alias, val_alias]]
    else:
        slot_data = _B['df_to_slot_data'](df[[x_alias, y_alias, val_alias]])
    chart_config = {'chartType': 'heatmap'}
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('candlestick')
def _ad_candle(spec, c: Chart, con):
    """K 线：dims[0] 时间轴 + 4 个角色 metrics（open/close/low/high）。

    返回 4 元组 (slot_data, sql, chart_config, sql_columns)：
      - slot_data 用前端 ECharts candlestick 需要的短列名 ['date','o','c','l','h']
      - sql_columns 是 SQL 顶层 SELECT 输出列 ['date','open','close','low','high']
      - lock_columns 选 sql_columns，避免 Spark 解析 'o'/'c' 报 UNRESOLVED_COLUMN
    """
    if not c.dims or not c.metrics:
        raise ValueError(f'[Runner] candlestick 需要 dims[0] + 4 个角色 metrics（chart={c.title}）')
    role_map = {m.role: m for m in c.metrics if m.role in ('open', 'close', 'low', 'high')}
    if len(role_map) < 4:
        raise ValueError(
            f'[Runner] candlestick 需要 4 个 Metric，分别 role=open/close/low/high（chart={c.title}）')
    m_o, m_c, m_l, m_h = role_map['open'], role_map['close'], role_map['low'], role_map['high']
    d0 = c.dims[0]
    dim_sql_expr, _ = _dim_sql(d0)
    sql = (
        f"SELECT\n  {dim_sql_expr} AS `date`,\n"
        f"  {m_o.expr} AS `open`,\n  {m_c.expr} AS `close`,\n"
        f"  {m_l.expr} AS `low`,\n  {m_h.expr} AS `high`\nFROM {spec.source.table}"
    )
    # 数据保真：时间维 NULL 会聚成 NULL 桶（K 线在 X 轴出现 null），自动过滤。
    extra_clauses: List[str] = []
    cl = _dim_null_filter(d0)
    if cl:
        extra_clauses.append(cl)
    sql += _merge_where(spec.source.where, *extra_clauses)
    sql += f'\nGROUP BY {dim_sql_expr}\nORDER BY `date`'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    rows: List[List[Any]] = [['date', 'o', 'c', 'l', 'h']]
    if not df.empty:
        for _, r in df.iterrows():
            rows.append([
                r.get('date'),
                _to_native(r.get('open')),
                _to_native(r.get('close')),
                _to_native(r.get('low')),
                _to_native(r.get('high')),
            ])
    chart_config = {'chartType': 'candlestick'}
    chart_config.update(c.extras or {})
    sql_cols = ['date', 'open', 'close', 'low', 'high']
    return rows, sql, chart_config, sql_cols


@_adapter('treemap', 'sunburst')
def _ad_hier(spec, c: Chart, con):
    """层级图（treemap/sunburst）：c.dims 是路径，metrics[0] 是值。"""
    if not c.dims or not c.metrics:
        raise ValueError(f'[Runner] {c.kind} 需要 dims (路径) + metrics[0]（chart={c.title}）')
    import pandas as pd

    path_sqls: List[str] = []
    path_aliases: List[str] = []
    for d in c.dims:
        sql_, alias = _dim_sql(d)
        path_sqls.append(sql_)
        path_aliases.append(alias)
    m = c.metrics[0]

    if len(c.dims) <= 1:
        sql = (
            f"SELECT\n  {path_sqls[0]} AS `name`,\n  {m.expr} AS `value`\n"
            f"FROM {spec.source.table}"
        )
        # 数据保真：treemap/sunburst 单层 NULL 类目会被聚成 "NULL" 框，自动过滤。
        extra_clauses: List[str] = []
        cl = _dim_null_filter(c.dims[0])
        if cl:
            extra_clauses.append(cl)
        sql += _merge_where(spec.source.where, *extra_clauses)
        sql += f"\nGROUP BY {path_sqls[0]}"
        # 远端一致性：treemap/sunburst 单层按 value DESC 排序，让 Top50 截断稳定可复现
        sql += f"\nORDER BY `value` DESC NULLS LAST"

        df = _exec_for_chart(con, sql, spec.source.table, c.title)
        # 数据保真兜底（单层基数爆炸）：> 100 类目时取 Top50（前端可读性 + HTML 体积）
        if not df.empty and len(df) > 100:
            print(f'⚠️ [Runner][软告警] {c.kind} "{c.title}" 单层 {len(df)} 类目 > 100，'
                  f'已自动取 Top50（按 value DESC）。建议改用更粗维度或多层路径。')
            df = df.head(50)
        slot_data: List[List[Any]] = [['name', 'value']]
        if not df.empty:
            for _, r in df.iterrows():
                name = r.get('name')
                if name is None or (isinstance(name, float) and pd.isna(name)):
                    continue
                slot_data.append([str(name), _to_native(r.get('value')) or 0])
    else:
        sql = (
            f"SELECT\n  {path_sqls[-1]} AS `name`,\n  {m.expr} AS `value`,\n"
            f"  {path_sqls[-2]} AS `parent`\nFROM {spec.source.table}"
        )
        # 数据保真：层级树 leaf/parent NULL 会破坏父子链路（出现游离节点），自动过滤。
        extra_clauses: List[str] = []
        for d_ in (c.dims[-1], c.dims[-2]):
            cl = _dim_null_filter(d_)
            if cl:
                extra_clauses.append(cl)
        sql += _merge_where(spec.source.where, *extra_clauses)
        sql += f"\nGROUP BY {path_sqls[-1]}, {path_sqls[-2]}"

        df = _exec_for_chart(con, sql, spec.source.table, c.title)
        slot_data = [['name', 'value', 'parent']]
        if not df.empty:
            leaf_topn = int((c.extras or {}).get('level_limit', 12))
            kept_rows = []
            for parent, grp in df.groupby('parent', dropna=False):
                grp_sorted = grp.sort_values('value', ascending=False)
                head = grp_sorted.head(leaf_topn)
                tail = grp_sorted.iloc[leaf_topn:]
                kept_rows.append(head)
                if len(tail) > 0:
                    others_val = tail['value'].sum()
                    others_row = pd.DataFrame([{
                        'name': 'Others',
                        'value': _to_native(others_val) or 0,
                        'parent': parent,
                    }])
                    kept_rows.append(others_row)
            df2 = pd.concat(kept_rows, ignore_index=True) if kept_rows else df

            for _, r in df2.iterrows():
                name = r.get('name')
                parent = r.get('parent')
                if name is None or (isinstance(name, float) and pd.isna(name)):
                    continue
                slot_data.append([
                    str(name),
                    _to_native(r.get('value')) or 0,
                    '' if (parent is None or (isinstance(parent, float) and pd.isna(parent)))
                    else str(parent),
                ])
            grp = df2.groupby('parent', dropna=False)['value'].sum().reset_index()
            grp.columns = ['name', 'value']
            for _, r in grp.iterrows():
                name = r.get('name')
                if name is None or (isinstance(name, float) and pd.isna(name)):
                    continue
                slot_data.append([str(name), _to_native(r.get('value')) or 0, ''])

    chart_config = {'chartType': c.kind}
    if c.kind == 'sunburst':
        chart_config['radius'] = ['15%', '70%']
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('sankey')
def _ad_sankey(spec, c: Chart, con):
    """桑基：dims[0]=source，dims[1]=target，metrics[0]=value。"""
    if len(c.dims) < 2 or not c.metrics:
        raise ValueError(f'[Runner] sankey 需要 dims[0,1] + metrics[0]（chart={c.title}）')
    d_s, d_t = c.dims[0], c.dims[1]
    m = c.metrics[0]
    src_sql, _ = _dim_sql(d_s)
    tgt_sql, _ = _dim_sql(d_t)

    sql = (
        f"SELECT\n  {src_sql} AS `source`,\n  {tgt_sql} AS `target`,\n"
        f"  {m.expr} AS `value`\nFROM {spec.source.table}"
    )
    # 数据保真：sankey 源/目标 NULL 会出现孤立 "null → x" 节点，破坏流向语义。
    extra_clauses: List[str] = []
    for d_ in (d_s, d_t):
        cl = _dim_null_filter(d_)
        if cl:
            extra_clauses.append(cl)
    sql += _merge_where(spec.source.where, *extra_clauses)
    sql += f'\nGROUP BY {src_sql}, {tgt_sql}'
    if c.order_by:
        ob_clause = _format_order_by(c.order_by, known_aliases=['source', 'target', 'value'])
        if ob_clause:
            sql += '\n' + ob_clause
    elif c.limit:
        sql += "\nORDER BY `value` DESC"
    if c.limit:
        sql += f'\nLIMIT {int(c.limit)}'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    if df.empty:
        slot_data = [['source', 'target', 'value']]
    else:
        slot_data = _B['df_to_slot_data'](df[['source', 'target', 'value']])
    chart_config = {'chartType': 'sankey'}
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('boxplot')
def _ad_box(spec, c: Chart, con):
    """箱线：dims[0]=group，metrics[0]=value（裸列名或表达式）。"""
    if not c.dims or not c.metrics:
        raise ValueError(f'[Runner] boxplot 需要 dims[0]=group + metrics[0]=value（chart={c.title}）')
    d_g = c.dims[0]
    m_v = c.metrics[0]
    grp_sql, _ = _dim_sql(d_g)

    # 数据保真：boxplot 分组维 NULL 会形成 "null" 箱体（X 轴出现空类目），自动过滤；
    # 尊重 __keep_null__ 逃生口，与 spec.source.where AND 共存。
    # 注意：boxplot 的 WHERE 嵌在内层子查询 (FROM (...) t)，这里仕插在同一位置。
    inner_where = _merge_where(spec.source.where, _dim_null_filter(d_g) or '')
    sql = (
        f"SELECT t.`category` AS `category`,\n"
        f"  MIN(t.`v`) AS `min`,\n"
        f"  percentile_approx(t.`v`, 0.25) AS `q1`,\n"
        f"  percentile_approx(t.`v`, 0.5) AS `median`,\n"
        f"  percentile_approx(t.`v`, 0.75) AS `q3`,\n"
        f"  MAX(t.`v`) AS `max`\n"
        f"FROM (SELECT {grp_sql} AS `category`, ({m_v.expr}) AS `v` "
        f"FROM {spec.source.table}{inner_where}) t\n"
        f"GROUP BY t.`category`"
    )

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    rows: List[List[Any]] = [['category', 'min', 'q1', 'median', 'q3', 'max']]
    if not df.empty:
        for _, r in df.iterrows():
            rows.append([
                r.get('category'),
                _to_native(r.get('min')),
                _to_native(r.get('q1')),
                _to_native(r.get('median')),
                _to_native(r.get('q3')),
                _to_native(r.get('max')),
            ])
    chart_config = {'chartType': 'boxplot'}
    chart_config.update(c.extras or {})
    return rows, sql, chart_config


@_adapter('graph')
def _ad_graph(spec, c: Chart, con):
    """关系图：边模式 / 节点模式。"""
    if not c.dims:
        raise ValueError(
            f'[Runner] graph 需要 dims[0]（节点）或 dims[0,1]+metrics[0]（边）（chart={c.title}）')
    has_edge = len(c.dims) >= 2

    if has_edge:
        d_s, d_t = c.dims[0], c.dims[1]
        m = c.metrics[0] if c.metrics else Metric('COUNT(*)')
        src_sql, _ = _dim_sql(d_s)
        tgt_sql, _ = _dim_sql(d_t)
        sql = (
            f"SELECT {src_sql} AS `source`, {tgt_sql} AS `target`, "
            f"{m.expr} AS `value`\nFROM {spec.source.table}"
        )
        # 数据保真：graph 边模式 NULL 节点会形成孤立子图，自动过滤。
        extra_clauses: List[str] = []
        for d_ in (d_s, d_t):
            cl = _dim_null_filter(d_)
            if cl:
                extra_clauses.append(cl)
        sql += _merge_where(spec.source.where, *extra_clauses)
        sql += f"\nGROUP BY {src_sql}, {tgt_sql}"
        # 数据保真兜底（边模式）：DSL 构造期已强制 limit，此处再给 raw_sql 旁路兜底 LIMIT 30
        edge_limit = c.limit if c.limit else 30
        if not c.limit:
            print(f'⚠️ [Runner][软告警] graph "{c.title}" 边模式未设 limit，'
                  f'已自动 ORDER BY value DESC LIMIT 30 取 Top30 边。')
        sql += f"\nORDER BY `value` DESC\nLIMIT {int(edge_limit)}"
    else:
        d0 = c.dims[0]
        topk = int(c.limit or 30)
        # 数据保真软告警（节点模式）：
        # runner 用 LEAD OVER (ORDER BY cnt DESC) 把 Top-K 节点串成链——
        # 生成的边语义是"排名相邻"而非真实业务关联。仅适合"想直观看 Top-K
        # 节点权重"的场景；若用户想看"流向/共现/隶属关系"，应改用边模式
        # （dims=[source, target] + metrics 权重）或 sankey。
        print(f'⚠️ [Runner][软告警] graph "{c.title}" 节点模式（dims=1）：'
              f'生成的边是 LEAD 排名链（第1名→第2名→...），仅反映 Top{topk} 节点权重，'
              f'非真实业务关联。需要"流向/共现/隶属"语义请改用边模式或 sankey。')
        node_sql, _ = _dim_sql(d0)
        # 数据保真：graph 节点模式内层 GROUP BY 会将 NULL 节点聚成一条 source=NULL 记录，
        # 外层 LEAD 后甚至可能进入 Top-K（只过滤了 target IS NOT NULL）。
        # 这里补上内层节点 NULL 过滤，尊重 __keep_null__ 逃生口。
        node_null = _dim_null_filter(d0)
        inner_where = _merge_where(spec.source.where, node_null or '')
        # 保持原有嵌入形状：` WHERE ...` 要同时处理为空串的情况
        where_clause = (' ' + inner_where.lstrip()) if inner_where else ''
        # 三层结构（Spark/DuckDB 双引擎安全 + 数据保真）：
        #   ① 内层 topk_plus：先 GROUP BY+COUNT 物化为别名 `cnt`，ORDER BY `cnt` DESC LIMIT k+1
        #      —— 多取 1 行，确保第 k 名仍能 LEAD 到第 k+1 名（生成第 k 条边的 target/value）。
        #   ② 中层 windowed：在 k+1 行上做 LEAD（O(k)），并打 ROW_NUMBER 用于精准截断。
        #   ③ 外层：用 `rn <= k` 截取真实 Top-K 起点，且过滤 LEAD 末尾的 NULL（target IS NOT NULL）。
        #
        # 设计要点：
        #   - 规避 Spark [UNSUPPORTED_EXPR_FOR_OPERATOR]：所有外层 ORDER BY 都引用别名 `cnt`，无裸聚合。
        #   - 数据保真：与旧版"全表 GROUP BY → Window"产出的 Top-K 边集完全一致（单测通过）。
        #   - 性能：Window 仅扫 k+1 行而非全表分组结果；k 通常 ≤ 30，开销可忽略。
        sql = (
            f"SELECT `source`, `target`, `value` FROM ("
            f"SELECT `source`, "
            f"LEAD(`source`) OVER (ORDER BY `cnt` DESC) AS `target`, "
            f"LEAD(`cnt`) OVER (ORDER BY `cnt` DESC) AS `value`, "
            f"ROW_NUMBER() OVER (ORDER BY `cnt` DESC) AS `rn` "
            f"FROM ("
            f"SELECT {node_sql} AS `source`, COUNT(*) AS `cnt` "
            f"FROM {spec.source.table}{where_clause} "
            f"GROUP BY {node_sql} "
            f"ORDER BY `cnt` DESC "
            f"LIMIT {topk + 1}"
            f") topk_plus"
            f") windowed WHERE `target` IS NOT NULL AND `rn` <= {topk}"
        )

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    rows: List[List[Any]] = [['source', 'target', 'value']]
    if not df.empty:
        for _, r in df.iterrows():
            s = r.get('source')
            t = r.get('target')
            if s is None or t is None:
                continue
            rows.append([str(s), str(t), _to_native(r.get('value')) or 0])
    chart_config = {'chartType': 'graph', 'layout': 'force', 'roam': True}
    chart_config.update(c.extras or {})
    return rows, sql, chart_config


@_adapter('parallel')
def _ad_parallel(spec, c: Chart, con):
    """平行坐标：dims[0..-2] 为坐标轴，dims[-1] 为分类色标。

    数据保真双层防护：
      ① DSL 构造期：dims 必须含聚合表达式 或 显式 limit ≤ 1000（must_aggregate_or_limit）
      ② Runner 执行期：未聚合且无 limit 时强制 LIMIT 500 + 软告警（兜底 raw_sql 旁路）
    """
    if len(c.dims) < 3:
        raise ValueError(
            f'[Runner] parallel 需要 dims 至少 3 个（前 N-1 为轴，最后一个为分类）（chart={c.title}）')
    axis_dims = c.dims[:-1]
    grp_dim = c.dims[-1]
    g_sql, g_alias = _dim_sql(grp_dim)

    is_agg_axis = any(
        re.search(r'\b(SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(', d.expr, re.I)
        for d in axis_dims
    )

    sql_cols: List[str] = []
    out_aliases: List[str] = []
    for d in axis_dims:
        s_, alias = _dim_sql(d)
        sql_cols.append(f'{s_} AS `{alias}`')
        out_aliases.append(alias)
    sql_cols.append(f'{g_sql} AS `{g_alias}`')
    out_aliases.append(g_alias)

    sql = f"SELECT {', '.join(sql_cols)}\nFROM {spec.source.table}"
    # 数据保真：parallel 在聚合分组模式下，分组维 NULL 会形成 "null" 折线，破坏类目辨识度。
    # 行级（is_agg_axis=False）模式不在 SQL 层过滤——前端 ECharts 对单维 NULL 已天然跳过。
    # 注意：聚合表达式（如 COUNT/SUM）不能出现在 WHERE 子句中，只能出现在 HAVING 中。
    # 此处仅对非聚合 dim 做 null 过滤（is_agg_axis=False 时由前端处理，is_agg_axis=True 时过滤分组维）。
    extra_clauses: List[str] = []
    if is_agg_axis:
        # 聚合模式下，只对最后一个分组 dim（grp_dim）做 null 过滤
        cl = _dim_null_filter(grp_dim)
        if cl:
            extra_clauses.append(cl)
    sql += _merge_where(spec.source.where, *extra_clauses)
    if is_agg_axis:
        sql += f'\nGROUP BY {g_sql}'
    # 数据保真兜底：未聚合且无 limit → 强制 LIMIT 500（DSL 构造期已 raise，此处兜 raw_sql 旁路）
    effective_limit = c.limit
    if not is_agg_axis and effective_limit is None:
        effective_limit = 500
        print(f'⚠️ [Runner][软告警] parallel "{c.title}" 未聚合且无 limit，'
              f'已自动 LIMIT 500。建议把前 N-1 轴改为聚合表达式（AVG/SUM）按最后一维分组。')
    if effective_limit:
        sql += f'\nLIMIT {int(effective_limit)}'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)
    if df.empty:
        slot_data = [out_aliases]
    else:
        slot_data = _B['df_to_slot_data'](df[[a for a in out_aliases if a in df.columns]])
    chart_config = {'chartType': 'parallel'}
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


@_adapter('table')
def _ad_table(spec, c: Chart, con):
    """表格：c.dims 是明细列，c.metrics 是可选聚合度量。

    支持三种形态：
      ① 纯明细：dims=裸列(s)，无 metrics → SELECT dims FROM t（默认 LIMIT 50）
      ② dim 含聚合：dims=[dim('SUM(x)'), 'cat'] → 聚合表达式同时充当度量
      ③ 推荐聚合：dims=裸列(s) + metrics=SUM/AVG/COUNT(...)
                  → SELECT dims, metrics FROM t GROUP BY 裸 dim
    SKILL.md 提倡形态 ③（语义最清晰 + 与 ECharts table 显示对齐）。
    """
    if not c.dims:
        raise ValueError(f'[Runner] table 需要 dims（明细列）（chart={c.title}）')
    sql_cols: List[str] = []
    out_aliases: List[str] = []
    # 进 GROUP BY 的列：裸列 + 非聚合 SQL 表达式（如 spark_safe_date_format(...) / CASE WHEN 行级表达式）。
    # 聚合表达式（SUM/AVG/...）不进 GROUP BY。
    # 修复（消除"非聚合 SQL 表达式 dim 不进 GROUP BY 导致 Spark/DuckDB 严格模式报错或返空"的返工）：
    #   旧逻辑只把"裸列名"加进 GROUP BY，spark_safe_date_format/CASE WHEN 等行级表达式 dim
    #   既不在 GROUP BY 也不是聚合 → 与 metrics 中的聚合并存时违反 SQL 严格语义。
    group_by_cols: List[str] = []
    has_agg_dim = False
    for d in c.dims:
        s_, alias = _dim_sql(d)
        sql_cols.append(f'{s_} AS `{alias}`')
        out_aliases.append(alias)
        if re.search(r'\b(SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(', d.expr, re.I):
            has_agg_dim = True
        else:
            group_by_cols.append(s_)

    # metrics 也要进 SELECT —— 这是 SKILL.md 推荐的"聚合 table"形态契约
    has_agg_metric = False
    for m in (c.metrics or []):
        m_alias = _metric_alias_of(m)
        sql_cols.append(f'{m.expr} AS `{m_alias}`')
        out_aliases.append(m_alias)
        if re.search(r'\b(SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(', m.expr, re.I):
            has_agg_metric = True

    has_agg = has_agg_dim or has_agg_metric

    sql = f"SELECT {', '.join(sql_cols)}\nFROM {spec.source.table}"
    # 数据保真：仅当"形态②/③（聚合 + 至少一个进 GROUP BY 的 dim）"时，
    # 把进 GROUP BY 的**裸列** dim 追加 IS NOT NULL，消除 ECharts 表格尾行
    # `[null, null, 0]` 的 NULL 桶失真。
    # 形态①（纯明细，无 GROUP BY）—— 不过滤，保留用户明细中的 NULL 行（信息保真）。
    # 尊重 Dim(description='__keep_null__') 逃生口；与 spec.source.where AND 共存。
    # 注意：非聚合 SQL 表达式 dim（spark_safe_date_format/CASE 等）已进 GROUP BY，
    # 但 NULL 过滤仅限裸列 dim（保持与 _dim_null_filter 既有语义一致，避免 CASE 表达式被强加 IS NOT NULL）。
    extra_clauses: List[str] = []
    if has_agg and group_by_cols:
        for d_ in c.dims:
            if _is_bare_col(d_.expr) and not re.search(
                r'\b(SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(', d_.expr, re.I
            ):
                cl = _dim_null_filter(d_)
                if cl:
                    extra_clauses.append(cl)
    sql += _merge_where(spec.source.where, *extra_clauses)
    # 任意 dim/metric 含聚合 + 至少一个非聚合 dim → 必须 GROUP BY 非聚合 dim
    if has_agg and group_by_cols:
        sql += f"\nGROUP BY {', '.join(group_by_cols)}"
    # 排序：用户显式 order_by 优先；否则若首个 dim 是时间维，默认按时间维 ASC
    # （消除 GROUP BY 下 hash 聚合返回乱序导致 "月度明细" 视觉错位的返工，与 _ad_series 对齐）
    effective_order_by = c.order_by
    if not effective_order_by and c.dims and c.dims[0].is_time:
        _, _t_alias = _dim_sql(c.dims[0])
        effective_order_by = _t_alias
    # 形态①（纯明细，无聚合）兜底默认排序：避免远端 SQL 是 `LIMIT 50` 无序抽稀
    # 导致每次刷新看到不同行、丢失极值与代表性样本的失真。
    # 优先级：首个 metric（若有）DESC → 首个 dim ASC。只在未显式 order_by 时生效，
    # 与 DSL 契约 limit_requires_order_by 精神一致（后者拦"显式 limit 无 order_by"，
    # 此处补"隐式 LIMIT 50 无 order_by"的另一半）。
    if not effective_order_by and not has_agg and c.dims:
        if c.metrics:
            effective_order_by = '-' + _metric_alias_of(c.metrics[0])
        else:
            _, _d0_alias = _dim_sql(c.dims[0])
            effective_order_by = _d0_alias
    if effective_order_by:
        ob_clause = _format_order_by(effective_order_by, known_aliases=out_aliases)
        if ob_clause:
            sql += '\n' + ob_clause
    # 数据保真兜底（避免 50w 行明细把 Dataset 初始快照撑爆 + 远端 UpdateAiKanBan 大字段超限）：
    #   ① 无聚合 dim 且未显式 limit → 强制 LIMIT 50（top50 明细，本地与平台一致）
    #   ② 显式 limit（正整数）→ 按用户值（不覆盖用户意图）
    #   ③ 有聚合 dim 且未显式 limit → 兜底 LIMIT 1000
    #      —— 治 "假聚合 GROUP BY 高基数列"（如按 order_id 分组）导致远端全表下发；
    #      行数仍超 500 时在执行后软截断到 50 行 + 打印告警，引导用更粗维度（年月/品类）
    # 关键不变式：保存到看板平台的 SQL 一定带 LIMIT。
    # 兜底值 1000 与项目既有 _MAX_LIMIT（kanban_dsl.py::parallel）及 pitfalls "显式 limit ≤ 1000 即可"
    # 的团队约定对齐；SKILL.md/example/pitfalls 中 table 用例最大仅 limit=500，1000 兜底零回归。
    TABLE_SQL_FALLBACK_LIMIT = 1000
    effective_limit = c.limit
    if effective_limit is None and not has_agg:
        effective_limit = 50
    # 兜底：仅当用户未提供合法正整数 limit 时才补上；显式 limit 严格保留原值。
    if not effective_limit or int(effective_limit) <= 0:
        effective_limit = TABLE_SQL_FALLBACK_LIMIT
    sql += f'\nLIMIT {int(effective_limit)}'

    df = _exec_for_chart(con, sql, spec.source.table, c.title)

    # 聚合后行数仍超 500：截到 50 + 软告警（保证 Dataset 初始快照不失真：top50 行已能体现分布）
    if has_agg and not c.limit and len(df) > 500:
        print(f'⚠️ [Runner][软告警] table "{c.title}" 聚合后 {len(df)} 行 > 500，'
              f'已自动截到前 50 行。建议改用更粗维度（如年月/品类）聚合，'
              f'或显式设置 limit + order_by。')
        df = df.head(50)
    # 列头优先用 d.label / m.label（与平台 dimensions[].name 对齐），后退到 SQL alias；
    # 列序严格按 c.dims + c.metrics 顺序，杜绝"本地按 SELECT、平台按字典序"的视觉错位。
    n_dims = len(c.dims)
    header = [(c.dims[i].label or out_aliases[i]) for i in range(n_dims)]
    for j, m in enumerate(c.metrics or []):
        idx_in_out = n_dims + j
        header.append(getattr(m, 'label', None) or out_aliases[idx_in_out])
    if df.empty:
        slot_data = [header]
    else:
        ordered_aliases = [a for a in out_aliases if a in df.columns]
        sub = df[ordered_aliases]
        # header 与 ordered_aliases 一一对齐（df 缺列时同步丢弃）
        idx_keep = [out_aliases.index(a) for a in ordered_aliases]
        header = [header[i] for i in idx_keep]
        slot_data = [header] + sub.values.tolist()
    return slot_data, sql, {}


# ============================================================
# 4bis. （已移除 SQL 列序锁）
# ------------------------------------------------------------
# 历史背景：曾用 `SELECT ... FROM (...) AS __slot_locked` 外层包壳，强制 Spark
# 输出列序与本地 DuckDB 一致。但该外层壳显著降低 SQL 可读性，且让用户在平台 UI
# 直接读 SQL 时困惑。决定：去掉外层包壳，直接落原始 SQL。
#
# 列序对齐策略改由 SQL 作者负责：
#   - 普通聚合（GROUP BY 后 SELECT 字面序输出，Spark 与 DuckDB 一致）
#   - 窗口函数 / 同环比 / WITH CTE 场景：编译期已显式按所需列序写 SELECT，
#     Spark Catalyst 在顶层 Project 仍按 SELECT 字面输出（对单层 Project 是稳定的）
# 若后续遇到平台返回列序与 SELECT 不一致，请在对应编译函数（_compile_compare 等）
# 内部调整 SELECT 顺序，而非再次引入外层包壳。
# ============================================================


# ============================================================
# 5. Compare（同环比）编译 —— DuckDB 单引擎
# ============================================================

def _compile_compare(spec: Spec, cp: Compare, con):
    """同环比：双层 WITH + LAG + NULLIF。本地 DuckDB 与远端 Spark 同段 SQL。

    数据保真：自动追加 `<dim> IS NOT NULL` 到内层 WHERE，消除 string 时间列
    解析失败导致的 NULL 期被 LAG 吃进去后产生 -100% 假同比/环比的失真。
    """
    dim_sql_expr, dim_alias = _dim_sql(cp.dim)
    metric_alias = _metric_alias_of(cp.metric)
    period_col = f'`{dim_alias}`'

    # WHERE = spec.where ∧ <time_dim> IS NOT NULL（内层 WITH 缩进 2 空格）
    null_filter = _dim_null_filter(cp.dim)
    where_clause = _merge_where(spec.source.where, null_filter or '')
    # 给内层 WITH 子句加上 2 空格缩进保持代码风格
    where = where_clause.replace('\nWHERE ', '\n  WHERE ') if where_clause else ''
    inner = (
        f"WITH agg AS (\n"
        f"  SELECT {dim_sql_expr} AS {period_col},\n"
        f"         {cp.metric.expr} AS `{metric_alias}`\n"
        f"  FROM {spec.source.table}{where}\n"
        f"  GROUP BY {dim_sql_expr}\n"
        f")\n"
    )

    select_extra: List[str] = []
    cols_out = [dim_alias, metric_alias]
    if 'mom' in cp.kinds:
        select_extra += [
            f"LAG(`{metric_alias}`) OVER (ORDER BY {period_col}) AS `prev_period`",
            f"(`{metric_alias}` - LAG(`{metric_alias}`) OVER (ORDER BY {period_col})) * 100.0\n"
            f"   / NULLIF(LAG(`{metric_alias}`) OVER (ORDER BY {period_col}), 0) AS `mom_rate`"
        ]
        cols_out += ['prev_period', 'mom_rate']
    if 'wow' in cp.kinds:
        select_extra += [
            f"LAG(`{metric_alias}`, 1) OVER (ORDER BY {period_col}) AS `wow_prev`",
            f"(`{metric_alias}` - LAG(`{metric_alias}`, 1) OVER (ORDER BY {period_col})) * 100.0\n"
            f"   / NULLIF(LAG(`{metric_alias}`, 1) OVER (ORDER BY {period_col}), 0) AS `wow_rate`"
        ]
        cols_out += ['wow_prev', 'wow_rate']
    if 'yoy' in cp.kinds:
        offset = {'day': 365, 'week': 52, 'month': 12, 'quarter': 4, 'year': 1}.get(
            cp.dim.granularity, 12)
        select_extra += [
            f"LAG(`{metric_alias}`, {offset}) OVER (ORDER BY {period_col}) AS `last_year`",
            f"(`{metric_alias}` - LAG(`{metric_alias}`, {offset}) OVER (ORDER BY {period_col})) * 100.0\n"
            f"   / NULLIF(LAG(`{metric_alias}`, {offset}) OVER (ORDER BY {period_col}), 0) AS `yoy_rate`"
        ]
        cols_out += ['last_year', 'yoy_rate']

    sql = inner + (
        f"SELECT {period_col}, `{metric_alias}`,\n  "
        + ',\n  '.join(select_extra)
        + f"\nFROM agg\nORDER BY {period_col}"
    )

    df = _exec_for_chart(con, sql, spec.source.table, cp.title)
    if df.empty:
        slot_data = [cols_out]
    else:
        avail = [c0 for c0 in cols_out if c0 in df.columns]
        slot_data = _B['df_to_slot_data'](df[avail])

    # 远端一致性铁律：series 配置长度必须严格等于"数据列数 - 1"。
    #   SQL 列形态：[time, base_metric, prev_period?, mom_rate?, wow_prev?, wow_rate?, last_year?, yoy_rate?]
    #   每个 kind 产出 2 个数据列（prev: 同左轴 / rate: 同右轴），渲染端按 headers[1..]
    #   依次取 series_config[i-1]，缺失则 fallback {} → yAxisIndex 错位 → 颜色与 Y 轴错乱。
    series = [{'type': 'line', 'smooth': True, 'areaStyle': {'opacity': 0.3}}]
    y_axis = [{'name': cp.metric.label or metric_alias}]
    for k in cp.kinds:
        if k == 'mom':
            # prev_period（绝对值，左轴） + mom_rate（百分比，右轴）
            series.append({'type': 'line', 'smooth': True, 'lineStyle': {'type': 'dashed'}})
            series.append({'type': 'line', 'smooth': True, 'yAxisIndex': 1})
            y_axis.append({'name': '环比%', 'position': 'right'})
        elif k == 'yoy':
            series.append({'type': 'line', 'smooth': True, 'lineStyle': {'type': 'dashed'}})
            series.append({'type': 'line', 'smooth': True, 'yAxisIndex': 1})
            y_axis.append({'name': '同比%', 'position': 'right'})
        elif k == 'wow':
            series.append({'type': 'line', 'smooth': True, 'lineStyle': {'type': 'dashed'}})
            series.append({'type': 'line', 'smooth': True, 'yAxisIndex': 1})
            y_axis.append({'name': '周环比%', 'position': 'right'})
    chart_config = {'chartType': 'line', 'series': series, 'yAxis': y_axis}
    return slot_data, sql, chart_config


# ============================================================
# 6. raw_sql 旁路（显式 SQL 逃生口）
# ============================================================

def _compile_raw(spec: Spec, c: Chart, con):
    """raw_sql 模式：按用户 SQL 生成 slot，并尽量用 DuckDB 做本地预览。

    精确边界：
    - lakehouse/Spark raw_sql：本地会经过 Spark→DuckDB 兼容层，预览通常能较好模拟远端；
    - OLAP raw_sql：SQL 必须使用目标数据源原生方言（MySQL/PG/GaussDB/StarRocks/Doris），
      DuckDB 不保证支持这些原生函数（如 GaussDB TO_CHAR、MySQL STR_TO_DATE），
      因此本地预览不是远端成功的充分条件，最终以 BatchQuery/目标数据源执行结果为准。

    chart_config 注入策略（远端一致性铁律）：
    - line/bar：按 slot_columns 长度自动生成 series 配置数组（每多一列 = 多一条 series）
      原因：远端按 chartConfig.series.length 决定渲染几条线，缺省时只画 1 条。
      参考 `_ad_line` / `_ad_bar` 普通适配器的同名做法。
    """
    sql = c.raw_sql.strip().rstrip(';')
    df = _exec_for_chart(con, sql, spec.source.table, c.title)

    if df.empty:
        slot_data = [list(c.slot_columns)]
    else:
        cols = [c0 for c0 in c.slot_columns if c0 in df.columns]
        if not cols:
            cols = list(df.columns)
        slot_data = _B['df_to_slot_data'](df[cols])

    chart_config = {'chartType': c.kind} if c.kind != 'table' else {}
    # 多 series 图表（line/bar）按 slot_columns 长度补 series 数组
    # slot_columns[0] 为维度列，[1:] 全部作为 series（与 _generic_dim_metric 协议一致）
    if c.kind in ('line', 'bar') and c.slot_columns and len(c.slot_columns) >= 2:
        n_series = len(c.slot_columns) - 1
        if c.kind == 'line':
            series_cfg = []
            for i in range(n_series):
                item = {'type': 'line', 'smooth': False}
                if i == 0:
                    item['areaStyle'] = {'opacity': 0.3}
                series_cfg.append(item)
        else:  # bar
            series_cfg = [{'type': 'bar', 'barMaxWidth': 40} for _ in range(n_series)]
        chart_config['series'] = series_cfg
    chart_config.update(c.extras or {})
    return slot_data, sql, chart_config


# ============================================================
# 7. 顶层组装
# ============================================================

def _emoji(c) -> str:
    """从 Chart/Compare 提取 emoji 原生字符（供 DSL widget.emoji 直传）。"""
    return (getattr(c, 'emoji', '') or '')


# ============================================================
# 图表形状偏好表（L3 自动布局核心）
# ------------------------------------------------------------
# pref : 默认 span（spec 未声明 span 时使用）
# max  : 上限 span（spec 即使声明也不允许超过；圆形图永远不能横拉）
# wide : 是否"宽友好"（行末补齐时优先扩张）
# ============================================================
_SHAPE_HINT: Dict[str, Dict[str, Any]] = {
    # 圆形/紧凑型：永远 ≤ 2，禁止横拉
    'pie':         {'pref': 2, 'max': 2, 'wide': False},
    'radar':       {'pref': 2, 'max': 2, 'wide': False},
    'sunburst':    {'pref': 2, 'max': 2, 'wide': False},
    'gauge':       {'pref': 2, 'max': 2, 'wide': False},
    'funnel':      {'pref': 2, 'max': 2, 'wide': False},
    # 方形/中等型：默认 2，可拉到 4（参与行末补齐）
    'scatter':     {'pref': 2, 'max': 4, 'wide': True},
    'boxplot':     {'pref': 2, 'max': 4, 'wide': True},
    'graph':       {'pref': 2, 'max': 4, 'wide': True},
    'treemap':     {'pref': 2, 'max': 4, 'wide': True},
    'bar':         {'pref': 2, 'max': 4, 'wide': True},
    'heatmap':     {'pref': 2, 'max': 4, 'wide': True},
    'sankey':      {'pref': 2, 'max': 4, 'wide': True},
    'parallel':    {'pref': 2, 'max': 4, 'wide': True},
    'candlestick': {'pref': 2, 'max': 4, 'wide': True},
    # 宽幅型：默认占满整行（line/table 视觉上明确需要宽度）
    'line':        {'pref': 4, 'max': 4, 'wide': True},
    'table':       {'pref': 4, 'max': 4, 'wide': True},
}
_DEFAULT_HINT = {'pref': 2, 'max': 4, 'wide': True}


def _hint_of(c: Any) -> Dict[str, Any]:
    """获取卡片的形状偏好。Compare 本质是双折线图，按 line 处理。"""
    if isinstance(c, Compare):
        return _SHAPE_HINT['line']
    if isinstance(c, Chart):
        return _SHAPE_HINT.get(c.kind, _DEFAULT_HINT)
    return _DEFAULT_HINT


def _resolve_span(c: Any, declared: Optional[int], grid_columns: int) -> int:
    """根据 spec 声明 + 形状偏好 + grid 列数，决定单卡最终 span。

    - declared=None：使用 hint['pref']
    - declared 给定：clamp 到 [1, hint['max']]
    - 最后再 clamp 到 [1, grid_columns]
    """
    hint = _hint_of(c)
    if declared is None:
        s = hint['pref']
    else:
        s = max(1, min(int(declared), hint['max']))
    return max(1, min(s, grid_columns))


def _layout_pack(charts_with_span: List[Tuple[Any, int]],
                 grid_columns: int = 4) -> List[Tuple[Any, int]]:
    """智能装箱布局（L3 通用）。

    设计原则（核心铁律：非物理末行右侧绝不留白 + 不删图表 + 不破坏圆形图比例）：
      1. 形状偏好优先：圆形图（pie/radar/sunburst/gauge/funnel）永不横拉
         （由 _resolve_span 在入口 clamp 完成；wide=False 卡片绝不被拉伸）。
      2. table 永远独占整行，整体置末（强制 span = grid_columns）。
      3. 物理末行 = 拼回结果中视觉上的最后一行：
         - 有 table → 物理末行是最后一张 table；rows[-1] 不是物理末行
         - 无 table → rows[-1] 即物理末行
      4. 收敛迭代：循环执行 [反落单交换 → 阶段2上提 → 阶段1 lookahead/拉伸]，
         直到所有"中间行"（rows[:-1]，且当 has_table 时也包含 rows[-1]）填满；
         每轮若无变化则退出，避免死循环。
      5. 物理末行允许少量留白（保护圆形图视觉比例）。

    返回 (chart, final_span) 列表。
    """
    if not charts_with_span:
        return []

    # 入口 clamp：spec 声明 → 受形状偏好限制 → 受 grid 限制
    items = [(c, _resolve_span(c, s, grid_columns)) for c, s in charts_with_span]

    non_tables = [(c, s) for c, s in items
                  if not (isinstance(c, Chart) and c.kind == 'table')]
    tables = [(c, grid_columns) for c, _ in items
              if isinstance(c, Chart) and c.kind == 'table']

    # 装箱（保留声明顺序）
    rows: List[List[Tuple[Any, int]]] = []
    cur_row: List[Tuple[Any, int]] = []
    cur_used = 0
    for c, s in non_tables:
        if cur_used + s > grid_columns:
            rows.append(cur_row)
            cur_row, cur_used = [], 0
        cur_row.append((c, s))
        cur_used += s
    if cur_row:
        rows.append(cur_row)

    # has_table=True 时，rows 整体都不是物理末行，全部参与严格补齐
    has_table = bool(tables)

    def _wide_idx(row: List[Tuple[Any, int]]) -> int:
        """返回行内最后一张宽友好卡的索引；没有则返回 -1。"""
        for i in range(len(row) - 1, -1, -1):
            if _hint_of(row[i][0])['wide']:
                return i
        return -1

    def _row_sum(row):
        return sum(s for _, s in row)

    def _strict_rows():
        """需严格补齐（无留白）的行索引上限。
        - has_table：所有 rows 都需补齐（rows[-1] 后面还有 table 行）
        - 无 table：rows[:-1]（rows[-1] 是物理末行允许留白）
        """
        return len(rows) if has_table else max(len(rows) - 1, 0)

    def _fingerprint():
        """快照所有 (id, span) 用于检测一轮无变化。"""
        return tuple((id(c), s) for row in rows for c, s in row), len(rows)

    # ── 反落单交换（每轮可能触发）────────────────────────────────
    def _try_anti_lonely():
        """末行 gap 且全 wide=False（圆形落单）时，与前一行末尾 wide 卡互换/借调。"""
        if len(rows) < 2:
            return False
        last_row = rows[-1]
        last_used = _row_sum(last_row)
        if last_used >= grid_columns:
            return False
        last_all_narrow = last_row and all(not _hint_of(c)['wide'] for c, _ in last_row)
        if not last_all_narrow:
            return False
        prev = rows[-2]
        wi = -1
        for j in range(len(prev) - 1, -1, -1):
            if _hint_of(prev[j][0])['wide']:
                wi = j
                break
        if wi < 0:
            return False
        wide_c, wide_s = prev[wi]
        narrow_c, narrow_s = last_row[0]
        if wide_s == narrow_s:
            # 等 span 互换：两行 sum 不变
            rows[-2][wi] = (narrow_c, narrow_s)
            rows[-1][0] = (wide_c, wide_s)
            return True
        elif wide_s <= grid_columns - last_used:
            # 把 wide 卡借到末行（前一行变 gap，下一轮阶段 1 收敛）
            rows[-2].pop(wi)
            rows[-1].insert(0, (wide_c, wide_s))
            return True
        return False

    # ── 阶段 2：从最后一行借卡上移到倒数第二行 ──────────────────
    def _try_lift_from_last():
        """当倒数第二行有 gap 时，把最后一行卡上提（保留 has_table 不动末 chart 行）。"""
        if has_table or len(rows) < 2:
            return False
        prev_row = rows[-2]
        last_row = rows[-1]
        gap = grid_columns - _row_sum(prev_row)
        if gap <= 0:
            return False
        changed = False
        # 优先：拉伸 prev 内的 wide 卡
        idx = _wide_idx(prev_row)
        if idx >= 0:
            c0, s0 = prev_row[idx]
            max_allow = _hint_of(c0)['max']
            grow = min(gap, max_allow - s0)
            if grow > 0:
                prev_row[idx] = (c0, s0 + grow)
                gap -= grow
                changed = True
        # 主策略：从 last_row 借卡上提
        while gap > 0 and last_row:
            cand_idx = next(
                (j for j, (_, ss) in enumerate(last_row) if ss <= gap), -1
            )
            if cand_idx < 0:
                break
            cc, ss = last_row.pop(cand_idx)
            prev_row.append((cc, ss))
            gap -= ss
            changed = True
        if not last_row:
            rows.pop()
        return changed

    # ── 阶段 1：中间行 lookahead/拉伸 严格无留白 ─────────────────
    def _try_fill_middle():
        """对所有非物理末行（< _strict_rows()）做：a)拉伸 wide  b)lookahead 借卡  c)兜底拉伸"""
        changed = False
        i = 0
        upto = _strict_rows()
        while i < upto and i < len(rows):
            row = rows[i]
            gap = grid_columns - _row_sum(row)
            if gap <= 0 or not row:
                i += 1
                continue
            # a) 拉伸 wide
            wi = _wide_idx(row)
            if wi >= 0:
                c0, s0 = row[wi]
                grow = min(gap, _hint_of(c0)['max'] - s0)
                if grow > 0:
                    row[wi] = (c0, s0 + grow)
                    gap -= grow
                    changed = True
            # b) lookahead 借卡
            while gap > 0:
                borrowed = False
                for ni in range(i + 1, len(rows)):
                    nrow = rows[ni]
                    ci = next(
                        (j for j, (_, ss) in enumerate(nrow) if ss <= gap), -1
                    )
                    if ci >= 0:
                        cc, ss = nrow.pop(ci)
                        row.append((cc, ss))
                        gap -= ss
                        borrowed = True
                        changed = True
                        break
                if any(not r for r in rows):
                    nonlocal_rows = [r for r in rows if r]
                    rows.clear()
                    rows.extend(nonlocal_rows)
                    upto = _strict_rows()
                if not borrowed:
                    break
            # c) 兜底拉伸（行内任一 wide 卡）
            if gap > 0:
                for j in range(len(row) - 1, -1, -1):
                    cj, sj = row[j]
                    if _hint_of(cj)['wide']:
                        grow = min(gap, _hint_of(cj)['max'] - sj)
                        if grow > 0:
                            row[j] = (cj, sj + grow)
                            gap -= grow
                            changed = True
                        if gap <= 0:
                            break
            i += 1
        return changed

    # ── 收敛主循环：最多 N 轮（防御性上限）─────────────────────
    MAX_ITERS = max(8, len(rows) * 2)
    for _ in range(MAX_ITERS):
        snapshot = _fingerprint()
        # 顺序：反落单 → 阶段 2 → 阶段 1 → 再反落单（处理链式新落单）
        c1 = _try_anti_lonely()
        c2 = _try_lift_from_last()
        c3 = _try_fill_middle()
        c4 = _try_anti_lonely()
        # 检查是否所有"中间行"都已填满
        upto = _strict_rows()
        all_filled = all(_row_sum(rows[i]) == grid_columns for i in range(upto))
        if all_filled:
            break
        # 一轮无任何变化 → 已收敛（剩余 gap 是无救场景，留给物理末行豁免）
        if not (c1 or c2 or c3 or c4) and _fingerprint() == snapshot:
            break

    # 拼回：非 table 行 → table 各自独占一行
    result: List[Tuple[Any, int]] = []
    for row in rows:
        result.extend(row)
    result.extend(tables)
    return result


def build_kanban(spec: Spec, *, dry_run: bool = False) -> Dict[str, Any]:
    """主入口：spec → DSL/Dataset 看板产物 + PREVIEW 同步。

    Args:
        spec: 看板 Spec 实例
        dry_run: True 时只编译不执行 wedatacli query-sql / 不同步 PREVIEW（CI 校验用）

    Returns:
        write_kanban_outputs 的返回值 + preview_sync 信息
    """
    print(f'🚀 [Runner] 启动看板：{spec.title}')

    # ---- B 阶段：取数 ----
    # resolved_resource_id：runner 自动从 query-sql 落盘 quant 解析得到（仅真实 ResourceId / ComputeResource 字段）
    # spec.resource_id 显式指定时优先；否则使用解析结果。JobId/TaskId 不是执行资源，不能回填。
    resolved_resource_id = ''
    csv_path = ''
    if dry_run:
        # dry_run 仍需要一个空 schema DataFrame 给 DuckDB 注册视图做 EXPLAIN 体检
        df = _build_empty_dataframe(spec.source)
    else:
        fetch_sql = _build_fetch_sql(spec.source)
        csv_path, resolved_resource_id = _fetch_table_csv(fetch_sql, src=spec.source)  # wedatacli query-sql 入口，lakehouse + OLAP 同协议
        # 生产路径不再做 pandas 全量装载：DuckDB 的 read_csv 已显式声明列类型 + NULL 集合，
        # parse_time_column / pd.to_numeric 在生产路径上从未被任何下游消费（chart adapter
        # 都基于 _exec_for_chart(con, sql) 走 DuckDB），删除可省一次 ~MB-GB 级 IO。
        df = None

        # ---- B.0 阶段：等齐所有副表 csv 落盘（消除 prefetch 竞态）----
        # 静态扫描 Spec 中 raw_sql 用到的三段式表名，剔除主表后逐张确认 prefetch
        # 缓存中 fresh meta.json 已落盘；超时退化为软告警（保留旧路径行为）。
        # 单表 spec / 无 raw_sql 场景：依赖列表为空，零开销直接返回。
        try:
            _dep_tables = _collect_dependent_tables(spec)
            if _dep_tables:
                # 默认超时与 prefetch 端 FETCH_TOTAL_TIMEOUT（600s/张）对齐：
                #   - prefetch 端：单张表 wedatacli query-sql 容忍 600s
                #   - runner 端：之前 60+30*N 封顶 240s，2 张副表只给 120s，实测必假阴性
                # 新公式：基础 180s（首张表网络抖动 buffer）+ 每张副表 60s（与 prefetch 单表 query-sql
                # 实测 30-60s 上限对齐），封顶 600s（=单张表 FETCH_TOTAL_TIMEOUT）。
                # 由于 prefetch_table.py 已改为全表整体并行 query-sql，
                # 副表实际就绪时间 ≈ max(单表取数)，远低于任何串行路径；
                # 但保留 60s/张是为了给慢副表（亿级行）留兜底，确保看板生成稳定不假阴性。
                # 环境变量 KANBAN_PREFETCH_WAIT_TIMEOUT 显式给值时直接覆盖。
                _env_timeout = os.environ.get('KANBAN_PREFETCH_WAIT_TIMEOUT', '').strip()
                if _env_timeout:
                    try:
                        _wait_timeout = float(_env_timeout)
                    except (TypeError, ValueError):
                        _wait_timeout = 180.0 + 60.0 * len(_dep_tables)
                else:
                    _wait_timeout = min(180.0 + 60.0 * len(_dep_tables), 600.0)
                _missing = _wait_for_companion_csvs(_dep_tables, timeout_s=_wait_timeout)
                if _missing:
                    print(
                        f'⚠️ [副表等待] 超时（{_wait_timeout:.0f}s）仍未就绪：{", ".join(_missing)}；'
                        f'对应 raw_sql / 跨表 KPI 本地体检将为空（不阻断 PREVIEW 同步；可设置 '
                        f'KANBAN_PREFETCH_WAIT_TIMEOUT 放宽，或原样重跑同一条 spec 命令即愈）'
                    )
        except Exception as _ex:
            # 等待逻辑任何异常都不应阻断主流程（保底回到旧软告警路径）
            print(f'⚠️ [副表等待] 等待环节异常（已回退旧软告警路径）：{_ex}')
    effective_resource_id = (spec.resource_id or resolved_resource_id or '').strip()

    # ---- B.1 阶段：开 DuckDB 连接（取代 pandas 切片，本地与远端同语义同 SQL） ----
    # 生产路径优先用 csv（DuckDB read_csv 显式 columns 类型，零第三方依赖）；
    # dry_run 走 df（空 schema 即可，仅做 EXPLAIN 体检）
    con = _open_duck(csv_path if csv_path else df, src=spec.source)
    print(f'🦆 DuckDB 视图已就绪：{_LOCAL_VIEW}')

    # ---- B.1.5 阶段：string 时间列样本嗅探（P1-1 健壮性增强）----
    # 解决 'Jan 2025' / 'Q1 2025' / 中文月份等非标字符串时间格式导致看板"无数据"的根因。
    # 仅在生产路径触发（dry_run csv 为空，嗅探无意义且会误报）；任何异常静默 → 不阻断主流程。
    _time_parse_failures: List[Dict[str, Any]] = []
    if not dry_run and csv_path:
        try:
            _time_parse_failures = _probe_string_time_columns(con, spec) or []
            if _time_parse_failures:
                print('')
                print('⚠️  [TimeProbe] 检测到 string 时间列解析失败率 > 50%（远端 Spark 可能同样空集）：')
                for _tpf in _time_parse_failures:
                    print(f"   - {_tpf['hint']}")
                print('   ↑ 若数据源含真正的 DATE/TIMESTAMP 列，强烈建议改用该 DATE 列；')
                print('     否则需在 spec 中给该列显式包 spark_safe_to_timestamp(col)。')
                print('')
        except Exception as _ex:
            # 嗅探失败完全软兜底（已在函数内部 try-except，外层再兜一次保险）
            print(f'⚠️  [TimeProbe] 嗅探异常（已忽略，主流程继续）：{_ex}')

    # 多表伴随视图（仅当 prefetch 缓存里还有别的表时才生效；单表场景零开销）
    # dry_run 时 csv_path 为空，仍然尝试 attach（让多表 spec 也能 EXPLAIN 校验）
    try:
        attached = _attach_companion_views(con, csv_path or '', spec.source.table)
        if attached:
            print(f'🔗 多表伴随视图已注册（raw_sql 可直接 JOIN）：{", ".join(attached)}')
    except Exception as ex:
        print(f'⚠️ 多表伴随视图注册失败（非致命，仍可走单表）：{ex}')

    # ---- B.2 阶段：基于真实 CSV 的维度画像 + 温和降级（方案 D 体感保障）----
    # CSV 已就位 + DuckDB 视图已注册，扫一遍 NDV/range 仅 0.1-0.5s；
    # 对必然退化的图表（NDV=1 单类目 / scatter 跨度≈0）只做"标题打标 + extras 留痕"，
    # 不改 kind / dims / metrics 契约 —— 保证编译期契约校验和入库协议零破坏。
    # dry_run 模式下视图为空 schema，扫描结果会全为 0，降级自然不触发，安全跳过。
    if not dry_run and getattr(spec, 'charts', None):
        _profile = _profile_csv_columns(con, spec)
        if _profile:
            print(f'🔍 维度画像扫描完成：{len(_profile)} 列（NDV / range）')
            _auto_degrade_charts(spec.charts, _profile)

    # ---- C 阶段：编译 SLOT_DATA + sqlSlots（三端统一入库：DSL + Dataset） ----
    print('🎨 编译 Spec...')
    slot_data: Dict[str, Any] = {}
    sql_slots_list: List[Dict[str, Any]] = []
    # raw_sql 卡片本地体检失败汇总：build 末尾统一红字打印，
    # 让 Agent 在 Step E 概览必抄、不会被前面海量 print 淹没。
    _raw_sql_check_failures: List[Tuple[str, str, str]] = []  # (slot_key, title, err_first_line)

    # DSL emitter 数据收集：每编译一个 widget 就 append 一条元数据。
    # 顺序与 spec.charts 遍历一致，emitter 据此做 30 栅格 layout。
    # 顶部先记录页标题文本 widget（与 DSL Title.Text 视觉对齐）；
    # 副标题（数据源 + 更新时间）在 D 阶段拼好 subtitle 后回填到该记录的 description，
    # emit_dsl 会将其写入 Title.Description.Text。
    _dsl_widget_records: List[Dict[str, Any]] = [
        {
            'widget_id': 'widget-page-title',
            'role': 'page_title',
            'type': 'text',
            'kind': None,
            'span': None,
            'title': spec.title,
            'emoji': '',
            'cfg': None,
            'kpi_config': None,
            'spec_obj': None,
            'kpi_metric': None,
            'description': None,
        },
    ]

    # 目标数据源方言（用于 sqlSlots 表名段数裁剪，与 _build_fetch_sql 对偶）：
    #   - MYSQL/POSTGRESQL/GAUSSDB：入库 SQL 中的三段式 catalog.db.table 会被自动归一为 db.table
    #   - SPARK/StarRocks/Doris：段数上限 3，_project_slot_sql_table_segments 直接返回原值零影响
    # 此处纯读缓存 meta，无副作用；异常保底空串走 lakehouse 语义。
    try:
        _slot_conn_type_for_meta = str(
            (_route_meta_from_src(spec.source) or {}).get('connection_type') or ''
        ).strip()
    except Exception as _route_ex:
        print(f'⚠️ [路由预读] 解析 slot conn_type 异常，按 lakehouse 语义处理：{_route_ex}')
        _slot_conn_type_for_meta = ''

    # KPI
    kpi_data, kpi_config, kpi_sql = _compile_kpi(spec, con)
    if spec.kpis:
        slot_key = 'kpi_overview'
        slot_data[slot_key] = kpi_data
        # 平台 Dataset 入库协议：key/sql/metrics/dimensions/refreshInterval
        # lock_columns：以本地 DuckDB 实际列序为权威源，强制远端 Spark 输出对齐
        sql_slots_list.append(_build_slot_meta(
            slot_key=slot_key,
            sql=kpi_sql,
            slot_kind='kpi',
            metrics=spec.kpis,
            dims=[],
            lock_columns=list(kpi_data[0]) if kpi_data else None,
            source_table=spec.source.table,
            conn_type=_slot_conn_type_for_meta,
        ))
        # 三端统一入库：DSL 侧每个 spec.kpis[i] 对应一个独立 KPI widget（indexCard）。

        # DSL 侧：KPI 段共享 dataset='kpi_overview'，每个 spec.kpis[i] 对应一个独立 KPI widget，
        # 由 emit_dsl 翻译为 indexCard；widget_id 用 kpi_<i> 保证全局唯一。
        for _i, _kpi_metric in enumerate(spec.kpis):
            _dsl_widget_records.append({
                'widget_id': f'kpi_{_i}',
                'role': 'kpi',
                'type': 'kpi',
                'kind': 'kpi',
                'span': None,
                'title': _kpi_metric.label or _kpi_metric.expr,
                'emoji': '',
                'cfg': None,
                'kpi_config': kpi_config,
                'spec_obj': None,
                'kpi_metric': _kpi_metric,
                'dataset_key': 'kpi_overview',
                'description': None,
            })

    # Charts / Compares
    items_with_span = [(c, c.span) for c in spec.charts]
    ordered = _layout_pack(items_with_span, spec.grid_columns)

    def _unpack_compile(ret):
        """兼容适配器返回 3 元组 (sd, sql, cfg) 与 4 元组 (sd, sql, cfg, sql_columns)。

        sql_columns 是 SQL 顶层 SELECT 的实际输出列名（权威源），
        优先用于 lock_columns；缺省时回落到 slot_data[0]（旧契约）。
        """
        if isinstance(ret, tuple) and len(ret) == 4:
            return ret  # (sd, sql, cfg, sql_columns)
        sd_, sql_, cfg_ = ret
        return sd_, sql_, cfg_, None

    for c, final_span in ordered:
        try:
            if isinstance(c, Compare):
                sd, sql, cfg, sql_columns = _unpack_compile(_compile_compare(spec, c, con))
                slot_key = c.slot_key
                data_type = 'echarts'
                title = c.title
                _ = _emoji(c)  # 保留调用以维持 DSL widget 记录顺序不变（无副作用）
            elif isinstance(c, Chart):
                if c.raw_sql:
                    sd, sql, cfg, sql_columns = _unpack_compile(_compile_raw(spec, c, con))
                else:
                    adapter = _ADAPTERS.get(c.kind)
                    if adapter is None:
                        raise ValueError(f'未注册的 kind: {c.kind}')
                    sd, sql, cfg, sql_columns = _unpack_compile(adapter(spec, c, con))
                slot_key = c.slot_key
                data_type = 'table' if c.kind == 'table' else 'echarts'
                title = c.title
                _ = _emoji(c)  # 同上：保留调用以维持一致性
            else:
                raise ValueError(f'未知 spec 项: {type(c).__name__}')

            slot_data[slot_key] = sd
            if sql:
                # 平台入库协议：key/sql/metrics/dimensions/refreshInterval
                if isinstance(c, Compare):
                    slot_metrics = [c.metric]
                    slot_dims = [c.dim]
                    slot_kind = 'line'  # 同环比本质是双折线
                    rfi = c.refresh_interval
                    slot_limit = None
                else:
                    slot_metrics = list(c.metrics or [])
                    slot_dims = list(c.dims or [])
                    slot_kind = c.kind
                    rfi = c.refresh_interval
                    slot_limit = c.limit
                # 编译期 SQL 体检（DuckDB EXPLAIN）：仅在 dry_run=False 时执行
                # 策略：
                #   - 普通 chart（DSL 编译生成的 SQL）：体检失败 → raise，强制阻断，
                #     避免破损 SQL 进入最终看板导致前端「无数据图表」。这是历史上
                #     "无数据图表" 的最隐蔽根因——之前仅 warning 不阻断，破损 SQL
                #     照样打包，运行时才看到空图。
                #   - raw_sql（用户显式声明 escape_hatch=True）：保留逃生口，体检失败仅
                #     警告不阻断，因为 DuckDB 不认识 Spark 独家函数（spark_safe_*、
                #     窗口函数特化语法等），这种情况下信任用户自己已在 Spark 端验证过。
                if not dry_run:
                    ok, err = _validate_sql(con, sql, spec.source.table)
                    if not ok:
                        _is_raw = isinstance(c, Chart) and bool(getattr(c, 'raw_sql', None))
                        _err_first_line = err.splitlines()[0] if err else ''
                        if _is_raw:
                            print(f'⚠️ [SQL 体检失败-raw_sql 逃生] {slot_key} ({title}): {_err_first_line}')
                            _raw_sql_check_failures.append((slot_key, title, _err_first_line))
                        else:
                            # 抛出可读异常，把出错的 SQL 一并打印帮助定位
                            raise ValueError(
                                f'[SQL 体检失败] chart "{title}" (slot_key={slot_key}) 生成的 SQL 在 DuckDB 编译期体检不通过，'
                                f'强制阻断以避免无数据图表进入看板。\n'
                                f'  错误: {_err_first_line}\n'
                                f'  SQL : {sql}\n'
                                f'  建议: 检查 dim/metric 的 expr/alias/order_by 是否引用了不存在的列或别名；'
                                f'若必须使用 Spark 独家函数，请改用 raw_sql(..., escape_hatch=True) 走逃生口。'
                            )
                # lock_columns 取值优先级（方案 A：协议层分离 SQL 列序与前端 headers）：
                #   1) 适配器显式声明的 sql_columns（funnel/candlestick 等需 reshape 的图表）
                #   2) 回落到 slot_data 第 0 行（line/bar/pie 等 SQL 列与 headers 一致的图表）
                # 这样 candlestick 不会再因为 SELECT date,open,close,low,high
                # 但 headers 是 date/o/c/l/h 而被外层 SELECT `o`,`c`,`l`,`h` 包错。
                if sql_columns:
                    lock_cols = list(sql_columns)
                elif sd and isinstance(sd, list) and sd:
                    lock_cols = list(sd[0])
                else:
                    lock_cols = None
                sql_slots_list.append(_build_slot_meta(
                    slot_key=slot_key,
                    sql=sql,
                    slot_kind=slot_kind,
                    metrics=slot_metrics,
                    dims=slot_dims,
                    refresh_interval=rfi,
                    limit=slot_limit,
                    lock_columns=lock_cols,
                    source_table=spec.source.table,
                    is_raw_sql=isinstance(c, Chart) and bool(getattr(c, 'raw_sql', None)),
                    conn_type=_slot_conn_type_for_meta,
                ))

            if data_type == 'kpi':
                continue  # 已处理

            # DSL 侧：chart / compare widget（table 走 data_type='table'，纯 chart 走 'echarts'）
            _kind_for_dsl = 'compare' if isinstance(c, Compare) else c.kind
            _dsl_widget_records.append({
                'widget_id': slot_key,           # slot_key 全局唯一，复用为 WidgetId
                'role': 'chart',
                'type': data_type,               # 'echarts' | 'table'
                'kind': _kind_for_dsl,           # 原 spec.kind（含 'compare'）
                'span': final_span,
                'title': title,
                'emoji': getattr(c, 'emoji', '') or '',
                'cfg': cfg if data_type == 'echarts' else None,
                'kpi_config': None,
                'spec_obj': c,                   # 原 Chart / Compare 对象（emitter 反查 dims/metrics）
                'kpi_metric': None,
                'description': None,
            })

        except Exception as ex:
            print(f'⚠️ 编译失败 [{getattr(c, "title", "?")}]: {ex}')
            raise

    # ---- D 阶段：拼装 subtitle（数据源 + 更新时间；供 DSL page_title.description 使用） ----
    # subtitle 格式跟随 spec.title 语言：含 CJK → "数据源: <fqn> | 更新时间: <ts>"；
    # 纯英文 → "Source: <fqn> | Updated: <ts>"。ts 取本次取数 CSV 的 mtime（数据快照时间），缺失回退 now。
    # 该 subtitle 在 E.1 阶段被 emitter 写入 DSL 的 Title.Description.Text，三端统一读取。
    _ts = datetime.fromtimestamp(os.path.getmtime(csv_path)) if (csv_path and os.path.isfile(csv_path)) else datetime.now()
    _ts_str = _ts.strftime("%Y-%m-%d %H:%M:%S")
    _has_cjk = any('\u4e00' <= ch <= '\u9fff' for ch in (spec.title or ''))
    if _has_cjk:
        subtitle = f'数据源: {spec.source.table} | 更新时间: {_ts_str}'
    else:
        subtitle = f'Source: {spec.source.table} | Updated: {_ts_str}'

    # sqlSlots 方言段数裁剪聚合打印：Step C 结束、E 阶段落盘前统一输出
    _flush_slot_projection_summary()

    if dry_run:
        return {
            'dry_run': True,
            'sql_slots_count': len(sql_slots_list),
        }

    # ---- E 阶段：落盘（自动跑 lint） ----
    print('💾 写入产物（builder lint 兜底）...')
    if effective_resource_id:
        print(f'🔗 ExecuteResourceId={effective_resource_id}')
    else:
        print('⚠️ ExecuteResourceId 未解析到（query-sql quant 未透出真实资源，且未取到默认数据分析资源），入库后该字段为空')

    _output_dir = _B['get_kanban_output_dir']()

    # 🛰️ 附加数据源路由信息到 sqlSlots，供 bi-server 侧执行分派：
    #   - lakehouse（sqlType ∈ {0,1,2}）：走 DlcEngineProxy.directSubmitJobAndResult（原路径零回归）
    #   - OLAP（sqlType == 3）           ：走 SqlQueryServiceAPI SubmitSqlQuery + Poll（新增支持）
    # 路由信息由 prefetch 阶段从 wedatacli search 结果解析得到，落在 route meta，
    # runner 侧 _route_meta_from_src 从 meta 反查，无需 spec 显式声明；缺失时保持 lakehouse 语义。
    try:
        _route_for_slots = _route_meta_from_src(spec.source) or {}
        _slot_conn_type = str(_route_for_slots.get('connection_type') or '').strip()
        _slot_sql_type = int(_route_for_slots.get('sql_type') or 1)
        _slot_data_source_id = str(_route_for_slots.get('data_source_id')
                                   or _route_for_slots.get('connection_id') or '').strip()
        # 全局单源约束由 prefetch 端的跨源闸门保证；此处对每个 slot 一律使用同一路由。
        for _slot in sql_slots_list:
            _slot.setdefault('sqlType', _slot_sql_type)
            if _slot_data_source_id:
                _slot.setdefault('dataSourceId', _slot_data_source_id)
            if _slot_conn_type:
                _slot.setdefault('connectionType', _slot_conn_type)
        if _slot_sql_type == 3:
            print(f'🛰️ 检测到 OLAP 数据源路由（sqlType=3, connectionType={_slot_conn_type}, '
                  f'dataSourceId={_slot_data_source_id or "?"}），已注入到 {len(sql_slots_list)} 个 slot')
    except Exception as _route_ex:
        # 路由注入是增量增强，异常保底走 lakehouse 语义，不阻断构建
        print(f'⚠️ [路由注入] 读取 route meta 异常，保持 lakehouse 语义：{_route_ex}')

    # 🛑 L2 OLAP 硬拦截（G1 修复）：sqlType=3 时禁 Spark 独有函数 / 不支持的表名段数
    #   - 触发条件：本次落盘的所有 slot 里任意一条 sqlType=3
    #   - 拦截项：
    #     ① spark_safe_*    宏族（DuckDB 本地能跑，MySQL/PG/StarRocks/Doris/GaussDB 不认）
    #     ② percentile_approx 函数（Spark/Doris/StarRocks 有，MySQL/PG 无）
    #     ③ 三段式表名 catalog.db.table（MySQL/PG/GaussDB 只支持 db.table）
    #   - 与 L0（SKILL P0-15） / L1（prefetch route_hint）三层防御闭环
    #   - lakehouse 场景 sqlType != 3 完全不触发，零回归
    try:
        _olap_slots = [s for s in sql_slots_list if int(s.get('sqlType') or 1) == 3]
        if _olap_slots:
            import re as _re_olap
            _spark_safe_re = _re_olap.compile(r'\bspark_safe_\w+\s*\(', _re_olap.IGNORECASE)
            _percentile_re = _re_olap.compile(r'\bpercentile_approx\s*\(', _re_olap.IGNORECASE)
            # G3 补齐：strftime 是 DuckDB/SQLite 专用函数，MySQL/PG/GaussDB/StarRocks/Doris
            # 均无此函数；OLAP raw_sql 里出现 strftime(...) 会在远端报 "function does not exist"，
            # 且不属于 spark_safe_* 宏族（不会被上面那条 re 命中），必须单独拦。
            _strftime_re = _re_olap.compile(r'\bstrftime\s*\(', _re_olap.IGNORECASE)
            # 只对 MySQL/PG/GaussDB 拦截三段式；StarRocks/Doris 支持三段式所以放行
            _reject_three_seg = (_slot_conn_type or '').upper() in {'MYSQL', 'POSTGRESQL', 'GAUSSDB'}
            # 裸三段式（catalog.db.table）
            _three_seg_re = _re_olap.compile(r'\b[A-Za-z_][\w]*\.[A-Za-z_][\w]*\.[A-Za-z_][\w]*\b')
            # G3 补齐：quoted 三段式变体，覆盖两种引号形态
            #   反引号：`catalog`.`db`.`table`（DSL 编译期常见）
            #   ANSI 双引号：`"catalog"."db"."table"`（PG/GaussDB 方言归一后可能出现）
            _three_seg_bt_re = _re_olap.compile(
                r'`[A-Za-z_][\w\-]*`\s*\.\s*`[A-Za-z_][\w\-]*`\s*\.\s*`[A-Za-z_][\w\-]*`'
            )
            _three_seg_dq_re = _re_olap.compile(
                r'"[A-Za-z_][\w\-]*"\s*\.\s*"[A-Za-z_][\w\-]*"\s*\.\s*"[A-Za-z_][\w\-]*"'
            )
            _violations = []
            for _slot in _olap_slots:
                _sql_text = _slot.get('sql') or ''
                _key = _slot.get('key') or '?'
                _is_raw = bool(_slot.get('_is_raw_sql'))
                _hits = []
                _m1 = _spark_safe_re.search(_sql_text)
                if _m1:
                    _hits.append(f"spark_safe_* 宏（片段：{_m1.group(0)}...）")
                _m2 = _percentile_re.search(_sql_text)
                if _m2:
                    _hits.append('percentile_approx（Spark 专有函数）')
                _m_st = _strftime_re.search(_sql_text)
                if _m_st:
                    _hits.append('strftime（DuckDB/SQLite 专有；请改用目标方言：'
                                 'MySQL DATE_FORMAT / PG|GaussDB TO_CHAR / '
                                 'StarRocks|Doris date_format）')
                if _reject_three_seg:
                    _m3 = _three_seg_re.search(_sql_text)
                    if _m3:
                        _hits.append(f"三段式表名 `{_m3.group(0)}`（{_slot_conn_type} 只支持两段 db.table）")
                    _m3b = _three_seg_bt_re.search(_sql_text)
                    if _m3b:
                        _hits.append(f"三段式表名 `{_m3b.group(0)}`（{_slot_conn_type} 只支持两段 db.table）")
                    _m3d = _three_seg_dq_re.search(_sql_text)
                    if _m3d:
                        _hits.append(f"三段式表名 {_m3d.group(0)}（{_slot_conn_type} 只支持两段 db.table）")
                if _hits:
                    _violations.append((_key, _is_raw, _hits))
            if _violations:
                _lines = [
                    f'🛑 [OLAP sqlSlots 硬拦截] connectionType={_slot_conn_type}, sqlType=3',
                    '  以下 slot 的 SQL 使用了目标 OLAP 数据源不支持的 Spark 方言，'
                    '若入库到平台会导致周期刷新永久失败（未知函数 / 表名段数不匹配）：',
                ]
                for _k, _raw, _hits in _violations:
                    _tag = 'raw_sql' if _raw else 'DSL 生成'
                    _lines.append(f'    · slot={_k} ({_tag}): ' + '; '.join(_hits))
                _lines.extend([
                    '',
                    '  修法（SKILL.md P0-15）：',
                    '    ① 全部 chart 改走 raw_sql(title=..., sql=..., slot_columns=[...])，',
                    '       SQL 用目标数据源原生方言手写；',
                    f'    ② 时间处理换用 {_slot_conn_type} 原生函数（如 MySQL: STR_TO_DATE / DATE_FORMAT，'
                    'PG: TO_TIMESTAMP / TO_CHAR），禁 spark_safe_*；',
                    '    ③ 分位数用目标方言函数（MySQL: 无原生，用 SUBSTRING_INDEX+GROUP_CONCAT 近似；'
                    'PG: percentile_cont(...) WITHIN GROUP；StarRocks/Doris: percentile 保留）；',
                    ('    ④ 表名去 catalog：写 `db.table`（两段式）'
                     if _reject_three_seg else '    ④ 表名段数按目标方言书写；'),
                ])
                raise ValueError('\n'.join(_lines))
    except ValueError:
        # OLAP 硬拦截触发的 raise 直接向上抛，让用户在 build_kanban 报错里看到修法
        raise
    except Exception as _lint_ex:
        # lint 自身异常不阻断构建（防御性），只软告警
        print(f'⚠️ [OLAP lint] 拦截逻辑执行异常，跳过 OLAP 校验：{_lint_ex}')

    write_result = _B['write_kanban_outputs'](
        sql_slots_list=sql_slots_list,
        slot_data=slot_data,
        workspace_id=spec.workspace_id,
        resource_id=effective_resource_id,
        column_types=getattr(spec, '_column_type_map', None) or None,
        display_name=spec.title,
    )

    # ---- E.1 阶段：DSL 描述层落盘（与 Dataset 同源同步）----
    # 设计目的：为「三端预览 / 面板编辑回显」提供结构化协议层。
    #   - emitter 直接复用编译循环里收集的 _dsl_widget_records（cfg / kpi_config / spec_obj）
    #     + slot_data（每 widget 的二维数组结果） + sql_slots（编译期 SQL），零重复计算；
    #     30 栅格 layout 由 _solve_layout 按 spec.charts 顺序贪心铺放。
    #   - 每个 chart/compare widget 一个独立 dataset（key 复用 widget_id），KPI 段共享
    #     dataset='kpi_overview'，data 字段是 slot_data 序列化后的快照；前端可直接渲染，
    #     也可按业务策略走 sql 实时查询。
    #   - Meta.Status='DRAFT' + KanbanVersion=1 由 emitter 硬置，发布/预览态以服务端返回为准。
    #   - emitter 内 _patch_save_params_with_dsl 会**覆盖** kanban_save_params.json 的
    #     HtmlContent / SqlSlots 字段为 DSL 协议形态：HtmlContent=base64(不含 Datasets 的页面/组件 DSL) 或 gzip+base64，
    #     SqlSlots=base64(Datasets 数组，唯一 Dataset 入库源) 或 gzip+base64；后续 PREVIEW 同步透传到 UpdateAiKanBan，
    #     发布 SaveAiKanBan 只提交 WorkspaceId + AccessKey。
    #   - 覆盖失败时必须阻断 PREVIEW 同步，避免三端统一预览读取到旧 params 内容。
    _preview_result: Dict[str, Any] = {
        'status': 'failed',
        'action': 'preview',
        'access_key': '',
        'display_name': spec.title or '',
        'error': 'PREVIEW 同步未执行',
    }
    try:
        _records_with_subtitle = list(_dsl_widget_records)

        # 将副标题（数据源 + 更新时间）回填到 DSL page-title widget 的 description
        # 使 emit_dsl 能将其写入 Title.Description.Text。
        for _r in _records_with_subtitle:
            if _r.get('role') == 'page_title':
                _r['description'] = subtitle
                break

        # 收集 sql_map / slot_meta_map（key=slot_key=widget_id），供 emitter 生成入库 Dataset。
        # Dataset 是三端统一入库源，必须携带 sqlType/dataSourceId/connectionType 等路由字段。
        _sql_map: Dict[str, str] = {
            _slot.get('key'): _slot.get('sql', '')
            for _slot in sql_slots_list if isinstance(_slot, dict) and _slot.get('key')
        }
        _slot_meta_map: Dict[str, Dict[str, Any]] = {
            _slot.get('key'): dict(_slot)
            for _slot in sql_slots_list if isinstance(_slot, dict) and _slot.get('key')
        }

        from kanban_dsl_emitter import emit_dsl as _emit_dsl
        _save_meta = write_result.get('save_meta') if isinstance(write_result, dict) else None
        _dsl_result = _emit_dsl(spec, _records_with_subtitle, slot_data, _sql_map, _output_dir, _slot_meta_map, _save_meta)
        _save_params_patched = isinstance(_dsl_result, dict) and bool(_dsl_result.get('_SaveParamsPatched'))
        _patch_error = ''
        _dsl_validation_report = {}
        if isinstance(_dsl_result, dict):
            _patch_error = str(_dsl_result.get('_SaveParamsPatchError') or '')
            _report = _dsl_result.get('_DslValidationReport')
            if isinstance(_report, dict):
                _dsl_validation_report = _report
                if isinstance(write_result, dict):
                    write_result['dsl_validation'] = _dsl_validation_report

        if not _save_params_patched:
            _preview_result = {
                'status': 'failed',
                'action': 'preview',
                'access_key': '',
                'display_name': spec.title or '',
                'error': _patch_error or 'DSL 写入最终 kanban_save_params.json 失败，已阻断 PREVIEW 同步',
                'recoverable': bool(_dsl_validation_report.get('recoverable', True)),
                'validation_report_path': _dsl_validation_report.get('reportPath') or '',
            }
            if isinstance(write_result, dict):
                write_result['preview_sync'] = _preview_result
                write_result['status'] = 'needs_dsl_repair'
            print(f"⚠️ 预览态同步已阻断: {_preview_result.get('error', '未知')}")
        else:
            # 每次构建成功后都必须保存/更新后端 PREVIEW，三端预览统一读取入库后的 PREVIEW。
            _preview_sync = _B.get('update_to_kanban_list')
            if callable(_preview_sync):
                _preview_result = _preview_sync(write_result)
                if isinstance(write_result, dict):
                    write_result['preview_sync'] = _preview_result
                if _preview_result.get('status') == 'failed':
                    print(f"❌ 预览态同步失败: {_preview_result.get('error', '未知')}")
            else:
                _preview_result = {
                    'status': 'failed',
                    'action': 'preview',
                    'access_key': '',
                    'display_name': spec.title or '',
                    'error': 'update_to_kanban_list 不可用，PREVIEW 同步未执行',
                }
                if isinstance(write_result, dict):
                    write_result['preview_sync'] = _preview_result
                print(f"❌ 预览态同步失败: {_preview_result.get('error')}")
    except Exception as _ex:
        _preview_result = {
            'status': 'failed',
            'action': 'preview',
            'access_key': '',
            'display_name': spec.title or '',
            'error': f'DSL 描述层生成或预览态同步失败: {_ex}',
        }
        if isinstance(write_result, dict):
            write_result['preview_sync'] = _preview_result
            write_result['status'] = 'preview_failed'
        print(f"❌ 预览态同步失败: {_preview_result.get('error')}")

    # ---- F 阶段：DSL + Dataset 三端统一入库收尾 ----
    # 三端权威源（PREVIEW / Save / Update）需要 preview_sync.status == success 才视为完成。

    if isinstance(_preview_result, dict) and _preview_result.get('status') == 'success':
        print(f'🎉 看板创建完成并已写入 PREVIEW：{spec.title}')
    else:
        if isinstance(write_result, dict):
            write_result['status'] = 'preview_failed'
        print(f"❌ 看板本地产物已生成，但 PREVIEW 入库失败：{(_preview_result or {}).get('error', '未知错误')}")

    # raw_sql 本地体检失败汇总：让 Agent 在 Step E 概览必抄
    if _raw_sql_check_failures:
        print('')
        print('❌ [本轮 raw_sql 卡片本地预览失败清单]（远端可能同样跑不通，请先核对方言/类型）：')
        for _sk, _t, _err in _raw_sql_check_failures:
            print(f'   - {_sk} ({_t}): {_err}')
        print('   ↑ 上述卡片若远端也无数据，请在 spec 中给时间字段显式包 spark_safe_to_timestamp(col)')
        print('')

    # P1-1：string 时间列样本嗅探失败汇总（与 raw_sql 一致的红字提示，让 Agent 在 Step E 必抄）
    if _time_parse_failures:
        print('')
        print('❌ [本轮 string 时间列解析失败清单]（远端 Spark 极可能同样空集 → 看板"无数据"）：')
        for _tpf in _time_parse_failures:
            print(f"   - 列 '{_tpf['col']}'：{_tpf['parsed_ok']}/{_tpf['total']} 行可解析"
                  f"（失败率 {_tpf['parse_fail_ratio']*100:.0f}%），样本 {_tpf['sample_raw']}")
        print('   ↑ 修复路径（按优先级）：')
        print('     ① 若 source.columns 含真正的 DATE/TIMESTAMP 列 → 改 time_col 为该列；')
        print('     ② 否则 spec 中给该列显式包 spark_safe_to_timestamp(col)。')
        print('')

    # 同步以字段形式回写到 build_kanban 返回值，避免上层 Agent 仅依赖 stderr 文本判定。
    # 字段恒存在（空列表 = 全部通过），便于上层稳定 if 判断。
    if isinstance(write_result, dict):
        write_result['raw_sql_preview_failures'] = [
            {'slot_key': _sk, 'title': _t, 'error': _err}
            for _sk, _t, _err in _raw_sql_check_failures
        ]
        # P1-1 健壮性增强：string 时间列样本嗅探结果回写，让 Agent 在 Step E 必抄
        # （上层可基于 time_parse_failures 自动决定是否换 time_col 重跑）
        write_result['time_parse_failures'] = list(_time_parse_failures)

    # ---- F.1 阶段：输出发布确认追问语 ----
    # 设计动机：
    #   - build_kanban 成功后已通过 UpdateAiKanBan 保存/更新后端 PREVIEW。
    #   - runner 禁止直接调 SaveAiKanBan 覆盖发布态；发布必须等待用户明确确认。
    #   - 上层 Agent 根据用户回答路由：发布/上线 → save_to_kanban_list()；保存/更新预览 → update_to_kanban_list()。
    try:
        _preview_status = ''
        _preview_access = ''
        if isinstance(write_result, dict):
            _preview = write_result.get('preview_sync') or {}
            if isinstance(_preview, dict):
                _preview_status = _preview.get('status') or ''
                _preview_access = _preview.get('access_key') or ''
        if _preview_status == 'success' and _preview_access:
            print(f'💡 预览已保存（AccessKey={_preview_access}）。确认后回复"保存/发布/上线"即可发布到「仪表盘 → AI 看板列表」（对话结束）')
        else:
            _preview_error = ''
            if isinstance(write_result, dict):
                _preview = write_result.get('preview_sync') or {}
                if isinstance(_preview, dict):
                    _preview_error = str(_preview.get('error') or '')
            print(f'💡 PREVIEW 未保存成功，暂不能发布；请按错误修复并重跑。{("原因：" + _preview_error) if _preview_error else ""}')
    except Exception:
        # 兜底：不影响主流程
        print('💡 PREVIEW 状态未知，暂不能发布；请检查上方日志并重跑。')

    return write_result


# ============================================================
# 8. 干跑/回退辅助
# ============================================================

def _emoji_str_for(title: str) -> str:
    return ''


def _dry_kpi_config(spec: Spec) -> Dict[str, Any]:
    """KPI dry-run 兑底配置：根据 Spec.kpis 直接构造 items（避免空数据时拿不到 kpi_config）。

    与 _compile_kpi 保持同一别名生成与去重逻辑，确保 items[*].field 在 dry-run 路径
    与正式路径输出一致（前端按 field 查 headers 取值的契约不破）。
    """
    raw_aliases = [_metric_alias_of(k) for k in spec.kpis]
    seen_count: Dict[str, int] = {}
    final_aliases: List[str] = []
    for a in raw_aliases:
        if a not in seen_count:
            seen_count[a] = 1
            final_aliases.append(a)
        else:
            seen_count[a] += 1
            final_aliases.append(f'{a}_{seen_count[a]}')
    return {
        'items': [
            {
                'label': k.label or a,
                'field': a,
                'format': k.format,
                **({'prefix': k.prefix} if k.prefix else {}),
                **({'suffix': k.suffix} if k.suffix else {}),
            }
            for a, k in zip(final_aliases, spec.kpis)
        ]
    }


# ============================================================
# SqlSlot 入库元数据构造（对齐平台样本协议）
# ------------------------------------------------------------
# 入库依据：kpi_overview/monthly_trend/category_pie/... 八个样本 slot
# 输出统一 schema：
#   { key, sql, metrics: [{name,field,formula,description}],
#                 dimensions: [{name,field,granularity,description}],
#                 refreshInterval: int }
# ============================================================

# refreshInterval 推断：slot_kind → 秒
REFRESH_KPI_DEFAULT = 60
REFRESH_GAUGE_DEFAULT = 120
REFRESH_TABLE_DEFAULT = 600
REFRESH_CHART_DEFAULT = 300


def _infer_refresh_interval(slot_kind: str, *,
                            limit: Optional[int] = None) -> int:
    """根据 slot 类型推断 refreshInterval。

    入库样本分级：KPI=60 / Gauge=120 / Top-N 与 Table=600 / 其他 Chart=300。
    """
    if slot_kind == 'kpi':
        return REFRESH_KPI_DEFAULT
    if slot_kind == 'gauge':
        return REFRESH_GAUGE_DEFAULT
    if slot_kind == 'table':
        return REFRESH_TABLE_DEFAULT
    # Top-N（小限额 bar 等）归为 600
    if limit is not None and 0 < int(limit) <= 20 and slot_kind in ('bar',):
        return REFRESH_TABLE_DEFAULT
    return REFRESH_CHART_DEFAULT


def _metric_meta(m: Metric) -> Dict[str, Any]:
    """构造入库协议 metrics[] 元素。"""
    field_name = _metric_alias_of(m)
    name = m.label or field_name
    desc = m.description if m.description is not None else (m.label or '')
    return {
        'name': name,
        'field': field_name,
        'formula': m.expr,
        'description': desc,
    }


def _dim_meta(d: Dim) -> Dict[str, Any]:
    """构造入库协议 dimensions[] 元素；granularity 业务粒度兼容。"""
    # field：优先 alias；后退到 dim_sql_and_pd 派生逻辑的简化版
    if d.alias:
        field_name = d.alias
    elif d.is_time:
        field_name = f'{d.expr.strip()}_{d.granularity}'
    else:
        expr = d.expr.strip()
        # 裸列名取原名，表达式取 _metric_alias 派生
        if _is_bare_col(expr):
            field_name = expr.strip('`').strip('"')
        else:
            field_name = _metric_alias(expr)
    name = d.label or field_name
    # granularity：时间按原值；非时间有显式 granularity 则原值；否则兑底 'category'
    if d.granularity:
        gran = d.granularity
    else:
        gran = 'category'
    desc = d.description if d.description is not None else (d.label or '')
    return {
        'name': name,
        'field': field_name,
        'granularity': gran,
        'description': desc,
    }


# 部分 chart 类型在入库 SQL 中使用语义化列名（与 ECharts/平台协议约定对齐）。
# 此处定义每种 kind 的 [dim_fields, metric_fields] 覆写表，保证 metrics[].field
# / dimensions[].field 与 SQL 列别名严格一致，避免平台按 field 取列时拿不到。
#
# 约定列名说明：
#   gauge       : dims=[]           metrics=['value']         SQL 输出 ['name','value']
#   scatter     : dims=['x'|'x','category']  metrics=['y']    SQL 输出 ['x','y'(,'category')]
#   funnel      : dims=['stage_name']         metrics=['value']  SQL 输出 ['stage_name','value']
#   sankey      : dims=['source','target']    metrics=['value']  SQL 输出 ['source','target','value']
#   candlestick : dims=['date']    metrics=['open','close','low','high']
#                 SQL 输出 ['date','open','close','low','high']
#   boxplot     : dims=['category'] metrics=['min','q1','median','q3','max']
#                 SQL 输出 ['category','min','q1','median','q3','max']
#   graph       : dims=['source','target']    metrics=['value']  SQL 输出（边模式） ['source','target','value']
#   treemap     : dims=['name']    metrics=['value']         单层 SQL 输出 ['name','value']
#   sunburst    : 同 treemap
#
# 覆写规则：只写覆写数量与 SQL 输出严格一致的图表，
# 覆写按顺序对齐用户 metrics/dims 的位置，不足部分保持原 field；
# **多余部分保持原 _metric_meta/_dim_meta 派生的 field**，避免误伤未预期的扩展形态。
_SEMANTIC_FIELD_OVERRIDES: Dict[str, Dict[str, List[str]]] = {
    'gauge':       {'dims': [],                        'metrics': ['value']},
    'scatter':     {'dims': ['x', 'category'],         'metrics': ['y']},
    'funnel':      {'dims': ['stage_name'],            'metrics': ['value']},
    'sankey':      {'dims': ['source', 'target'],      'metrics': ['value']},
    'candlestick': {'dims': ['date'],                  'metrics': ['open', 'close', 'low', 'high']},
    'boxplot':     {'dims': ['category'],              'metrics': ['min', 'q1', 'median', 'q3', 'max']},
    'graph':       {'dims': ['source', 'target'],      'metrics': ['value']},
    'treemap':     {'dims': ['name'],                  'metrics': ['value']},
    'sunburst':    {'dims': ['name'],                  'metrics': ['value']},
}


def _apply_semantic_field_overrides(slot_kind: str,
                                    dims_meta: List[Dict[str, Any]],
                                    metrics_meta: List[Dict[str, Any]]) -> None:
    """按 slot_kind 覆写 dims_meta / metrics_meta 的 field，对齐 SQL 输出列。

    与 _SEMANTIC_FIELD_OVERRIDES 表配套：
      - 表里未列出的 kind → 无操作（line/bar/pie/heatmap/radar/table/parallel/kpi/…）
      - 已列出的 kind → 按位置对齐覆写；覆写位置不足以覆盖用户全部 metrics/dims 时，
        剩余项保持 _metric_meta/_dim_meta 派生 field（防御未预期扩展形态）。
    """
    ov = _SEMANTIC_FIELD_OVERRIDES.get(slot_kind)
    if not ov:
        return
    # dims 覆写
    d_names = ov.get('dims') or []
    for i, name in enumerate(d_names):
        if i >= len(dims_meta):
            break
        item = dims_meta[i]
        if item.get('field') != name:
            item['field'] = name
        # name 若与用户原 label 无关（默认 = field）也随字段名收敛，避免展示 raw expr
        if not item.get('name') or item.get('name') == item.get('description'):
            pass  # 保留用户 label
    # metrics 覆写
    m_names = ov.get('metrics') or []
    for i, name in enumerate(m_names):
        if i >= len(metrics_meta):
            break
        item = metrics_meta[i]
        if item.get('field') != name:
            item['field'] = name


def _build_slot_meta(*, slot_key: str, sql: str, slot_kind: str,
                     metrics: List[Metric], dims: List[Dim],
                     refresh_interval: Optional[int] = None,
                     limit: Optional[int] = None,
                     lock_columns: Optional[List[str]] = None,
                     source_table: Optional[str] = None,
                     is_raw_sql: bool = False,
                     conn_type: str = '') -> Dict[str, Any]:
    """按平台样本协议组装 SqlSlot 入库项。

    Args:
        slot_kind:    用于 refreshInterval 推断。kpi/gauge/table/line/bar/pie/...
        metrics:      原始 Metric 列表（空列表 → metrics: []）
        dims:         原始 Dim 列表（空列表 → dimensions: []）
        refresh_interval: 显式覆盖推断值
        lock_columns: 兼容字段，已不再用于包壳；保留以兼容上游调用方签名。
                      列序对齐由各 _compile_xxx 函数在编译期按 SELECT 字面序保证。
        source_table: 可选；提供后将对入库 sql 做"本地占位名 → 真实表名"反向归一化
                      （_to_remote_sql），兜底 spec/raw_sql 误用 _kb_src / main_data 的笔误。
                      所有 KPI/chart/compare 路径都汇集到本函数，一处生效全员覆盖。
        conn_type:    可选；目标数据源 connection_type（SPARK/MYSQL/POSTGRESQL/GAUSSDB/…）。
                      非空时会在 _to_remote_sql 之后再做一次"方言段数裁剪"：
                        · MYSQL/POSTGRESQL/GAUSSDB 只支持两段 db.table，会把 sql 中出现的
                          三段式 catalog.db.table 归一为两段 db.table（含反引号变体）。
                        · 与 _build_fetch_sql 侧的取数 SQL 段数裁剪对偶（取数已裁、入库同裁）；
                          与 L2 OLAP 硬拦截对偶（拦截规则的物理修法直接一处闭环）。
                      lakehouse（SPARK/StarRocks/Doris）段数上限 3，函数返回原值零影响。
    """
    # 入库前反向归一化：sqlSlots 是单一出口，统一在此做兜底
    if source_table:
        sql = _to_remote_sql(sql, source_table, conn_type)
        # OLAP 方言段数裁剪：让 KPI / DSL chart / raw_sql 三条通道都在入库出口收敛
        if conn_type:
            sql = _project_slot_sql_table_segments(sql, source_table, conn_type)
    # 方言引号归一（G2）：反引号方言（Spark/MySQL/StarRocks/Doris）零回归；
    # ANSI 双引号方言（PG/GaussDB）把 DSL 编译期产生的所有反引号列/别名/表名
    # 翻译为 "..."。source_table 缺失场景也执行（此处仅做纯词法翻译，与占位名替换正交）。
    if conn_type:
        sql = _normalize_slot_sql_for_dialect(sql, conn_type)
    rfi = refresh_interval if refresh_interval is not None else _infer_refresh_interval(
        slot_kind, limit=limit)
    metrics_meta = [_metric_meta(m) for m in (metrics or [])]
    dims_meta = [_dim_meta(d) for d in (dims or [])]
    # 语义化列名覆写（G3）：让 gauge/scatter/funnel/sankey/candlestick/boxplot/graph/
    # treemap/sunburst 的 metrics[].field / dimensions[].field 与 SQL 输出列严格对齐，
    # 避免平台按 field 取列时拿不到（历史 gauge.metrics[0].field=count 但 SQL 列名 value）。
    # 表未列出的 kind 无操作，line/bar/pie/heatmap/radar/table/parallel/kpi 零回归。
    _apply_semantic_field_overrides(slot_kind, dims_meta, metrics_meta)
    # raw_sql 兜底：metrics/dims 都为空且 lock_columns 已知时，
    #   按 lock_columns 派生最小 dimensions/metrics 元数据，避免远端列推断与本地不一致。
    #   约定：lock_columns[0] 做维度（时间/分类），其余列均按 metric 处理。
    if not metrics_meta and not dims_meta and lock_columns:
        cols = [str(c) for c in lock_columns if c]
        if cols:
            head = cols[0]
            # 维度名/granularity 兜底：含 month/day/date/time 关键字 → 按粒度区分；否则 category
            head_l = head.lower()
            if 'month' in head_l:
                gran = 'month'
            elif any(k in head_l for k in ('day', 'date')):
                gran = 'day'
            elif any(k in head_l for k in ('week',)):
                gran = 'week'
            elif any(k in head_l for k in ('hour',)):
                gran = 'hour'
            elif any(k in head_l for k in ('time', 'timestamp')):
                gran = 'day'
            else:
                gran = 'category'
            dims_meta = [{
                'name': head, 'field': head,
                'granularity': gran, 'description': head,
            }]
            metrics_meta = [{
                'name': c, 'field': c, 'formula': c, 'description': c,
            } for c in cols[1:]]
    return {
        'key': slot_key,
        'sql': sql,
        'metrics': metrics_meta,
        'dimensions': dims_meta,
        'refreshInterval': int(rfi),
        # 内部字段：标记本 slot 来源是否为 raw_sql 字面量（escape_hatch=True）。
        # builder lint 在判断"列类型物理安全豁免"时据此跳过——raw_sql 不会被
        # DSL/runner 自动包 spark_safe_to_timestamp，column_types 豁免对其不成立。
        # 入库前由 write_kanban_outputs 剥离，不会写到平台 sqlSlots。
        '_is_raw_sql': bool(is_raw_sql),
    }


def _build_empty_dataframe(src: Source):
    """dry_run 用：构造带完整 schema 的空 DataFrame，使 adapter 能跑通。"""
    import pandas as pd
    cols = src.column_names()
    df = pd.DataFrame({c: pd.Series(dtype='object') for c in cols})
    # 给数值列正确 dtype
    for c in src.columns:
        if isinstance(c, dict):
            t = (c.get('type') or '').lower()
            name = c.get('name')
            if name and name in df.columns:
                if t in ('double', 'float', 'decimal'):
                    df[name] = df[name].astype('float64')
                elif t in ('integer', 'int', 'bigint'):
                    df[name] = df[name].astype('Int64')
    return df


__all__ = ['build_kanban']
