---
name: external-api
description: >
  外部 API 服务调用技能。安全管理 API 密钥，调用第三方 AI 服务生成资产。
  支持 3D 模型、贴图、音频等资产的 AI 生成。
version: 1.0.0
dependencies:
  - file-manager
triggers:
  - pattern: "生成模型|生成贴图|生成音效|AI生成|外部API"
inputs:
  - name: service
    type: string
    enum: ["meshy", "tripo3d", "stable_diffusion", "leonardo", "suno", "elevenlabs"]
    required: true
  - name: prompt
    type: string
    required: true
outputs:
  - name: asset_path
    type: string
    description: 生成的资产文件路径
---

# 外部 API 服务调用技能

提供第三方 AI 服务的安全调用能力，用于生成游戏资产。

## 密钥配置

### 配置步骤

1. 复制 `.env.template` 为 `.env.local`
2. 填入对应服务的 API Key
3. 确保 `.env.local` 已添加到 `.gitignore`

### 环境变量模板

```bash
# ===== 3D 模型生成服务 =====
MESHY_API_KEY=your_meshy_api_key_here
TRIPO3D_API_KEY=your_tripo3d_api_key_here

# ===== 贴图生成服务 =====
SD_API_KEY=your_stable_diffusion_api_key_here
SD_API_ENDPOINT=https://api.stability.ai
LEONARDO_API_KEY=your_leonardo_api_key_here

# ===== 音频生成服务 =====
SUNO_API_KEY=your_suno_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# ===== 通用配置 =====
API_TIMEOUT=60
API_RETRY_COUNT=3
```

---

## 安全原则

1. **永不打印密钥**：日志中仅显示密钥是否存在，不显示实际值
2. **环境隔离**：开发/生产环境使用不同密钥
3. **权限最小化**：仅申请服务必要的 API 权限
4. **错误处理**：密钥无效时给出清晰指引，不暴露密钥内容

---

## 密钥检查

调用任何外部服务前，先检查密钥配置状态：

```typescript
interface KeyStatus {
  service: string;
  configured: boolean;
  masked_key?: string;  // 如 "sk-****abcd"
}

function checkApiKeys(): KeyStatus[] {
  return [
    { service: "MESHY", configured: !!process.env.MESHY_API_KEY },
    { service: "STABLE_DIFFUSION", configured: !!process.env.SD_API_KEY },
    { service: "SUNO", configured: !!process.env.SUNO_API_KEY },
    // ...
  ];
}
```

---

## 可用服务

### 3D 模型生成

#### Meshy.ai

**用途**：文本到 3D 模型生成

**API 调用示例**：
```typescript
interface MeshyRequest {
  prompt: string;           // 模型描述
  art_style: string;        // "realistic" | "cartoon" | "low-poly" | "sculpture"
  negative_prompt?: string; // 排除元素
  topology: string;         // "quad" | "triangle"
  target_polycount: number; // 目标面数
}

interface MeshyResponse {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  model_url?: string;       // glTF/GLB 下载地址
  thumbnail_url?: string;
}

async function generateModel(request: MeshyRequest): Promise<MeshyResponse> {
  const response = await fetch("https://api.meshy.ai/v1/text-to-3d", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.MESHY_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
  return response.json();
}
```

**Godot 兼容格式**：`.glb`, `.gltf`

#### Tripo3D

**用途**：高质量 3D 模型生成（备选）

**API 调用示例**：
```typescript
interface Tripo3DRequest {
  prompt: string;
  style: string;  // "game-ready" | "high-poly" | "stylized"
}
```

---

### 贴图生成

#### Stable Diffusion API

**用途**：2D 贴图、UI 素材、概念图生成

