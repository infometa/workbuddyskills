# 环境与排障说明

本文件承接 `SKILL.md` 的自动排障引用。默认不在 Skill 加载时执行检查，只在脚本或可选 JD MCP 能力不可用时按需读取。

## 普通外部用户

- 普通外部用户不需要安装 MCP。
- 流程/制度类问题不做 MCP 排障；通用流程优先运行 `scripts/fetch_recruit_info.py flow` 动态查询官网公告，个人流程信息引导登录 `join.qq.com` 并咨询校招官网 offer 鹅智能体。
- 岗位/JD、招聘动态、简历检查优先使用 `scripts/` 下的官网脚本和本地规则脚本。

## 触发条件

1. `scripts/fetch_recruit_jds.py`、`scripts/fetch_recruit_info.py`、`scripts/resume_checker.py` 等脚本执行失败。
2. 岗位/JD 意图明确，但官网脚本返回异常，判断为服务问题而不是业务无命中。
3. 受控内测环境明确启用 `campus-recruit-jd-qa`，但工具不可见、描述获取失败、调用失败或连接异常。
4. 用户明确反馈岗位查不到、官网脚本跑不起来或 JD MCP 不生效。

## 最小排障顺序

1. 先检查 Python 环境：

```bash
python scripts/check_python_env.py --json
```

2. 如果是岗位/JD 或招聘动态脚本失败，优先重试更通用关键词；仍失败时引导官网岗位页或动态页。

3. 仅受控内测需要 JD MCP 时，再检查 MCP 依赖与注册：

```bash
python scripts/check_python_env.py --mcp --json
python scripts/check_mcp_registration.py
```

4. 如果可选 JD MCP 未注册，再运行：

```bash
bash scripts/install_mcp.sh
python scripts/check_mcp_registration.py
```

安装后必须完全退出并重启 WorkBuddy。只关闭窗口通常不够。

## 检测逻辑

| 情况 | 行为 |
|------|------|
| Python 环境自检失败 | 先提示更新 Python，不继续运行业务脚本 |
| 官网岗位脚本失败 | 重试更通用关键词；仍失败则引导官网岗位页 |
| `check_mcp_registration.py` 缺少 `campus-recruit-jd-qa` | 仅内测需要时运行 `bash scripts/install_mcp.sh` 后重启 WorkBuddy |
| JD MCP 可用 | 可作为岗位/JD 内测辅助 |
| JD MCP 失败 | 改用 `scripts/fetch_recruit_jds.py` 从官网获取真实岗位/JD；脚本也失败时再引导官网岗位页 |
| 通用流程/制度类问题 | 不查 MCP，优先运行 `scripts/fetch_recruit_info.py flow` 动态查询官网公告；个人流程信息引导校招官网 offer 鹅智能体 |

## 国产模型 / MCP 不显示时

1. 流程/制度类问题不处理 MCP；通用流程动态查询官网公告，个人流程信息引导 `join.qq.com` 校招官网 offer 鹅智能体。
2. 岗位/JD 类优先使用官网脚本；无明确筛选条件时运行 `python scripts/fetch_recruit_jds.py all --max-pages 50 --page-size 100` 全量抓取，有关键词/方向/城市/简历时再运行 `search` 或 `match`。
3. 仅受控内测需要 JD MCP 时，再重启 WorkBuddy 并运行 `python scripts/check_mcp_registration.py`。
4. 注册正常但模型仍看不到工具，继续使用官网脚本；必要时切换支持 MCP 的模型/客户端。

## 禁答模式

- 通用流程/制度类问题优先动态查询官网公告；公告未覆盖或涉及个人流程信息时，只引导官方渠道，不凭训练数据回答。
- JD MCP 和 `scripts/fetch_recruit_jds.py` 官网脚本都不可用时，岗位/JD 类问题只引导官网岗位页，不凭经验推荐岗位。
- 排障或降级到官网引导时，如上下文包含学校层级、院校标签或学历背景，只做中性事实转述，不因工具无命中而评价学校或学生能力。
