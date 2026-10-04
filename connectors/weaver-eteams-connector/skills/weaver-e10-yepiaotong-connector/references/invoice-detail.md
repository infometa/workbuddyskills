# 查看发票详情

## 什么时候读取

用户给出 `fid`、发票号码，或需要查看完整票面、附件、可编辑状态、可删除状态时读取本文件。

## Operation

| Operation | 固定规则 |
| --- | --- |
| `invoice.get` | 优先用 `fid`；没有 `fid` 时可用 `number` 查询 |

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"fid":"12345"}'

weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"number":"00188205"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"fid":"12345"}'

weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"number":"00188205"}'
```

## 返回

`invoice.get` 返回服务端详情响应本身。常见字段包括 `infos[].info.fid`、`code`、`number`、`comm_info.pro`、`comm_info.price`、`comm_info.buyer`、`comm_info.payer`、`flist` 和 `modify_info`。交通类发票还可从 `infos[].info.from` / `infos[].info.to`（或 `ext.passengersService`）取出发地和目的地。

## 注意

用户已经给出 `fid` 时不要先查列表再过滤。找不到或无权查看时按失败 envelope 处理，不要自动扩大数据范围。
