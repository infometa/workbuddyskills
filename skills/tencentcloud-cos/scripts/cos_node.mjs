#!/usr/bin/env node
/**
 * 腾讯云 COS Node.js SDK 统一操作脚本
 * 基于 cos-nodejs-sdk-v5，覆盖 COS 存储 + 数据万象(CI) 全部能力
 *
 * 依赖：npm install cos-nodejs-sdk-v5
 * 凭证通过环境变量读取：
 *   TENCENT_COS_SECRET_ID / TENCENT_COS_SECRET_KEY / TENCENT_COS_REGION / TENCENT_COS_BUCKET
 *   TENCENT_COS_TOKEN（可选，STS 临时凭证）
 *   TENCENT_COS_DATASET_NAME（可选，MetaInsight 数据集名称）
 *
 * 用法：node cos_node.mjs <action> [options]
 */

import { createRequire } from "module";
import { createReadStream, createWriteStream, existsSync, readFileSync, statSync, writeFileSync, unlinkSync, chmodSync } from "fs";
import { basename, resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { pipeline } from "stream/promises";
import crypto from "crypto";

const require = createRequire(import.meta.url);
const COS = require("cos-nodejs-sdk-v5");

// ========== 凭证加解密工具 ==========

const __dirname = dirname(fileURLToPath(import.meta.url));
const envPath = resolve(__dirname, "..", ".env");
const envEncPath = resolve(__dirname, "..", ".env.enc");

// 基于机器特征派生 AES-256 密钥（hostname + username + 项目绝对路径）
// 同一台机器、同一用户、同一项目目录才能解密，防止 .env.enc 被拷贝到其他环境后解密
function deriveKeySync() {
  const os = require("os");
  const seed = `${os.hostname()}:${os.userInfo().username}:${resolve(__dirname, "..")}`;
  return crypto.createHash("sha256").update(seed).digest();
}

function encryptEnv(plaintext) {
  const key = deriveKeySync();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(plaintext, "utf-8"), cipher.final()]);
  const authTag = cipher.getAuthTag();
  // 格式：iv(12) + authTag(16) + ciphertext
  return Buffer.concat([iv, authTag, encrypted]);
}

function decryptEnv(encBuffer) {
  const key = deriveKeySync();
  const iv = encBuffer.subarray(0, 12);
  const authTag = encBuffer.subarray(12, 28);
  const ciphertext = encBuffer.subarray(28);
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(authTag);
  return decipher.update(ciphertext, undefined, "utf-8") + decipher.final("utf-8");
}

function parseEnvContent(content) {
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const eqIndex = trimmed.indexOf("=");
    if (eqIndex === -1) {
      continue;
    }
    const key = trimmed.slice(0, eqIndex).trim();
    let value = trimmed.slice(eqIndex + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    // 环境变量优先，.env 文件仅做兜底
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

// ========== 加载凭证 ==========
// 优先级：环境变量 > .env.enc（加密） > .env（明文，兼容旧版）
// .env.enc 解密失败时自动 fallback 到 .env（兼容老用户迁移场景）

let _credentialSource = "env";

if (existsSync(envEncPath)) {
  try {
    const encBuffer = readFileSync(envEncPath);
    const plaintext = decryptEnv(encBuffer);
    parseEnvContent(plaintext);
    _credentialSource = "env.enc";
  } catch {
    // .env.enc 解密失败，可能是跨机器/用户拷贝的，fallback 到 .env
    if (existsSync(envPath)) {
      parseEnvContent(readFileSync(envPath, "utf-8"));
      _credentialSource = "env(fallback)";
    }
  }
} else if (existsSync(envPath)) {
  parseEnvContent(readFileSync(envPath, "utf-8"));
  _credentialSource = "env";
}

// ========== 环境变量 ==========

const SecretId = process.env.TENCENT_COS_SECRET_ID;
const SecretKey = process.env.TENCENT_COS_SECRET_KEY;
const Token = process.env.TENCENT_COS_TOKEN;

// 默认值（可被 --bucket / --region / --dataset-name 等参数覆盖）
let Region = process.env.TENCENT_COS_REGION;
let Bucket = process.env.TENCENT_COS_BUCKET;
let DatasetName = process.env.TENCENT_COS_DATASET_NAME;
const Domain = process.env.TENCENT_COS_DOMAIN;
const ServiceDomain = process.env.TENCENT_COS_SERVICE_DOMAIN;
const Protocol = process.env.TENCENT_COS_PROTOCOL;

if (!SecretId || !SecretKey) {
  console.error(
    JSON.stringify({
      success: false,
      error: "缺少环境变量，需要：TENCENT_COS_SECRET_ID, TENCENT_COS_SECRET_KEY。Region/Bucket 可通过环境变量或 --region/--bucket 参数指定。",
    })
  );
  process.exit(1);
}

const cosOptions = { SecretId, SecretKey };
cosOptions.UserAgent = "skills/node_sdk_cos";
if (Token) {
  cosOptions.SecurityToken = Token;
}
if (Domain) {
  cosOptions.Domain = Domain;
}
if (ServiceDomain) {
  cosOptions.ServiceDomain = ServiceDomain;
}
if (Protocol) {
  cosOptions.Protocol = Protocol;
}

const cos = new COS(cosOptions);

// ========== 工具函数 ==========

function parseArgs(args) {
  const result = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const next = args[i + 1];
      if (next && !next.startsWith("--")) {
        result[key] = next;
        i++;
      } else {
        result[key] = true;
      }
    }
  }
  return result;
}

function output(data) {
  console.log(JSON.stringify(data, null, 2));
}

function cosPromise(method, params) {
  return new Promise((resolveP, rejectP) => {
    cos[method]({ Bucket, Region, ...params }, (err, data) => {
      if (err) {
        rejectP(err);
      } else {
        resolveP(data);
      }
    });
  });
}

function cosRequestPromise(params) {
  return new Promise((resolveP, rejectP) => {
    cos.request(params, (err, data) => {
      if (err) {
        rejectP(err);
      } else {
        resolveP(data);
      }
    });
  });
}

function generateCode(length = 6) {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
  const randomBytes = crypto.randomBytes(length);
  let code = "";
  for (let i = 0; i < length; i++) {
    code += chars[randomBytes[i] % chars.length];
  }
  return code;
}

function generateOutputFileId(objectKey) {
  const now = new Date();
  const date = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("");
  if (objectKey) {
    const lastDot = objectKey.lastIndexOf(".");
    const base = lastDot === -1 ? objectKey : objectKey.substring(0, lastDot);
    return encodeURIComponent(`${date}_${base}_${generateCode()}`);
  }
  return encodeURIComponent(`${date}_${generateCode()}`);
}

function ciHost() {
  return `${Bucket}.ci.${Region}.myqcloud.com`;
}

function appId() {
  return Bucket.split("-").pop();
}

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ========== COS 存储操作 ==========

async function upload(opts) {
  const filePath = opts.file;
  const key = opts.key || basename(filePath);
  if (!filePath) {
    throw new Error("缺少 --file 参数");
  }
  if (!existsSync(filePath)) {
    throw new Error(`文件不存在：${filePath}`);
  }
  const data = await cosPromise("putObject", {
    Key: key,
    Body: createReadStream(filePath),
    ContentLength: statSync(filePath).size,
  });
  output({ success: true, action: "upload", key, etag: data.ETag, location: data.Location, statusCode: data.statusCode });
}

async function putString(opts) {
  const { content, key } = opts;
  const contentType = opts["content-type"] || "text/plain";
  if (!content) {
    throw new Error("缺少 --content 参数");
  }
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosPromise("putObject", { Key: key, Body: content, ContentType: contentType });
  output({ success: true, action: "put-string", key, etag: data.ETag, location: data.Location, statusCode: data.statusCode });
}

