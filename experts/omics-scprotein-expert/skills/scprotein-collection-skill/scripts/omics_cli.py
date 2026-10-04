#!/usr/bin/env python3
"""
Omics Platform CLI Command Builder & Executor (v6 · 产物注入版)

封装 omics-platform-cli 的命令拼接与执行，供生成的专用 SKILL 调用。

⚠️ 本文件是 omics-common-app-skill 的 **产物模板**，不直接使用。
   generate_app_skill.py 生成时会：
   1. 将 @@SKILL_APP_ID@@ 替换为实际 AppId（独立应用）
   2. 将 @@SKILL_APP_TYPE@@ 替换为实际 AppType（WDL 或 NEXTFLOW）
   3. 将 @@SKILL_COLLECTION_APP_ID@@ 替换为合集 AppId（仅合集模式）
   4. 将 @@SKILL_SUB_APPS_JSON@@ 替换为子应用清单 JSON（仅合集模式）
   5. 将 @@SKILL_IS_COLLECTION@@ 替换为 true/false
   并用特化后的 build_run() 替换 # @@INJECT_BUILD_RUN@@ 注释区段。

⚠️ 能力边界（不可违反 · 最高优先级）⚠️
生成的产物 SKILL 只能调用以下命令，禁止越界：

    login / whoami / config / list（region / project / env / cos-bucket / apps）
    run（仅 --public-app 形态，AppId 已硬编码）/ status / debug

禁止行为：
  1. 严禁调用 list public-apps（AppId 已硬编码）
  2. 严禁直接调用 omics 后端 HTTP API、SQL、文件系统写入等旁路通道
  3. 严禁 run --wdl / --app / --nf 形态

用法示例（生成后的产物）：
  python omics_cli.py login
  python omics_cli.py whoami
  python omics_cli.py config show -o json
  python omics_cli.py config set -r ap-guangzhou -p prj-xxx -e env-yyy -b my-bucket
  python omics_cli.py list region -o json
  python omics_cli.py list project -o json
  python omics_cli.py list env --region ap-guangzhou -o json
  python omics_cli.py list cos-bucket -o json
  python omics_cli.py list apps --type WDL -o json
  python omics_cli.py run --public-app-name my-app --nf-version 23.10.0
  python omics_cli.py status -o json
  python omics_cli.py debug rg-aa11bb22 -o json
"""

import argparse
import os
import subprocess
import sys

# 默认 CLI 可执行文件名，可通过环境变量 OMICS_CLI_PATH 覆盖
DEFAULT_CLI_NAME = "omics"


def find_cli() -> str:
    """查找 omics CLI 可执行文件的路径。优先级：环境变量 > PATH > 固定路径探测

    固定路径探测说明：
      安装脚本默认将 omics 放到 ~/.local/bin（macOS/Linux）或 WindowsApps（Windows），
      并将该目录写入 ~/.zshrc / ~/.bashrc。但 WorkBuddy 的 subprocess 不会重新 source
      这些配置文件，导致跨会话时 PATH 中可能没有该目录，shutil_which() 找不到 omics。
      固定路径探测直接检查文件是否存在，绕开 PATH 限制，使跨会话检测可靠工作。

      命中固定路径时会输出一行提示，告知用户终端可能尚未生效（需新建终端窗口）。
    """
    env_path = os.environ.get("OMICS_CLI_PATH")
    if env_path:
        if os.path.isfile(env_path) and os.access(env_path, os.X_OK):
            return env_path
        raise FileNotFoundError(
            f"OMICS_CLI_PATH 指定的路径不存在或不可执行: {env_path}\n"
            f"如尚未安装 omics-platform-cli，请前往下载页按页面提供的安装脚本和使用指南完成安装：\n"
            f"  https://cnb.cool/tencenthealthcareomics/omics-platform-cli"
        )

    # 优先查 PATH（尊重用户的 shell 配置）
    cli_path = shutil_which(DEFAULT_CLI_NAME)
    if cli_path:
        return cli_path

    # PATH 未命中时，探测常见固定安装路径
    # 原因：安装后 ~/.zshrc 已更新，但当前 subprocess 的 PATH 尚未刷新
    fixed_candidates: list[str] = []
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            fixed_candidates.append(
                os.path.join(local_app_data, "Microsoft", "WindowsApps", "omics.exe")
            )
    else:
        home = os.path.expanduser("~")
        fixed_candidates = [
            os.path.join(home, ".local", "bin", "omics"),  # macOS/Linux 默认安装路径
            os.path.join(home, "bin", "omics"),            # 部分 Linux 发行版
        ]

    for candidate in fixed_candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            print(
                f"[omics-skill] 已通过固定路径找到 CLI：{candidate}\n"
                f"[omics-skill] 提示：若在终端直接输入 omics 命令不可用，"
                f"请新建终端窗口（重新加载 shell 配置后即可生效）。",
                file=sys.stderr,
            )
            return candidate

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
# 命令构建器（产物专用，仅包含允许的命令）
# ──────────────────────────────────────────────

