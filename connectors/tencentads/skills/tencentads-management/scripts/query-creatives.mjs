#!/usr/bin/env node
/**
 * query-creatives.mjs — 腾讯广告管理 - 创意列表查询
 *
 * 封装腾讯广告开放 API dynamic_creatives/get 接口，用于获取创意的完整信息，
 * 包括创意组件引用（creative_components）、投放模式、创意类型等。
 *
 * 智能组件解析策略（自动判断，无需手动控制）：
 * - 当查询结果**只有 1 条创意**时，脚本自动：
 *   1. 从 creative_components 中提取所有 component_id
 *   2. 调用 components/get 批量拉取组件详情
 *   3. 从组件中提取 image_id / video_id
 *   4. 调用 images/get 和 videos/get 获取图片/视频的预览 URL
 *   5. 将组件内容 + 预览 URL 内联到 _component_detail 字段
 * - 当查询结果**有多条创意**时，只返回创意基本信息，不解析组件
 *
 * 入参:
 * '{
 *   "account_id": "<ID>",
 *
 *   // ─── 以下均为可选 ───
 *   "tencent_ads_type": "smart" | "standard" | "all",   // 实体类型："smart"=智能投放项目, "standard"=竞价广告（非智投）, "all"=所有广告（默认）
 *   "creative_ids": ["123456"],             // 指定创意 ID 列表
 *   "adgroup_ids": ["789"],                 // 按广告 ID 过滤创意
 *   "fields": ["dynamic_creative_id", ...], // 自定义返回字段
 *   "filtering": [...],                     // 自定义过滤条件
 *   "page": 1,                              // 页码（最大 100）
 *   "page_size": 10,                        // 每页条数（最大 100）
 *   "is_deleted": false,                    // 是否查询已删除创意
 *   "pagination_mode": "PAGINATION_MODE_NORMAL",  // 分页方式
 *   "cursor": ""                            // 游标值（配合游标分页）
 * }'
 *
 * 输出:
 * {
 *   "list": [...],
 *   "page_info": { "page": 1, "page_size": 10, "total_number": 50, "total_page": 5 }
 * }
 */

import { callApi } from "tencentads-cli";

// ─── 参数解析 ───

let input;
try {
  let raw;
  if (process.argv[2] === "--base64") {
    const b64 = process.argv[3];
    if (!b64) throw new Error("--base64 后需指定 Base64 编码的 JSON 字符串");
    raw = Buffer.from(b64, "base64").toString("utf-8");
  } else {
    raw = process.argv[2];
  }
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串或使用 --base64 <string>");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。支持两种传参方式：1) 直接传 JSON 字符串（Bash/Zsh）；2) --base64 <string> Base64 编码传参（PowerShell）` }));
  process.exit(1);
}

// ─── tencent_ads_type 枚举 ───
const TENCENT_ADS_TYPE = {
  SMART: "smart",         // 智能投放项目
  STANDARD: "standard",   // 竞价广告（非智投）
  ALL: "all",             // 所有广告（默认）
};
const VALID_ADS_TYPES = new Set(Object.values(TENCENT_ADS_TYPE));

const {
  account_id,
  tencent_ads_type = TENCENT_ADS_TYPE.ALL,
  creative_ids,
  adgroup_ids,
  fields: userFields,
  filtering: userFiltering,
  page = 1,
  page_size = 10,
  is_deleted = false,
  pagination_mode,
  cursor,
} = input;

// ─── 参数校验 ───

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!VALID_ADS_TYPES.has(tencent_ads_type)) {
  console.log(JSON.stringify({ error: `invalid tencent_ads_type: "${tencent_ads_type}", must be one of: ${[...VALID_ADS_TYPES].join(", ")}` }));
  process.exit(1);
}

// ─── 默认字段 ───

