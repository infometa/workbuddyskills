# Fundus Disease Analysis

[基于普角与超广角眼底彩照的AI多病种分析，覆盖青光眼、糖网、AMD等数十种疾病的诊断与报告解读。]

## 类型

Agent 型（单个 AI 专家）

## 功能

[我是腾讯觅影眼底多病种AI诊断模型，基于大量眼科临床实验及真实世界数据训练。当用户在医院完成眼底照相检查后，我可以对眼底彩照进行 AI 分析，输出疾病判别结果与完整结构化报告。]

## 使用示例

- [请帮我分析这张蔡司超广角眼底彩照，看看有没有异常]
- [请对这份普角眼底图像进行多病种分析]
- [请帮我分析这几张普角眼底图像，并输出分析报告]

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 依赖环境

`bin/fundus_ai.py` 仅依赖 Python 标准库（urllib/hmac/hashlib/gzip/base64），无需安装第三方包，但需要 **Python 3.6+** 环境（代码使用了 f-string 与类型注解语法）。

## 安装

将专家包目录放到专家目录下（如 `plugins/fundus-disease-analysis/`）：

```
<专家目录>/plugins/fundus-disease-analysis/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r fundus-disease-analysis.zip fundus-disease-analysis/
```
