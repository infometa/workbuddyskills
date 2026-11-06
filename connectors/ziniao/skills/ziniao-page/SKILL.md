---
name: ziniao-page
version: 1.2.1
description: "Use when a request concerns a webpage running inside an already-opened 紫鸟/ZClaw store browser, including navigation, inspection, interaction, extraction, or screenshots. If the task starts by identifying or opening a store, use ziniao-store first."
metadata:
  requires:
    bins: ["ziniao-cli"]
---

> 连接器登录已由 WorkBuddy 完成。不要运行 `ziniao-cli config init`。命令返回未登录或 API Key 无效时，请用户在 WorkBuddy 里重新连接。页面操作仍需要本机紫鸟客户端。参数不确定时运行对应命令的 `--help`。本文件不带 `references/`，不要去读那些路径。

# 紫鸟页面能力

本技能负责已打开紫鸟店铺浏览器中的通用网页资源操作，不负责店铺生命周期，也不定义用户的业务流程。

## 负责范围

- 对当前店铺浏览器中的网页进行通用操作或读取。
- 在页面操作中复用已确认的 `store-id`，必要时指定 `target-id`。
- 根据页面状态选择 CLI 已提供的页面命令；参数以 `ziniao-cli page <command> --help` 为准。
- 页面操作需要复杂编排时，看 `ziniao-cli automation run --help`。

## 路由边界

- 已有店铺浏览器并且目标是网页资源：直接使用本技能。
- 任务尚未确定或打开店铺：转到 `ziniao-store`，不要自行猜测店铺 ID。
- 不要把用户的业务目标或任务参数写入技能；这些是用户任务，由模型组合通用页面能力完成。
- 配置、认证、Bridge、客户端或网络异常：按需读取 `ziniao-shared` 的诊断规则，不在本技能重复维护环境修复流程。

## 最小执行规则

1. 确认店铺已打开，并取得有效 `store-id`；页面命令通常都需要它。
2. 先确认当前页面状态，再执行必要的页面操作；页面变化后不要复用失效的目标或定位信息。
3. 对导航、等待、读取、交互、提取和截图等能力，直接使用 CLI 的对应命令；不确定参数时先看 `--help`。
4. 涉及附件或图片上传时，先遵守本文件「上传」一节，再看 `ziniao-cli page upload --help`。未按该节执行不得上传。
5. 不得在本次 `page upload` 返回结果前预判文件是否需要外部路径确认；只有实际返回 `confirmationRequired=true` 才进入确认流程，返回 `confirmationRequired=false` 时不得向用户索要确认，应继续验证网站侧结果。
6. 只在当前任务需要时读取 reference，不要默认读取全部页面文档。
7. 报错时区分页面/目标定位问题和环境问题；环境问题再转 `ziniao-shared`/`doctor`。

## 页面读取与定位顺序

1. 页面状态、`target-id` 和稳定 CSS selector 已知时，直接复用并执行必要操作；不要为每一步重复读取页面。selector 是否唯一不确定时，先用 `page query` 检查匹配数量和候选文本。
2. 需要理解页面或验证导航、搜索、提交结果时，优先使用 `page content --content-format structured`；需要查看轻量 DOM 结构时再使用 `page content --content-format html`，只需 URL/title 时也可使用 `page exec`。
3. selector 未知时，先使用 `page query` 或只读 `page exec` 分析普通 document DOM。能得到唯一稳定 selector 时，使用 `page input` / `page click --selector`。
4. 普通 DOM 中缺少关键文本或目标位于 Web Component 内部时，用 `page exec` 检查开放的 shadow root；不要仅因标签名是自定义元素就直接升级到 snapshot。参数见 `ziniao-cli page exec --help`。
5. 只有上传控件、自定义或图标控件、多个相似控件仍存在歧义，或上述 DOM/shadow DOM 方法仍无法唯一定位时，才使用 `page snapshot` 和当前页面 ref。
6. closed shadow root、Canvas、纯图片或 snapshot 仍无法识别目标时，使用截图进行视觉确认或请求用户消歧；不得盲点。

## Selector 与脚本边界

- `page click --selector` 使用标准 `document.querySelector` 语义，支持合法的复杂 CSS（包括 `:nth-of-type()`），但只操作第一个匹配元素。可能多匹配时必须先 `page query`；优先使用稳定的 id、name、`data-testid`、ARIA 属性或稳定父级组合，动态列表中的位置 selector 需在操作前重新验证。
- 普通可定位元素优先使用 `page click --selector` 的可信鼠标事件。`page exec` 中的 DOM `.click()` 只用于普通 selector 无法触达的开放 shadow DOM 等目标，不得把它当成复杂 selector 的通用替代。
- `page exec --script` 会原样交给 `Runtime.evaluate`。直接表达式会执行；函数表达式必须显式调用，例如 `(() => document.title)()`，裸 `() => document.title` 只会返回函数。执行后必须检查返回结果和 `exceptionDetails`。
- `page content`、`page query`、`page click --selector` 和 `page snapshot` 都不保证递归进入 shadow root。开放 shadow root 可用 `page exec` 检查；closed shadow root 不能通过页面脚本直接穿透。

`page snapshot` 不是通用页面状态检查命令，也不是 shadow DOM 穿透器。不得为了验证店铺窗口、读取 URL/title/`target-id`、操作已知 selector、普通搜索或结果验证而调用 snapshot；页面未变化时也不得重复创建 snapshot/ref。snapshot 是针对当前未解决目标的局部、非粘性兜底：一次使用 snapshot/ref 不得把后续流程切换为 snapshot 模式。完成当前目标的操作后，下一操作必须重新从上述定位顺序开始；若下一目标按该顺序仍满足 snapshot 兜底条件，并且页面、tab 和现有 snapshot 均未失效，可直接使用当前 snapshot 中对应的有效 ref，无需重新 snapshot。snapshot ref 只属于当前店铺、tab 和页面，页面导航、刷新或明显重渲染后不得复用。

输入后提交只能选择一种方式：使用 `page input --submit` 后等待并验证结果，或不传 `--submit` 再执行提交按钮的 `page click --wait-nav`；不得重复提交。

## 上传

- `page upload` 只接受用户提供的本地文件路径。来源是 `http://` 或 `https://` 时立即停止，原样回复「暂不支持从 URL 上传附件，请提供本地文件路径。」不得先下载再上传。
- 不得根据路径文字判断文件是否在店铺下载目录。先执行本次 `page upload`，只以返回的 `confirmationRequired` 和 `downloadFolderPath` 为准。
- `confirmationRequired=true` 时，最终回复必须同时包含完整 `confirmationMessage` 和 `screenshotFilePath` 指向的实际截图，并说明文件尚未上传，然后等待用户按该消息确认。确认后只用相同参数追加 `--confirmation-token` 重试一次。
- 命令退出码为 0、`attached=true` 或文件进入控件，都不能单独证明网站侧上传完成。

## 按需参考

- 导航：`ziniao-cli page visit --help`
- 截图：`ziniao-cli page screenshot --help`
- 多步编排：`ziniao-cli automation run --help`
- `ziniao-store`：需要确定或打开店铺时使用。
- `ziniao-shared`：仅在环境、配置、认证或 Bridge 诊断时读取。
