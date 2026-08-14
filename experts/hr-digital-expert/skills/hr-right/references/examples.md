# 输出示例集

本文件包含 `SKILL.md` 中所有输出示例，供 AI 在处理用户请求时参考格式。

---

## 版本A：新增场景 (type=0) 输出示例

适用于以下两种子场景：
1. **全新申请**：角色和权限包均未持有 → 角色和权限包的 `isNewApply` 均为 `true`
2. **已有角色追加权限包**：角色已持有、权限包未持有 → 角色 `isNewApply = false`，待新增权限包 `isNewApply = true`

---

### 示例一：角色仅有单个分工维度，仅有规则生成权限包（无自主申请）

| 填单项 | 内容 |
|--------|------|
| **申请场景** | 新增 |
| **申请角色** | 校招简历筛选员角色（`Recruit_ResumeFilter_Campus`） |
| **组织范围** | IEG互动娱乐事业群 / 天美工作室群 / 天美J3工作室 / C-Game项目组 |
| **默认权限包** | 校招简历筛选员（`Recruit_ResumeFilter_Campus`）<br>（默认权限包根据角色授权范围和申请人信息自动计算得出，请以实际生效结果为准） |
| **申请原因** | （用户原始需求文本） |

> 说明：角色 `role_division_dim = "组织"`，仅1个维度 → **单维度场景**，维度名"组织范围"直接作为填单项列名。因不涉及自主申请权限包和期限，相关行不展示。

---

### 示例二：角色有多个分工维度，自主申请权限包必选维度含非组织维度

| 填单项 | 内容 |
|--------|------|
| **申请场景** | 新增 |
| **申请角色** | 核心人事海外BA角色（`hr_core_oversea_ba`） |
| **角色范围** | 【组织】：S3职能系统－HR与管理线<br>【工作地】：全部<br>【在职状态】：全部<br>【合同公司所在地】：全部 |
| **默认权限包** | 核心人事海外BA（`hr_core_oversea_ba`）<br>（默认权限包根据角色授权范围和申请人信息自动计算得出，请以实际生效结果为准） |
| **自主申请权限包** | 业务分析-海外薪酬（`BA_oversea_CB`） |
| **自主申请权限包范围** | 【组织】：腾讯 / CSIG / xxx中心<br>【管理职级(含空码值)】：全部<br>【专业职级】：全部<br>【合同地】：亚太<br>【工作地】：亚太 |
| **自主申请权限包期限** | 2026-04-01 ~ 2027-03-31 |
| **申请原因** | （用户原始需求文本） |

> 说明：
> - 角色有多个分工维度，部分通过瀑布填充得到"全部"
> - 自主申请权限包展示了 `pkg_required_ctrl_dim` 中列出的全部5个必选维度及其各自的具体值
> - **合同地/工作地 = "亚太"**：用户需求中提到"APAC地区"或"亚太"，经步骤①-A 地域类维度三级码表解析，匹配到码表中 L2 层级节点「亚太」（`dim_item_code` 为该节点真实编码），包含其下所有国家（含港澳台）。输出时使用码表实际存在的节点编码和名称，不构造聚合编码

---

### 示例三：地域类维度 — 全球除大中华区/除港澳台扩充（APAC→全海外）

> 场景：用户持有 `Wagesalary_COE_oversea`（激励COE-海外角色）下原仅限 APAC 的薪酬权限，现基于兼岗海外整体 CoE 需求，将合同地/工作地从 APAC 扩充至所有海外国家（全球除大中华区/港澳台）。此场景为 **type=1（变更）**——已有权限包、范围发生变化。

| 填单项 | 内容 |
|--------|------|
| **申请场景** | 变更 |
| **申请角色** | 激励COE-海外角色（`Wagesalary_COE_oversea`） |
| **角色范围** | 【组织】：S3职能系统－HR与管理线 / 薪酬福利部<br>【合同地】：亚太；美洲；欧洲；中东及非洲<br>【工作地】：亚太；美洲；欧洲；中东及非洲 |
| **自主申请权限包** | 薪酬COE-海外（`Wagesalary_COE_oversea`） |
| **自主申请权限包范围** | 【组织】：全部<br>【管理职级(薪酬专用)】：全部<br>【专业职级】：全部<br>【合同地】：亚太（不含港澳台）；美洲；欧洲；中东及非洲 ⚠️ 已从原"亚太"扩充至全部4个海外大洲区域(L2)，亚太仅保留除港澳台外的所有L3国家节点，排除中国大陆整棵子树及港澳台<br>【工作地】：亚太（不含港澳台）；美洲；欧洲；中东及非洲<br>【在职状态】：全部<br>【管理主体】：全部<br>【员工类型】：全部<br>【员工子类型】：全部 |
| **申请原因** | 基于兼岗海外整体CoE的需求，申请将原先局限在APAC地区的薪酬权限扩充至所有海外国家（全球除大中华区/除港澳台地区），覆盖薪酬激励政策和周期性业务方案落地所需的全部海外地区薪酬数据访问能力。 |

> 说明：
> - **地域类维度解析过程（步骤①-A）**：
>   1. 用户需求关键词 = "所有海外国家（全球除大中华区/除港澳台地区）"
>   2. 匹配地域映射表 → 命中 **"全球除大中华区且除港澳台"** 模式
>   3. 展开为4个L2区域集合：**亚太、美洲、欧洲、中东及非洲**；其中"亚太"需进一步细化到L3层级并排除港澳台
>   4. 最终输出：亚太输出为**排除港澳台后的所有L3国家节点**（日本、韩国、新加坡等），其余3个大洲保留L2节点
>   5. 排除范围 = 中国大陆整棵子树 + 亚太下的港澳台3个L3节点（香港/澳门/台湾）
>   6. 最终输出的每个 `dimItemCode` / `dimItemName` 均来自 `v_ai_data_scope` 码表中的真实节点
> - **变更标识**：因权限包已持有、本次仅为范围扩大 → type=1（变更）
> - JSON 组装中 `operationType` 设置为 `"Update"`，`rowId` 使用已有授权记录的行ID

---

### 示例五：自主申请权限包某必选维度瀑布填充失败

