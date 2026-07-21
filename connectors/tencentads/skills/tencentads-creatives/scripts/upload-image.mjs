#!/usr/bin/env node
/**
 * upload-image.mjs — 上传图片到素材库
 *
 * 读取本地图片文件，自动计算 MD5 签名，调用 images/add 接口上传到腾讯广告素材库。
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, file_path（本地文件绝对路径）
 * 可选: description（图片描述，≤255字节，不支持@等特殊符号）
 *       image_usage（图片用途：IMAGE_USAGE_DEFAULT | IMAGE_USAGE_MARKETING_PENDANT | IMAGE_USAGE_SHOP_IMG）
 *
 * 示例:
 * { "account_id": "123456789", "file_path": "/tmp/banner.jpg" }
 * { "account_id": "123456789", "file_path": "/tmp/banner.png", "description": "首页横幅" }
 *
 * 输出（成功）: { "success": true, "image_id": "xxx", "width": 1280, "height": 720, "preview_url": "..." }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 *
 * 文件格式限制: jpg / png / gif，最大 10MB，GIF 播放时长 ≤ 5 秒
 * 详细规范: references/materials/images-add.md
 */

import { callApi } from "tencentads-cli";
import { createHash } from "crypto";
import { readFileSync, statSync } from "fs";
import { resolve, extname } from "path";

let input;
try {
  const raw = process.argv[2] != null
    ? process.argv[2]
    : await new Promise(res => {
        let buf = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', d => (buf += d));
        process.stdin.on('end', () => res(buf.trim()));
      });
  if (!raw) throw new Error("缺少入参，请传入完整的 JSON 参数或通过 stdin 传入");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}` } }));
  process.exit(1);
}

for (const field of ["account_id", "file_path"]) {
  if (input[field] == null || input[field] === "") {
    console.log(JSON.stringify({ success: false, error: { message: `missing required field: ${field}` } }));
    process.exit(1);
  }
}

const filePath = resolve(input.file_path);

// 读取文件并计算 MD5
let fileBuffer;
try {
  fileBuffer = readFileSync(filePath);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `无法读取文件: ${err.message}` } }));
  process.exit(1);
}

const fileSizeBytes = statSync(filePath).size;
const MAX_SIZE = 10 * 1024 * 1024; // 10MB
if (fileSizeBytes > MAX_SIZE) {
  console.log(JSON.stringify({ success: false, error: { message: `文件大小 ${(fileSizeBytes / 1024 / 1024).toFixed(2)}MB 超过限制（最大 10MB）` } }));
  process.exit(1);
}

const ext = extname(filePath).toLowerCase().replace(".", "");
if (!["jpg", "jpeg", "png", "gif"].includes(ext)) {
  console.log(JSON.stringify({ success: false, error: { message: `不支持的图片格式 .${ext}，仅支持 jpg / png / gif` } }));
  process.exit(1);
}

const signature = createHash("md5").update(fileBuffer).digest("hex");
const accountId = String(input.account_id);

// 构建 multipart body（Base64 编码方式，避免 CLI 二进制流复杂度）
const base64Content = fileBuffer.toString("base64");

const body = {
  account_id: parseInt(accountId, 10),
  upload_type: "UPLOAD_TYPE_BYTES",
  bytes: base64Content,
  signature,
};
if (input.description) body.description = input.description;
if (input.image_usage) body.image_usage = input.image_usage;

const result = await callApi({
  method: "POST",
  path: "/v3.0/images/add",
  accountId,
  body,
});

if (!result.success) {
  console.log(JSON.stringify({ success: false, error: { message: `上传图片失败: ${result.error?.message}` } }));
  process.exit(1);
}

const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify({
  success: true,
  image_id: data.image_id,
  width: data.image_width,
  height: data.image_height,
  file_size: data.image_file_size,
  signature: data.image_signature,
  preview_url: data.preview_url,
}, null, 2));
