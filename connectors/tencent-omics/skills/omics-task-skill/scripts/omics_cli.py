#!/usr/bin/env python3
"""Build argv and execute the installed Omics CLI without shell expansion.

Contract checked against CLI feature/hosted-environment-agent-bucket d61562e.
Older installations must be checked with ``omics run --help`` before using
Lambda/project flags. Builders do not load credentials, alter config or call APIs.

``--print-command`` only renders argv; ``run --dry-run`` invokes the CLI's real
Lambda validation. The deprecated top-level ``--dry-run`` is a print-only alias
and explicitly reports that no platform validation took place.
"""

from __future__ import annotations

import argparse
import os
import shlex
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
# 命令构建器（白名单命令族）
# ──────────────────────────────────────────────

class OmicsCLI:
    """Omics CLI 命令构建与执行；保留已有 WDL/NF builder API。"""

    def __init__(self, cli_path: str | None = None):
        self.cli_path = cli_path or find_cli()

    # --- 1. login（SKILL 主动调用，拉起浏览器完成 OAuth 授权） ---
    def build_login(self, no_browser: bool = False) -> list[str]:
        """
        omics login：触发 OAuth 浏览器登录。

        SKILL 应主动调用此命令完成用户授权（拉起浏览器）。
        远程 / 无图形环境下 CLI 会自动切换为打印 URL 模式。

        参数:
          no_browser: True 时传 --no-browser，仅打印授权 URL（远程场景）
        """
        cmd = [self.cli_path, "login"]
        if no_browser:
            cmd.append("--no-browser")
        return cmd

    # --- 2. whoami ---
    def build_whoami(self) -> list[str]:
        return [self.cli_path, "whoami"]

    # --- 辅助：version ---
    def build_version(self) -> list[str]:
        return [self.cli_path, "version"]

    # --- 3. config show / set / clear ---
    def build_config_show(self, output: str = "table") -> list[str]:
        return [self.cli_path, "config", "show", "-o", output]

    def build_config_set(
        self,
        region: str,
        project_id: str,
        environment_id: str,
        bucket: str,
    ) -> list[str]:
        """
        omics config set：写入本地配置（四项必填）。

        SKILL 在配置引导流程中调用，参数必须来自用户通过 AskUserQuestion 选项卡
        选定的值，禁止猜测或编造。

        参数:
          region         : 地域（如 ap-guangzhou）；来自 list region 结果
          project_id     : 项目 ID（如 prj-xxx）；来自 list project 结果
          environment_id : 环境 ID（如 env-xxx）；来自 list env 结果
          bucket         : COS 存储桶名称；来自 list cos-bucket 结果
        """
        if not all([region, project_id, environment_id, bucket]):
            raise ValueError("build_config_set: region / project_id / environment_id / bucket 均为必填")
        return [
            self.cli_path, "config", "set",
            "-r", region,
            "-p", project_id,
            "-e", environment_id,
            "-b", bucket,
        ]

    def build_config_clear(self) -> list[str]:
        return [self.cli_path, "config", "clear"]

    # --- 4. list 命令族 ---

    def build_list_region(self, output: str = "json") -> list[str]:
        """
        omics list region：列平台支持的全部地域。

        SKILL 在配置引导 Step C-B-1 中调用，解析结果呈现给用户选择。
        """
        return [self.cli_path, "list", "region", "-o", output]

    def build_list_project(
        self,
        region: str | None = None,
        output: str = "json",
    ) -> list[str]:
        """
        omics list project：列用户的全部项目。

        SKILL 在配置引导 Step C-B-2 中调用（B端用户选项目；C端自动取第一条）。

        参数:
          region : 可选，按地域过滤
        """
        cmd = [self.cli_path, "list", "project", "-o", output]
        if region:
            cmd.extend(["--region", region])
        return cmd

    def build_list_env(
        self,
        region: str | None = None,
        output: str = "json",
    ) -> list[str]:
        """
        omics list env：列用户的全部环境。

        SKILL 在配置引导 Step C-B-2（并行查询）和 C-B-3（展示选择）中调用。

        参数:
          region : 可选，按地域过滤
        """
        cmd = [self.cli_path, "list", "env", "-o", output]
        if region:
            cmd.extend(["--region", region])
        return cmd

    def build_list_cos_bucket(self, output: str = "json", *, environment_id: str | None = None) -> list[str]:
        """
        omics list cos-bucket：列指定环境（缺省组织默认 CLI 环境）的存储桶。

        可通过 environment_id 临时选择环境，不修改 config。
        """
        cmd = [self.cli_path, "list", "cos-bucket", "-o", output]
        if environment_id:
            cmd += ["--environment", environment_id]
        return cmd

    def build_list_volume(
        self,
        environment_id: str | None = None,
        output: str = "json",
    ) -> list[str]:
        """
        omics list volume：列当前环境下的缓存卷。

        SKILL 在用户询问"用哪个 volume"时调用，结果用于 run --volume-id 参数。

        参数:
          environment_id : 可选，临时指定环境 ID（默认读 config）
        """
        cmd = [self.cli_path, "list", "volume", "-o", output]
        if environment_id:
            cmd.extend(["--environment", environment_id])
        return cmd

    def build_list_public_apps(
        self,
        tag: str | None = None,
        app_type: str | None = None,
        keyword: str | None = None,
        parent_app: str | None = None,
        output: str = "table",
        *,
        public_app_id: str | None = None,
    ) -> list[str]:
        """
        omics list public-apps：列平台公共应用，按 AppTag 分组展示。

        参数:
          tag        : 业务分类标签精确过滤（如 "WGS" / "RNA-seq"）
          app_type   : 二级类型过滤（WDL / NEXTFLOW / LAMBDA），可叠加在 tag 之上
          keyword    : service 端关键词搜索
          parent_app : 展开公共应用合集，传入合集 AppId；
                       可以继续按 type/keyword/tag 筛选
          output     : table / json

        JSON 由当前 CLI 原样返回；详情、合集和搜索可有不同字段。
        """
        cmd = [self.cli_path, "list", "public-apps", "-o", output]
        if public_app_id and any((parent_app, tag, app_type, keyword)):
            raise ValueError("list public-apps --app 与筛选/合集参数互斥")
        for flag, value in (("app", public_app_id), ("parent-app", parent_app),
                            ("tag", tag), ("type", app_type), ("keyword", keyword)):
            if value:
                cmd += ["--" + flag, value]
        return cmd

    def build_list_apps(
        self,
        app_type: str | None = None,
        output: str = "table",
        *,
        project: str | None = None,
        agent_project: bool = False,
    ) -> list[str]:
        """
        omics list apps：按显式项目、config 或团队默认项目查询，不创建资源。
        """
        cmd = [self.cli_path, "list", "apps", "-o", output] + self._project_args(project, agent_project)
        if app_type:
            cmd.extend(["--type", app_type])
        return cmd

    def build_list_versions(
        self,
        app: str,
        version_type: str | None = None,
        limit: int | None = None,
        output: str = "json",
    ) -> list[str]:
        """
        omics list versions：列指定应用的可用版本。

        参数:
          app          : 应用 ApplicationId（必填）
          version_type : RELEASE / HISTORY；缺省返回全部
          limit        : 返回条数上限（默认 50）
        """
        if not (app and app.strip()):
            raise ValueError("build_list_versions: --app 不能为空")
        cmd = [self.cli_path, "list", "versions", "--app", app, "-o", output]
        if version_type:
            cmd.extend(["--type", version_type])
        if limit is not None:
            cmd.extend(["--limit", str(limit)])
        return cmd

    def build_list_templates(
        self,
        app: str,
        version: str | None = None,
        limit: int | None = None,
        with_content: bool = False,
        output: str = "json",
    ) -> list[str]:
        """
        omics list templates：列指定应用的运行参数模板。

        SKILL 在 form B/C 运行前调用，呈现模板列表供用户拍板，
        拍板后通过 build_run(template_id=<Id>) 传给 run 命令。

        参数:
          app          : 应用 ApplicationId（必填）
          version      : 可选，按应用版本 ID 过滤模板
          limit        : 返回条数上限（默认 50）
          with_content : True 则附带模板内容
        """
        if not (app and app.strip()):
            raise ValueError("build_list_templates: --app 不能为空")
        cmd = [self.cli_path, "list", "templates", "--app", app, "-o", output]
        if version:
            cmd.extend(["--version", version])
        if limit is not None:
            cmd.extend(["--limit", str(limit)])
        if with_content:
            cmd.append("--with-content")
        return cmd

    @staticmethod
    def _project_args(project: str | None, agent_project: bool) -> list[str]:
        if project is not None and agent_project:
            raise ValueError("--project/-p 与 --agent-project 互斥")
        if project is not None:
            if not project.strip():
                raise ValueError("--project 不能为空")
            return ["--project", project]
        return ["--agent-project"] if agent_project else []

    # Existing positional arguments remain in the same order; additions are keywords.
    def build_run(
        self,
        wdl: str | None = None,
        nf_cos_path: str | None = None,
        public_app: str | None = None,
        app: str | None = None,
        input_json: str | None = None,
        name: str | None = None,
        main: str | None = None,
        update_app_id: str | None = None,
        public_app_name: str | None = None,
        app_type: str | None = None,
        nf_version: str | None = None,
        output: str = "table",
        target_version: str | None = None,
        release_name: str | None = None,
        release_desc: str | None = None,
        template_id: str | None = None,
        nf_resume: bool = False,
        nf_config: str | None = None,
        nf_profile: str | None = None,
        nf_report: bool = False,
        volume_id: str | None = None,
        output_dir: str | None = None,
        *,
        project: str | None = None,
        agent_project: bool = False,
        environment: str | None = None,
        lambda_file: str | None = None,
        lambda_text: str | None = None,
        lambda_cos: str | None = None,
        lambda_build: bool = False,
        override_file: str | None = None,
        override_text: str | None = None,
        override_cos: str | None = None,
        dry_run: bool = False,
        output_prefix: str | None = None,
        param: list[str] | None = None,
        param_json: list[str] | None = None,
        param_output: list[str] | None = None,
        omit_input: list[str] | None = None,
        use_example: bool | None = None,
        image: str | None = None,
        command_json: str | None = None,
        lambda_name: str | None = None,
        lambda_volume: str | None = None,
        lambda_input: list[str] | None = None,
        lambda_output: list[str] | None = None,
        env: list[str] | None = None,
        gpu_json: str | None = None,
        cpu: float | None = None,
        memory: float | None = None,
        disk: float | None = None,
        timeout_seconds: int | None = None,
        client_token: str | None = None,
    ) -> list[str]:
        """Build WDL/NF/application/direct Lambda argv, preserving CLI identity.

        Workflow step overrides use an unchanged YAML ``steps: [{name: ...}]``
        document via override_file/text/cos. The installed CLI validates/merges
        it; this wrapper never converts registered PUBLIC/PRIVATE apps to direct
        YAML. ``param*`` and input_json are schema inputs for Lambda applications,
        not direct Tasks/workflows. Only Lambda accepts run's dry_run flag.
        """
        sources = {"wdl": wdl, "nf": nf_cos_path, "public-app": public_app,
                   "app": app, "lambda-file": lambda_file,
                   "lambda-text": lambda_text, "lambda-cos": lambda_cos}
        selected = [(flag, value) for flag, value in sources.items() if value is not None]
        if len(selected) + bool(lambda_build) != 1:
            raise ValueError("必须且只能选择一个 --wdl/--nf/--public-app/--app/--lambda-file/--lambda-text/--lambda-cos/--lambda-build")
        if any(not value.strip() for _, value in selected):
            raise ValueError("运行来源不能为空")
        overrides = {"override-file": override_file, "override-text": override_text,
                     "override-cos": override_cos}
        if sum(value is not None for value in overrides.values()) > 1:
            raise ValueError("--override-file/--override-text/--override-cos 互斥")
        if any(value is not None and not value.strip() for value in overrides.values()):
            raise ValueError("override 来源不能为空")
        if template_id and input_json:
            raise ValueError("--template 与 --input 互斥")
        if template_id and not (public_app or app):
            raise ValueError("--template 仅适用于 --public-app/--app 的 WDL/NF 应用")
        if update_app_id and nf_cos_path:
            raise ValueError("--update 与 --nf 互斥；已有 NF 应用请使用 --app")
        if output_dir is not None:
            raise ValueError("当前 CLI 没有 --output-dir；Lambda 使用 --output-prefix，WDL 使用实际应用输入/默认结果回执")
        direct = lambda_build or any(value is not None for value in (lambda_file, lambda_text, lambda_cos))
        schema = any((input_json is not None, param, param_json, param_output,
                      omit_input, use_example is not None, target_version is not None))
        if direct and schema:
            raise ValueError("直接 Lambda 不接受应用 schema 参数、--input、--use-example 或 --version；请使用 override/具名 I/O")
        if sum(value == "-" for value in (lambda_file, override_file, input_json)) > 1:
            raise ValueError("标准输入只能供一个 YAML/参数来源使用")
        if lambda_build and (not image or not command_json):
            raise ValueError("--lambda-build 必须提供 --image 与 --command-json")
        lambda_scalars = {**overrides, "output-prefix": output_prefix, "image": image,
                          "command-json": command_json, "lambda-name": lambda_name,
                          "lambda-volume": lambda_volume, "gpu-json": gpu_json,
                          "cpu": cpu, "memory": memory, "disk": disk,
                          "timeout-seconds": timeout_seconds, "client-token": client_token}
        lambda_arrays = {"param": param, "param-json": param_json, "param-output": param_output,
                         "omit-input": omit_input, "lambda-input": lambda_input,
                         "lambda-output": lambda_output, "env": env}
        if (wdl or nf_cos_path) and (dry_run or use_example is not None
                or any(v is not None for v in lambda_scalars.values())
                or any(lambda_arrays.values())):
            raise ValueError("--dry-run 和 Lambda 专属参数不适用于直接 WDL/NF 来源")
        if direct and any((main, update_app_id, public_app_name, app_type, nf_version,
                           release_name, release_desc, template_id, nf_resume,
                           nf_config, nf_profile, nf_report, volume_id)):
            raise ValueError("WDL/NF 应用参数不适用于直接 Lambda")
        if environment is not None and not environment.strip():
            raise ValueError("--environment 不能为空")

        cmd = [self.cli_path, "run", "-o", output]
        cmd += self._project_args(project, agent_project)
        if environment is not None:
            cmd += ["--environment", environment]
        if lambda_build:
            cmd.append("--lambda-build")
        else:
            cmd += ["--" + selected[0][0], selected[0][1]]
        # Pass supplied arguments through; the CLI validates engine-specific
        # application fields after reading the authoritative application type.
        common = {"input": input_json, "name": name, "main": main,
                  "update": update_app_id, "public-app-name": public_app_name,
                  "app-type": app_type, "nf-version": nf_version,
                  "version": target_version, "release-name": release_name,
                  "release-desc": release_desc, "template": template_id,
                  "nf-config": nf_config, "nf-profile": nf_profile, "volume-id": volume_id}
        for flag, value in {**common, **lambda_scalars}.items():
            if value is not None:
                cmd += ["--" + flag, str(value)]
        for flag, values in lambda_arrays.items():
            if isinstance(values, str):
                raise ValueError(f"{flag} 应为字符串列表，不能把一个字符串拆成多个参数")
            for value in values or []:
                if not isinstance(value, str):
                    raise ValueError(f"{flag} 每项必须是字符串")
                cmd += ["--" + flag, value]
        for flag, value in (("nf-resume", nf_resume), ("nf-report", nf_report), ("dry-run", dry_run)):
            if value:
                cmd.append("--" + flag)
        if use_example is not None:
            cmd.append("--use-example=" + str(use_example).lower())
        return cmd

    def build_status(self, run_group_id: str | None = None, output: str = "table",
                     *, project: str | None = None, agent_project: bool = False) -> list[str]:
        """List groups or a group's runs using the same project as submission."""
        cmd = [self.cli_path, "status", "-o", output] + self._project_args(project, agent_project)
        if run_group_id:
            cmd.append(run_group_id)
        return cmd

    def build_debug(self, run_group_id: str | None = None, run_uuid: str | None = None,
                    job_id: str | None = None, output: str = "table", *,
                    project: str | None = None, agent_project: bool = False,
                    with_stdout: bool = False, with_trace: bool = False,
                    with_reports: bool = False, app_type: str | None = None) -> list[str]:
        """Read partial evidence and *Error/*Truncated fields even on failure.

        --with-stdout also retrieves successful Lambda call logs. Run metadata
        supplies the actual execution environment; no config mutation is needed.
        """
        if bool(run_group_id) == bool(run_uuid):
            raise ValueError("debug: 必须且只能传入 run_group_id 或 run_uuid")
        if job_id and not run_uuid:
            raise ValueError("debug: --job 仅在 --run 模式下生效")
        cmd = [self.cli_path, "debug", "-o", output] + self._project_args(project, agent_project)
        if run_group_id:
            cmd.append(run_group_id)
        if run_uuid:
            cmd += ["--run", run_uuid]
        if job_id:
            cmd += ["--job", job_id]
        if app_type:
            cmd += ["--type", app_type]
        for flag, value in (("with-stdout", with_stdout), ("with-trace", with_trace), ("with-reports", with_reports)):
            if value:
                cmd.append("--" + flag)
        return cmd

    # --- 8. quota（仅 C 端体验用户可用） ---
    def build_quota(self, output: str = "table") -> list[str]:
        """
        omics quota：查询 C 端体验用户的配额（仅 C 端用户可用）。

        返回字段：
          run_limit        : 每日运行次数上限
          run_remain_limit : 今日剩余运行次数
          days             : 试用总天数
          remain_days      : 试用剩余天数

        非 C 端用户调用会报错（CLI 内部先做身份校验）。
        """
        return [self.cli_path, "quota", "-o", output]

    # --- 执行 ---
    def execute(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        执行 CLI 命令。

        参数:
          args : 完整命令列表
          check: True 则在非零退出码时抛出 CalledProcessError

        保留原退出码及部分 stdout/stderr。依据 CLI 错误信息判断鉴权、
        参数或业务错误；不能把非零退出或日志读取失败直接当作可以重提任务。
        """
        print(f"> 执行命令: {shlex.join(args)}", file=sys.stderr)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
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
# CLI 入口（argparse 顶层注册所有白名单命令）
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Omics CLI argv 构建与执行；Lambda 参数需要支持对应 flags 的 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cli-path", default=None,
                        help="指定 omics 可执行文件的完整路径（默认自动查找 PATH）")
    parser.add_argument("--print-command", action="store_true", help="仅打印命令，不执行或校验平台")
    parser.add_argument("--dry-run", dest="legacy_print_command", action="store_true",
                        help="已弃用的顶层纯打印别名；真实 Lambda 预览请用 run --dry-run")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 1. login
    login_p = subparsers.add_parser("login", help="OAuth 浏览器登录（SKILL 主动调用，拉起浏览器授权）")
    login_p.add_argument("--no-browser", dest="no_browser", action="store_true",
                         help="不自动拉起浏览器，仅打印授权 URL（远程/无图形环境）")

    # 2. whoami
    subparsers.add_parser("whoami", help="查看当前登录用户")

    # 工具：version
    subparsers.add_parser("version", help="CLI 版本号")

    # 3. config（show / set / clear）
    cfg = subparsers.add_parser("config", help="本地配置管理（show / set / clear）")
    cfg_sub = cfg.add_subparsers(dest="config_action")
    cfg_show = cfg_sub.add_parser("show", help="显示当前配置")
    cfg_show.add_argument("-o", "--output", default="table", choices=["table", "json"])
    cfg_set = cfg_sub.add_parser("set", help="写入配置（四项必填；参数来自用户选择）")
    cfg_set.add_argument("-r", "--region", required=False, default=None, help="地域（如 ap-guangzhou）")
    cfg_set.add_argument("-p", "--project-id", dest="project_id", required=False, default=None, help="项目 ID")
    cfg_set.add_argument("-e", "--environment", dest="environment_id", required=False, default=None, help="环境 ID")
    cfg_set.add_argument("-b", "--bucket", dest="bucket", required=False, default=None, help="COS 存储桶名称")
    cfg_sub.add_parser("clear", help="清除本地配置")

    # 4. list（多子命令）
    list_p = subparsers.add_parser("list", help="只读查询（应用、项目、环境、地域、COS桶、缓存卷等）")
    list_sub = list_p.add_subparsers(dest="list_action")

    # list region
    list_reg = list_sub.add_parser("region", help="列平台支持的全部地域")
    list_reg.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list project
    list_proj = list_sub.add_parser("project", help="列用户的全部项目")
    list_proj.add_argument("--region", default=None, help="按地域过滤")
    list_proj.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list env
    list_env = list_sub.add_parser("env", help="列用户的全部环境")
    list_env.add_argument("--region", default=None, help="按地域过滤")
    list_env.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list cos-bucket
    list_cos = list_sub.add_parser("cos-bucket", help="列指定或组织默认 CLI 环境的存储桶")
    list_cos.add_argument("--environment", dest="environment_id", default=None)
    list_cos.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list volume
    list_vol = list_sub.add_parser("volume", help="列当前环境下的缓存卷")
    list_vol.add_argument("--environment", dest="environment_id", default=None, help="临时指定环境 ID")
    list_vol.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list public-apps
    list_pub = list_sub.add_parser("public-apps", help="列平台公共应用，按 AppTag 分组")
    list_pub.add_argument("--app", dest="public_app_id", default=None, help="查看单个公共应用详情")
    list_pub.add_argument("--tag", default=None, help="按 AppTag 业务标签精确过滤")
    list_pub.add_argument("--type", dest="app_type", default=None,
                          help="二级类型过滤：WDL / NEXTFLOW / LAMBDA")
    list_pub.add_argument("--keyword", default=None, help="service 端关键词搜索")
    list_pub.add_argument("--parent-app", dest="parent_app", default=None,
                          help="展开合集：传入合集 AppId")
    list_pub.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # list apps
    list_apps = list_sub.add_parser("apps", help="列所选项目或团队项目下的应用")
    list_apps.add_argument("--type", dest="app_type", default=None,
                           help="WDL / WDL_GRAPH / NEXTFLOW / LAMBDA")
    list_apps.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # list versions
    list_ver = list_sub.add_parser("versions", help="列指定应用的版本")
    list_ver.add_argument("--app", dest="app", required=True, help="应用 ApplicationId（必填）")
    list_ver.add_argument("--type", dest="version_type", default=None,
                          choices=["RELEASE", "HISTORY"])
    list_ver.add_argument("--limit", type=int, default=None)
    list_ver.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list templates
    list_tpl = list_sub.add_parser("templates", help="列指定应用的运行参数模板")
    list_tpl.add_argument("--app", dest="app", required=True, help="应用 ApplicationId（必填）")
    list_tpl.add_argument("--version", dest="version", default=None)
    list_tpl.add_argument("--limit", type=int, default=None)
    list_tpl.add_argument("--with-content", dest="with_content", action="store_true")
    list_tpl.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # 5. run
    run_p = subparsers.add_parser("run", help="提交 WDL/NF/应用或直接 Lambda（来源互斥）")
    grp = run_p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--wdl", default=None, help="形态 A：本地 WDL 文件或目录")
    grp.add_argument("--nf", dest="nf_cos_path", default=None,
                     help="形态 D：COS 上的 NF 路径（cos://bucket/prefix/）；文件须预先通过 omics cos upload 上传")
    grp.add_argument("--public-app", dest="public_app", default=None, help="形态 B：公共应用 AppId")
    grp.add_argument("--app", default=None, help="形态 C：项目内 ApplicationId")
    grp.add_argument("--lambda-file", default=None, help="直接 Task/workflow YAML 文件，- 表示 stdin")
    grp.add_argument("--lambda-text", default=None, help="直接 Task/workflow YAML 文本")
    grp.add_argument("--lambda-cos", default=None, help="直接 Task/workflow COS YAML 对象")
    grp.add_argument("--lambda-build", action="store_true", help="用 image/command-json 等构造直接 Task")
    run_p.add_argument("--main", default=None, help="主入口文件（form A 目录时指定；form D 默认 main.nf）")
    run_p.add_argument("--update", dest="update_app_id", default=None,
                       help="形态 A 专用：复用已有应用 ApplicationId 做覆盖上传重试（与 --nf 互斥）")
    run_p.add_argument("--input", dest="input_json", default=None, help="本地参数模板 JSON（override）")
    run_p.add_argument("--public-app-name", dest="public_app_name", default=None)
    run_p.add_argument("--app-type", dest="app_type", default=None,
                       help="公共应用类型校验 WDL / NEXTFLOW / LAMBDA；省略自动识别")
    run_p.add_argument("--nf-version", dest="nf_version", default=None,
                       help="NF 引擎版本：COS NF 新建必填，公共应用可省略由服务端选择")
    run_p.add_argument("--version", dest="target_version", default=None,
                       help="指定目标应用版本 ApplicationVersionId")
    run_p.add_argument("--release-name", dest="release_name", default=None,
                       help="form A + --update：把新 HISTORY 版本发布为 RELEASE 并命名")
    run_p.add_argument("--release-desc", dest="release_desc", default=None)
    run_p.add_argument("--template", dest="template_id", default=None,
                       help="form B/C：服务端模板 InputTemplateId（与 --input 互斥）")
    run_p.add_argument("--name", default=None, help="RunGroup 名称前缀（form A/D 必填）")
    # NF 高级选项
    run_p.add_argument("--nf-resume", dest="nf_resume", action="store_true",
                       help="NF 专用：从断点继续执行")
    run_p.add_argument("--nf-config", dest="nf_config", default=None,
                       help="NF 专用：Nextflow config 文件路径")
    run_p.add_argument("--nf-profile", dest="nf_profile", default=None,
                       help="NF 专用：profile 名称（多个逗号分隔）")
    run_p.add_argument("--nf-report", dest="nf_report", action="store_true",
                       help="NF 专用：生成 workflow execution report")
    run_p.add_argument("--volume-id", dest="volume_id", default=None,
                       help="NF 专用：指定非默认缓存卷 ID（可通过 list volume 查询）")
    # Keep the legacy spelling for an actionable error instead of forwarding a nonexistent flag.
    run_p.add_argument("--output-dir", dest="output_dir", default=None,
                       help="旧 wrapper 参数，当前 CLI 不支持；Lambda 使用 --output-prefix")
    run_p.add_argument("--environment", default=None, help="本次执行环境；不修改 config")
    run_p.add_argument("--dry-run", action="store_true", help="调用 CLI 的真实 Lambda 预览；不适用于直接 WDL/NF")
    override = run_p.add_mutually_exclusive_group()
    for flag in ("file", "text", "cos"):
        override.add_argument("--override-" + flag, default=None,
                              help="覆盖 YAML；workflow 使用 steps[].name")
    for flag in ("output-prefix", "image", "command-json", "lambda-name", "lambda-volume", "gpu-json", "client-token"):
        run_p.add_argument("--" + flag, default=None)
    for flag in ("param", "param-json", "param-output", "omit-input", "lambda-input", "lambda-output", "env"):
        run_p.add_argument("--" + flag, action="append", default=None, help="可重复；每项原样传给 CLI")
    for flag in ("cpu", "memory", "disk"):
        run_p.add_argument("--" + flag, type=float, default=None)
    run_p.add_argument("--timeout-seconds", type=int, default=None)
    run_p.add_argument("--use-example", type=parse_boolean, nargs="?", const=True, default=None,
                       help="Lambda 应用使用示例输入；--use-example=false 强制 CUSTOM")
    run_p.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 6. status
    st = subparsers.add_parser("status", help="所选项目任务批次/子任务状态（只读）")
    st.add_argument("run_group_id", nargs="?", default=None)
    st.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 7. debug
    dbg = subparsers.add_parser("debug", help="异步任务失败取证：<runGroupId> / --run / --run + --job")
    dbg.add_argument("run_group_id", nargs="?", default=None)
    dbg.add_argument("--run", dest="run_uuid", default=None)
    dbg.add_argument("--job", dest="job_id", default=None)
    dbg.add_argument("--type", dest="app_type", default=None, choices=["WDL", "NEXTFLOW", "LAMBDA"])
    for flag in ("with-stdout", "with-trace", "with-reports"):
        dbg.add_argument("--" + flag, action="store_true")
    dbg.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 8. quota
    quota_p = subparsers.add_parser("quota", help="C端体验用户配额查询")
    quota_p.add_argument("-o", "--output", default="table", choices=["table", "json"])

    for scoped_parser in (run_p, st, dbg, list_apps):
        project_group = scoped_parser.add_mutually_exclusive_group()
        project_group.add_argument("--project", "-p", default=None, help="本次项目 > config 项目 > 团队项目")
        project_group.add_argument("--agent-project", action="store_true", help="强制团队项目，忽略 config 项目")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        cli = OmicsCLI(cli_path=args.cli_path)

        if args.command == "login":
            cmd_args = cli.build_login(no_browser=getattr(args, "no_browser", False))
        elif args.command == "whoami":
            cmd_args = cli.build_whoami()
        elif args.command == "version":
            cmd_args = cli.build_version()
        elif args.command == "config":
            if args.config_action == "show":
                cmd_args = cli.build_config_show(output=args.output)
            elif args.config_action == "set":
                if not all([args.region, args.project_id, args.environment_id, args.bucket]):
                    _print_errors(["config set 需要 -r <region> -p <project-id> -e <environment> -b <bucket> 四项参数"])
                    sys.exit(1)
                cmd_args = cli.build_config_set(
                    region=args.region,
                    project_id=args.project_id,
                    environment_id=args.environment_id,
                    bucket=args.bucket,
                )
            elif args.config_action == "clear":
                cmd_args = cli.build_config_clear()
            else:
                cfg.print_help(); sys.exit(1)
        elif args.command == "list":
            if args.list_action == "region":
                cmd_args = cli.build_list_region(output=args.output)
            elif args.list_action == "project":
                cmd_args = cli.build_list_project(
                    region=getattr(args, "region", None),
                    output=args.output,
                )
            elif args.list_action == "env":
                cmd_args = cli.build_list_env(
                    region=getattr(args, "region", None),
                    output=args.output,
                )
            elif args.list_action == "cos-bucket":
                cmd_args = cli.build_list_cos_bucket(output=args.output, environment_id=args.environment_id)
            elif args.list_action == "volume":
                cmd_args = cli.build_list_volume(
                    environment_id=getattr(args, "environment_id", None),
                    output=args.output,
                )
            elif args.list_action == "public-apps":
                cmd_args = cli.build_list_public_apps(
                    tag=args.tag,
                    app_type=args.app_type,
                    keyword=args.keyword,
                    parent_app=args.parent_app,
                    output=args.output,
                    public_app_id=args.public_app_id,
                )
            elif args.list_action == "apps":
                cmd_args = cli.build_list_apps(app_type=args.app_type, output=args.output,
                                              project=args.project, agent_project=args.agent_project)
            elif args.list_action == "versions":
                cmd_args = cli.build_list_versions(
                    app=args.app,
                    version_type=args.version_type,
                    limit=args.limit,
                    output=args.output,
                )
            elif args.list_action == "templates":
                cmd_args = cli.build_list_templates(
                    app=args.app,
                    version=args.version,
                    limit=args.limit,
                    with_content=args.with_content,
                    output=args.output,
                )
            else:
                list_p.print_help(); sys.exit(1)
        elif args.command == "run":
            if args.wdl:
                errs = validate_run_local_wdl(args.wdl, args.input_json, args.name)
                if errs:
                    _print_errors(errs); sys.exit(1)
            if args.nf_cos_path and getattr(args, "update_app_id", None):
                _print_errors(["--update 与 --nf 互斥：NF 应用不支持通过 --update 复用旧应用"])
                sys.exit(1)
            cmd_args = cli.build_run(
                wdl=args.wdl,
                nf_cos_path=args.nf_cos_path,
                public_app=args.public_app,
                app=args.app,
                input_json=args.input_json,
                name=args.name,
                main=args.main,
                update_app_id=getattr(args, "update_app_id", None),
                public_app_name=getattr(args, "public_app_name", None),
                app_type=getattr(args, "app_type", None),
                nf_version=getattr(args, "nf_version", None),
                output=args.output,
                target_version=getattr(args, "target_version", None),
                release_name=getattr(args, "release_name", None),
                release_desc=getattr(args, "release_desc", None),
                template_id=getattr(args, "template_id", None),
                nf_resume=getattr(args, "nf_resume", False),
                nf_config=getattr(args, "nf_config", None),
                nf_profile=getattr(args, "nf_profile", None),
                nf_report=getattr(args, "nf_report", False),
                volume_id=getattr(args, "volume_id", None),
                output_dir=getattr(args, "output_dir", None),
                **{key: getattr(args, key) for key in (
                    "project", "agent_project", "environment", "lambda_file", "lambda_text",
                    "lambda_cos", "lambda_build", "override_file", "override_text", "override_cos",
                    "dry_run", "output_prefix", "param", "param_json", "param_output", "omit_input",
                    "use_example", "image", "command_json", "lambda_name", "lambda_volume",
                    "lambda_input", "lambda_output", "env", "gpu_json", "cpu", "memory", "disk",
                    "timeout_seconds", "client_token")},
            )
        elif args.command == "status":
            cmd_args = cli.build_status(run_group_id=args.run_group_id, output=args.output,
                                        project=args.project, agent_project=args.agent_project)
        elif args.command == "debug":
            try:
                cmd_args = cli.build_debug(
                    run_group_id=args.run_group_id,
                    run_uuid=args.run_uuid,
                    job_id=args.job_id,
                    output=args.output,
                    project=args.project, agent_project=args.agent_project,
                    with_stdout=args.with_stdout, with_trace=args.with_trace,
                    with_reports=args.with_reports, app_type=args.app_type,
                )
            except ValueError as e:
                _print_errors([str(e)]); sys.exit(1)
        elif args.command == "quota":
            cmd_args = cli.build_quota(output=args.output)
        else:
            parser.print_help(); sys.exit(1)

        if args.print_command or args.legacy_print_command:
            if args.legacy_print_command:
                print("[DEPRECATED] 顶层 --dry-run 仅打印，未执行 CLI 或平台校验；请改用 --print-command。真实 Lambda 预览使用 run --dry-run。", file=sys.stderr)
            print("PRINT ONLY - 未执行 CLI 或平台校验:", file=sys.stderr)
            print(shlex.join(cmd_args))
            sys.exit(0)

        result = cli.execute(cmd_args, check=False)
        sys.exit(result.returncode)

    except ValueError as e:
        _print_errors([str(e)])
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n[WARN] 用户中断操作", file=sys.stderr)
        sys.exit(130)


def _print_errors(errors: list[str]) -> None:
    print("[ERROR] 参数错误:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)


def parse_boolean(value: str) -> bool:
    if value.lower() not in ("true", "false"):
        raise argparse.ArgumentTypeError("请使用 true 或 false")
    return value.lower() == "true"


if __name__ == "__main__":
    main()