| 填单项 | 内容 |
|--------|------|
| **申请场景** | 新增 |
| **申请角色** | 数据资源使用角色（`Data_Management_HRIS`） |
| **组织范围** | 腾讯 / CSIG / xxx中心 |
| **默认权限包** | （该角色下所有规则生成权限包）<br>（默认权限包根据角色授权范围和申请人信息自动计算得出，请以实际生效结果为准） |
| **自主申请权限包** | 规则库_规则查看（`Hrule_User_Sens`） |
| **自主申请权限包范围** | 【规则目录】：⚠️ 无法自动填充，需用户手动选择（瀑布式三级填充均无结果） |
| **申请原因** | （用户原始需求文本） |

> 说明：该权限包 `pkg_required_ctrl_dim` 包含"规则目录"这一必选维度（非组织维度）。瀑布式填充三级均无结果，但因是必选维度，仍然必须展示并标注无法自动填充。

---

### 示例六（新增子场景）：已有角色，追加新权限包

> 场景：用户已持有 `Data_Management_HRIS` 角色，现需在该角色下新增申请 `dos_sys_data` 权限包。此场景为 **type=0（新增）** 的第二种子场景——角色不变、权限包新增。

| 填单项 | 内容 |
|--------|------|
| **申请场景** | 新增 |
| **申请角色** | 数据资源使用角色（`Data_Management_HRIS`） |
| **自主申请权限包** | DOS_配置管理员（`dos_sys_data`） |
| **自主申请权限包范围** | 【DOS数据源】：hrcore / hrmd / hrdw / ds-r-pg-hrcore / ds-r-pg-hrmd-md3 / ds-r-pg-hrdw-dpc / dw3-tbase-dpc |
| **申请原因** | （用户原始需求文本） |

> 说明：
> - 角色已持有 → 表单中角色 `isNewApply = false`
> - 权限包未持有 → 该权限包 `isNewApply = true`
> - 整体 type=0（新增），因为对 `dos_sys_data` 而言是全新申请
> - 无规则生成权限包行、无角色范围行（角色已有无需重复设置）

**对应 JSON 组装**：

```json
{
  "roleFormItemList": [
    {
      "roleCode": "Data_Management_HRIS",
      "roleName": "数据资源使用角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "dos_sys_data",
          "packageName": "DOS_配置管理员",
          "maxExpire": 12,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "dos_data_source",
                  "dimTypeName": "DOS数据源",
                  "items": [
                    { "dimItemCode": "hrcore", "dimItemName": "核心人事(hrcore)" },
                    { "dimItemCode": "hrmd", "dimItemName": "主数据(hrmd)" }
                  ]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2026-04-14",
              "endDate": "2027-04-14",
              "rowId": null,
              "operationType": null
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，不删减）"
}
```

---

## 版本B：变更/续期场景 (type=1 / type=2) 输出示例

适用于以下场景：
- **type=1（变更）**：用户已有有效授权，本次涉及范围维度变化（权限包本身已有授权，需修改其范围或有效期）
- **type=2（续期）**：用户已有有效授权，本次仅涉及有效期变化（范围不变，仅延长/更新到期日）

---

### 示例七：变更场景 — 多组分工下的组织范围扩大 + 期限延长

> 场景：用户已持有招聘经理角色（RecruitmentManager），在 `query_staff_role_right` 中存在**两组有效授权记录**：一组管理主体为「集团本部」、另一组为「全资-直管+投资公司+全资-其他」。用户描述需求为：「组织范围从 PCG平台与内容事业群/在线视频BU 扩大到再加社交平台与应用线」。
>
> **关键判断（跨组传播规则）**：查询发现两组的变更前组织范围**均为**「PCG平台与内容事业群/在线视频BU」，与用户描述的变更前值完全匹配 → 根据**关键规则第3条（变更值跨组传播）**，该组织范围的扩大操作需**同时应用于两组**。此场景为 **type=1（变更）**。

| **填单项** | 内容 |
|--------|------|
| **场景** | type=1（变更） |
| **角色** | 招聘经理角色（`RecruitmentManager`） |
| **角色范围1** | 变更前：<br>【管理主体】：集团本部；<br>【员工子类型】：（15个子类型）；<br>【组织范围】：PCG平台与内容事业群 / 在线视频BU；<br>【工作地】：全部<br><br>变更后：<br>【管理主体】：集团本部；<br>【员工子类型】：（15个子类型）；<br>【组织范围】：PCG平台与内容事业群 / 在线视频BU；PCG平台与内容事业群 / 社交平台与应用线；<br>【工作地】：全部 |
| **角色范围2** | 变更前：<br>【管理主体】：全资-直管、投资公司、全资-其他；<br>【员工子类型】：（15个子类型）；<br>【组织范围】：PCG平台与内容事业群 / 在线视频BU；<br>【工作地】：全部<br><br>变更后：<br>【管理主体】：全资-直管、投资公司、全资-其他；<br>【员工子类型】：（15个子类型）；<br>【组织范围】：PCG平台与内容事业群 / 在线视频BU；PCG平台与内容事业群 / 社交平台与应用线；<br>【工作地】：全部 |
| **默认权限包** | 招聘经理、HR资格面试官、伯乐HR资格面试官、猎头HR资格面试官（默认权限包根据角色授权范围和申请人信息自动计算得出，请以实际生效结果为准） |
| **自主申请权限包** | 部门默认招聘经理（`RecruitmentManager_Department`） |
| **自主申请权限包范围** | 变更前：<br>【组织范围】：PCG平台与内容事业群 / 在线视频BU；<br>【工作地】：全部<br><br>变更后：<br>【组织范围】：PCG平台与内容事业群 / 在线视频BU；PCG平台与内容事业群 / 社交平台与应用线；<br>【工作地】：全部 |
| **自主申请权限包期限** | 2025/2/13～2026/05/01<br>2026/04/14～2027/05/01 |
| **申请说明** | 【岗位职责】负责 PCG平台与内容事业群 / 社交平台与应用线；申请部门主招聘经理权限 【申请原因】职责调整，申请招聘经理权限 |

