# 发起借阅与续借

## 什么时候读取

用户要从借阅车发起借阅、要从检索结果直接发起借阅、或要为借阅单续借时读取本文件。写操作前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 场景 | 准备 | 确认 |
| --- | --- | --- |
| 从借阅车发起借阅 | `archive.flow.borrow-car.prepare`（`arcIds`、`carIds`，两者数量必须一致） | `archive.flow.borrow-car.apply` |
| 从检索结果发起借阅 | `archive.flow.search.prepare`（`arcIds`） | `archive.flow.search.apply` |
| 借阅单续借 | `archive.flow.renew.prepare`（`dataId`） | `archive.flow.renew.apply` |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.flow.borrow-car.prepare --input-json '{"arcIds":["1252600626189156465_1190991330335571989"],"carIds":["1302754028599656449"]}'

weaver-work-cli --profile eteams --json archive run archive.flow.borrow-car.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'

weaver-work-cli --profile eteams --json archive run archive.flow.renew.prepare --input-json '{"dataId":"1302806508947652629"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.flow.borrow-car.prepare --input-json '{"arcIds":["1252600626189156465_1190991330335571989"],"carIds":["1302754028599656449"]}'

weaver-work-cli --profile eteams --json archive run archive.flow.borrow-car.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'

weaver-work-cli --profile eteams --json archive run archive.flow.renew.prepare --input-json '{"dataId":"1302806508947652629"}'
```

## 参数来源

- `arcIds`：档案标识数组，元素为 `{档案ID}_{表单ID}`。从借阅车取 `arcDangan[*].id`，从检索结果取 `id` + `formId` 拼接。
- `carIds`：借阅车记录 ID 数组，取借阅车行的 `dataId`，与 `arcIds` 一一对应。
- 续借只用 `dataId`（借阅单主表 ID），不需要缓存参数。

## 注意

- `.prepare` 会检查是否绑定借阅流程；未绑定时返回 `validation/borrow_flow_unbound`，应提示联系管理员在档案设置中绑定借阅流程，不要重试。
- `.apply` 返回的是**流程创建页 URL**，CLI 不自动打开浏览器。Agent 拿到 URL 后**默认用系统默认浏览器打开**供用户填写提交（macOS `open`，Windows `start`），除非用户明确要求“在 IDE 内置浏览器打开”；不要声称“已发起借阅申请”。
- 从借阅车发起会缓存档案与借阅车两组参数（两次缓存写入），从检索结果发起只缓存档案，续借不缓存。
- URL 中的缓存参数由服务端生成，Agent 不要手工拼接或改写 URL。
