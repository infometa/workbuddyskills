#!/usr/bin/env node
/**
 * create-asset.mjs — 创建推广内容资产（marketing_target_assets/add）
 *
 * 调用 /v3.0/marketing_target_assets/add 接口，在指定业务单元下创建推广内容资产。
 *
 * 入参: '<完整参数 JSON>'
 * 必填:
 *   organization_id                — integer，业务单元 ID
 *   marketing_target_type          — string，推广内容资产类型（枚举 ApiMarketingTargetType）
 *   properties                     — struct[]，资产属性列表
 *
 * 可选:
 *   marketing_asset_name           — string，产品名称（最长 1024 字符）
 *   marketing_asset_type           — string，产品类型（枚举 MarketingAssetType）
 *   meituan_rank                   — string，美团排名（最长 1024 字符）
 *
 * properties[i] 结构:
 *   property_name                  — string，属性名称（枚举 PromotedAssetAttrKey）
 *   property_value                 — string[]，属性值列表
 *
 * 示例:
 *   {
 *     "organization_id": 23919277,
 *     "marketing_asset_name": "个人店铺测试",
 *     "marketing_target_type": "MARKETING_TARGET_TYPE_PERSONAL_STORE",
 *     "properties": [
 *       {
 *         "property_name": "PROMOTED_ASSET_ATTR_KEY_PERSONAL_STORE_COMPANY_ENTITY",
 *         "property_value": ["深圳市腾讯计算机系统有限公司"]
 *       }
 *     ]
 *   }
 *
 * 输出（成功）: { "marketing_asset_id": <integer> }
 * 输出（失败）: { "success": false, "error": { "message": "..." } }
 */

import { callApi } from "tencentads-cli";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 地域名称合法性校验（geo-regions.json 存放于 shared/resources）
const GEO_REGIONS_FILE = join(__dirname, "../resources/geo-regions.json");
let geoRegions = null;
function getGeoRegions() {
  if (!geoRegions) {
    const raw = readFileSync(GEO_REGIONS_FILE, "utf-8");
    const data = JSON.parse(raw);
    // 构建 name → id 的查找索引
    geoRegions = new Map();
    for (const [id, info] of Object.entries(data)) {
      geoRegions.set(info.name, { id: Number(id), ...info });
    }
  }
  return geoRegions;
}

/** 地域类属性的 property_name 精确后缀，触发地名校验 */
const GEO_ATTR_SUFFIXES = new Set([
  "_EXHIBITION_CITY",
  "_ISSUING_PROVINCE",
  "_SERVICE_CITY",
  "_SERVICE_AREA",
  "_DEPARTURE_CITY",
  "_DESTINATION_CITY",
  "_ATTRACTIONS_TICKETS_CITY",
  "_HOTEL_SERVICE_CITY",
  "_HOTEL_SERVICE_AREA",
  "_REGION_NODE",
]);