> 说明：
> - **跨组传播（关键规则第3条）**：用户描述的变更前组织范围「PCG平台与内容事业群/在线视频BU」**同时出现在两组有效分工中**，因此组织范围扩大操作同步应用到两组——两组的变更后值完全一致
> - **多组分工来源**：`query_staff_role_right` 返回了该角色的两条有效授权记录（rowId 分别为 12345 和 12347），对应两个不同的管理主体分组
> - **变更前信息补全**：各维度的变更前值来自 `query_staff_role_right` 已有授权记录，即使用户未逐维度描述修改前值也需完整展示
> - 两组的组织范围均从单一BU扩大到两个BU → type=1（变更）
> - JSON 组装中 `roleDataScopes` 包含**两个元素**，分别对应两行的 `rowId`，每个元素的 `operationType` 均为 `Update`

**对应 JSON 组装**：

```json
{
  "roleFormItemList": [
    {
      "roleCode": "RecruitmentManager",
      "roleName": "招聘经理角色",
      "isNewApply": false,
      "roleDataScopes": [
        {
          "dataScopeDimItems": [
            { "dimTypeCode": "ManageEntity", "dimTypeName": "管理主体", "items": ["集团本部"] },
            { "dimTypeCode": "StaffSubType", "dimTypeName": "员工子类型", "items": [/* 15个子类型码值 */] },
            { "dimTypeCode": "Org", "dimTypeName": "组织范围", "items": [/* 含新增的社交平台与应用线路径 */] },
            { "dimTypeCode": "WorkLocation", "dimTypeName": "工作地", "items": ["ALL"] }
          ],
          "memberFrom": "apply",
          "startDate": null,
          "endDate": null,
          "rowId": 12345,
          "operationType": "Update"
        },
        {
          "dataScopeDimItems": [
            { "dimTypeCode": "ManageEntity", "dimTypeName": "管理主体", "items": ["全资-直管", "投资公司", "全资-其他"] },
            { "dimTypeCode": "StaffSubType", "dimTypeName": "员工子类型", "items": [/* 15个子类型码值 */] },
            { "dimTypeCode": "Org", "dimTypeName": "组织范围", "items": [/* 含新增的社交平台与应用线路径 */] },
            { "dimTypeCode": "WorkLocation", "dimTypeName": "工作地", "items": ["ALL"] }
          ],
          "memberFrom": "apply",
          "startDate": null,
          "endDate": null,
          "rowId": 12347,
          "operationType": "Update"
        }
      ],
      "rightPackageList": [
        {
          "packageCode": "RecruitmentManager_Department",
          "packageName": "部门默认招聘经理",
          "maxExpire": 12,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                { "dimTypeCode": "Org", "dimTypeName": "组织范围", "items": [/* 变更后：含新增路径 */] },
                { "dimTypeCode": "WorkLocation", "dimTypeName": "工作地", "items": ["ALL"] }
              ],
              "memberFrom": "apply",
              "startDate": "2026-04-14",
              "endDate": "2027-05-01",
              "rowId": 12348,
              "operationType": "Update"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "【岗位职责】负责 PCG平台与内容事业群 / 社交平台与应用线；申请部门主招聘经理权限 【申请原因】职责调整，申请招聘经理权限"
}
```

---

### 示例八：变更场景 — 新增一组分工（Insert）⭐

> 场景：用户已持有招聘经理角色（RecruitmentManager）下的部门默认招聘经理权限包，已有1组有效授权记录：管理主体=集团本部、组织范围=PCG平台与内容事业群/在线视频BU、工作地=深圳。现用户描述需求为：「我想**新增**负责 PCG平台与内容事业群/社交平台与应用线的招聘经理权限」。
>
> **关键判断（关键规则第4条）**：
> - 用户措辞为「**新增**」（非「从A改到B」）
> - 用户新求的组织范围「PCG平台与内容事业群/社交平台与应用线」与已有组（PCG/在线视频BU）不匹配
> - → 判定为 **type=1（变更）— 新增一组分工子场景**

| **填单项** | 内容 |
|--------|------|
| **场景** | type=1（变更） |
| **角色** | 招聘经理角色（`RecruitmentManager`） |
| **角色范围1** | 新增一组分工<br><br>变更后：<br>【管理主体】：集团本部；<br>【员工子类型】：（15个子类型）；<br>【组织范围】：PCG平台与内容事业群 / 社交平台与应用线；<br>【工作地】：深圳、广州 |
| **默认权限包** | 招聘经理、HR资格面试官、伯乐HR资格面试官、猎头HR资格面试官（默认权限包根据角色授权范围和申请人信息自动计算得出，请以实际生效结果为准） |
| **自主申请权限包** | 部门默认招聘经理（`RecruitmentManager_Department`） |
| **自主申请权限包范围** | 新增一组分工<br><br>变更后：<br>【组织范围】：PCG平台与内容事业群 / 社交平台与应用线；<br>【工作地】：全部 |
| **自主申请权限包期限** | 2026/04/14～2027/05/01 |
| **申请说明** | 【岗位职责】负责 PCG平台与内容事业群 / 社交平台与应用线；申请部门主招聘经理权限 【申请原因】职责调整，申请招聘经理权限 |

> 说明：
> - **Add 模式**：行标签为「新增一组分工」，内容栏仅展示新增组的维度值（无变更前值），右侧标注「变更后」
> - 已有的其他分工组（PCG/在线视频BU那组）不在本次表格中展示
> - JSON 中 `operationType = "Add"`，**不需要 `rowId`**
> - 角色和权限包的 `isNewApply` 均为 `false`（已有角色下新增分工，非新建角色）

**对应 JSON 组装**：