**API 调用示例**：
```typescript
interface SDRequest {
  prompt: string;
  negative_prompt?: string;
  width: number;      // 512, 768, 1024
  height: number;
  steps: number;      // 20-50
  cfg_scale: number;  // 7-12
  seed?: number;
}

async function generateTexture(request: SDRequest): Promise<Buffer> {
  const response = await fetch(`${process.env.SD_API_ENDPOINT}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.SD_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text_prompts: [{ text: request.prompt, weight: 1 }],
      cfg_scale: request.cfg_scale,
      width: request.width,
      height: request.height,
      steps: request.steps
    })
  });
  const data = await response.json();
  return Buffer.from(data.artifacts[0].base64, "base64");
}
```

**常用提示词模板**：

| 贴图类型 | 提示词模板 |
|----------|----------|
| 无缝贴图 | `seamless tileable {material} texture, top-down view, 4k, pbr` |
| 像素风格 | `pixel art {subject}, 16x16 sprite, transparent background` |
| UI 图标 | `game UI icon of {item}, flat design, transparent background` |
| 角色立绘 | `{character} character portrait, game art style, detailed` |

#### Leonardo.ai

**用途**：风格化贴图生成（备选）

---

### 音频生成

#### Suno AI

**用途**：背景音乐生成

**API 调用示例**：
```typescript
interface SunoRequest {
  prompt: string;         // 音乐描述
  duration: number;       // 秒数 (最大 120)
  genre?: string;         // "orchestral" | "electronic" | "ambient" ...
  mood?: string;          // "epic" | "peaceful" | "tense" ...
}

interface SunoResponse {
  task_id: string;
  status: string;
  audio_url?: string;     // MP3/WAV 下载地址
}
```

**常用音乐提示词**：

| 场景 | 提示词模板 |
|------|----------|
| 主菜单 | `epic orchestral main menu theme, game music, loop-ready` |
| 战斗 | `intense battle music, fast drums, orchestral, game soundtrack` |
| 探索 | `ambient exploration music, mysterious, calm, atmospheric` |
| Boss战 | `boss battle theme, dramatic, intense, choir, orchestral` |

#### ElevenLabs

**用途**：语音合成（NPC 对话、旁白）

**API 调用示例**：
```typescript
interface VoiceRequest {
  text: string;
  voice_id: string;
  model_id: string;       // "eleven_multilingual_v2"
  voice_settings: {
    stability: number;    // 0-1
    similarity_boost: number;
  };
}

async function generateVoice(request: VoiceRequest): Promise<Buffer> {
  const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${request.voice_id}`, {
    method: "POST",
    headers: {
      "xi-api-key": process.env.ELEVENLABS_API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
  return Buffer.from(await response.arrayBuffer());
}
```

---

## 资产下载与导入流程

### 下载资产

```typescript
async function downloadAsset(url: string, localPath: string): Promise<boolean> {
  const response = await fetch(url);
  const buffer = await response.arrayBuffer();
  
  // 写入到项目 assets 目录
  await fs.writeFile(localPath, Buffer.from(buffer));
  
  return true;
}
```

### 导入到 Godot

下载完成后，通过 MCP 工具通知 Godot 刷新资源：

```typescript
// 刷新文件系统
await callMcpTool("execute_editor_script", {
  script: `EditorInterface.get_resource_filesystem().scan()`
});
```

---

## 错误处理

### 常见错误码

| 错误码 | 含义 | 处理方式 |
|--------|------|----------|
| 401 | API Key 无效 | 提示用户检查 .env.local 配置 |
| 402 | 余额不足 | 提示用户充值或更换服务 |
| 429 | 请求过于频繁 | 等待后重试，增加间隔 |
| 500 | 服务器错误 | 重试或使用备选服务 |
| timeout | 请求超时 | 增加超时时间或重试 |

### 重试策略

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(r => setTimeout(r, delay * (i + 1)));
    }
  }
  throw new Error("Max retries exceeded");
}
```

---

## 费用估算参考

| 服务 | 单次调用成本 | 说明 |
|------|-------------|------|
| Meshy.ai | ~$0.20 | 单个 3D 模型 |
| Stable Diffusion | ~$0.01 | 单张图片 |
| Suno | ~$0.10 | 2分钟音乐 |
| ElevenLabs | ~$0.03 | 1000字符语音 |

建议：
- 开发阶段使用低分辨率/低质量设置测试
- 确认效果后再生成高质量版本
- 批量生成时注意 API 调用限制
