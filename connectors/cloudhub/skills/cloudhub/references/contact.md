# contact（通讯录）

## 意图映射

| 用户说 | 命令 |
|--------|------|
| 我是谁 / 我的信息 / 当前登录人 | `contact user get`（不传任何 flag） |
| 找同事 / 搜人 / 查某个人 | `contact user search --keyword "<姓名/关键词>"` |
| 查用户详情 / 批量查多个用户 | `contact user get --open-id <OPEN_ID> [--open-id ...]` |

## 快捷命令

```bash
# 查当前登录用户（whoami / 我是谁）— 最常用，无需任何参数
yzj-cli contact user get
```

## 核心工作流

```
搜索员工姓名 → contact user search → 获取 oId
获取用户详情 → contact user get --open-id <oId>
查当前登录人 → contact user get（不传任何 flag）
```

## 命令速览

```bash
# 搜索员工
yzj-cli contact user search --keyword "张三"
yzj-cli contact user search --keyword "张三" --org-id <ORG_ID>

# 获取用户详情（不传 flag = 当前登录用户）
yzj-cli contact user get
yzj-cli contact user get --open-id <OPEN_ID>
yzj-cli contact user get --open-id <OID1> --open-id <OID2>
```

## contact user search

| Flag | 必填 | 说明 |
|------|------|------|
| `--keyword` | 是 | 搜索关键词（姓名等） |
| `--org-id` | 否 | 限定搜索范围的部门 ID |

返回 `data.list` 数组，元素字段：`name`、`userName`、`oId`、`jobTitle`、`department`、`fulldepartment`、`orgName`、`orgId`、`photoUrl`、`status`；伴随字段 `data.more`（是否还有下一页）

## contact user get

| Flag | 必填 | 说明 |
|------|------|------|
| `--open-id` | 否 | 用户 openId，可重复传多个；**省略则返回当前登录用户** |

返回 `data.list` 数组，元素字段：`name`、`openId`、`department`、`jobTitle`、`jobNo`、`gender`、`orgId`、`globalId`、`isAdmin`、`photoUrl`、`status`

## Notes

- `contact user search` 返回的 `oId` 即为其他命令所需的 `openId`
- 需要多个用户详情时可一次传多个 `--open-id`，减少请求次数
