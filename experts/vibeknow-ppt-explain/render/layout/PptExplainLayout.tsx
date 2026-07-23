/**
 * PptExplainLayout —— 单幕:整页文档图 contain 静态展示 + 底部字幕（分页滚动，跟配音走）。
 * 画面刻意不做运镜（用户要求），只有字幕随时间一句一句切换（不再整段糊满屏）。
 * 字幕 cue：把本页旁白按标点切成短句，按字数比例分配到本页时长，只显示当前这句。
 */
import React from "react";
import { AbsoluteFill, Img, useVideoConfig } from "remotion";

export type PptSlots = {
  gtImageUrl: string;      // 整页文档图（staticFile 后的 URL）
  narration?: string;      // 本页旁白全文（会被切成 cue）
  subtitle?: boolean;      // 是否显示字幕（默认 true）
};

// 把一段中文旁白切成"一句一屏"的短 cue：先按标点断句，再按目标长度合并/硬切。
function splitCues(text: string, maxLen = 20): string[] {
  const parts = text
    .split(/(?<=[，。！？；、,.!?;])/)
    .map((s) => s.trim())
    .filter(Boolean);
  const cues: string[] = [];
  let buf = "";
  for (const p of parts) {
    if ((buf + p).length <= maxLen) {
      buf += p;
    } else {
      if (buf) cues.push(buf);
      if (p.length <= maxLen) {
        buf = p;
      } else {
        for (let i = 0; i < p.length; i += maxLen) cues.push(p.slice(i, i + maxLen));
        buf = "";
      }
    }
  }
  if (buf) cues.push(buf);
  return cues.length ? cues : [text];
}

export const PptExplainLayout: React.FC<{
  frame: number;
  durationInFrames: number;
  slots: PptSlots;
}> = ({ frame, durationInFrames, slots }) => {
  const { width, height } = useVideoConfig();
  const showSub = slots.subtitle !== false && !!(slots.narration && slots.narration.trim());

  // 字号按短边缩放（竖屏更大更清晰，与生产一致 ~短边×0.05）；每句字数按**画面宽度**自适应，
  // 竖屏窄→每句少字、横屏宽→多字，避免竖屏时单行溢出被截断。
  const fontSize = Math.round(Math.min(width, height) * 0.05);
  const charsPerLine = Math.max(8, Math.floor((width * 0.86) / fontSize));
  const maxLen = Math.min(charsPerLine, 24);

  // 当前该显示哪句：按各 cue 字数占比切分本页时长，取 frame 落在的那段。
  let current = "";
  if (showSub) {
    const cues = splitCues(slots.narration!.trim(), maxLen);
    const total = cues.reduce((a, c) => a + c.length, 0) || 1;
    let acc = 0;
    let picked = cues[cues.length - 1];
    for (const c of cues) {
      const startF = (acc / total) * durationInFrames;
      acc += c.length;
      const endF = (acc / total) * durationInFrames;
      if (frame >= startF && frame < endF) { picked = c; break; }
    }
    current = picked;
  }

  return (
    <AbsoluteFill style={{ background: "#111318" }}>
      {/* 页面图：contain 完整展示，不裁不变形；letterbox 用近黑给「屏幕」质感 */}
      <Img
        src={slots.gtImageUrl}
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      />

      {/* 底部字幕：安全区内，半透明底 + 白字，只显示当前一句（不糊满屏） */}
      {showSub && current && (
        <AbsoluteFill
          style={{
            justifyContent: "flex-end",
            alignItems: "center",
            padding: "0 6% 4.5%",
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              maxWidth: "90%",
              background: "rgba(8,8,12,0.68)",
              color: "#fff",
              borderRadius: 10,
              padding: "0.35em 0.9em",
              fontSize,
              lineHeight: 1.3,
              fontWeight: 500,
              textAlign: "center",
              wordBreak: "break-word",
              fontFamily:
                '"PingFang SC","Microsoft YaHei","Noto Sans SC","Noto Sans CJK SC","Source Han Sans SC",-apple-system,"Segoe UI",Roboto,sans-serif',
            }}
          >
            {current}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
