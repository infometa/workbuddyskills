#!/usr/bin/env node
/**
 * push-auth-sys-info v1
 * 推送系统信息与菜单权限项到权限中台（仅测试环境）
 *
 * 运行：node <SKILL_DIR>/scripts/push-auth-sys-info.js
 *   - 默认从「当前工作目录」下的 .hrright/auth.config.json 读取配置
 *   - 也可通过环境变量 HRRIGHT_CONFIG 指定绝对路径
 *
 * 依赖：Node.js >= 18（使用内置 fetch），无第三方依赖
 *
 * 退出码：
 *   0 = 推送成功（success === true && code === "0"）
 *   非 0 = 配置/校验/网络/接口失败（自带 1 次重试后仍失败）
 */
'use strict';

const fs = require('fs');
const path = require('path');

const URL = 'http://test-prod-slave-right.woa.com/api/ai/auth/saveAiAppSysInfo';
const CONFIG = path.resolve(
  process.env.HRRIGHT_CONFIG || path.join(process.cwd(), '.hrright/auth.config.json')
);

if (typeof fetch !== 'function') {
  console.error('[FATAL] 需要 Node.js >= 18（缺少全局 fetch）');
  process.exit(1);
}

async function main() {
  if (!fs.existsSync(CONFIG)) {
    throw new Error(`配置文件不存在: ${CONFIG}`);
  }

  let cfg;
  try {
    cfg = JSON.parse(fs.readFileSync(CONFIG, 'utf-8'));
  } catch (e) {
    throw new Error(`配置文件解析失败: ${CONFIG} (${e.message})`);
  }

  const { sysCode, hrclawAppId, operator, permissions } = cfg;

  for (const [k, v] of Object.entries({ sysCode, hrclawAppId, operator })) {
    if (!v || typeof v !== 'string') {
      throw new Error(`字段 ${k} 为空或类型错误，无法推送`);
    }
  }
  if (!Array.isArray(permissions) || permissions.length === 0) {
    throw new Error('permissions 为空，无法推送');
  }

  const payload = { sysCode, hrclawAppId, operator, permissions };

  console.log(
    `[INFO] 准备推送：sysCode=${sysCode}, hrclawAppId=${hrclawAppId}, ` +
      `operator=${operator}, permissions.count=${permissions.length}`
  );
  console.log(`[INFO] URL=${URL}`);

  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const res = await fetch(URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const text = await res.text();
      let r;
      try {
        r = JSON.parse(text);
      } catch (_) {
        console.error(`[FAIL ${attempt}] HTTP ${res.status}, body 非 JSON: ${text.slice(0, 500)}`);
        continue;
      }

      if (r.success === true && r.code === '0') {
        console.log(
          `[OK] 推送成功：sysCode=${sysCode}, hrclawAppId=${hrclawAppId}, count=${permissions.length}`
        );
        return;
      }
      console.error(`[FAIL ${attempt}] code=${r.code}, msg=${r.msg}`);
    } catch (e) {
      console.error(`[ERROR ${attempt}] ${e.message}`);
    }
  }

  console.error('[FATAL] 重试 1 次后仍失败，已中止');
  process.exit(1);
}

main().catch((e) => {
  console.error(`[FATAL] ${e.message}`);
  process.exit(1);
});
