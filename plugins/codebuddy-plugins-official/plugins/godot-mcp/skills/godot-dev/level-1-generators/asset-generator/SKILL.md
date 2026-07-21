---
name: asset-generator
description: >
  游戏资产生成技能。调用外部 AI 服务生成 3D 模型、贴图、音效等资产，
  并自动导入到 Godot 项目中。
version: 1.0.0
dependencies:
  - godot-core
  - file-manager
  - external-api
triggers:
  - pattern: "生成模型|生成贴图|生成材质|生成音乐|生成音效|生成角色|创建资产"
inputs:
  - name: asset_type
    type: string
    enum: ["model_3d", "texture", "sprite", "music", "sfx", "voice"]
    required: true
  - name: prompt
    type: string
    required: true
  - name: style
    type: string
    required: false
outputs:
  - name: asset_path
    type: string
    description: 生成的资产在项目中的路径
  - name: manifest_entry
    type: object
    description: 添加到 manifest.json 的条目
---

# 游戏资产生成技能

通过 AI 服务生成游戏资产，并自动导入 Godot 项目。

## 前置条件

1. 确保已配置相应服务的 API Key（见 external-api skill）
2. 确保项目目录结构已初始化

---

## 资产类型与服务映射

| 资产类型 | 首选服务 | 备选服务 | 输出格式 |
|----------|----------|----------|----------|
| 3D 模型 | Meshy.ai | Tripo3D | .glb |
| 贴图 | Stable Diffusion | Leonardo.ai | .png |
| 精灵图 | Stable Diffusion | - | .png |
| 背景音乐 | Suno | - | .ogg |
| 音效 | - | - | .wav |
| 语音 | ElevenLabs | - | .ogg |

---

## 3D 模型生成

### 生成流程

```
用户提示 → AI 生成 → 下载 GLB → 导入 Godot → 更新清单
```

### 提示词模板

#### 角色模型
```
{style} {character_type} character, game-ready model, T-pose, 
low-poly ({poly_count} triangles), clean topology, 
{texture_style} texture, full body
```

**示例**：
```
cartoon fantasy knight character, game-ready model, T-pose,
low-poly (5000 triangles), clean topology, 
hand-painted texture, full body
```

#### 道具模型
```
{item_name}, game prop, {style} style, 
{poly_count} polygons, centered, {material_description}
```

**示例**：
```
medieval sword, game prop, stylized fantasy style,
2000 polygons, centered, metallic blade with leather-wrapped handle
```

#### 环境模型
```
{environment_object}, game asset, modular, 
{style} style, optimized for games, {additional_details}
```

### 导入配置

```json
{
  "import_options": {
    "generate_collisions": false,
    "generate_lightmap_uv": false,
    "create_shadow_mesh": true,
    "scale": 1.0,
    "offset": [0, 0, 0],
    "import_animations": true
  }
}
```

### 生成后处理

1. **碰撞体生成**：复杂模型需手动或使用简化网格
2. **材质调整**：检查材质是否正确导入
3. **LOD 设置**：为大型模型设置细节层次

---

## 贴图生成

### 贴图类型

#### 无缝贴图（Tileable）
```
seamless tileable {material} texture, top-down view, 
high detail, 4k resolution, pbr ready, {additional_details}
```

**示例**：
```
seamless tileable stone floor texture, top-down view,
high detail, 4k resolution, pbr ready, medieval dungeon style
```

#### 精灵/角色
```
{character} sprite, {view} view, {style} style, 
transparent background, game asset, {size} pixels
```

**示例**：
```
pixel art knight sprite, side view, 16-bit style,
transparent background, game asset, 64x64 pixels
```

#### UI 图标
```
game UI icon, {item_name}, flat design style, 
{color_scheme} colors, transparent background, {size}x{size}
```

#### Tileset
```
2D game tileset, {theme} theme, {tile_size}x{tile_size} tiles,
{count} variations, top-down view, seamless edges
```

### 尺寸规范

| 用途 | 推荐尺寸 | 说明 |
|------|----------|------|
| 角色精灵 | 64x64, 128x128 | 2D 游戏角色 |
| UI 图标 | 32x32, 64x64 | 物品、技能图标 |
| 贴图 | 512x512, 1024x1024 | 3D 模型贴图 |
| 背景 | 1920x1080 | UI 背景 |
| Tileset | 16x16, 32x32 per tile | 地图瓦片 |

### 导入配置

```json
{
  "import_options": {
    "compress_mode": "lossless",
    "mipmaps": true,
    "filter": true,
    "repeat": "enabled",
    "size_limit": 0
  }
}
```

---