```json
{
  "roleFormItemList": [
    {
      "roleCode": "RecruitmentManager",
      "roleName": "招聘经理角色",
      "isNewApply": false,
      "roleDataScopes": [
        {
          "dataScopeDimItems": [
            { "dimTypeCode": "ManageEntity", "dimTypeName": "管理主体", "items": ["集团本部"] },
            { "dimTypeCode": "StaffSubType", "dimTypeName": "员工子类型", "items": [/* 15个子类型码值 */] },
            { "dimTypeCode": "Org", "dimTypeName": "组织范围", "items": [/* PCG平台与内容事业群 / 社交平台与应用线路径 */] },
            { "dimTypeCode": "WorkLocation", "dimTypeName": "工作地", "items": ["深圳", "广州"] }
          ],
          "memberFrom": "apply",
          "startDate": null,
          "endDate": null,
          "rowId": null,
          "operationType": "Add"
        }
      ],
      "rightPackageList": [
        {
          "packageCode": "RecruitmentManager_Department",
          "packageName": "部门默认招聘经理",
          "maxExpire": 12,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                { "dimTypeCode": "Org", "dimTypeName": "组织范围", "items": [/* PCG平台与内容事业群 / 社交平台与应用线路径 */] },
                { "dimTypeCode": "WorkLocation", "dimTypeName": "工作地", "items": ["ALL"] }
              ],
              "memberFrom": "apply",
              "startDate": "2026-04-14",
              "endDate": "2027-05-01",
              "rowId": null,
              "operationType": "Insert"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "【岗位职责】负责 PCG平台与内容事业群 / 社交平台与应用线；申请部门主招聘经理权限 【申请原因】职责调整，申请招聘经理权限"
}
```

---

### 示例九：续期场景 — 仅有效期变化

> 场景：用户已有的核心人事海外BA角色的业务分析-海外薪酬权限包即将到期，本次仅需续期（范围不变，仅延长有效期）。此场景为 **type=2（续期）**。

| **填单项** | 内容 |
|--------|------|
| **场景** | type=2（续期） |
| **角色** | 核心人事海外BA角色（`hr_core_oversea_ba`） |
| **自主申请权限包** | 业务分析-海外薪酬（`BA_oversea_CB`） |
| **自主申请权限包范围** | （范围无变化，省略对比展示）<br>当前范围：【组织】：腾讯 / CSIG / xxx中心；【合同地】：亚太；【工作地】：亚太 |
| **自主申请权限包期限** | 2026-04-01～2027-03-31<br>2027-04-01～2028-03-31 |
| **申请说明** | （用户原始需求文本） |

> 说明：
> - **续期标识**：仅有效期变化，范围维度无任何改动 → type=2（续期）
> - 范围行简化展示：因无变化，仅列出现有值作为参考，不做前后对比
> - JSON 组装中 `operationType` 可设置为 `"Update"`（更新有效期），`rowId` 使用原记录行ID
> - 续期场景下若系统支持独立的续期操作类型，也可使用专门的续期标识

---

## 使用说明

1. **新增场景**参考示例一至示例六
2. **变更场景**参考示例七至示例八
3. **续期场景**参考示例九
4. 每个示例包含：表格输出格式 + JSON组装示例（部分）
5. 示例中的 `⭐` 标记表示关键优化点，`⚠️` 标记表示注意事项

---

# 第二部分：JSON 组装示例（最后一步：调用 `submit_apply_form`）

> 本部分覆盖所有写操作场景的 `RoleRightApplyFormDTO` JSON 完整组装示例。
> SKILL.md 主文件中以引用方式指向本部分对应小节。

## J-1. 新增场景（type=0 + Add）— JSON 示例

**场景**：申请未持有的角色 + 多个权限包（含规则生成 + 自主申请）。

```json
// 调用：submit_apply_form(type=0, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "Recruit_ResumeFilter_Campus",
      "roleName": "校招简历筛选员角色",
      "isNewApply": true,
      "roleDataScopes": [
        {
          "dataScopeDimItems": [
            {
              "dimTypeCode": "Org",
              "dimTypeName": "组织范围",
              "items": [
                { "dimItemCode": "IEG-TM-J3-CGame", "dimItemName": "C-Game项目组" }
              ]
            }
          ],
          "memberFrom": "apply",
          "startDate": null,
          "endDate": null,
          "rowId": null,
          "operationType": "Add"
        }
      ],
      "rightPackageList": [
        {
          "packageCode": "Recruit_ResumeFilter_Campus",
          "packageName": "校招简历筛选员",
          "maxExpire": null,
          "packageDataScopes": []
        },
        {
          "packageCode": "BA_oversea_CB",
          "packageName": "业务分析-海外薪酬",
          "maxExpire": 12,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "Org",
                  "dimTypeName": "组织范围",
                  "items": [
                    { "dimItemCode": "CSIG-xxx", "dimItemName": "xxx中心" }
                  ]
                },
                {
                  "dimTypeCode": "contractCompany_place",
                  "dimTypeName": "合同公司所在地",
                  "items": [
                    { "dimItemCode": "AP", "dimItemName": "亚太" }
                  ]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2026-04-14 23:59:59",
              "endDate": "2027-04-14 23:59:59",
              "rowId": null,
              "operationType": "Add"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，不删减）"
}
```

> ⚠️ **注意**：示例中的 `dimItemCode`（如 `"AP"`、`"CSIG-xxx"`）为占位说明，**实际生成时必须先通过 `v_ai_data_scope` 码表查询确认实际编码**，禁止直接复制本示例的编码。

---

## J-2. 变更场景（type=1）— JSON 示例

变更场景包含两类子场景，**operationType 严格区分**：

| 子场景 | operationType | rowId | 适用情况 |
|---|---|---|---|
| 修改已有记录的范围 | `"Update"` | ✅ 必填 | 调整某条已有记录的维度码值 |
| 在已有角色下追加一组新分工 | `"Add"` | ❌ 否（传 `null`） | 已有角色下新增一组维度组合 |

### J-2.1 变更示例 1：修改已有记录的范围（Update）

**场景**：用户已持有 BA-HRIS 角色下 `hrrightMgr` 权限包的某条记录（rowId=778277），现需把范围扩大新增"反舞弊领域"。

