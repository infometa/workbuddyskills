#!/usr/bin/env node
/**
 * TeachAny 课件完整性校验器 v1.0
 * 
 * 自动化 Completeness Gate 的 18 项审查清单。
 * 运行方式：
 *   node scripts/validate-courseware.cjs ./examples/math-linear-function
 *   node scripts/validate-courseware.cjs ./examples/math-linear-function --fix-hints
 * 
 * 返回值：
 *   0 = 全部通过
 *   1 = 有未通过项
 *   2 = 致命错误（文件不存在等）
 */

const fs = require('fs');
const path = require('path');

// ─── 颜色输出 ───
const C = {
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
  cyan: (s) => `\x1b[36m${s}\x1b[0m`,
  bold: (s) => `\x1b[1m${s}\x1b[0m`,
  dim: (s) => `\x1b[2m${s}\x1b[0m`,
};

function shouldSkipAssetRef(ref) {
  if (!ref) return true;
  const trimmed = ref.trim();
  if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('{{')) return true;
  return /^(https?:|data:|blob:|mailto:|tel:|javascript:|about:|chrome:|edge:)/i.test(trimmed);
}

function resolveLocalRef(dir, ref) {
  const repoRoot = path.resolve(__dirname, '..');
  let clean;
  try {
    clean = decodeURIComponent(ref.split('#')[0].split('?')[0]);
  } catch (e) {
    clean = ref.split('#')[0].split('?')[0];
  }
  if (!clean) return null;
  return clean.startsWith('/') ? path.resolve(repoRoot, clean.slice(1)) : path.resolve(dir, clean);
}

function findMissingLocalAssets(dir, html) {
  const repoRoot = path.resolve(__dirname, '..');
  const re = /(?:\b(?:src|href|poster)\s*=\s*['"]([^'"]+)['"]|url\(\s*['"]?([^'")]+)['"]?\s*\))/gi;
  const missing = [];
  const seen = new Set();
  let m;
  while ((m = re.exec(html)) !== null) {
    const raw = (m[1] || m[2] || '').trim();
    if (shouldSkipAssetRef(raw)) continue;
    let clean;
    try {
      clean = decodeURIComponent(raw.split('#')[0].split('?')[0]);
    } catch (e) {
      clean = raw.split('#')[0].split('?')[0];
    }
    if (!clean || clean.startsWith('#')) continue;
    const target = resolveLocalRef(dir, clean);
    const key = `${raw}\u0000${target}`;
    if (seen.has(key)) continue;
    seen.add(key);
    if (!fs.existsSync(target)) {
      missing.push(`${raw} → ${path.relative(repoRoot, target) || target}`);
    }
  }
  return missing;
}

