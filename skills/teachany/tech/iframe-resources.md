# 🌐 可嵌入 iframe 资源总目录（TeachAny · v7.12.2）

> **触发时机**：制作**任意学科**课件时，先查此表，优先嵌入已验证的高质量外部资源，而非重复造轮子。
> **实测状态**：所有 URL 均经过 `curl -I` 实测（2026-05-15），标注 ✅200 / ❌非200。

---

## 一、通用嵌入规范

```html
<!-- 标准 iframe 容器（响应式 16:9） -->
<div style="position:relative;width:100%;padding-top:62.5%;border-radius:12px;overflow:hidden;background:#0f172a">
  <iframe
    src="<URL>"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0"
    allowfullscreen
    loading="lazy"
    sandbox="allow-scripts allow-same-origin allow-forms allow-popups">
  </iframe>
</div>
<p style="font-size:12px;color:#64748b;margin-top:6px">💡 <提示文字，引导学生操作></p>
```

**sandbox 说明**：PhET / GeoGebra / Desmos 需要 `allow-scripts allow-same-origin`；H5P 需要加 `allow-forms`。

---

## 二、数学工具

| 工具 | URL 模板 | 中文 | 状态 | 适用场景 |
|:---|:---|:---:|:---:|:---|
| **GeoGebra Classic** | `https://www.geogebra.org/classic?lang=zh_CN` | ✅ | ✅ | 函数/几何/概率综合，推荐用 Deploy API 自建 applet |
| **GeoGebra Graphing** | `https://www.geogebra.org/graphing?lang=zh_CN` | ✅ | ✅ | 纯函数图像探索 |
| **GeoGebra Geometry** | `https://www.geogebra.org/geometry?lang=zh_CN` | ✅ | ✅ | 几何作图 |
| **GeoGebra 3D** | `https://www.geogebra.org/3d?lang=zh_CN` | ✅ | ✅ | 空间几何、立体图形 |
| **Desmos Calculator** | `https://www.desmos.com/calculator` | ✅ | ✅ | 函数图像+滑块探究（用 API 注入） |
| **Desmos Geometry** | `https://www.desmos.com/geometry` | ✅ | ✅ | 几何作图 |
| **PhET Function Builder** | `https://phet.colorado.edu/sims/html/function-builder/latest/function-builder_zh_CN.html` | ✅ | ✅ | 初中函数概念 |
| **Scratch embed** | `https://scratch.mit.edu/projects/<id>/embed` | ✅ | ✅ | 编程入门、互动游戏化练习 |

### GeoGebra Deploy API（推荐写法）

```html
<div id="ggb-applet" style="width:100%;max-width:840px;margin:0 auto"></div>
<script src="https://www.geogebra.org/apps/deployggb.js"></script>
<script>
window.addEventListener('load', () => {
  new GGBApplet({
    appName: "graphing",        // graphing / classic / geometry / 3d
    width: 800, height: 480,
    showMenuBar: false, showAlgebraInput: true, showToolBar: false,
    showResetIcon: true, language: "zh-CN",
    appletOnLoad(api) {
      // 示例：一次函数 y = kx + b，两个滑块
      api.evalCommand("k = 1");
      api.evalCommand("b = 0");
      api.evalCommand("f(x) = k * x + b");
      api.evalCommand("SetSliderRange[k, -5, 5]");
      api.evalCommand("SetSliderRange[b, -10, 10]");
      api.setColor("f", 59, 130, 246);
    }
  }, '5.0').inject('ggb-applet');
});
</script>
```

### Desmos API（推荐写法）

```html
<div id="desmos" style="width:100%;height:460px"></div>
<script src="https://www.desmos.com/api/v1.8/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6"></script>
<script>
const calc = Desmos.GraphingCalculator(document.getElementById('desmos'), {
  language: 'zh-CN', expressionsCollapsed: false
});
// 示例：正弦函数 a·sin(bx+c)
calc.setExpression({ id:'f', latex:'f(x)=a\\sin(bx+c)' });
calc.setExpression({ id:'a', latex:'a=1', sliderBounds:{ min:-3, max:3 }});
calc.setExpression({ id:'b', latex:'b=1', sliderBounds:{ min:0.1, max:5 }});
calc.setExpression({ id:'c', latex:'c=0', sliderBounds:{ min:-3.14, max:3.14 }});
</script>
```

---

## 三、物理模拟（PhET）

URL 模板：`https://phet.colorado.edu/sims/html/<slug>/latest/<slug>_zh_CN.html`

### 3.1 力学

| 知识点 | slug | 中文 | 状态 |
|:---|:---|:---:|:---:|
| 力和运动基础 | `forces-and-motion-basics` | ✅ | ✅ |
| 抛体运动 | `projectile-motion` | ✅ | ✅ |
| 摩擦力 | `friction` | ✅ | ✅ |
| 能量滑板公园 | `energy-skate-park-basics` | ✅ | ✅ |
| 单摆实验 | `pendulum-lab` | ✅ | ✅ |
| 质量与弹簧 | `masses-and-springs` | ✅ | ✅ |
| 引力与轨道 | `gravity-and-orbits` | ✅ | ✅ |
| 碰撞实验室 | `collision-lab` | ✅ | ✅ |

### 3.2 电磁

| 知识点 | slug | 中文 | 状态 |
|:---|:---|:---:|:---:|
| 直流电路搭建 | `circuit-construction-kit-dc` | ✅ | ✅ |
| 交直流电路 | `circuit-construction-kit-ac` | ✅ | ✅ |
| 欧姆定律 | `ohms-law` | ✅ | ✅ |
| 电阻 | `resistance-in-a-wire` | ✅ | ✅ |
| 法拉第电磁感应 | `faradays-law` | ✅ | ✅ |
| 电荷与电场 | `charges-and-fields` | ✅ | ✅ |
| 库仑定律 | `coulombs-law` | ✅ | ✅ |

