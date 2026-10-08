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

- **默认摘要省流**：默认精简输出，加 `--verbose` 输出完整数据。
- **多行用单引号**：bash 参数为多行文本时用单引号，降低命令注入风险。

## issue/pr 访问说明

编号同 `--repo` 一样默认从环境变量识别，无需传递；用 `--repo <组织/仓库>`、`--number <编号>` 可覆盖。

例如：
- `cnb issues get --number 66`
- `cnb pulls get --repo x/y --number 99`

## 图片与附件解析

正文里图片、附件的下载地址形如：

- 图片 `.../-/imgs/<issues|pulls>/<数字 ID>/<key>/<文件名>`
- 附件 `.../-/files/<issues|pulls>/<数字 ID>/<key>/<文件名>`

`图片路径/附件路径`=`<数字 ID>/<key>/<文件名>`，即 `参数` 取 `<issues|pulls>/` 之后的**完整尾段**。

## 常用链接

生成链接时遵循以下结构：
- Issue: `<host>/<slug>/-/issues/<number>`
- PR: `<host>/<slug>/-/pulls/<number>`

## 更多 API

1. `cnb --help` 查看所有模块
2. `cnb <module> --help` 查看模块下的工具列表
3. `cnb <module> <tool> --help` 查看工具参数