async function download(opts) {
  const { key } = opts;
  const outputPath = opts.output || basename(key);
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosPromise("getObject", { Key: key });
  const resolvedPath = resolve(outputPath);
  const ws = createWriteStream(resolvedPath);
  if (data.Body instanceof Buffer) {
    ws.write(data.Body);
    ws.end();
  } else if (data.Body && typeof data.Body.pipe === "function") {
    await pipeline(data.Body, ws);
  } else {
    ws.write(String(data.Body));
    ws.end();
  }
  output({ success: true, action: "download", key, savedTo: resolvedPath, contentLength: data.headers?.["content-length"], statusCode: data.statusCode });
}

async function list(opts) {
  const prefix = opts.prefix || "";
  const maxKeys = parseInt(opts["max-keys"], 10) || 100;
  const data = await cosPromise("getBucket", { Prefix: prefix, MaxKeys: maxKeys });
  const files = (data.Contents || []).map((item) => ({
    key: item.Key,
    size: parseInt(item.Size, 10),
    lastModified: item.LastModified,
    etag: item.ETag,
    storageClass: item.StorageClass,
  }));
  output({ success: true, action: "list", prefix, count: files.length, isTruncated: data.IsTruncated === "true", files });
}

async function signUrl(opts) {
  const { key } = opts;
  const expires = parseInt(opts.expires, 10) || 3600;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const url = await new Promise((resolveP, rejectP) => {
    cos.getObjectUrl({ Bucket, Region, Key: key, Expires: expires, Sign: true }, (err, data) => {
      if (err) {
        rejectP(err);
      } else {
        resolveP(data.Url);
      }
    });
  });
  output({ success: true, action: "sign-url", key, expires, url });
}

async function deleteObject(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosPromise("deleteObject", { Key: key });
  output({ success: true, action: "delete", key, statusCode: data.statusCode });
}

async function head(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosPromise("headObject", { Key: key });
  output({
    success: true,
    action: "head",
    key,
    contentLength: parseInt(data.headers?.["content-length"], 10),
    contentType: data.headers?.["content-type"],
    etag: data.headers?.etag,
    lastModified: data.headers?.["last-modified"],
    storageClass: data.headers?.["x-cos-storage-class"] || "STANDARD",
    statusCode: data.statusCode,
  });
}

// ========== COS 存储桶管理 ==========

// 安全防护：禁止删除和清空存储桶
const FORBIDDEN_ACTIONS = ["deleteBucket"];
function guardBucketSafety(action) {
  if (FORBIDDEN_ACTIONS.includes(action)) {
    throw new Error(`🚫 安全限制：禁止执行 ${action} 操作。删除/清空存储桶操作被本技能明确禁止。`);
  }
}

async function listBuckets(opts) {
  const data = await new Promise((resolveP, rejectP) => {
    cos.getService({ Region: opts.region || "" }, (err, data) => (err ? rejectP(err) : resolveP(data)));
  });
  const buckets = (data.Buckets || []).map((b) => ({
    name: b.Name,
    region: b.Location,
    createDate: b.CreationDate,
  }));
  output({ success: true, action: "list-buckets", count: buckets.length, buckets });
}

async function createBucket(opts) {
  const bucketName = opts.bucket || opts.name;
  const region = opts.region || Region;
  if (!bucketName) {
    throw new Error("缺少 --bucket 参数（格式 name-appid）");
  }
  const data = await new Promise((resolveP, rejectP) => {
    cos.putBucket({ Bucket: bucketName, Region: region }, (err, data) => (err ? rejectP(err) : resolveP(data)));
  });
  output({ success: true, action: "create-bucket", bucket: bucketName, region, data });
}

async function headBucket(opts) {
  const bucketName = opts.bucket || Bucket;
  const region = opts.region || Region;
  const data = await new Promise((resolveP, rejectP) => {
    cos.headBucket({ Bucket: bucketName, Region: region }, (err, data) => (err ? rejectP(err) : resolveP(data)));
  });
  output({ success: true, action: "head-bucket", bucket: bucketName, region, data });
}

async function getBucketAcl(opts) {
  const data = await cosPromise("getBucketAcl", {});
  output({ success: true, action: "get-bucket-acl", data });
}

async function putBucketAcl(opts) {
  const acl = opts.acl || "private";
  const data = await cosPromise("putBucketAcl", { ACL: acl });
  output({ success: true, action: "put-bucket-acl", acl, data });
}

async function getBucketCors(opts) {
  const data = await cosPromise("getBucketCors", {});
  output({ success: true, action: "get-bucket-cors", data });
}

async function putBucketCors(opts) {
  const origin = opts.origin || "*";
  const methods = (opts.methods || "GET,POST,PUT,DELETE,HEAD").split(",");
  const data = await cosPromise("putBucketCors", {
    CORSRules: [{ AllowedOrigin: [origin], AllowedMethod: methods, AllowedHeader: ["*"], MaxAgeSeconds: 600 }],
  });
  output({ success: true, action: "put-bucket-cors", data });
}

async function getBucketTagging(opts) {
  try {
    const data = await cosPromise("getBucketTagging", {});
    output({ success: true, action: "get-bucket-tagging", data });
  } catch (err) {
    if (err.code === "NoSuchTagSet") {
      output({ success: true, action: "get-bucket-tagging", data: { Tags: [] } });
    } else {
      throw err;
    }
  }
}

async function putBucketTagging(opts) {
  const tags = opts.tags ? JSON.parse(opts.tags) : [];
  if (!tags.length) {
    throw new Error('缺少 --tags 参数（JSON 数组，如 \'[{"Key":"env","Value":"prod"}]\'）');
  }
  const data = await cosPromise("putBucketTagging", { Tags: tags });
  output({ success: true, action: "put-bucket-tagging", data });
}

async function getBucketVersioning(opts) {
  const data = await cosPromise("getBucketVersioning", {});
  output({ success: true, action: "get-bucket-versioning", data });
}

async function getBucketLifecycle(opts) {
  try {
    const data = await cosPromise("getBucketLifecycle", {});
    output({ success: true, action: "get-bucket-lifecycle", data });
  } catch (err) {
    if (err.code === "NoSuchLifecycleConfiguration") {
      output({ success: true, action: "get-bucket-lifecycle", data: { Rules: [] } });
    } else {
      throw err;
    }
  }
}

async function getBucketLocation(opts) {
  const data = await cosPromise("getBucketLocation", {});
  output({ success: true, action: "get-bucket-location", data });
}

async function copyObject(opts) {
  const { source, key } = opts;
  if (!source || !key) {
    throw new Error("缺少 --source 和 --key 参数。--source 格式：bucket.cos.region.myqcloud.com/sourceKey");
  }
  const data = await cosPromise("putObjectCopy", { Key: key, CopySource: source });
  output({ success: true, action: "copy-object", key, data });
}

async function deleteMultipleObjects(opts) {
  const keys = opts.keys ? JSON.parse(opts.keys) : [];
  if (!keys.length) {
    throw new Error('缺少 --keys 参数（JSON 数组，如 \'["file1.txt","file2.txt"]\'）');
  }
  const objects = keys.map((k) => ({ Key: k }));
  const data = await cosPromise("deleteMultipleObject", { Objects: objects });
  output({ success: true, action: "delete-multiple", count: keys.length, data });
}

// ========== CI 图片基础处理 ==========

async function imageInfo(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Action: "imageInfo",
    RawBody: false,
  });
  output({ success: true, action: "image-info", key, data });
}

