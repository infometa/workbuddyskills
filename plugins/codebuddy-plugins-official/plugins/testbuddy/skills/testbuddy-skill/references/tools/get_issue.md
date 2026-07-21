# get_issue

获取 TAPD 需求/缺陷详情。支持通过 **TAPD 链接** 或 **workspace + issue_id** 两种方式查询。

**⚠️ 重要**：执行脚本前**不要切换目录（不要 cd）**，确保在工作区根目录执行。

---

## 命令格式

```shell
# 方式 1：通过 TAPD 链接获取
python3 <script_dir>/scripts/get_issue.py --link <tapd_link>

# 方式 2：通过 workspace + issue_id 获取
python3 <script_dir>/scripts/get_issue.py --workspace <workspace> --issue_id <issue_id> [--issue_type STORY|BUG]
```

**参数说明**：

| 参数           | 是否必填 | 说明                                                               |
| -------------- | -------- | ------------------------------------------------------------------ |
| `--link`       | 二选一   | TAPD 链接（支持 tapd_fe/prong 格式），与 workspace/issue_id 二选一 |
| `--workspace`  | 二选一   | TAPD 工作区 ID，与 --link 二选一                                   |
| `--issue_id`   | 二选一   | 需求/缺陷 ID，与 --link 二选一                                     |
| `--issue_type` | 可选     | 类型：`STORY`（默认）或 `BUG`                                      |

- `<script_dir>`：脚本目录的绝对路径（通常为 `.codebuddy/skills/testbuddy-skill`）
- token 从 `session.json` 或环境变量 `TESTBUDDY_TOKEN` 自动读取

---

## 命令执行输出

### 成功输出示例

```json
{
  "status": "success",
  "content": "需求/缺陷的详细内容..."
}
```

### 失败输出示例

```json
{
  "status": "error",
  "msg": "缺少 token 或参数错误的具体信息"
}
```

---

## 使用示例

```shell
# 通过 TAPD 链接获取需求详情
python3 <script_dir>/scripts/get_issue.py --link "https://tapd.woa.com/tapd_fe/12345678/story/detail/1001"

# 通过 workspace + issue_id 获取需求详情
python3 <script_dir>/scripts/get_issue.py --workspace 12345678 --issue_id 1001

# 获取缺陷详情
python3 <script_dir>/scripts/get_issue.py --workspace 12345678 --issue_id 2001 --issue_type BUG
```

---

## 注意事项

1. **不要创建脚本**：直接执行 `get_issue.py`，不要创建任何辅助脚本
2. **token 要求**：需要 token，token 从 `session.json` 或环境变量 `TESTBUDDY_TOKEN` 读取
3. **两种调用方式二选一**：`--link` 与 `--workspace/--issue_id` 不要混用
4. **错误处理**：脚本会返回详细的错误信息，根据提示修正参数后重新执行
