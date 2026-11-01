'use strict';
/*
 * 轮次播报的「覆盖面」判定 —— 回答一个问题：**这一轮该由谁推「🙋 收到指令 / ✅ 任务完成」？**
 *
 * 为什么要它（2026-10-23）：
 *   旧口径让 AI 按**宿主品牌**判断（「WorkBuddy / Claude Code 有 hook → 不要调轮次工具」）。
 *   这是错的代理变量：hook 的真实生效条件是**三件事同时成立**
 *     ① 宿主注册了 hook（settings.json / 插件 hooks.json）
 *     ② 有可用接收端（`~/.warroom/receiving-endpoint.json` 或 mcp.json 里有真地址）
 *     ③ 进程真跑起来且推成功（node 路径失效 / 目录被删 / 网络断 → 静默失败）
 *   三者与品牌无关。实际会踩的三种误判：
 *     · WorkBuddy + stdio 套件 + 没跑 install-hook.mjs  → 无 hook，AI 却以为有 → 轮次全丢
 *     · 连接器（插件形态）+ 没跑 --setup               → hook 静默跳过（见 hook 的 explicit 判定）→ 轮次全丢
 *     · hook 注册路径指向一个已被删除/移动的目录          → 宿主每轮起进程失败，日志停在旧日期 → 轮次全丢
 *   三种都是「零报错、大屏就是没有」，AI 与用户都无从判断。
 *
 * 做法：**读本地事实**（hook 日志的真实活动 + 接收端文件 + hook 注册痕迹），给出结论 + 证据，
 *   让 MCP 在 initialize 的 instructions 里直接断言「你该不该调」，而不是让模型猜。
 *
 * 判定表（mode）：
 *   hook    → 近期确有 hook 事件在跑。AI **不要**调 notify_turn_start / notify_turn_end。
 *             子状态 failing：hook 在跑但推送失败 → 仍不要调（同一接收端，补推也一样失败），
 *             该做的是修配置，故 reason 里直说。
 *   self    → 完全没有 hook 的任何痕迹。AI **必须**每轮调那两个工具（并成对）。
 *   unknown → 有注册痕迹但近期无活动（刚装 / 日志被清 / 只是配了接收端还没跑过）。
 *             AI **默认不调**（避免与 hook 重复上屏），先用一句话问用户大屏上有没有「🙋 收到指令」，
 *             没有再由 AI 补 —— 这样既不重复、也不静默缺失。
 *
 * 纯只读、无副作用、无三方依赖。任何异常一律降级为 unknown（绝不让探测本身打断 MCP 启动）。
 */
const fs = require('fs');
const path = require('path');

// 多久之内有过 hook 事件才算「hook 在跑」。24h 足够覆盖「昨天用过、今天还没开口」，
// 又能在「目录被删」后一天内收紧成 self/unknown。
const FRESH_MS = 24 * 60 * 60 * 1000;
// 日志最多读尾部这么多字节 —— hook 日志会轮转到 256KB，全量读没必要。
const TAIL_BYTES = 192 * 1024;

function homeDir() {
  return process.env.USERPROFILE || process.env.HOME || '';
}

function hookLogPath() {
  if (process.env.WARROOM_HOOK_LOG) return process.env.WARROOM_HOOK_LOG;
  const home = homeDir();
  return home ? path.join(home, '.workbuddy', 'logs', 'warroom-hook.log') : '';
}

function receivingStatePath() {
  // 复用 receiving-endpoint.cjs 的路径解析（含按 WARROOM_AI_NAME 隔离的 scope）——
  // 两处各写一份路径拼接，迟早漂移成「探测说缺失、实际能读到」。
  try {
    return require('./receiving-endpoint.cjs').stateFilePath();
  } catch {
    const home = homeDir();
    return home ? path.join(home, '.warroom', 'receiving-endpoint.json') : '';
  }
}

/** 读文件尾部（避免把整个 256KB 日志读进内存再切）。失败返回 ''。 */
function readTail(p) {
  try {
    const st = fs.statSync(p);
    const start = Math.max(0, st.size - TAIL_BYTES);
    const fd = fs.openSync(p, 'r');
    try {
      const len = st.size - start;
      const buf = Buffer.alloc(len);
      fs.readSync(fd, buf, 0, len, start);
      return buf.toString('utf8');
    } finally {
      fs.closeSync(fd);
    }
  } catch {
    return '';
  }
}

function exists(p) {
  try {
    return !!p && fs.existsSync(p);
  } catch {
    return false;
  }
}

