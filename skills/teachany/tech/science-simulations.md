# 🔬 科学实验模拟卫星文档（TeachAny · v7.9.5）

> **触发时机**：物理 / 化学 / 生物课件需要**交互式实验模拟**时加载。
> **定位**：在标准 Canvas 互动（基线 ③）之外，补充三类高质量科学可视化工具。
> **渐进披露**：本文档约 800 tokens，按需加载，不入必读骨架。

---

## 一、工具矩阵与选型

| 工具 | 适用学科 | 调用方式 | 离线 | 版权 |
|:---|:---|:---|:---:|:---|
| **PhET Interactive Simulations** | 物理/化学/生物/数学 | `<iframe>` 嵌入 | ✅ 可下载 HTML5 包 | 科罗拉多大学 CC-BY 4.0 |
| **Matter.js** | 物理（力学、碰撞、流体） | 纯 JS + `<canvas>` | ✅ 单文件 JS | MIT |
| **3Dmol.js** | 化学/生物（分子结构 3D） | 纯 JS + `<canvas>` | ✅ 单文件 JS | BSD-3 |
| **JSmol** | 化学（晶体、有机分子） | `<div>` + JS | ✅ 单文件 JS | LGPL |

**优先级判断**：
- 需要**完整实验情境**（已有精细 UI）→ PhET
- 需要**自定义物理世界**（两个小球碰撞演示动量守恒）→ Matter.js
- 需要**3D 分子**（DNA 双螺旋、水分子）→ 3Dmol.js
- 需要**晶体结构**（NaCl 晶格）→ JSmol

---

## 二、PhET 嵌入模板（最常用）

### 2.1 在线嵌入（推荐，课件打包更小）

```html
<section class="ta-standard-section" id="module-phet">
  <h2>🧪 互动实验：电路搭建</h2>
  <div class="phet-wrapper" style="position:relative;padding-top:66%;">
    <iframe
      src="https://phet.colorado.edu/sims/html/circuit-construction-kit-dc/latest/circuit-construction-kit-dc_zh_CN.html"
      style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;border-radius:12px"
      allowfullscreen
      loading="lazy">
    </iframe>
  </div>
  <p class="phet-hint">💡 拖拽电池、导线、灯泡，观察闭合回路时电流方向与灯泡亮度。</p>
</section>
```

### 2.2 离线嵌入（网络受限环境）

1. 访问 `https://phet.colorado.edu/zh_CN/simulations/filter?type=html` 下载 `.html` 文件
2. 放到 `<课件>/assets/phet/<sim-name>.html`
3. iframe src 改为 `./assets/phet/<sim-name>.html`

### 2.3 常用中文模拟清单（v7.9.6 实测命中率 91%）

以下 22 个常用 PhET HTML5 模拟全部经过 `curl -I` 实测，命中率 20/22。AI 制作课件时直接套用 URL 模板即可：

```
https://phet.colorado.edu/sims/html/<slug>/latest/<slug>_zh_CN.html
```

| 学科 | slug | 说明 | 中文版 |
|:---|:---|:---|:---:|
| **力学·运动** | `projectile-motion` | 抛体运动 | ✅ |
| 力学·运动 | `forces-and-motion-basics` | 力和运动基础 | ✅ |
| 力学·运动 | `friction` | 摩擦力 | ✅ |
| 力学·能量 | `energy-skate-park-basics` | 能量滑板公园 | ✅ |
| 力学·振动 | `pendulum-lab` | 单摆实验 | ✅ |
| 力学·振动 | `masses-and-springs` | 质量与弹簧 | ✅ |
| 力学·引力 | `gravity-and-orbits` | 引力与轨道 | ✅ |
| 力学·碰撞 | `collision-lab` | 碰撞实验室 | ✅ |
| **电磁·电路** | `circuit-construction-kit-dc` | 直流电路搭建 | ✅ |
| 电磁·电路 | `circuit-construction-kit-ac` | 交直流电路搭建 | ✅ |
| 电磁·电路 | `ohms-law` | 欧姆定律 | ✅ |
| 电磁·电路 | `resistance-in-a-wire` | 电阻 | ✅ |
| 电磁·磁 | `faradays-law` | 法拉第电磁感应 | ✅ |
| 电磁·静电 | `charges-and-fields` | 电荷与电场 | ✅ |
| 电磁·静电 | `coulombs-law` | 库仑定律 | ✅ |
| 波动·机械波 | `wave-on-a-string` | 绳波 | ✅ |
| 波动·机械波 | `waves-intro` | 波入门 | ✅ |
| **光学** | `bending-light` | 光的折射 | ✅ |
| 光学 | `geometric-optics` | 几何光学 | ✅ |
| 光学 | `color-vision` | 色觉 | ✅ |
| 化学·原子 | `build-an-atom` | 原子构建器 | ✅ |
| 数学·函数 | `function-builder` | 函数生成器 | ✅ |
| ⚠️ 失效 | `magnet-and-compass` | 磁铁与指南针 | ❌ 404 |
| ⚠️ 失效 | `sound-waves` | 声波 | ❌ 404 |

### 2.4 AI 自主搜索 PhET 资源的标准工作流（v7.9.6 新增）

当用户给的主题不在上方清单中时，AI 应**主动搜索**而不是问用户。流程：

