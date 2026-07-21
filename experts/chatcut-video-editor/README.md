# ChatCut 视频剪辑专家

这是面向 WorkBuddy 的 ChatCut 专家安装包。安装并通过连接卡完成 ChatCut OAuth 授权后，专家可以在可编辑的 ChatCut 项目中完成素材导入、时间线剪辑、口播清理、字幕、转场、Motion Graphics、AI 素材生成、配音配乐、验证和导出。

## 使用方式

1. 在 WorkBuddy 中安装本 ZIP。
2. 首次召唤专家时，在内联连接卡中登录并授权 ChatCut。
3. 选择已有项目，或让专家创建新项目。
4. 提供素材和目标；专家会先完成可编辑时间线，只有在你明确要求时才导出成片。

本地附件和文件路径由专家通过安装包内置的 `chatcut-upload-media` 命令上传。用户和 Agent 都不需要查找插件安装目录或手动定位上传脚本。

## 示例

- 用我的素材剪一条 60 秒竖屏短视频，去掉口头禅并加字幕。
- 给这段口播补 B-roll、转场、动效和背景音乐。
- 生成一段英文旁白和配乐，制作一条 16:9 产品介绍视频。
- 导出当前项目为 1080p H.264 MP4。

## 边界

- 生成视频、图片、音乐、配音、音效、Shader 或 Motion Graphics 可能消耗 ChatCut credits；专家会在提交付费生成任务前说明并确认。
- 实时屏幕/摄像头录制、直接修改 Premiere/Resolve/FCP 工程、向社交平台发布或排期不属于本专家能力。
- 本包不保存 ChatCut 密码、OAuth token 或其他用户密钥。

支持与产品信息：[chatcut.io](https://chatcut.io)