/**
 * 解析 hook 日志尾部，取出「最后一次被触发的轮次事件」与「最后一次推送成功」。
 * 日志行形状（warroom-hook.cjs 的 fileLog 产出）：
 *   2026-10-22T17:25:18.586Z [warroom-hook] 事件=UserPromptSubmit 目标=… 来源=…
 *   2026-10-22T17:25:19.292Z ✓ https://… :: ✅ 已推送至 ch-xxx（…）
 *   2026-10-22T17:25:19.298Z [warroom-hook] UserPromptSubmit 推送完成 exit=0
 * 失败形态：`✗` / `推送失败` / `exit=<非0>`。
 */
function parseHookLog(p) {
  const out = {
    exists: false,
    lastTurnEventAt: 0,
    lastTurnEvent: '',
    lastOkAt: 0,
    lastFailAt: 0,
    // hook 实际推去的工位 / 基址 —— 用来发现「hook 在跑，但推的不是用户配的那个工位」
    // （实测现场：接收端 channelId=qclaw，hook 日志 147 条全推 ch-workbuddy）
    lastPushChannel: '',
    lastPushBase: '',
    samples: [],
  };
  const text = readTail(p);
  if (!text) return out;
  out.exists = true;
  const lines = text.split('\n');
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    const m = /^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+(.*)$/.exec(line);
    if (!m) continue;
    const at = Date.parse(m[1]) || 0;
    const rest = m[2];
    const ev = /事件=([A-Za-z]+)/.exec(rest);
    if (ev) {
      const name = ev[1];
      // 只认轮次相关事件：UserPromptSubmit（收到指令）/ Stop / StopFailure（任务完成）
      if (name === 'UserPromptSubmit' || name === 'Stop' || name === 'StopFailure') {
        if (at >= out.lastTurnEventAt) {
          out.lastTurnEventAt = at;
          out.lastTurnEvent = name;
        }
      }
      if (out.samples.length < 3) out.samples.push(m[1] + ' ' + name);
      continue;
    }
    if (/^✓/.test(rest) || /推送完成 exit=0/.test(rest)) {
      if (at > out.lastOkAt) out.lastOkAt = at;
      const ch = /已推送至\s+([A-Za-z0-9_.-]+)/.exec(rest);
      if (ch) out.lastPushChannel = ch[1];
      const b = /^✓\s+(\S+)\s+::/.exec(rest);
      if (b) out.lastPushBase = b[1];
    } else if (/^✗/.test(rest) || /推送失败/.test(rest) || /推送完成 exit=[1-9]/.test(rest)) {
      if (at > out.lastFailAt) out.lastFailAt = at;
    }
  }
  return out;
}

/** 宿主是否注册过本套件的 hook（只取「有/没有」，不判它是否还有效）。 */
function detectHookRegistration() {
  const found = [];
  const home = homeDir();
  if (!home) return found;
  // ① 手工 install-hook 写进宿主 settings.json
  for (const rel of ['.workbuddy/settings.json', '.claude/settings.json']) {
    const p = path.join(home, rel);
    if (!exists(p)) continue;
    try {
      const txt = fs.readFileSync(p, 'utf8');
      if (txt.includes('warroom-hook')) found.push(rel + '（命令含 warroom-hook）');
    } catch {
      /* ignore */
    }
  }
  // ② 连接器插件包（引擎自动发现 <插件根>/hooks/hooks.json）
  const cacheRoot = path.join(home, '.workbuddy', 'plugins', 'cache');
  try {
    for (const market of fs.readdirSync(cacheRoot)) {
      const pkgRoot = path.join(cacheRoot, market, 'aiwho-warroom');
      if (!exists(pkgRoot)) continue;
      for (const ver of fs.readdirSync(pkgRoot)) {
        if (exists(path.join(pkgRoot, ver, 'hooks', 'hooks.json'))) {
          found.push('插件包 ' + market + '/' + ver + '/hooks/hooks.json');
        }
      }
    }
  } catch {
    /* cache 目录不存在 */
  }
  return found;
}

function isHttp(u) {
  return /^https?:\/\//i.test(String(u || ''));
}

function isLoopback(u) {
  return /localhost|127\.0\.0\.1|0\.0\.0\.0/i.test(String(u || ''));
}

/** 接收端是否「可用」（有真地址，不是回环兜底）。 */
function detectReceiving() {
  const p = receivingStatePath();
  if (!exists(p)) return { ok: false, path: p, base: '' };
  try {
    const j = JSON.parse(fs.readFileSync(p, 'utf8'));
    const base = String(j.base || '');
    return { ok: isHttp(base) && !isLoopback(base) && !!j.channelId, path: p, base, channelId: String(j.channelId || '') };
  } catch {
    return { ok: false, path: p, base: '' };
  }
}