### 3.3 光学 & 波动

| 知识点 | slug | 中文 | 状态 |
|:---|:---|:---:|:---:|
| 光的折射（弯折光线） | `bending-light` | ✅ | ✅ |
| 几何光学（透镜成像） | `geometric-optics` | ✅ | ✅ |
| 色觉 | `color-vision` | ✅ | ✅ |
| 绳波 | `wave-on-a-string` | ✅ | ✅ |
| 波入门 | `waves-intro` | ✅ | ✅ |

---

## 四、化学模拟（PhET + 其他）

### 4.1 PhET 化学（已实测）

| 知识点 | slug | 中文 | 状态 |
|:---|:---|:---:|:---:|
| 原子构建器 | `build-an-atom` | ✅ | ✅ |
| 配平化学方程式 | `balancing-chemical-equations` | ✅ | ✅ |
| 摩尔浓度 | `molarity` | ✅ | ✅ |
| 溶液浓度 | `concentration` | ✅ | ✅ |
| pH 标尺 | `ph-scale` | ✅ | ✅ |
| 酸碱溶液 | `acid-base-solutions` | ✅ | ✅ |
| 分子形状 | `molecule-shapes` | ✅ | ✅ |
| 物质状态（基础） | `states-of-matter-basics` | ✅ | ✅ |

### 4.2 3Dmol.js（分子 3D 可视化，无需 iframe）

```html
<div id="mol-viewer" style="width:100%;height:360px;position:relative;border-radius:12px;overflow:hidden"></div>
<script src="https://3Dmol.org/build/3Dmol-min.js"></script>
<script>
const viewer = $3Dmol.createViewer('mol-viewer', { backgroundColor:'#0f172a' });
// 方式A：在线加载（PDB ID，如水分子）
$3Dmol.download('cid:962', viewer, {}, () => {  // 962 = water
  viewer.setStyle({}, { stick:{}, sphere:{ radius:0.4 }});
  viewer.zoomTo(); viewer.render();
});
</script>
```

常用 PDB/CID：
- `cid:962` 水（H₂O）
- `cid:280` 二氧化碳（CO₂）  
- `cid:6334` 乙醇
- `cid:5793` 葡萄糖
- `pdb:1HHO` 血红蛋白

---

## 五、生物模拟（PhET + 其他）

### 5.1 PhET 生物

| 知识点 | slug | 中文 | 状态 |
|:---|:---|:---:|:---:|
| 基因表达（转录翻译） | `gene-expression-essentials` | ✅ | ✅ |
| 自然选择 | `natural-selection` | ✅ | ✅ |

### 5.2 其他生物可视化

| 工具 | 用途 | URL |
|:---|:---|:---|
| **3Dmol.js** | DNA 双螺旋、蛋白质结构 | `https://3Dmol.org/build/3Dmol-min.js` |
| **BioDigital Human** | 人体解剖（需账号） | `https://www.biodigital.com/` |

---

## 六、互动练习（语文/英语/通用）

| 工具 | 用途 | 嵌入方式 | 状态 |
|:---|:---|:---|:---:|
| **LearningApps** | 填空/配对/排序/单词游戏 | iframe embed 链接 | ✅ |
| **Wordwall** | 单词游戏/问答/配对 | 生成 iframe 代码 | ✅ |
| **H5P** | 互动视频/拖拽题/时间轴 | iframe embed | ✅ |
| **Scratch** | 互动故事/编程演示 | `https://scratch.mit.edu/projects/<id>/embed` | ✅ |

### LearningApps 嵌入流程

1. 访问 `https://learningapps.org/`，搜索或创建练习
2. 点击"嵌入" → 复制 iframe 代码（含 `src="https://learningapps.org/watch?app=<id>"`）
3. 直接粘贴入课件 HTML

### H5P 嵌入流程

1. 访问 `https://www.h5p.com/`（付费）或自建 H5P Hub
2. 创建内容 → 获取 embed 代码
3. 也可用 `<iframe src="https://h5p.org/h5p/embed/<id>">`

---

## 七、学科-工具快查表

| 学科 | 首选 | 备选 |
|:---|:---|:---|
| **初中数学** | GeoGebra Deploy API | Desmos API |
| **高中数学** | GeoGebra 3D / Desmos | PhET Function Builder |
| **初中物理** | PhET（力学/光学/电磁） | Matter.js |
| **高中物理** | PhET（电磁/波动） | Matter.js / GeoGebra 3D |
| **初中化学** | PhET（原子/方程/溶液） | 3Dmol.js |
| **高中化学** | PhET + 3Dmol.js | — |
| **生物** | PhET（基因/自然选择）+ 3Dmol.js | BioDigital |
| **语文/英语** | LearningApps / Wordwall | H5P |
| **编程** | Scratch embed | — |

---

## 八、嵌入自检清单

- [ ] iframe 外有提示文字（`💡 拖拽...观察...`）
- [ ] 使用中文本地化版本（`lang=zh_CN` 或 `_zh_CN.html`）
- [ ] sandbox 属性已设置（避免 XSS）
- [ ] 有 `loading="lazy"` 避免首屏加载过慢
- [ ] 移动端测试：iframe 在 375px 宽度下可正常显示和操作

---

## 版本
- v7.12.2 · 2026-05-15 · 首次发布，综合整理所有可嵌入 iframe 资源
