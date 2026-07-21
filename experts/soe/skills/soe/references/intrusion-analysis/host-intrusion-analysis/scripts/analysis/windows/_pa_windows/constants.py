"""预分析工具常量定义。

包含 Windows 专用常量（白名单、枚举值等）。
平台无关的格式正则从 _common.constants 重导出。
"""

import re

from _common.constants import (  # noqa: F401
    METADATA_IPS,
    RE_EVENTS,
    RE_EVENTS_NO_COUNT,
    RE_KV,
    RE_NO_DATA,
    RE_SECTION,
    RE_SECTION_DESC,
    RE_SUB,
    RE_TABLE_SEP,
    RE_WHOAMI_TABLE_SEP,
)

# 4104 Path 白名单前缀（小写化比较）
PS_PATH_WHITELIST = [
    r"c:\windows\system32\windowspowershell",
    r"c:\windows\syswow64\windowspowershell",
    r"c:\program files\windowspowershell",
    r"c:\program files (x86)\windowspowershell",
    r"c:\program files\powershell",
]

# 4104 ScriptBlockText 特征白名单
# 注意：PS1 输出中 ScriptBlockText 被截断为约 80 字符，
# 所以需要匹配截断后仍可识别的特征
PS_CONTENT_PATTERNS = [
    # 系统 CDXML cmdletization 模块（首个脚本块）
    # 截断后的典型形式: "#requires -version 3.0 try { Microsoft.PowerShell.Core\Set-StrictMode -Off } ..."
    lambda text: (
        "#requires -version 3.0" in text.lower()
        and "microsoft.powershell." in text.lower()
    ),
    # 系统 CDXML cmdletization 模块（后续脚本块片段 - 变量名特征）
    # 注意：截断可能从行中间开始，所以 $ 可能丢失
    lambda text: "__cmdletization_" in text,
    # 系统 CDXML cmdletization 模块（后续脚本块片段 - 类型引用特征）
    lambda text: "Microsoft.PowerShell.Cmdletization.MethodParameter" in text,
    # 系统 CDXML cmdletization 模块（后续脚本块片段 - ParameterSet 定义特征）
    lambda text: "ParameterSetName=" in text and ("Mandatory=" in text or "ValidateNotNull" in text),
    # 系统 CDXML cmdletization 模块（后续片段 - Bindings 属性）
    lambda text: "ParameterType =" in text and "Bindings =" in text,
    # 系统 CDXML cmdletization 模块（更多后续片段特征）
    # 截断可能从 "Microsoft.PowerShell.Cmdletization." 中间切开
    lambda text: "Cmdletization." in text,
    # 系统 CDXML 模块中的 ciminstance/CIM 相关参数
    lambda text: "[ciminstance" in text and "ValidateNotNull" in text,
]

# 4104 Path 白名单额外模式（使用通配符 / 部分匹配）
PS_PATH_EXTRA_WHITELIST = [
    # Windows 系统诊断临时目录
    r"c:\windows\temp\sdiag_",
]

# ---------------------------------------------------------------------------
# Phase 2.5: Data Condensation Constants (v1.5.0)
# ---------------------------------------------------------------------------

# (E6) Startup 段 5 个中文 SUB 名称 → JSON key 映射
SUB_WMI_STARTUP = "WMI 启动命令"
SUB_AUTO_START_SERVICES = "自动启动服务（名称列表）"
SUB_REGISTRY_STARTUP = "注册表启动项"
SUB_BROWSER_EXTENSIONS = "浏览器扩展"
SUB_SCHEDULED_TASKS = "计划任务"

# 启动项白名单：WMI 启动命令中的标准 Windows 组件（小写化匹配 Command 字段）
WMI_STARTUP_WHITELIST_COMMANDS = {
    "securityhealthsystray.exe",
    "securityhealthsystray",
    "onedrive.exe",
    "realtekaudiosystray.exe",
}

# 启动项白名单：注册表启动项中的标准 Windows 值（小写化匹配 Name+Value 字段）
REGISTRY_STARTUP_WHITELIST = {
    # Shell / Userinit / 标准系统 Run 键
    ("shell", "explorer.exe"),
    ("userinit", r"c:\windows\system32\userinit.exe,"),
    ("vmapplet", r"c:\windows\system32\control.exe sysdm.cpl"),
    ("vmapplet", "systempropertiesperformance.exe /pagefile"),
    ("webcheck", "{e6fb5e20-de35-11cf-9c87-00aa005127ed}"),
    ("securityhealth", r"c:\windows\system32\securityhealthsystray.exe"),
}

