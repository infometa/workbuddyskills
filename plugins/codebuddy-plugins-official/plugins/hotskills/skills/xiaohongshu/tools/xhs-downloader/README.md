# XHS-Downloader 辅助工具

配合 [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) 使用的工具脚本，用于下载小红书收藏/点赞笔记并导出为 OpenClaw 记忆库格式。

## 依赖

需要先安装 XHS-Downloader：

```bash
git clone https://github.com/JoeanAmier/XHS-Downloader.git
cd XHS-Downloader
pip install -r requirements.txt
```

## 使用流程

### 1. 获取收藏/点赞链接（使用油猴脚本）

手动复制链接效率低，推荐使用 XHS-Downloader 提供的油猴脚本批量提取：

**安装脚本：**

1. 安装 [Tampermonkey](https://www.tampermonkey.net/) 浏览器扩展
2. 安装用户脚本：[XHS-Downloader.js](https://raw.githubusercontent.com/JoeanAmier/XHS-Downloader/refs/heads/master/static/XHS-Downloader.js)

**提取链接：**

1. 打开 [小红书网页版](https://www.xiaohongshu.com) 并登录
2. 进入个人主页 → **收藏** 或 **点赞** 页面
3. 点击 Tampermonkey 图标，选择：
   - `提取收藏作品链接`
   - `提取点赞作品链接`
4. 脚本会自动滚动页面加载全部内容
5. 提取完成后链接自动复制到剪贴板

**保存链接：**

将剪贴板内容粘贴到 `links.md` 文件：

```
https://www.xiaohongshu.com/explore/xxx?xsec_token=...
https://www.xiaohongshu.com/explore/yyy?xsec_token=...
```

> **注意**：自动滚动功能默认关闭，需在脚本设置中手动开启。开启后可能触发风控，建议适度使用。

### 2. 批量下载

```bash
# 在 XHS-Downloader 目录下运行
python batch_download.py links.md
```

下载的数据会保存到 `Volume/Download/ExploreData.db`。

### 3. 导出记忆库

**方式 A：导出为单文件**

```bash
python export_memory.py
# 生成 xhs_memory.md
```

**方式 B：导出为多文件（推荐用于 OpenClaw）**

```bash
python export_to_workspace.py
# 生成到 ~/.openclaw/workspace/xhs-memory/
```

### 4. 配置 OpenClaw 记忆搜索

编辑 `~/.openclaw/openclaw.json`，添加：

```json
{
  "memorySearch": {
    "extraPaths": [
      "~/.openclaw/workspace/xhs-memory"
    ]
  }
}
```

或者如果使用单文件导出，将 `xhs_memory.md` 放到 workspace 目录下。

## 脚本说明

| 脚本 | 功能 |
|------|------|
| `batch_download.py` | 批量下载笔记并记录到数据库 |
| `export_memory.py` | 导出为单个 Markdown 文件 |
| `export_to_workspace.py` | 导出为多个独立文件（按日期+标题命名） |

## 致谢

- [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) - GPL-3.0 License
