## 场景七：轨迹可视化

用户有一份包含轨迹坐标的数据（JSON 格式），希望在地图上以轨迹图的形式可视化展示。

**注意** 严格按照下面的步骤，不要生成代码或者调取其他脚本或者接口

### 触发条件

用户提到"轨迹"、"轨迹图"、"轨迹可视化"、"GPS 轨迹"、"运动轨迹"、"行驶轨迹"等意图，并提供了数据地址或轨迹数据。

### URL 格式

```
https://mapapi.qq.com/web/claw/trail-map.html?data={数据地址(URL编码)}
```

- **域名**：`mapapi.qq.com`
- **路由**：`/web/claw/trail-map.html`
- **必填参数**：
  - `data` = 轨迹数据的 URL 地址（**必须进行 URL 编码**）

### 执行步骤

#### 第一步：获取数据地址

从用户输入中提取轨迹数据的 URL 地址。

- 如果用户提供了一个 JSON 数据的 URL 地址，直接使用
- 如果用户未提供数据地址，提示用户给出数据链接

**请求数据地址的回复模板（用户未提供时）：**

```
📍 生成轨迹图需要你提供轨迹数据地址（JSON 格式的 URL），请给出数据链接。

轨迹数据格式示例：
- 数据为 JSON 数组，每个点包含经纬度信息
- 示例地址：https://mapapi.qq.com/web/claw/trail.json
```

#### 第二步：URL 编码

将数据地址进行 URL 编码（将 `://` → `%3A%2F%2F`，`/` → `%2F` 等）。

#### 第三步：拼接链接

将编码后的数据地址拼接到轨迹可视化 URL 中：

```
https://mapapi.qq.com/web/claw/trail-map.html?data={编码后的数据地址}
```

#### 第四步：返回链接给用户

### 完整示例

**用户输入：** "帮我用这份数据生成轨迹图：`https://mapapi.qq.com/web/claw/trail.json`"

1. 数据地址：`https://mapapi.qq.com/web/claw/trail.json`
2. URL 编码后的数据地址：`https%3A%2F%2Fmapapi.qq.com%2Fweb%2Fclaw%2Ftrail.json`
3. 最终链接：

```
https://mapapi.qq.com/web/claw/trail-map.html?data=https%3A%2F%2Fmapapi.qq.com%2Fweb%2Fclaw%2Ftrail.json
```

### 回复模板

```
📍 已为你生成轨迹可视化链接：

https://mapapi.qq.com/web/claw/trail-map.html?data={编码后的数据地址}

数据来源：{原始数据地址}

点击链接即可查看轨迹图展示。
```