const DEFAULT_FIELDS = [
  "dynamic_creative_id",
  "dynamic_creative_name",
  "adgroup_id",
  "creative_template_id",
  "delivery_mode",
  "dynamic_creative_type",
  "creative_components",
  "impression_tracking_url",
  "click_tracking_url",
  "program_creative_info",
  "page_track_url",
  "auto_derived_program_creative_switch",
  "configured_status",
  "is_deleted",
  "created_time",
  "last_modified_time",
  "marketing_asset_verification",
  "creative_set_approval_status",
  "asset_inconsistent_status",
  "source_dynamic_creative_id",
  "smart_delivery_platform",
];

// ─── 构建 filtering ───

/** 需要从 'YYYY-MM-DD HH:mm:ss' 转为 Unix 时间戳的过滤字段 */
const TIME_FILTER_FIELDS = new Set(["created_time", "last_modified_time", "completed_time"]);

/**
 * 将 filtering 中时间字段的值从 'YYYY-MM-DD HH:mm:ss' 格式自动转为 Unix 时间戳（秒）。
 * 如果值已经是纯数字（时间戳），则原样保留。
 */
function convertFilteringTimeValues(filters) {
  return filters.map((f) => {
    const bareField = f.field?.includes(".") ? f.field.split(".").pop() : f.field;
    if (!TIME_FILTER_FIELDS.has(bareField)) return f;

    return {
      ...f,
      values: (f.values || []).map((v) => {
        if (/^\d+$/.test(String(v))) return v;
        const parsed = Date.parse(String(v).replace(" ", "T") + "+08:00");
        if (isNaN(parsed)) return v;
        return String(Math.floor(parsed / 1000));
      }),
    };
  });
}

function buildFiltering() {
  const filters = [];

  // 如果传了 creative_ids，构建 ID 过滤
  if (creative_ids?.length) {
    filters.push({
      field: "dynamic_creative_id",
      operator: creative_ids.length === 1 ? "EQUALS" : "IN",
      values: creative_ids.map(String),
    });
  }

  // 如果传了 adgroup_ids，按广告 ID 过滤
  if (adgroup_ids?.length) {
    filters.push({
      field: "adgroup_id",
      operator: adgroup_ids.length === 1 ? "EQUALS" : "IN",
      values: adgroup_ids.map(String),
    });
  }

  // 追加用户自定义过滤条件（自动转换时间字段）
  if (Array.isArray(userFiltering)) {
    filters.push(...convertFilteringTimeValues(userFiltering));
  }

  return filters.length > 0 ? filters : undefined;
}

// ─── 构造请求参数 ───

const params = {
  account_id: parseInt(account_id, 10),
  fields: userFields?.length ? userFields : DEFAULT_FIELDS,
  page: Math.min(Number(page), 100),
  page_size: Math.min(Number(page_size), 100),
};

// 可选参数
if (is_deleted) params.is_deleted = true;

const filtering = buildFiltering();
if (filtering) params.filtering = filtering;

if (pagination_mode) params.pagination_mode = pagination_mode;
if (cursor) params.cursor = cursor;

// ─── 调用创意列表 API ───

const result = await callApi({
  method: "GET",
  path: "/v3.0/dynamic_creatives/get",
  accountId: String(account_id),
  params,
});

if (!result.success) {
  console.log(JSON.stringify({
    error: result.error?.message || "API 调用失败",
    detail: result.error,
  }));
  process.exit(1);
}
// ─── 处理返回数据 ───

const data = result.data?.data ?? result.data ?? {};
const list = data?.list ?? [];
const pageInfo = data?.page_info ?? {};
const cursorPageInfo = data?.cursor_page_info ?? undefined;

// ─── 自动解析组件详情（仅当查询结果只有 1 条创意时触发） ───

/**
 * 从创意列表中提取所有组件 ID
 */
function extractComponentIds(creativeList) {
  const componentIds = new Set();

  for (const creative of creativeList) {
    const components = creative.creative_components;
    if (!components || typeof components !== "object") continue;

    // creative_components 是一个 map，key 为组件类型，value 为组件数组或单个组件
    for (const [, compValue] of Object.entries(components)) {
      if (Array.isArray(compValue)) {
        for (const comp of compValue) {
          if (comp?.component_id) componentIds.add(String(comp.component_id));
        }
      } else if (compValue && typeof compValue === "object") {
        if (compValue.component_id) componentIds.add(String(compValue.component_id));
        // 有些结构中组件列表在 value 字段内
        if (Array.isArray(compValue.value)) {
          for (const comp of compValue.value) {
            if (comp?.component_id) componentIds.add(String(comp.component_id));
          }
        }
      }
    }
  }

  return [...componentIds];
}

