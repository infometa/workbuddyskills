# 脚本速查

| 脚本                                                                      | 用途                                                                             | 示例                                                        |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `scripts/serve.py start`                                                  | 启动场景初筛                                                                     | `--theme "..." --probe-scene proposal --probe-reason "..."` |
| `scripts/serve.py advance <WD> --to intent_questionnaire`                 | 切到细分意图问卷                                                                 |                                                             |
| `scripts/serve.py advance <WD> --to template_choice --top 3`              | 切到 3 套模板卡                                                                  |                                                             |
| `scripts/serve.py advance <WD> --to skeleton_loading --skeleton-file ...` | 切到生成骨架 loading                                                             |                                                             |
| `scripts/serve.py stop <WD>`                                              | 清理 server + workdir；仅删除带 `.smart-page-workdir` 标记的 smart-page 临时目录 |                                                             |
| `scripts/match.py --answers <file>`                                       | 独立调用打分匹配（serve.py advance 会内部调用）                                  |                                                             |
| `scripts/validate_data.py --scene --narrative --data`                     | **data.js 结构自检**（注入前必跑）                                               | `--scene proposal --narrative pyramid --data /tmp/data.js`  |
| `scripts/inject.py --scene --narrative --skin --data --output`            | 注入并输出单文件 HTML（模板走 COS）                                              |                                                             |
| `scripts/template_source.py url/fetch/exists/index`                       | COS 模板资源访问工具（调试用）                                                   |                                                             |
| `scripts/prepare-pack.sh --html --title`                                  | 打包 zip 供 tencent-docs 上传                                                    |                                                             |
| `scripts/publish.sh --html --title`                                       | 一键发布到腾讯文档                                                               |                                                             |

---

## 文件等待协议（通用模板）

`serve.py advance` 推进 stage 后，agent 需**轮询等待**用户在右侧面板生成的信号文件。统一使用下面这个模板，把 `<FILE>` 和 `<MAX>` 替换即可：

```bash
WD="<workdir>"
FILE="<scene_confirm.json | answers.json | choice.json>"
MAX=180   # 见下表

for i in $(seq 1 "$MAX"); do
  [ -f "$WD/$FILE" ] && { cat "$WD/$FILE"; break; }
  [ -f "$WD/server.pid" ] && ! kill -0 "$(cat "$WD/server.pid")" 2>/dev/null && {
    echo '{"ready":false,"error":"server died"}'; exit 1;
  }
  sleep 1
done
```

**各阶段超时（`MAX` 取值）**：

| 阶段        | 等待文件             | MAX（秒） |
| ----------- | -------------------- | --------- |
| 阶段 1 末尾 | `scene_confirm.json` | 180       |
| 阶段 2 末尾 | `answers.json`       | 180       |
| 阶段 3 末尾 | `choice.json`        | 300       |

> **强制规则**：禁止用 heredoc 写长 python 脚本做轮询，禁止自定义复杂进程管理。统一用上面这套 `for + sleep + test -f`。

---

## 模板库来源

**模板资源全部托管在腾讯云 COS，无需本地下载。**

- **根 URL**：`https://artifact-page.gtimg.com/html_templates/`
- **可覆盖**：环境变量 `SMART_PAGE_COS_BASE`（不含结尾 `/`）
- **不做本地缓存**：每次调用都直接联网拉取，保证拿到的是 COS 最新版本

所有 Python 脚本通过 `scripts/template_source.py` 统一访问，接口：

| 接口                               | 用途                                                        |
| ---------------------------------- | ----------------------------------------------------------- |
| `template_source.cos_url(rel)`     | 拼接 `https://.../html_templates/<rel>` 绝对 URL            |
| `template_source.fetch_text(rel)`  | 拉取文本资源（narrative.md / template.html / _.css / _.js） |
| `template_source.fetch_bytes(rel)` | 拉取二进制（图片等）                                        |
| `template_source.load_index()`     | 拉取并解析 `_index.json`                                    |
| `template_source.exists(rel)`      | HEAD 探测远端是否存在                                       |

**命令行调试**：

```bash
python3 $SKILL_DIR/scripts/template_source.py url scenes/proposal/pyramid/template.html
python3 $SKILL_DIR/scripts/template_source.py index                # 打印 _index.json
python3 $SKILL_DIR/scripts/template_source.py fetch scenes/proposal/pyramid/narrative.md
python3 $SKILL_DIR/scripts/template_source.py exists _assets/skins/tencent-blue.css
```

---

## 模板库目录结构（COS 远端）

```
https://artifact-page.gtimg.com/html_templates/
├── _index.json                 # 全局注册（scenes / narratives / skins）
├── _meta/
│   ├── ARCHITECTURE.md         # 三层正交说明
│   ├── ROUTER.md               # 问卷规则（已内化进 serve.py）
│   └── TECH_STACK.md           # 技术栈约束
├── _assets/
│   ├── motion/                 # motion.js + motion.css（全局动效运行时）
│   ├── fonts/                  # TencentSans（inject.py 已改走 artifact-page.gtimg.com CDN，无需本地内联）
│   └── skins/
│       ├── _contract.css       # 35 变量合同
│       └── {skin}.css × 12     # 12 套皮肤实现
└── scenes/
    ├── proposal/               # × 3 narrative（pyramid / scqa / blm）
    ├── sync/                   # × 3 narrative（prep / star / okr）
    ├── insight/                # × 3 narrative（pyramid-data / attribution / contrast）
    └── share/                  # × 3 narrative（story-arc / qa-driven / magazine）
         └── {narrative}/
            ├── narrative.md   # data.js 生成前必读（字段契约）
            ├── template.html  # 不读！由 inject.py 处理
            ├── mock-data.js   # data.js 生成前必读（黄金示例）

             └── preview/       # 封面 + full 长图
                 ├── {skin}.png         # 1280x800 缩略
                 └── {skin}-full.png    # 1280x(fullPage) 长图
```

---

## Agent 生成 data.js 前必读

- **必须读 1**：`scenes/{scene}/{narrative}/narrative.md`
  - 读取方式：`python3 $SKILL_DIR/scripts/template_source.py fetch scenes/{scene}/{narrative}/narrative.md`
  - 或直接 `web_fetch` / `curl` 该 COS URL
  - 内含 7 节：Role · 叙事骨架 · 输入前置检查 · CoT 推理链 · 数据契约 · 视觉契约 · 约束
- **必须读 2**：`scenes/{scene}/{narrative}/mock-data.js`
  - 读取方式：`python3 $SKILL_DIR/scripts/template_source.py fetch scenes/{scene}/{narrative}/mock-data.js`
  - 用于确认值类型、嵌套结构、数组元素形态、`compute` 字符串/函数写法
- **不要读**：`template.html`（27–36KB，浪费 token），由 inject.py 处理