async function watermarkFont(opts) {
  const { key, text } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  if (!text) {
    throw new Error("缺少 --text 参数");
  }
  const encodedText = Buffer.from(text).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const rule = ["watermark/2", `text/${encodedText}`, "scatype/3", "spcent/20"].join("/");
  const outFileId = generateOutputFileId(key);
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ rules: [{ fileid: outFileId, rule }] }) },
  });
  output({ success: true, action: "watermark-font", key, data });
}

// ========== CI AI 图片处理 ==========

async function assessQuality(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "AssessQuality" },
  });
  output({ success: true, action: "assess-quality", key, data });
}

async function aiSuperResolution(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const outFileId = generateOutputFileId(key);
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ rules: [{ fileid: outFileId, rule: "ci-process=AISuperResolution" }] }) },
  });
  output({ success: true, action: "ai-super-resolution", key, data });
}

async function aiPicMatting(opts) {
  const { key, width, height } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const outFileId = generateOutputFileId(key);
  let rule = "ci-process=AIImageCrop";
  if (width) {
    rule += `&width=${width}`;
  }
  if (height) {
    rule += `&height=${height}`;
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ rules: [{ fileid: outFileId, rule }] }) },
  });
  output({ success: true, action: "ai-pic-matting", key, data });
}

async function aiQrcode(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "QRcode", cover: 0 },
  });
  output({ success: true, action: "ai-qrcode", key, data });
}

// ========== CI 文档处理 ==========

async function createDocToPdfJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const lastDot = key.lastIndexOf(".");
  const base = lastDot === -1 ? key : key.substring(0, lastDot);
  const now = new Date();
  const date = [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0"), String(now.getDate()).padStart(2, "0")].join("");
  const outObject = `${date}_\${SheetID}/${base}_pdf_${generateCode(6)}.pdf`;

  const url = `https://${ciHost()}/doc_jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "DocProcess",
      Input: { Object: key },
      Operation: {
        DocProcess: { TgtType: "pdf" },
        Output: { Bucket, Region, Object: outObject },
      },
    },
  });

  const createResult = await cosRequestPromise({ Key: "doc_jobs", Method: "POST", Url: url, Body: body, ContentType: "application/xml" });
  const jobsDetail = createResult?.Response?.JobsDetail;

  if (jobsDetail?.Code === "Failed") {
    output({ success: false, action: "create-doc-to-pdf-job", data: createResult });
    return;
  }
  if (jobsDetail?.State === "Success") {
    output({ success: true, action: "create-doc-to-pdf-job", data: createResult });
    return;
  }

  const jobId = jobsDetail?.JobId;
  if (!jobId) {
    output({ success: true, action: "create-doc-to-pdf-job", jobId: null, data: createResult });
    return;
  }

  const maxAttempts = 10;
  const interval = 2000;
  for (let i = 0; i < maxAttempts; i++) {
    if (i > 0) {
      await sleep(interval);
    }
    const queryUrl = `https://${ciHost()}/doc_jobs/${jobId}`;
    const qResult = await cosRequestPromise({ Bucket, Region, Method: "GET", Key: `doc_jobs/${jobId}`, Url: queryUrl });
    const detail = qResult?.Response?.JobsDetail;
    if (detail?.Code === "Success" && detail?.State === "Success") {
      output({ success: true, action: "create-doc-to-pdf-job", jobId, data: qResult });
      return;
    }
    if (detail?.Code === "Failed") {
      output({ success: false, action: "create-doc-to-pdf-job", jobId, data: qResult });
      return;
    }
  }
  output({ success: false, action: "create-doc-to-pdf-job", jobId, error: `轮询超时（${maxAttempts}次未完成）`, data: createResult });
}

async function describeDocProcessJob(opts) {
  const jobId = opts["job-id"] || opts.jobId;
  if (!jobId) {
    throw new Error("缺少 --job-id 参数");
  }
  const url = `https://${ciHost()}/doc_jobs/${jobId}`;
  const data = await cosRequestPromise({ Bucket, Region, Method: "GET", Key: `doc_jobs/${jobId}`, Url: url });
  output({ success: true, action: "describe-doc-job", jobId, data });
}

// ========== CI 媒体处理 ==========

async function createMediaSmartCoverJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const lastDot = key.lastIndexOf(".");
  const base = lastDot === -1 ? key : key.substring(0, lastDot);
  const outObject = `${base}_\${jobid}_\${number}`;
  const url = `https://${ciHost()}/jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "SmartCover",
      Input: { Object: key },
      Operation: {
        Output: { Bucket, Region, Object: outObject },
        SmartCover: { Count: 1 },
      },
    },
  });

  const createResult = await cosRequestPromise({ Key: "jobs", Method: "POST", Url: url, Body: body, ContentType: "application/xml" });
  const jobsDetail = createResult?.Response?.JobsDetail;

  if (jobsDetail?.Code === "Failed") {
    output({ success: false, action: "create-media-smart-cover-job", data: createResult });
    return;
  }
  if (jobsDetail?.State === "Success") {
    output({ success: true, action: "create-media-smart-cover-job", data: createResult });
    return;
  }

  const jobId = jobsDetail?.JobId;
  if (!jobId) {
    output({ success: true, action: "create-media-smart-cover-job", jobId: null, data: createResult });
    return;
  }

  const maxAttempts = 10;
  const interval = 4000;
  for (let i = 0; i < maxAttempts; i++) {
    if (i > 0) {
      await sleep(interval);
    }
    const queryUrl = `https://${ciHost()}/jobs/${jobId}`;
    const qResult = await cosRequestPromise({ Bucket, Region, Method: "GET", Key: `jobs/${jobId}`, Url: queryUrl });
    const detail = qResult?.Response?.JobsDetail;
    if (detail?.Code === "Success" && detail?.State === "Success") {
      output({ success: true, action: "create-media-smart-cover-job", jobId, data: qResult });
      return;
    }
    if (detail?.Code === "Failed") {
      output({ success: false, action: "create-media-smart-cover-job", jobId, data: qResult });
      return;
    }
  }
  output({ success: false, action: "create-media-smart-cover-job", jobId, error: `轮询超时（${maxAttempts}次未完成）`, data: createResult });
}

async function describeMediaJob(opts) {
  const jobId = opts["job-id"] || opts.jobId;
  if (!jobId) {
    throw new Error("缺少 --job-id 参数");
  }
  const url = `https://${ciHost()}/jobs/${jobId}`;
  const data = await cosRequestPromise({ Bucket, Region, Method: "GET", Key: `jobs/${jobId}`, Url: url });
  output({ success: true, action: "describe-media-job", jobId, data });
}

// ========== CI MetaInsight ==========
//
// 三种检索需要不同模板的数据集：
//   图片检索 → Official:ImageSearch  → TENCENT_COS_DATASET_IMAGE_SEARCH
//   人脸搜索 → Official:FaceSearch   → TENCENT_COS_DATASET_FACE_SEARCH
//   元数据检索 → Official:COSBasicMeta → TENCENT_COS_DATASET_META
// 兼容：TENCENT_COS_DATASET_NAME 作为通用兜底
// 每个 action 也支持 --dataset 参数覆盖

const DatasetImageSearch = process.env.TENCENT_COS_DATASET_IMAGE_SEARCH || DatasetName;
const DatasetFaceSearch = process.env.TENCENT_COS_DATASET_FACE_SEARCH;
const DatasetMeta = process.env.TENCENT_COS_DATASET_META;
const MetaInsightRegion = process.env.TENCENT_COS_METAINSIGHT_REGION;
const METAINSIGHT_REGIONS = ["ap-chengdu", "ap-beijing", "ap-shanghai"];
const _regionCache = {};

function resolveDataset(opts, envValue, label) {
  const ds = opts.dataset || envValue;
  if (!ds) {
    throw new Error(`缺少数据集名称。通过 --dataset 参数指定，或设置对应环境变量。${label}`);
  }
  return ds;
}

