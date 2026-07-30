# API 接口参考（搬运场景专用）

> 本文件保留「搬运式跟进记录同步」用得到的接口。全部经 omp-service MCP 转发；
> 其中 `get_user_info` 是 omp-service 的**通用工具**（直接调用），其余业务接口用 `request_api({ apiPath, data })`。

## 目录
- [0. 读取用户信息 get_user_info](#0-读取用户信息-get_user_info)
- [2. finalRole 计算规则](#2-finalrole-计算规则)
- [3. 客户搜索 + cid 名下校验 GetCustomerListForVisitForMcp](#3-客户搜索--cid-名下校验-getcustomerlistforvisitformcp)
- [3B. 商机（项目）搜索 + 负责人校验 list](#3b-商机项目搜索--负责人校验-list)
- [4. 查询签到打卡 GetVisitCheckInsListForMcp + 签到规则](#4-查询签到打卡-getvisitcheckinslistformcp)
- [5. 提交 AddCustomerVisitForMcp](#5-提交-addcustomervisitformcp)

---

## 0. 读取用户信息 get_user_info

omp-service 通用工具（**非** request_api）。既用于拿当前登录用户身份（作为"对象是否在你名下"一致性校验的比对基准），也用于**拿角色**。

`get_user_info` 的**主要用途是拿角色**：调用时传 `showDetail=true`，从返回 `detail.roles[]`（如 `sales` / `architect`）判断用户角色，再映射为 `finalRole`（用于字段校验；角色由后台自动处理，接口调用**无需传 `role` 参数**）：

| `detail.roles[]` 含 | finalRole |
|---|---|
| 销售族 `sales*` | `Sales` |
| 售前架构师族 `architect*` | `Owner` |

- 返回当前用户 rtx（英文名）+ 中文名等，存入 `SYNC_STATE.user`。`staffName` 应与 `USER` 一致，可作交叉校验。
- 商机侧比对负责人（businessManager 主销售 / architect 架构师 / projectMembers[].rtx 成员）时，用此处拿到的 rtx 做匹配。

---

## 2. finalRole 计算规则

从 `get_user_info` 返回的 `detail.roles[]` 角色标签**直接映射** `finalRole`（一步映射，角色由后台自动处理，`finalRole` 仅用于字段校验）：

| `detail.roles[]` 含 | finalRole（国内） |
|---|---|
| 销售族 `sales*`（`gw_dsales`/`gw_dsales_leader`/`gw_dsales_director`/`gw_dsales_gm`/`gw_sales_gm`/`gw_sales_leader`/`gw_channel_resale`/`gw_channel_resale_leader`/`gw_channel_resale_director`） | **`Sales`** |
| 售前架构师族 `architect*`（`gw_presales_sa`/`gw_presales_sa_leader`/`gw_presales_sa_director`） | **`Owner`** |

> 若同时含销售族和售前架构师族角色，按优先级取高（销售 Leader > 直销销售 > 售前 Leader > 售前架构师）。

> ⚠️ 计算出的 finalRole **不是 Sales 也不是 Owner** 时，按下面两种场景分别输出并终止：
> - **roles 非空但不含 `sales*`/`architect*`**（如产研架构师、分包、POC、VP、海外角色）→ 输出「本次版本仅支持销售和售前架构师，您的角色为 {finalRole}，暂不支持」
> - **roles 为空**（rare 兜底）→ 输出「当前用户为 {rtx}（{中文名}），但系统返回的角色标签为空（`roles: []`），无法判定您属于销售 (Sales) 还是售前架构师 (Owner)。本次版本仅支持销售和售前架构师使用。」

> ⚠️ 角色由后台自动处理，**提交接口与查询接口均无需传 `role` 参数**。

---

## 3. 客户搜索 + cid 名下校验 GetCustomerListForVisitForMcp

**apiPath：** `csm/GetCustomerListForVisitForMcp`

官方命名「查销售**及架构师**（包含leader）客户列表接口-MCP」。**本身按当前登录用户的销售/架构师权限过滤**，因此它既用于"把源文对象名模糊匹配到磐石客户"，又用于"cid 是否在你名下"的一致性校验。

```json
{
  "type": [1],
  "customer_name": "源文档中的对象名关键词",
  "cid": "校验场景下传选定的 cid（模糊搜索时不传）",
  "page": 1,
  "page_size": 100
}
```

> `type` 为数字数组：`[1]`=「我相关」，`[2]`=「长尾客户」。**无需传 `role`**（后台按登录态自动过滤销售/架构师权限）。

**两种用法：**
1. **模糊搜索**（Gate 3-A）：传 `customer_name`，**`type:[1]`（我相关）或 `type:[2]`（长尾）命中均可列候选给用户选**；`type:[1]` 为空时改查 `type:[2]`，长尾命中即可落定（直接允许，不额外校验权限）；`type:[1]` 与 `type:[2]` 均为空 → 拦截提示换实体（见 STEPS 3-A）。
2. **名下一致性校验**（Gate 3-A 第 5 步）：传 `cid`(选定) + `type:[1]`，返回列表**含该 cid = 在你名下**（你是它的销售或架构师）；不含 = 不在名下，走不一致处理。

**返回字段：** `list[].cid`（客户 CID）、`list[].customer_name`（磐石标准客户名）、`list[].gid`。

> ⚠️ 该接口返回**不含**销售/架构师姓名——一致性靠"cid 能否命中"判定，而非读取负责人字段。
> ⚠️ 客户详情 `csm/GetCustomerInfoByFields` 仅有主销售（business_manager / business_manager_name），**无架构师字段**，故不用于一致性校验；仅在需要向用户展示主销售中文名时可选调用。
> ⚠️ 严禁调用 `GetAssociationCustomerList`（无权限过滤）。

---

## 3B. 商机（项目）搜索 + 负责人校验 list

**apiPath：** `ltc.project/list`（MCP: omp-service）

商机（项目）列表。**商机 = 项目**。用于把源文里的商机/项目名或编号匹配到磐石商机，并读取负责人字段做名下一致性校验。

> ⚠️ **此接口不做「名下过滤」，返回全公司匹配结果（不传搜索词会拉全量 70 万+ 条）。是否「在你名下」不能靠「能不能查到」判断，必须靠返回里的 `businessManager` / `architect` / `projectMembers[].rtx` 三处字段核验。**

**两种搜索方式（择一）：**

① 按商机名称模糊搜（源文里给的是商机名）：
```json
{
  "name": "商机/项目名关键词（模糊）",
  "page": 1,
  "size": 100,
  "type": 12,
  "switchPanshiBase": 1,
  "projectArea": [0, 1]
}
```

② 按商机编号精确搜（源文里给的是项目编号，如 20250328690198）：
```json
{
  "code": "商机编号（精确）",
  "page": 1,
  "size": 20,
  "type": 12,
  "switchPanshiBase": 1,
  "projectArea": [0, 1]
}
```

> ⚠️ `projectArea: [0, 1]` 仅国内版传，海外版不传。`name` 只匹配名称、不匹配编号；编号必须走 `code` 参数。

**返回字段（`list[]` 每条）：**
- `code`：商机编码 = **项目编号**
- `name`：商机名称（= 项目名）
- `cId`：关联客户 CID（可与客户侧「李言」等对齐）
- `companyName`：关联客户名称
- `businessManager`：主销售（rtx，单值）
- `architect`：架构师（rtx，多值时逗号分隔；可能不存在此字段）
- `projectMembers[]`：项目成员数组，每项含 `rtx` / `roleName`（businessManager / projectShareMember 等）

**名下一致性校验（Gate 3-B 第 4 步）：**
`businessManager`(主销售) / `architect`(架构师，逗号分隔逐个比) / `projectMembers[].rtx`(任一成员) **三处之一 == 当前用户 rtx**（SYNC_STATE.user 的 rtx）→ 视为你负责/参与该商机，校验通过；三处都不是你 → 不在名下，走不一致处理（Gate 3-C，提示用户换商机名/编号重搜）。

> 💡 **实测确认**（prod）：编号 `20250328690198` 用 `code` 搜命中，`name`=「test测试商机报备流程专用测试202503」，`businessManager`=simonyanli，`projectMembers` 含 vickyzypan(projectShareMember)，命中「成员任一」规则 → 在名下，校验通过。
> ⚠️ **废弃通道**：`dcem/get_product_opp_entity_list`（仅海外可用）、`dcem/getOpportuntiyList`（依赖 CEM 用户体系，国内 prod 报「CEM 用户不存在」）。这两个国内 prod 都不通，禁止再用。

---

## 4. 查询签到打卡 GetVisitCheckInsListForMcp

**apiPath：** `csm/GetVisitCheckInsListForMcp`（MCP: omp-service）

用于需要关联打卡的场景（`type=10000` 拜访，或 Sales×`type=10002` 跟进进展非线索，见下方 shouldShowSignIn），查询用户名下**未填写跟进的**已有打卡记录，供用户选择关联。

> ✅ **该接口已对 MCP 开放**（实测：传 `type=1, role=Sales` 成功返回未关联打卡列表，含 `id/address/create_time/creator/cid/customer_name/is_bind_visit` 字段）。下方参数与字段名已据实校验，可直接调用。

> ⚠️ **PC 端只能查询已有打卡记录，禁止调用 `AddCustomerVisitCheckIns` 创建新打卡**（凭空造打卡 = 幻觉，违反铁律 #8）。用户若无可关联打卡，引导其去磐石小程序补打卡，或改用「跟进进展」方式。

**请求：**
```json
{
  "page": 1,
  "page_size": 10,
  "type": 1,
  "cid": "客户CID（客户类型时传入）",
  "address": "地址关键词（可选，按地址搜索过滤）"
}
```

**返回字段（重点取「打卡地址 + 签到时间」用于展示）：**
- `list[]`：可关联的打卡记录
  - `id`：打卡记录 ID，即关联跟进记录时写入的 `visit_check_ins_id`
  - `address`：**打卡地址**（展示给用户识别用）
  - `create_time`：**签到时间**（展示给用户识别用）
  - `creator`：打卡人
  - `attachment`：现场照片列表（含 `url`，可选）
- `total`：总数

**「未填写跟进的打卡」判定（业务口径）：**
> 每条跟进记录会用 `visit_check_ins_id` 记录它关联的那次打卡；每条打卡只能被关联一次。⚠️ **实测后端不会过滤已关联打卡**——返回 list 可能含 `is_bind_visit=1`（已绑定其他跟进）的记录。skill 侧必须：① **客户端过滤 `is_bind_visit=0`** 作为可关联候选，`is_bind_visit=1` 一律排除（重复关联会被后端 2001 拒绝）；② 仅保留最近 15 天；③ 展示过滤后的列表。

> 💡 **仅支持关联最近 15 天内的打卡记录，每条打卡记录只能被关联一次**（对齐磐石表单「关联打卡记录」弹窗）。

### 签到规则（isSignInRequired / shouldShowSignIn，按方式统一，不分角色）

**是否必填（isSignInRequired）：**
```
type=10000（拜访） → 签到必填（无论 Sales/Owner）
type=10002（跟进进展，非线索） → 非必填（无论 Sales/Owner）
```

**是否需要处理关联打卡（shouldShowSignIn）：**
```
  type=10000（拜访） → 显示（查列表让用户选，必填）
  type=10002（跟进进展）AND from_type≠12（非线索） → 显示（非必填，可跳过）
  线索(from_type=12) → 不显示（无需处理打卡）
```
> 打卡规则已改为**按方式统一，不分角色**：拜访必填、进展非必填（无论 Sales/Owner）。

| type | 是否显示/处理打卡 | 是否必填 |
|------|--------------|---------|
| 10000 拜访 | 是 | **必填**（不许跳过，无论角色） |
| 10002 跟进进展（非线索） | 是（查列表供选） | 非必填（可跳过，无论角色） |
| 10002 跟进进展 + 线索(from_type=12) | 否 | — |

---

## 5. 提交 AddCustomerVisitForMcp

**apiPath：** `csm/AddCustomerVisitForMcp`

MCP 专用提交接口。已通过 get_api_detail 核实的 schema 要点：

- root 必填：`base_info`(object)
- `base_info` 必填：`type`、`source`、`from_type`

**请求骨架（搬运场景，字段值全部来自源文原文，缺失留空）：**
```json
{
  "base_info": {
    "from_type": 1,
    "type": 10000,
    "source": 11,
    "cid": "用户在 Gate3 选定的客户 CID",
    "customer_name": "磐石标准客户名（来自搜索结果，非源文原名）",
    "visit_time": "YYYY-MM-DD HH:mm:ss（Gate3 确认后的时间字符串，禁止 Unix 时间戳）",
    "time_section": "noon",
    "location": "Gate3 确认后的地点原文（⚠️ 仅在同时传 visit_check_ins_id 时才传此字段；未关联打卡时绝对不传 location，否则 CRM 会将 location 值展示于「签到打卡」列造成假象）",
    "conclusion": "源文『沟通内容/纪要正文』原文照搬",
    "summary_type": "源文若写明纪要类型则填对应枚举，否则留空",
    "visit_check_ins_id": "Gate3.5 用户关联的打卡记录 id（进入过 Gate3.5 且已关联时传：type=10000 拜访，或 Sales×type=10002 跟进进展；未关联/未进入则不传）",
    "tx_participants": "源文『腾讯参与人』原文照搬（全部我方人员含当前用户），由 Gate 3⑦-C 提取",
    "collaborators": [
      { "name": "源文其他腾讯参与人姓名（不含当前用户）", "rtx": "源文写法里的 rtx（无则留空）", "rtx_role": "源文看出的角色（看不出留空）" }
    ]
  },
  "business_info": {
    "current_progress": "源文『当前进展』原文（type=10002 时）",
    "plan": "源文『下一步计划』原文",
    "main_risk": "源文『风险』原文",
    "pain_problem": "源文『痛点』原文",
    "product_difficult_point": "源文『产品卡点』原文",
    "meeting_address": "源文『会议地址』原文（如有）"
  },
  "contact_info": [
    { "name": "源文联系人姓名原文", "position": "枚举文字标签（如「市场负责人」，见 ENUMS.md；🔴 只能写枚举文字，严禁写菜单序号数字如「19」「20」，用户回序号时先还原成文字再写）", "is_decision_man": 0 }
  ],
  "goal_info": [
    { "goal_key": "源文拜访目标原文（如有）", "is_goal_reached": "源文是否达成（如有）" }
  ]
}
```

### 字段组装规则（搬运版）
```
1. from_type/type  → 数字。from_type 由 Gate 3② 识别结果决定：客户=1 / 商机(项目)=2；type 由 Gate 3⑥ 用户确认（10000 拜访 / 10002 跟进进展）
2. source          → 固定 11（crm-ai 对话）
3. 对象字段         → from_type=1（客户）传 cid + customer_name（磐石标准名）；from_type=2（商机）传项目编号(商机id) + 商机名，具体字段名以提交接口 schema 为准
4. visit_time      → 必须 'YYYY-MM-DD HH:mm:ss' **单一时刻**字符串（禁止时间范围如 `2026-07-02 16:00-17:00`、禁止 Unix 时间戳）；来自 Gate3 提取与格式化（非阻塞确认）；缺失时由用户补充，禁止默认当前时间
5. time_section    → 固定 'noon'（源文无时段信息时）
6. location        → 来自 Gate3 提取；**⛔ 与 visit_check_ins_id 强耦合：仅在有打卡关联时才传 location，未关联打卡时即使提取到了地点也绝对不传该字段**（CRM 前端会将 location 展示于「签到打卡」列，未关联打卡却传 location 会造成"假打卡"展示）
7. visit_check_ins_id → 进入过 Gate3.5 且用户关联了打卡时传（type=10000 拜访，或 Sales×type=10002 跟进进展非线索）；未关联/未进入 Gate3.5 则不传。Sales×拜访必须有值方可提交
8. 沟通内容按方式分流（均必填、原文照搬）：**拜访(10000) → `conclusion`**；**跟进进展(10002) → `current_progress`（即"项目当前进展"，= 源文沟通内容原文）**。plan/risk/pain/… 同理原文照搬，禁止改写。⚠️ 跟进进展缺 `current_progress` 后端报 2001「项目当前进展为必填项」
9. 任何源文读不到的字段 → 留空，绝不编造
10. collaborators / tx_participants → 来自 Gate 3⑦-C：collaborators 仅含「除当前用户外的其他腾讯人员」，每项 {name, rtx, rtx_role}（rtx/rtx_role 看不出则留空）；tx_participants 为全部我方参与人原文照搬。当前用户不重复入 collaborators；无协同人则 collaborators 整字段不传
```

> ⚠️ **提交体严禁项（实测踩坑，D2 验证）**：
> - **禁止在 base_info / 任何层级传 `null` 或无关字段**（如 `contact_info: null`、`cross_object: null`、`risk: null` 等）。实测：误传这些字段会干扰后端反序列化，导致 cid 解析异常、后端误报 `2022「未找到您名下的客户」` 的伪权限错。只传 schema 允许且本次有值的字段；无值字段**直接省略该 key**（不写 `null`、也不写空字符串占位）。
> - **2022 统一处理**：返回 `2022` 时**先去 null/无关字段重试**（伪错）；**重试仍报 `2022`/`4030` → 视为真权限错，走 `ask_user_authority` 友好引导**（申请链接+联系人），禁止冷拒绝。
> - 🔴 **`contact_info[].position` 只能写枚举文字标签**（如「市场负责人」「商务负责人」「其他」），**严禁写入菜单序号数字**（如「19」「20」）。用户以序号选择职位时，必须先按 ENUMS.md 菜单把序号还原成对应文字再写入。提交前自检：position 为纯数字或不在枚举文字列表内即视为未映射，禁止提交。
> - `current_progress` 仅跟进进展(10002) 场景必填；拜访(10000) 场景无此字段，不传。

**响应：** 返回 `base_info_visit_id`（跟进记录 id）。
提交成功后拼详情链接告知用户（dev 环境：`https://dev.panshi.woa.com/` 下的跟进记录详情，具体路径以现网为准）。

### 提交前校验
```
1. 角色 ∈ {Sales, Owner}          （Gate 2）
2. 对象类型已识别（标题优先）      （Gate 3②，客户/商机，不单独确认）
3. 对象已定位且【在你名下】       （Gate 3③：客户 cid 命中 / 商机 owner|sales|architect 命中；不一致已重选）
4. 确认 1 · 跟进对象实体确认       （Gate 3-D：类型+全称+CID/编号，含候选改选）
5. visit_time 已提取/格式化且（若可确定）在 15 天内   （Gate 3① / ④；Owner×跟进进展不传但仍做 15 天校验）
6. location 已提取（源文，非必填）；**⛔ 未关联打卡时不得传 location**  （Gate 3⑤ + Gate 5 耦合规则）
7. 跟进方式已识别（AI 判有无线下会面，不单独确认，在确认 2 可改判）      （Gate 3⑥）
8. 若 type=10000（拜访）：已按 Gate 3.5 静默查到候选打卡；**Sales×拜访必须已关联 visit_check_ins_id**（否则禁止提交）；**有关联打卡时才传 location**
9. 必填字段齐全（含拜访对象职位已补全） （见 FIELDS_MAPPING 各场景必填）
10. 确认 2 · 职位+打卡+预览一次性确认 → 调用 AddCustomerVisitForMcp
```
