# Changelog

## v1.1.0 — 输出一致性、发布版强约束、开箱即用配置（2026-05-20）

本次更新核心目标：
1. **让同一份输入 JSON 跑 N 次产出文件逐字节相同**（L1 幂等性）
2. **消除历史报告中的样式不一致问题**
3. **让线上发布的 Skill 真正开箱即用**（默认配置随仓库发布，首次运行自动落盘）

### 新增

1. **稳定排序键** (`render_report.py`)
   - 第四章威胁情报表按 `(威胁等级 → CVSS 降序 → CVE)` 稳定排序
   - 第五章紧急/高危条目内部按 `(CVE → 漏洞名 → IP → 端口)` 排序
   - 第五章中危表按稳定键排序
   - 第六章修复优先级按稳定键排序
   - **效果**：消除 dict/Counter 顺序随机性导致的章节内乱序

2. **同 CVE 跨 IP 自动聚合** (`render_report.py`)
   - 紧急/高危逐条分析按 `(CVE 编号 + 漏洞名称)` 聚合为一条
   - IP/端口/资产用 `;` 拼接去重
   - 第六章修复优先级同步聚合
   - **效果**：CVE-2025-8194 跨 3 个 IP 不再拆为 3 条，与小数据集报告风格一致

3. **低危/信息表聚合展示** (`render_report.py`)
   - 按 `(漏洞名称 + CVE)` 去重，展示「影响主机数」列
   - 排序：主机数降序 → 漏洞名升序 → CVE 升序
   - 最多展示 50 类，超出标注「按主机数降序」
   - **效果**：1845 条原始记录聚合为 ≈34 类，告别"NTP 服务"重复 50 行

4. **统一字段渲染 `_fmt()`** (`render_report.py`)
   - `None / "" / [] / "无" → -`
   - Python list / tuple → 用 `；` 拼接
   - **`str(list)` 字面量** (`"['a', 'b']"`) → 安全 `ast.literal_eval` 还原
   - **效果**：`['Apache是…', '存在…']` 这种泄漏到报告的情况彻底消除

5. **`--freeze-time` 参数** (`render_report.py`)
   - 用于幂等性回归测试：`--freeze-time "2026-05-20 00:00:00"`
   - 同输入 + 同 freeze-time → `diff -q` 无任何差异

6. **`--output-dir` 自动命名** (`render_report.py`)
   - 文件名规范：`漏洞分析报告_<YYYY-MM-DD>_<厂商>.md`
   - `<厂商>` 取值固定枚举（绿盟RSAS / 深信服 / Nessus / Trivy 等）
   - **`--output` 自由命名参数已移除**（避免 AI 回退到旧用法导致命名漂移）
   - `ArgumentParser(allow_abbrev=False)` 禁用前缀匹配（避免 `--output` 被误识别为 `--output-dir`）
   - **效果**：杜绝 `_rsas_html2.md` / `_v2.md` 等自由命名

7. **多级指纹去重** (`extract_vulns.py`)
   - 旧策略：仅当 (CVE + 名 + IP) 三项都非空才去重 → 大量低危项漏网
   - 新策略：CVE+名+IP+端口（首选）→ 名+IP+端口+描述前 80 字符（次选）→ 名+IP+端口（兜底）
   - 应用于所有出口（zip 聚合、单文件插件、单文件 cfg.yaml）
   - **效果**：解决 zip 包同时含 `index.html` + `host/<ip>.html` 导致的镜像重复

8. **zip 子文件遍历顺序稳定化** (`extract_vulns.py`)
   - `os.walk` 后按相对路径排序再处理，避免文件系统 inode 顺序影响输出

9. **🎯 开箱即用：默认 `providers.yaml` 随 Skill 发布** (`plan_gate.py` + 仓库结构)
   - **仓库自带** `providers.yaml`（v1.1 起入库，原 `providers.yaml.example` 保留兼容）
   - **首次运行 `plan_gate.py --init` 自动落盘**：将 `{SKILL_DIR}/providers.yaml` 复制到 `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/providers.yaml`（未设置 `CODEBUDDY_PLUGIN_DATA` 时兜底为 `~/ninetail/tmp/vul-analyse/providers.yaml`）
   - 用户后续修改不会被覆盖（仅首次创建时复制）
   - 默认运行模式 = `with-intel`（步骤 3 通过 `default_intel.py` 查询 NVD+EPSS）
   - **效果**：线上用户零配置即可使用，不再依赖"providers.yaml 不存在 → 兜底"的隐式约定

