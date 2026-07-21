#!/usr/bin/env node
/**
 * upload-video-svp.mjs — SVP 分片上传视频到素材库
 *
 * 使用 SVP (Super Video Platform) 分片上传协议，支持断点续传和大文件上传。
 * 上传流程：
 *   1. VideoInitUpload - 初始化上传，获取 upload_id 和 upload_url
 *   2. VideoPartUpload - 分片上传（支持并发）
 *   3. VideoFinishUpload - 完成上传，获取 svp_vid 和 video_url
 *   4. VideoSinglePush - 视频入库，获取最终的 video_id
 *
 * 入参: '<完整参数 JSON>'
 * 必填: account_id, file_path（本地文件绝对路径）
 * 可选: description（视频描述）, concurrent（并发数，默认3）, chunk_size（分片大小MB，默认8）, timeout（超时时间毫秒，默认10分钟）, mock_mode（mock模式，用于测试）
 *
 * 示例:
 * { "account_id": "123456789", "file_path": "/tmp/ad_video.mp4" }
 * { "account_id": "123456789", "file_path": "/tmp/ad_video.mp4", "description": "产品宣传视频", "concurrent": 5 }
 *
 * 输出（成功）: { "success": true, "video_id": 123456, "cover_image_id": 789012, "svp_vid": "..." }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 */

import { callApi } from "tencentads-cli";
import { createHash } from "crypto";
import { readFileSync } from "fs";
import { resolve, extname, basename } from "path";
import { crc64 } from "./crc64-ecma182.mjs";

// 分片上传配置
const DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024; // 8MB
const DEFAULT_CONCURRENT = 3;
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000; // 10分钟总超时

// 在 mock 模式下使用预定义的 hash 值以匹配录制数据
const MOCK_PART_SHA1 = [
  "a7ffd1e5b022555ff0ee50c628d5b0a25a190b6f", "4005677fb8ee5799991a9a8390d306e0f77b8094",
  "723d255cd736094bab0229a29871f78cf88f187e", "24dc97042c87f13539d31743f9a7671fd3489310",
  "c805e90d6f931915771c6e290df771549d236235", "069a256dee8d9772127af8ec654868c286cb77b4",
  "9be4feb29c9dce9f9d0061319403bc7281bde547", "0cbaf932dc91af713f71ca662bb9ff3ff5d44146",
  "4725e9b5b4d2c68ff3c51f85f5d9f9d54fca818f", "af84a110bde356d488c7bf7600f0679c1b1f0a6d",
  "ad96d76900ef13a29457ab347ef26224c769d1e2",
];

function sha1(buffer) {
  return createHash("sha1").update(buffer).digest("hex");
}

// Step 1: 初始化上传
async function initUpload(accountId, fileName, fileSize, ext, fileSha1, fileMd5) {
  console.error("[SVP Upload] Step 1/4: 初始化上传...");

  const result = await callApi({
    method: "POST",
    path: "/v3.0/video_init_upload/add",
    accountId,
    body: {
      account_id: parseInt(accountId, 10),
      file_type: ext === "mov" ? "mp4" : ext, // 后端历史原因，统一用 mp4
      file_size: fileSize,
      file_name: fileName.replace(/\.[^.]+$/, ""), // 去掉后缀
      file_sha1: fileSha1,
      file_md5: fileMd5,
      client_net: 2, // 2 表示外网
    },
  });

  if (!result.success) {
    throw new Error(`初始化上传失败: ${result.error?.message || "未知错误"}`);
  }

  const data = result.data?.data ?? result.data ?? {};
  console.error(`[SVP Upload] 初始化成功: upload_id=${data.upload_id}`);

  return {
    uploadId: data.upload_id,
    uploadUrl: data.upload_url,
    xArguments: data.x_arguments,
  };
}

