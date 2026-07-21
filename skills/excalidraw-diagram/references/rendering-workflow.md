# Rendering Workflow

## Purpose

`.excalidraw` 只是中间产物。真正的质量判断要看渲染后的 PNG。

## First-time setup

```bash
brew install uv
uv sync --project {baseDir}/scripts
uv run --project {baseDir}/scripts playwright install chromium
```

## Render command

```bash
uv run --project {baseDir}/scripts python {baseDir}/scripts/render_excalidraw.py /absolute/path/to/diagram.excalidraw --output /absolute/path/to/diagram.png
```

## Recommended review loop

1. 生成 `.excalidraw`
2. 渲染 PNG
3. 打开 PNG 检查布局
4. 修正 JSON
5. 再渲染一次
6. 直到没有明显问题再交付

## What to check

- 文本是否裁切
- 箭头是否落对位置
- 区块之间是否拥挤
- 是否有大面积空洞
- 技术证据块是否可读
- 标题、主流程、说明文字是否有清晰层级

## Typical fixes

- 扩大文字容器
- 调整节点 `x` / `y`
- 给箭头增加转折点
- 重分配区块间距
- 缩小次级元素，放大核心节点
