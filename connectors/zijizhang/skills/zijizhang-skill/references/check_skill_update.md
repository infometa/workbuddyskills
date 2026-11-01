## 检查 Skill 更新（check_skill_update）

用于在执行任务前检查 `zijizhang-skill` 是否有新版本；若有，则提示用户按安装指南升级（本命令不会自动覆盖安装）。

```shell
zijizhang-cli updater check_skill_update '<skill_version>'
```

> `skill_version` 取 `zijizhang-skill/SKILL.md` 顶部 YAML 的 `version:` 值，例如 `0.0.2`。

### 使用示例

```shell
zijizhang-cli updater check_skill_update 0.0.2
```

### 返回参数

返回为 JSON：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| code | int | 状态码，`200` 代表成功，其他代表失败 |
| msg | string | 提示信息 |
| data | object | 更新信息 |

data 字段说明：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| latest | string | 最新 skill 版本（语义化版本号） |
| installation_guide_url | string | 安装/升级指南链接（按指南升级/覆盖安装，不要自行猜安装命令/来源，是个zip包，skill在zip里） |
| must_be_update | bool | 是否必须升级（`true` 时应强提示用户先升级再继续关键流程） |
| note | string | 更新说明/更新笔记 |

### 返回例子

#### 成功

```json
{
  "code": 200,
  "msg": "ok",
  "data": {
    "latest": "0.0.3",
    "installation_guide_url": "https://res.zijizhang.com/download/skill/zijizhang-skill-0.0.3.zip",
    "must_be_update": false,
    "note": "..."
  }
}
```

#### 失败

```json
{
  "code": 500,
  "msg": "获取失败",
  "data": {}
}
```

### 处理规则（重要）

- 当 `code != 200`：不阻塞用户业务请求，继续按当前版本执行，并告知“远端查询失败，本次跳过更新检查”。
- 当 `code == 200` 且发现有更新（`data.latest` 高于当前 `skill_version`）：必须提示用户按 `data.installation_guide_url` 升级/覆盖安装。
- 当 `must_be_update == true`：必须强提醒用户先升级，再继续可能受版本影响的关键流程。

