#!/usr/bin/env node
/**
 * create-creative.mjs — 创建动态创意
 *
 * 调用 POST /v3.0/dynamic_creatives/add
 *
 * 前置要求：入参必须是 build-creative-params.mjs 输出的 params 对象（已完成所有预处理和校验）。
 * 不要将原始用户输入直接传入此脚本，所有参数规范化、字段补全、校验均在 build-creative-params 中完成。
 * 若需在 build 输出的基础上修改参数，请修改后重新调用 build-creative-params.mjs 再传入此脚本。
 *
 * 入参: '<build-creative-params.mjs 输出的 params JSON>'
 * 必填: account_id, adgroup_id, creative_components, dynamic_creative_name
 *
 * 输出（成功）:
 * { "success": true, "dynamic_creative_id": 8362490722 }
 *
 * 输出（失败）:
 * { "success": false, "error": { "code": 40001, "message": "..." } }
 */

import { callApi } from "tencentads-cli";
import { validateCreativeParams } from "./lib/validate-creative-params.mjs";

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
  console.log(JSON.stringify({ success: false, error: { message: `参数解析失败: ${err.message}。请检查：1) JSON 参数是否完整；2) 引号转义是否适配当前终端（Windows CMD 用双引号+反斜杠转义，PowerShell 5.x 须加 --% 或用 \`" 组合转义，Bash/Zsh/Git Bash 用单引号包裹）` } }));
  process.exit(1);
}

// ── 参数校验（共享校验模块，防止跳过 build-creative-params 时遗漏必填字段）────
const { errors: validationErrors } = validateCreativeParams(input);
if (validationErrors.length > 0) {
  // 检测是否缺少 build-creative-params.mjs 自动生成的字段（如 dynamic_creative_name）
  // 若缺少，说明 Agent 很可能跳过了 build 步骤，需引导其先执行 build
  const buildGeneratedFields = ["dynamic_creative_name", "dynamic_creative_type"];
  const missingBuildFields = buildGeneratedFields.filter(
    f => input[f] == null || input[f] === ""
  );
  const hint = missingBuildFields.length > 0
    ? `。检测到缺少 ${missingBuildFields.join(', ')} 等由 build-creative-params.mjs 自动生成的字段，` +
      `请先执行 build-creative-params.mjs 完成参数预处理和校验，再将其输出的 params 传入本脚本`
    : "";
  console.log(JSON.stringify({
    success: false,
    error: { message: validationErrors.join('; ') + hint },
  }));
  process.exit(1);
}

const { account_id, ...bodyParams } = input;
const accountId = parseInt(account_id, 10);
const adgroupId = bodyParams.adgroup_id;

// ── 创意数量上限检查（与前端对齐：非自定义创意上限 100 个）────────────────────
const CREATIVE_MAX_SIZE = 100;
const deliveryMode = bodyParams.delivery_mode ?? "DELIVERY_MODE_COMPONENT";
if (deliveryMode !== "DELIVERY_MODE_CUSTOMIZE") {
  try {
    const countResult = await callApi({
      method: "GET",
      path: "/v3.0/dynamic_creatives/get",
      accountId: String(accountId),
      params: {
        account_id: accountId,
        page: 1,
        page_size: 1,
        filtering: JSON.stringify([
          { field: "adgroup_id", operator: "EQUALS", values: [String(adgroupId)] },
        ]),
        fields: JSON.stringify(["dynamic_creative_id"]),
        is_deleted: false,
      },
    });
    if (countResult.success) {
      const totalNumber =
        countResult.data?.data?.page_info?.total_number ??
        countResult.data?.page_info?.total_number ??
        0;
      if (totalNumber >= CREATIVE_MAX_SIZE) {
        console.log(JSON.stringify({
          success: false,
          error: {
            message:
              `该广告组下创意已达到 ${totalNumber} 个（上限 ${CREATIVE_MAX_SIZE}），不能再新增创意。` +
              `请先删除部分已有创意后重试。`,
          },
        }));
        process.exit(1);
      }
    }
  } catch {
    // 查询失败时不阻断创建流程，由 API 自身返回错误
  }
}

const result = await callApi({
  method: "POST",
  path: "/v3.0/dynamic_creatives/add",
  accountId: String(accountId),
  body: {
    account_id: accountId,
    ...bodyParams,
  },
});

if (!result.success) {
  console.log(JSON.stringify({
    success: false,
    error: {
      code: result.error?.code,
      message: result.error?.message || "API 调用失败",
      message_cn: result.error?.message_cn,
      trace_id: result.error?.trace_id,
    },
  }));
  process.exit(1);
}

const creativeId =
  result.data?.data?.dynamic_creative_id ??
  result.data?.dynamic_creative_id ??
  null;

if (!creativeId) {
  console.log(JSON.stringify({ success: true, data: result.data }, null, 2));
} else {
  console.log(JSON.stringify({ success: true, dynamic_creative_id: creativeId }, null, 2));
}