/**
 * 批量拉取组件详情
 */
async function fetchComponentDetails(componentIds) {
  if (!componentIds.length) return {};

  const componentMap = {};
  const batchSize = 200; // components/get 每页最多 200

  for (let i = 0; i < componentIds.length; i += batchSize) {
    const batch = componentIds.slice(i, i + batchSize);

    const compResult = await callApi({
      method: "GET",
      path: "/v3.0/components/get",
      accountId: String(account_id),
      params: {
        account_id: parseInt(account_id, 10),
        filtering: [{
          field: "component_id",
          operator: batch.length === 1 ? "EQUALS" : "IN",
          values: batch,
        }],
        page: 1,
        page_size: batchSize,
        fields: [
          "component_id",
          "component_value",
          "component_sub_type",
          "component_custom_name",
          "generation_type",
          "created_time",
          "last_modified_time",
          "is_deleted",
          "similarity_status",
        ],
      },
    });

    if (compResult.success) {
      const compList = compResult.data?.list ?? compResult.data?.data?.list ?? [];
      for (const comp of compList) {
        if (comp.component_id) {
          componentMap[String(comp.component_id)] = comp;
        }
      }
    }
    // 组件拉取失败不中断流程，只是该批次组件不会被解析
  }

  return componentMap;
}

/**
 * 从组件详情中提取所有 image_id 和 video_id
 *
 * component_value 的实际结构为：
 *   { "<type>": { "value": { "video_id": "xxx", "cover_id": "xxx" } } }
 * 需穿透 .value 层才能取到媒体 ID。
 */
function extractMediaIds(componentMap) {
  const imageIds = new Set();
  const videoIds = new Set();

  for (const comp of Object.values(componentMap)) {
    const cv = comp.component_value;
    if (!cv || typeof cv !== "object") continue;

    // 遍历所有子组件类型，提取 image_id / video_id
    for (const [, subValue] of Object.entries(cv)) {
      if (!subValue || typeof subValue !== "object") continue;

      // 实际结构多一层 .value，穿透取值
      const inner = subValue.value ?? subValue;

      // 单个子组件对象
      if (inner.image_id) imageIds.add(String(inner.image_id));
      if (inner.video_id) videoIds.add(String(inner.video_id));
      // cover_id 也是图片 ID，一并收集
      if (inner.cover_id) imageIds.add(String(inner.cover_id));

      // 图片列表场景（list 数组）
      if (Array.isArray(inner.list)) {
        for (const item of inner.list) {
          if (item?.image_id) imageIds.add(String(item.image_id));
          if (item?.video_id) videoIds.add(String(item.video_id));
          if (item?.cover_id) imageIds.add(String(item.cover_id));
        }
      }
    }
  }

  return { imageIds: [...imageIds], videoIds: [...videoIds] };
}

/**
 * 批量获取图片预览 URL
 */
async function fetchImagePreviews(imageIds) {
  if (!imageIds.length) return {};

  const imageMap = {};
  const batchSize = 100;

  for (let i = 0; i < imageIds.length; i += batchSize) {
    const batch = imageIds.slice(i, i + batchSize);

    const imgResult = await callApi({
      method: "GET",
      path: "/v3.0/images/get",
      accountId: String(account_id),
      params: {
        account_id: parseInt(account_id, 10),
        filtering: [{
          field: "image_id",
          operator: batch.length === 1 ? "EQUALS" : "IN",
          values: batch,
        }],
        page: 1,
        page_size: batchSize,
        fields: ["image_id", "preview_url", "width", "height", "file_size", "signature"],
      },
    });

    if (imgResult.success) {
      const imgList = imgResult.data?.list ?? imgResult.data?.data?.list ?? [];
      for (const img of imgList) {
        if (img.image_id) {
          imageMap[String(img.image_id)] = img;
        }
      }
    }
  }

  return imageMap;
}

