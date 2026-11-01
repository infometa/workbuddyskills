# edge

`edge` 不是独立顶层命令组。画布节点连线通过 [node.md](node.md) 中 ``## `reelmate node`（连线）`` 完成；本页仅作 SKILL 路由入口，参数与示例以 node 为准。

## 用法

```text
reelmate node --canvas CANVAS_ID --left NODE_ID --right NODE_ID
reelmate node --canvas CANVAS_ID --left-add NODE_ID --right NODE_ID
reelmate node --canvas CANVAS_ID --left-rm NODE_ID --right NODE_ID
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate node`（连线） | 创建、增量增加或删除有向连线；上列三种参数形态见 node.md 连线小节 |

## 注意事项

- 读写连线请打开 [node.md](node.md) 的 ``## `reelmate node`（连线）``，不要在本页重复维护参数细节。
- `--left` / `--right` 与 `--left-add` / `--left-rm` 互斥规则、语义默认值与写操作心跳要求，均以 node.md 为准。
