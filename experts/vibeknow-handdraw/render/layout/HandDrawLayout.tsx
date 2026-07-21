import React, { useEffect, useState } from "react";
import { AbsoluteFill, Img, continueRender, delayRender, interpolate } from "remotion";
import type { LayoutProps } from "./types";
import { cumulative, revealState, type SvgData } from "./pacing";

// 一个 svgDataUrl 指向的合并文件：{coarse, full} 两层路径数据（worker 传 TOS 的单文件）。
type CombinedSvg = { coarse: SvgData; full: SvgData };

const cache: Record<string, CombinedSvg> = {};
function load(url: string): Promise<CombinedSvg> {
  if (cache[url]) return Promise.resolve(cache[url]);
  return fetch(url).then((r) => r.json()).then((j: CombinedSvg) => (cache[url] = j));
}

// warmHandDrawCache 预取一幕的合并 SVG 数据 URL 到本模块 cache。预览态由 VideoComposition
// 提前调用各幕的 svgDataUrl，使场景挂载时 cache 已就绪、直接拿到 data，
// 避免 SVG 未加载时先渲染兜底 GT 大图（首次转场到下一幕会闪一下原图）。失败静默忽略。
export function warmHandDrawCache(url?: string): Promise<void> {
  if (!url || cache[url]) return Promise.resolve();
  return load(url).then(() => undefined).catch(() => undefined);
}

// ── 运镜方案库 ──
// 每幕从中确定性地挑一种（按内容 URL 哈希），避免所有场景都用同一种单调放大。
// 每个方案给出归一化时间 e∈[0,1]（已缓动）下的缩放 z、平移 tx/ty(px) 与缩放锚点 origin(%)。
// 振幅刻意保守：最小缩放 ≥1.03、平移 ≤±18px，配合 origin 仍保证缩放后画面铺满、不露白边。
type CamScheme = {
  name: string;
  z: [number, number];
  tx?: [number, number];
  ty?: [number, number];
  ox?: number; // transformOrigin x（%），默认 50
  oy?: number; // transformOrigin y（%），默认 50
};

const CAMERA_SCHEMES: CamScheme[] = [
  { name: "push-center", z: [1.03, 1.12] },
  { name: "pull-center", z: [1.12, 1.03] },
  { name: "push-top-left", z: [1.05, 1.14], ox: 35, oy: 35 },
  { name: "push-bottom-right", z: [1.05, 1.14], ox: 65, oy: 65 },
  { name: "push-top-right", z: [1.05, 1.14], ox: 65, oy: 35 },
  { name: "push-bottom-left", z: [1.05, 1.14], ox: 35, oy: 65 },
  { name: "pan-right", z: [1.1, 1.1], tx: [18, -18] },
  { name: "pan-left", z: [1.1, 1.1], tx: [-18, 18] },
  { name: "tilt-down", z: [1.08, 1.12], ty: [-14, 14] },
  { name: "tilt-up", z: [1.08, 1.12], ty: [14, -14] },
];

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
// smoothstep：缓入缓出，让运镜有电影感而非匀速直推。
const smoothstep = (u: number) => {
  const t = Math.min(1, Math.max(0, u));
  return t * t * (3 - 2 * t);
};
// 稳定字符串哈希（FNV-1a 变体），用于按内容 URL 确定性选方案：同一幕每次渲染一致。
const hashStr = (s: string) => {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
};

// pickCamScheme：优先用 URL 里的场景序号轮换（相邻幕方案不重复），取不到序号则退回哈希。
function pickCamScheme(seed: string): CamScheme {
  const m = String(seed).match(/(?:scene[_-])?(\d+)[_.]/);
  const idx = m ? parseInt(m[1], 10) : hashStr(seed);
  const n = CAMERA_SCHEMES.length;
  return CAMERA_SCHEMES[((idx % n) + n) % n];
}