```bash
# Step 1：用 LLM 知识储备先猜 5-8 个候选 slug（基于 PhET 命名惯例）
# 例如要做"动量守恒"课件，候选：
#   collision-lab / momentum-conservation / projectile-motion

# Step 2：对每个候选用 curl 实测中文版可达性
for sim in collision-lab momentum-conservation projectile-motion; do
  url="https://phet.colorado.edu/sims/html/${sim}/latest/${sim}_zh_CN.html"
  code=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 6 "$url")
  echo "$sim: $code"
done
# 输出：
#   collision-lab: 200          ← 用这个
#   momentum-conservation: 404
#   projectile-motion: 200      ← 也可

# Step 3：用 web_search 兜底（前两步都没 200 时）
#   关键词："PhET <主题> _zh_CN.html"
#   或访问 https://phet.colorado.edu/zh_CN/simulations/category/physics
```

**经验法则**：
- PhET slug 命名习惯：动名词或主题名 + 连字符（kebab-case），如 `bending-light`
- 不要用动词开头（"calculate-..."、"solve-..." 几乎都不存在）
- 中学物理几乎所有大主题都有覆盖；化学/生物较少
- `_zh_CN.html` 后缀仅适用于已翻译的模拟，未翻译的回退到 `_en.html`

---

## 三、Matter.js 物理引擎（自定义场景）

### 3.1 最小可用模板

```html
<canvas id="physics-sandbox" width="800" height="500" style="border:1px solid #ddd;border-radius:8px"></canvas>
<script src="https://cdn.jsdelivr.net/npm/matter-js@0.19.0/build/matter.min.js"></script>
<script>
  const { Engine, Render, Runner, Bodies, Composite, Mouse, MouseConstraint } = Matter;
  const engine = Engine.create();
  const render = Render.create({
    canvas: document.getElementById('physics-sandbox'),
    engine,
    options: { width: 800, height: 500, wireframes: false, background: '#f8fafc' }
  });
  // 搭建场景：地面 + 两个小球
  const ground = Bodies.rectangle(400, 490, 800, 20, { isStatic: true, render: { fillStyle: '#64748b' }});
  const ballA = Bodies.circle(300, 100, 30, { restitution: 0.7, render: { fillStyle: '#ef4444' }});
  const ballB = Bodies.circle(500, 100, 30, { restitution: 0.7, render: { fillStyle: '#3b82f6' }});
  Composite.add(engine.world, [ground, ballA, ballB]);
  // 鼠标拖拽
  const mouse = Mouse.create(render.canvas);
  Composite.add(engine.world, MouseConstraint.create(engine, { mouse, constraint: { stiffness: 0.2, render: { visible: false }}}));
  Render.run(render); Runner.run(Runner.create(), engine);
</script>
```

### 3.2 适用场景

- **碰撞演示**（弹性/非弹性碰撞，动量守恒）
- **斜面滑块**（重力分解、摩擦力）
- **弹簧振子**（用 `Constraint.create` 造弹簧）
- **多体问题**（行星运动近似）

⚠️ **不适合**：电磁场、波动、量子现象——这些要么用 PhET，要么用自定义 Canvas 直接画。

---

## 四、3Dmol.js 分子可视化

### 4.1 基础模板（显示 PDB 分子）

```html
<div id="mol-viewer" style="width:100%;height:400px;position:relative"></div>
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>
<script>
  const viewer = $3Dmol.createViewer('mol-viewer', { backgroundColor: '#fafafa' });
  // 方式 A：加载 PDB ID（需联网，首次加载）
  $3Dmol.download('pdb:1HHO', viewer, {}, function() {
    viewer.setStyle({}, { cartoon: { color: 'spectrum' }});
    viewer.zoomTo(); viewer.render();
  });
  // 方式 B：内联 SDF/MOL 数据（离线）
  // const waterSDF = `...`; viewer.addModel(waterSDF, 'sdf'); ...
</script>
```

### 4.2 常用显示风格

```javascript
// 球棍模型（最直观）
viewer.setStyle({}, { stick: {}, sphere: { radius: 0.4 }});
// 卡通带状（蛋白质二级结构）
viewer.setStyle({}, { cartoon: { color: 'spectrum' }});
// 表面（疏水/亲水可视化）
viewer.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.7, color: 'white' });
```

### 4.3 适用场景

- **小分子演示**（H₂O、CO₂、CH₄、乙醇）
- **蛋白质结构**（DNA 双螺旋、血红蛋白、酶）
- **晶体**（NaCl、金刚石）

**教学建议**：显示模型后 `viewer.rotate(..., 'animate')` 自动旋转演示，配合 TTS 讲解各部分结构。

---

## 五、与 TeachAny 基线能力的配合

| 基线条目 | 与本文档关系 |
|:---|:---|
| ③ Canvas 互动组件 | PhET / 3Dmol / Matter.js 均可**算作**合规 Canvas 组件（它们最终都渲染到 `<canvas>`） |
| ⑩ 历史地图 | 无关，但科学史课件可两者结合（如"伽利略斜面实验"用 Matter.js + 历史地图标注比萨） |
| ④ AI 生图 | **互补**：AI 生图做情境引入，PhET/3Dmol 做交互探究 |
| ② Remotion 视频 | **互补**：Remotion 做过程性讲解，PhET 做自由探究 |

---

## 六、自检清单

- [ ] 物理/化学/生物课件至少嵌入 1 个 PhET 或 Matter.js 模拟？
- [ ] PhET 使用**中文**本地化版本（URL 含 `_zh_CN`）？
- [ ] iframe/canvas 外围有提示文字（`💡 拖拽...观察...`）引导学生操作？
- [ ] 离线包已复制到 `<课件>/assets/` 或明确声明"需联网"？
- [ ] 3Dmol 分子有配套的"部位标注/讲解"文字（不能光转模型无文字）？

---

## 七、版本
- v7.9.5 · 2026-05-09 · 首次发布
- 与主文 SKILL_CN.md 的路由关系：在"技术实现延伸"表新增一行 → `tech/science-simulations.md`
