#!/usr/bin/env node
// check-script.mjs — **机器实测讲稿字数 vs 时长预算**,不信模型自报(弱模型数不准自己的字数)。
// 读 JOBDIR 下所有 `NN.txt`,按中文口播 ~250 字/分钟折算时长,和目标分钟比,超了就点名最长的页。
// 用在:写完稿、进人审/配音之前。超预算 → agent 去砍最长的几页,再跑一次,达标再往下。
//
// 用法:
//   node check-script.mjs <JOBDIR> --minutes 8        # 目标时长(分钟)
//   node check-script.mjs <JOBDIR> --budget 2000      # 或直接给字数预算(优先于 --minutes)
//   → JSON: {pages, filled, blank, totalChars, estMinutes, budgetChars, over, overBy, avgPerPage, longest:[...]}
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const CHARS_PER_MIN = 250;   // 中文口播近似语速(和 render 无关,仅估时长/定预算)

// 只数"能读出来的字":去空白;不计标点也行,但简单起见按去空白后的长度算,和语速经验值匹配。
const countChars = (s) => s.replace(/\s+/g, "").length;

export function checkScript(dir, { minutes, budget } = {}) {
  const budgetChars = budget != null ? budget
    : (minutes != null ? Math.round(minutes * CHARS_PER_MIN) : null);
  const pages = readdirSync(dir)
    .map((f) => { const m = f.match(/^(\d+)\.txt$/); return m ? m[1] : null; })
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

  const per = pages.map((nn) => {
    const p = join(dir, `${nn}.txt`);
    const chars = existsSync(p) ? countChars(readFileSync(p, "utf8")) : 0;
    return { nn, chars };
  });
  const totalChars = per.reduce((a, x) => a + x.chars, 0);
  const filled = per.filter((x) => x.chars > 0).length;
  const blank = per.filter((x) => x.chars === 0).map((x) => x.nn);
  const estMinutes = Math.round((totalChars / CHARS_PER_MIN) * 10) / 10;
  const longest = [...per].sort((a, b) => b.chars - a.chars).slice(0, 6);

  const out = {
    pages: pages.length, filled, blankPages: blank,
    totalChars, estMinutes,
    avgPerPage: pages.length ? Math.round(totalChars / pages.length) : 0,
    longest,
  };
  if (budgetChars != null) {
    out.budgetChars = budgetChars;
    out.over = totalChars > budgetChars;
    out.overBy = Math.max(0, totalChars - budgetChars);
    out.hint = out.over
      ? `超预算 ${out.overBy} 字(约 ${Math.round(out.overBy / CHARS_PER_MIN * 10) / 10} 分钟)。优先砍上面 longest 里最长的页,砍到 ≤ ${budgetChars} 字再进人审/配音。`
      : `在预算内(${totalChars}/${budgetChars})。`;
  }
  return out;
}

// CLI
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) {
  const args = process.argv.slice(2);
  const get = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const dir = args.find((a) => !a.startsWith("--") && a !== get("--minutes") && a !== get("--budget"));
  if (!dir) { console.error("Usage: node check-script.mjs <JOBDIR> [--minutes 8 | --budget 2000]"); process.exit(1); }
  const minutes = get("--minutes") != null ? parseFloat(get("--minutes")) : undefined;
  const budget = get("--budget") != null ? parseInt(get("--budget"), 10) : undefined;
  const r = checkScript(dir, { minutes, budget });
  process.stdout.write(JSON.stringify(r, null, 2));
  // 超预算用退出码 4 提示 agent(不影响拿 JSON);没给预算就只报告不判定。
  process.exit(r.over ? 4 : 0);
}