## 音频生成

### 背景音乐

#### 提示词模板
```
{genre} {mood} music, {tempo} bpm, {instruments},
game soundtrack, {duration} seconds, loop-ready
```

**场景音乐示例**：

| 场景 | 提示词 |
|------|--------|
| 主菜单 | `orchestral epic theme, moderate tempo, strings and brass, game soundtrack, 90 seconds, loop-ready` |
| 探索 | `ambient atmospheric music, slow, piano and synth pads, mysterious mood, 120 seconds, seamless loop` |
| 战斗 | `intense action music, fast 140bpm, drums and orchestra, battle theme, 60 seconds, loopable` |
| Boss 战 | `epic boss battle music, dramatic, choir and orchestra, intense and climactic, 90 seconds` |
| 胜利 | `triumphant victory fanfare, uplifting, brass and strings, short 15 seconds` |

### 音效

音效通常需要组合或后处理，建议：
1. 使用音效库（Freesound、Sonniss 等）
2. AI 生成基础音效后在 Audacity 中调整

**常用音效类型**：
- 脚步声（草地、石头、木板）
- 攻击/打击声
- 拾取物品
- UI 点击/悬停
- 环境音效（风、水、火）

### 语音生成

```typescript
interface VoiceConfig {
  character_name: string;
  voice_id: string;        // ElevenLabs voice ID
  personality: string;     // "wise old man" | "young hero" | "villain"
  emotion: string;         // "neutral" | "angry" | "sad" | "happy"
}

// 批量生成对话
interface DialogueLine {
  id: string;
  text: string;
  emotion?: string;
}
```

### 音频导入配置

```json
{
  "music_import": {
    "loop": true,
    "bpm": 120,
    "beat_count": 0
  },
  "sfx_import": {
    "loop": false
  }
}
```

---

## 资产清单管理

### manifest.json 结构

```json
{
  "version": "1.0.0",
  "last_updated": "2026-04-16T10:30:00Z",
  "assets": {
    "models": [],
    "textures": [],
    "audio": {
      "music": [],
      "sfx": [],
      "voice": []
    }
  }
}
```

### 资产条目格式

```json
{
  "id": "model_player_knight",
  "name": "Player Knight",
  "type": "model_3d",
  "path": "res://assets/models/characters/player_knight.glb",
  "source": {
    "service": "meshy.ai",
    "prompt": "cartoon fantasy knight character...",
    "generation_date": "2026-04-16T10:30:00Z",
    "task_id": "task_abc123"
  },
  "metadata": {
    "poly_count": 5000,
    "has_animations": true,
    "animations": ["idle", "walk", "run", "attack"],
    "materials": ["body", "armor", "weapon"]
  },
  "tags": ["player", "character", "knight", "humanoid"]
}
```

### 更新清单

```gdscript
func add_asset_to_manifest(asset_info: Dictionary) -> bool:
    var manifest_path = "res://assets/manifest.json"
    var manifest = load_json(manifest_path)
    
    if manifest == null:
        manifest = {
            "version": "1.0.0",
            "last_updated": "",
            "assets": {
                "models": [],
                "textures": [],
                "audio": {"music": [], "sfx": [], "voice": []}
            }
        }
    
    # 根据类型添加到对应数组
    var asset_type = asset_info.get("type", "")
    match asset_type:
        "model_3d":
            manifest.assets.models.append(asset_info)
        "texture", "sprite":
            manifest.assets.textures.append(asset_info)
        "music":
            manifest.assets.audio.music.append(asset_info)
        "sfx":
            manifest.assets.audio.sfx.append(asset_info)
        "voice":
            manifest.assets.audio.voice.append(asset_info)
    
    manifest.last_updated = Time.get_datetime_string_from_system()
    
    return save_json(manifest_path, manifest)
```

---

## 批量生成

### 从配置批量生成

```json
{
  "batch_generate": {
    "characters": [
      {
        "id": "player",
        "prompt_template": "cartoon {class} character",
        "variants": ["knight", "mage", "archer"]
      }
    ],
    "items": [
      {
        "category": "weapons",
        "items": ["sword", "staff", "bow"],
        "style": "fantasy medieval"
      }
    ]
  }
}
```

### 批量处理流程

```typescript
async function batchGenerate(config: BatchConfig): Promise<BatchResult[]> {
  const results: BatchResult[] = [];
  
  for (const item of config.items) {
    // 控制并发，避免 API 限制
    await delay(1000);
    
    const result = await generateAsset(item);
    results.push(result);
    
    // 更新进度
    console.log(`Generated ${results.length}/${config.items.length}`);
  }
  
  return results;
}
```