```json
// 调用：submit_apply_form(type=1, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "BA_HRIS",
      "roleName": "BA-HRIS角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "hrrightMgr",
          "packageName": "权限中台_超级管理员",
          "maxExpire": null,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "Org",
                  "dimTypeName": "组织",
                  "items": [{ "dimItemCode": "Org-All", "dimItemName": "全公司" }]
                },
                {
                  "dimTypeCode": "sysdata",
                  "dimTypeName": "权限接入系统清单",
                  "items": [{ "dimItemCode": "global", "dimItemName": "全部（含有效、失效和空值）" }]
                },
                {
                  "dimTypeCode": "flowcodes",
                  "dimTypeName": "权限流程类型",
                  "items": [{ "dimItemCode": "global", "dimItemName": "全部（含有效、失效和空值）" }]
                },
                {
                  "dimTypeCode": "hrrightDomain",
                  "dimTypeName": "权限包领域（旧）",
                  "items": [
                    { "dimItemCode": "10", "dimItemName": "人员领域" },
                    { "dimItemCode": "11", "dimItemName": "福利领域" },
                    { "dimItemCode": "14", "dimItemName": "薪酬领域" },
                    { "dimItemCode": "30", "dimItemName": "其他（反舞弊/内审/BG发文等)" }
                  ]
                },
                {
                  "dimTypeCode": "hr_role_domain",
                  "dimTypeName": "HR角色和权限所属领域",
                  "items": [{ "dimItemCode": "global", "dimItemName": "全部（含有效、失效和空值）" }]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2025-10-22",
              "endDate": "2026-12-01",
              "rowId": 778277,
              "operationType": "Update"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，如：BA-HRIS 角色下 hrrightMgr 权限包扩展支持反舞弊领域）"
}
```

> **关键**：
> - `rowId=778277` 必填，定位到要改的那一行
> - `operationType="Update"`
> - `dataScopeDimItems` 是**变更后的完整维度集合**（不只是新增的部分，要把不变的维度也原样带上）

### J-2.2 变更示例 2：在已有角色下追加一组新分工（Add）

**场景**：用户已持有"招聘经理角色"下针对"PCG/在线视频BU"的一组分工，现需**新增**针对"PCG/社交平台与应用线"的另一组分工（不修改原有那组）。

```json
// 调用：submit_apply_form(type=1, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "RecruitmentManager",
      "roleName": "招聘经理角色",
      "isNewApply": false,
      "roleDataScopes": [
        {
          "dataScopeDimItems": [
            {
              "dimTypeCode": "ManageEntity",
              "dimTypeName": "管理主体",
              "items": [{ "dimItemCode": "101", "dimItemName": "集团本部" }]
            },
            {
              "dimTypeCode": "Org",
              "dimTypeName": "组织范围",
              "items": [{ "dimItemCode": "PCG-SAB", "dimItemName": "PCG平台与内容事业群 / 社交平台与应用线" }]
            },
            {
              "dimTypeCode": "WorkLocation",
              "dimTypeName": "工作地",
              "items": [{ "dimItemCode": "ALL", "dimItemName": "全部" }]
            }
          ],
          "memberFrom": "apply",
          "startDate": null,
          "endDate": null,
          "rowId": null,
          "operationType": "Add"
        }
      ],
      "rightPackageList": [],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，如：在招聘经理角色下新增 PCG / 社交平台与应用线的分工）"
}
```

> **关键**：
> - `rowId=null`（新行无历史 ID）
> - `operationType="Add"`
> - 这是**追加一行**，原有的 PCG/在线视频BU 那行不会被修改也不需要在本次 JSON 中出现

---

## J-3. 续期场景（type=2 + Update）— JSON 示例

> ⚠️ **核心约定**：**续期接口与变更接口传入的信息结构完全一致**——使用相同的 `RoleRightApplyFormDTO` JSON 结构、相同的字段含义、相同的 `operationType` 取值。**唯一区别仅是 `submit_apply_form` 的 `type` 参数不同（续期=`2`，变更=`1`）**。

### 字段约定

| 字段 | 续期场景取值 | 说明 |
|---|---|---|
| `submit_apply_form.type` | `2` | 唯一与变更（`1`）不同的地方 |
| `roleFormItemList[].isNewApply` | `false` | 角色已持有，不重复申请 |
| `packageDataScopes[].rowId` | **必填**，使用 `query_staff_role_right` 返回的原 `rowId` | 定位待续期记录 |
| `packageDataScopes[].dataScopeDimItems` | **原样回传**已有记录的全部维度值 | 不修改任何维度码值 |
| `packageDataScopes[].startDate` | 原值或新的起始时间 | 通常为原值；若用户要求重置则改 |
| `packageDataScopes[].endDate` | **新的结束时间**（按 `max_member_expiration` 计算） | 续期的核心变化点 |
| `packageDataScopes[].operationType` | `"Update"` | 与变更场景一致 |
| `packageDataScopes[].memberFrom` | 原值（通常为 `"apply"`） | 原样回传 |

### 续期 vs 变更的判断口径

- **续期（type=2）**：**仅 `endDate` 变化**，所有 `dataScopeDimItems` 维度码值集合无任何增删改
- **变更（type=1）**：维度码值集合发生变化（增/删/改任一码值都算）；`endDate` 可能同时变也可能不变

### 续期 JSON 示例

```json
// 调用：submit_apply_form(type=2, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "Data_Management_HRIS",
      "roleName": "数据资源使用角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "Hrule_User_Sens",
          "packageName": "规则库_规则查看",
          "maxExpire": 12,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "business_rule_catalog",
                  "dimTypeName": "规则目录",
                  "items": [
                    { "dimItemCode": "Menu_Data_Rule", "dimItemName": "数据规则" }
                  ]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2026-12-26",
              "endDate": "2027-12-26",
              "rowId": 815234,
              "operationType": "Update"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，不删减，例如：规则库_规则查看 即将到期，申请续期一年）"
}
```

> **关键提示**：
> - 上面 JSON 与「变更场景」**100% 同构**，唯一区别是调用 `submit_apply_form` 时传 `type=2`
> - `dataScopeDimItems` 中的所有维度码值与 `query_staff_role_right` 返回的原值**完全一致**
> - `endDate` 是新的到期日期；`startDate` 通常保持原值
> - 不要因为"是续期"就省略 `dataScopeDimItems` 或 `rowId`——这两个字段必须原样回传

---

## J-4. 删除场景（type=1 + Delete）— JSON 示例

### J-4.1 权限包级 Delete：清理某权限包下的某一条记录

**场景**：清理 BA-HRIS 角色下 hrrightMgr 权限包的某一条记录（rowId=24521）