class OmicsCLI:
    """Omics Platform CLI 命令构建与执行封装（产物专用版）"""

    def __init__(self, cli_path: str | None = None):
        self.cli_path = cli_path or find_cli()

    # --- 1. login ---
    def build_login(self) -> list[str]:
        """
        omics login：启动 localhost:18000 监听，打开浏览器至 OAuth 授权页。
        SKILL 调用时机：whoami 返回 exit 2（未登录或 session 过期）时主动触发。
        """
        return [self.cli_path, "login"]

    # --- 2. whoami ---
    def build_whoami(self) -> list[str]:
        """
        omics whoami：验证当前 session 有效性，判断用户类型（B端/C端）。
        退出码：0=已登录；2=未登录/session 过期 → SKILL 应触发 omics login
        """
        return [self.cli_path, "whoami"]

    # --- 辅助：version ---
    def build_version(self) -> list[str]:
        return [self.cli_path, "version"]

    # --- 3. config ---
    def build_config_show(self, output: str = "table") -> list[str]:
        return [self.cli_path, "config", "show", "-o", output]

    def build_config_clear(self) -> list[str]:
        return [self.cli_path, "config", "clear"]

    def build_config_set(
        self,
        region: str,
        project_id: str,
        environment_id: str,
        bucket_name: str,
    ) -> list[str]:
        """omics config set（一次性自动化模式）：四参数全部必填。"""
        if not region:
            raise ValueError("config set: region 不能为空")
        if not project_id:
            raise ValueError("config set: project_id 不能为空")
        if not environment_id:
            raise ValueError("config set: environment_id 不能为空")
        if not bucket_name:
            raise ValueError("config set: bucket_name 不能为空")
        return [
            self.cli_path, "config", "set",
            "-r", region,
            "-p", project_id,
            "-e", environment_id,
            "-b", bucket_name,
        ]

    # --- 4. list region ---
    def build_list_region(self, output: str = "table") -> list[str]:
        return [self.cli_path, "list", "region", "-o", output]

    # --- 5. list project ---
    def build_list_project(self, output: str = "table") -> list[str]:
        return [self.cli_path, "list", "project", "-o", output]

    # --- 6. list env ---
    def build_list_env(
        self,
        region: str | None = None,
        output: str = "table",
    ) -> list[str]:
        cmd = [self.cli_path, "list", "env", "-o", output]
        if region:
            cmd.extend(["--region", region])
        return cmd

    # --- 7. list cos-bucket ---
    def build_list_cos_bucket(self, output: str = "table") -> list[str]:
        return [self.cli_path, "list", "cos-bucket", "-o", output]

    # --- 8. list apps（仅用于导入前同名检查，必须带 --type）---
    def build_list_apps(
        self,
        app_type: str,
        output: str = "table",
    ) -> list[str]:
        """
        omics list apps：仅用于导入前同名检查。
        ⚠️ app_type 必填，不允许不带 --type 调用（那会列出项目所有应用）。
        """
        if not app_type:
            raise ValueError("build_list_apps: app_type 必填（不允许不带 --type 调用）")
        return [self.cli_path, "list", "apps", "--type", app_type, "-o", output]

    # --- 9. run（合集模式，AppId 来自硬编码子应用清单，生成时注入）---
    def build_run(
        self,
        sub_app_id: str,
        public_app_name: str,
        app_type: str | None = None,
        nf_version: str | None = None,
        input_json: str | None = None,
        name: str | None = None,
        output: str = "table",
    ) -> list[str]:
        """
        omics run（合集模式）：AppId 必须来自本 SKILL 硬编码子应用清单。
        ⚠️ 合集本身（COLLECTION_APP_ID）不可直接作为 --public-app 参数。
        """
        COLLECTION_APP_ID = '5c63718b-d24f-4a9f-9838-4177185f414a'  # 合集 AppId（硬编码，禁止覆盖）
        SUB_APPS = [{"AppId": "bfa72f47-c230-41eb-806f-973fe00a8cda", "AppName": "scPROTEIN_stage1", "AppType": "NEXTFLOW", "AppDesc": "scPROTEIN stage1", "NextflowVersions": ["v24.04.3"]}, {"AppId": "58a00e72-116b-4bd1-bfee-ee22763f21e5", "AppName": "scPROTEIN_stage2", "AppType": "NEXTFLOW", "AppDesc": "scPROTEIN stage2", "NextflowVersions": ["v24.04.3"]}]  # 子应用清单（生成时注入）
        
        # 强校验：sub_app_id 必须在 SUB_APPS 清单中
        valid_ids = {a['AppId'] for a in SUB_APPS}
        if sub_app_id == COLLECTION_APP_ID:
            raise ValueError(
                f"不允许用合集 AppId（{COLLECTION_APP_ID}）直接 run，"
                "请从子应用清单中选择具体子应用"
            )
        if sub_app_id not in valid_ids:
            raise ValueError(
                f"sub_app_id '{sub_app_id}' 不在本合集的子应用清单中。"
                f"合法的 AppId: {sorted(valid_ids)}"
            )
        
        # 从清单中取该子应用的 AppType，用于本地校验
        resolved_app_type = app_type
        if not resolved_app_type:
            for sa in SUB_APPS:
                if sa['AppId'] == sub_app_id:
                    resolved_app_type = sa.get('AppType', '')
                    break
        
        # 本地校验：NEXTFLOW 类型必须传 nf_version
        if resolved_app_type and resolved_app_type.upper() == 'NEXTFLOW' and not nf_version:
            raise ValueError(
                f"子应用 '{sub_app_id}' 为 NEXTFLOW 类型，必须指定 nf_version"
            )
        if resolved_app_type and resolved_app_type.upper() == 'WDL' and nf_version:
            import warnings
            warnings.warn("WDL 类型不需要 nf_version，该参数将被 CLI 忽略", UserWarning)
        
        cmd = [self.cli_path, "run", "-o", output,
               "--public-app", sub_app_id,
               "--public-app-name", public_app_name,
               "--app-type", resolved_app_type]
        if nf_version:
            cmd.extend(["--nf-version", nf_version])
        if input_json:
            cmd.extend(["--input", input_json])
        if name:
            cmd.extend(["--name", name])
        return cmd

    # --- 10. status ---
    def build_status(
        self,
        run_group_id: str | None = None,
        output: str = "table",
    ) -> list[str]:
        cmd = [self.cli_path, "status", "-o", output]
        if run_group_id:
            cmd.append(run_group_id)
        return cmd

    # --- 11. debug 三段式 ---
    def build_debug(
        self,
        run_group_id: str | None = None,
        run_uuid: str | None = None,
        job_id: str | None = None,
        output: str = "table",
    ) -> list[str]:
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
        退出码语义：0=成功；1=业务错误；2=鉴权失败（SKILL 应触发 omics login）
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

