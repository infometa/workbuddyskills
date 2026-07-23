#!/usr/bin/env python3
"""
Omics Platform CLI Command Builder & Executor (v4 · 7 命令边界)

封装 omics-platform-cli 的命令拼接与执行，供 SKILL 调用。

⚠️ 能力边界（不可违反 · 最高优先级）⚠️
SKILL 只能调用以下 7 条 CLI 一级命令，禁止越界：

    login / whoami / config / list / run / status / debug

禁止行为：
  1. 严禁编造其他命令（如 app / project / import / app templates 等已废弃命令）
  2. 严禁直接调用 omics 后端 HTTP API、SQL、文件系统写入等任何旁路通道
  3. 严禁通过组合现有命令"模拟"出白名单外的语义
  4. 严禁单独"导入公共应用"——导入是 run --public-app 的内部步骤，必须随 run 一起发生

run 前置确认：
  SKILL 触发 omics run 前必须先输出"完整命令字符串 + 参数摘要表"，
  等用户显式 y/yes/确认 才能执行。本 wrapper 提供 build_run(...) 后由调用方
  完成确认流程，再 cli.execute(...) 真实发起。

子命令结构（由 argparse 强约束）：
  - login                       OAuth 浏览器登录（仅作建议，SKILL 不主动调）
  - whoami                      当前登录用户
  - config show / clear         本地配置查看/清除（SKILL 不调 set，引导用户本机执行）
  - list public-apps            平台公共应用，按 AppTag 分组（含 --tag/--keyword/--parent-app/--type）
  - list apps                   config 项目下的应用（form C 用户挑 ApplicationId 用）
  - run                         唯一运行入口（form A/B/C），baseline + override 合并
  - status [<rgId>]             任务批次/子任务状态
  - debug                       三段式失败取证（<rgId> / --run / --run + --job）

CLI v3 起已删除（SKILL 不再使用）：
  - omics app list / list-public / templates / file *  → 迁入 omics list 或内化到 run
  - omics project list                                   → 由 omics config set 校验链替代
  - omics run-app                                        → 合并到 omics run --public-app/--app

用法示例：
  python omics_cli.py whoami
  python omics_cli.py config show -o json
  python omics_cli.py list public-apps -o json
  python omics_cli.py list public-apps --tag WGS
  python omics_cli.py list public-apps --parent-app cm-collection-xxx -o json
  python omics_cli.py list apps --type WDL -o json
  python omics_cli.py run --wdl ./hello.wdl --name hello --input ./hello.json
  python omics_cli.py run --public-app cm-xxx --public-app-name my-app
  python omics_cli.py run --app app-xxx --input ./run.json
  python omics_cli.py status -o json
  python omics_cli.py status rg-aa11bb22 -o json
  python omics_cli.py debug rg-aa11bb22 -o json
  python omics_cli.py debug --run <runUuid> -o json
  python omics_cli.py debug --run <runUuid> --job <jobId> -o json
"""

import argparse
import os
import subprocess
import sys

# 默认 CLI 可执行文件名，可通过环境变量 OMICS_CLI_PATH 覆盖
DEFAULT_CLI_NAME = "omics"


def find_cli() -> str:
    """查找 omics CLI 可执行文件的路径。优先级：环境变量 > PATH"""
    env_path = os.environ.get("OMICS_CLI_PATH")
    if env_path:
        if os.path.isfile(env_path) and os.access(env_path, os.X_OK):
            return env_path
        raise FileNotFoundError(
            f"OMICS_CLI_PATH 指定的路径不存在或不可执行: {env_path}\n"
            f"如尚未安装 omics-platform-cli，请前往下载页按页面提供的安装脚本和使用指南完成安装：\n"
            f"  https://cnb.cool/tencenthealthcareomics/omics-platform-cli"
        )

    cli_path = shutil_which(DEFAULT_CLI_NAME)
    if cli_path:
        return cli_path

    raise FileNotFoundError(
        f"未找到 '{DEFAULT_CLI_NAME}' 命令。\n"
        f"请前往下载页按页面提供的安装脚本和使用指南完成安装：\n"
        f"  https://cnb.cool/tencenthealthcareomics/omics-platform-cli"
    )