10. **`intel_provider.enabled` 语义统一** (`plan_gate.py`)
    - `enabled: true` → 步骤 3 走用户配置的 MCP Provider
    - `enabled: false` / 字段缺失 → 步骤 3 走 `default_intel.py`（NVD+EPSS 兜底）
    - **步骤 3 始终运行**：默认情报始终保底，区别仅在于后端
    - **效果**：消除"is intel 启用还是关闭"的认知歧义；PLAN.md 显式记录"intel_provider 实际后端"

11. **🗂️ 任务目录隔离（不兼容变更）** (`plan_gate.py`)
    - 旧版：所有产物（PLAN.md、4 个 JSON、报告 .md）都在 `~/ninetail/tmp/vul-analyse/` 根目录共享，跨任务互相覆盖
    - 新版：`--init` 在 `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/runs/<YYYYMMDD-HHMMSS>/` 创建独立任务目录（未设置 `CODEBUDDY_PLUGIN_DATA` 时兜底为 `~/ninetail/tmp/vul-analyse/runs/`），stdout 仅输出该目录绝对路径
    - 同时维护 `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/latest` symlink 指向最新任务（兜底 `~/ninetail/tmp/vul-analyse/latest`）
    - 工作流：`TASK_DIR=$(plan_gate.py --init --input-report ...)`，后续所有命令使用 `$TASK_DIR/PLAN.md` / `$TASK_DIR/vulnerabilities.json` 等
    - 新增**铁律 11**：禁止手写路径（如 `$WORKDIR/xxx.json`），违反即任务失败
    - **效果**：彻底消除跨任务数据污染；同输入跑两次产生两个独立目录，可历史比对

### 变更

- 报告头部版本号 `v1.0.0` → `v1.1.0`
- 厂商标签 slug 化：去掉空格（`绿盟 RSAS` → `绿盟RSAS`），便于文件名嵌入
- 第五章低危表头：`| 漏洞名称 | CVE 编号 | 影响资产 |` → `| 漏洞名称 | CVE 编号 | 影响主机数 |`
- 第七章总结：基于聚合后的「类」数报告（`12 条高危` → `10 类高危`）
- `.gitignore`：移除 `providers.yaml` 排除规则（默认配置入库）；`.env` 仍排除

### 强约束（铁律 11）

发布前必须通过幂等性回归：

```bash
SAMPLE_TASK_DIR="$HOME/ninetail/tmp/vul-analyse/latest"
python3 scripts/render_report.py --workdir "$SAMPLE_TASK_DIR" --output-dir /tmp/r1 --freeze-time "2026-05-20 00:00:00"
python3 scripts/render_report.py --workdir "$SAMPLE_TASK_DIR" --output-dir /tmp/r2 --freeze-time "2026-05-20 00:00:00"
diff -q /tmp/r1 /tmp/r2   # 必须无任何差异
```

### 已知行为变化（迁移指引）

| 项 | v1.0 | v1.1 | 影响 |
|----|------|------|------|
| 高危条目数 | 原始记录数 | (CVE+名) 聚合后类数 | 数字会变小 |
| 低危表行数 | 最多 50 行原始记录 | 最多 50 类聚合记录 | 表更短，信息密度更高 |
| 漏洞描述格式 | 可能是 `['a','b']` 字面量 | 自然语句 | 阅读体验提升 |
| 文件名 | 用户自定义 | 强制 `漏洞分析报告_<日期>_<厂商>.md` | 历史脚本可能需调整 |
| `--output` 参数 | 必填，自由命名 | **已移除**（仅 `--output-dir`） | **不兼容变更**：使用 `--output` 的脚本必须改为 `--output-dir` |
| 漏洞总数 | zip 内可能重复 | 多级指纹去重后 | 数字会变小 |
| `providers.yaml` | 用户需 `cp .example .yaml` | **仓库自带，首次自动落盘** | 零配置即可用 |
| `intel_provider.enabled=false` | 步骤 3 跳过 | 步骤 3 走 default_intel.py 兜底 | **语义变更**：步骤 3 始终运行 |
| **产物路径** | 共享 `~/ninetail/tmp/vul-analyse/` 根目录 | **每次任务独立** `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/runs/<时间戳>/`（兜底 `~/ninetail/tmp/vul-analyse/runs/`） | **不兼容变更**：所有路径必须用 `$TASK_DIR` |
| **`plan_gate.py --init`** | `--plan PLAN.md` 用户指定 | stdout 输出任务目录，`TASK_DIR=$(...)` 捕获 | **不兼容变更**：CLI 接口变化 |

## v1.0.0 — 初始发布

四步骨架：extract → dedupe → intel → render；支持 NVD/EPSS 默认情报；支持 25+ 解析器。

