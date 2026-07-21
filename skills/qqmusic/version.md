# 技能升级

本 skill 内置了 `/skill/version` 接口用于检查版本更新。建议每周检查一次升级，无需每次加载都检查。

**用户触发示例：**

- "更新 QQ音乐 skill"
- "升级 QQ音乐 技能"
- "检查 QQ音乐 有没有新版本"
- "更新 QQ音乐到最新版"

## 接口

```text
POST ${BaseUrl}/skill/version
```

**请求示例：**

```bash
curl -X POST "${BaseUrl}/skill/version" \
  -H "Authorization: Bearer $QQMUSIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"params": {}, "comm": {"skill_version": "0.0.1"}}'
```

**PATH：** `/skill/version`

**请求参数：**

| 参数                 | 类型   | 必填 | 说明                                               |
| -------------------- | ------ | ---- | -------------------------------------------------- |
| `comm.skill_version` | string | 是   | 当前 skill 版本号，取 SKILL.md 顶部 `version` 字段 |
| `params`             | object | 否   | 留空 `{}`                                          |

**响应格式（仅需升级时返回 `upgradeInfo`）：**

```json
{
  "traceId": "abc12345",
  "ts": 1716889600000,
  "ret": 0,
  "sub_ret": 0,
  "msg": "",
  "upgradeInfo": {
    "needUpgrade": true,
    "latestVersion": "0.0.2",
    "upgradeMessage": "请安装 QQ音乐 技能\n下载地址：..."
  }
}
```

| 字段                         | 类型   | 说明           |
| ---------------------------- | ------ | -------------- |
| `upgradeInfo.needUpgrade`    | bool   | 是否需要升级   |
| `upgradeInfo.latestVersion`  | string | 最新版本号     |
| `upgradeInfo.upgradeMessage` | string | 升级指引说明   |

## 升级流程

1. 如需检查升级，调用 `/skill/version` 接口。
2. 若 `upgradeInfo.needUpgrade` 为 `false` 或不存在 `upgradeInfo`，表示已是最新版本，**直接结束流程**，继续处理用户请求。
3. 若 `upgradeInfo.needUpgrade` 为 `true`：
   1. **不要自动升级** 把 `upgradeMessage` 的内容原样展示给用户，由用户决定是否升级
   2. 对下载到的新版本做基本校验：
      - 必须包含 `SKILL.md`，且文件头部 YAML frontmatter 的 `name`、`description`、`version` 字段齐全
      - 目录结构完整，各能力说明文件存在
      - 下载地址必须是 https://github.com/tencentmusic/qqmusic-skills 或 y.qq.com 域名下的发布链接，其它一律拒绝。
   3. **校验通过**：更新 skill
   4. **校验不通过 / 网络错误 / 下载失败**：放弃本次升级，**继续使用当前版本**，不阻塞用户请求。
4. 建议至少每周检查一次升级