# 启动项白名单：自动启动服务中的标准 Windows 服务（小写化匹配服务名）
AUTO_START_SERVICE_WHITELIST = {
    # Windows 核心服务
    "bam", "bfe", "bits", "brokerinfrastructure", "coreMessagingRegistrar",
    "dcomlaunch", "dhcp", "diagtrack", "dnscache",
    "dosvc", "dps", "eventlog", "eventsystem", "fontsvc", "gpsvc",
    "iphlpsvc", "lanmanserver", "lanmanworkstation", "lsm", "mpssvc",
    "nsi", "power", "profSvc", "rpcEptMapper", "rpcss",
    "samss", "schedule", "seclogon", "sens", "spooler",
    "stateRepository", "systemEventsBroker", "themes", "tiledatamodelsvc",
    "timeBrokerSvc", "tokenBroker", "trustInstaller", "usosvc",
    "windefend", "winmgmt", "wlanSvc", "wsearch", "wuauserv",
    # 常见第三方但非可疑
    "vmtools", "vmwaretoolsd",
}
# 构建小写化集合用于匹配
AUTO_START_SERVICE_WHITELIST_LOWER = {s.lower() for s in AUTO_START_SERVICE_WHITELIST}

# (C7) 4688 系统启动进程白名单
# 匹配逻辑：提取 NewProcessName 文件名部分后，同时检查全名和去 .exe 后缀
BOOT_PROCESS_WHITELIST = {
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    "services.exe", "lsass.exe", "autochk.exe", "registry",
}

# 启动周期时间聚类阈值（秒）
BOOT_CYCLE_THRESHOLD_SEC = 30

# 进程快照：Windows 标准系统进程白名单（小写化匹配）
# 这些进程在安全分析中无价值，输出时直接过滤
PROCESS_WHITELIST = {
    # Windows 核心系统进程
    "system", "idle", "registry", "smss", "csrss", "wininit",
    "winlogon", "services", "lsass", "lsaiso", "svchost",
    "fontdrvhost", "dwm", "sihost", "ctfmon",
    # 用户界面/Shell 进程
    "explorer", "runtimebroker", "applicationframehost",
    "shellexperiencehost", "searchapp", "searchhost",
    "startmenuexperiencehost", "textinputhost",
    "systemsettings", "systemsettingsbroker",
    # 登录/远程桌面辅助
    "logonui", "rdpclip", "rdpinput", "consent",
    # Windows 服务和维护
    "spoolsv", "msdtc", "taskhostw", "securityhealthservice",
    "securityhealthsystray", "sgrmbroker", "smartscreen",
    "searchindexer", "searchprotocolhost", "searchfilterhost",
    "compattelrunner", "usoclient", "musnotification",
    # WMI / COM
    "wmiprvse", "dllhost", "conhost", "dashost",
    # Windows Update / 安装
    "trustedinstaller", "tiworker", "wuauclt", "msiexec",
    "mpsigstub",
    # 内存压缩 / 系统
    "memcompression", "audiodg", "camsvc",
    # Windows Defender
    "msmpeng", "nissrv", "mpdefendercoreservice",
    "securityhealthhost",
}

# SystemInfo security_hygiene 删除字段（诊断字段，非安全数据）
SECURITY_HYGIENE_DROP_FIELDS = {
    "Prefetch_RegistryError", "Prefetch_RecentFiles",
    "OpenSSH_LogSizeBytes", "OpenSSH_LogEmpty",
    "SSHD_ConfigSizeBytes", "SSHD_LogLevel",
    "VSS_ShadowCopies", "VSS_ServiceStartType",
    "VSS_ServiceStatus",  # 报告只用 ShadowCopyCount，服务状态未被引用
    "OpenSSH_DirExists",  # 报告未引用，SSH 分析通过 7045 服务安装推导
    "OpenSSH_LogExists",
    "SSHD_ConfigExists",
    "Prefetch_DirExists",  # 报告只用 Prefetch_FileCount，目录是否存在未引用
}

# IIS 攻击模式匹配规则
IIS_ATTACK_PATTERNS = {
    "path_traversal": re.compile(
        r"(?:\.\.|%2e|/etc/|/passwd)", re.IGNORECASE
    ),
    "config_probe": re.compile(
        r"(?:\.env|\.git/config|config\.json|docker-compose|\.secret|\.vscode)",
        re.IGNORECASE,
    ),
    # (B6) 仅匹配 URI 路径直接以源码后缀结尾，排除带查询参数的正常资源请求
    "source_probe": re.compile(r"^/[^?]*\.(?:php|py|go|rb)$", re.IGNORECASE),
    "info_disclosure": re.compile(
        r"(?:/api/|/wsman|/telescope/|pom\.properties|/status)", re.IGNORECASE
    ),
    "generic_scan": re.compile(
        r"^(?:/?|/robots\.txt|/favicon\.ico|/security\.txt|/\.well-known/)$",
        re.IGNORECASE,
    ),
}

