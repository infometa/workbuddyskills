#!/usr/bin/env python3
"""
Linux 多主机 ZIP 包预分析器

接受 .zip 文件作为输入，自动完成：
  1. 解压 zip 到 $HOME/ninetail/tmp/intrusion_analysis/{UUID}/
  2. 在解压目录内查找所有 .tar/.tar.gz/.tgz 文件
  3. 每个 tar 解压到独立子目录（以 tar 文件名命名），避免 var/log 路径冲突
  4. 在每个解压子目录中查找 var/log/ 结构
  5. 对每个找到的 var/log/ 调用 linux_log_folder 分析器
  6. 将所有主机的预分析结果拼接输出（含主机分隔标识）

解压目录不做垃圾回收，保留供 AI 精准回查。

数据流:
  xxx.zip
    → 解压到 $HOME/ninetail/tmp/intrusion_analysis/{UUID}/
        ├── {tar_stem_1}/      ← 如 172_16_0_4/
        │   └── var/log/...
        └── {tar_stem_2}/      ← 如 172_16_0_8/
            └── var/log/...
    → 对每个 var/log/ 调用 linux_log_folder
    → 拼接多主机预分析结果 → stdout

用法（通过统一入口）:
  python3 scripts/analysis/preanalyze.py /path/to/archive.zip

用法（直接调用）:
  python3 scripts/analysis/linux_zip/preanalyze_linux_zip.py /path/to/archive.zip
"""

import argparse
import os
import sys
import tarfile
import uuid
import zipfile
from pathlib import Path

# 支持直接调用：确保 _common 和 linux_log_folder 包可导入
# ⚠️ 注意：绝对不要把 _LINUX_DIR / _LINUX_CHECK_DIR / _WINDOWS_DIR 等
#    含有同名 _preanalyze 子包的目录加进 sys.path——
#    多个平台的 _preanalyze 同名会污染 Python 模块缓存，
#    导致后续被路由到的平台预分析器 import 失败。
#    本平台仅需要在运行时调用 linux_log_folder，因此只加 _LOG_FOLDER_DIR。
_THIS_DIR = Path(__file__).resolve().parent          # .../scripts/analysis/linux_zip
_ANALYSIS_DIR = _THIS_DIR.parent                     # .../scripts/analysis
_LOG_FOLDER_DIR = _ANALYSIS_DIR / "linux_log_folder"