async function resolveMetaInsightRegion(datasetName) {
  if (MetaInsightRegion) {
    return MetaInsightRegion;
  }
  if (_regionCache[datasetName]) {
    return _regionCache[datasetName];
  }
  for (const r of METAINSIGHT_REGIONS) {
    try {
      const key = "dataset";
      const host = `${appId()}.ci.${r}.myqcloud.com`;
      const url = `https://${host}/${key}?datasetname=${encodeURIComponent(datasetName)}`;
      const result = await cosRequestPromise({
        Method: "GET",
        Key: key,
        Url: url,
        Headers: { Accept: "application/json" },
      });
      if (result?.Dataset?.DatasetName === datasetName) {
        _regionCache[datasetName] = r;
        return r;
      }
    } catch {
      // 此 region 不可用，继续下一个
    }
  }
  throw new Error(`数据集 "${datasetName}" 在支持的 region (${METAINSIGHT_REGIONS.join(", ")}) 中未找到。可通过 TENCENT_COS_METAINSIGHT_REGION 环境变量指定。`);
}

async function miRequest(datasetName, apiKey, body) {
  const miRegion = await resolveMetaInsightRegion(datasetName);
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${apiKey}`;
  return cosRequestPromise({
    Method: "POST",
    Key: apiKey,
    Url: url,
    Body: JSON.stringify(body),
    Headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
}

// 以图搜图（需 Official:ImageSearch 数据集）
async function imageSearchPic(opts) {
  const { uri } = opts;
  if (!uri) {
    throw new Error("缺少 --uri 参数");
  }
  const ds = resolveDataset(opts, DatasetImageSearch, "图片检索需要 Official:ImageSearch 模板数据集（TENCENT_COS_DATASET_IMAGE_SEARCH）");
  const data = await miRequest(ds, "datasetquery/imagesearch", { DatasetName: ds, Mode: "pic", URI: uri });
  output({ success: true, action: "image-search-pic", dataset: ds, data });
}

// 文本搜图（需 Official:ImageSearch 数据集）
async function imageSearchText(opts) {
  const { text } = opts;
  if (!text) {
    throw new Error("缺少 --text 参数");
  }
  const ds = resolveDataset(opts, DatasetImageSearch, "图片检索需要 Official:ImageSearch 模板数据集（TENCENT_COS_DATASET_IMAGE_SEARCH）");
  const data = await miRequest(ds, "datasetquery/imagesearch", { DatasetName: ds, Mode: "text", Text: text });
  output({ success: true, action: "image-search-text", dataset: ds, data });
}

// 人脸搜索（需 Official:FaceSearch 数据集）
async function faceSearch(opts) {
  const { uri } = opts;
  if (!uri) {
    throw new Error("缺少 --uri 参数");
  }
  const ds = resolveDataset(opts, DatasetFaceSearch, "人脸搜索需要 Official:FaceSearch 模板数据集（TENCENT_COS_DATASET_FACE_SEARCH）");
  const maxFaceNum = parseInt(opts["max-face-num"], 10) || 1;
  const limit = parseInt(opts.limit, 10) || 10;
  const threshold = parseInt(opts.threshold, 10) || 80;
  const data = await miRequest(ds, "datasetquery/facesearch", {
    DatasetName: ds,
    URI: uri,
    MaxFaceNum: maxFaceNum,
    Limit: limit,
    MatchThreshold: threshold,
  });
  output({ success: true, action: "face-search", dataset: ds, data });
}

// 元数据检索 — 简单查询（需 Official:COSBasicMeta 或任意数据集）
async function datasetSimpleQuery(opts) {
  const ds = resolveDataset(opts, DatasetMeta || DatasetImageSearch, "元数据检索需要数据集名称（TENCENT_COS_DATASET_META 或 --dataset）");
  const query = opts.query ? JSON.parse(opts.query) : undefined;
  const maxResults = parseInt(opts["max-results"], 10) || 100;
  const sort = opts.sort;
  const order = opts.order || "desc";
  const bodyObj = { DatasetName: ds, MaxResults: maxResults, Order: order };
  if (query) {
    bodyObj.Query = query;
  }
  if (sort) {
    bodyObj.Sort = sort;
  }
  const data = await miRequest(ds, "datasetquery/simple", bodyObj);
  output({ success: true, action: "dataset-simple-query", dataset: ds, data });
}

// 多模态检索 — 文档检索（hybridsearch）
async function hybridSearch(opts) {
  const { text } = opts;
  if (!text) {
    throw new Error("缺少 --text 参数（检索文本）");
  }
  const ds = resolveDataset(opts, DatasetMeta || DatasetImageSearch || DatasetName, "多模态检索需要数据集名称（--dataset 或 TENCENT_COS_DATASET_META）");
  const templates = opts.templates || "DocSearch";
  const mode = opts.mode || "text";
  const limit = parseInt(opts.limit, 10) || 10;
  const offset = parseInt(opts.offset, 10) || 0;
  const threshold = parseInt(opts.threshold, 10) || 1;

  const bodyObj = {
    DatasetName: ds,
    Mode: mode,
    Templates: templates,
    SearchText: text,
    Offset: offset,
    Limit: limit,
    MatchThreshold: threshold,
  };

  if (opts.filter) {
    try {
      bodyObj.Filter = JSON.parse(opts.filter);
    } catch {
      throw new Error("--filter 参数必须是有效的 JSON 字符串");
    }
  }

  const data = await miRequest(ds, "datasetquery/hybridsearch", bodyObj);
  output({ success: true, action: "hybrid-search", dataset: ds, templates, data });
}

// 列出数据集
async function listDatasets(opts) {
  const maxResults = parseInt(opts["max-results"], 10) || 100;
  const prefix = opts.prefix || "";
  // 需要探测 region，用任意已知数据集或逐个尝试
  let miRegion = MetaInsightRegion;
  if (!miRegion) {
    // 尝试每个 region，取第一个能返回结果的
    for (const r of METAINSIGHT_REGIONS) {
      try {
        const key = "datasets";
        const host = `${appId()}.ci.${r}.myqcloud.com`;
        const url = `https://${host}/${key}?maxresults=${maxResults}${prefix ? `&prefix=${encodeURIComponent(prefix)}` : ""}`;
        const result = await cosRequestPromise({
          Method: "GET",
          Key: key,
          Url: url,
          Headers: { Accept: "application/json" },
        });
        if (result?.Datasets) {
          output({ success: true, action: "list-datasets", region: r, data: result });
          return;
        }
      } catch {
        // 此 region 不可用，继续
      }
    }
    throw new Error(`在支持的 region (${METAINSIGHT_REGIONS.join(", ")}) 中均无法查询数据集。可通过 TENCENT_COS_METAINSIGHT_REGION 环境变量指定。`);
  }
  const key = "datasets";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}?maxresults=${maxResults}${prefix ? `&prefix=${encodeURIComponent(prefix)}` : ""}`;
  const data = await cosRequestPromise({
    Method: "GET",
    Key: key,
    Url: url,
    Headers: { Accept: "application/json" },
  });
  output({ success: true, action: "list-datasets", region: miRegion, data });
}

// 创建数据集
async function createDataset(opts) {
  const { name, template, description } = opts;
  if (!name) {
    throw new Error("缺少 --name 参数（数据集名称）");
  }
  const tpl = template || "Official:COSBasicMeta";
  const miRegion = MetaInsightRegion || METAINSIGHT_REGIONS[0];
  const key = "dataset";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}`;
  const body = JSON.stringify({ DatasetName: name, TemplateId: tpl, Description: description || "" });
  const data = await cosRequestPromise({
    Method: "POST",
    Key: key,
    Url: url,
    Body: body,
    Headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
  output({ success: true, action: "create-dataset", name, template: tpl, region: miRegion, data });
}

// 查询数据集详情
async function describeDataset(opts) {
  const name = opts.name || opts.dataset;
  if (!name) {
    throw new Error("缺少 --name 参数（数据集名称）");
  }
  const miRegion = await resolveMetaInsightRegion(name);
  const key = "dataset";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}?datasetname=${encodeURIComponent(name)}&statistics=true`;
  const data = await cosRequestPromise({
    Method: "GET",
    Key: key,
    Url: url,
    Headers: { Accept: "application/json" },
  });
  output({ success: true, action: "describe-dataset", name, region: miRegion, data });
}

// 绑定存储桶到数据集（Mode: 1=存量索引 0=增量索引，默认存量）
async function createDatasetBinding(opts) {
  const name = opts.name || opts.dataset;
  const uri = opts.uri || `cos://${Bucket}`;
  const mode = opts.mode !== undefined ? parseInt(opts.mode, 10) : 1;
  if (!name) {
    throw new Error("缺少 --name 参数（数据集名称）");
  }
  const miRegion = await resolveMetaInsightRegion(name);
  const key = "datasetbinding";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}`;
  const body = JSON.stringify({ DatasetName: name, URI: uri, Mode: mode });
  const data = await cosRequestPromise({
    Method: "POST",
    Key: key,
    Url: url,
    Body: body,
    Headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
  output({ success: true, action: "create-dataset-binding", name, uri, data });
}

// 查询数据集绑定关系
async function describeDatasetBindings(opts) {
  const name = opts.name || opts.dataset;
  if (!name) {
    throw new Error("缺少 --name 参数（数据集名称）");
  }
  const miRegion = await resolveMetaInsightRegion(name);
  const key = "datasetbindings";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}?datasetname=${encodeURIComponent(name)}&maxresults=100`;
  const data = await cosRequestPromise({
    Method: "GET",
    Key: key,
    Url: url,
    Headers: { Accept: "application/json" },
  });
  output({ success: true, action: "describe-dataset-bindings", name, data });
}