# RFC 1918 / 特殊 IP 段（用于 IP 分类）
# 注意：METADATA_IPS 已从 _common.constants 重导出（第 10 行），
# 此处不再重复定义，避免两处不同步。

# ---------------------------------------------------------------------------
# USN Ransomware Scan Constants
# ---------------------------------------------------------------------------

# 已知勒索软件加密文件后缀（小写化比较）
# 来源: 常见勒索家族样本 + ID Ransomware 数据库
RANSOMWARE_EXTENSIONS = {
    # 通用/高频
    ".encrypted", ".enc", ".locked", ".crypt", ".crypto",
    ".crypted", ".locky", ".zepto", ".cerber", ".cerber3",
    # 特定家族
    ".rox", ".weaxor",  # Weaxor 勒索家族
    ".wncry", ".wncryt", ".wcry",  # WannaCry
    ".deadbolt",  # DeadBolt (NAS)
    ".lockbit", ".abcd",  # LockBit 家族
    ".blackbit", ".basta",  # BlackBit / Black Basta
    ".phobos", ".eking", ".eight", ".faust",  # Phobos 家族
    ".makop", ".mkp",  # Makop 家族
    ".hive",  # Hive
    ".avos", ".avos2", ".avoslinux",  # AvosLocker
    ".medusa",  # MedusaLocker
    ".royal",  # Royal
    ".play",  # Play
    ".clop", ".cl0p",  # Clop
    ".ryuk",  # Ryuk
    ".conti",  # Conti
    ".revil", ".sodinokibi",  # REvil/Sodinokibi
    ".maze",  # Maze
    ".dharma", ".cezar", ".combo", ".java",  # Dharma 家族
    ".stop", ".djvu", ".nood", ".wiaw",  # STOP/Djvu 家族
    ".mallox", ".malox", ".xollam",  # Mallox
    ".trigona",  # Trigona
    ".akira",  # Akira
    ".blackcat", ".alphv",  # BlackCat/ALPHV
    ".cuba",  # Cuba
    ".bianlian",  # BianLian
    ".rhysida",  # Rhysida
    ".8base",  # 8Base
    ".cactus",  # Cactus
    ".ransomhouse",  # RansomHouse
    ".monti",  # Monti
    ".nokoyawa",  # Nokoyawa
    ".rorschach", ".bablock",  # Rorschach/BabLock
    ".yashma", ".chaos",  # Yashma/Chaos
}

# 勒索信文件名模式（正则匹配，忽略大小写）
# 匹配完整文件名（Name 字段），而非路径
RANSOM_NOTE_PATTERNS = [
    r"^readme\.txt$",
    r"^read[-_]?me[!.]*\.(?:txt|html|hta)$",
    r"^how[-_]?to[-_]?(?:decrypt|recover|restore|unlock)",
    r"^recovery[-_ ]?info",
    r"^restore[-_]?files",
    r"^decrypt[-_]?(?:files|info|instructions)",
    r"^!+.*\.(?:txt|html|hta)$",  # !!!xxx.txt 等
    r"^#.*(?:decrypt|recover).*\.(?:txt|html|hta)$",
    r"^ransom[-_]?note",
    r"^your[-_]?files",
    r"^attention[!.]*\.(?:txt|html|hta)$",
    r"^warning[!.]*\.(?:txt|html|hta)$",
    r"^help[-_]?(?:decrypt|restore|recover)",
    r"^unlock[-_]?(?:files|instructions)",
    r"^_readme\.txt$",  # STOP/Djvu
    r"^info\.hta$",  # Dharma/Phobos
    r"^info\.txt$",  # Phobos
    r"^restore-my-files\.txt$",  # LockBit
    r"^lockbit.*\.hta$",  # LockBit
    r"^conti_readme\.txt$",  # Conti
    r"^how_to_back_files\.html$",  # Medusa
]
RANSOM_NOTE_COMPILED = [re.compile(p, re.IGNORECASE) for p in RANSOM_NOTE_PATTERNS]

# Defender 相关路径模式（用于检测 Defender 状态变更）
DEFENDER_PATH_PATTERNS = [
    r"windows defender",
    r"windows security health",
    r"detectionhistory",
    r"detections\.log",
    r"quarantine",
]
DEFENDER_PATH_COMPILED = [re.compile(p, re.IGNORECASE) for p in DEFENDER_PATH_PATTERNS]
