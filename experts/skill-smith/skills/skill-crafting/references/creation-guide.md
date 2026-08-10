# 制作标准

生成或修改 Skill 文件时执行本文件。

## 目录结构

```text
skill-name/
├── SKILL.md
├── scripts/
├── references/
└── assets/
```

- `SKILL.md` 必须存在，大小写精确。
- 目录名使用 kebab-case，与 frontmatter 的 `name` 完全一致。
- 只创建任务需要的目录和文件，不生成 README、CHANGELOG、示例脚本或占位资源。
- 确定性、重复性操作下沉到 scripts；领域资料和规范放 references；交付素材放 assets。

## frontmatter

跨平台核心字段：

- `name`：1—64 字符，只含小写字母、数字和单个连字符；不以连字符开头或结尾。
- `description`：20—1024 字符，包含做什么、何时用、关键能力和用户真实触发短语。

目标平台要求的字段按当前平台兼容规则生成。默认目标为 WorkBuddy，本地模型创建的 Skill 同时包含 `version: 1.0.0` 和 `agent_created: true`。

## 正文写法

- 只写做什么、怎么做。
- 使用祈使句和编号步骤。
- 给出确定的输入、动作、产物、通过条件和失败分支。
- 输出格式使用完整模板和填好的真实示例。
- 包含质量自查清单和停止条件。
- 正文不超过 500 行；细节拆到 references。
- 加载式引用只放在顶层 SKILL.md，reference 不再加载其他 reference。
- 信息只放一处，不重复维护同一条硬规则。
- 不出现 TODO、伪代码、修改说明、版本状态标签或历史记录。

## 渐进式披露

- 元数据承担触发判断。
- SKILL.md 保留核心流程和路由。
- references 按任务由顶层 SKILL.md 直接加载。
- scripts 可直接执行，但必须写明参数、输出、环境要求和失败状态。
- assets 只存放最终产物使用的模板与素材。

## 生成方式

1. 先生成完整、无 frontmatter 的正文文件。
2. 确认 name、description、版本和目标目录。
3. 用户完成写入确认后，调用包内 `render` 生成目录和 SKILL.md。
4. 调用包内 `validate` 校验。
5. 校验失败时只修改对应问题，重新运行全部相关检查。
6. 校验通过后再执行实测、打包或安装。

不得使用会自动产生 TODO、example.py、示例 reference 或示例 asset 的初始化模板。

## 依赖与运行环境

逐项识别 MCP、CLI、API、账号、本地工具、Runtime、模型、网络、文件权限和其他会影响功能的条件。

依赖型 Skill 同时生成：

- `skill-dependencies.json`：依赖、功能映射、检查项、配置和降级规则
- `scripts/check_environment.py`：启动前只读检查，不修改配置、不输出凭据
- `references/setup-guide.md`：安装、登录、授权、凭据获取、验证、轮换和撤销说明

每个依赖写明名称、用途、受影响功能、支持版本、官方主页、官方文档、官方下载地址、登录网址、凭据入口、登录后页面路径、所需权限、凭据存储、最小验证、过期处理、轮换、撤销和核验日期。

环境检查结果必须能区分 ready、partial、needs_setup 和 unavailable。ready 时跳过配置教程；partial 时继续可用功能；needs_setup 时只展示缺失项；unavailable 时给故障恢复和安全降级。

不得要求用户在对话中粘贴完整 Token、Key、密码、Cookie 或私钥。不得用未经核验的第三方教程补写官方配置步骤。

## 安装

- 安装位置固定为用户级 `~/.workbuddy/skills/<skill-name>/`。
- 安装前先输出预览，不写入文件。
- 用户完成独立安装确认后才执行。
- 同名更新必须检查 version 严格自增、先备份、再原子替换。
- 安装失败必须回滚并保留可读备份。

## 输出物检查

- [ ] name 合规且与目录同名
- [ ] description 四要素完整，包含用户原话触发短语
- [ ] WorkBuddy 本地模型创建的 Skill 含 version 和 agent_created
- [ ] 正文不超过 500 行，无占位符和伪代码
- [ ] 加载式引用只存在于顶层 SKILL.md，目标真实存在
- [ ] 确定性操作已下沉 scripts
- [ ] 依赖与功能逐项映射，必需项和可选项明确
- [ ] 登录、凭据和授权有准确官方入口、页面路径、权限、安全存储、验证、轮换和撤销说明
- [ ] 启动前环境检查覆盖 CLI、MCP、API、账号、Runtime、本地工具、网络和权限
- [ ] 配置齐全时跳过引导；缺失时只展示缺失项
- [ ] 第三方服务和普通功能都有降级、限制、恢复和停止条件
- [ ] 输出模板和验收标准完整
- [ ] 无修改注释、状态标签和历史记录