// 创建文件元数据索引
async function createFileMetaIndex(opts) {
  const name = opts.name || opts.dataset;
  const uri = opts.uri;
  if (!name) {
    throw new Error("缺少 --name 参数（数据集名称）");
  }
  if (!uri) {
    throw new Error("缺少 --uri 参数（文件地址，格式 cos://bucket/path）");
  }
  const miRegion = await resolveMetaInsightRegion(name);
  const key = "filemeta";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}`;
  const fileObj = { URI: uri };
  if (opts["media-type"]) {
    fileObj.MediaType = opts["media-type"];
  }
  if (opts["custom-id"]) {
    fileObj.CustomId = opts["custom-id"];
  }
  const body = JSON.stringify({ DatasetName: name, File: fileObj });
  const data = await cosRequestPromise({
    Method: "POST",
    Key: key,
    Url: url,
    Body: body,
    Headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
  output({ success: true, action: "create-file-meta-index", name, uri, data });
}

// 查询文件元数据索引
async function describeFileMetaIndex(opts) {
  const name = opts.name || opts.dataset;
  const uri = opts.uri;
  if (!name || !uri) {
    throw new Error("缺少 --name 和 --uri 参数");
  }
  const miRegion = await resolveMetaInsightRegion(name);
  const key = "filemeta";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}?datasetname=${encodeURIComponent(name)}&uri=${encodeURIComponent(uri)}`;
  const data = await cosRequestPromise({
    Method: "GET",
    Key: key,
    Url: url,
    Headers: { Accept: "application/json" },
  });
  output({ success: true, action: "describe-file-meta-index", name, uri, data });
}