def shutil_which(name: str) -> str | None:
    """跨平台 which 实现"""
    for dir_name in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(dir_name, name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            if sys.platform == "win32":
                exe_path = full_path + ".exe"
                if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                    return exe_path
            return full_path
    return None


# ──────────────────────────────────────────────
# 命令构建器（仅 7 个白名单一级命令）
# ──────────────────────────────────────────────

class OmicsCLI:
    """Omics Platform CLI 命令构建与执行封装（v4 · 7 命令边界）"""

    def __init__(self, cli_path: str | None = None):
        self.cli_path = cli_path or find_cli()

    # --- 1. login（保留 builder 仅供 dry-run 演示，SKILL 不应自动 execute） ---
    def build_login(self) -> list[str]:
        return [self.cli_path, "login"]

    # --- 2. whoami ---
    def build_whoami(self) -> list[str]:
        return [self.cli_path, "whoami"]

    # --- 辅助：version（不属白名单一级命令，但属 CLI 自身工具命令，可调） ---
    def build_version(self) -> list[str]:
        return [self.cli_path, "version"]

    # --- 3. config show / clear（SKILL 不应调 set） ---
    def build_config_show(self, output: str = "table") -> list[str]:
        return [self.cli_path, "config", "show", "-o", output]

    def build_config_clear(self) -> list[str]:
        return [self.cli_path, "config", "clear"]

    # --- 4. list public-apps / apps（替代旧 app list / list-public） ---
    def build_list_public_apps(
        self,
        tag: str | None = None,
        app_type: str | None = None,
        keyword: str | None = None,
        parent_app: str | None = None,
        output: str = "table",
    ) -> list[str]:
        """
        omics list public-apps：列平台公共应用，按 AppTag 分组展示。

        参数:
          tag        : 业务分类标签精确过滤（如 "WGS" / "RNA-seq"）
          app_type   : 二级类型过滤（WDL / NEXTFLOW），可叠加在 tag 之上
          keyword    : service 端关键词搜索
          parent_app : 展开公共应用合集，传入合集 AppId；
                       service 端会屏蔽 type/keyword/tag
          output     : table / json

        JSON 输出形态:
          {
            "Tags": [str, ...],          # 全部出现过的 Tag（含"未分类"）
            "TotalApps": int,            # 去重后的应用总数
            "Groups": [
              { "Tag": str, "Count": int, "Apps": [CommonApp, ...] },
              ...
            ]
          }
        """
        cmd = [self.cli_path, "list", "public-apps", "-o", output]
        if parent_app:
            cmd.extend(["--parent-app", parent_app])
        else:
            if tag:
                cmd.extend(["--tag", tag])
            if app_type:
                cmd.extend(["--type", app_type])
            if keyword:
                cmd.extend(["--keyword", keyword])
        return cmd

    def build_list_apps(
        self,
        app_type: str | None = None,
        output: str = "table",
    ) -> list[str]:
        """
        omics list apps：列当前 config 项目下的应用。

        固定走 config 写入的 ProjectId，不支持 -p。
        SKILL 主要在两处场景使用：
          1. 用户想跑 form C（项目内已有应用）时帮其挑 ApplicationId
          2. form B 导入公共应用前的同名预检（SKILL 比对 Name == candidateName）

        参数:
          app_type : WDL / WDL_GRAPH / NEXTFLOW（默认不过滤）
        """
        cmd = [self.cli_path, "list", "apps", "-o", output]
        if app_type:
            cmd.extend(["--type", app_type])
        return cmd

    # --- 5. run（唯一运行入口 · 触发前必须二次确认） ---
    def build_run(
        self,
        # 三选一
        wdl: str | None = None,
        public_app: str | None = None,
        app: str | None = None,
        # 通用
        input_json: str | None = None,
        name: str | None = None,
        main: str | None = None,
        update_app_id: str | None = None,
        public_app_name: str | None = None,
        nf_version: str | None = None,
        output: str = "table",
    ) -> list[str]:
        """
        合并后的 omics run 命令（CLI v3 唯一运行入口）。

        ⚠️ 调用前必须完成"二次确认"：先 build_run 拼出命令、向用户展示
           参数摘要表，等用户显式回复 y/yes/确认 后才能 cli.execute(...)。

        形态分流（互斥三选一，CLI 强校验）：
          A. 本地 WDL              wdl=...
          B. 公共应用              public_app=...    public_app_name 视情况必传：
                                   - 独立公共应用 + 用户未指定名 → 可省（CLI 兜底用原名）
                                   - 合集子应用 → 必须传（CLI 拿不到子应用元信息无法兜底）
                                   - 用户明确改名 → 必传
                                   nf_version 仅 form B 且 AppType=NEXTFLOW 时必填
          C. 项目内已有应用        app=...

        参数模板（v3 起统一为 baseline + override 合并模式）：
          - 形态 A / C：input_json 为 override；不传时仅靠 baseline（WDL Default）跑
          - 形态 B：CLI 自动取该公共应用第一个 InputTemplate 作为 override；
                   显式 input_json 会覆盖自动模板
          缺必填项时 CLI 以 PARAM_MERGE_FAILED 报错，由 SKILL 引导用户补值。

        Validate 失败后整改重试（仅 A）：
          首次因 WDL Validate 不过被中止时，CLI stderr 会输出 ApplicationId；
          用户更新 WDL 后调用 build_run(wdl=..., update_app_id=app-xxxx) 即可
          复用空白应用做覆盖上传重试（CLI 内部走整目录覆盖 + 乐观锁回退）。
        """
        provided = sum(1 for v in (wdl, public_app, app) if v)
        if provided != 1:
            raise ValueError("--wdl / --public-app / --app 必须三选一")
        if nf_version and not public_app:
            raise ValueError("--nf-version 仅在 form B（--public-app）下生效")

        cmd = [self.cli_path, "run", "-o", output]
        if wdl:
            cmd.extend(["--wdl", wdl])
            if main:
                cmd.extend(["--main", main])
            if update_app_id:
                cmd.extend(["--update", update_app_id])
        elif public_app:
            cmd.extend(["--public-app", public_app])
            if public_app_name:
                cmd.extend(["--public-app-name", public_app_name])
            if nf_version:
                cmd.extend(["--nf-version", nf_version])
        elif app:
            cmd.extend(["--app", app])

        if input_json:
            cmd.extend(["--input", input_json])
        if name:
            cmd.extend(["--name", name])
        return cmd

    # --- 6. status ---
    def build_status(
        self,
        run_group_id: str | None = None,
        output: str = "table",
    ) -> list[str]:
        """
        omics status：固定走 config 的 ProjectId，不支持跨项目查询。
        如需查别的项目，先重新 omics config set。
        """
        cmd = [self.cli_path, "status", "-o", output]
        if run_group_id:
            cmd.append(run_group_id)
        return cmd

    # --- 7. debug 三段式 ---
    def build_debug(
        self,
        run_group_id: str | None = None,
        run_uuid: str | None = None,
        job_id: str | None = None,
        output: str = "table",
    ) -> list[str]:
        """
        omics debug：异步任务失败的"取证"出口（CLI 仅取证，不做规则匹配）。

        三种形态（位置参数 / --run / --run + --job）：
          omics debug <runGroupId>            列该批次所有子任务，标出 Failed
          omics debug --run <runUuid>         单子任务现场（Status + Calls + JobLogs[].Stderr/PodEvents）
          omics debug --run <uuid> --job <j>  在 Calls/JobLogs 中按 JobId 过滤

        run_group_id 与 run_uuid 互斥；job_id 仅在 run_uuid 非空时生效。
        内部链路：GetRunStatus + GetRunCalls + 自动钻取最多 5 个失败 call 的
        JobService.GetRunJobLog(stderr) + MonitorService.DescribeKubernetesEvents(PLAN, JobId)。
        段 2/3 输出 JobLogs[]：含 JobId / CallName / Status / Stderr / StderrTruncated /
        PodEvents（保留 FailedMount 信号）。详见 references/cli_commands.md §debug。
        """
        if run_group_id and run_uuid:
            raise ValueError("debug: <runGroupId> 与 --run 互斥，只能传一个")
        if not run_group_id and not run_uuid:
            raise ValueError("debug: 必须传入 run_group_id 或 run_uuid 之一")
        if job_id and not run_uuid:
            raise ValueError("debug: --job 仅在 --run 模式下生效")

        cmd = [self.cli_path, "debug", "-o", output]
        if run_group_id:
            cmd.append(run_group_id)
        if run_uuid:
            cmd.extend(["--run", run_uuid])
        if job_id:
            cmd.extend(["--job", job_id])
        return cmd

    # --- 执行 ---
    def execute(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        执行 CLI 命令。

        参数:
          args : 完整命令列表
          check: True 则在非零退出码时抛出 CalledProcessError

        退出码语义：
          0 → 成功
          1 → 业务错误
          2 → 鉴权失败（SKILL 应捕获并提示用户在本机跑 omics login，不要循环重试）
        """
        print(f"\n▶ 执行命令: {' '.join(args)}\n")
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, args, result.stdout, result.stderr
            )
        return result


# ──────────────────────────────────────────────
# 参数校验辅助
# ──────────────────────────────────────────────

def validate_run_local_wdl(wdl: str, input_json: str, name: str) -> list[str]:
    errors = []
    if not wdl:
        errors.append("缺少 --wdl")
    elif not os.path.exists(wdl):
        errors.append(f"--wdl 路径不存在: {wdl}")
    if input_json and not os.path.exists(input_json):
        errors.append(f"--input 文件不存在: {input_json}")
    if not (name and name.strip()):
        errors.append("形态 A 必须 --name")
    return errors


# ──────────────────────────────────────────────
# CLI 入口（argparse 顶层只注册 7 个一级命令 + version 工具）
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Omics Platform CLI 命令构建与执行工具（v4 · 7 命令边界）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cli-path", default=None,
                        help="指定 omics 可执行文件的完整路径（默认自动查找 PATH）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印命令而不执行")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 1. login
    subparsers.add_parser("login", help="OAuth 浏览器登录（SKILL 不应自动调；引导用户本机执行）")

    # 2. whoami
    subparsers.add_parser("whoami", help="查看当前登录用户")

    # 工具：version
    subparsers.add_parser("version", help="CLI 版本号")

    # 3. config（show / clear；不暴露 set，避免 SKILL 误调）
    cfg = subparsers.add_parser("config", help="本地配置（show / clear；set 由用户在本机执行）")
    cfg_sub = cfg.add_subparsers(dest="config_action")
    cfg_show = cfg_sub.add_parser("show", help="显示当前配置")
    cfg_show.add_argument("-o", "--output", default="table", choices=["table", "json"])
    cfg_sub.add_parser("clear", help="清除本地配置")

    # 4. list（public-apps / apps）
    list_p = subparsers.add_parser("list", help="只读查询（公共应用 / 项目内应用）")
    list_sub = list_p.add_subparsers(dest="list_action")

    list_pub = list_sub.add_parser("public-apps", help="列平台公共应用，按 AppTag 分组")
    list_pub.add_argument("--tag", default=None, help="按 AppTag 业务标签精确过滤")
    list_pub.add_argument("--type", dest="app_type", default=None,
                          help="二级类型过滤：WDL / NEXTFLOW（叠加在 tag 之上）")
    list_pub.add_argument("--keyword", default=None, help="service 端关键词搜索")
    list_pub.add_argument("--parent-app", dest="parent_app", default=None,
                          help="展开合集：传入合集 AppId（屏蔽 --type/--keyword/--tag）")
    list_pub.add_argument("-o", "--output", default="table", choices=["table", "json"])

    list_apps = list_sub.add_parser("apps", help="列 config 项目下的应用")
    list_apps.add_argument("--type", dest="app_type", default=None,
                           help="WDL / WDL_GRAPH / NEXTFLOW")
    list_apps.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 5. run（合并三形态）
    run_p = subparsers.add_parser("run", help="发起任务批次（form A/B/C 三选一）")
    grp = run_p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--wdl", default=None, help="形态 A：本地 WDL")
    grp.add_argument("--public-app", dest="public_app", default=None, help="形态 B：公共应用 AppId")
    grp.add_argument("--app", default=None, help="形态 C：项目内 ApplicationId")
    run_p.add_argument("--main", default=None)
    run_p.add_argument("--update", dest="update_app_id", default=None)
    run_p.add_argument("--input", dest="input_json", default=None,
                       help="本地参数模板 JSON（override）。form A/C 不传仅靠 baseline；form B 不传时 CLI 自动取第一个 InputTemplate")
    run_p.add_argument("--public-app-name", dest="public_app_name", default=None,
                       help="form B 导入到项目时的应用名。独立公共应用 CLI 兜底用原名；合集子应用必须传。")
    run_p.add_argument("--nf-version", dest="nf_version", default=None,
                       help="form B 专用：NF 公共应用必填；候选见 list public-apps 输出 NextflowVersion[]。")
    run_p.add_argument("--name", default=None)
    run_p.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 6. status
    st = subparsers.add_parser("status", help="任务批次/子任务状态（固定走 config 项目）")
    st.add_argument("run_group_id", nargs="?", default=None)
    st.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 7. debug
    dbg = subparsers.add_parser(
        "debug",
        help="异步任务失败取证：<runGroupId> / --run / --run + --job",
    )
    dbg.add_argument("run_group_id", nargs="?", default=None,
                     help="批次 RunGroupId；与 --run 互斥")
    dbg.add_argument("--run", dest="run_uuid", default=None,
                     help="子任务 RunUuid；与位置参数 <runGroupId> 互斥")
    dbg.add_argument("--job", dest="job_id", default=None,
                     help="底层作业 ID（plan-xxx / tes-xxx）；仅在 --run 模式下生效")
    dbg.add_argument("-o", "--output", default="table", choices=["table", "json"])

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        cli = OmicsCLI(cli_path=args.cli_path)

        if args.command == "login":
            cmd_args = cli.build_login()
        elif args.command == "whoami":
            cmd_args = cli.build_whoami()
        elif args.command == "version":
            cmd_args = cli.build_version()
        elif args.command == "config":
            if args.config_action == "show":
                cmd_args = cli.build_config_show(output=args.output)
            elif args.config_action == "clear":
                cmd_args = cli.build_config_clear()
            else:
                cfg.print_help(); sys.exit(1)
        elif args.command == "list":
            if args.list_action == "public-apps":
                cmd_args = cli.build_list_public_apps(
                    tag=args.tag,
                    app_type=args.app_type,
                    keyword=args.keyword,
                    parent_app=args.parent_app,
                    output=args.output,
                )
            elif args.list_action == "apps":
                cmd_args = cli.build_list_apps(
                    app_type=args.app_type, output=args.output,
                )
            else:
                list_p.print_help(); sys.exit(1)
        elif args.command == "run":
            if args.wdl:
                # 形态 A：name 必填；input_json 可选（不传仅靠 baseline）；CLI 还会做完整校验
                errs = validate_run_local_wdl(args.wdl, args.input_json, args.name)
                if errs:
                    _print_errors(errs); sys.exit(1)
            if args.nf_version and not args.public_app:
                _print_errors(["--nf-version 仅在 form B（--public-app）下生效"])
                sys.exit(1)
            cmd_args = cli.build_run(
                wdl=args.wdl,
                public_app=args.public_app,
                app=args.app,
                input_json=args.input_json,
                name=args.name,
                main=args.main,
                update_app_id=args.update_app_id,
                public_app_name=args.public_app_name,
                nf_version=args.nf_version,
                output=args.output,
            )
        elif args.command == "status":
            cmd_args = cli.build_status(
                run_group_id=args.run_group_id,
                output=args.output,
            )
        elif args.command == "debug":
            try:
                cmd_args = cli.build_debug(
                    run_group_id=args.run_group_id,
                    run_uuid=args.run_uuid,
                    job_id=args.job_id,
                    output=args.output,
                )
            except ValueError as e:
                _print_errors([str(e)])
                sys.exit(1)
        else:
            parser.print_help(); sys.exit(1)

        if args.dry_run:
            print("DRY RUN - 将执行以下命令:")
            print(" ".join(cmd_args))
            sys.exit(0)

        result = cli.execute(cmd_args, check=False)
        sys.exit(result.returncode)

    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作", file=sys.stderr)
        sys.exit(130)


def _print_errors(errors: list[str]) -> None:
    print("❌ 参数错误:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
