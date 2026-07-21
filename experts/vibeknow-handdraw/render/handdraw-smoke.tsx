/**
 * Remotion 入口:注册 HandDrawReel(多幕手绘成片)。
 * 由 skills/handdraw/scripts/render-reel.mjs 调起;尺寸/时长由 calcReelMetadata 按 props 动态算。
 */
import React from "react";
import { Composition, registerRoot } from "remotion";
import { HandDrawReel, calcReelMetadata } from "./HandDrawReel";

const FPS = 30;
const DUR_FRAMES = 120; // 4s 预览循环
const W = 1920;
const H = 1080;
const GT_HOLD_SEC = 1.2; // 片尾停留(以绘制为主)

export const RemotionRoot: React.FC = () => (
  <>
    {/* 多幕成片(带转场)。默认 props 只是预览用;实际时长/尺寸由 calcReelMetadata 按 props 动态算。 */}
    <Composition
      id="HandDrawReel"
      component={HandDrawReel}
      durationInFrames={DUR_FRAMES}
      fps={FPS}
      width={W}
      height={H}
      calculateMetadata={calcReelMetadata}
      defaultProps={{
        scenes: [
          { svgDataUrl: "hdprev/sample.json", gtImageUrl: "hdprev/sample.jpg", durationInFrames: DUR_FRAMES },
          { svgDataUrl: "hdprev/sample.json", gtImageUrl: "hdprev/sample.jpg", durationInFrames: DUR_FRAMES },
        ],
        transition: "fade" as const,
        transitionFrames: 15,
        width: W,
        height: H,
        fps: FPS,
        gtHoldSec: GT_HOLD_SEC,
      }}
    />
  </>
);

registerRoot(RemotionRoot);
