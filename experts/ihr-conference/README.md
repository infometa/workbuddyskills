# i人事-利唐智语AI面谈官

i人事-利唐智语AI面谈官是一款面向管理者的企业级智能沟通专家，通过 `ihr-cli` 支持面谈安排、历史会议检索、纪要读取、结论总结和行动项梳理。

## 类型

Agent 型专家。

## 核心能力

- **会前安排**：查找并确认面谈官与面谈对象，将相对时间转换为绝对时间，按绩效复盘、绩效辅导、项目复盘等目的创建面谈。
- **历史检索**：按关键词、状态和时间范围搜索历史面谈或项目会议，先返回候选，再按需读取具体内容。
- **会后总结**：基于云录制形成的会议文档，提取会议结论、后续分工、行动计划、待办事项和待确认项。
- **过程约束**：人员 ID、会议状态、纪要和待办均以 `ihr-cli` 的真实返回结果为准，不凭空补全。

## 技能

| 技能名 | 说明 |
|---|---|
| `ihr-bootstrap` | CLI 缺失安装、用户确认后的更新和授权委托入口。 |
| `ihr-shared` | `ihr-cli` 运行环境、登录鉴权、JSON 协议、时间处理和错误排查。 |
| `ihr-base` | 选人组件人员搜索，用于确认面谈官、面谈对象等内部人员 ID。 |
| `ihr-conference` | 历史面谈搜索、会议文档读取、数字人模板和面谈发起。 |

## 环境依赖

专家运行依赖 `ihr-cli`，默认运行环境为 `work100-prod`。专家包已携带 `ihr-bootstrap`、`ihr-shared`、`ihr-base` 和 `ihr-conference`，保证首次加载即有必需 Skills；npm 主路径只安装当前平台 CLI，不安装 Skills。首次需要业务能力时直接执行正式业务命令，不预执行 `auth status`、`version`、Node/npm 或 PATH 检查。CLI 缺失时直接通过 npm 安装，安装成功后直接进入 `auth ensure`；业务返回结构化鉴权错误时再进入授权。版本基线只在用户明确询问版本或要求更新时软提示，不自动更新、切换或降级。后续业务不重复检查，也不统一追加 `--expected-env`。npm 不可用或安装失败时返回通用运行时前置条件错误并停止。

Bootstrap 使用宿主托管的 Node.js/npm runtime 直接通过 `npm install -g @ihr360cli/ihr-cli@latest`（beta 使用 `@beta`）安装 CLI；不预检 Node/npm，不修改 PATH，npm 不安装 Skills，专家包也不携带 installer。npm 安装成功后，若原始请求已有明确业务意图，直接进入 `auth ensure`，不重复执行 `auth status` 或 `version`，不询问“是否继续授权”；授权未完成时提示用户完成授权后回复“已授权”。授权阶段结束后才允许新的业务阶段，当前响应不继续面谈。单独安装/更新请求不会创建授权 Session。后续授权、状态和业务通过宿主正常命令通道直接执行 `ihr-cli`。只更新 CLI 不提示重启，专家包或内置 Skills 变化时只软提示重启，不探测热加载。

结构化纪要、转写和待办的生成依赖线上会议开启云录制；未开启云录制时，可读取的会后内容可能不完整。

## 使用示例

- 安排本周五与张三（[邮箱/手机号]）的绩效复盘，沟通目标达成与改进计划
- 发起下周一与李四（[邮箱/手机号]）的辅导面谈，了解困难并明确支持措施
- 总结近期项目会议结论，明确后续分工和行动计划

## 统一收尾文案

专家会在每轮最终答复的最末尾原样追加以下文案，且仅出现一次：

💡 面谈结束自动出纪要与待办，不用再熬夜整理……
📱 想一起把管理者沟通做扎实的，进HRAI实战群聊聊：[https://work.weixin.qq.com/ca/cawcde4e8626fbb658](https://work.weixin.qq.com/ca/cawcde4e8626fbb658)

## 头像

头像位于 `avatars/expert.png`。如需替换，必须满足：

- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB
- 风格：专业自然，符合企业级 AI 面谈官定位

## 打包

在 `docs` 仓库根目录执行：

```bash
./scripts/package_work100_conference_prod.sh
```

脚本从固定的 `ihr-cli` commit 复制 allowlist Skills，从 `latest.json` 获取专家软提示最低版本，渲染 Agent 主文件四个运行参数，并校验目录与 ZIP inventory 以及 npm runtime 策略。最终包不包含 runtime requirements、runtime manifest、CLI 二进制或 installer。