// 删除文件元数据索引
async function deleteFileMetaIndex(opts) {
  const name = opts.name || opts.dataset;
  const uri = opts.uri;
  if (!name || !uri) {
    throw new Error("缺少 --name 和 --uri 参数");
  }
  const miRegion = await resolveMetaInsightRegion(name);
  const key = "filemeta";
  const host = `${appId()}.ci.${miRegion}.myqcloud.com`;
  const url = `https://${host}/${key}`;
  const body = JSON.stringify({ DatasetName: name, URI: uri });
  const data = await cosRequestPromise({
    Method: "DELETE",
    Key: key,
    Url: url,
    Body: body,
    Headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
  output({ success: true, action: "delete-file-meta-index", name, uri, data });
}

// ========== 快捷功能 ==========

// 创建知识库：一键创建桶 + DocSearch 数据集 + 绑定
async function createKnowledgeBase(opts) {
  const name = opts.name;
  if (!name) {
    throw new Error("缺少 --name 参数（知识库名称，将用于存储桶和数据集命名）");
  }

  // MetaInsight 仅支持部分 region，桶和数据集必须在同一 region
  const kbRegion = opts.region || MetaInsightRegion || "ap-chengdu";
  const kbBucket = `${name}-${appId()}`;
  const kbDataset = opts.dataset || `${name}-docsearch`;

  const steps = [];
  let hasError = false;

  // 步骤 1：创建存储桶
  try {
    await new Promise((resolveP, rejectP) => {
      cos.putBucket({ Bucket: kbBucket, Region: kbRegion }, (err, data) => (err ? rejectP(err) : resolveP(data)));
    });
    steps.push({ step: 1, action: "创建存储桶", status: "success", bucket: kbBucket, region: kbRegion });
  } catch (err) {
    if (err.code === "BucketAlreadyExists" || err.code === "BucketAlreadyOwnedByYou") {
      steps.push({ step: 1, action: "创建存储桶", status: "exists", bucket: kbBucket, message: "存储桶已存在，继续" });
    } else {
      steps.push({ step: 1, action: "创建存储桶", status: "failed", error: err.message || err.code });
      hasError = true;
    }
  }

  // 步骤 2：创建 DocSearch 数据集
  if (!hasError) {
    try {
      const dsKey = "dataset";
      const dsHost = `${appId()}.ci.${kbRegion}.myqcloud.com`;
      const dsUrl = `https://${dsHost}/${dsKey}`;
      const dsBody = JSON.stringify({
        DatasetName: kbDataset,
        TemplateId: "Official:DocSearch",
        Description: `知识库：${name}`,
      });
      await cosRequestPromise({
        Method: "POST",
        Key: dsKey,
        Url: dsUrl,
        Body: dsBody,
        Headers: { "Content-Type": "application/json", Accept: "application/json" },
      });
      steps.push({ step: 2, action: "创建数据集", status: "success", dataset: kbDataset, template: "Official:DocSearch", region: kbRegion });
    } catch (err) {
      const errMsg = err.message || String(err);
      const errCode = err.statusCode || err.code;
      // 数据集已存在时 API 返回 400，尝试查询确认
      if (errCode === 400 || errCode === "400" || errMsg.includes("already exist") || errMsg.includes("AlreadyExist")) {
        steps.push({ step: 2, action: "创建数据集", status: "exists", dataset: kbDataset, message: "数据集已存在，继续" });
      } else {
        steps.push({ step: 2, action: "创建数据集", status: "failed", error: errMsg });
        hasError = true;
      }
    }
  }

  // 步骤 3：绑定存储桶到数据集
  if (!hasError) {
    try {
      const bindKey = "datasetbinding";
      const bindHost = `${appId()}.ci.${kbRegion}.myqcloud.com`;
      const bindUrl = `https://${bindHost}/${bindKey}`;
      const bindBody = JSON.stringify({ DatasetName: kbDataset, URI: `cos://${kbBucket}`, Mode: 1 });
      await cosRequestPromise({
        Method: "POST",
        Key: bindKey,
        Url: bindUrl,
        Body: bindBody,
        Headers: { "Content-Type": "application/json", Accept: "application/json" },
      });
      steps.push({ step: 3, action: "绑定存储桶", status: "success", dataset: kbDataset, bucket: kbBucket });
    } catch (err) {
      const errMsg = err.message || String(err);
      const errCode = err.statusCode || err.code;
      if (errCode === 400 || errCode === "400" || errMsg.includes("bindingisexisted") || errMsg.includes("bindingis existed") || errMsg.includes("already bind")) {
        steps.push({ step: 3, action: "绑定存储桶", status: "exists", message: "绑定关系已存在" });
      } else {
        steps.push({ step: 3, action: "绑定存储桶", status: "failed", error: errMsg });
        hasError = true;
      }
    }
  }

  output({
    success: !hasError,
    action: "create-knowledge-base",
    knowledgeBase: {
      name,
      bucket: kbBucket,
      bucketRegion: kbRegion,
      dataset: kbDataset,
      datasetRegion: kbRegion,
      template: "Official:DocSearch",
    },
    steps,
    usage: hasError
      ? undefined
      : {
          upload: `node cos_node.mjs upload --file /path/to/doc.pdf --key docs/doc.pdf --bucket ${kbBucket} --region ${kbRegion}`,
          search: `node cos_node.mjs hybrid-search --text "你想检索的内容" --dataset ${kbDataset} --templates DocSearch`,
          note: "上传文件后，CI 会自动建立文档向量索引。索引建立需要几秒到几分钟，之后即可通过 hybrid-search 检索文档内容。",
        },
  });
}

// ========== 凭证加密管理 ==========

async function encryptEnvAction() {
  if (!existsSync(envPath)) {
    // 兼容：如果 .env 不存在但 .env.enc 存在，说明已经加密过了
    if (existsSync(envEncPath)) {
      output({ success: true, action: "encrypt-env", message: "凭证已处于加密状态（.env.enc 已存在，.env 不存在），无需重复加密。" });
      return;
    }
    throw new Error("未找到 .env 文件，无法加密。请先使用 setup.sh --from-env --persist 创建 .env 文件。");
  }
  const plaintext = readFileSync(envPath, "utf-8");
  if (!plaintext.trim()) {
    throw new Error(".env 文件为空，无需加密。");
  }

  // 如果已有 .env.enc，先备份再覆盖（兼容重新加密场景）
  if (existsSync(envEncPath)) {
    const backupPath = envEncPath + ".bak";
    writeFileSync(backupPath, readFileSync(envEncPath));
    chmodSync(backupPath, 0o600);
  }

  const encBuffer = encryptEnv(plaintext);
  writeFileSync(envEncPath, encBuffer);
  chmodSync(envEncPath, 0o600);
  // 删除明文 .env
  unlinkSync(envPath);

  // 确保 .gitignore 包含 .env.enc
  const gitignorePath = resolve(__dirname, "..", ".gitignore");
  if (existsSync(gitignorePath)) {
    const content = readFileSync(gitignorePath, "utf-8");
    const additions = [];
    if (!content.includes(".env.enc")) {
      additions.push(".env.enc");
    }
    if (!content.includes(".env.enc.bak")) {
      additions.push(".env.enc.bak");
    }
    if (additions.length > 0) {
      writeFileSync(gitignorePath, content.trimEnd() + "\n" + additions.join("\n") + "\n");
    }
  } else {
    writeFileSync(gitignorePath, ".env\n.env.enc\n.env.enc.bak\n");
  }

  output({
    success: true,
    action: "encrypt-env",
    message: "凭证已加密。明文 .env 已删除，加密文件 .env.enc 已创建（权限 600）。",
    encFile: envEncPath,
    algorithm: "AES-256-GCM",
    keyDerivation: "基于 hostname + username + 项目路径 的 SHA-256 派生",
    note: "加密文件绑定当前机器和用户，不可跨机器/用户使用。如需在新机器上使用，请重新 export 环境变量并 setup.sh --from-env --persist 后再加密。",
  });
}

async function decryptEnvAction() {
  if (!existsSync(envEncPath)) {
    // 兼容：如果 .env.enc 不存在但 .env 存在，说明本来就是明文的
    if (existsSync(envPath)) {
      output({ success: true, action: "decrypt-env", message: "凭证已处于明文状态（.env 已存在，.env.enc 不存在），无需解密。" });
      return;
    }
    throw new Error("未找到 .env.enc 加密文件，也未找到 .env 明文文件。请先使用 setup.sh --from-env --persist 创建凭证。");
  }
  const encBuffer = readFileSync(envEncPath);
  let plaintext;
  try {
    plaintext = decryptEnv(encBuffer);
  } catch (err) {
    throw new Error(`解密失败：密钥不匹配或文件损坏。可能是在其他机器/用户下创建的加密文件。${err.message}`);
  }
  writeFileSync(envPath, plaintext);
  chmodSync(envPath, 0o600);

  output({
    success: true,
    action: "decrypt-env",
    message: "凭证已解密还原为 .env 文件（权限 600）。加密文件 .env.enc 保留。",
    envFile: envPath,
    note: "如需删除加密文件：rm -f .env.enc",
  });
}

// ========== CI 图片基础处理（扩展） ==========

async function imageThumbnail(opts) {
  const { key, width, height } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  let rule = "imageMogr2/thumbnail/";
  if (width && height) {
    rule += `${width}x${height}`;
  } else if (width) {
    rule += `${width}x`;
  } else if (height) {
    rule += `x${height}`;
  } else {
    rule += "!50p";
  }
  const outFileId = generateOutputFileId(key);
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ is_pic_info: 1, rules: [{ fileid: outFileId, rule }] }) },
  });
  output({ success: true, action: "image-thumbnail", key, data });
}

async function imageCrop(opts) {
  const { key, width, height, gravity } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const w = width || "300";
  const h = height || "300";
  const g = gravity || "center";
  const rule = `imageMogr2/cut/${w}x${h}x0x0/gravity/${g}`;
  const outFileId = generateOutputFileId(key);
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ is_pic_info: 1, rules: [{ fileid: outFileId, rule }] }) },
  });
  output({ success: true, action: "image-crop", key, data });
}

async function imageRotate(opts) {
  const { key, degree } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const rule = `imageMogr2/rotate/${degree || "90"}`;
  const outFileId = generateOutputFileId(key);
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ is_pic_info: 1, rules: [{ fileid: outFileId, rule }] }) },
  });
  output({ success: true, action: "image-rotate", key, data });
}

async function imageFormat(opts) {
  const { key, format } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const fmt = format || "webp";
  const rule = `imageMogr2/format/${fmt}`;
  const outFileId = generateOutputFileId(key);
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Key: key,
    Method: "POST",
    Action: "image_process",
    Headers: { "Pic-Operations": JSON.stringify({ is_pic_info: 1, rules: [{ fileid: outFileId, rule }] }) },
  });
  output({ success: true, action: "image-format", key, data });
}

// ========== CI 内容审核 ==========

async function auditImage(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "sensitive-content-recognition" },
  });
  output({ success: true, action: "audit-image", key, data });
}

async function auditImageJob(opts) {
  const { key, url: imageUrl } = opts;
  if (!key && !imageUrl) {
    throw new Error("缺少 --key 或 --url 参数");
  }
  const ciUrl = `https://${ciHost()}/image/auditing`;
  const input = key ? { Object: key } : { Url: imageUrl };
  const body = COS.util.json2xml({ Request: { Input: input, Conf: { BizType: "" } } });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "image/auditing",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "audit-image-job", data });
}