export const HandDrawLayout: React.FC<LayoutProps> = ({ slots, frame, fps, durationInFrames, editing }) => {
  // 单文件：fetch 一次合并 JSON（{coarse,full}），按 editing 取粗线稿/细节层。
  const url = slots.svgDataUrl;
  const pick = (c: CombinedSvg | null): SvgData | null => (c ? (editing ? c.coarse : c.full) : null);
  const [data, setData] = useState<SvgData | null>(pick(cache[url] ?? null));
  const [handle] = useState(() => (cache[url] ? -1 : delayRender(`handdraw ${url}`)));
  useEffect(() => {
    if (cache[url]) { setData(pick(cache[url])); return; }
    load(url).then((j) => { setData(editing ? j.coarse : j.full); continueRender(handle); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, handle, editing]);

  // 时序（单一清晰模型）：SVG 必须在「幕时长 - GT保留区间」内**画完**；之后 GT(原片) 占据片尾
  // gtHoldSec 秒（其内含 0.5s 渐显，余下定格）。幕时长即 TTS 校准帧数 durationInFrames（不延长）。
  // gtHoldSec 由 render-reel.mjs 全局注入（当前 1.2s：≈0.5s 渐显 + 余下静止定帧），每幕同值；缺省 2.0s 兜底。
  //   揭示时长 = 幕时长 - GT保留区间 = TTS - gtHoldSec（旁白过短时被下方 Math.max(1,…) clamp 到 1 帧）
  // 这些只依赖 durationInFrames/fps/slots，不依赖 SVG 数据 —— 提到 data 判空之前算，
  // 让兜底分支也能复用同一套 gtOpacity 时序（开头为 0），避免 SVG 未就绪时开头闪一下 GT。
  const gtHoldSec = typeof slots.gtHoldSec === "number" && slots.gtHoldSec > 0 ? slots.gtHoldSec : 2.0;
  const gtHold = Math.round(fps * gtHoldSec);
  const xfade = Math.min(gtHold, Math.round(fps * 0.5));
  const revealFrames = Math.max(1, durationInFrames - gtHold);

  // 运镜：按内容确定性挑一种方案（种子取自该幕的 SVG/GT URL，含场景序号），smoothstep 缓动。
  const scheme = pickCamScheme(slots.svgDataUrl ?? slots.gtImageUrl ?? url);
  const e = smoothstep(durationInFrames > 1 ? frame / (durationInFrames - 1) : 0);
  const z = lerp(scheme.z[0], scheme.z[1], e);
  const dx = scheme.tx ? lerp(scheme.tx[0], scheme.tx[1], e) : 0;
  const dy = scheme.ty ? lerp(scheme.ty[0], scheme.ty[1], e) : 0;
  const origin = `${scheme.ox ?? 50}% ${scheme.oy ?? 50}%`;
  // GT 在揭示结束后的 0.5s 内渐显到满，并保持（停留）到片尾。
  const gtOpacity = interpolate(frame, [revealFrames, revealFrames + xfade], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cam = { transform: `scale(${z}) translate(${dx}px, ${dy}px)`, transformOrigin: origin, alignItems: "center" as const, justifyContent: "center" as const };

  // GT 层（兜底与正常路径共用）：按 gtOpacity 渐显——开头为 0，故 SVG 未就绪时开头不会闪原图。
  const gtLayer = (
    <AbsoluteFill style={{ ...cam, opacity: gtOpacity }}>
      {slots.gtImageUrl && <Img src={slots.gtImageUrl} style={{ width: "100%", height: "100%", objectFit: "contain" }} />}
    </AbsoluteFill>
  );

  if (!data) {
    // SVG 数据未就绪：只渲染白底 + 按时序渐显的 GT 层（开头空白，不闪）。数据到达后切到完整揭示。
    return (
      <AbsoluteFill style={{ background: "white" }}>{gtLayer}</AbsoluteFill>
    );
  }

  const cum = cumulative(data.weights);
  const p = interpolate(frame, [0, revealFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const { nDone, curFrac } = revealState(p, cum);

  // 已揭示集合按**原始下标(z 序)**绘制：晚揭示的背景自动落到主体身后，避免遮挡。
  // 对恒等序数据 == 原行为（no-op），对主体优先重排数据才生效 → 向下兼容、可先于 worker 发布。
  const revealed = data.order.slice(0, nDone + 1);
  const current = data.order[nDone];
  const paintIdx = [...revealed].sort((a, b) => a - b);

  // GT 渐进落定：一条路径画完 SETTLE_DELAY 后加进 mask，清晰原图透过它自己的形状、经高斯羽化 + 时间淡入
  // 地逐区域晕染上来（跟着绘制推进，主体/背景一视同仁），而非最后整帧切。片尾整帧停留仍由 gtLayer 接管。
  const settleDelay = Math.round(fps * 0.45);
  const fadeFrames = Math.max(1, Math.round(fps * 0.45));
  const blurPx = Math.max(1, Math.round(data.w * 0.004));
  const uid = "hd" + (hashStr(slots.svgDataUrl ?? url) >>> 0).toString(36);
  const settleMask: { idx: number; a: number }[] = [];
  for (let k = 0; k < data.order.length; k++) {
    const a = Math.min(1, Math.max(0, (frame - cum[k] * revealFrames - settleDelay) / fadeFrames));
    if (a > 0.01) settleMask.push({ idx: data.order[k], a });
  }

  return (
    <AbsoluteFill style={{ background: "white" }}>
      <AbsoluteFill style={cam}>
        <svg width="100%" height="100%" viewBox={`0 0 ${data.w} ${data.h}`}
             preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
          {paintIdx.map((idx) => {
            const pth = data.paths[idx];
            const tr = `translate(${pth.t[0]} ${pth.t[1]})`;
            const isCurrent = idx === current;
            return (
              <path key={idx} d={pth.d} fill={pth.fill} transform={tr}
                    fillOpacity={isCurrent ? Math.max(0, curFrac - 0.25) / 0.75 : 1} />
            );
          })}
        </svg>
      </AbsoluteFill>
      {slots.gtImageUrl && settleMask.length > 0 && (
        <AbsoluteFill style={cam}>
          <svg width="100%" height="100%" viewBox={`0 0 ${data.w} ${data.h}`}
               preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <filter id={`${uid}b`} x="-5%" y="-5%" width="110%" height="110%">
                <feGaussianBlur stdDeviation={blurPx} />
              </filter>
              <mask id={`${uid}m`} maskUnits="userSpaceOnUse" x={0} y={0} width={data.w} height={data.h}>
                <g filter={`url(#${uid}b)`}>
                  {settleMask.map(({ idx, a }) => {
                    const pth = data.paths[idx];
                    return <path key={idx} d={pth.d} transform={`translate(${pth.t[0]} ${pth.t[1]})`} fill="#fff" fillOpacity={a} />;
                  })}
                </g>
              </mask>
            </defs>
            <image href={slots.gtImageUrl} x={0} y={0} width={data.w} height={data.h}
                   preserveAspectRatio="xMidYMid meet" mask={`url(#${uid}m)`} />
          </svg>
        </AbsoluteFill>
      )}
      {gtLayer}
    </AbsoluteFill>
  );
};
