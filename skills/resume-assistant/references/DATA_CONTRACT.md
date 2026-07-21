# Data Contract · resume-assistant Skill

> 本文档明确区分 **User Layer（用户层）** 与 **System Layer（系统层）**，规定 Skill 行为边界。
>
> 设计灵感来自 `santifer/career-ops` 的 `DATA_CONTRACT.md` —— 用户数据永不被自动更新，系统逻辑可安全升级。

---

## 一、User Layer · 用户层（永不被自动更新）

这些文件由用户创建 / 拥有 / 维护，Skill 只能**读取**或**按用户指令写入**，**绝不自动修改或删除**。

| 路径 | 用途 | Skill 可以…… |
|---|---|---|
| `<workspace>/experiences/**/*.{md,yaml,json}` | 用户原始经历库（事实来源）| ✅ 读取作为生成素材<br>❌ 自动改写 / 覆盖 |
| `<workspace>/resume-output/_master/` | 主档简历（`is_master: true`）| ✅ 读取<br>✅ 仅在 `mode=rewrite` 且用户确认后更新<br>❌ 删除 |
| `<workspace>/resume-output/<version_id>/` | 派生版本（per-JD 定制）| ✅ 新建 / 更新指定版本<br>❌ 未经确认批量清理 |
| `<workspace>/resume-output/_manifest.json` | 版本树索引 | ✅ 增删版本记录时更新<br>❌ 随意重写 |
| `<workspace>/.resume-assistant/profile.yml` | 用户个性化配置（目标城市 / 排除公司 / 薪资区间）| ✅ 读取<br>✅ 仅在 `mode=config` 明确修改<br>❌ 自动覆盖 |
| `<workspace>/.resume-assistant/experience_library.md` | 跨简历复用的 STAR 故事库（v0.3+）| ✅ 读取<br>✅ 追加新故事<br>❌ 删除已有故事 |
| 用户上传的旧 PDF/DOCX 原件 | 素材来源 | ✅ 读取解析<br>❌ 修改 |

### Skill 强制遵守

1. **不自动触达**：除非用户明确进入 `mode=generate/tailor/rewrite/refine`，Skill 不得写入 `resume-output/`
2. **尊重旧版本**：对任何已存在的 `<version_id>/` 目录，默认 `--no-overwrite`，除非用户传 `--force`
3. **Master 保护**：`_master/` 目录只能通过 `mode=rewrite` 且用户显式确认才修改
4. **Manifest 一致性**：每次写入都要同步更新 `_manifest.json`，且旧记录保留（哪怕 version 状态为 `deprecated`）

---

## 二、System Layer · 系统层（可安全自动更新）

这些文件是 Skill 本身的代码与指令，未来升级可安全替换。

| 路径 | 用途 |
|---|---|
| `<skill_root>/SKILL.md` | 主路由 + 核心原则 |
| `<skill_root>/DATA_CONTRACT.md` | 本文档 |
| `<skill_root>/modes/*.md`（v0.3+）| 各 mode 指令 |
| `<skill_root>/references/*.md` | 参考规则（keyword / provenance / schema / ai-phrase-blacklist）|
| `<skill_root>/assets/*.md` | 简历模板（中/英）|
| `<skill_root>/scripts/*.py` | 工具脚本（JD 解析 / provenance 审计等）|

> 上表的 `<skill_root>` = 当前 skill 包安装目录的绝对路径（脚本内用 `__file__` 解析）。

### 升级行为

1. **覆盖安全**：上述文件可随 Skill 版本升级全量替换，不需保留旧版
2. **不引用用户数据**：系统层代码不得将用户经历/简历硬编码进来
3. **向后兼容**：input-schema / output-schema 变更遵循 semver，breaking change 需升 major 版

---

## 三、边界规则（核心约束）

> **Rule**: If a file is in the User Layer, no update process may read, modify, or delete it without explicit user instruction.
>
> **Rule**: If a file is in the System Layer, it can be safely replaced with the latest version from the Skill repo.

### 具体禁止清单

| 场景 | 禁止行为 |
|---|---|
| Skill 升级 | ❌ 不得清理 `<workspace>/resume-output/` 下任何历史版本 |
| `mode=generate` | ❌ 不得读写 `experiences/` 以外的用户文件 |
| `mode=tailor` | ❌ 不得修改 `_master/`，只能派生新 version_id |
| `mode=delete` 对 master | ❌ 必须拒绝，除非用户显式 `--promote-next <version_id>` 并传入合法 version |
| 任何 mode | ❌ 不得上传用户简历或经历到任何外部服务 |
| 任何 mode | ❌ 不得把用户姓名/电话/邮箱硬编码进系统文件 |

---

## 四、与 `_manifest.json` 的关系

`_manifest.json` 是 User Layer 中最"活跃"的文件 —— 每次生成 / 删除 / 重命名版本都会更新。为了兼顾工程正确性与用户数据保护，约定：

1. Skill 修改 `_manifest.json` **必须**采用"读-改-写"原子模式（读入全量 → 修改内存对象 → 一次写回）
2. 保留 `schema_version` 字段，Skill 升级导致 schema 变化时自动迁移（不能让旧 manifest 报错）
3. 用户手动编辑 `_manifest.json` 是允许的 —— Skill 下次读入时要容忍人类输入（信号化字段允许缺失）

---

## 五、跨 Skill 协作的数据边界（为 job-coach 父 Skill 准备）

未来 `job-coach` 父 Skill 调用本 Skill 时：

```yaml
job-coach → resume-assistant:
  输入: 结构化 JSON（参见 references/input-schema.md）
  输出: 结构化 JSON + 文件路径（参见 references/output-schema.md）

job-coach 不得:
  - 绕过本 Skill 直接读写 resume-output/
  - 修改 _master/
  - 删除任何派生版本

job-coach 可以:
  - 请求本 Skill 的 mode=list 查询版本
  - 请求本 Skill 的 mode=score 做评分
  - 把评分结果写入 job-coach 自己的用户数据目录（`<workspace>/job-coach-output/`），但不影响本 Skill 数据
```

---

## 附录 · 参考来源

- `santifer/career-ops` `DATA_CONTRACT.md`（38K ⭐ 开源项目的工程实践）
- `srbhr/Resume-Matcher` 的 `is_master` + `parent_id` 数据模型（26K ⭐）
- 详细调研与吸收论证见 [`docs/requirements/AI简历助手/需求说明/融合吸收点.md`](../../../docs/requirements/AI简历助手/需求说明/融合吸收点.md)