/**
 * 批量获取视频预览 URL
 *
 * 注意：videos/get 接口的过滤字段为 media_id（不是 video_id），
 * 且每次只支持查 1 个 media_id，需逐个请求。
 */
async function fetchVideoPreviews(videoIds) {
  if (!videoIds.length) return {};

  const videoMap = {};

  for (const vid_id of videoIds) {
    const vidResult = await callApi({
      method: "GET",
      path: "/v3.0/videos/get",
      accountId: String(account_id),
      params: {
        account_id: parseInt(account_id, 10),
        filtering: [{
          field: "media_id",
          operator: "EQUALS",
          values: [String(vid_id)],
        }],
        page: 1,
        page_size: 1,
      },
    });

    if (vidResult.success) {
      const vidList = vidResult.data?.list ?? vidResult.data?.data?.list ?? [];
      for (const vid of vidList) {
        if (vid.video_id) {
          videoMap[String(vid.video_id)] = vid;
        }
      }
    }
    // 单个失败不中断，跳过继续
  }

  return videoMap;
}

/**
 * 将组件详情 + 图片/视频预览 URL 内联到创意数据中
 */
function enrichCreativesWithComponents(creativeList, componentMap, imageMap, videoMap) {
  return creativeList.map((creative) => {
    const components = creative.creative_components;
    if (!components || typeof components !== "object") return creative;
    if (Object.keys(componentMap).length === 0) return creative;

    const enriched = { ...creative };
    const enrichedComponents = {};

    for (const [compType, compValue] of Object.entries(components)) {
      if (Array.isArray(compValue)) {
        enrichedComponents[compType] = compValue.map((comp) => {
          if (comp?.component_id && componentMap[String(comp.component_id)]) {
            const detail = { ...componentMap[String(comp.component_id)] };
            // 内联图片/视频预览 URL
            injectMediaPreviews(detail, imageMap, videoMap);
            return { ...comp, _component_detail: detail };
          }
          return comp;
        });
      } else if (compValue && typeof compValue === "object") {
        if (compValue.component_id && componentMap[String(compValue.component_id)]) {
          const detail = { ...componentMap[String(compValue.component_id)] };
          injectMediaPreviews(detail, imageMap, videoMap);
          enrichedComponents[compType] = { ...compValue, _component_detail: detail };
        } else {
          enrichedComponents[compType] = compValue;
        }
      } else {
        enrichedComponents[compType] = compValue;
      }
    }

    enriched.creative_components = enrichedComponents;
    return enriched;
  });
}

/**
 * 在组件详情的 component_value 中注入图片/视频预览信息
 *
 * component_value 实际结构为 { "<type>": { "value": { "video_id": "xxx" } } }，
 * 需穿透 .value 层匹配媒体 ID，并将 _preview 注入到 .value 内部。
 */
function injectMediaPreviews(detail, imageMap, videoMap) {
  const cv = detail.component_value;
  if (!cv || typeof cv !== "object") return;

  for (const [subKey, subValue] of Object.entries(cv)) {
    if (!subValue || typeof subValue !== "object") continue;

    // 穿透 .value 层
    const hasValueLayer = subValue.value && typeof subValue.value === "object";
    const inner = hasValueLayer ? subValue.value : subValue;

    // 单个图片
    if (inner.image_id && imageMap[String(inner.image_id)]) {
      const enrichedInner = { ...inner, _preview: imageMap[String(inner.image_id)] };
      cv[subKey] = hasValueLayer ? { ...subValue, value: enrichedInner } : enrichedInner;
    }
    // 单个视频（video_id + cover_id 都注入预览）
    if (inner.video_id && videoMap[String(inner.video_id)]) {
      const enrichedInner = {
        ...inner,
        _preview: videoMap[String(inner.video_id)],
        ...(inner.cover_id && imageMap[String(inner.cover_id)]
          ? { _cover_preview: imageMap[String(inner.cover_id)] }
          : {}),
      };
      cv[subKey] = hasValueLayer ? { ...subValue, value: enrichedInner } : enrichedInner;
    }

    // 图片列表场景
    if (Array.isArray(inner.list)) {
      const enrichedList = inner.list.map((item) => {
        let enrichedItem = item;
        if (item?.image_id && imageMap[String(item.image_id)]) {
          enrichedItem = { ...enrichedItem, _preview: imageMap[String(item.image_id)] };
        }
        if (item?.video_id && videoMap[String(item.video_id)]) {
          enrichedItem = { ...enrichedItem, _preview: videoMap[String(item.video_id)] };
        }
        if (item?.cover_id && imageMap[String(item.cover_id)]) {
          enrichedItem = { ...enrichedItem, _cover_preview: imageMap[String(item.cover_id)] };
        }
        return enrichedItem;
      });
      const enrichedInner = { ...inner, list: enrichedList };
      cv[subKey] = hasValueLayer ? { ...subValue, value: enrichedInner } : enrichedInner;
    }
  }
}

