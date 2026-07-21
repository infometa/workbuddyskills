# 📐 数学动画与可视化卫星文档（TeachAny · v7.9.5）

> **触发时机**：数学课件需要**函数图像、几何变换、概率可视化**时加载。
> **定位**：在标准 Canvas 互动（基线 ③）之外，补充四类数学专用工具。
> **渐进披露**：本文档约 900 tokens，按需加载。

---

## 一、工具矩阵与选型

| 工具 | 适用场景 | 调用方式 | 离线 | 版权 |
|:---|:---|:---|:---:|:---|
| **GeoGebra** | 函数/几何/概率/微积分综合 | `<iframe>` + Deploy/Applet | ✅ | Apache-2.0 |
| **Desmos** | 函数图像、参数方程 | `<iframe>` + API | ❌ 需联网 | 免费商用需署名 |
| **p5.js** | 自定义数学动画（分形、曲线） | JS + `<canvas>` | ✅ | LGPL |
| **MathBox / Manim** | 高级 3D 数学动画 | 后处理视频 → mp4 | - | MIT |

**优先级判断**：
- 要做**交互式函数探索**（拖动参数看图像变化）→ GeoGebra 或 Desmos
- 要做**自定义曲线 / 分形 / 点运动轨迹** → p5.js
- 要做**高精度 3D 数学动画**（如讲向量场、流形）→ Manim 渲染成 mp4 走基线 ②

---

## 二、GeoGebra 嵌入（首选）

### 2.1 在线嵌入（最简单）

```html
<section class="ta-standard-section" id="module-geogebra">
  <h2>📈 探究：二次函数的参数影响</h2>
  <div style="width:100%;aspect-ratio:16/9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,.1)">
    <iframe
      src="https://www.geogebra.org/classic?lang=zh_CN"
      width="100%" height="100%" frameborder="0"
      allowfullscreen loading="lazy">
    </iframe>
  </div>
</section>
```

### 2.2 用 Deploy API 自建 applet（**强烈推荐，比找现成 ID 更可靠**）

⚠️ **重要更新（v7.9.6）**：我们曾尝试列出"经典 applet ID"清单（emn4j25f / GhU5n6kR 等），但 GeoGebra 资源 ID **会过期失效**——经实测 5/5 全部 404。改为用 Deploy API 现场自建，命中率 100%：

```html
<div id="ggb-applet" style="width:100%;max-width:840px"></div>
<script src="https://www.geogebra.org/apps/deployggb.js"></script>
<script>
  window.addEventListener('load', function() {
    const params = {
      appName: "graphing",     // graphing / classic / geometry / 3d
      width: 800, height: 480,
      showMenuBar: false, showAlgebraInput: true, showToolBar: false,
      showResetIcon: true, language: "zh-CN",
      appletOnLoad: function(api) {
        // 注入数学对象（GGB Script 语法）
        api.evalCommand("a = 1");
        api.evalCommand("b = 0");
        api.evalCommand("c = 0");
        api.evalCommand("f(x) = a*x^2 + b*x + c");
        api.evalCommand("SetSliderRange[a, -3, 3]");
        api.evalCommand("SetSliderRange[b, -5, 5]");
        api.evalCommand("SetSliderRange[c, -5, 5]");
        api.setColor("f", 59, 130, 246);
      }
    };
    new GGBApplet(params, '5.0').inject('ggb-applet');
  });
</script>
```

**为什么自建胜过找现成 ID**：
- ✅ 命中率 100%（不依赖第三方维护的 applet ID）
- ✅ 完全可定制（颜色、滑块范围、初始值）
- ✅ 可重复使用同一段代码生成不同主题（改 `evalCommand` 即可）
- ❌ 缺点：需要会写少量 GGB Script（但 ChatGPT/Claude 都熟）

### 2.3 找现成 applet（**仅作辅助参考，不可靠**）

如果你坚持要找现成 applet，访问 `https://www.geogebra.org/m/<id>` 浏览。但**不要在 skill / 课件中硬编码 applet ID**，因为：
- ID 会被原作者删除或改私有
- 中文版 applet 数量少，质量参差
- 嵌入代码长（每个 applet 一个独立 iframe）

---

## 三、Desmos 嵌入（函数图像专精）