for p in [str(_THIS_DIR), str(_ANALYSIS_DIR), str(_LOG_FOLDER_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# 日志辅助（仅 --debug 模式输出 INFO，否则静默）
# ---------------------------------------------------------------------------

def _info(msg: str) -> None:
    """输出 INFO 日志到 stderr，仅当 PREANALYZE_DEBUG=1 时生效。"""
    if os.environ.get("PREANALYZE_DEBUG") == "1":
        print(f"[INFO] linux_zip: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 工作目录管理
# ---------------------------------------------------------------------------

_WORK_BASE = Path.home() / "ninetail" / "tmp" / "intrusion_analysis"


def _make_work_dir() -> Path:
    """创建唯一的工作目录，返回路径。"""
    work_dir = _WORK_BASE / str(uuid.uuid4())
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


# ---------------------------------------------------------------------------
# 任务委派接口
# ---------------------------------------------------------------------------

def can_handle(path: str) -> bool:
    """判断路径是否为 .zip 文件（大小写不敏感）。"""
    try:
        p = Path(path)
        return p.is_file() and p.suffix.lower() == ".zip"
    except Exception:
        return False


def run(path: str) -> str:
    """执行多主机 zip 预分析，返回拼接后的 Markdown 文本。"""
    analyzer = LinuxZipAnalyzer(path)
    return analyzer.run()


# ---------------------------------------------------------------------------
# 主分析器
# ---------------------------------------------------------------------------

class LinuxZipAnalyzer:
    """多主机 ZIP 包预分析调度器。"""

    def __init__(self, zip_path: str):
        self.zip_path = Path(zip_path).resolve()

    def run(self) -> str:
        """执行分析，返回拼接的多主机预分析 Markdown。"""
        # Step 1: 创建工作目录
        work_dir = _make_work_dir()
        _info(f"工作目录 → {work_dir}")
        _info(f"解压目录已保留，可用于精准回查: {work_dir}")

        # Step 2: 解压 zip 到工作目录
        try:
            self._extract_zip(work_dir)
        except Exception as e:
            return f"# 预分析报告\n\n[ERROR] ZIP 解压失败: {e}\n"

        # Step 3: 在工作目录下查找 tar 文件并逐一解压
        tar_files = self._find_tar_files(work_dir)
        _info(
            f"在 zip 中找到 {len(tar_files)} 个 tar 文件: "
            f"{[f.name for f in tar_files]}"
        )

        # Step 4: 逐个解压 tar → 查找 var/log → 分析
        host_results: list[tuple[str, str]] = []  # [(host_label, markdown), ...]

        if tar_files:
            for tar_file in tar_files:
                host_label, result = self._process_tar(tar_file, work_dir)
                if result:
                    host_results.append((host_label, result))
        else:
            # zip 中没有 tar，直接在 zip 解压目录中查找 var/log
            log_dirs = self._find_var_log_dirs(work_dir)
            _info(
                f"未找到 tar 文件，直接在解压目录查找 var/log: "
                f"{len(log_dirs)} 个"
            )
            for log_dir in log_dirs:
                host_label = self._infer_host_label(log_dir, work_dir)
                result = self._analyze_log_dir(log_dir, host_label)
                if result:
                    host_results.append((host_label, result))

        # Step 5: 拼接多主机结果
        if not host_results:
            return (
                "# 预分析报告\n\n"
                f"[WARN] 未在 {self.zip_path.name} 中找到可识别的 var/log 目录\n"
            )

        return self._render_combined(host_results)

    # ── 内部方法 ──

    def _extract_zip(self, work_dir: Path) -> None:
        """将 zip 文件解压到工作目录。"""
        _info(f"解压 {self.zip_path.name} → {work_dir}")
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            zf.extractall(work_dir)

    def _find_tar_files(self, search_dir: Path) -> list[Path]:
        """递归查找所有 tar 文件（.tar / .tar.gz / .tgz）。"""
        tar_files = []
        for f in search_dir.rglob("*"):
            if f.is_file() and (
                f.name.endswith(".tar")
                or f.name.endswith(".tar.gz")
                or f.name.endswith(".tgz")
            ):
                tar_files.append(f)
        return sorted(tar_files)

    def _process_tar(self, tar_file: Path, work_dir: Path) -> tuple[str, str]:
        """解压单个 tar 文件到独立子目录，查找 var/log 并分析。

        Returns:
            (host_label, markdown) — host_label 来自 tar 文件名
        """
        # 以 tar 文件名（去扩展名）作为子目录名，避免多个 tar 的 var/log 冲突
        tar_stem = tar_file.name
        for suffix in (".tar.gz", ".tgz", ".tar"):
            if tar_stem.endswith(suffix):
                tar_stem = tar_stem[: -len(suffix)]
                break

        extract_dir = work_dir / tar_stem
        extract_dir.mkdir(exist_ok=True)

        _info(f"解压 {tar_file.name} → {extract_dir}")
        try:
            with tarfile.open(tar_file, "r:*") as tf:
                # filter="data" 安全模式：阻止绝对路径和路径遍历（Python 3.12+）
                try:
                    tf.extractall(extract_dir, filter="data")
                except TypeError:
                    # Python < 3.12 不支持 filter 参数
                    tf.extractall(extract_dir)  # noqa: S202
        except Exception as e:
            print(f"[WARN] linux_zip: 解压 {tar_file.name} 失败: {e}", file=sys.stderr)
            return tar_stem, ""

        # 在解压目录中查找 var/log
        log_dirs = self._find_var_log_dirs(extract_dir)
        if not log_dirs:
            print(
                f"[WARN] linux_zip: {tar_file.name} 解压后未找到 var/log 目录",
                file=sys.stderr,
            )
            return tar_stem, ""

        if len(log_dirs) > 1:
            print(
                f"[WARN] linux_zip: {tar_file.name} 中找到多个 var/log 目录，"
                f"使用第一个: {log_dirs[0]}",
                file=sys.stderr,
            )

        log_dir = log_dirs[0]
        host_label = tar_stem  # 用 tar 文件名作为主机标识
        result = self._analyze_log_dir(log_dir, host_label)
        return host_label, result

    def _find_var_log_dirs(self, search_dir: Path) -> list[Path]:
        """在目录树中递归查找所有 var/log 结构。

        匹配规则：目录路径以 var/log 或 var\\log 结尾（兼容不同提取路径）。
        """
        found = []
        for d in search_dir.rglob("*"):
            if d.is_dir():
                # 路径以 var/log 结尾
                parts = d.parts
                if len(parts) >= 2 and parts[-1] == "log" and parts[-2] == "var":
                    found.append(d)
        return sorted(found)

    def _infer_host_label(self, log_dir: Path, work_dir: Path) -> str:
        """从路径推断主机标签。"""
        try:
            rel = log_dir.relative_to(work_dir)
            # 取相对路径第一段（通常是 tar stem 或 zip 内部目录名）
            return rel.parts[0] if rel.parts else log_dir.parent.parent.name
        except ValueError:
            return log_dir.parent.parent.name

    def _analyze_log_dir(self, log_dir: Path, host_label: str) -> str:
        """调用 linux_log_folder 分析单个 var/log 目录。"""
        try:
            from preanalyze_linux_log_folder import can_handle as lf_can_handle
            from preanalyze_linux_log_folder import run as lf_run
        except ImportError:
            # 通过 ANALYSIS_DIR 路径导入
            sys.path.insert(0, str(_LOG_FOLDER_DIR))
            from preanalyze_linux_log_folder import can_handle as lf_can_handle
            from preanalyze_linux_log_folder import run as lf_run

        if not lf_can_handle(str(log_dir)):
            print(
                f"[WARN] linux_zip: {log_dir} 不是有效的 var/log 目录，跳过",
                file=sys.stderr,
            )
            return ""

        _info(f"分析主机 [{host_label}] → {log_dir}")
        return lf_run(str(log_dir), hostname_hint=host_label)

    def _render_combined(self, host_results: list[tuple[str, str]]) -> str:
        """将多主机预分析结果拼接为统一 Markdown。

        格式：
          # 多主机预分析报告
          受影响主机数: N
          ---
          ## 主机: {label}
          {markdown}
          ---
          ## 主机: {label2}
          {markdown2}
        """
        host_count = len(host_results)
        parts: list[str] = []

        parts.append("# 多主机预分析报告")
        parts.append("")
        parts.append(f"受影响主机数: {host_count}")
        parts.append(
            f"主机列表: {', '.join(label for label, _ in host_results)}"
        )
        parts.append("")
        parts.append(
            "> ⚠️ 以下为各主机独立预分析结果，"
            "AI 分析时需跨主机关联相同攻击者 IP 和内网横向移动行为。"
        )
        parts.append("")

        for i, (label, markdown) in enumerate(host_results):
            parts.append("---")
            parts.append("")
            parts.append(f"## 主机: {label}")
            parts.append("")
            parts.append(markdown.strip())
            parts.append("")

        parts.append("---")
        parts.append("")
        parts.append("# 多主机预分析结束")
        parts.append("")

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Linux 多主机 ZIP 包预分析工具（Markdown 输出到 stdout）",
        epilog=(
            "示例:\n"
            "  python3 preanalyze_linux_zip.py /path/to/incident.zip\n"
            "\n"
            "推荐通过统一入口调用:\n"
            "  python3 scripts/analysis/preanalyze.py /path/to/incident.zip\n"
            "\n"
            "解压目录: $HOME/ninetail/tmp/intrusion_analysis/{UUID}/\n"
            "（不自动清理，保留供精准回查）\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("zip_file", help="包含多主机日志 tar 包的 ZIP 文件路径")

    args = parser.parse_args()

    zip_path = Path(args.zip_file)
    if not zip_path.exists():
        print(f"[ERROR] 文件不存在: {zip_path}", file=sys.stderr)
        sys.exit(1)

    if not can_handle(str(zip_path)):
        print(f"[ERROR] 不是 .zip 文件: {zip_path}", file=sys.stderr)
        sys.exit(1)

    print(run(str(zip_path)))


if __name__ == "__main__":
    main()
