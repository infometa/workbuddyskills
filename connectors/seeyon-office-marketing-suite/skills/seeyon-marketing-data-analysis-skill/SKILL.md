---
name: seeyon-marketing-data-analysis-skill
description: 在 Seeyon OA 中统一查询“销售订单查询”报表、查询单位/部门/人员/岗位等组织信息、基于订单事实生成营销分析，并把分析报告发送为自由协同。用户要求销售订单报告、订单汇总、发货/开票/收款分析、未发货订单分析、营销数据分析、查询接收人或发送 OA 分析协同时使用；协同发送默认直接执行，不额外要求确认。
---

# Seeyon 营销数据分析

使用 `scripts/seeyon_marketing.py` 作为唯一公开入口。脚本优先从环境变量登录 OA；账号或密码未配置时，复用连接器通过浏览器登录保存的本地会话。不要要求用户提供 Cookie、`JSESSIONID` 或 `route`。

## 准备认证

优先使用运行环境配置：

- `OA_BASE_URL`：完整 OA 登录地址。
- `OA_AUTH_USERNAME`：当前登录账号，同时作为自由协同默认发送人。
- `OA_AUTH_PASSWORD`：登录密码。

当 `OA_AUTH_USERNAME` 或 `OA_AUTH_PASSWORD` 未配置时，不要中止或要求用户复制 Cookie。先在 WorkBuddy 中连接“Seeyon 营销数据分析”连接器：连接器读取已配置的 OA 服务地址，打开隔离登录页面；用户登录成功后自动保存会话，当前 Skill 随后直接复用该 `sessionId`。`OA_BASE_URL`、`SEEYON_SERVICE_URL` 和连接器 `connector-config.json.serviceUrl` 按此顺序提供服务地址。

不要在命令、回复、日志或文件中展示这些变量的值。浏览器会话不可用时，只提示用户在 WorkBuddy 中重新连接对应连接器，不要索要 Cookie。

运行环境需要 Python 3.9+、`requests` 和 `pycryptodome`，版本范围见 `scripts/requirements.txt`。依赖缺失时，只有在用户授权修改环境后才能安装。

## 选择命令

```text
order-query         查询销售订单报表前 100 行
organization        查询单位、部门、人员、岗位、角色、职务级别或完整快照
collaboration-send  生成流程并发送营销分析自由协同
```

先查看参数：

```bash
python scripts/seeyon_marketing.py --help
python scripts/seeyon_marketing.py collaboration-send --help
```

若登录地址不能正确推导业务根地址，可用当前命令的 `--base-url` 覆盖。不要改为手工传 Cookie。

## 查询销售订单

```bash
python scripts/seeyon_marketing.py order-query
```

默认报表名为“销售订单查询”，需要覆盖时使用 `--report-name "销售订单查询"`。

查询严格遵循以下数据边界：

- 只匹配名称完全一致的报表，多个同名报表取服务端顺序中的第一个。
- 使用首个匹配报表的 `createMember` 作为临时 `bizId`，缺失时停止，不猜测。
- 固定查询第 1 页、每页 100 条。
- 保留服务端行数、重复记录和顺序，不去重、不合并、不排序、不修正。
- 不查询销售出库报表，也不拼接出库记录。
- 字段名按显示名称优先级解析；单元格优先使用显示值 `v`，缺少时回退原始值 `s`。

除非用户明确要求原始数据，不要整段原样展示 `orders`。将其作为分析事实输入。

## 生成营销分析

只根据 `orders` 中真实存在的字段回答用户问题：

- 明确区分报表事实、计算结果和分析判断。
- 计算金额和数量时处理千分位逗号、空值和非数字显示值。
- 重复行仍属于本次报表结果，不自行删除；需要说明重复影响时单独提示。
- 数据为空时说明当前报表没有返回订单，不虚构客户、金额或状态。
- 用户要求订单汇总、未发货、开票、收款或客户分析时，只使用实际存在的对应字段。

推荐报告结构：

```markdown
# 销售订单分析
## 数据范围
## 核心指标
## 状态与异常
## 客户或负责人分布
## 建议
```

不存在相应字段时省略该章节，并说明数据限制。

## 查询组织信息

```bash
python scripts/seeyon_marketing.py organization accounts
python scripts/seeyon_marketing.py organization departments --account-id "单位ID"
python scripts/seeyon_marketing.py organization members --account-id "单位ID" --login-name "lisi"
python scripts/seeyon_marketing.py organization posts --account-id "单位ID"
python scripts/seeyon_marketing.py organization roles --account-id "单位ID"
python scripts/seeyon_marketing.py organization job-levels --account-id "单位ID"
python scripts/seeyon_marketing.py organization all --account-id "单位ID"
```

分页中途失败时保留已经取得的数据并明确标记不完整，不把部分结果描述为完整结果。

## 发送营销分析协同

当用户要求把分析结果发送给 OA 人员时，业务参数完整后直接执行，不在发送前额外询问确认。发送人默认使用 `OA_AUTH_USERNAME`，接收人可使用登录名或完整人员 JSON。

```bash
python scripts/seeyon_marketing.py collaboration-send \
  --account-id "单位ID" \
  --subject "销售订单分析报告" \
  --content "<h1>销售订单分析</h1><p>……</p>" \
  --recipient-login-name "lisi" \
  --recipient-login-name "wanger"
```

未提供原始流程 XML 时生成并行流程。需要自定义流程时提供 `--process-xml-file`；XML 在任何附件和正文写入前校验。

附件可选，需要时重复使用 `--attachment "D:/reports/销售订单分析.xlsx"`。

只有用户明确要求预览或暂不发送时才增加 `--dry-run`。dry-run 允许人员与流程校验，但不上传附件、不保存正文、不发送协同。

## 判断结果

所有命令输出单个 JSON 文档。使用 `ok` 判断业务成功，不以 HTTP 200 代替业务成功。

公共字段：

- `ok`
- `command`
- `completedStages`
- `failed_step`（失败时）
- `error`（失败时，已脱敏）

订单查询成功还包含 `reportName`、`reportId`、分页摘要和 `orders`。自由协同成功还包含 `summaryId`、`contentId`、发送人、接收人、流程模式和附件摘要。

附件、正文或最终发送失败时，报告已完成阶段和已有业务 ID，不自动重试、不自动回滚，避免重复协同。

## 安全边界

- 不输出用户名、密码、Cookie、`JSESSIONID`、`route`、Token 或附件二进制。
- 不访问或加载同级来源 Skill 目录；本 Skill 必须独立运行。
- 不在自动测试中连接真实 OA。
- 用户只要求查询或分析时不发送协同。
- 用户明确要求发送时直接执行；用户明确要求预览时才使用 `--dry-run`。
