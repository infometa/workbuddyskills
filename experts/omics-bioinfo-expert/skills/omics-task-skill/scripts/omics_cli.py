#!/usr/bin/env python3
"""
Omics Platform CLI Command Builder & Executor (v6 · 完整命令边界)

封装 omics-platform-cli 的命令拼接与执行，供 SKILL 调用。

⚠️ 能力边界（不可违反 · 最高优先级）⚠️
SKILL 只能调用以下白名单命令，禁止越界：

    login / whoami / config(show/set/clear) / list(*) / run / status / debug / quota

禁止行为：
  1. 严禁编造其他命令（如旧版 app / project / import / app templates 等已废弃命令）
  2. 严禁直接调用 omics 后端 HTTP API、SQL、文件系统写入等任何旁路通道
  3. 严禁通过组合现有命令"模拟"出白名单外的语义
  4. 严禁单独"导入公共应用"——导入是 run --public-app 的内部步骤，必须随 run 一起发生

run 前置确认：
  SKILL 触发 omics run 前必须先输出"完整命令字符串 + 参数摘要表"，
  等用户显式 y/yes/确认 才能执行。本 wrapper 提供 build_run(...) 后由调用方
  完成确认流程，再 cli.execute(...) 真实发起。

子命令结构（由 argparse 强约束）：
  - login                              OAuth 浏览器登录（SKILL 主动调用，拉起浏览器授权）
  - whoami                             当前登录用户
  - config show / set / clear          本地配置（set 由 SKILL 在配置引导流程中调用，参数来自用户选择）
  - list public-apps                   平台公共应用，按 AppTag 分组
  - list apps                          config 项目下的应用
  - list versions                      指定应用的可用版本
  - list templates                     指定应用的运行参数模板
  - list project                       用户全部项目（配置引导用）
  - list env                           用户全部环境（配置引导用）
  - list region                        平台支持的地域列表（配置引导用）
  - list cos-bucket                    当前环境绑定的 COS 桶列表（配置引导用）
  - list volume                        当前环境下的缓存卷列表
  - run                                唯一运行入口（form A/B/C/D）
  - status [<rgId>]                    任务批次/子任务状态
  - debug                              三段式失败取证
  - quota                              C端体验用户配额查询

CLI v3 起已删除（SKILL 不再使用）：
  - omics app list / list-public / templates / file *  → 迁入 omics list 或内化到 run
  - omics project list                                   → 迁入 omics list project
  - omics run-app                                        → 合并到 omics run --public-app/--app

用法示例：
  python omics_cli.py whoami
  python omics_cli.py config show -o json
  python omics_cli.py config set -r ap-guangzhou -p prj-xxx -e env-xxx -b my-bucket
  python omics_cli.py list region -o json
  python omics_cli.py list project -o json
  python omics_cli.py list env --region ap-guangzhou -o json
  python omics_cli.py list cos-bucket -o json
  python omics_cli.py list volume -o json
  python omics_cli.py list public-apps -o json
  python omics_cli.py list public-apps --tag WGS
  python omics_cli.py list public-apps --parent-app cm-collection-xxx -o json
  python omics_cli.py list apps --type WDL -o json
  python omics_cli.py list versions --app app-xxx -o json
  python omics_cli.py list templates --app app-xxx -o json
  python omics_cli.py run --wdl ./hello.wdl --name hello --input ./hello.json
  python omics_cli.py run --wdl ./hello.wdl --name hello --output-dir cos://bucket/out/
  python omics_cli.py run --public-app cm-xxx --public-app-name my-app --app-type WDL
  python omics_cli.py run --app app-xxx --input ./run.json
  python omics_cli.py run --nf cos://bucket/nf-apps/my-pipeline/ --name my-nf --nf-version 24.04.3
  python omics_cli.py status -o json
  python omics_cli.py status rg-aa11bb22 -o json
  python omics_cli.py debug rg-aa11bb22 -o json
  python omics_cli.py debug --run <runUuid> -o json
  python omics_cli.py debug --run <runUuid> --job <jobId> -o json
  python omics_cli.py quota -o json
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
# 命令构建器（白名单命令族）
# ──────────────────────────────────────────────

class OmicsCLI:
    """Omics Platform CLI 命令构建与执行封装（v6 · 完整命令边界）"""

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

    def build_list_cos_bucket(self, output: str = "json") -> list[str]:
        """
        omics list cos-bucket：列当前 config 环境下绑定的 COS 存储桶。

        SKILL 在配置引导 Step C-B-5 中调用（需先完成 Step C-B-4 临时写入 config）。
        过滤 Associated=true 的条目呈现给用户选择。
        """
        return [self.cli_path, "list", "cos-bucket", "-o", output]

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
            "Tags": [str, ...],
            "TotalApps": int,
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
        """
        cmd = [self.cli_path, "list", "apps", "-o", output]
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

    # --- 5. run（唯一运行入口 · 触发前必须二次确认） ---
    def build_run(
        self,
        # 四选一（互斥）
        wdl: str | None = None,          # 形态 A：本地 WDL 文件/目录
        nf_cos_path: str | None = None,  # 形态 D：COS 上的 NF 路径（cos://bucket/prefix/）
        public_app: str | None = None,   # 形态 B：公共应用 AppId
        app: str | None = None,          # 形态 C：项目内 ApplicationId
        # 通用参数
        input_json: str | None = None,
        name: str | None = None,
        main: str | None = None,
        update_app_id: str | None = None,   # 仅形态 A：复用现有应用重试
        public_app_name: str | None = None,
        app_type: str | None = None,        # 仅形态 B：WDL / NEXTFLOW（不传默认 WDL）
        nf_version: str | None = None,
        output: str = "table",
        # 版本管理
        target_version: str | None = None,
        # 形态 A + --update 时的发布命名
        release_name: str | None = None,
        release_desc: str | None = None,
        # 服务端参数模板拍板（form B/C，与 input_json 互斥）
        template_id: str | None = None,
        # NF 运行高级选项（仅 NEXTFLOW 应用有效）
        nf_resume: bool = False,
        nf_config: str | None = None,
        nf_profile: str | None = None,
        nf_report: bool = False,
        volume_id: str | None = None,
        # WDL 运行选项
        output_dir: str | None = None,
    ) -> list[str]:
        """
        合并后的 omics run 命令（CLI v6 唯一运行入口）。

        形态分流（互斥四选一，CLI 强校验）：
          A. 本地 WDL              wdl=...
             - name 必填
             - main 可选（多文件时指定主入口）
             - update_app_id 可选（整改重试时复用已有应用）
             - release_name 可选（配合 update_app_id 发布命名版本）
             - output_dir 可选（指定 COS 结果输出路径）

          D. COS Nextflow          nf_cos_path=...（cos://bucket/prefix/）
             - 文件须预先通过 omics cos upload 上传到 COS，服务端直接读取
             - name 必填
             - nf_version 必填（候选: 22.10.7/23.10.1/23.10.3/24.04.3/25.10.2）
             - main 可选（默认 main.nf）
             - update_app_id 与 --nf 互斥（CLI 会报错拒绝）
             - NF 高级选项可选（nf_resume / nf_config / nf_profile / nf_report）
             - volume_id 可选

          B. 公共应用              public_app=...
             - public_app_name 视情况必传：
               独立公共应用可省（CLI 兜底用原名）；合集子应用必传
             - app_type 可选（WDL 或 NEXTFLOW；不传默认 WDL）
             - nf_version 仅 AppType=NEXTFLOW 时必填
             - template_id 可选（拍板服务端模板，与 input_json 互斥）
             - NF 高级选项可选（AppType=NEXTFLOW 时）
             - volume_id 可选（NF 应用专用）

          C. 项目内已有应用        app=...
             - target_version 可选（指定历史版本）
             - template_id 可选（拍板服务端模板，与 input_json 互斥）
             - nf_version 可选（NEXTFLOW 应用，CLI 会从 RunConstraints 自动取，可覆盖）
             - NF 高级选项可选（NEXTFLOW 应用时）
             - volume_id 可选（NF 应用专用）

        结果引导（output_dir）：
          - 若传入 output_dir，任务成功后 SKILL 应告知用户结果在该 COS 路径
          - 若未传入 output_dir，无需结果引导
        """
        provided = sum(1 for v in (wdl, nf_cos_path, public_app, app) if v)
        if provided != 1:
            raise ValueError("--wdl / --nf / --public-app / --app 必须四选一")
        if template_id and input_json:
            raise ValueError("--template 与 --input 互斥")
        if template_id and not (public_app or app):
            raise ValueError("--template 仅在 form B（--public-app）或 form C（--app）下生效")
        if update_app_id and nf_cos_path:
            raise ValueError("--update 与 --nf 互斥。NF 应用每次运行自动创建新应用，不支持通过 --update 复用旧应用。"
                             "如需运行已有 NF 应用，请使用形态 C：--app <ApplicationId>")

        cmd = [self.cli_path, "run", "-o", output]

        if wdl:
            cmd.extend(["--wdl", wdl])
            if main:
                cmd.extend(["--main", main])
            if update_app_id:
                cmd.extend(["--update", update_app_id])
            if release_name:
                cmd.extend(["--release-name", release_name])
            if release_desc:
                cmd.extend(["--release-desc", release_desc])
            if output_dir:
                cmd.extend(["--output-dir", output_dir])

        elif nf_cos_path:
            cmd.extend(["--nf", nf_cos_path])
            if nf_version:
                cmd.extend(["--nf-version", nf_version])
            # form D 主流程不依赖本地 COS 工具（服务端直接读 COS 源码）
            # 注：--cos-tool flag 仍存在于 CLI 但 form D 主流程不调用 syncFromCos
            if nf_resume:
                cmd.append("--nf-resume")
            if nf_config:
                cmd.extend(["--nf-config", nf_config])
            if nf_profile:
                cmd.extend(["--nf-profile", nf_profile])
            if nf_report:
                cmd.append("--nf-report")
            if volume_id:
                cmd.extend(["--volume-id", volume_id])

        elif public_app:
            cmd.extend(["--public-app", public_app])
            if public_app_name:
                cmd.extend(["--public-app-name", public_app_name])
            if app_type:
                cmd.extend(["--app-type", app_type])
            if nf_version:
                cmd.extend(["--nf-version", nf_version])
            if nf_resume:
                cmd.append("--nf-resume")
            if nf_config:
                cmd.extend(["--nf-config", nf_config])
            if nf_profile:
                cmd.extend(["--nf-profile", nf_profile])
            if nf_report:
                cmd.append("--nf-report")
            if volume_id:
                cmd.extend(["--volume-id", volume_id])

        elif app:
            cmd.extend(["--app", app])
            if nf_version:
                cmd.extend(["--nf-version", nf_version])
            if nf_resume:
                cmd.append("--nf-resume")
            if nf_config:
                cmd.extend(["--nf-config", nf_config])
            if nf_profile:
                cmd.extend(["--nf-profile", nf_profile])
            if nf_report:
                cmd.append("--nf-report")
            if volume_id:
                cmd.extend(["--volume-id", volume_id])

        # 通用参数
        if target_version:
            cmd.extend(["--version", target_version])
        if template_id:
            cmd.extend(["--template", template_id])
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

        退出码语义：
          0 → 成功
          1 → 业务错误
          2 → 鉴权失败（SKILL 应捕获并调用 omics login 引导用户授权）
        """
        print(f"\n> 执行命令: {' '.join(args)}\n")
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
# CLI 入口（argparse 顶层注册所有白名单命令）
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Omics Platform CLI 命令构建与执行工具（v6 · 完整命令边界）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cli-path", default=None,
                        help="指定 omics 可执行文件的完整路径（默认自动查找 PATH）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印命令而不执行")

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
    list_cos = list_sub.add_parser("cos-bucket", help="列当前 config 环境绑定的 COS 存储桶")
    list_cos.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list volume
    list_vol = list_sub.add_parser("volume", help="列当前环境下的缓存卷")
    list_vol.add_argument("--environment", dest="environment_id", default=None, help="临时指定环境 ID")
    list_vol.add_argument("-o", "--output", default="json", choices=["table", "json"])

    # list public-apps
    list_pub = list_sub.add_parser("public-apps", help="列平台公共应用，按 AppTag 分组")
    list_pub.add_argument("--tag", default=None, help="按 AppTag 业务标签精确过滤")
    list_pub.add_argument("--type", dest="app_type", default=None,
                          help="二级类型过滤：WDL / NEXTFLOW")
    list_pub.add_argument("--keyword", default=None, help="service 端关键词搜索")
    list_pub.add_argument("--parent-app", dest="parent_app", default=None,
                          help="展开合集：传入合集 AppId")
    list_pub.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # list apps
    list_apps = list_sub.add_parser("apps", help="列 config 项目下的应用")
    list_apps.add_argument("--type", dest="app_type", default=None,
                           help="WDL / WDL_GRAPH / NEXTFLOW")
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
    run_p = subparsers.add_parser("run", help="发起任务批次（form A/B/C/D 四选一）")
    grp = run_p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--wdl", default=None, help="形态 A：本地 WDL 文件或目录")
    grp.add_argument("--nf", dest="nf_cos_path", default=None,
                     help="形态 D：COS 上的 NF 路径（cos://bucket/prefix/）；文件须预先通过 omics cos upload 上传")
    grp.add_argument("--public-app", dest="public_app", default=None, help="形态 B：公共应用 AppId")
    grp.add_argument("--app", default=None, help="形态 C：项目内 ApplicationId")
    run_p.add_argument("--main", default=None, help="主入口文件（form A 目录时指定；form D 默认 main.nf）")
    run_p.add_argument("--update", dest="update_app_id", default=None,
                       help="形态 A 专用：复用已有应用 ApplicationId 做覆盖上传重试（与 --nf 互斥）")
    run_p.add_argument("--input", dest="input_json", default=None, help="本地参数模板 JSON（override）")
    run_p.add_argument("--public-app-name", dest="public_app_name", default=None)
    run_p.add_argument("--app-type", dest="app_type", default=None,
                       help="仅 form B：应用类型 WDL / NEXTFLOW（不传默认 WDL）")
    run_p.add_argument("--nf-version", dest="nf_version", default=None,
                       help="NF 引擎版本（form B NEXTFLOW 必填；form D 必填；form C 可选覆盖）")
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
    # WDL 运行选项
    run_p.add_argument("--output-dir", dest="output_dir", default=None,
                       help="WDL 专用：结果输出目录（COS 路径，如 cos://bucket/path）")
    run_p.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 6. status
    st = subparsers.add_parser("status", help="任务批次/子任务状态（固定走 config 项目）")
    st.add_argument("run_group_id", nargs="?", default=None)
    st.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 7. debug
    dbg = subparsers.add_parser("debug", help="异步任务失败取证：<runGroupId> / --run / --run + --job")
    dbg.add_argument("run_group_id", nargs="?", default=None)
    dbg.add_argument("--run", dest="run_uuid", default=None)
    dbg.add_argument("--job", dest="job_id", default=None)
    dbg.add_argument("-o", "--output", default="table", choices=["table", "json"])

    # 8. quota
    quota_p = subparsers.add_parser("quota", help="C端体验用户配额查询")
    quota_p.add_argument("-o", "--output", default="table", choices=["table", "json"])

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
                cmd_args = cli.build_list_cos_bucket(output=args.output)
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
                )
            elif args.list_action == "apps":
                cmd_args = cli.build_list_apps(app_type=args.app_type, output=args.output)
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
            )
        elif args.command == "status":
            cmd_args = cli.build_status(run_group_id=args.run_group_id, output=args.output)
        elif args.command == "debug":
            try:
                cmd_args = cli.build_debug(
                    run_group_id=args.run_group_id,
                    run_uuid=args.run_uuid,
                    job_id=args.job_id,
                    output=args.output,
                )
            except ValueError as e:
                _print_errors([str(e)]); sys.exit(1)
        elif args.command == "quota":
            cmd_args = cli.build_quota(output=args.output)
        else:
            parser.print_help(); sys.exit(1)

        if args.dry_run:
            print("DRY RUN - 将执行以下命令:")
            print(" ".join(cmd_args))
            sys.exit(0)

        result = cli.execute(cmd_args, check=False)
        sys.exit(result.returncode)

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


if __name__ == "__main__":
    main()