```html
<div id="desmos-calc" style="width:100%;height:500px"></div>
<script src="https://www.desmos.com/api/v1.8/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"></script>
<script>
  const calc = Desmos.GraphingCalculator(document.getElementById('desmos-calc'), {
    language: 'zh-CN',
    expressionsCollapsed: false
  });
  calc.setExpression({ id: 'f', latex: 'f(x) = a \\cdot \\sin(b x + c)' });
  calc.setExpression({ id: 'a', latex: 'a = 1', sliderBounds: { min: -3, max: 3 }});
  calc.setExpression({ id: 'b', latex: 'b = 1', sliderBounds: { min: 0, max: 5 }});
  calc.setExpression({ id: 'c', latex: 'c = 0', sliderBounds: { min: -3.14, max: 3.14 }});
</script>
```

**注意**：Desmos API 免费 Key 仅供非商业课件使用。教研 / 营利场景须向 Desmos 申请授权。

---

## 四、p5.js 自定义数学动画

### 4.1 模板：函数图像逐段绘制

```html
<div id="p5-container"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
<script>
  new p5((p) => {
    let t = 0;
    p.setup = () => {
      const c = p.createCanvas(800, 400);
      c.parent('p5-container');
    };
    p.draw = () => {
      p.background(250);
      // 坐标轴
      p.stroke(180); p.line(0, 200, 800, 200); p.line(400, 0, 400, 400);
      // 正弦曲线逐帧推进
      p.stroke('#3b82f6'); p.strokeWeight(2); p.noFill();
      p.beginShape();
      for (let x = 0; x <= t; x += 2) {
        const y = 200 + 80 * p.sin((x - 400) * 0.02);
        p.vertex(x, y);
      }
      p.endShape();
      t = (t + 4) % 800;
    };
  });
</script>
```

### 4.2 典型数学场景

| 场景 | 关键 API |
|:---|:---|
| 函数图像逐帧绘制 | `beginShape()` + `vertex()` + `endShape()` |
| 分形（科赫雪花、曼德博集合） | 递归 + `translate/rotate` |
| 点运动轨迹（抛物线、摆线） | `push/pop` + 参数方程 |
| 向量场 | 网格 + `line(x, y, x+vx, y+vy)` |
| 概率模拟（蒙特卡洛求 π） | `random()` + 点计数 |

---

## 五、Manim（高级，渲染为 mp4 走基线 ②）

Manim 是 3Blue1Brown 的数学动画引擎。**不直接嵌入课件**，而是先渲染成 mp4 放入 `<课件>/assets/video/`，作为基线 ② Remotion 视频的**补充来源**（但基线 ② 本身要求 Remotion 渲染至少 1 段，Manim 只能作为额外加分项）。

```bash
pip install manim
manim -pql script.py SceneName  # 低质量预览
manim -pqh script.py SceneName  # 高质量最终渲染 1920x1080@30fps
```

**适用场景**：讲"极限"、"级数求和"、"矩阵变换"等需要严格数学符号同步的主题。

---

## 六、与 TeachAny 基线能力的配合

| 基线条目 | 与本文档关系 |
|:---|:---|
| ③ Canvas 互动组件 | GeoGebra applet / Desmos calc / p5.js canvas **均算合规** |
| ② Remotion 视频 | **补充来源**：Manim 渲染的 mp4 可作为 Remotion 视频的片段叠加 |
| ⑦ 知识图谱 | 数学课件的"函数图像"模块可作为知识图谱节点的跳转目标 |
| ⑪ TTS 悬浮播放器 | 在 GeoGebra 旁加 `<p data-tts>讲解步骤...</p>` 配合操作 |

---

## 七、自检清单

- [ ] 数学课件至少嵌入 1 个可交互工具（GeoGebra / Desmos / p5.js）？
- [ ] GeoGebra / Desmos 使用**中文**本地化（`language: 'zh-CN'` 或 URL 含 `_zh`）？
- [ ] iframe / canvas 外围有提示文字引导学生操作？
- [ ] 函数/参数命名用数学常规符号（a, b, c, f(x)），不用代码变量名（param1, val）？
- [ ] 默认参数值让初次打开图像**有意义**（不是空白或退化情况）？

---

## 八、版本
- v7.9.5 · 2026-05-09 · 首次发布
- 主文 SKILL_CN.md 的"技术实现延伸"表新增一行 → `tech/math-animations.md`
