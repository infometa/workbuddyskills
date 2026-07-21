#!/usr/bin/env node
/**
 * get-enum-options.mjs — 查询枚举可选值（Agent 运行时调用）
 *
 * 从本地 enums.json 读取枚举定义，返回指定字段的可选值列表。
 * 纯本地操作，无 API 调用，零延迟。
 *
 * 入参:
 *   查询指定字段:  '{"fields": ["education", "bid_mode"]}'
 *   查询某个分类:  '{"category": "targeting"}'
 *   查询全部:      '{"fields": "all"}'
 *
 * 输出:
 * {
 *   "education": {
 *     "desc": "学历",
 *     "field_path": "targeting.education",
 *     "options": [
 *       { "key": "DOCTOR", "label": "博士" },
 *       { "key": "MASTER", "label": "硕士" },
 *       ...
 *     ]
 *   },
 *   "bid_mode": { ... }
 * }
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// enums.json 位于 skill 的 resources 目录
const ENUMS_FILE = join(__dirname, "../resources/enums.json");

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

// ─── 加载枚举数据 ───

let allEnums;
try {
  allEnums = JSON.parse(readFileSync(ENUMS_FILE, "utf-8"));
} catch (err) {
  console.log(
    JSON.stringify({
      error: `无法读取枚举文件 ${ENUMS_FILE}: ${err.message}`,
      hint: "请先运行 node scripts/gen-enums.mjs 生成 enums.json",
    })
  );
  process.exit(1);
}

// ─── 筛选逻辑 ───

const { fields, category } = input;

let selectedKeys;

if (fields === "all") {
  // 返回全部
  selectedKeys = Object.keys(allEnums);
} else if (Array.isArray(fields) && fields.length > 0) {
  // 返回指定字段
  selectedKeys = fields;
} else if (typeof category === "string") {
  // 按分类筛选
  selectedKeys = Object.keys(allEnums).filter(
    (k) => allEnums[k].category === category
  );
  if (selectedKeys.length === 0) {
    const validCategories = [
      ...new Set(Object.values(allEnums).map((e) => e.category)),
    ];
    console.log(
      JSON.stringify({
        error: `未找到分类 "${category}" 的枚举`,
        available_categories: validCategories,
      })
    );
    process.exit(1);
  }
} else {
  console.log(
    JSON.stringify({
      error:
        '请指定 fields（数组或 "all"）或 category（分类名）',
      usage: {
        "查询指定字段": '{"fields": ["education", "bid_mode"]}',
        "查询某分类": '{"category": "targeting"}',
        "查询全部": '{"fields": "all"}',
      },
      available_fields: Object.keys(allEnums),
      available_categories: [
        ...new Set(Object.values(allEnums).map((e) => e.category)),
      ],
    })
  );
  process.exit(1);
}

// ─── 构造输出 ───

const result = {};
const notFound = [];

for (const key of selectedKeys) {
  const enumDef = allEnums[key];
  if (!enumDef) {
    notFound.push(key);
    continue;
  }

  // 输出只保留 Agent 需要的信息：desc, field_path, options (去掉 value 数值)
  result[key] = {
    desc: enumDef.desc,
    field_path: enumDef.field_path,
    options: enumDef.options.map((opt) => ({
      key: opt.key,
      label: opt.label,
    })),
  };
}

// 如果有找不到的字段，附上提示
if (notFound.length > 0) {
  result._not_found = {
    fields: notFound,
    hint: "以下字段在枚举库中不存在，请检查字段名是否正确",
    available_fields: Object.keys(allEnums),
  };
}

console.log(JSON.stringify(result, null, 2));
