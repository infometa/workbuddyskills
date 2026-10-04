# 应用版本检测与详情卡片页链接

## 何时使用

判断「日程」应用是否安装、版本是否满足要求，或需要日程详情卡片页链接时使用。全部为只读操作。

## operation 清单

| operation | 用途 |
| --- | --- |
| `calendar.app.check` | 检测应用安装状态与版本（要求 >= 4.1.4），并返回日程表单 ID |

## 何时触发

- 日程接口返回 404，或提示「找不到动作流 / 动作流 ID 不存在」。
- `status: false` 且语义含「不存在」「未找到」「不支持」。
- 用户主动问版本或「为什么用不了」。

权限不足、字段校验报错、查询结果为空、网络超时**不触发**版本检测。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.app.check --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{}' | weaver-work-cli --profile eteams --json calendar run calendar.app.check --input -
```

## 输出处理

返回字段：`installed`（是否安装）、`appId`、`commitVersion`、`versionOk`（版本是否 >= 4.1.4）、`minRequiredVersion`、`formId`（日程表单 ID）、`status`（`OK` / `NOT_INSTALLED` / `VERSION_TOO_LOW`）。

- `status=NOT_INSTALLED`：停止调用所有日程接口，提示用户先安装「日程」应用。
- `status=VERSION_TOO_LOW`：停止调用，提示当前版本低于 4.1.4，请升级。
- `status=OK`：可用，按原始接口错误如实报告。

## 详情卡片页链接

查询列表/详情时，日程名称可渲染为可点击链接跳转详情卡片页：

```text
https://<E10环境地址>/sp/ebdfpage/card/0/{表单ID}/{日程ID}
```

- `<E10环境地址>`：当前 E10 环境域名。
- `{表单ID}`：`calendar.app.check` 返回的 `formId`。
- `{日程ID}`：`calendar.list` 返回的 `agenda[].id` 或 `calendar.get` 返回的 `mainTable.id`。

`formId` 为空（获取偶发空返回重试后仍失败）时降级为纯文本展示，不阻断查询结果。

## 注意

- `appId` 会随应用重装/迁移变化，禁止硬编码。
- 版本比较按 `.` 分段转整数逐段比较，不做字符串比较（CLI 已内置）。
- 默认不主动做版本校验，只在出现异常时检测。

## 失败处理

- 三步 GET 接口失败或返回空：CLI 会给出 `installed=false` 与原因，据此向用户说明，不做盲目重试。
