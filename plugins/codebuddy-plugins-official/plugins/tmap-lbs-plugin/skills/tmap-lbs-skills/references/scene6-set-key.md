## 场景六：设置 Web Service Key

当用户在对话中提供了腾讯地图 Web Service Key 时，将 Key 保存到环境变量或本地配置文件。

### 触发条件

- 用户说"我的 key 是 xxx"、"设置 key 为 xxx"
- 用户直接粘贴了一串类似 API Key 的字符串（如 `XXXXX-XXXXX-XXXXX-XXXXX-XXXXX`）
- 在场景二~五中提示用户提供 Key 后，用户回复了 Key 值

### 设置方式

**方式一：设置环境变量（推荐）**

```bash
export TMAP_WEBSERVICE_KEY=YOUR_TMAP_WEBSERVICE_KEY
```

**方式二：写入配置文件**

将 Key 写入 `config.json` 文件：

```bash
echo '{"apiToken":"YOUR_TMAP_WEBSERVICE_KEY"}' > config.json
```

### 执行步骤

1. **提取 Key**：从用户输入中识别出 Key 字符串
2. **基本校验**：检查 Key 长度是否合理（至少 10 个字符）
3. **保存 Key**：将 Key 写入环境变量或 `config.json` 文件
4. **确认结果**：提示用户设置成功

### 回复模板

设置成功时：

```
🔑 已成功保存你的腾讯地图 Web Service Key！

现在可以使用以下功能：
- 📍 POI 搜索
- 🛣️ 路径规划
- 🗺️ 旅游规划
- 📍 周边搜索
```

设置失败时：

```
❌ Key 设置失败，请检查 Key 是否正确后重试。

获取 Key: https://lbs.qq.com/dev/console/application/mine
```
