---
name: scm-report-directory-safe
description: "安全查询当前账号 SCM 权限内可见的供应链报表目录；适用于询问有哪些供应链报表、是否有库存/采购/成本类报表。仅调用经 AI Gateway 认证的只读固定接口。"
version: "1.0.174"
---

# SCM 可见报表目录

## 使用场景

用户询问“供应链有哪些报表”“有没有库存报表”“查找采购或成本报表”时使用本技能。

## 固定调用

所有查询通过连接器安装的 `sl-sea` 二进制和 AI Gateway 执行。`<sl-sea-absolute>` 是按当前系统运行规则解析出的绝对路径占位符；不要改用旧的 `sl`、`sl.cmd` 或开发版入口。

查询全部可见目录：

```text
<sl-sea-absolute> scm_analysis list --skill-ref scm-report-directory-safe@1.0.174 --format json
```

用户明确给出报表名称关键词时，只允许增加 `--name '<用户关键词>'`。不得使用 `report-id`、`task-id`、动态筛选接口或报表执行接口。

## 安全与输出规则

1. 只允许上述固定目录查询；其它 SCM analysis 子命令在 WorkBuddy 中一律禁止。
2. SCM 凭据由 AI Gateway 交换、缓存与刷新；本地不读取或保存 SCM Token。
3. 只展示报表名称、菜单分组和可见数量等业务目录信息。报表 ID、任务 ID、集团/门店 ID、账号 ID、Token 等禁止展示。
4. 接口失败与无匹配报表必须区分；失败不能解释成“没有权限”或“没有报表”。
5. 不输出命令、原始 JSON、内部路径、请求头、鉴权信息或底层错误堆栈。
6. 本技能只证明目录可见，不代表对应报表执行能力已经发布；用户要求报表数据时，必须改用已发布的数据 Skill，不能拿目录接口代替数据。