```json
// 调用：submit_apply_form(type=1, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "BA_HRIS",
      "roleName": "BA-HRIS角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "hrrightMgr",
          "packageName": "权限中台_超级管理员",
          "maxExpire": null,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "Org",
                  "dimTypeName": "组织",
                  "items": [{ "dimItemCode": "Org-All", "dimItemName": "全公司" }]
                },
                {
                  "dimTypeCode": "hrrightDomain",
                  "dimTypeName": "权限包领域（旧）",
                  "items": [{ "dimItemCode": "1", "dimItemName": "BP领域" }]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2025-10-22",
              "endDate": "2026-12-01",
              "rowId": 24521,
              "operationType": "Delete"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，不删减）"
}
```

### J-4.2 角色级 Delete：删除某个角色下的某条角色级分工记录

```json
// 调用：submit_apply_form(type=1, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "Recruit_InterviewerNew",
      "roleName": "国内面试官角色",
      "isNewApply": false,
      "roleDataScopes": [
        {
          "dataScopeDimItems": [
            {
              "dimTypeCode": "Org",
              "dimTypeName": "组织",
              "items": [{ "dimItemCode": "4791", "dimItemName": "S3职能系统－HR与管理线/人力资源平台部" }]
            }
          ],
          "memberFrom": "rule",
          "startDate": null,
          "endDate": null,
          "rowId": 4608420,
          "operationType": "Delete"
        }
      ],
      "rightPackageList": [],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本，不删减）"
}
```

**关键字段说明**：
- `operationType`：固定为 `"Delete"`
- `rowId`：**必填**，使用 `query_staff_role_right` 返回的原 `rowId`
- `dataScopeDimItems`：**必须原样回传**待删除记录的原维度值（不能传空，便于后端审计核对）
- `startDate / endDate`：原样回传待删除记录的原值
- `roleFormItemList[].isNewApply`：固定为 `false`
- `rightPackageList`：仅放本次涉及删除的权限包；该角色下未涉及删除的其他权限包**不要放**（避免被误处理）

---

## J-5. 多意图场景：拆任务 vs 不拆任务 JSON 示例

> ⚠️ **核心提示**：**不存在所谓"多意图独立 JSON"**——
> - 拆任务时：每笔单据各用各场景的标准 JSON（参见 J-1 ~ J-4），分别提交
> - 不拆任务时：在**同一笔** `submit_apply_form` 内，多个 `roleDataScopes` / `packageDataScopes` 元素并存，operationType 各取所需

### J-5.1 必须拆任务示例（不同命令 / 不同 type）

**场景**：用户说「**把 hrrightMgr 权限包的 rowId=24521（BP领域）那条删掉，并且申请新增"流程引擎_数据分析员"权限**（用户当前未持有该权限包）」

- 子任务 1：`(submit_apply_form, type=1, Delete)`
- 子任务 2：`(submit_apply_form, type=0, Add)`
- → type 不同 → **拆**

**子任务 1：删除已有记录（type=1 + Delete）**

```json
// 调用：submit_apply_form(type=1, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "BA_HRIS",
      "roleName": "BA-HRIS角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "hrrightMgr",
          "packageName": "权限中台_超级管理员",
          "maxExpire": null,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "Org",
                  "dimTypeName": "组织",
                  "items": [{ "dimItemCode": "Org-All", "dimItemName": "全公司" }]
                },
                {
                  "dimTypeCode": "hrrightDomain",
                  "dimTypeName": "权限包领域（旧）",
                  "items": [{ "dimItemCode": "1", "dimItemName": "BP领域" }]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2025-10-22",
              "endDate": "2026-12-01",
              "rowId": 24521,
              "operationType": "Delete"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "清理 BA-HRIS 角色下 hrrightMgr 权限包 BP领域 这条记录"
}
```

**子任务 2：新增权限（type=0 + Add）**

```json
// 调用：submit_apply_form(type=0, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "Approval_Workflow_HRIS",
      "roleName": "审批流资源使用角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "workflow_data_analyst",
          "packageName": "流程引擎_数据分析员",
          "maxExpire": 12,
          "packageDataScopes": [
            {
              "dataScopeDimItems": [
                {
                  "dimTypeCode": "datascope_area_app_process",
                  "dimTypeName": "业务流程(流程引擎)",
                  "items": [{ "dimItemCode": "root", "dimItemName": "全部" }]
                }
              ],
              "memberFrom": "apply",
              "startDate": "2026-04-30 23:59:59",
              "endDate": "2027-04-30 23:59:59",
              "rowId": null,
              "operationType": "Add"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "申请流程引擎_数据分析员权限"
}
```

> **执行顺序**：
> 1. 告知用户：「此次需求涉及多个独立操作（无法用单次 MCP 调用完成），需拆分为 2 笔依次处理：先处理【删除 hrrightMgr/BP领域 那条记录】，完成后再启动【新增 流程引擎_数据分析员 权限】。」
> 2. 处理子任务 1 → 输出删除场景填单表 → 等用户确认 → 调用 `submit_apply_form (type=1)` → 告知"子任务 1 已完成"
> 3. 等用户回复肯定词 → 处理子任务 2 → 输出新增场景填单表 → 等用户确认 → 调用 `submit_apply_form (type=0)`

### J-5.2 不拆任务示例（同命令同 type，对应标准案例 #4 / #5）

**场景**：用户说「**针对 hrrightMgr 权限包：删掉 BP领域那条（rowId=24521），同时在该权限包下新增一组维度组合（管理主体=集团本部、组织=CSIG）**」

- 子操作 1：`(submit_apply_form, type=1, Delete)` — packageDataScopes 内
- 子操作 2：`(submit_apply_form, type=1, Add)` — 同一 packageDataScopes 内
- → 同命令同 type → **不拆，组装一笔**

