# ai

AI 单点能力命令组，用于图片或视频超清、字幕擦除、改视频、续写、重绘、转码、裁剪和切片等操作。

## 用法

```text
reelmate ai upscale --image FILE_ID|--video FILE_ID
reelmate ai subtitle-erase FILE_ID
reelmate ai revideo FILE_ID
reelmate ai extend FILE_ID
reelmate ai repaint ...
reelmate ai convert|crop|slice ...
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate ai upscale` | 图片或视频超清 |
| `reelmate ai subtitle-erase` | 擦除字幕 |
| `reelmate ai revideo` | 改视频 |
| `reelmate ai extend` | 续写视频 |
| `reelmate ai repaint` | 重绘素材 |
| `reelmate ai convert` | 转码素材 |
| `reelmate ai crop` | 裁剪素材 |
| `reelmate ai slice` | 切片素材 |

## `reelmate ai upscale`

### 作用

图片或视频超清。

### 参数与输出

`--image FILE_ID` 或 `--video FILE_ID` 二选一。`FILE_ID` 来自 `reelmate upload PATH --json` 的 `file_id`。返回任务或资源结果；远程失败会转为 CLI 错误。

### 示例

```bash
reelmate ai upscale --image FILE_ID --json
```

## `reelmate ai subtitle-erase`

### 作用

擦除字幕。

### 参数与输出

位置参数 `FILE_ID` 为输入文件。返回任务或资源结果。

### 示例

```bash
reelmate ai subtitle-erase FILE_ID --json
```

## `reelmate ai revideo`

### 作用

改视频。

### 参数与输出

位置参数 `FILE_ID` 为输入文件。其余字段按当前帮助和结构化错误传入；未登记字段不得猜测。

### 示例

```bash
reelmate ai revideo FILE_ID --json
```

## `reelmate ai extend`

### 作用

续写视频。

### 参数与输出

位置参数 `FILE_ID` 为输入文件。

### 示例

```bash
reelmate ai extend FILE_ID --json
```

## `reelmate ai repaint`

### 作用

重绘素材。

### 参数与输出

按当前帮助和结构化错误传入；未登记字段不得猜测。

### 示例

```bash
reelmate ai repaint --json
```

## `reelmate ai convert`

### 作用

转码素材。

### 参数与输出

按当前帮助和结构化错误传入；未登记字段不得猜测。

### 示例

```bash
reelmate ai convert --json
```

## `reelmate ai crop`

### 作用

裁剪素材。

### 参数与输出

`FILE_ID` 为输入文件；可用 `--set` 传入裁剪字段。

### 示例

```bash
reelmate ai crop FILE_ID --set ratio=16:9 --json
```

## `reelmate ai slice`

### 作用

切片素材。

### 参数与输出

按当前帮助和结构化错误传入；未登记字段不得猜测。

### 示例

```bash
reelmate ai slice --json
```

## 注意事项

- AI 操作会产生真实远端请求，执行前确认输入文件、模型参数和账号点数。
- `lipsync` 属于预留能力，不应视为当前稳定命令。