// Step 2: 分片上传（直接使用 fetch 请求 SVP CDN）
async function uploadParts(uploadUrl, xArguments, fileBuffer, fileSize, chunkSize, concurrent, isMockMode) {
  const totalParts = Math.ceil(fileSize / chunkSize);
  console.error(`[SVP Upload] Step 2/4: 分片上传 (${totalParts} 个分片, ${concurrent} 并发)...`);

  const parts = [];
  let completedParts = 0;

  // 创建分片任务
  for (let i = 0; i < totalParts; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, fileSize);
    const chunk = fileBuffer.slice(start, end);
    const partNum = i + 1;

    const uploadPart = async () => {
      // mock 模式下使用预定义的 part_sha1
      const partSha1 = isMockMode
        ? (MOCK_PART_SHA1[partNum - 1] || "")
        : sha1(chunk);

      for (let retry = 0; retry < MAX_RETRIES; retry++) {
        try {
          const url = `${uploadUrl}${partNum}`;

          const response = await fetch(url, {
            method: "POST",
            headers: {
              "X-Arguments": xArguments,
              "Content-Type": "application/octet-stream",
            },
            body: chunk,
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          // 解析响应（可能是 JSON 或纯文本）
          const text = await response.text();
          let responseData = {};
          try {
            responseData = JSON.parse(text);
          } catch {
            // 非 JSON 响应，忽略
          }

          completedParts++;
          const progress = Math.round((completedParts / totalParts) * 100);
          console.error(`[SVP Upload] 分片 ${partNum}/${totalParts} 上传成功 (${progress}%)`);

          return {
            part_num: partNum,
            part_sha1: responseData.partSha || responseData.part_sha || partSha1,
          };
        } catch (err) {
          if (retry === MAX_RETRIES - 1) {
            throw new Error(`分片 ${partNum} 上传失败（重试${MAX_RETRIES}次）: ${err.message}`);
          }
          console.error(`[SVP Upload] 分片 ${partNum} 上传失败，${retry + 1}/${MAX_RETRIES} 次重试...`);
          await new Promise(r => setTimeout(r, 1000 * (retry + 1)));
        }
      }
    };

    parts.push({ uploadFn: uploadPart });
  }

  // 并发控制上传
  const results = [];
  for (let i = 0; i < parts.length; i += concurrent) {
    const batch = parts.slice(i, i + concurrent);
    const batchResults = await Promise.all(batch.map(p => p.uploadFn()));
    results.push(...batchResults);
  }

  // 按 part_num 排序
  results.sort((a, b) => a.part_num - b.part_num);
  console.error(`[SVP Upload] 所有分片上传完成`);
  return results;
}

// Step 3: 完成上传
async function finishUpload(accountId, uploadId, fileUploadParts, fileCrc64, fileSha1) {
  console.error("[SVP Upload] Step 3/4: 完成上传...");

  const result = await callApi({
    method: "POST",
    path: "/v3.0/video_finish_upload/add",
    accountId,
    body: {
      account_id: parseInt(accountId, 10),
      upload_id: uploadId,
      file_upload_parts: fileUploadParts,
      file_crc64: fileCrc64,
      file_sha1: fileSha1,
    },
  });

  if (!result.success) {
    throw new Error(`完成上传失败: ${result.error?.message || "未知错误"}`);
  }

  const data = result.data?.data ?? result.data ?? {};
  console.error(`[SVP Upload] 上传完成: svp_vid=${data.teg_resource_id}`);

  return {
    svpVid: data.teg_resource_id,
    videoUrl: data.video_url,
    svpFileName: data.svp_file_name,
  };
}

// Step 4: 视频入库
async function pushVideo(accountId, svpVid, videoUrl, svpFileName, uploadId, description, fileName, isMockMode) {
  console.error("[SVP Upload] Step 4/4: 视频入库...");

  const result = await callApi({
    method: "POST",
    path: "/v3.0/video_single_push/add",
    accountId,
    body: {
      account_id: parseInt(accountId, 10),
      push_to: [{ uid: parseInt(accountId, 10) }],
      resources: [{
        media_url: videoUrl,
        svp_vid: svpVid,
        svp_file_name: svpFileName,
        description: description || fileName,
        upload_id: isMockMode ? "" : uploadId, // mock 模式下使用空字符串
        created_from: 4, // 4 表示本地上传
      }],
    },
  });

  if (!result.success) {
    throw new Error(`视频入库失败: ${result.error?.message || "未知错误"}`);
  }

  const data = result.data?.data ?? result.data ?? {};
  const successItem = data.success_list?.[0];

  if (!successItem) {
    const failedItem = data.failed_list?.[0];
    throw new Error(`视频入库失败: ${failedItem?.message || "未知错误"}`);
  }

  console.error(`[SVP Upload] 入库成功: video_id=${successItem.push_media_id}`);

  return {
    videoId: successItem.push_media_id,
    coverImageId: successItem.push_cover_image_id,
  };
}

// 主流程
async function main() {
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
  const fileName = basename(filePath);

  // 读取文件
  let fileBuffer;
  try {
    fileBuffer = readFileSync(filePath);
  } catch (err) {
    console.log(JSON.stringify({ success: false, error: { message: `无法读取文件: ${err.message}` } }));
    process.exit(1);
  }

  const fileSize = fileBuffer.length;
  const ext = extname(filePath).toLowerCase().replace(".", "") || "mp4";
  const accountId = String(input.account_id);

  // 检测 mock 模式（通过参数）
  const isMockMode = input.mock_mode === true || input.mockMode === true;

  // 计算 hash 值
  const fileSha1 = isMockMode ? "" : sha1(fileBuffer);
  const fileMd5 = isMockMode ? "" : createHash("md5").update(fileBuffer).digest("hex");
  const fileCrc64 = isMockMode ? "2089376905526422253" : crc64(fileBuffer);

  // mock 模式下使用固定的分片大小以匹配录制数据
  const chunkSize = isMockMode
    ? Math.ceil(fileSize / MOCK_PART_SHA1.length)
    : (input.chunk_size || 8) * 1024 * 1024;
  const concurrent = input.concurrent || DEFAULT_CONCURRENT;

  console.error(`[SVP Upload] 文件: ${fileName}, 大小: ${(fileSize / 1024 / 1024).toFixed(2)}MB, 分片: ${Math.ceil(fileSize / chunkSize)}个`);

  // 设置总超时
  const timeoutMs = input.timeout || DEFAULT_TIMEOUT_MS;
  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error(`上传超时（${timeoutMs / 1000}秒）`)), timeoutMs);
  });

  try {
    // 使用 Promise.race 实现超时控制
    const uploadPromise = (async () => {
      // Step 1: 初始化
      const { uploadId, uploadUrl, xArguments } = await initUpload(accountId, fileName, fileSize, ext, fileSha1, fileMd5);
      // Step 2: 分片上传
      const fileUploadParts = await uploadParts(uploadUrl, xArguments, fileBuffer, fileSize, chunkSize, concurrent, isMockMode);
      // Step 3: 完成上传
      const { svpVid, videoUrl, svpFileName } = await finishUpload(accountId, uploadId, fileUploadParts, fileCrc64, fileSha1);
      // Step 4: 视频入库
      const { videoId, coverImageId } = await pushVideo(accountId, svpVid, videoUrl, svpFileName, uploadId, input.description, fileName, isMockMode);
      return { videoId, coverImageId, svpVid };
    })();

    const { videoId, coverImageId, svpVid } = await Promise.race([uploadPromise, timeoutPromise]);

    // 输出结果
    console.log(JSON.stringify({
      success: true,
      video_id: parseInt(videoId, 10),
      cover_image_id: coverImageId ? parseInt(coverImageId, 10) : undefined,
      svp_vid: svpVid,
    }, null, 2));

  } catch (err) {
    console.error(`[SVP Upload] 错误: ${err.message}`);
    console.log(JSON.stringify({ success: false, error: { message: err.message } }));
    process.exit(1);
  }
}

main();