// ── Parse input ──
let input;
try {
  const raw = process.argv[2] != null
    ? process.argv[2]
    : await new Promise((res) => {
        let buf = '';
        process.stdin.setEncoding('utf8');
        process.stdin.on('data', (d) => (buf += d));
        process.stdin.on('end', () => res(buf.trim()));
      });
  if (!raw) throw new Error("缺少入参，请传入完整的 JSON 参数或通过 stdin 传入");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}` } }));
  process.exit(1);
}

// ── Validate required fields ──
const missing = [];
if (input.organization_id == null || input.organization_id === "") missing.push("organization_id");
if (!input.marketing_target_type) missing.push("marketing_target_type");
if (!Array.isArray(input.properties) || input.properties.length === 0) missing.push("properties");

if (missing.length > 0) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `缺少必填参数: ${missing.join(", ")}` },
  }));
  process.exit(1);
}

// ── Validate marketing_target_type enum ──
const VALID_MARKETING_TARGET_TYPES = new Set([
  "MARKETING_TARGET_TYPE_FRANCHISE_BRAND",
  "MARKETING_TARGET_TYPE_ENTERPRISE_SERVICES",
  "MARKETING_TARGET_TYPE_REAL_ESTATE",
  "MARKETING_TARGET_TYPE_LIVE_STREAM_ROOM",
  "MARKETING_TARGET_TYPE_PERSONAL_STORE",
  "MARKETING_TARGET_TYPE_AUDIOVISUAL_ENTERTAINMENT",
  "MARKETING_TARGET_TYPE_PLATFORM_CHANNEL",
  "MARKETING_TARGET_TYPE_STORE",
  "MARKETING_TARGET_TYPE_FINANCE",
  "MARKETING_TARGET_TYPE_TOURIST_ATTRACTIONS_TICKETS",
  "MARKETING_TARGET_TYPE_TOURIST_TRAVEL_ROUTE",
  "MARKETING_TARGET_TYPE_TOURIST_CRUISE_LINE",
  "MARKETING_TARGET_TYPE_TOURIST_HOTEL_SERVICE",
  "MARKETING_TARGET_TYPE_TOURIST_AIRLINE_TICKETS",
  "MARKETING_TARGET_TYPE_ACTIVITY",
  "MARKETING_TARGET_TYPE_CATERING_AND_LEISURE",
  "MARKETING_TARGET_TYPE_CHAIN_RESTAURANT",
  "MARKETING_TARGET_TYPE_PRODUCT",
  "MARKETING_TARGET_TYPE_TELECOMMUNICATIONS_OPERATOR",
  "MARKETING_TARGET_TYPE_RENOVATION_SERVICES",
  "MARKETING_TARGET_TYPE_FURNITURE_AND_BUILDING_MATERIALS",
  "MARKETING_TARGET_TYPE_BEAUTY_AND_PERSONAL_CARE",
  "MARKETING_TARGET_TYPE_WEDDING_AND_PORTRAIT_PHOTOGRAPHY",
  "MARKETING_TARGET_TYPE_COMPREHENSIVE_HOUSEKEEPING",
  "MARKETING_TARGET_TYPE_VIDEO_PROGRAM",
  "MARKETING_TARGET_TYPE_FICTION",
  "MARKETING_TARGET_TYPE_SHORT_DRAMA",
  "MARKETING_TARGET_TYPE_TRAFFIC",
]);

if (!VALID_MARKETING_TARGET_TYPES.has(input.marketing_target_type)) {
  const suggestions = [];
  const inputLower = input.marketing_target_type.toLowerCase();
  for (const valid of VALID_MARKETING_TARGET_TYPES) {
    if (valid.toLowerCase().includes(inputLower.replace(/^promoted_asset_type_/, 'marketing_target_type_')) ||
        inputLower.includes(valid.toLowerCase()) ||
        valid.endsWith(input.marketing_target_type.toUpperCase())) {
      suggestions.push(valid);
    }
  }

  // Levenshtein distance fallback
  if (suggestions.length === 0) {
    let best = null;
    let bestDist = Infinity;
    for (const valid of VALID_MARKETING_TARGET_TYPES) {
      const dist = levenshtein(input.marketing_target_type, valid);
      if (dist < bestDist) { bestDist = dist; best = valid; }
    }
    if (best && bestDist <= 10) suggestions.push(best);
  }

  const hint = suggestions.length > 0
    ? `\n💡 是否要使用: ${suggestions.join(", ")}？`
    : `\n📋 有效值列表: ${[...VALID_MARKETING_TARGET_TYPES].sort().join(", ")}`;

  console.log(JSON.stringify({
    success: false,
    error: {
      message: `无效的 marketing_target_type: "${input.marketing_target_type}"。${hint}`,
    },
  }));
  process.exit(1);
}

// ── Validate properties structure ──
for (let i = 0; i < input.properties.length; i++) {
  const prop = input.properties[i];
  const propIssues = [];
  if (!prop.property_name) propIssues.push("property_name");
  if (!Array.isArray(prop.property_value) || prop.property_value.length === 0) propIssues.push("property_value");
  if (propIssues.length > 0) {
    console.log(JSON.stringify({
      success: false,
      error: { message: `properties[${i}] 缺少必填字段: ${propIssues.join(", ")}` },
    }));
    process.exit(1);
  }
  // Validate property_name starts with correct prefix
  if (!prop.property_name.startsWith("PROMOTED_ASSET_ATTR_KEY_")) {
    console.log(JSON.stringify({
      success: false,
      error: { message: `properties[${i}].property_name 必须以 PROMOTED_ASSET_ATTR_KEY_ 开头，当前值为: "${prop.property_name}"` },
    }));
    process.exit(1);
  }
}

// ── Geo name → id conversion for geo-type property values ──
// 地域类属性的 property_value 支持两种格式：
//   1. 中文名（如"青海省"）→ 自动转换为 geo_id 字符串（如"630000"）
//   2. 数字字符串（如"630000"）→ 直接透传，跳过转换
function isGeoAttr(propertyName) {
  for (const suffix of GEO_ATTR_SUFFIXES) {
    if (propertyName.endsWith(suffix)) return true;
  }
  return false;
}

function findGeoSuggestions(name, regions, limit = 5) {
  const suggestions = [];
  for (const [regionName] of regions) {
    if (regionName.includes(name) || name.includes(regionName)) {
      suggestions.push(regionName);
      if (suggestions.length >= limit) return suggestions;
    }
  }
  return suggestions;
}

const geoErrors = [];
for (let i = 0; i < input.properties.length; i++) {
  const prop = input.properties[i];
  if (!isGeoAttr(prop.property_name)) continue;

  const regions = getGeoRegions();
  const converted = [];
  for (const val of prop.property_value) {
    // 已经是数字 id，直接透传
    if (/^\d+$/.test(val)) {
      converted.push(val);
      continue;
    }
    // 中文名 → 查找 id
    const entry = regions.get(val);
    if (!entry) {
      const suggestions = findGeoSuggestions(val, regions);
      const hint = suggestions.length > 0
        ? `\n💡 候选地名: ${suggestions.join("、")}`
        : "\n💡 请检查地名是否正确，可参考腾讯广告地域列表";
      geoErrors.push(
        `properties[${i}].property_value 中 "${val}" 不是合法地域名称。${hint}`
      );
    } else {
      converted.push(String(entry.id));
    }
  }
  // 替换为转换后的 id 列表（仅在无错误时生效）
  if (geoErrors.length === 0) {
    prop.property_value = converted;
  }
}

if (geoErrors.length > 0) {
  console.log(JSON.stringify({
    success: false,
    error: { message: geoErrors.join("\n") },
  }));
  process.exit(1);
}

// ── Warn if marketing_asset_name is missing (optional but strongly recommended) ──
if (!input.marketing_asset_name || input.marketing_asset_name === "") {
  console.error("⚠️  警告: 未提供 marketing_asset_name，创建的资产将没有名称。建议传入资产名称。");
}

// ── Helper: Levenshtein distance ──
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    }
  }
  return dp[m][n];
}

// ── Build request body ──
const body = {
  organization_id: parseInt(String(input.organization_id), 10),
  marketing_target_type: String(input.marketing_target_type),
  properties: input.properties.map((prop) => {
    const item = {
      property_name: String(prop.property_name),
      property_value: prop.property_value.map((v) => String(v)),
    };
    if (prop.property_class) item.property_class = String(prop.property_class);
    if (prop.property_cn) item.property_cn = String(prop.property_cn);
    return item;
  }),
};

if (input.marketing_asset_name != null && input.marketing_asset_name !== "") {
  body.marketing_asset_name = String(input.marketing_asset_name);
}
if (input.marketing_asset_type != null && input.marketing_asset_type !== "") {
  body.marketing_asset_type = String(input.marketing_asset_type);
}
if (input.meituan_rank != null && input.meituan_rank !== "") {
  body.meituan_rank = String(input.meituan_rank);
}

// ── Call API ──
const result = await callApi({
  method: "POST",
  path: "/v3.0/marketing_target_assets/add",
  accountId: undefined,
  body,
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: { message: `创建推广内容资产失败: ${result.error?.message || JSON.stringify(result.error)}` },
  }));
  process.exit(1);
}

// ── Output ──
const data = result.data?.data ?? result.data ?? {};
console.log(JSON.stringify(data, null, 2));
