#!/usr/bin/env node
/**
 * get-geo-exclude.mjs — 地域排除转正选（直接输出编码）
 *
 * 从 34 个省级行政区中去掉要排除的省份，直接返回剩余省份的
 * 地域编码 results 数组，格式与 get-targeting-lookup.mjs 的 geo 输出一致。
 *
 * 入参:
 *   '{"exclude":"河北"}'
 *   '{"exclude":"河北 山西"}'
 *   '{"exclude":"河北省 山西省"}'
 *
 * 输出:
 * {
 *   "results": [
 *     {"id": 110000, "name": "北京市", "level": "province"},
 *     {"id": 120000, "name": "天津市", "level": "province"},
 *     ...
 *   ]
 * }
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const RESOURCE_DIR = join(__dirname, "../resources");
const GEO_REGIONS_FILE = join(RESOURCE_DIR, "geo-regions.json");

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}` }));
  process.exit(1);
}

const { exclude } = input;

if (!exclude) {
  console.log(JSON.stringify({ error: "missing required field: exclude（要排除的省份名称，空格或逗号分隔）" }));
  process.exit(1);
}

// ─── 加载地域数据 ───

function loadGeoRegions() {
  try {
    return JSON.parse(readFileSync(GEO_REGIONS_FILE, "utf-8"));
  } catch (err) {
    throw new Error(`无法读取地域编码文件: ${err.message}`);
  }
}

// ─── 获取中国 34 个省级行政区 ───

function getAllProvinces(regions) {
  return Object.entries(regions)
    .filter(([code, entry]) => {
      return /^\d{6}$/.test(code)
        && code.endsWith("0000")
        && entry.level === "province";
    })
    .map(([code, entry]) => ({
      id: parseInt(code, 10),
      name: entry.name ?? "",
      level: entry.level ?? "province",
    }))
    .sort((a, b) => a.id - b.id);
}

// ─── 主逻辑 ───

try {
  const regions = loadGeoRegions();
  const allProvinces = getAllProvinces(regions);

  // 解析排除关键词
  const excludeKeywords = String(exclude)
    .split(/[\s,，]+/)
    .filter(Boolean)
    .map((kw) => kw.toLowerCase());

  // 匹配要排除的省份（模糊包含匹配，和 get-targeting-lookup 的匹配规则一致）
  const excludedNames = [];
  const remaining = allProvinces.filter((p) => {
    const nameLower = p.name.toLowerCase();
    const shouldExclude = excludeKeywords.some((kw) => nameLower.includes(kw));
    if (shouldExclude) {
      excludedNames.push(p.name);
    }
    return !shouldExclude;
  });

  if (excludedNames.length === 0) {
    console.log(JSON.stringify({
      error: `未匹配到要排除的省份: "${exclude}"。请检查省份名称是否正确（如"河北"、"广东"）`,
    }));
    process.exit(1);
  }

  // 直接返回剩余省份的编码结果，格式与 get-targeting-lookup.mjs 的 geo 输出一致
  const results = remaining.map((p) => ({
    id: p.id,
    name: p.name,
    level: p.level,
  }));

  console.log(JSON.stringify({ results }));
} catch (err) {
  console.log(JSON.stringify({ error: err.message }));
  process.exit(1);
}
