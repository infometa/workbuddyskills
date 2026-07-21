# get_session

初始化测试会话。执行脚本自动完成 token 校验、环境检测、session 存活检查、模式判断。

**⚠️ 不要 cd 切换目录，不要创建任何临时脚本。**

---

## 命令格式

```shell
# 读取 session
python3 <skills_dir>/scripts/get_session.py

# 回写 session（合并写入，dict 字段做 key 级别合并，其他字段直接覆盖）
echo '<json_data>' | python3 <skills_dir>/scripts/get_session.py --write
```

**参数说明**：

- `<skills_dir>`：脚本目录的绝对路径（通常为 `.codebuddy/skills/testbuddy-skill`）
- `--write`：可选，从 stdin 读取 JSON 合并写入 session.json，输出合并后的完整数据

---

## 输出说明

脚本输出 JSON，根据 `design_uid` 是否存在区分模式：

| 模式      | 条件                    | 说明                                              |
| --------- | ----------------------- | ------------------------------------------------- |
| `mindmap` | `design_uid` 存在且非空 | session 已由画布填充完整，直接进入后续工作流      |
| `chat`    | `design_uid` 不存在     | 缺少脑图上下文，需通过对话补充后用 `--write` 回写 |

---

## 错误处理

缺少 token 时脚本返回错误提示，按提示申请 token 并写入环境变量 `TESTBUDDY_TOKEN` 即可。
