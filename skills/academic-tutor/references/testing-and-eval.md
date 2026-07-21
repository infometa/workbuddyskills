# 端到端冒烟测试 / 触发率评测

> 仅在用户问「怎么测试」「跑评测」「冒烟测试」「触发率」时加载本文件。

## 端到端冒烟测试

```bash
# 从仓库根目录执行
python3 .codebuddy/skills/academic-tutor/tests/integration_test.py

# 或者先 cd 进 skill 目录
cd .codebuddy/skills/academic-tutor && python3 tests/integration_test.py
```

测试覆盖 6 步：

1. `init_profile`：初始化 profile（major / grade / preferences）
2. `update_profile`：追加论文进度（thesis.stage / topic_draft）
3. `new_session`：开启对话会话（指定 topic）
4. `append_turn × 3`：依次追加 3 类轮次
   - 学业题目：高数 / 算法 / 编程
   - 论文选题：proposal stage anchoring
   - 越界拒答：用户说"直接代写"，验证 NEVER 5 触发
5. `render_three_segments`：校验三段式格式契约（emoji 锚点 / 段序 / 段非空）
6. `archive`：会话归档到 `sessions/` 只读副本

**隔离机制**：测试自动用 `ACADEMIC_TUTOR_DATA_DIR=$(mktemp -d)` 切换到临时目录，
**绝不污染**真实 `~/.workbuddy/data/academic-tutor/`。每次运行后临时目录可手动清理。

## 触发率 / 对话质量评测

`evals/` 含两份评测：

| 文件 | 用途 | 用例数 |
|---|---|---|
| `evals.json` | 端到端对话质量（5 happy + 1 越界拒答）| 6 |
| `trigger-eval.json` | 触发率：should-trigger vs should-not-trigger（与 out-of-scope 相邻请求紧贴）| 8+8 |

调用方式（由 skill-assistant 触发）：

```
> "评测 academic-tutor skill"
```

→ 路由到 `skill-assistant/modules/inspect.md` 的 `eval_mode=hybrid`，自动跑：

- D10.1 输出质量可验证性：用 `evals.json` 做 baseline vs with-skill 双跑
- D10.2 触发率：用 `trigger-eval.json` 做 should/should-not 分类准确率
- D10.3 测试集判别力：Grader critique evals 输出

详细评测协议见 `skill-assistant/modules/inspect.md`。
