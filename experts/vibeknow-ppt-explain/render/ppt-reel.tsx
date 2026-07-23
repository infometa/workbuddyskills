/**
 * Remotion 入口:注册 PptReel(多页文档讲解成片)。
 * 由 skills/ppt-explain/scripts/render-reel.mjs 调起;尺寸/时长由 calcReelMetadata 按 props 动态算。
 */
import React from "react";
import { Composition, registerRoot } from "remotion";
import { PptReel, calcReelMetadata } from "./PptReel";

const FPS = 30;
const DUR_FRAMES = 120;
const W = 1920;
const H = 1080;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="PptReel"
      component={PptReel}
      durationInFrames={DUR_FRAMES}
      fps={FPS}
      width={W}
      height={H}
      calculateMetadata={calcReelMetadata}
      defaultProps={{
        scenes: [
          { gtImageUrl: "pptprev/scene0.jpg", durationInFrames: DUR_FRAMES },
          { gtImageUrl: "pptprev/scene1.jpg", durationInFrames: DUR_FRAMES },
        ],
        transition: "fade" as const,
        transitionFrames: 15,
        subtitle: true,
        width: W,
        height: H,
        fps: FPS,
      }}
    />
  </>
);

registerRoot(RemotionRoot);
