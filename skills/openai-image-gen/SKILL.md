---
name: openai-image-gen
description: "Batch-generate images via OpenAI Images API. Random prompt sampler + `index.html` gallery."
description_zh: "批量生成图片并创建图库"
description_en: "Batch image generation with gallery view"
version: 1.0.1
---

# OpenAI Image Gen

Generate a handful of "random but structured" prompts and render them via OpenAI Images API.

## Setup

- Needs env: `OPENAI_API_KEY`

## Run

```bash
python3 {baseDir}/scripts/gen.py
```

Useful flags:
```bash
python3 {baseDir}/scripts/gen.py --count 16 --model gpt-image-1.5
python3 {baseDir}/scripts/gen.py --prompt "ultra-detailed studio photo of a lobster astronaut" --count 4
python3 {baseDir}/scripts/gen.py --size 1536x1024 --quality high --out-dir ./out/images
```

## Output

- `*.png` images
- `prompts.json` (prompt > file mapping)
- `index.html` (thumbnail gallery)
