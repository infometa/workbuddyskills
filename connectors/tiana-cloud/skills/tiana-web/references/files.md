# WebApp 文件存储

CLI 文件操作要求 1.0.4 或更新正式版，使用 `tiana file --help` 核验命令入口。WebApp 文件能力还需目标环境提供配套的 MGR、Web 与 serverless-js Bootstrap；使用前核对目标环境能力。

## 归属和创建顺序

文件归当前租户，租户成员共享，用量与数据库共用存储配额。Console 和 CLI 展示整个租户文件目录；WebApp 使用其中的 `<WebApp ID>/` 子目录。应用只传相对路径，服务端确定 tenant 和 WebApp 根，不能从 JavaScript 修改授权范围。

先执行既有 `tiana web create` 获取 Web ID，再 `tiana web serve WEB_ID`。预览不要求先 publish，因此未发布应用也能访问自己的稳定文件目录。沿用已存在项目的真实 ID，不为一次预览另造 ID，也不把环境域名写死在应用里。

## 挂载 API

平台会在调用 `mount` 前准备文件访问。使用平台提供的 `context.files`：

```js
export async function mount(root, { files }) {
  const image = document.createElement('img');
  image.alt = '封面';
  root.append(image);
  const unbind = await files.bindImage(image, 'images/cover.png');
  return () => unbind();
}
```

- `files.list(path, { cursor })`：一页文件和目录，`items` 加下一页 `cursor`；只按用户所需导航，不为统计遍历全部目录。
- `files.get(path)`：下载 Response；`files.getUrl(path)`：下载域名 URL，仍需授权。
- `files.put(path, blob, options)`：直传 OSS，返回上传记录；可用 `onPrepared` 保留 ID、`onProgress` 显示进度。
- `files.delete(path)`：删除一个文件，UI 必须先确认用户意图。
- `files.bindImage(image, path)`：准备 URL 并绑定一次授权失败恢复，返回卸载函数。

Site Bootstrap 在导入应用模块前安装 15 分钟的 HttpOnly 文件 Cookie。`<img>` 请求会自动携带有效 Cookie，但原生标签不负责续期；优先用 `bindImage`，或在设置 `src` 前调用 `getUrl`。SDK 对授权失败最多刷新并重试一次，不把文件不存在当成授权过期。

本地预览使用同源 CLI broker，文件授权 Header 保留在 CLI 中；应用仍用同一个 `context.files`。上传数据在两种场景都直接去 OSS，平台接口仅签发和结算。不要自行读取 HttpOnly Cookie、复制数据库 Token 到文件域名，或把凭据拼进 URL。

```js
let uploadID;
const upload = await files.put('documents/note.txt', new Blob(['内容'], {
  type: 'text/plain',
}), {
  onPrepared: receipt => { uploadID = receipt.id; },
});
const downloadURL = await files.getUrl(upload.path);
```

同名默认拒绝。用户明确替换时才用 `{ overwrite: true }`，其行为是删除旧文件再上传；新上传失败无法恢复旧文件。签发凭据有效 30 分钟，预留本次完整大小；完成确认或后台到期核验后结算。关闭浏览器不取消后台核验。

上传结果不确定时保留 `uploadID`，调用 `files.uploadStatus(uploadID)`、`files.completeUpload(uploadID)` 检查，不重新执行替换。路径不能包含 `.`、`..`、反斜线和编码穿透片段。

## CLI 操作同一目录

```sh
tiana file list WEB_ID/images/
tiana file put ./cover.png WEB_ID/images/cover.png
tiana file get WEB_ID/images/cover.png ./downloaded-cover.png
tiana file get-url WEB_ID/images/cover.png
tiana file delete WEB_ID/images/cover.png
```

保持本任务选择的 `TIANA_API_ORIGIN`。CLI 操作租户根，所以访问应用文件时显式带真实 Web ID 子目录。`get-url` 的 URL 不是匿名分享链接；CLI 下载会另取并发送文件授权 Header。`put --overwrite` 同样先删除后上传，不能作为不确定结果的自动重试手段。