// ─── 解析组件（仅当结果只有 1 条创意时自动触发） ───

let processedList = list;

if (list.length === 1) {
  const componentIds = extractComponentIds(list);
  if (componentIds.length > 0) {
    // Step 1: 拉取组件详情
    const componentMap = await fetchComponentDetails(componentIds);

    // Step 2: 从组件中提取 image_id / video_id，拉取预览 URL
    const { imageIds, videoIds } = extractMediaIds(componentMap);
    const [imageMap, videoMap] = await Promise.all([
      fetchImagePreviews(imageIds),
      fetchVideoPreviews(videoIds),
    ]);

    // Step 3: 内联组件详情 + 预览 URL 到创意数据中
    processedList = enrichCreativesWithComponents(list, componentMap, imageMap, videoMap);
  }
}

// ─── 字段名映射（屏蔽技术债：智投项目复用广告接口） ───

const isProject = tencent_ads_type === TENCENT_ADS_TYPE.SMART;

/**
 * 将对象中所有包含 "adgroup" 的 key 替换为 "project"，递归处理嵌套对象/数组。
 * 例：adgroup_id → project_id, adgroup_name → project_name
 */
function renameAdgroupToProject(obj) {
  if (Array.isArray(obj)) return obj.map(renameAdgroupToProject);
  if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      const newKey = key.replace(/adgroup/g, "project");
      result[newKey] = renameAdgroupToProject(value);
    }
    return result;
  }
  return obj;
}

// ─── 时间戳 → 可读时间格式转换 ───

/** 需要从 Unix 时间戳转为 'YYYY-MM-DD HH:mm:ss' 的字段 */
const TIMESTAMP_FIELDS = new Set(["created_time", "last_modified_time"]);

/**
 * 将 Unix 时间戳（秒）转为 'YYYY-MM-DD HH:mm:ss' 格式字符串
 */
function formatTimestamp(ts) {
  const d = new Date(Number(ts) * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

/**
 * 递归遍历对象，将时间戳字段转为可读格式
 */
function convertTimestampFields(obj) {
  if (Array.isArray(obj)) return obj.map(convertTimestampFields);
  if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      if (TIMESTAMP_FIELDS.has(key) && typeof value === "number") {
        result[key] = formatTimestamp(value);
      } else if (value && typeof value === "object") {
        result[key] = convertTimestampFields(value);
      } else {
        result[key] = value;
      }
    }
    return result;
  }
  return obj;
}

// ─── 裁剪返回数据 ───

const cleanedList = processedList.map((item) => {
  const cleaned = {};
  for (const [key, value] of Object.entries(item)) {
    // 跳过空对象 {}
    if (value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length === 0) {
      continue;
    }
    // 跳过 null/undefined
    if (value == null) continue;
    cleaned[key] = value;
  }
  const converted = convertTimestampFields(cleaned);
  return isProject ? renameAdgroupToProject(converted) : converted;
});

const output = {
  list: cleanedList,
  page_info: pageInfo,
};

// 如果使用游标分页，附加游标信息
if (cursorPageInfo) {
  output.cursor_page_info = cursorPageInfo;
}

console.log(JSON.stringify(output, null, 2));