```json
// 调用：submit_apply_form(type=1, data=<以下JSON>)
{
  "roleFormItemList": [
    {
      "roleCode": "BA_HRIS",
      "roleName": "BA-HRIS角色",
      "isNewApply": false,
      "roleDataScopes": [],
      "rightPackageList": [
        {
          "packageCode": "hrrightMgr",
          "packageName": "权限中台_超级管理员",
          "maxExpire": null,
          "packageDataScopes": [
            // 元素 1：删除原 BP领域 那条
            {
              "dataScopeDimItems": [
                { "dimTypeCode": "Org", "dimTypeName": "组织", "items": [{ "dimItemCode": "Org-All", "dimItemName": "全公司" }] },
                { "dimTypeCode": "hrrightDomain", "dimTypeName": "权限包领域（旧）", "items": [{ "dimItemCode": "1", "dimItemName": "BP领域" }] }
              ],
              "memberFrom": "apply",
              "startDate": "2025-10-22",
              "endDate": "2026-12-01",
              "rowId": 24521,
              "operationType": "Delete"
            },
            // 元素 2：在该权限包下追加一组新分工
            {
              "dataScopeDimItems": [
                { "dimTypeCode": "ManageEntity", "dimTypeName": "管理主体", "items": [{ "dimItemCode": "101", "dimItemName": "集团本部" }] },
                { "dimTypeCode": "Org", "dimTypeName": "组织", "items": [{ "dimItemCode": "CSIG", "dimItemName": "CSIG" }] }
              ],
              "memberFrom": "apply",
              "startDate": "2026-04-30 23:59:59",
              "endDate": "2027-04-30 23:59:59",
              "rowId": null,
              "operationType": "Add"
            }
          ]
        }
      ],
      "checkData": null
    }
  ],
  "applyReason": "（用户原始需求文本）"
}
```

> **执行顺序**：
> 1. 直接组装上述**单笔** JSON
> 2. 输出**一张**填单表格（包含两个子操作的明细），让用户确认
> 3. 用户肯定回复后调用**一次** `submit_apply_form (type=1)`
> 4. **不要拆成两次调用**——这种情况后端能一次完成

---

## J-6. 弱校验二次确认 JSON 示例（带 `confirmReusltMap`）

> 触发条件：`submit_apply_form` 返回 `success=false` 且 `data` 字段含"弱校验场景"四字。
> 详细处理流程参见 SKILL.md 主文件「弱校验二次确认」节。

### 第一次后端返回（典型弱校验提示）

```json
{
  "success": false,
  "code": "-1",
  "msg": "本次申请只涉及授权范围的缩小，无需经过审批，提交后会立即生效,请确认是否提交!",
  "data": "弱校验场景，提示用户是否确认操作，key:后端校验给出的提示信息，value:用户是否确认操作..."
}
```

### 用户确认后第二次提交（带 `confirmReusltMap`）

```json
{
  "roleFormItemList": [ /* 与第一次提交完全一致 */ ],
  "applyReason": "（用户原始需求文本，与第一次提交完全一致）",
  "confirmReusltMap": {
    "本次申请只涉及授权范围的缩小，无需经过审批，提交后会立即生效,请确认是否提交!": true
  }
}
```

> **关键约束**：
> - `confirmReusltMap` 的 key 必须是后端 msg 的**完全原文**（标点/空格/感叹号一字不差）
> - `roleFormItemList` 和 `applyReason` 必须与第一次完全一致
> - **禁止 AI 自动确认**——必须等用户回复肯定词后才能补 `confirmReusltMap` 重提

---

# 第三部分：典型交互 Case

