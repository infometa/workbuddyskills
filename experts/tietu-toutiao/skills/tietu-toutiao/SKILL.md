---
name: tietu-toutiao-layout
description: This skill should be used when a newspaper page has been analyzed into a content-state.v1 JSON and needs schema validation, one of three deterministic mobile cover layouts, accurate Chinese text rendering, aspect-ratio-preserving photo cropping, structured revision patches, or versioned rollback.
agent_created: true
---

# 贴图头条：确定性头图排版

## 目的

将多模态模型输出的报纸内容状态转换为可审计的固定模板头图。多模态模型只负责理解版面、选择内容和提出方案；本 Skill 负责校验结构化状态、生成版式、准确绘制中文、等比裁切图片、保存版本和执行回退。

## 触发条件

在以下情况加载本 Skill：

- 已上传 JPG、JPEG 或 PNG 报纸版面，需要生成三种头图方案；
- 已有 `content-state.v1`，需要渲染或修改当前版本；
- 用户要求保留原标题、只调整日期、突出某张图片、减少装饰或返回上一版。

## 固定流程

1. 将多模态识别结果整理为 `content-state.v1`，保留原文、来源、坐标、置信度和确认状态。
2. 运行 `scripts/validate_content_state.py`；关键字段缺失、低置信度未确认、素材路径不存在时停止，不生成伪成功图片。
3. 对 `authoritative`、`visual`、`digest` 三种模板分别运行 `scripts/layout_engine.py`。
4. 运行 `scripts/render_cover.py`；使用明确的中文字体文件，标题自动换行或缩小，图片只做等比裁切。
5. 在用户确认或生成修订后，用 `scripts/version_manager.py save` 保存 `state.json`、`layout.json` 和 `cover.png`。
6. 自然语言修改先转换为 `scripts/apply_patch.py` 接受的结构化 patch；锁定字段不得被修改。
7. 用户要求回退时，同时恢复内容状态、布局和图片，不只恢复图片文件。

## 三种模板

- `authoritative`：保留报头、原标题、日期和核心图片，突出正式媒体感。
- `visual`：放大核心图片和标题，减少次要信息，适合手机信息流。
- `digest`：以“今日关注”或同类标签组织一个主标题和少量辅助信息。

模板文件是唯一版式真相源，位于 `templates/`；版式引擎不得再复制一套坐标硬编码。

状态契约定义位于专家包根目录的 `../../references/content-state.v1.schema.json`；运行时由 `scripts/validate_content_state.py` 执行关键门禁。

## 命令

以下命令在 `skills/tietu-toutiao/` 目录执行。安装依赖：

```bash
python -m pip install -r ../../requirements.txt
```

校验状态：

```bash
python scripts/validate_content_state.py --input content-state.json
```

生成版式并渲染：

```bash
python scripts/layout_engine.py --state content-state.json --type authoritative --output layout.json
python scripts/render_cover.py --input layout.json --output cover_authoritative.png
```

应用结构化修改：

```bash
python scripts/apply_patch.py --input content-state.json --patch revision.patch.json --output next-state.json
```

保存和回退：

```bash
python scripts/version_manager.py save --workspace session --name v1 --state content-state.json --layout layout.json --cover cover.png
python scripts/version_manager.py revert --workspace session --name v1 --output-state session/restored-state.json --output-layout session/restored-layout.json --output-cover session/restored-cover.png
```

运行回归测试：

```bash
python scripts/test_pipeline.py
```

## 失败原则

- 不允许静默使用不支持中文的默认字体。
- 不允许把关键中文交给图像模型直接绘制。
- 不允许拉伸新闻图片改变人物或现场比例。
- 不允许在缺少内容状态、字体、图片或模板字段时报告“已生成可发布成品”。
- 不允许让版本名、输出路径或输入图片路径越出当前会话工作目录。
