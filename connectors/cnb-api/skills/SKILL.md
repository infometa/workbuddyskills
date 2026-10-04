---
name: cnb-api
description: CNB 平台交互命令，支持代码仓库、Issue、PR、CI、制品库读写等操作。
---

# cnb-api

## 快捷命令

issues:
- `cnb issues get` — 获取详情
- `cnb issues list-comments` — 获取评论列表
- `cnb issues comment --body 内容` — 评论
- `cnb issues close` — 关闭
- `cnb issues open` — 打开
- `cnb issues list-labels` — 查看标签
- `cnb issues add-labels --labels bug --labels feature` — 添加标签
- `cnb issues list-assignees` — 查看处理人
- `cnb issues add-assignees --assignees username` — 添加处理人
- `cnb issues get-imgs --img-path 图片路径` — 获取 issue 图片
- `cnb issues get-files --file-path 附件路径` — 获取 issue 附件

pulls:
- `cnb pulls get` — 获取详情
- `cnb pulls list-files` — 获取文件变更
- `cnb pulls list-commits` — 获取提交记录
- `cnb pulls list-comments` — 获取评论列表
- `cnb pulls comment --body 内容` — 评论
- `cnb pulls list-labels` — 查看标签
- `cnb pulls add-labels --labels ready --labels approved` — 添加标签
- `cnb pulls check-status` — 查看 CI 状态
- `cnb pulls list-reviews` — 查看评审列表
- `cnb pulls submit-review` — 发送评审评论或提交评审结论
- `cnb pulls list-assignees` — 查看处理人
- `cnb pulls get-ci-logs --sn 构建号（可选）` — 获取 CI 失败日志
- `cnb pulls get-ci-timing --sn 构建号（可选）` — 分析 CI 耗时瓶颈
- `cnb pulls get-imgs --img-path 图片路径` — 获取 PR 图片
- `cnb pulls get-files --file-path 附件路径` — 获取 PR 附件

skills:
- `cnb skills list -p -a codebuddy --json` — 列出本地 skills

## 使用约定

- **编号自识别**：Issue/PR 编号自动从环境变量识别，无需额外传递。
- **可显式覆盖**：`--repo <组织/仓库>` 与 `--number <编号>` 均为可选参数。
  不传时沿用环境变量（即当前仓库的当前 Issue/PR）；传入时覆盖环境变量，
  可用于跨仓库或跨编号场景，例如 `cnb pulls get --repo x/y --number 97`、
  `cnb issues get --number 68`。两个参数相互独立，可只传其中一个。
- **默认摘要省流**：默认精简输出，加 `--verbose` 输出完整数据。
- **多行用单引号**：bash 参数为多行文本时用单引号，降低命令注入风险。
- **提及不召唤**：评论中直接 @npc 会召唤 npc；仅提及不召唤时，用反引号包裹 `@npc`。
  NPC 的触发条件见 `cnb-npc-search`，单独 `@仓库名` 不会触发。

## 取正文里的图片与附件

评论正文里的图片、附件 URL，一律用 `get-imgs` / `get-files` 取回，URL 从 `list-comments` 原文取：

- **参数取 URL 的尾段，且必须含数字 ID 段**：图片取 `/imgs/<issues|pulls>/` 之后的**完整尾段**，
  附件取 `/files/<issues|pulls>/` 之后的完整尾段；尾段首位的数字 ID 段不能省，漏掉会返回 `404 Resource not found`：
  - 原文 `.../-/imgs/issues/2101868753481326592/Lma2nfHjnchalMtHZcq4OA/6d7ab033-xxxx.png`
  - 正确 `2101868753481326592/Lma2nfHjnchalMtHZcq4OA/6d7ab033-xxxx.png` ✅
  - 漏 ID `Lma2nfHjnchalMtHZcq4OA/6d7ab033-xxxx.png` ❌ `404`
- **CLI 内置鉴权**：手写 `Authorization: Bearer` 或 `token` 都不被识别，只会拿到 400

## 常用链接

生成链接时遵循以下结构：
- Issue: `<host>/<slug>/-/issues/<number>`
- PR: `<host>/<slug>/-/pulls/<number>`

## 更多 API

1. `cnb --help` 查看所有模块
2. `cnb <module> --help` 查看模块下的工具列表
3. `cnb <module> <tool> --help` 查看工具参数
