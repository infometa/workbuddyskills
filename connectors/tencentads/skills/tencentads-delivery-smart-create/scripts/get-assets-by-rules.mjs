#!/usr/bin/env node
/**
 * get-assets-by-rules.mjs — 根据 combinations 批量获取各 marketing_target_type 对应的推广资产
 *
 * 接收 get-rules.mjs 返回的 combinations 数组和 account_id，
 * 内部自动对 marketing_target_type 去重（distinct），每种只调一次 API，
 * 返回以 marketing_target_type 为 key 的资产 map。
 *
 * 核心查询逻辑复用 get-assets.mjs 的 fetchAssetsForTargetType()，
 * 避免维护两份相同的 API 调用代码。返回结构与 get-assets.mjs 完全一致
 * （含 flat_params、type 等字段），Agent 可直接复用。
 *
 * 入参: '{"account_id":"<ID>","combinations":[...]}'
 *   combinations 为 get-rules.mjs 返回的 combinations 数组（脚本内部处理去重，调用方无需预处理）
 *
 * 输出:
 * {
 *   "asset_map": {
 *     "MARKETING_TARGET_TYPE_REAL_ESTATE": {
 *       "asset_type": "INDUSTRY",
 *       "assets": [
 *         {
 *           "marketing_asset_id": "342574",
 *           "name": "京投发展森与天成",
 *           "type": "REAL_ESTATE",
 *           "flat_params": {
 *             "asset_id": "342574"
 *           }
 *         }
 *       ]
 *     },
 *     "MARKETING_TARGET_TYPE_WECHAT_MINI_GAME": {
 *       "asset_type": "ONEID",
 *       "assets": [
 *         {
 *           "marketing_asset_outer_id": "wx123",
 *           "marketing_carrier_id": "wx123",
 *           "name": "某小游戏",
 *           "type": "WECHAT_MINI_GAME",
 *           "flat_params": {
 *             "asset_id": "wx123",
 *             "carrier_id": "wx123",
 *             "asset_name": "某小游戏",
 *             "carrier_name": "某小游戏"
 *           }
 *         }
 *       ]
 *     }
 *   }
 * }
 *
 * flat_params 说明（与 get-assets.mjs / create-adgroup.mjs 方式一完全一致，共 7 个）：
 *   asset_id       — 推广产品 ID（ONEID→outer_id / 行业→asset_id / 商品库→catalog_id）
 *   carrier_id     — 载体 ID（ONEID 类和视频号直播类 = outer_id；行业/商品库类不含此字段，若需要载体需从用户处获取）
 *   catalog_id     — 商品库场景的 catalog_id
 *   asset_sub_id   — 子标识（商品库→product_outer_id；直播预约需 Agent 选 notice_id 后补入）
 *   asset_name     — 资产名称（ONEID 类自动填入；写入 marketing_asset_outer_name）
 *   carrier_name   — 载体名称（ONEID 类自动填入；仅 QUICK_APP/PC_GAME 生效，其他类型自动忽略）
 *   sub_carrier_id — 载体子标识（直播预约需 Agent 选 notice_id 后补入 → marketing_sub_carrier_id）
 *
 * Agent 选定 asset 后，将 flat_params 直接展开透传给 create-adgroup.mjs 即可。
 *
 * 设计说明：
 * - 相同 marketing_target_type 只调一次 API（内部自动 distinct）
 * - key 为 marketing_target_type 枚举值，调用方直接按 target_type 查找即可
 * - 查询失败或返回空的 target_type，value 中 assets 为空数组（不中断流程）
 * - 返回结构与 get-assets.mjs 完全一致（含 flat_params），可直接用于步骤 3 的资产选择
 */

import { fetchAssetsForTargetType } from "./get-assets.mjs";

// ─── 参数解析 ───

let input;
try {
  const raw = process.argv[2];
  if (!raw) throw new Error("缺少入参，请传入 JSON 字符串");
  input = JSON.parse(raw);
} catch (err) {
  console.log(JSON.stringify({ error: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` }));
  process.exit(1);
}

const { account_id, combinations } = input;

if (!account_id) {
  console.log(JSON.stringify({ error: "missing required field: account_id" }));
  process.exit(1);
}
if (!combinations || !Array.isArray(combinations) || combinations.length === 0) {
  console.log(JSON.stringify({ error: "missing required field: combinations (应为 get-rules.mjs 返回的 combinations 数组)" }));
  process.exit(1);
}

// ─── 按 marketing_target_type 去重，每种只调一次 API ───

const uniqueTargetTypes = [...new Set(combinations.map(c => c.marketing_target_type))];

const assetMap = {};

for (const targetType of uniqueTargetTypes) {
  try {
    assetMap[targetType] = await fetchAssetsForTargetType(account_id, targetType);
  } catch (err) {
    // 查询失败不中断，记录空结果
    assetMap[targetType] = { asset_type: "UNKNOWN", assets: [] };
  }
}

console.log(JSON.stringify({ asset_map: assetMap }, null, 2));