function fmt(ms) {
  if (!ms) return '（无）';
  try {
    return new Date(ms).toISOString().replace('T', ' ').slice(0, 19) + 'Z';
  } catch {
    return String(ms);
  }
}

/**
 * 主入口。所有参数可注入（便于测试与护栏断言），默认读真实环境。
 * @returns {{mode:'hook'|'self'|'unknown', confidence:'high'|'medium'|'low',
 *            reason:string, evidence:string[], failing:boolean,
 *            lastTurnEventAt:string, lastTurnEvent:string,
 *            receiving:{ok:boolean, base:string, channelId?:string},
 *            logPath:string, hookRegistration:string[]}}
 */
function probeTurnCoverage(opts) {
  const o = opts || {};
  const now = typeof o.now === 'number' ? o.now : Date.now();
  const logPath = o.logPath || hookLogPath();
  try {
    const log = o.log || parseHookLog(logPath);
    const registration = o.hookRegistration || detectHookRegistration();
    const receiving = o.receiving || detectReceiving();
    const evidence = [];

    const fresh = log.lastTurnEventAt && now - log.lastTurnEventAt <= FRESH_MS;
    const okFresh = log.lastOkAt && now - log.lastOkAt <= FRESH_MS;
    if (log.exists) {
      evidence.push(
        log.lastTurnEventAt
          ? 'hook 日志最后一次轮次事件 = ' + log.lastTurnEvent + ' @ ' + fmt(log.lastTurnEventAt)
          : 'hook 日志存在但未见轮次事件',
      );
      if (log.lastOkAt) evidence.push('hook 最后一次推送成功 @ ' + fmt(log.lastOkAt));
      if (log.lastFailAt) evidence.push('hook 最后一次推送失败 @ ' + fmt(log.lastFailAt));
    } else {
      evidence.push('未找到 hook 日志（' + (logPath || '路径不可用') + '）');
    }
    if (registration.length) evidence.push('检测到 hook 注册：' + registration.join('；'));
    else evidence.push('未检测到任何 hook 注册痕迹');
    evidence.push(
      receiving.ok
        ? '接收端可用：' + receiving.base + ' / ' + (receiving.channelId || '?')
        : '未找到本 AI 的接收端文件（' + (receiving.path || '路径不可用') + '）—— 这不代表推不出去：' +
          '若 mcp.json 的 env 里已配 WARROOM_API_BASE / WARROOM_WEBHOOK_KEY，hook 与 MCP 会走那份基线；' +
          '两者都没有时才需要先 setup。',
    );

    // 「hook 推的工位」与「接收端记的工位」不一致 —— 记录为**事实**，但**不据此报警**。
    // 原因（2026-10-23 用户纠正）：`~/.warroom/receiving-endpoint.json` 是**全机器唯一**的一份，
    // 同机上每个 AI 都往同一路径写。实测本机：文件里是 qclaw（另一套 AI 软件 QClaw 写进去的），
    // 而 WorkBuddy 的 hook 推 ch-workbuddy —— 两者**各自正确**，不是故障。
    // 早先版本把这种不一致判成「hook 推错目标」，属误报。真正该修的是「状态文件没有按 AI 隔离」。
    const targetDiffers = [];
    if (log.lastPushChannel && receiving.ok && receiving.channelId && log.lastPushChannel !== receiving.channelId) {
      targetDiffers.push('hook 推的工位是「' + log.lastPushChannel + '」，接收端文件记的是「' + receiving.channelId + '」');
    }
    if (log.lastPushBase && receiving.ok && receiving.base) {
      const a = log.lastPushBase.replace(/\/+$/, '').toLowerCase();
      const b = receiving.base.replace(/\/+$/, '').toLowerCase();
      if (a !== b) targetDiffers.push('hook 推的基址是「' + log.lastPushBase + '」，接收端文件记的是「' + receiving.base + '」');
    }
    if (targetDiffers.length) {
      evidence.push(
        'ℹ️ 目标不同：' + targetDiffers.join('；') +
          '（接收端文件全机共享，同机多 AI 时这通常是各自工位不同，**不算故障**；仅当确认这两者本应相同时才需排查）',
      );
    }

    let mode;
    let confidence;
    let reason;
    let failing = false;

    if (fresh) {
      mode = 'hook';
      const lastFailAfterOk = log.lastFailAt > log.lastOkAt;
      if (okFresh && !lastFailAfterOk) {
        confidence = 'high';
        reason =
          '宿主 hook 在跑且推送成功（' +
          fmt(log.lastTurnEventAt) +
          ' 的 ' +
          log.lastTurnEvent +
          '）。轮次事件已自动上屏 —— 你**不要**调 notify_turn_start / notify_turn_end，否则同一轮会重复两条。';
      } else {
        confidence = 'medium';
        failing = true;
        reason =
          '宿主 hook 在跑（' +
          fmt(log.lastTurnEventAt) +
          ' 的 ' +
          log.lastTurnEvent +
          '），但推送失败（最近失败 @ ' +
          fmt(log.lastFailAt) +
          '）。**不要**改由你补推 —— 你走的是同一个接收端，一样推不出去；请让用户按 SKILL §7.1.1 的四步排查修好它。';
      }
      if (targetDiffers.length) {
        reason +=
          '（补充事实：' + targetDiffers.join('；') +
          '。`~/.warroom/receiving-endpoint.json` 是**全机唯一**的一份，同机装多个 AI 时各自工位不同属正常，' +
          '别据此断定 hook 坏了；只有确认「这两者本应相同」时才需要排查。）';
      }
    } else if (registration.length || receiving.ok) {
      mode = 'unknown';
      confidence = 'low';
      reason =
        '检测到 hook 注册/接收端，但近 24 小时没有任何 hook 事件 —— 它可能刚装还没跑过、日志被清、或注册路径已失效。' +
        '**默认不要**调轮次工具（会与 hook 重复上屏）。先用一句话问用户：「大屏上能看到『🙋 收到指令』吗？」' +
        '看不到 → 本轮起你自己每轮调 notify_turn_start / notify_turn_end 补齐，并建议用户排查 hook。';
    } else {
      mode = 'self';
      confidence = 'high';
      reason =
        '本机没有任何 hook 痕迹（无注册、无日志、无接收端以外的配置）→ 轮次事件没有任何自动来源。' +
        '**你必须**每轮自己推：收到用户消息后立刻 notify_turn_start，本轮回答结束前 notify_turn_end（成对，含普通对话）。';
    }

    return {
      mode,
      confidence,
      reason,
      failing,
      targetDiffers: targetDiffers.length > 0,
      evidence,
      lastTurnEventAt: log.lastTurnEventAt ? new Date(log.lastTurnEventAt).toISOString() : '',
      lastTurnEvent: log.lastTurnEvent,
      lastPushChannel: log.lastPushChannel || '',
      lastPushBase: log.lastPushBase || '',
      receiving: { ok: !!receiving.ok, base: receiving.base || '', channelId: receiving.channelId || '' },
      logPath,
      hookRegistration: registration,
    };
  } catch (e) {
    // 探测失败绝不能拖累 MCP 启动 / 工具调用
    return {
      mode: 'unknown',
      confidence: 'low',
      reason:
        '轮次覆盖探测失败（' + (e && e.message ? e.message : String(e)) + '）→ 无法判断 hook 是否在跑。' +
        '默认不要调轮次工具；先问用户大屏上有没有「🙋 收到指令」，看不到再由你补。',
      failing: false,
      targetDiffers: false,
      evidence: [],
      lastTurnEventAt: '',
      lastTurnEvent: '',
      receiving: { ok: false, base: '' },
      logPath: hookLogPath(),
      hookRegistration: [],
    };
  }
}

/** 给 instructions / 工具返回值用的一行摘要（不含「你该怎么做」，只有事实）。 */
function summarize(cov) {
  if (!cov) return '（未探测）';
  const bits = ['mode=' + cov.mode];
  if (cov.lastTurnEventAt) bits.push('last=' + cov.lastTurnEvent + '@' + cov.lastTurnEventAt);
  if (cov.failing) bits.push('push=failing');
  if (cov.targetDiffers) bits.push('target=differs(' + (cov.lastPushChannel || '?') + '≠' + ((cov.receiving && cov.receiving.channelId) || '?') + ')');
  bits.push('receiving=' + (cov.receiving && cov.receiving.ok ? 'ok' : 'missing'));
  return bits.join(' · ');
}

module.exports = {
  probeTurnCoverage,
  summarize,
  // 导出内部件便于单元/护栏断言，不对外承诺稳定性
  _internal: { parseHookLog, detectHookRegistration, detectReceiving, hookLogPath, FRESH_MS },
};
