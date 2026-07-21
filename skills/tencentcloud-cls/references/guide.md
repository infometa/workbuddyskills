# 腾讯云 CLS 助手

> 📊 让日志检索、故障排查、告警运维变得简单高效

---

## 📋 适用场景

### 场景一：快速定位线上故障

**典型问题**：

- "线上突然报错了，不知道哪条日志有问题"
- "这个错误在什么时候开始出现的？"
- "出错前后发生了什么？"

**解决方案**：
用 CQL 语法快速检索错误日志，一键查看上下文，还原故障现场。

---

### 场景二：统计分析和容量规划

**典型问题**：

- "过去一周的日志量有多少？"
- "哪些服务报错最多？"
- "日志存储成本怎么优化？"

**解决方案**：
用 SQL 分析日志分布、错误类型统计，生成直方图展示趋势。

---

### 场景三：采集和机器组排障

**典型问题**：

- "日志为什么没采集上来？"
- "机器是否在线？采集配置对不对？"
- "机器组绑定了哪些采集规则？"

**解决方案**：
一键查询机器状态、采集配置、绑定关系，快速定位采集问题。

---

### 场景四：告警策略排查

**典型问题**：

- "告警为什么没触发？"
- "这个告警屏蔽规则是什么时候设置的？"
- "告警历史记录在哪里看？"

**解决方案**：
查询告警策略配置、执行历史、屏蔽规则，快速排查告警问题。

---

## 🚀 安装配置流程

### 前置条件

