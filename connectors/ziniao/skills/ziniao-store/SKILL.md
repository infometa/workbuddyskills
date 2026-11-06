---
name: ziniao-store
version: 1.2.0
description: "Use when a request concerns the local 紫鸟/ZClaw browser, a store name or ID, listing/resolving/opening/reusing/closing a store browser, or a store-scoped task that starts from a store. Do not use for server-side account CRUD or for a webpage task on an already-open store."
metadata:
  requires:
    bins: ["ziniao-cli"]
---

> 连接器登录已由 WorkBuddy 完成。不要运行 `ziniao-cli config init`。命令返回未登录或 API Key 无效时，请用户在 WorkBuddy 里重新连接。店铺浏览器操作仍需要本机紫鸟客户端。参数不确定时运行对应命令的 `--help`。本文件不带 `references/`，不要去读那些路径。

# 紫鸟店铺入口

本技能负责“店铺”这一资源及其本地浏览器生命周期，不负责定义用户的业务目标，也不复制 CLI 帮助文档。

## 负责范围

- 列出、解析、打开、复用、关闭本地紫鸟店铺浏览器。
- 保存本次任务确认过的 `store-id`，供后续步骤复用。
- 用户从某个店铺开始并继续操作网页时，按需使用 `ziniao-page`。
- 任务涉及配置、认证、Bridge、客户端或网络异常时，按需读取 `ziniao-shared` 的诊断规则。

## 路由边界

- 请求以店铺名称/ID或“本地紫鸟店铺”为起点：先处理店铺，再判断是否需要页面能力。
- 已有明确且正在运行的店铺，只需网页操作：使用 `ziniao-page`，不要重复打开店铺。
- 店铺后台账号的创建、删除、授权、标签等服务端管理不在本连接器里，不要用本技能代替。
- 不要把用户的业务目标或任务参数写入本技能；这些属于任务内容，不是店铺能力。

## 最小执行规则

1. 需要店铺对象时，使用 CLI 的 `store list` 或 `store resolve` 获取并确认目标。
2. 需要浏览器窗口时，使用 `store open`；已有有效 `store-id` 且店铺仍运行时直接复用。
3. 需要网页资源操作时，继续使用 `ziniao-page`；不要在本技能中重述页面命令。
4. 店铺命令失败时，根据错误按需运行 `ziniao-cli doctor`；不要无条件登录、启动或重复重试。
5. 具体参数不确定时，使用 `ziniao-cli store <command> --help`。环境问题按 `ziniao-shared`。

## 打开后的验证边界

- 用户只要求打开店铺时，精确解析店铺并成功执行带 `--expected-name` 的 `store open` 即可结束；不得为了证明窗口存在而追加 `page snapshot`。
- 用户同时给出目标 URL 时，首次打开优先使用同一次 `store open --url`，不要再对同一 URL 重复执行 `page visit`。
- 用户要求确认最终页面或业务状态时，转到 `ziniao-page`，使用导航返回值、`page content` 或 `page exec` 验证 URL/title/正文；不得用 snapshot 代替普通页面验证。
- 只有后续页面任务本身满足上传、自定义控件或复杂歧义定位条件时，才由 `ziniao-page` 决定使用 snapshot。

## 按需参考

- 列出店铺：`ziniao-cli store list --help`
- 打开或复用店铺：`ziniao-cli store open --help`
- `ziniao-shared`：仅在配置、认证、Bridge 或诊断问题出现时读取。
- `ziniao-page`：仅在任务继续操作已打开店铺内网页时读取。