async function auditVideoJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/video/auditing`;
  const body = COS.util.json2xml({ Request: { Input: { Object: key }, Conf: { BizType: "" } } });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "video/auditing",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "audit-video-job", data });
}

async function auditAudioJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/audio/auditing`;
  const body = COS.util.json2xml({ Request: { Input: { Object: key }, Conf: { BizType: "" } } });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "audio/auditing",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "audit-audio-job", data });
}

async function auditTextJob(opts) {
  const { content, key } = opts;
  if (!content && !key) {
    throw new Error("缺少 --content 或 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/text/auditing`;
  const input = key ? { Object: key } : { Content: Buffer.from(content).toString("base64") };
  const body = COS.util.json2xml({ Request: { Input: input, Conf: { BizType: "" } } });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "text/auditing",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "audit-text-job", data });
}

async function auditDocumentJob(opts) {
  const { key, url: docUrl } = opts;
  if (!key && !docUrl) {
    throw new Error("缺少 --key 或 --url 参数");
  }
  const ciUrl = `https://${ciHost()}/document/auditing`;
  const input = key ? { Object: key } : { Url: docUrl };
  const body = COS.util.json2xml({ Request: { Input: input, Conf: { BizType: "" } } });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "document/auditing",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "audit-document-job", data });
}

async function describeAuditJob(opts) {
  const jobId = opts["job-id"] || opts.jobId;
  const type = opts.type || "image";
  if (!jobId) {
    throw new Error("缺少 --job-id 参数");
  }
  const ciUrl = `https://${ciHost()}/${type}/auditing/${jobId}`;
  const data = await cosRequestPromise({
    Method: "GET",
    Url: ciUrl,
    Key: `${type}/auditing/${jobId}`,
  });
  output({ success: true, action: "describe-audit-job", type, jobId, data });
}

// ========== CI 智能语音 ==========

async function speechRecognitionJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/asr_jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "SpeechRecognition",
      Input: { Object: key },
      Operation: {
        SpeechRecognition: {
          EngineModelType: opts.engine || "16k_zh_video",
          ChannelNum: opts.channel || 1,
          ResTextFormat: 0,
          FilterDirty: 1,
          FilterModal: 1,
          ConvertNumMode: 0,
        },
        Output: { Bucket, Region, Object: `asr_result/${generateOutputFileId(key)}.txt` },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "asr_jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "speech-recognition-job", data });
}

async function ttsJob(opts) {
  const { text } = opts;
  if (!text) {
    throw new Error("缺少 --text 参数");
  }
  const ciUrl = `https://${ciHost()}/jobs`;
  const codec = opts.codec || "mp3";
  const voiceType = opts["voice-type"] || "ruxue";
  const body = COS.util.json2xml({
    Request: {
      Tag: "Tts",
      Operation: {
        TtsTpl: {
          Mode: "Sync",
          Codec: codec,
          VoiceType: voiceType,
        },
        TtsConfig: { InputType: "Text", Input: text },
        Output: { Bucket, Region, Object: `tts_result/${generateOutputFileId("")}.${codec}` },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "tts-job", data });
}

async function noiseReductionJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "NoiseReduction",
      Input: { Object: key },
      Operation: {
        Output: { Bucket, Region, Object: `noise_result/${generateOutputFileId(key)}.mp3` },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "noise-reduction-job", data });
}

async function voiceSeparateJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/jobs`;
  const outId = generateOutputFileId(key);
  const body = COS.util.json2xml({
    Request: {
      Tag: "VoiceSeparate",
      Input: { Object: key },
      Operation: {
        VoiceSeparate: { AudioMode: "IsAudio" },
        Output: { Bucket, Region, Object: `voice_sep/${outId}_bg.mp3`, AuObject: `voice_sep/${outId}_voice.mp3` },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "voice-separate-job", data });
}

// ========== CI 文件处理 ==========

async function fileHashJob(opts) {
  const { key, type: hashType } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  // 同步方式
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "filehash", type: hashType || "md5" },
  });
  output({ success: true, action: "file-hash", key, data });
}

async function fileCompressJob(opts) {
  const { prefix, format } = opts;
  const key = opts.key || opts.output || `compressed_${generateOutputFileId("")}.zip`;
  const ciUrl = `https://${ciHost()}/file_jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "FileCompress",
      Operation: {
        FileCompressConfig: { Flatten: "0", Format: format || "zip", Prefix: prefix || "/" },
        Output: { Bucket, Region, Object: key },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "file_jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "file-compress-job", data });
}

async function fileUncompressJob(opts) {
  const { key, prefix } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const ciUrl = `https://${ciHost()}/file_jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "FileUncompress",
      Input: { Object: key },
      Operation: {
        FileUncompressConfig: { Prefix: prefix || "", PrefixReplaced: "0" },
        Output: { Bucket, Region },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "file_jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "file-uncompress-job", data });
}

async function describeFileJob(opts) {
  const jobId = opts["job-id"] || opts.jobId;
  if (!jobId) {
    throw new Error("缺少 --job-id 参数");
  }
  const ciUrl = `https://${ciHost()}/file_jobs/${jobId}`;
  const data = await cosRequestPromise({
    Method: "GET",
    Url: ciUrl,
    Key: `file_jobs/${jobId}`,
  });
  output({ success: true, action: "describe-file-job", jobId, data });
}

// ========== CI 内容识别 ==========

async function recognizeImage(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  // 图片标签识别
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "detect-label" },
  });
  output({ success: true, action: "recognize-image", key, data });
}

async function ocrGeneral(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "OCR", type: opts.type || "general" },
  });
  output({ success: true, action: "ocr-general", key, data });
}

// ========== CI 媒体处理（扩展） ==========

async function mediaTranscodeJob(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const lastDot = key.lastIndexOf(".");
  const base = lastDot === -1 ? key : key.substring(0, lastDot);
  const format = opts.format || "mp4";
  const outObject = `${base}_transcode_${generateCode(6)}.${format}`;
  const ciUrl = `https://${ciHost()}/jobs`;
  const body = COS.util.json2xml({
    Request: {
      Tag: "Transcode",
      Input: { Object: key },
      Operation: {
        Transcode: { Container: { Format: format } },
        Output: { Bucket, Region, Object: outObject },
      },
    },
  });
  const data = await cosRequestPromise({
    Method: "POST",
    Url: ciUrl,
    Key: "jobs",
    Body: body,
    ContentType: "application/xml",
  });
  output({ success: true, action: "media-transcode-job", data });
}

async function mediaSnapshotJob(opts) {
  const { key, time } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    RawBody: true,
    Query: { "ci-process": "snapshot", time: time || "1", format: opts.format || "jpg" },
  });
  output({ success: true, action: "media-snapshot", key, data: { statusCode: data.statusCode, headers: data.headers } });
}

async function mediaInfoGet(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "videoinfo" },
  });
  output({ success: true, action: "media-info", key, data });
}

// ========== CI 文档处理（扩展） ==========

async function docPreview(opts) {
  const { key, page } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const data = await cosRequestPromise({
    Bucket,
    Region,
    Method: "GET",
    Key: key,
    Query: { "ci-process": "doc-preview", page: page || "1", dstType: opts.format || "jpg" },
  });
  output({ success: true, action: "doc-preview", key, data: { statusCode: data.statusCode, headers: data.headers } });
}

async function docPreviewHtmlUrl(opts) {
  const { key } = opts;
  if (!key) {
    throw new Error("缺少 --key 参数");
  }
  const url = await new Promise((resolveP, rejectP) => {
    cos.getObjectUrl(
      {
        Bucket,
        Region,
        Key: key,
        Query: { "ci-process": "doc-preview", dstType: "html" },
        Expires: parseInt(opts.expires, 10) || 3600,
        Sign: true,
      },
      (err, data) => {
        if (err) {
          rejectP(err);
        } else {
          resolveP(data.Url);
        }
      }
    );
  });
  output({ success: true, action: "doc-preview-html-url", key, url });
}

