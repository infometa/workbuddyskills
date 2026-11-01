# 数据标签子域 — 领域知识

> 本文说明数据标签子域的业务模型与状态（标签值/人群包的组织方式、状态机、规则表达式两种运行时格式），不描述传输细节；可调用能力与参数见 `apis/data-tag/`（查询与写操作契约文件），操作流程见 `flows/data-tag.md`。会员子域（会员/积分/等级/权益）的领域知识见 `references/domains/member-concepts.md` / `member-enums.md`。
> 数据标签域把会员特征组织为标签值与人群包：标签值可被规则计算或人群包成员命中；人群包是营销/促销定向的基础数据。

## 核心实体

- **标签分类**：只支持根分类与一层子分类（最多两层）；删除前必须没有关联标签。
- **标签**：`PRESET=1`、`RULE=2`、`MANUAL=3`、`ATTRIBUTE=4`、`METRIC=5`。规则与手工标签由运营维护；全局范围标签不可被普通租户编辑或删除。
- **标签值**：规则标签的每个值各自保存一份规则定义；手工标签的每个值必须绑定一个人群包。
- **人群包**：`RULE_SELECT=1`、`FILE_UPLOAD=2`、`DYNAMIC=3`。规则圈选、文件上传、动态加入均属当前开放写范围。
- **文件上传人群包**：CSV/TXT 单列 ID 清单（≤50MB），按 `convertType`（权威枚举：0=UID / 1=OPEN_ID / 2=W_UID / 3=UNION_ID / 4=手机号，官方模板默认手机号；⚠️ **2=W_UID 与 3=UNION_ID 当前后端未实现，传入将全部行失败，勿使用**——实际可用仅 0/1/4）转换匹配会员；官方模板表头行（uid/openid/phone）自动跳过；导入异步执行（任务记录核验）；**APPEND 追加仅允许 DYNAMIC / FILE_UPLOAD 类型**（规则圈选包禁止，避免规则重算冲掉）；失败明细按任务落 COS（人群包级别 download-fail=最近一次，task-download-fail=按次历史）。
- **动态人群包**：创建后立即可用；新增成员同步写入成员位图，面向 C 端标签命中的异步同步存在秒级延迟。

## 人群包状态机

```
规则圈选：CALCULATING(1) → ONLINE(2) 或 FAILED(4)
文件上传：INIT(0) → CALCULATING(1) → ONLINE(2) 或 FAILED(4)（轮询期间详情可能短暂返回 status=0，属正常中间态）
ONLINE(2) → OFFLINE(3) → ONLINE(2，仅周期性规则圈选与动态人群包)
OFFLINE(3) → INVALID(5)（OFFLINE 满足 365 天后由定时任务自动失效）
任意存在态 → 删除（不可恢复）
动态人群包：创建即 ONLINE(2)
```

- 规则圈选提交成功只代表任务已受理，**不代表人群已生效**。用任务记录与详情轮询：当前实现的任务记录 `status=0` 为处理中、`1` 为成功、`2` 为失败；只有人群 `ONLINE=2` 且最新任务为 `1` 才可报告完成；人群 `FAILED=4` 或最新任务为 `2` 报失败原因。注意这与同模块未被本接口使用的 `CrowdTaskStatus` 六值枚举漂移，以运行时写入值为准。
- 上线只允许 OFFLINE；文件上传和单次规则圈选（计算周期 NONE=0）下线后不能重新上线，周期性规则圈选与动态人群包可重上。下线只允许 ONLINE，且会影响促销活动的触达面。

## 规则表达式：两种不可混用的运行时格式

### 规则标签的 `tagValues[].valueDefine`

运营端规则标签编辑器保存兼容格式。每个规则项的 `dimension` 是被引用标签的十进制 ID；服务缓存层将 `dimension` 反查为英文列名并转换为运行时 V2 规则（也容忍直接传英文列名，但应传 ID）。`field` 是被引用标签的 **tagType 分类**（`"1"`=预置 / `"2"`=规则 / `"4"`=属性 / `"5"`=指标）——**前端编辑回显依赖此字段渲染维度下拉和启用标签选择器，缺失会导致编辑表单维度空白、标签选择器禁用**；创建时必须携带。每个组合只能使用统一 `ruleLogic`，组合之间只能使用统一 `combinationLogic`（**仅 `AND` / `OR` 两态**，非 AND 一律按 OR 处理）；**不要传** `ruleLogics` 或 `combinationLogics`，当前缓存转换会静默忽略它们，不能表达独立相邻逻辑。规则项 `value` 匹配的是被引用标签的**标签值名称**（`tag.search` 的 `tagValList[].tagValue`）。⚠️ dimension 反查不到英文名的规则被**静默跳过**（该标签值条件缺失、可能永不命中）——**规则标签命中无运营端查询面**（`tag.user-values` 仅返回手工标签命中，不能用来验证规则标签），如需抽查规则标签命中请联系平台侧提供引擎查询通道。

```json
{"combinations":[{"rules":[{"dimension":"6400000000000000001","field":"5","operator":"eq","value":"1"}],"ruleLogic":"AND"}],"combinationLogic":"AND"}
```

> 示例中 `field: "5"` 表示引用的是指标标签（tagType=5）；引用规则标签时用 `"2"`、属性标签用 `"4"`、预置标签用 `"1"`。

### 人群包的 `queryCondition`

人群计算器的前端组合格式只读取规则项 `tagId`，不读取 `dimension` 或历史 `field`。计算器将 tagId 反查为标签英文名后计算位图——**标签必须存在且已配置英文名（tagNameEn），否则整次圈选报错**。人群包支持可选 `ruleLogics` / `combinationLogics` 数组表示相邻规则/组合的独立逻辑（`logics[i]` 为第 i 与第 i+1 项之间的逻辑，优先于标量逻辑字段）。`EXCEPT`、`AND_NOT`、`ANDNOT` 都表示差集，其他未知**逻辑**会静默按 AND 处理，因此只能使用 `AND`、`OR`、`EXCEPT`；但未知**运算符**会直接报错（不静默）。运算符 `in`/`not_in` 的 `value` 为逗号分隔多值、`between` 为恰好两值逗号分隔（`"min,max"`）；`eq` 值为 `0`/`0.0` 时服务端自动补「或为空」（数值型标签兼容）。

```json
{"combinations":[{"rules":[{"tagId":"6400000000000000001","operator":"eq","value":"1"}],"ruleLogic":"AND"}],"combinationLogic":"AND"}
```

运算符和可引用标签须先查询；值类型、日期与取值格式以返回的标签定义为准。不要把对象直接传到 `valueDefine` / `queryCondition`，二者都是 JSON 字符串。

服务端还兼容旧标准格式：`rules[]`（每项含 `seq`、`dimType`、`dimValue`、`operator`、`conditionValue`）配 `expression`（如 `"1&2"`）。开放能力只发布与现行运营端一致的 combinations 格式，禁止把两种格式字段混用。

## 跨域引用

```
标签值 / 人群包 ──> 促销活动 SPECIFIED 定向（audienceTagValueIds）
口令购活动 ──> 动态人群包 ──> 批量加入命中会员 ──> 促销触达
```

促销域使用的是标签值 ID，不是标签 ID。创建/更新定向前先查询标签详情，取得正确 `tagValues[].id`；人群包下线或删除前应明确告知可能影响已经引用它的标签和活动。