// ─── 校验项定义 ───
const CHECKS = [
  {
    id: 1,
    name: 'ABT + 情境引入',
    desc: '每个核心模块都有"为什么学"的叙事引入+情境角色',
    check: (html) => {
      // 检查 ABT 关键词：And/But/Therefore 结构或中文等价
      const hasABT = /为什么.*学|已经知道|但.*问题|所以.*学|Therefore|已经会|现有知识/i.test(html);
      const hasScenario = /情境|角色|场景|任务|侦探|工程师|规划师|设计师|研究员|探险|冒险|餐厅|博物馆/i.test(html);
      return {
        pass: hasABT,
        detail: hasABT
          ? (hasScenario ? 'ABT 引入 ✅ + 情境角色 ✅' : 'ABT 引入 ✅，但未检测到明确的情境角色设计')
          : '未找到 ABT 叙事引入（缺少"为什么学"模块）',
        fix: '在每个核心模块前添加"为什么要学这个？"卡片，包含 And（已知）→ But（问题）→ Therefore（新知）结构',
      };
    },
  },
  {
    id: 2,
    name: '前测存在',
    desc: '是否有前置知识检测题',
    check: (html) => {
      const hasPretest = /前测|pre-?test|你已经知道什么|前置.*检测|先来测一测/i.test(html);
      const hasPretestId = /id=["']pretest/i.test(html);
      return {
        pass: hasPretest || hasPretestId,
        detail: (hasPretest || hasPretestId) ? '前测模块已找到' : '未找到前测模块',
        fix: '添加"前测：你已经知道什么？"section，至少包含 2 道前置知识检测题',
      };
    },
  },
  {
    id: 3,
    name: '互动练习',
    desc: '每个核心知识点至少配 1 道互动练习',
    check: (html) => {
      // 统计选择题/交互题的数量
      const quizOptions = (html.match(/quiz-option|quiz-opt|handleQuiz|data-conceptest|checkAnswer|onclick.*check|选择题|练习题|马上练/gi) || []).length;
      const interactiveElements = (html.match(/draggable|ondrop|slider|range|input.*type/gi) || []).length;
      const total = quizOptions + interactiveElements;
      return {
        pass: total >= 3,
        detail: `检测到约 ${Math.ceil(total / 3)} 组互动练习（${quizOptions} 个选项元素，${interactiveElements} 个交互控件）`,
        fix: '每个核心知识模块后添加"✏️ 马上练一题"卡片，包含带错因诊断的选择题或拖拽题',
      };
    },
  },
  {
    id: 4,
    name: '诊断性反馈',
    desc: '练习反馈不只"正确/错误"，需有错因诊断',
    check: (html) => {
      // 检查是否有具体的错误分析
      const hasDiagnosis = /错.*因|为什么错|你.*搞反|你.*搞混|你.*忘记|你.*混淆|常见错误|注意区分|不要.*混|diagnosis|错在|再想想/i.test(html);
      const genericOnly = /正确|错误|对了|Wrong|Correct/i.test(html) && !hasDiagnosis;
      return {
        pass: hasDiagnosis,
        detail: hasDiagnosis ? '检测到诊断性反馈内容' : '仅有"正确/错误"通用反馈，缺少具体错因分析',
        fix: '每道练习的错误选项需附带具体错因诊断，如"你把 k 的正负与 b 的正负搞混了"',
      };
    },
  },
  {
    id: 5,
    name: '后测与学习闭环',
    desc: '是否有后测，前测后测形成闭环',
    check: (html) => {
      const hasPosttest = /后测|post-?test|学会了吗|学完.*检验|总结.*测试/i.test(html);
      const hasPosttestId = /id=["']posttest/i.test(html);
      return {
        pass: hasPosttest || hasPosttestId,
        detail: (hasPosttest || hasPosttestId) ? '后测模块已找到' : '未找到后测模块',
        fix: '添加"后测：学会了吗？"section，题目应与前测对照，检验学习效果',
      };
    },
  },
  {
    id: 6,
    name: 'Bloom 层级覆盖',
    desc: '练习至少覆盖 Bloom 3 个层级',
    check: (html) => {
      const levels = {
        remember: /识别|列举|说出|写出|选出哪个是|下面哪个/i.test(html),
        understand: /解释|比较|描述|为什么|区别|含义/i.test(html),
        apply: /计算|求解|运用|求.*值|代入|画出/i.test(html),
        analyze: /推导|区分|归纳|分析.*原因|判断.*为什么/i.test(html),
        evaluate: /判断.*是否正确|验证|评估|评价|哪个更/i.test(html),
        create: /设计|构建|提出|编写一个|创造|方案/i.test(html),
      };
      const covered = Object.entries(levels).filter(([, v]) => v).map(([k]) => k);
      return {
        pass: covered.length >= 3,
        detail: `Bloom 覆盖 ${covered.length}/6 层：${covered.join(', ') || '无'}`,
        fix: '确保练习覆盖至少 3 个 Bloom 层级。当前缺少的层级应补充对应题型。',
      };
    },
  },
  {
    id: 7,
    name: '知识图谱溯源',
    desc: '核心内容可追溯到知识图谱/Web搜索',
    check: (html) => {
      // 检查 meta 标签和知识图谱引用标记
      const hasNodeMeta = /teachany-node/i.test(html);
      const hasSubjectMeta = /teachany-subject/i.test(html);
      const hasDomainMeta = /teachany-domain/i.test(html);
      const hasGraphRef = /knowledge.?layer|知识图谱|_graph\.json|data-source/i.test(html);
      // 检查定义是否规范（有"形如""叫做"等教材式表述）
      const hasFormalDef = /形如|叫做|定义为|是指|称为/i.test(html);
      return {
        pass: hasNodeMeta && hasSubjectMeta,
        detail: [
          hasNodeMeta ? 'teachany-node ✅' : 'teachany-node ❌',
          hasSubjectMeta ? 'teachany-subject ✅' : 'teachany-subject ❌',
          hasDomainMeta ? 'teachany-domain ✅' : 'teachany-domain ❌',
          hasFormalDef ? '规范定义 ✅' : '规范定义 ⚠️',
        ].join(' | '),
        fix: '确保 <head> 中包含 teachany-node, teachany-subject, teachany-domain 等 meta 标签，且核心定义来自知识图谱',
      };
    },
  },
  {
    id: 8,
    name: '五镜头深层理解',
    desc: '是否有深层理解模块（五镜头法）',
    check: (html) => {
      const hasDeep = /深层理解|five.?lens|五镜头|看见它|拆开它|解释它|比较它|迁移它|insight/i.test(html);
      const hasInsightBox = /insight-box|深层|深入理解|本质|背后的原理/i.test(html);
      return {
        pass: hasDeep || hasInsightBox,
        detail: (hasDeep || hasInsightBox) ? '深层理解模块已找到' : '未找到深层理解/五镜头模块',
        fix: '在核心讲解后添加"🔍 深层理解"insight-box，选择 2-3 个镜头：看见它/拆开它/解释它/比较它/迁移它',
      };
    },
  },
  {
    id: 9,
    name: '卡片文字密度',
    desc: '核心卡片文字不超过 ~100 字（75字标准，留余量）',
    check: (html) => {
      // 提取 card 内的文本内容，检查是否有超长卡片
      const cardMatches = html.match(/<div[^>]*class="[^"]*card[^"]*"[^>]*>([\s\S]*?)<\/div>/gi) || [];
      let longCards = 0;
      let maxLen = 0;
      cardMatches.forEach(card => {
        const text = card.replace(/<[^>]+>/g, '').replace(/\s+/g, '');
        if (text.length > maxLen) maxLen = text.length;
        if (text.length > 200) longCards++; // 200字作为单卡片上限
      });
      return {
        pass: longCards === 0,
        detail: `${cardMatches.length} 张卡片，最长 ${maxLen} 字${longCards > 0 ? `，${longCards} 张超长` : ''}`,
        fix: '超长卡片需拆分为多张，每张核心文字控制在 75 字左右',
      };
    },
  },
  {
    id: 10,
    name: '三段式作业分层',
    desc: '综合练习有 ⭐/⭐⭐/⭐⭐⭐ 分层设计',
    check: (html) => {
      const hasLevel = /Level\s*[123]|基础巩固|能力应用|迁移挑战|⭐|★|分层|必做|选做/i.test(html);
      return {
        pass: hasLevel,
        detail: hasLevel ? '检测到分层练习设计' : '未找到三段式分层练习',
        fix: '综合练习区需包含三级：Level 1 基础巩固（⭐）、Level 2 能力应用（⭐⭐）、Level 3 迁移挑战（⭐⭐⭐）',
      };
    },
  },
  {
    id: 11,
    name: '前置知识链',
    desc: 'meta 标签中是否声明了 prerequisites',
    check: (html) => {
      const hasPre = /teachany-prerequisites/i.test(html);
      const hasPreContent = /content=["'][^"']+["']/.test(
        (html.match(/<meta[^>]*teachany-prerequisites[^>]*>/i) || [''])[0]
      );
      return {
        pass: hasPre,
        detail: hasPre
          ? (hasPreContent ? '前置知识已声明' : '前置知识标签存在但内容为空')
          : '未找到 teachany-prerequisites meta 标签',
        fix: '在 <head> 中添加 <meta name="teachany-prerequisites" content="前置知识节点ID">',
      };
    },
  },
  {
    id: 12,
    name: '真实场景应用',
    desc: '课件中是否有真实生活场景（来自 real_world）',
    check: (html) => {
      const hasScene = /生活|真实|实际|场景|例如.*日常|手机.*话费|出租车|弹簧|温度|购物|旅行|工程|实验/i.test(html);
      return {
        pass: hasScene,
        detail: hasScene ? '检测到真实场景应用' : '未找到真实生活场景',
        fix: '使用知识图谱 _graph.json 的 real_world 字段，在 ABT 引入和应用模块中融入真实场景',
      };
    },
  },
  {
    id: 13,
    name: 'Meta 标签完整性',
    desc: '必需的 teachany-* meta 标签是否齐全',
    check: (html) => {
      const required = ['teachany-node', 'teachany-subject', 'teachany-grade', 'teachany-version'];
      const recommended = ['teachany-domain', 'teachany-prerequisites', 'teachany-difficulty', 'teachany-author'];
      const missing = required.filter(m => !new RegExp(`name=["']${m}["']`, 'i').test(html));
      const missingRec = recommended.filter(m => !new RegExp(`name=["']${m}["']`, 'i').test(html));
      return {
        pass: missing.length === 0,
        detail: missing.length === 0
          ? `必需标签全部齐全${missingRec.length > 0 ? `，推荐标签缺 ${missingRec.length} 个: ${missingRec.join(', ')}` : '，推荐标签也齐全'}`
          : `缺少必需 meta 标签: ${missing.join(', ')}`,
        fix: `在 <head> 中添加缺失的 meta 标签：${missing.concat(missingRec).map(m => `<meta name="${m}" content="...">`).join(', ')}`,
      };
    },
  },
  {
    id: 14,
    name: 'AI 多模态互动区',
    desc: '文科/视觉化课题是否包含 AI 互动区',
    check: (html, meta) => {
      const subject = meta.subject || '';
      const isHumanity = /chinese|history|english|geography/i.test(subject);
      const hasAIZone = /ai.?media|ai.?zone|ai.*互动|多模态|生成.*图|upload.*image/i.test(html);
      if (!isHumanity) {
        return { pass: true, detail: 'N/A（非文科课题，可跳过）', fix: '' };
      }
      return {
        pass: hasAIZone,
        detail: hasAIZone ? 'AI 多模态互动区已找到' : '文科课题但未找到 AI 多模态互动区',
        fix: '文科课题默认需要插入 AI 多模态互动区，包含提示词输入框和生成/上传按钮',
      };
    },
  },
  {
    id: 15,
    name: '双语版本',
    desc: '仅用户明确要求双语时才需要 index_en.html',
    check: (html, meta, dir) => {
      const hasEn = fs.existsSync(path.join(dir, 'index_en.html'));
      const wantsBilingual = /output_formats[\s\S]*index_en|双语|英文版|bilingual/i.test(html);
      return {
        pass: !wantsBilingual || hasEn,
        detail: hasEn ? '英文版 index_en.html 存在' : '未声明双语需求，中文单版本通过',
        fix: '只有用户要求双语/英文版时才生成 index_en.html；默认中文课件不强制双语',
      };
    },
  },
  {
    id: 16,
    name: '课件打包',
    desc: '是否有 manifest.json',
    check: (html, meta, dir) => {
      const hasManifest = fs.existsSync(path.join(dir, 'manifest.json'));
      const hasTeachany = fs.readdirSync(dir).some(f => f.endsWith('.teachany'));
      return {
        pass: hasManifest,
        detail: [
          hasManifest ? 'manifest.json ✅' : 'manifest.json ❌',
          hasTeachany ? '.teachany 包 ✅' : '.teachany 包 ❌',
        ].join(' | '),
        fix: '运行 node scripts/pack-courseware.cjs 生成 manifest.json 并打包',
      };
    },
  },
  {
    id: 17,
    name: '记忆锚点',
    desc: '是否有记忆辅助（口诀/类比/总结）',
    check: (html) => {
      const hasAnchor = /口诀|记忆|类比|就像|想象成|比喻|助记|锚点|窍门|秘诀|总结.*规律/i.test(html);
      return {
        pass: hasAnchor,
        detail: hasAnchor ? '检测到记忆锚点/类比' : '未找到记忆辅助内容',
        fix: '使用知识图谱 _graph.json 的 memory_anchors 字段，添加类比或口诀帮助学生记忆',
      };
    },
  },
  {
    id: 18,
    name: '易错点覆盖',
    desc: '练习中是否融入了知识图谱的高频易错点',
    check: (html) => {
      // 检查是否有错误追踪相关内容
      const hasError = /常见错误|容易.*错|搞反|搞混|混淆|误认为|错误.*类型|注意.*陷阱|易错/i.test(html);
      return {
        pass: hasError,
        detail: hasError ? '检测到易错点融入' : '未找到知识图谱易错点的融入',
        fix: '参考 _errors.json 中 frequency=high 的易错点，将其作为练习题的干扰项和错因诊断内容',
      };
    },
  },
  {
    id: 19,
    name: '本地资源无 404',
    desc: 'HTML 中所有本地 src/href/poster/url(...) 引用都必须指向真实文件',
    check: (html, meta, dir) => {
      const missing = findMissingLocalAssets(dir, html);
      return {
        pass: missing.length === 0,
        detail: missing.length === 0
          ? '未发现本地资源死链'
          : `发现 ${missing.length} 个本地资源死链：${missing.slice(0, 5).join('；')}${missing.length > 5 ? '；...' : ''}`,
        fix: '使用 image_gen/复制文件后的真实落盘文件名写入 HTML；交付前运行 validate-courseware，禁止凭 prompt 猜文件名',
      };
    },
  },
  {
    id: 20,
    name: '连续音频质量',
    desc: '至少三段真实 mp3，并挂载标准连续音频播放器',
    check: (html, meta, dir) => {
      const refs = [...html.matchAll(/["']([^"']+\.mp3)["']/gi)].map(m => m[1]).filter(r => !shouldSkipAssetRef(r));
      const valid = refs.filter(ref => {
        const target = resolveLocalRef(dir, ref);
        return target && fs.existsSync(target) && fs.statSync(target).size >= 20 * 1024;
      });
      const hasPlayer = /data-teachany-audio-playlist|teachany-audio-player\.js|audioPlaylist/i.test(html);
      return {
        pass: valid.length >= 3 && hasPlayer,
        detail: `有效 mp3 ${valid.length}/${refs.length}；${hasPlayer ? '播放器 ✅' : '播放器 ❌'}`,
        fix: '生成至少 3 段非占位 mp3，并使用 data-teachany-audio-playlist + teachany-audio-player.js 渲染连续播放 UI',
      };
    },
  },
  {
    id: 21,
    name: '视频模块可见可控',
    desc: '已有 mp4 必须嵌入 video 标签，且有 controls 与真实文件',
    check: (html, meta, dir) => {
      const refs = [...html.matchAll(/<(?:video|source)[^>]+src=["']([^"']+\.mp4)["']/gi)].map(m => m[1]);
      const valid = refs.filter(ref => {
        const target = resolveLocalRef(dir, ref);
        return target && fs.existsSync(target) && fs.statSync(target).size >= 20 * 1024;
      });
      const videoTags = [...html.matchAll(/<video\b[^>]*>/gi)].map(m => m[0]);
      const controlsOk = videoTags.length > 0 && videoTags.every(v => /controls/i.test(v) && /playsinline/i.test(v));
      return {
        pass: valid.length >= 1 && controlsOk,
        detail: `有效 mp4 ${valid.length}/${refs.length}；video controls/playsinline ${controlsOk ? '✅' : '❌'}`,
        fix: '把 Remotion/教学 mp4 用 <video controls preload="metadata" playsinline><source ...> 嵌入对应知识模块',
      };
    },
  },
  {
    id: 22,
    name: 'Canvas 真实互动',
    desc: 'Canvas 不得只是空白或静态图，必须有绘制逻辑、事件和学生控件',
    check: (html) => {
      const hasCanvas = /<canvas\b/i.test(html);
      const hasDraw = /getContext\s*\(|draw\w*\s*\(/i.test(html);
      const hasEvent = /addEventListener\s*\(\s*["'](?:pointer|mouse|touch|click|input|change)/i.test(html);
      const hasControl = /<(?:input|select|button)\b/i.test(html);
      return {
        pass: hasCanvas && hasDraw && hasEvent && hasControl,
        detail: [hasCanvas ? 'canvas ✅' : 'canvas ❌', hasDraw ? '绘制逻辑 ✅' : '绘制逻辑 ❌', hasEvent ? '事件 ✅' : '事件 ❌', hasControl ? '控件 ✅' : '控件 ❌'].join(' | '),
        fix: '补充 getContext/draw、pointer/click/input/change 事件，以及学生可操作的按钮/滑块/选择器',
      };
    },
  },
  {
    id: 23,
    name: '无占位图片',
    desc: 'assets/ 下不得存在 <5KB 的占位 webp/png（纯色块或极低质量图）',
    check: (html, meta, dir) => {
      const assetsDir = path.join(dir, 'assets');
      if (!fs.existsSync(assetsDir)) return { pass: true, detail: 'assets/ 不存在，跳过', fix: '' };
      const files = fs.readdirSync(assetsDir).filter(f => /\.(webp|png|jpg|jpeg)$/i.test(f));
      const placeholders = files.filter(f => {
        const stat = fs.statSync(path.join(assetsDir, f));
        // hero-infographic.svg 通常较小但合法，这里只检测 webp/png/jpg
        return stat.size < 5 * 1024; // <5KB 视为占位
      });
      // 排除明确的图标类小图（如 favicon）
      const suspicious = placeholders.filter(f => !/favicon|icon|logo/i.test(f));
      return {
        pass: suspicious.length === 0,
        detail: suspicious.length === 0
          ? `${files.length} 张图片，无占位文件`
          : `发现 ${suspicious.length} 张疑似占位图（<5KB）: ${suspicious.slice(0, 5).join(', ')}`,
        fix: '删除 <5KB 的占位图片，使用 gen-hero-svg.py 或 image_gen 生成真实内容图片。如果不需要这些图片，从 HTML 中也删除对应 <img> 标签。',
      };
    },
  },
  {
    id: 24,
    name: 'Hero 后无裸 img 堆叠',
    desc: 'hero/header 区块与正文 section 之间不得有独立的裸 <img> 标签堆叠',
    check: (html) => {
      // 检测 </header> 之后、第一个 <section 或 <div class="tutor 之前是否有连续裸 img
      const afterHero = html.split(/<\/header>/i)[1] || '';
      const beforeContent = afterHero.split(/<(?:section|div\s+class=["'][^"']*tutor)/i)[0] || '';
      // 计算裸 img 标签数量（不在 section/figure/div 内部的顶级 img）
      const nakedImgs = (beforeContent.match(/<img\s[^>]*>/gi) || []).filter(img => {
        // 排除 onerror="this.style.display='none'" 的 logo 类图片
        return !/onerror.*display.*none/i.test(img);
      });
      return {
        pass: nakedImgs.length === 0,
        detail: nakedImgs.length === 0
          ? 'hero 后无裸 img 堆叠'
          : `hero 后发现 ${nakedImgs.length} 个裸 <img> 标签堆叠（会显示为空白区块）`,
        fix: '删除 hero/header 与第一个 section 之间的独立 <img> 标签。概念图/示意图应嵌入对应教学 section 内部，或使用 <figure> 包裹并添加 figcaption。',
      };
    },
  },
];

// ─── 主函数 ───
function main() {
  const args = process.argv.slice(2);
  const showFix = args.includes('--fix-hints');
  const dirArg = args.find(a => !a.startsWith('--'));

  if (!dirArg) {
    console.log(C.bold('\n📋 TeachAny 课件完整性校验器 v1.0\n'));
    console.log('用法：node scripts/validate-courseware.cjs <课件目录> [--fix-hints]');
    console.log('\n示例：');
    console.log('  node scripts/validate-courseware.cjs ./examples/math-linear-function');
    console.log('  node scripts/validate-courseware.cjs ./examples/math-linear-function --fix-hints');
    console.log('\n选项：');
    console.log('  --fix-hints    显示每个未通过项的修复建议');
    process.exit(2);
  }

  const dir = path.resolve(dirArg);
  const indexPath = path.join(dir, 'index.html');

  if (!fs.existsSync(indexPath)) {
    console.error(C.red(`\n❌ 致命错误：找不到 ${indexPath}`));
    console.error('请确认课件目录路径正确，且包含 index.html 文件。');
    process.exit(2);
  }

  const html = fs.readFileSync(indexPath, 'utf8');

  // 从 meta 标签提取元信息
  const meta = {};
  const metaRegex = /<meta\s+name=["']teachany-(\w+)["']\s+content=["']([^"']*)["']/gi;
  let m;
  while ((m = metaRegex.exec(html)) !== null) {
    meta[m[1]] = m[2];
  }

  console.log(C.bold('\n═══════════════════════════════════════════'));
  console.log(C.bold('🔍 COMPLETENESS GATE — 自动化校验报告'));
  console.log(C.bold('═══════════════════════════════════════════'));
  console.log(C.dim(`📁 ${dir}`));
  console.log(C.dim(`📄 ${indexPath}`));
  if (Object.keys(meta).length > 0) {
    console.log(C.dim(`🏷️  ${Object.entries(meta).map(([k, v]) => `${k}=${v}`).join(' | ')}`));
  }
  console.log('');

  let passed = 0;
  let failed = 0;
  const failedItems = [];

  for (const check of CHECKS) {
    const result = check.check(html, meta, dir);
    const icon = result.pass ? C.green('✅') : C.red('❌');
    const status = result.pass ? C.green('PASS') : C.red('FAIL');

    console.log(`${icon} #${String(check.id).padStart(2, '0')} ${check.name} — ${status}`);
    console.log(C.dim(`     ${result.detail}`));

    if (!result.pass && showFix && result.fix) {
      console.log(C.yellow(`     💡 修复：${result.fix}`));
    }
    console.log('');

    if (result.pass) {
      passed++;
    } else {
      failed++;
      failedItems.push({ id: check.id, name: check.name, fix: result.fix });
    }
  }

  console.log(C.bold('═══════════════════════════════════════════'));
  console.log(C.bold(`📊 总评：${passed}/${CHECKS.length} 通过`));

  if (failed > 0) {
    console.log(C.red(`\n⚠️  ${failed} 项未通过：`));
    failedItems.forEach(item => {
      console.log(C.red(`   #${item.id} ${item.name}`));
    });
    if (!showFix) {
      console.log(C.yellow('\n💡 提示：添加 --fix-hints 参数查看修复建议'));
    }
  } else {
    console.log(C.green('\n🎉 恭喜！课件通过全部完整性检查！'));
  }

  console.log(C.bold('═══════════════════════════════════════════\n'));

  // 输出 JSON 格式结果（方便程序读取）
  if (args.includes('--json')) {
    const report = {
      dir,
      meta,
      total: CHECKS.length,
      passed,
      failed,
      results: CHECKS.map(check => {
        const result = check.check(html, meta, dir);
        return {
          id: check.id,
          name: check.name,
          pass: result.pass,
          detail: result.detail,
          fix: result.fix,
        };
      }),
    };
    console.log(JSON.stringify(report, null, 2));
  }

  process.exit(failed > 0 ? 1 : 0);
}

main();