1. ✅ 已安装 WorkBuddy（如何安装？）
2. ✅ 有腾讯云账号并开通 CLS 服务
3. ✅ 有腾讯云 SecretId 和 SecretKey（[获取方式](https://console.cloud.tencent.com/cam/capi)）

---

### 步骤一：安装 Skill

####  从技能市场安装（推荐）
**安装步骤**：
1. **打开技能市场** - 在 WorkBuddy 左侧导航栏点击 **"技能"**

2. **搜索技能** - 在搜索框输入 `CLS` 或 `日志`，找到 **"腾讯云 CLS 助手"**

3. **一键安装** - 点击技能卡片上的 **"安装"** 按钮

4. **验证安装** - 安装完成后，技能出现在"已安装"列表，状态显示"已启用"

> 💡 **提示**：从市场安装的技能会自动配置，无需手动修改配置文件

---

### 步骤二：配置腾讯云凭证

#### 方式 A：配置环境变量（推荐）

**macOS/Linux (Zsh)**：

```bash
# 编辑 ~/.zshrc
echo 'export TENCENTCLOUD_SECRET_ID="你的SecretId"' >> ~/.zshrc
echo 'export TENCENTCLOUD_SECRET_KEY="你的SecretKey"' >> ~/.zshrc

# 生效配置
source ~/.zshrc
```

**Windows (PowerShell)**：

```powershell
# 设置系统环境变量
[Environment]::SetEnvironmentVariable("TENCENTCLOUD_SECRET_ID", "你的SecretId", "User")
[Environment]::SetEnvironmentVariable("TENCENTCLOUD_SECRET_KEY", "你的SecretKey", "User")
```

#### 方式 B：在 .env 文件中配置

```bash
# 创建配置文件
mkdir -p ~/.workbuddy/skills/tencentcloud-cls
cat > ~/.workbuddy/skills/tencentcloud-cls/.env << EOF
TENCENTCLOUD_SECRET_ID=你的SecretId
TENCENTCLOUD_SECRET_KEY=你的SecretKey
EOF
```

---

### 步骤三：验证安装

在 WorkBuddy 中输入：

```
查看我在广州地域的日志主题
```

如果看到日志主题列表，说明安装成功，这里需确认相关地域已有日志主题 ✅

常用地域代码：

| 地域  | Region  |
| - | - |
| 广州   | ap-guangzhou   |
| 上海   | ap-shanghai   |
| 北京   | ap-beijing   |
| 成都   | ap-chengdu   |
| 中国香港   | ap-hongkong   |
| 新加坡   | ap-singapore   |

完整地域列表请参考 [腾讯云地域列表](https://cloud.tencent.com/document/api/614/56474#.E5.9C.B0.E5.9F.9F.E5.88.97.E8.A1.A8)

---

## 🎯 典型场景：生产环境突发异常排查

### 📖 故事背景

**时间**：周五 17:30，准备下班时
**事件**：收到业务反馈，用户投诉页面加载慢，部分请求超时
**目标**：在 30 分钟内定位根因，给出解决方案

---

### 📊 排查路径图

```
17:30 🚨 收到告警
  │
  ▼
Step 1: 检索错误日志 → SearchLog: level:ERROR
  │
  ▼
Step 2: 分析错误分布 → SQL: GROUP BY service
  │
  ▼
Step 3: 查看上下文 → DescribeLogContext
  │
  ▼
Step 4: 对比日志趋势 → DescribeLogHistogram
  │
  ▼
🎯 定位根因：数据库连接池耗尽
  │
  ▼
Step 5: 检查采集链路 → DescribeMachines + DescribeConfigs
  │
  ▼
18:00 ✅ 问题解决
```

---

### 🔍 详细交互流程

#### Step 1：检索错误日志

**用户**：`查一下 ap-guangzhou 的 payment-topic 最近1小时的错误日志`

**AI 响应**：
```
发现 127 条错误日志，主要集中在：
- payment-service: DB_CONNECTION_TIMEOUT (89条)
- order-service: UPSTREAM_ERROR (31条)
- api-gateway: 502_BAD_GATEWAY (7条)
峰值错误率：12.3%（正常 < 1%）
```

---

#### Step 2：分析错误分布

**用户**：`统计 payment-service 的错误分布，按错误码分组`

**AI 响应**：
```
| 错误码 | 数量 | 占比 | 首次出现 |
|--------|------|------|----------|
| DB_CONNECTION_TIMEOUT | 89 | 70% | 17:25:00 |
| DB_QUERY_TIMEOUT | 28 | 22% | 17:26:00 |
| REDIS_TIMEOUT | 10 | 8% | 17:27:00 |

🔍 分析结论：数据库连接问题是主因
```

---

#### Step 3：查看上下文

**用户**：`展开第一条 DB_CONNECTION_TIMEOUT 的上下文，前后各10条`

**AI 响应**：
```
17:28:03 WARN  数据库连接池使用率 95%
17:28:05 WARN  等待数据库连接 timeout=5000ms
17:28:12 ERROR DB_CONNECTION_TIMEOUT 连接池已满
17:28:15 ERROR → 支付回调失败 reason=连接池耗尽

🔍 根因线索：连接池使用率从 95% 到耗尽仅用 2 分钟
```

---

#### Step 4：对比日志趋势

**用户**：`对比今天和昨天同时间段的日志量`

**AI 响应**：
```
时间段  今日    昨日    变化
17:00  12,345  8,234   +50%
17:15  18,678  8,567   +118%
17:30  45,231  8,890   +409% ⚠️ 异常激增
```

---

#### Step 5：检查采集链路

**用户**：`检查机器组状态和采集配置`

**AI 响应**：
```
机器组状态：✅ 2台机器在线，Agent 3.6.0
采集配置：✅ 配置正确，延迟 < 1s
结论：采集链路正常，日志完整
```

---

### 📋 排查总结

| 时间 | 动作 | 发现 |
|------|------|------|
| 17:30 | 检索错误日志 | 127 条错误，集中在 payment-service |
| 17:35 | 分析错误分布 | DB_CONNECTION_TIMEOUT 占 70% |
| 17:40 | 查看上下文 | 连接池使用率从 95% 到耗尽 |
| 17:45 | 对比日志趋势 | 流量激增 409%，疑似异常流量 |
| 17:50 | 检查采集链路 | 采集正常，无日志丢失 |

**根因**：异常流量导致数据库连接池耗尽，支付服务大面积超时

**解决方案**：
1. 扩容数据库连接池（临时）
2. 接入限流组件（长期）

---

## ⚠️ 常见误区与 Tips

### 误区 1：时间戳精度混淆

❌ **错误认知**：所有接口都用秒级时间戳

✅ **正确理解**：

- **SearchLog**: 毫秒级时间戳
- **DescribeLogHistogram**: 毫秒级时间戳
- **QueryRangeMetric**: 秒级时间戳
- **GetMetricLabelValues**: 秒级时间戳

**Tips**: 不确定时，直接说"过去1小时""过去24小时"，AI 会自动转换。

---

### 误区 2：DescribeLogContext 地域限制

❌ **错误认知**：所有地域都支持上下文检索

✅ **正确理解**：

- DescribeLogContext 的 From/To 参数**仅支持**：

    - 上海 (ap-shanghai)
    - 弗吉尼亚 (na-ashburn)
    - 新加坡 (ap-singapore)

- 其他地域会返回空结果

**解决方案**：
用 SearchLog 按时间范围 + Sort 排序模拟上下文查询。

---

### 误区 3：SQL 分析时使用 Limit 参数

❌ **错误做法**：

```python
# 错误：SQL 分析时 Limit 参数无效
SearchLog(..., QueryString="* | SELECT ...", Limit=10)
```

✅ **正确做法**：

```python
# 正确：在 SQL 中使用 LIMIT
SearchLog(..., QueryString="* | SELECT ... LIMIT 10")
```

**原因**：SQL 分析时，Sort/Limit/Offset 参数无效，需在 SQL 语句中指定。

---

### 误区 4：CQL vs Lucene 语法混淆

❌ **错误做法**：

```python
# 错误：混用语法
SearchLog(..., QueryString="level:ERROR", QuerySyntax=0)  # Lucene 模式下用 CQL 语法
```

✅ **正确做法**：

```python
# CQL 语法（推荐）
SearchLog(..., QueryString="level:ERROR", QuerySyntax=1)

# 或 Lucene 语法
SearchLog(..., QueryString="level:ERROR", QuerySyntax=0)
```

**Tips**：推荐统一使用 CQL (QuerySyntax=1)，功能更强大。

---

### 误区 5：忽略必需参数

❌ **错误示例**：

```python
# DescribeAlertRecordHistory 缺少必需参数
DescribeAlertRecordHistory(From=xxx, To=xxx)  # 缺少 Offset 和 Limit
```

✅ **正确做法**：

```python
# 补充必需参数
DescribeAlertRecordHistory(
    From=xxx,
    To=xxx,
    Offset=0,  # 必需
    Limit=20   # 必需
)
```

**Tips**: 让 AI 处理参数填写，避免手动调用时遗漏。

---

### Tips 1：自然语言检索更高效

不需要记住 CQL 语法，直接用自然语言：

```
✅ 推荐：查找包含 "timeout" 的错误日志
❌ 不推荐：SearchLog level:ERROR AND message:*timeout*
```

AI 会自动转换为正确的 CQL 语句。

---

### Tips 2：利用 SQL 分析能力

CLS 支持强大的 SQL 分析：

```
统计每个服务的错误数量
  → * | SELECT service, COUNT(*) as cnt WHERE level:ERROR GROUP BY service

查找最慢的 10 个请求
  → * | SELECT url, latency ORDER BY latency DESC LIMIT 10

计算错误率趋势
  → * | SELECT histogram(__TIMESTAMP__, interval 1h) as time,
           COUNT(*) as total,
           COUNT_IF(level:ERROR) as errors
       GROUP BY time ORDER BY time
```

---

### Tips 3：多主题检索

SearchLog 支持同时检索多个主题：

```python
# 同时检索 3 个主题
SearchLog(
    Topics=["topic-1", "topic-2", "topic-3"],
    From=xxx,
    To=xxx,
    QueryString="level:ERROR"
)
```

最多支持 50 个主题并发检索。

---

### Tips 4：保存常用查询

如果经常执行相同的查询，可以让 AI 记住：

```
记住：每天早上帮我检查昨天的错误日志数量
```

AI 会创建自动化任务，定时执行。

---

## 📚 相关资源

- [腾讯云 CLS 官方文档](https://cloud.tencent.com/document/product/614)
- [CQL 查询语法](https://cloud.tencent.com/document/product/614/47044)
- [API 文档](https://cloud.tencent.com/document/api/614/56480)

---

## 🤝 反馈与支持

遇到问题或有建议？

联系腾讯云 CLS 团队

---

**祝你使用愉快！** 🎉