---

## 最佳实践

1. **提示词迭代**：先用低质量快速测试，确认效果后再生成高质量版本
2. **版本管理**：在清单中记录生成参数，方便重新生成
3. **统一风格**：在提示词中保持一致的风格描述词
4. **资源复用**：相似资产使用变体而非重新生成
5. **本地缓存**：避免重复生成相同资产

---

## AI 生图编排流程（需要后端服务支持）

> 此流程依赖 `godot-plugin-backend` 后端服务和 4 个内部 MCP 工具。

### 触发条件

用户自然语言中包含以下意图之一：
- 「生成 / 创建 / 做一个 图片 / 图标 / 贴图 / 背景 / 立绘 / 素材」
- 「generate / create image / icon / texture / sprite / asset」
- 明确提到尺寸、风格（像素 / 写实 / 动漫）+ 素材相关

### 编排步骤

#### 第 1 步：检查登录

调用 `check_auth` MCP 工具：

```
check_auth({ action: "check" })
```

- 返回 `authenticated: true` → 继续
- 返回 `authenticated: false` → 输出登录引导，告诉用户：
  「需要登录才能使用 AI 生图服务。请在浏览器中访问 {loginUrl} 完成 GitHub 授权。
   授权完成后，将页面显示的 Token 告诉我，我会帮你保存。」
- 用户提供 Token 后，调用 `check_auth({ action: "save", token: "..." })` 保存

#### 第 2 步：校验额度

调用 `get_user_quota` MCP 工具：

```
get_user_quota({})
```

- 返回 `sufficient: true` → 继续，告知用户当前剩余额度
- 返回 `sufficient: false` → 告诉用户「额度不足（剩余 0），请联系管理员申请更多额度」

#### 第 3 步：优化提示词

Skill 自身能力，根据游戏类型和 Godot 需求自动优化提示词：

| 游戏类型 | 自动追加的提示词 |
|----------|-----------------|
| 像素游戏 | `pixel art, 16-bit color, no anti-aliasing, game sprite` |
| 3D 游戏  | `PBR material, 4K resolution, seamless tiling` |
| UI 元素  | `flat design, transparent background, clean edges` |
| 通用     | `game asset, transparent background, no watermark` |

还会根据用户指定的尺寸自动适配，如果没指定则用合理默认值。

#### 第 4 步：请求生图

调用 `generate_image` MCP 工具：

```
generate_image({
  prompt: "用户原始提示词",
  optimizedPrompt: "Skill 优化后的完整提示词",
  width: 128,
  height: 128,
  style: "pixel",
  outputDir: "${gameDir}/assets/generated"
})
```

- 返回 `status: "SUCCESS"` → 获得 `localPath`，继续
- 返回 `error` → 告诉用户「生成失败：{message}，已自动退还额度」

#### 第 5 步：导入到 Godot 项目

调用 `import_to_godot` MCP 工具：

```
import_to_godot({
  sourcePath: "{generate_image 返回的 localPath}",
  targetDir: "${gameDir}/assets/icons",
  fileName: "coin.png"
})
```

- 将图片从临时目录复制到用户指定的项目目录
- 默认目录：`${gameDir}/assets/generated/`
- 用户可以指定：「导入到 assets/icons/」

#### 第 6 步：返回结果

- 成功：「✓ 已生成 [描述] 并导入到 [resPath]，剩余额度：XX」
- 失败：「✗ 生成失败：[错误原因]，已自动退还额度」

### 完整调用示例

用户说：「给我生成一个 128×128 的像素金币图标，放到 assets/icons/」

```
1. check_auth({ action: "check" })
   → authenticated: true, userName: "alice"

2. get_user_quota({})
   → remainingQuota: 47, sufficient: true

3. [Skill 优化提示词]
   原始: "128×128像素金币图标"
   优化: "128x128 pixel art gold coin icon, game asset, transparent background, no watermark, suitable for Godot engine, top-down view, 16-bit color"

4. generate_image({
     prompt: "128×128像素金币图标",
     optimizedPrompt: "128x128 pixel art gold coin icon, ...",
     width: 128, height: 128, style: "pixel"
   })
   → status: SUCCESS, localPath: "/tmp/generated_xxx.png", remainingQuota: 46

5. import_to_godot({
     sourcePath: "/tmp/generated_xxx.png",
     targetDir: "${gameDir}/assets/icons",
     fileName: "coin.png"
   })
   → success: true, resPath: "res://assets/icons/coin.png"

6. 返回：「✓ 已生成像素金币图标并导入到 res://assets/icons/coin.png，剩余额度：46」
```