def _print_errors(errors: list[str]) -> None:
    print("❌ 参数错误:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)


# ──────────────────────────────────────────────
# CLI 入口（argparse — 产物专用命令集）
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Omics Platform CLI 命令构建与执行工具（产物专用版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cli-path", default=None,
                        help="指定 omics 可执行文件的完整路径（默认自动查找 PATH）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印命令而不执行")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 1. login
    subparsers.add_parser("login", help="OAuth 浏览器登录（SKILL 主动触发）")

    # 2. whoami
    subparsers.add_parser("whoami", help="查看当前登录用户及用户类型（C端/B端）")

    # version（工具命令）
    subparsers.add_parser("version", help="CLI 版本号")

    # 3. config
    cfg = subparsers.add_parser("config", help="本地配置（show / clear / set）")
    cfg_sub = cfg.add_subparsers(dest="config_action")
    cfg_show = cfg_sub.add_parser("show", help="显示当前配置")
    cfg_show.add_argument("-o", "--output", default="table", choices=["table", "json"])
    cfg_sub.add_parser("clear", help="清除本地配置")
    cfg_set = cfg_sub.add_parser("set", help="设置配置（-r/-p/-e/-b 四者必填）")
    cfg_set.add_argument("-r", "--region", required=True)
    cfg_set.add_argument("-p", "--project", dest="project_id", required=True)
    cfg_set.add_argument("-e", "--environment", dest="environment_id", required=True)
    cfg_set.add_argument("-b", "--bucket", dest="bucket_name", required=True)

    # 4. list
    list_p = subparsers.add_parser("list", help="只读查询（地域/项目/环境/COS桶/项目内应用）")
    list_sub = list_p.add_subparsers(dest="list_action")

    list_region = list_sub.add_parser("region", help="列平台全部地域列表")
    list_region.add_argument("-o", "--output", default="table", choices=["table", "json"])

    list_proj = list_sub.add_parser("project", help="列用户全部项目列表")
    list_proj.add_argument("-o", "--output", default="table", choices=["table", "json"])

    list_env = list_sub.add_parser("env", help="列用户全部环境列表")
    list_env.add_argument("--region", default=None)
    list_env.add_argument("-o", "--output", default="table", choices=["table", "json"])

    list_cos = list_sub.add_parser("cos-bucket", help="列当前 config 环境绑定的 COS 桶")
    list_cos.add_argument("-o", "--output", default="table", choices=["table", "json"])

    list_apps = list_sub.add_parser("apps", help="列 config 项目下同类型应用（仅用于同名检查）")
    list_apps.add_argument("--type", dest="app_type", required=True,
                           help="WDL / NEXTFLOW（必填，用于限定查询范围）")
    list_apps.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 5. run（产物专用 — 仅 --public-app 形态，AppId 由 build_run() 内部硬编码）
    run_p = subparsers.add_parser("run", help="发起任务批次（仅 --public-app 形态）")
    run_p.add_argument("--sub-app-id", dest="sub_app_id", required=True,
                       help="子应用 AppId（必须来自本 SKILL 硬编码子应用清单）")
    run_p.add_argument("--public-app-name", dest="public_app_name", default=None,
                       help="导入到项目时的应用名。合集子应用必传；独立应用可省略（CLI 兜底用原名）。")
    run_p.add_argument("--nf-version", dest="nf_version", default=None,
                       help="NEXTFLOW 类型必填；候选版本见 SKILL 中的子应用清单。")
    run_p.add_argument("--input", dest="input_json", default=None,
                       help="本地参数 JSON（override）。不传时 CLI 自动取 InputTemplate 第一个模板。")
    run_p.add_argument("--name", default=None, help="运行批次名称（可选）。")
    run_p.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 6. status
    st = subparsers.add_parser("status", help="任务批次/子任务状态")
    st.add_argument("run_group_id", nargs="?", default=None)
    st.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 7. debug
    dbg = subparsers.add_parser("debug", help="异步任务失败取证（三段式）")
    dbg.add_argument("run_group_id", nargs="?", default=None)
    dbg.add_argument("--run", dest="run_uuid", default=None)
    dbg.add_argument("--job", dest="job_id", default=None)
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
            elif args.config_action == "set":
                cmd_args = cli.build_config_set(
                    region=args.region,
                    project_id=args.project_id,
                    environment_id=args.environment_id,
                    bucket_name=args.bucket_name,
                )
            else:
                cfg.print_help(); sys.exit(1)
        elif args.command == "list":
            if args.list_action == "region":
                cmd_args = cli.build_list_region(output=args.output)
            elif args.list_action == "project":
                cmd_args = cli.build_list_project(output=args.output)
            elif args.list_action == "env":
                cmd_args = cli.build_list_env(region=args.region, output=args.output)
            elif args.list_action == "cos-bucket":
                cmd_args = cli.build_list_cos_bucket(output=args.output)
            elif args.list_action == "apps":
                cmd_args = cli.build_list_apps(
                    app_type=args.app_type, output=args.output,
                )
            else:
                list_p.print_help(); sys.exit(1)
        elif args.command == "run":
            cmd_args = cli.build_run(
                sub_app_id=args.sub_app_id,
                public_app_name=args.public_app_name,
                nf_version=args.nf_version,
                input_json=args.input_json,
                name=args.name,
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
            print("DRY RUN — 将执行以下命令:")
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


if __name__ == "__main__":
    main()

