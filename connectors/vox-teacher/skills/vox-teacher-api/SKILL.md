---
name: vox-teacher-api
version: 2.0.0
description: 一起作业（17zuoye）教师端业务接口知识库——班级列表、作业数据、学情报告等只读查询接口的调用方法与响应字段说明（生产环境）。当用户询问自己的班级、学生、作业完成情况、学情数据时使用本技能，通过 MCP 连接器 vox-teacher 的 fetch_as_user 工具携带登录 cookie 调用接口。
---

# 一起作业教师端接口知识库（生产环境）

## 适用前提

- 用户已通过 WorkBuddy 连接器 **vox-teacher** 完成 OAuth 授权登录（cookie 已注入 token）
- 所有接口通过 MCP 工具 **`fetch_as_user`** 调用——cookie 由网关自动携带，**你（AI）不需要也无法直接获取 cookie**
- 服务地址：`https://www.17zuoye.com`（**生产环境**）
- 本技能涉及的真实用户数据（学生名单/成绩等）**仅对授权用户本人展示**，输出时不重复存储

## 通用调用模式

```
fetch_as_user(url="https://www.17zuoye.com/<接口路径>", method="GET")
```

- 响应为 ALPS MapMessage JSON：`{"success": true/false, "info": "...", ...}`
- **`success` 是布尔值**（不是字符串 result）——判断成功看 `success == true`
- `success=false` 时错误信息在 `info` 字段
- **会话失效识别**：返回 302 跳登录页 / 401 / 返回登录页 HTML / `info` 含 not_authenticated → 引导用户：「请在 WorkBuddy 连接器管理中点击 vox-teacher 的『重新连接』，10 秒即可恢复」

---

## 接口一：我的班级列表（确认可用 ⭐）

**用途**：查老师带了哪些班、各班学生数、年级分布。

```
GET https://www.17zuoye.com/teacher/new/homework/clazzlist.vpage
```

**响应结构**（`success=true` 时）：

```json
{
  "success": true,
  "clazzList": [
    {
      "classLevel": 3,          // 年级（1-6）
      "canBeAssigned": true,    // 该年级是否可布置作业
      "clazzs": [
        {
          "classId": 30123456,      // 班级 ID
          "className": "三年一班",   // 班级名
          "groupId": 40123456,      // 教学组 ID（查作业用）
          "studentCount": 42,       // 学生数
          "canBeAssigned": true,    // 本班是否可布置作业
          "teamList": []            // 分层教学分组（可忽略）
        }
      ]
    }
  ]
}
```

**使用要点**：
- 按年级分组嵌套（`clazzList[].clazzs[]`），汇总班级数 = 各年级 clazzs 数量之和
- 用户问"我带了几个班/哪些班" → 调此接口，汇总输出；问某班人数 → 找到对应 classId 的 studentCount
- **classId 和 groupId 是后续查作业/学情的必用参数**，记得保留

## 接口二：作业列表（按教学组）

**用途**：查某个班（教学组）布置过的作业及完成情况。

```
GET https://www.17zuoye.com/teacher/new/homework/report/loadhomeworks.vpage?groupId=<groupId>&subject=<科目>&page=<页码>
```

**参数**（来自接口一的 groupId）：
- `groupId`：教学组 ID（必填）
- `subject`：科目英文（MATH/CHINESE/ENGLISH，来自用户学科；不确定时可省略试一次）
- `page`：页码（默认 0）

**响应结构**（`success=true` 时，字段以实测为准——本接口为教学报告域，返回作业列表含作业 ID、布置时间、完成率等；若字段与本描述有出入，以实际响应为准并向用户如实呈现）：

```json
{
  "success": true,
  "homeworks": [
    {
      "homeworkId": "HW202609...",
      "createAt": "2026-09-20",
      "finishRate": 0.85,
      "...": "以实际响应为准"
    }
  ]
}
```

**使用要点**：
- 用户问"我布置了什么作业/最近的作业" → 先调接口一拿 groupId → 再调本接口
- **字段结构标注了"以实测为准"——第一次调用时先完整输出响应的键名清单，再按实际字段组织答案**（教学报告域接口多且形态不一，诚实呈现优于编造字段）

## 接口三：作业学情报告（单次作业）

**用途**：查某次作业的学情详情——完成率、平均分、未交名单等。

```
GET https://www.17zuoye.com/teacher/new/homework/report.vpage?homeworkId=<homeworkId>&clazzGroupId=<groupId>
```

**参数**：
- `homeworkId`：作业 ID（来自接口二）
- `clazzGroupId`：教学组 ID（来自接口一）

**响应结构**：学情报告数据（完成统计/成绩分布/题目正确率等，**以实际响应为准**，同接口二的处理原则）

**使用要点**：
- 用户问"上次作业完成得怎么样/谁没交" → 接口一（groupId）→ 接口二（homeworkId）→ 本接口
- 若返回 HTML 页面而非 JSON（部分报告是页面渲染）→ 告知用户该报告需在网页查看，并给出 URL（把接口 URL 直接给用户浏览器打开）

---

## 组合查询流程（推荐话术链）

```
用户：「我带的班最近作业情况怎么样？」
  ① clazzlist.vpage → 拿班级 + groupId 列表
  ② 每班 loadhomeworks.vpage → 作业列表（近 N 次）
  ③ （用户追问某次）report.vpage → 学情详情
```

## 重要边界（必须遵守）

1. **只调只读接口**：本技能只包含查询类接口。布置作业、批改等**写操作严禁调用**（服务端有状态变更，且 Skill 无确认机制）
2. **不做数据加工编造**：字段与描述不符时如实呈现实际响应，不猜测字段含义
3. **学生隐私**：未交名单等数据仅对用户本人展示，输出时不重复存储
4. **频率克制**：组合查询最多 3-5 次接口调用；更深的明细让用户明确追问后再查

## 故障排查

| 现象 | 处理 |
|---|---|
| `fetch_as_user` 不在工具列表 | 网关未部署该工具——提示用户稍后再试或联系管理员 |
| 返回 `会话已过期` | 引导用户点连接器「重新连接」 |
| 返回 HTML 而非 JSON | 该接口是页面型——把 URL 给用户直接打开 |
| 404 | 接口未部署或路径变更——如实告知，建议网页端操作 |
| 403（域名被拒） | 接口 host 不在 fetch 白名单——如实告知「该服务暂未接入」，建议网页端操作 |
| 字段与本文档不符 | 以实际响应为准如实呈现（接口二/三字段本就以实测校准为准），不编造 |
