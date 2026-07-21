# LSP 补偿与路径敏感分析

> 引用方：agents/vuln-scan.md、agents/logic-scan.md、agents/red-team.md

---

## 第一部分：LSP 不可达场景补偿

### 问题背景

LSP 在反射调用、动态代理、AOP 切面、IoC 注入、消息驱动、MyBatis XML 等场景中会失效。这些是现代 Java/Spring、Node.js、Python 项目的核心机制。

此外，部分语言完全无可用 LSP（如 Kotlin，jdtls 不支持 Kotlin），此类项目整体走 `Grep+AST` 降级路径（tree-sitter 提供 AST 精度），traceMethod 上限为 95。

### 补偿策略总览

#### 一级断崖（高频，必须补偿）

| 场景 | 补偿策略 | 每个断点预算 |
|------|---------|-----------|
| 反射调用（Method.invoke, Class.forName） | Grep 反射目标字符串，关联真实方法 | 3 次工具调用 |
| 动态代理（Proxy, cglib） | 找 InvocationHandler/MethodInterceptor 实现 | 3 次 |
| AOP 切面（@Around/@Before/@After） | 枚举切面，解析切入点表达式，构建切面-方法映射 | 3 次 |
| IoC 接口注入（@Autowired） | goToImplementation + Grep implements，找默认实现 | 2 次 |
| 消息驱动（@KafkaListener） | 枚举生产者/消费者，按通道名称关联 | 3 次 |
| MyBatis XML Mapper | namespace 关联接口，检测 `${}` 占位符 | 3 次 |

#### 二级断崖（中频，条件补偿）

| 场景 | 补偿策略 |
|------|---------|
| 动态路由（Gateway, Zuul） | 解析路由配置，追加到 entryPoints |
| 模板引擎（Thymeleaf, Jinja2） | 提取模板变量，追踪 Controller 赋值 |
| 隐式绑定（@ModelAttribute） | 检测敏感字段暴露，验证 DTO 分离 |
| 事件驱动（ApplicationEvent） | 按事件类型关联发布-订阅 |

### indexer 预侦察

indexer 在广度枚举阶段检测以下维度，产出两层数据：

1. **布尔标记 + 文件列表** -> `stage1-context.json > frameworkImplicitBehaviors`
2. **完整桥接映射** -> `project-index.db > framework_bridges` 表

| 维度 | Grep 探针 | framework_bridges |
|------|---------|-----------------|
| AOP 切面 | `@Aspect`; XML `aop:config` | 含切入点和安全效果 |
| 消息队列 | `@KafkaListener/@RabbitListener` | 生产者-通道-消费者映射 |
| MyBatis XML | `Glob *Mapper.xml` + `namespace=` | 接口-XML + `${}` 检测 |
| 动态代理 | `InvocationHandler/MethodInterceptor` | -- |
| 反射调用 | `Class.forName/Method.invoke` | -- |
| 模板引擎 | `Glob *.ftl *.vm` + `th:utext` | -- |
| 隐式绑定 | `@ModelAttribute` | -- |
| 事件驱动 | `ApplicationEventPublisher/@EventListener` | -- |

当 `framework_bridges` 可用时，扫描 Agent 可直接查询跳过补偿 Grep+Read（每断点省 2-3 次调用）。

### LSP 补偿置信度影响

| 补偿结果 | 攻击链可达性上限（维度 1） |
|---------|----------------------|
| `resolved` | 35 分 |
| `partially-resolved` | 28 分 |
| `unresolved` | 18 分 |

与扫描 Agent 置信度上限取较低者。

### 预算控制

补偿总预算不超过扫描 Agent 总工具调用量的 **15%**。

优先级：MyBatis XML > AOP 切面 > 消息通道 > 反射 > 实现类枚举 > 隐式绑定 > 其他。

补偿预算从子任务总预算中划拨，不额外增加。

---

## 第二部分：路径敏感分支条件分析

### 核心原则

在 LSP 数据流追踪中遇到分支结构时，显式分析每个可达路径上的防御状态和数据可控性。不要求构建完整 CFG，在关键分析点对分支条件做定向推理。

### 分析触发条件

| 触发条件 | 判断方式 |
|---------|---------|
| Sink 位于分支内部 | Read 上下文 +-30 行检查 if/else/switch/try |
| 防御代码位于分支内部 | sanitizer/validator 在条件块中 |
| 提前返回/异常抛出 | return/throw/exit 在条件块中 |
| 安全检查后多路径 | true/false 分支处理不同 |

未触发时按原有路径不敏感方式处理。

### 分支类型

- **类型 A 条件防御**：`if(isValid)` 分支有防御，else 分支无防御
- **类型 B 条件 Sink**：Sink 仅在特定条件分支可达
- **类型 C 异常处理缺陷**：`try { auth() } catch { log only }` 后继续执行敏感操作
- **类型 D 提前返回**：多个提前 return 后到达 Sink，需验证检查是否充分
- **类型 E Switch/模式匹配**：不同 case 安全处理不一致

### 分支条件可控性

| 条件类型 | 可控性 |
|---------|--------|
| 用户输入直接比较 | 高 |
| 间接比较（user.getRole()） | 中 |
| 服务端状态/环境变量 | 低 |
| 异常条件 | 中 |
| Null 检查 | 高 |

### 判定矩阵

| 分支可控性 | Sink 可达 | 有效防御 | 判定 |
|-----------|----------|---------|------|
| 高 | 是 | 否 | 漏洞确认（高置信度） |
| 高 | 是 | 是 | 安全路径 |
| 低 | 是 | 否 | 漏洞存在（低置信度） |
| 中（异常路径） | 是 | 否 | 漏洞确认（中置信度） |
| -- | 否 | -- | 非漏洞 |

### 与现有流程集成

- **vuln-步骤1**：Read Sink 上下文时同时识别分支结构
- **vuln-scan 防御检查**：判断防御是否在所有路径生效
- **verifier.py chain-verify**：验证防御是否覆盖所有可达路径
- **verifier-步骤1**：攻击链深度验证时评估分支条件

### 路径敏感置信度调整

| 路径分析结论 | 维度 1 调整 |
|------------|-----------|
| 所有路径均可达无防御 | 无调整 |
| 特定路径可达，可控性高 | -2 分 |
| 特定路径可达，可控性中 | -5 分 |
| 特定路径可达，可控性低 | -10 分 |
| 仅异常路径可达 | -5 分 |

> **注意**：路径敏感置信度调整与 LSP 补偿置信度影响叠加，两者均作用于维度 1（攻击链可达性）。

### 预算控制

路径敏感分析不额外增加工具调用（基于已有 Read 做推理增强）。仅 High/Critical finding 可触发每个 finding 最多 2 次额外 Read。
