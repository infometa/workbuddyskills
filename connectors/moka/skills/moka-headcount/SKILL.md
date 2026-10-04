---
name: moka-headcount
display_name: Moka 招聘需求
display_name_en: Moka Headcount
description: Moka 招聘需求查询。查询招聘系统的招聘需求清单、各状态数量、名额（HC）进度与单个需求详情，以及人事系统内的招聘需求业务单据列表与详情。两者是完全独立的两套业务数据。当用户问招聘需求进度、剩余 HC、各状态需求数量，或要查人事侧的招聘需求单据时使用。
description_zh: 面向招聘负责人与人事伙伴的招聘需求查询。一边是招聘系统的招聘需求：清单、各状态数量、名额进度（HC 需求人数/已招/剩余）与单个需求详情；另一边是人事系统内的招聘需求业务单据：列表、详情与同步结果。两者是完全独立的两套业务数据。当用户问「我有哪些进行中的招聘需求」「需求都在什么状态、各有多少个」「这个需求还剩多少 HC」「人事里的招聘需求单据有哪些」时使用。
description_en: Headcount lookup for recruiting owners and HR partners. On one side, headcounts in the recruiting system - the list, per-status counts, progress (needed/hired/remaining) and single-headcount details; on the other, headcount business forms inside the HR system - list, details and sync results. The two are completely independent datasets. Use it for questions like "which of my headcounts are in progress", "how many headcounts are in each status", or "what headcount forms exist in the HR system".
category: productivity
version: 1.0.0
author: Moka
---

# 招聘需求查询

查招聘需求的名额（HC）进度与状态分布，以及人事系统内的招聘需求业务单据。只编排以下两个工具：

- `mcp__moka__list_hiring_requirements`
- `mcp__moka__get_recruit_requirements`

## 选择工具

**最重要的一条：两个工具查的是两套完全独立的业务数据，标识互不关联、不能互查。**`mcp__moka__list_hiring_requirements` 查询招聘系统的招聘需求；`mcp__moka__get_recruit_requirements` 查询人事系统内的招聘需求业务单据——它与 `mcp__moka__list_hiring_requirements` 查询的招聘需求是两套完全独立的数据，标识互不关联、不能混用。具体来说：

- 一边的需求 ID 绝不能传给另一边查详情——即使名称、编号看起来像同一件事。
- 两边的数量不要相加，也不要拿一边的数字去「核对」另一边；数字对不上是正常的，因为本来就是两套数据。
- 回答里同时出现两边时，各自说清数据来源（招聘系统的需求 / 人事系统的业务单据），不要合并陈述。

分流规则：

- 「我有哪些进行中的招聘需求」「需求都在什么状态、各有多少个」「这个需求招到几个了、还剩几个名额」：招聘视角，用 `mcp__moka__list_hiring_requirements`。
- 「人事里的招聘需求业务单据有哪些」「打开这条业务单据看详情」「哪些单据同步失败了」：人事单据视角，用 `mcp__moka__get_recruit_requirements`。
- 用户没说清是哪一边时，默认按招聘视角理解（问进度、HC、招聘状态的都是招聘侧）；只有明确提到人事系统、业务单据或同步结果时才走人事侧。

概念辨析：**职位 vs 招聘需求**——需求是「要招几个人（HC 名额）、招得怎么样了」，职位是对外发布的岗位与要求。问职责要求、JD、发布情况是职位问题，这些问题应由当前可用的其他 Moka 工具处理；统计候选人在流程各阶段的人数同理。

## 常见问题速查

- 「我有哪些进行中的招聘需求」→ `mcp__moka__list_hiring_requirements`（status 过滤）
- 「需求各状态各有多少个」→ `mcp__moka__list_hiring_requirements`，直接读 counts
- 「这个需求招到几个了、还剩几个名额」→ `mcp__moka__list_hiring_requirements`（列表定位后 `action="detail"`）
- 「人事里的招聘需求单据有哪些」→ `mcp__moka__get_recruit_requirements`（列表模式）
- 「这条业务单据的详情/同步结果」→ `mcp__moka__get_recruit_requirements`（传本工具列表返回的 id）

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. `mcp__moka__list_hiring_requirements` 的详情走两段式：先 `action="list"`（缺省）查清单拿到返回项的 requirementId，再用同一工具 `action="detail"` 带 requirementId 查单个需求详情（进度、负责人、汇报对象、关联职位、学历要求与需求描述）。
3. `mcp__moka__get_recruit_requirements` 是自己的双模式：不传 id 分页查列表，传 id 查详情——id 只能来自**本工具**列表返回的 requirementId，不能拿招聘侧的需求 ID 来传；id 与列表筛选参数不能同时传。
4. 读 `mcp__moka__list_hiring_requirements` 的数字要分清口径：counts 是七个状态（进行中/未开始/已完成/已暂停/已取消/已超时/草稿）各自的数量、不受 status 入参影响；total 是当前筛选条件（含 status）下的总数。
5. 回答「某状态有几个」直接读 counts 里对应的数字，不必为每个状态各查一次；回答「一共有多少个需求」用不传 status 时的 total。
6. `mcp__moka__list_hiring_requirements` 不传招聘模式时统计的是全部模式（社招+校招）。用户没有明确说「社招」「校招」时不要自行加模式过滤——那会静默缩小口径。
7. 只传用户明确给出的条件（状态、关键词、日期、部门等），不自行扩展；相对日期按用户所在时区换算成绝对日期再调用，回答里说明实际查询口径。
8. 需要翻很深的清单时优先用状态、关键词或招聘模式缩小范围，而不是逐页翻到底。

## 结果与权限

- 空列表一律按「未返回数据」如实说明，不据此反推权限，也不断言「没有需求/单据」。
- 招聘侧的统计范围是当前账号有权限查看的需求，不等于「你创建的」或「你负责的」；不同账号看到的数字可能不同。
- 招聘侧某个状态计数为 0，表示该状态下没有当前账号有权限查看的需求，转述时保留这一层含义。
- 草稿状态的可见范围与其余六个状态不同，两边数字对不上时以 total 为准。
- 人事侧部分字段（职务名称、招聘方式、员工类型等）的具体业务语义未经业务侧确认，转述时按返回文本原意表达，不做引申解读。
- 人事侧详情返回的是经过敏感字段过滤的可读字段与同步结果；同步失败时如实转达失败原因文本，不自行归因。
- 工具返回的 notices 与 message 是数据解读须知，先读再组织回答，如实转达，不自行改写归因。
- 两边都只读：不支持新建、修改、审批、导出、同步重试或状态变更，这些操作需要用户在 Moka 页面完成。

## 安全边界

- 不向用户展示访问令牌、内部标识符或原始技术响应；需求 ID、页码只用于串联工具，不出现在回答里。
- 只使用工具返回的字段组织回答，不虚构需求进度、负责人或同步结果。
- 需求数据按当前账号权限范围返回，不扩散与提问无关的部门或负责人信息。
- 隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 面向用户的回答只用业务语言：没数据说「没有查到」，不引用参数名、状态值或字段名。
- 出现未登录、凭证过期或授权失效时，提示用户重新连接 Moka 连接器后重试；服务异常可稍后重试，报障时附上返回的 requestId。