// ========== CI 通用 request（扩展入口） ==========

async function ciRequest(opts) {
  const method = (opts.method || "GET").toUpperCase();
  const path = opts.path;
  if (!path) {
    throw new Error("缺少 --path 参数（CI API 路径，如 doc_jobs、jobs、file_jobs）");
  }
  const url = `https://${ciHost()}/${path}`;
  const reqParams = { Bucket, Region, Method: method, Key: path, Url: url };
  if (opts.body) {
    reqParams.Body = opts.body;
    reqParams.ContentType = opts["content-type"] || "application/xml";
  }
  if (opts.query) {
    try {
      reqParams.Query = JSON.parse(opts.query);
    } catch {
      throw new Error("--query 参数必须是有效的 JSON 字符串");
    }
  }
  const data = await cosRequestPromise(reqParams);
  output({ success: true, action: "ci-request", path, method, data });
}

// ========== 主入口 ==========

const args = process.argv.slice(2);
const action = args[0];
const opts = parseArgs(args.slice(1));

// 所有 action 都支持 --bucket / --region / --dataset-name 覆盖默认值
if (opts.bucket) {
  Bucket = opts.bucket;
}
if (opts.region) {
  Region = opts.region;
}
if (opts["dataset-name"]) {
  DatasetName = opts["dataset-name"];
}

const actions = {
  // COS 存储操作
  upload,
  "put-string": putString,
  download,
  list,
  "sign-url": signUrl,
  delete: deleteObject,
  head,

  // COS 存储桶管理
  "list-buckets": listBuckets,
  "create-bucket": createBucket,
  "head-bucket": headBucket,
  "get-bucket-acl": getBucketAcl,
  "put-bucket-acl": putBucketAcl,
  "get-bucket-cors": getBucketCors,
  "put-bucket-cors": putBucketCors,
  "get-bucket-tagging": getBucketTagging,
  "put-bucket-tagging": putBucketTagging,
  "get-bucket-versioning": getBucketVersioning,
  "get-bucket-lifecycle": getBucketLifecycle,
  "get-bucket-location": getBucketLocation,
  "copy-object": copyObject,
  "delete-multiple": deleteMultipleObjects,

  // CI 图片基础处理
  "image-info": imageInfo,
  "image-thumbnail": imageThumbnail,
  "image-crop": imageCrop,
  "image-rotate": imageRotate,
  "image-format": imageFormat,
  "watermark-font": watermarkFont,

  // CI AI 图片处理
  "assess-quality": assessQuality,
  "ai-super-resolution": aiSuperResolution,
  "ai-pic-matting": aiPicMatting,
  "ai-qrcode": aiQrcode,

  // CI 内容识别
  "recognize-image": recognizeImage,
  "ocr-general": ocrGeneral,

  // CI 文档处理
  "create-doc-to-pdf-job": createDocToPdfJob,
  "describe-doc-job": describeDocProcessJob,
  "doc-preview": docPreview,
  "doc-preview-html-url": docPreviewHtmlUrl,

  // CI 媒体处理
  "create-media-smart-cover-job": createMediaSmartCoverJob,
  "describe-media-job": describeMediaJob,
  "media-transcode-job": mediaTranscodeJob,
  "media-snapshot": mediaSnapshotJob,
  "media-info": mediaInfoGet,

  // CI 内容审核
  "audit-image": auditImage,
  "audit-image-job": auditImageJob,
  "audit-video-job": auditVideoJob,
  "audit-audio-job": auditAudioJob,
  "audit-text-job": auditTextJob,
  "audit-document-job": auditDocumentJob,
  "describe-audit-job": describeAuditJob,

  // CI 智能语音
  "speech-recognition-job": speechRecognitionJob,
  "tts-job": ttsJob,
  "noise-reduction-job": noiseReductionJob,
  "voice-separate-job": voiceSeparateJob,

  // CI 文件处理
  "file-hash": fileHashJob,
  "file-compress-job": fileCompressJob,
  "file-uncompress-job": fileUncompressJob,
  "describe-file-job": describeFileJob,

  // CI MetaInsight
  "list-datasets": listDatasets,
  "create-dataset": createDataset,
  "describe-dataset": describeDataset,
  "create-dataset-binding": createDatasetBinding,
  "describe-dataset-bindings": describeDatasetBindings,
  "create-file-meta-index": createFileMetaIndex,
  "describe-file-meta-index": describeFileMetaIndex,
  "delete-file-meta-index": deleteFileMetaIndex,
  "image-search-pic": imageSearchPic,
  "image-search-text": imageSearchText,
  "face-search": faceSearch,
  "dataset-simple-query": datasetSimpleQuery,
  "hybrid-search": hybridSearch,

  // CI 通用 request（扩展入口）
  "ci-request": ciRequest,

  // 快捷功能
  "create-knowledge-base": createKnowledgeBase,

  // 凭证加密管理
  "encrypt-env": encryptEnvAction,
  "decrypt-env": decryptEnvAction,
};

if (!action || !actions[action]) {
  output({
    success: false,
    error: `未知操作：${action || "(空)"}`,
    availableActions: Object.keys(actions),
    usage: "node cos_node.mjs <action> [--option value ...]",
    categories: {
      存储操作: ["upload", "put-string", "download", "list", "sign-url", "delete", "delete-multiple", "head", "copy-object"],
      存储桶管理: [
        "list-buckets",
        "create-bucket",
        "head-bucket",
        "get-bucket-acl",
        "put-bucket-acl",
        "get-bucket-cors",
        "put-bucket-cors",
        "get-bucket-tagging",
        "put-bucket-tagging",
        "get-bucket-versioning",
        "get-bucket-lifecycle",
        "get-bucket-location",
      ],
      图片基础处理: ["image-info", "image-thumbnail", "image-crop", "image-rotate", "image-format", "watermark-font"],
      AI图片处理: ["assess-quality", "ai-super-resolution", "ai-pic-matting", "ai-qrcode"],
      内容识别: ["recognize-image", "ocr-general"],
      文档处理: ["create-doc-to-pdf-job", "describe-doc-job", "doc-preview", "doc-preview-html-url"],
      媒体处理: ["create-media-smart-cover-job", "describe-media-job", "media-transcode-job", "media-snapshot", "media-info"],
      内容审核: ["audit-image", "audit-image-job", "audit-video-job", "audit-audio-job", "audit-text-job", "audit-document-job", "describe-audit-job"],
      智能语音: ["speech-recognition-job", "tts-job", "noise-reduction-job", "voice-separate-job"],
      文件处理: ["file-hash", "file-compress-job", "file-uncompress-job", "describe-file-job"],
      MetaInsight数据集管理: ["list-datasets", "create-dataset", "describe-dataset", "create-dataset-binding", "describe-dataset-bindings"],
      MetaInsight索引管理: ["create-file-meta-index", "describe-file-meta-index", "delete-file-meta-index"],
      MetaInsight检索: ["image-search-pic", "image-search-text", "face-search", "dataset-simple-query", "hybrid-search"],
      通用CI请求: ["ci-request"],
      "🚀快捷功能": ["create-knowledge-base"],
      "🔐凭证管理": ["encrypt-env", "decrypt-env"],
      "⚠️禁止操作": ["不允许删除存储桶(deleteBucket)", "不允许清空存储桶"],
    },
  });
  process.exit(1);
}

try {
  await actions[action](opts);
} catch (err) {
  output({
    success: false,
    action,
    error: err.message || String(err),
    code: err.code,
  });
  process.exit(1);
}
