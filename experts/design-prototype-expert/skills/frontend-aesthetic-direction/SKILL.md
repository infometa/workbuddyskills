---
name: frontend-aesthetic-direction
description: "Generates 3-4 distinct aesthetic directions after starter kits have been rejected or when the user explicitly requests custom directions. Each direction has a clear aesthetic thesis, named color palette, font pairing with rationale, layout concept with ASCII wireframe, and a signature element. Rejects AI default aesthetics."
trigger:
  - 用户拒绝了所有预制模板（路径 A → 路径 B 降级）后
  - 用户明确要求从零定制美学方向时
  - DesignBrief 完成后，aesthetic-starter-kits 被拒绝后进入 ConceptRoutes 阶段时
---

# 美学方向（Frontend Aesthetic Direction）

## 触发时机

- 用户拒绝了所有预制模板（路径 A → 路径 B 降级）后，需要从零定制美学方向时
- 用户明确要求自定义美学方向时
- DesignBrief 完成后，aesthetic-starter-kits 被拒绝后进入 ConceptRoutes 阶段时

## 执行内容

给出 **3 到 4 个美学方向**，每个方向必须有明确的美学主张，**不能是模型的默认审美**（参见强禁止清单）。

### 每个方向必须包含

**1. 方向名称和一句话主张**
- 名称要有辨识度，不要"现代简约风"这种废话
- 主张说明这个方向的美学立场——它在反抗什么，在主张什么

**2. 配色方案（4 到 6 个命名色值）**
- 每个色值要有名字（如 "Midnight Ink #1a1a2e"）
- 说明主色、辅助色、强调色、中性色的角色分工
- 禁止紫色/蓝紫渐变、禁止奶油底+赤陶橙、禁止近黑底+酸性绿/朱红

**3. 字体配对（display + body）**
- 标题字体（display）+ 正文字体（body）
- 说明为什么选这对——它们在一起传达了什么气质
- 禁止 Inter、Roboto、Arial 或系统字体作为默认选择

**4. 布局概念（一句话描述 + ASCII 线框）**
- 一句话描述布局策略
- ASCII 线框展示大致结构

**5. 签名元素**
- 这个方向最被记住的一个独特视觉元素
- 不是"好看的渐变"这种泛泛之谈，而是一个具体的、可识别的设计决策

### 输出格式

```markdown
# ConceptRoutes

---

## 方向 A：{方向名称}

**主张**：{一句话美学主张}

### 配色方案
| 角色 | 色名 | 色值 |
|------|------|------|
| 主色 | {名称} | #{hex} |
| 辅助色 | {名称} | #{hex} |
| 强调色 | {名称} | #{hex} |
| 中性色 | {名称} | #{hex} |
| 背景色 | {名称} | #{hex} |

### 字体配对
- Display: {字体名} — {为什么选它}
- Body: {字体名} — {为什么选它}
- 配对理由: {它们在一起传达了什么}

### 布局概念
{一句话描述}

{ASCII 线框}

### 签名元素
{这个方向最被记住的独特元素}

---

## 方向 B：{...}

{同上结构}

---

## 方向 C：{...}

{同上结构}
```

## 注意事项

- 每个方向必须有**不同的美学主张**，不是同一个风格换个配色。
- **绝对禁止**以下三种 AI 默认审美（除非用户明确要求并注明是有意识选择）：
  1. 奶油底 + 高对比衬线 + 赤陶橙强调色
  2. 近黑底 + 单一亮色（酸性绿或朱红）
  3. 报纸风 + 零圆角 + 密集列
- 给出方向后让用户选择，不要替用户决定。
- 用与用户相同的语言输出。
