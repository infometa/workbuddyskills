#!/usr/bin/env python3
"""
_plan_utils.py - plan-tracker 共享工具

封装跨脚本复用的逻辑：
1) resolve_plan_dates(plan)        计划起止日期解析（兼容任意 plan_id 命名）
2) check_plan_length(plan)         180 天上限校验（软警告 + 硬截断标记）
3) load_user_config()              统一加载 user-config.json
4) is_quiet_hours(cfg, now=None)   判断当前时间是否在免打扰时段
5) silence_if_quiet(text, cfg)     若处于免打扰时段，去除 emoji + 截断为简讯
"""

import json
import os
import re
import sys
from datetime import datetime, date, time, timedelta


def _resolve_data_dir() -> str:
    """数据目录解析（plan-tracker 自用数据目录）。
    优先级：GOAL_TRACKER_DATA_DIR env > <cwd>/.plan-tracker/plans/
    """
    env = os.environ.get("GOAL_TRACKER_DATA_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.abspath(os.path.join(os.getcwd(), ".plan-tracker", "plans"))


def _resolve_user_config_path() -> str:
    """用户配置路径。
    优先级：GOAL_TRACKER_USER_CONFIG env > <cwd>/.plan-tracker/user-config.json
    """
    env = os.environ.get("GOAL_TRACKER_USER_CONFIG")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.abspath(os.path.join(os.getcwd(), ".plan-tracker", "user-config.json"))


DATA_DIR = _resolve_data_dir()
USER_CONFIG_PATH = _resolve_user_config_path()

# 单计划最长 180 天（与 SKILL.md 边界声明一致）
MAX_PLAN_DAYS = 180

# 断签提醒默认阈值：连续 N 天未打卡 → 触发温和提醒
# 可通过 user-config.json.revive_threshold_days 覆盖（取值 1~7，超出范围回退默认）
DEFAULT_REVIVE_THRESHOLD_DAYS = 2

# bottleneck 阈值：某 task 在过去 N 个计划日中 miss 次数 ≥ M 视为瓶颈
DEFAULT_BOTTLENECK_MISS_LOOKBACK_DAYS = 14
DEFAULT_BOTTLENECK_MIN_MISS_COUNT = 3

# emoji 粗匹配（用于免打扰降级），覆盖常见 BMP/SMP 区段
_EMOJI_RE = re.compile(
    "["  # 颜文字 / 符号 / 杂项
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F000-\U0001F02F"
    "\U0001F900-\U0001F9FF"
    "\u2700-\u27bf"
    "]+",
    flags=re.UNICODE,
)


# ---------- 日期解析 ----------

def resolve_start_date(plan: dict) -> date:
    """解析计划起始日期，按优先级兜底，绝不崩溃。

    1) daily_tasks[0].date          —— 最权威
    2) meta.start_date              —— 显式字段
    3) plan.id 中匹配 8 位 YYYYMMDD —— 兼容老命名
    4) date.today()                 —— 兜底
    """
    daily = plan.get("daily_tasks") or []
    if daily and isinstance(daily[0], dict):
        d = daily[0].get("date")
        if d:
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

    meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
    s = meta.get("start_date")
    if s:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass

    pid = plan.get("id", "") or ""
    m = re.search(r"(\d{8})", pid)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d").date()
        except ValueError:
            pass

    return date.today()


def resolve_end_date(plan: dict, fallback: date = None) -> date:
    """解析计划截止日期，优先 meta.deadline，再回退 daily_tasks[-1].date。"""
    meta = plan.get("meta") if isinstance(plan.get("meta"), dict) else {}
    deadline = meta.get("deadline")
    if deadline:
        try:
            return datetime.strptime(deadline, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass

    daily = plan.get("daily_tasks") or []
    if daily and isinstance(daily[-1], dict):
        d = daily[-1].get("date")
        if d:
            try:
                return datetime.strptime(d, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

    return fallback or date.today()


# ---------- 180 天上限 ----------

def check_plan_length(plan: dict, max_days: int = MAX_PLAN_DAYS, emit: bool = True) -> dict:
    """检查计划长度。

    返回 {"days": int, "over_limit": bool, "max_days": int}。
    若超限且 emit=True，向 stderr 输出软警告（不阻塞主流程）。
    上层可据此决定是否截断 daily_tasks（plan-tracker 默认仅警告，
    硬截断由 plan-tracker 在生成阶段拦截，避免破坏已存盘数据）。
    """
    start = resolve_start_date(plan)
    end = resolve_end_date(plan, fallback=start)
    days = (end - start).days + 1

    result = {"days": days, "over_limit": days > max_days, "max_days": max_days}

    if result["over_limit"] and emit:
        print(
            f"⚠️ 计划「{(plan.get('meta') or {}).get('title', plan.get('id', ''))}」"
            f"跨度 {days} 天，超过单计划 {max_days} 天上限。\n"
            f"   建议拆分为多阶段（可新建一个 plan-tracker 计划）。",
            file=sys.stderr,
        )

    return result


# ---------- 用户配置 / 免打扰 ----------

def load_user_config() -> dict:
    """加载 user-config.json，缺失时返回默认值。"""
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "persona": "gentle-senior",
        "active_plan_id": None,
        "checkin_channel": "daily",
        "reminder_time": "09:00",
        "do_not_disturb": None,  # 默认未启用
    }


def _parse_hhmm(s: str):
    """解析 HH:MM 字符串为 datetime.time，失败返回 None。"""
    if not s or not isinstance(s, str):
        return None
    try:
        h, m = s.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        return None


def is_quiet_hours(cfg: dict = None, now: datetime = None) -> bool:
    """判断 now 是否落在免打扰时段。

    支持配置：
      cfg["do_not_disturb"] = {"start": "22:00", "end": "08:00"}    # 跨午夜
      cfg["do_not_disturb"] = {"start": "12:00", "end": "14:00"}    # 同日

    缺失或格式非法 → 返回 False（不打扰逻辑不生效）。
    """
    if cfg is None:
        cfg = load_user_config()
    dnd = cfg.get("do_not_disturb")
    if not dnd or not isinstance(dnd, dict):
        return False

    start_t = _parse_hhmm(dnd.get("start"))
    end_t = _parse_hhmm(dnd.get("end"))
    if start_t is None or end_t is None:
        return False

    if now is None:
        now = datetime.now()
    cur = now.time()

    if start_t <= end_t:
        # 同一天的窗口，例如 12:00 ~ 14:00
        return start_t <= cur < end_t
    # 跨午夜窗口，例如 22:00 ~ 08:00
    return cur >= start_t or cur < end_t


def silence_if_quiet(text: str, cfg: dict = None, now: datetime = None) -> str:
    """若当前在免打扰时段，对输出做"轻量降级"：去 emoji + 单行简讯。
    否则原样返回。
    """
    if not is_quiet_hours(cfg, now):
        return text
    stripped = _EMOJI_RE.sub("", text or "")
    # 仅保留首个非空行，避免长篇通知
    for line in stripped.splitlines():
        line = line.strip()
        if line:
            return f"[quiet] {line}"
    return "[quiet]"


# ---------- 断签阈值 / bottleneck 配置 ----------

def get_revive_threshold(cfg: dict = None) -> int:
    """从 user-config.json 读取断签提醒阈值（天数）。

    取值范围 [1, 7]；缺失/非法 → DEFAULT_REVIVE_THRESHOLD_DAYS=2。
    与 SKILL.md "连续 2 天未打卡触发温和提醒" 需求对齐。
    """
    if cfg is None:
        cfg = load_user_config()
    raw = cfg.get("revive_threshold_days", DEFAULT_REVIVE_THRESHOLD_DAYS)
    try:
        v = int(raw)
        if 1 <= v <= 7:
            return v
    except (ValueError, TypeError):
        pass
    return DEFAULT_REVIVE_THRESHOLD_DAYS


# ---------- bottleneck 计算 ----------

def compute_bottleneck_tasks(
    plan: dict,
    checkins: dict,
    today: date = None,
    lookback_days: int = DEFAULT_BOTTLENECK_MISS_LOOKBACK_DAYS,
    min_miss: int = DEFAULT_BOTTLENECK_MIN_MISS_COUNT,
) -> list:
    """识别瓶颈任务：在过去 lookback_days 内 miss 次数 ≥ min_miss 的 task。

    "miss" 定义：plan.daily_tasks 中 date < today 且 checkable=True，
    但其 task_id 从未出现在 checkin-log 的 task_ids 中。

    返回结构：
        [
          {
            "task_id": "t-001",
            "title": "听力剑 14 Test 1",
            "category": "listening",
            "miss_count": 4,
            "last_missed": "2026-05-07"
          },
          ...
        ]
    按 miss_count 倒序，最多 5 条（避免周报塞爆）。
    """
    today = today or date.today()
    cutoff = today - timedelta(days=lookback_days)

    # 收集已打卡 task_ids
    done_ids = set()
    for c in checkins.get("checkins", []):
        for tid in c.get("task_ids", []):
            done_ids.add(tid)

    # 遍历 plan，收集 miss 信息
    miss_map = {}  # task_id -> {title, category, miss_count, last_missed}
    for day in plan.get("daily_tasks", []):
        try:
            d = datetime.strptime(day["date"], "%Y-%m-%d").date()
        except (ValueError, KeyError, TypeError):
            continue
        if d > today or d < cutoff:
            continue
        for t in day.get("tasks", []):
            tid = t.get("id")
            if not tid or not t.get("checkable", True):
                continue
            if tid in done_ids:
                continue
            entry = miss_map.setdefault(
                tid,
                {
                    "task_id": tid,
                    "title": t.get("title", ""),
                    "category": t.get("category", "其他"),
                    "miss_count": 0,
                    "last_missed": None,
                },
            )
            entry["miss_count"] += 1
            d_str = d.isoformat()
            if entry["last_missed"] is None or d_str > entry["last_missed"]:
                entry["last_missed"] = d_str

    bottlenecks = [e for e in miss_map.values() if e["miss_count"] >= min_miss]
    bottlenecks.sort(key=lambda e: (-e["miss_count"], e["last_missed"] or ""))
    return bottlenecks[:5]


def persist_bottleneck_to_streak(plan_id: str, bottlenecks: list) -> None:
    """把 bottleneck_tasks 写回 streak.json，供下游 agent 直接读取。"""
    streak_path = os.path.join(DATA_DIR, plan_id, "streak.json")
    if os.path.exists(streak_path):
        try:
            with open(streak_path, "r", encoding="utf-8") as f:
                streak = json.load(f)
        except (json.JSONDecodeError, OSError):
            streak = {}
    else:
        streak = {"plan_id": plan_id}

    streak["bottleneck_tasks"] = bottlenecks
    streak["bottleneck_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    os.makedirs(os.path.dirname(streak_path), exist_ok=True)
    with open(streak_path, "w", encoding="utf-8") as f:
        json.dump(streak, f, ensure_ascii=False, indent=2)


# ---------- dashboard 自动重渲染 ----------

def regenerate_dashboard(plan_id: str = None, theme: str = None, verbose: bool = True) -> bool:
    """重渲染 dashboard.html。

    设计契约：
      - 静默失败：任何异常都不抛出，主流程绝不中断
      - 优先 import 直接调用（0 启动开销）；失败时降级 subprocess
      - 成功 stderr 一行 `↻ dashboard 已更新`（让用户感知；走 stderr 避免污染 stdout 被自动化解析）
      - 失败 stderr 一行 `[warn] dashboard 重渲染失败: <type>: <msg>`，不影响 exit code

    参数：
      plan_id：指定计划 id，None 则用最近 plan
      theme：主题（dark/light），None 则用环境变量或默认
      verbose：是否输出 ↻ 提示（True 默认；快速批量调用可关）

    返回：
      True 表示成功，False 表示失败（已静默捕获）。调用方一般不需要看返回值。
    """
    try:
        # 第 1 优先级：import 直接调用同进程函数
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            import importlib
            dashboard_mod = importlib.import_module("dashboard")
            # 重新加载以拿到最新代码（用户在调试时可能改了 dashboard.py）
            dashboard_mod = importlib.reload(dashboard_mod)
            chosen_theme = theme or os.environ.get("PLAN_TRACKER_THEME", "dark")
            dashboard_mod.render_dashboard(plan_id=plan_id, theme=chosen_theme)
            if verbose:
                print("↻ dashboard 已更新", file=sys.stderr)
            return True
        except Exception as e_import:  # noqa: BLE001
            # 第 2 优先级：subprocess 降级
            import subprocess
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dash_py = os.path.join(script_dir, "dashboard.py")
            if not os.path.exists(dash_py):
                if verbose:
                    print(f"[warn] dashboard 重渲染失败: dashboard.py 不存在", file=sys.stderr)
                return False
            cmd = [sys.executable, dash_py]
            if plan_id:
                cmd.extend(["--plan", plan_id])
            if theme:
                cmd.extend(["--theme", theme])
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=8, check=False)
                if proc.returncode == 0:
                    if verbose:
                        print("↻ dashboard 已更新", file=sys.stderr)
                    return True
                if verbose:
                    err_msg = (proc.stderr or b"").decode("utf-8", errors="replace").strip().splitlines()[-1:]
                    err_tail = err_msg[0] if err_msg else f"exit={proc.returncode}"
                    print(f"[warn] dashboard 重渲染失败 (subprocess): {err_tail}", file=sys.stderr)
                    print(f"[warn] (import 失败原因: {type(e_import).__name__}: {e_import})", file=sys.stderr)
                return False
            except Exception as e_sub:  # noqa: BLE001
                if verbose:
                    print(f"[warn] dashboard 重渲染失败: {type(e_sub).__name__}: {e_sub}", file=sys.stderr)
                return False
    except Exception as e:  # noqa: BLE001
        # 终极兜底：绝不让此函数抛异常
        try:
            if verbose:
                print(f"[warn] dashboard 重渲染失败: {type(e).__name__}: {e}", file=sys.stderr)
        except Exception:  # noqa: BLE001
            pass
        return False