> 本部分约束 LLM 的**对话风格与交互体感**（不是数据结构）。每个 Case 提供"用户原话 → 错误回应 → 正确回应"对照。主文档 [1.4 典型交互 Case](./SKILL.md#14-典型交互-case输出风格约束) 已包含其中 5 个高频 Case；本部分提供完整 8 个 Case（含边界场景）。

## Case 1：标准新增申请 — 不暴露内部推理

**用户**：「帮我申请招聘经理的权限」

❌ **不应该**（暴露分数与方案选择）：
> 「执行步骤一三方案并行识别。方案一角色搜索匹配到 `RecruitmentManager_role`（得分 95），方案二权限包搜索得分 60，方案三系统反查得分 35。最高分方案：方案一。执行步骤一.5 调用 `role_apply_validation`...」

❌ **也不应该**（把内部步骤名说给用户）：
> 「步骤一完成。现在进入步骤一.5 资格校验...」

✅ **应该**：
> 「好的，已查到「招聘经理角色」，下面是申请填单内容，请确认：
> [填单表格]
> 确认无误请回复"确认"，需要调整请告诉我。」

**约束总结**：所有方案选择、分数比较、MCP 调用、字段映射、内部步骤名等**对用户不可见**。LLM 的输出 = 同事帮忙办事的回应，不是给开发者看的执行日志。

---

## Case 2：用户表述模糊 — 不自由发挥，反问澄清

**用户**：「取消我那个 BBS 相关的」

❌ **不应该**（擅自选一种执行不可逆操作）：
> 「好的，已为您清理 BBS 内容运营角色下的所有权限包」（直接 `clear_role_package`）

❌ **也不应该**（猜测但不告诉用户）：
> 「已为您撤回 BBS AI 审核的申请单据」（直接 `revoke_apply_form`）

✅ **应该**：
> 「您是想：① **清理已生效**的『BBS 相关』权限授权（不可逆），还是 ② **撤回审批中**的『BBS 相关』申请单据？另外，您说的"BBS 相关"是指 BBS 内容运营角色，还是 BBS AI 审核权限包？」

**约束总结**：表述存在多种含义/对象时**必须反问**，不得猜测；`clear_role_package` 不可逆，猜错代价极高。反问要把候选选项**明确编号列出**，并说明操作差异（不可逆 vs 可撤销）。

---

## Case 3：用户已提供完整信息 — 不要重复问

**用户**：「给我加上招聘经理角色下 PCG/社交平台与应用线 这一组分工，3 个月有效期」

❌ **不应该**：
> 「请问您要申请的是哪个角色？维度值是什么？期限要多久？」

❌ **也不应该**（部分重复问）：
> 「您提到的招聘经理角色，是 RecruitmentManager_role 吗？维度值"PCG/社交平台与应用线"是要扩展还是替换？」

✅ **应该**：直接走流程，输出填单表格，等待确认。
> 「已根据您的需求生成填单内容：
> - 角色：招聘经理角色
> - 新增分工：PCG/社交平台与应用线
> - 期限：3 个月
> [完整填单表格]
> 请确认。」

**约束总结**：用户已明确给出的信息（角色名、维度值、期限）**禁止重新询问**；只有真正缺失的字段（如必选维度未提及）才反问。对于 SQL 能自动 disambiguate 的（如角色名→角色编码），LLM 内部完成即可。

---

## Case 4：失败/无结果场景 — 给出可行建议，不甩锅

**用户**：「帮我申请数据科学家的权限」（系统中无此角色）

❌ **不应该**（终结式回应）：
> 「三方案识别均为 0 分，未匹配到结果。」

❌ **也不应该**（暴露内部细节）：
> 「方案一 SQL 查询 `ai_role_def` 表无匹配，方案二 / 方案三同样无结果。」

✅ **应该**：
> 「没找到名为「数据科学家」的角色。您可以：
> 1. 描述您想做的具体工作（如"想查看招聘数据报表"），我帮您找对应角色
> 2. 告诉我您的同事中谁有这个权限，我帮您参照申请
> 3. 也可以让我列出您当前可申请的全部角色，您挑一个看看」

**约束总结**：失败场景**必须给出 2-3 条可行的下一步**，而不是把"找不到"作为终点。建议要从用户视角出发（"想做什么工作"），不是从系统视角出发（"调哪个 tool"）。

---

## Case 5：写操作前 — 永远等用户显式回复

**场景**：LLM 已输出填单 → 用户没回复，又问了别的：「顺便看下我现在有什么权限」

❌ **不应该**（把新问题当默认确认）：
> （静默提交了申请单据，然后回答查询请求）

❌ **也不应该**（强迫用户先回应）：
> 「请先回复刚才的填单是否确认，我才能帮您查权限」

✅ **应该**：
> 「先帮您查当前权限：[权限清单...]
> 顺便提醒：刚才的招聘经理申请填单还在等您确认是否提交，需要我现在提交吗？」

**约束总结**：用户的新问题**不构成对前一个填单的确认**；LLM 应**并行处理**（查询请求可以做，写操作必须等显式确认）。永远不要为了"推进对话流畅"而把模糊状态判为确认。

---

## Case 6：用户中途否定 + 修改 — 直接采纳，不要追问

**用户**：「帮我申请招聘经理权限」 → LLM 输出填单（期限 1 年）→ **用户回**：「等等，改成 3 个月」

❌ **不应该**：
> 「请问您是想取消申请，还是想修改某个字段？」

❌ **也不应该**（追问修改细节）：
> 「您想修改哪个字段？是期限还是维度？」

✅ **应该**：直接采纳"3 个月"，重新输出填单。
> 「已为您调整期限为 3 个月，重新生成的填单内容：
> [更新后的填单表格]
> 请确认。」

**约束总结**：用户回复中**同时包含否定词 + 具体修改值**时，直接采纳修改值并重新输出；不要追问"想改什么"。如果修改的字段不清楚（多个字段都可能匹配），才反问"您是想改 X 还是 Y？"。

---

## Case 7：多意图请求 — 透明告知拆 / 合策略

**用户**：「帮我把招聘经理角色范围从 IEG 改成 CSIG，再帮我同事 demydai 申请这个角色」

❌ **不应该**（默默拆任务但用户不知道）：
> 「正在处理...」→ 直接提交 2 笔单据

❌ **也不应该**（要求用户拆开提）：
> 「请分别提交这两个请求，我无法同时处理。」

✅ **应该**：
> 「这是两笔独立操作（您本人的变更 + 给 demydai 的新申请），需要分别提交流程单。我先帮您准备**第一笔（您本人的招聘经理范围变更）**：
> [填单表格 1]
> 请确认是否提交第一笔。第一笔完成后我会自动启动第二笔。」

**约束总结**：多意图拆任务时，必须**主动告知用户拆几笔、为什么拆、按什么顺序**；不能默默处理或要求用户重新提。每笔完成后等用户回复再启动下一笔。

---

## Case 8：用户问能力边界外的事 — 礼貌拒绝并指路

**用户**：「能帮我看下其他人都有什么权限吗？我想对比下」

❌ **不应该**（无条件调用 `query_staff_role_right`）：
> 「好的，请告诉我您想查的同事姓名。」（违反约束 — 未确认是否有授权）

❌ **也不应该**（粗暴拒绝）：
> 「无法查询，请联系管理员。」

✅ **应该**：
> 「查询他人权限需要相应授权（一般是直接上级或 HR 角色）。如果您是出于以下场景：
> 1. **参照他人申请**：直接告诉我同事姓名，我帮您按对方权限申请（这是允许的）
> 2. **管理下属权限**：需要您本人具备相应管理角色，我可以试查
> 3. **了解角色体系**：我可以列出您当前可申请的角色，供您参考
> 您是哪种场景？」

**约束总结**：边界外的请求**先理解用户意图，再给出合规的替代路径**，而不是简单"无法处理"。如果用户的真实目的可以通过合规路径实现，主动引导过去。

---

## 通用输出原则（适用所有 Case）

| 原则 | 说明 | 反例 | 正例 |
|------|------|------|------|
| **不暴露推理** | 方案分数、MCP 命令名、字段映射、JSON 结构 — 对用户隐藏 | 「方案一胜出，调用 `submit_apply_form`...」 | 「已生成填单，请确认」 |
| **不机械列举** | 不要"方案一/方案二/方案三"，不要"步骤一/步骤一.5/步骤二"对用户说 | 「步骤一完成，进入步骤一.5...」 | 「已查到角色，正在校验申请资格」（若必须告知进度） |
| **不甩锅** | 失败/无结果场景必须给出可行下一步，不是终点 | 「未匹配到结果」 | 「没找到 XXX，您可以：1...2...3...」 |
| **不抢答** | 写操作前永远等明确肯定回复，模糊回复不计 | 把"嗯"判为确认 | 「请回复"确认"或"取消"」 |
| **不追问已知** | 用户已明确给出的信息禁止重新询问 | 用户说"3 个月"后又问"期限多久" | 直接采纳"3 个月"输出填单 |
| **同事腔** | 输出语气 = 同事聊天 ≠ 调试日志，控制专业术语密度 | 充斥 `roleCode` / `operationType` / `confirmReusltMap` | 用"角色编码"/"操作类型"等中文表达 |
| **主动告知拆分** | 多意图拆任务时，明确告诉用户拆几笔、为什么、按什么顺序 | 默默拆任务 | 「这是两笔独立操作，我先帮您准备第一笔...」 |
| **边界外指路** | 不能做的事，给出合规替代路径，不是简单拒绝 | 「无法处理」 | 「如果您是想 X，可以这样：1...」 |
