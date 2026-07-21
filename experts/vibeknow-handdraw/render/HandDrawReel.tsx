/**
 * HandDrawReel:把多幕手绘按序串成一条成片,幕间用 @remotion/transitions 做转场。
 * 每幕复用 HandDrawLayout(逐笔画出→落定),帧/时长按「幕内局部」传入,故各幕独立计时。
 */
import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { HandDrawLayout } from "./layout/HandDrawLayout";
import type { Theme } from "./layout/types";

export type ReelScene = {
  svgDataUrl?: string;  // public 相对路径,如 hdprev/scene1.json(降级页无此项)
  gtImageUrl: string;
  audioUrl?: string;    // 可选:本幕旁白音频(public 相对路径)
  narration?: string;   // 可选:本幕旁白文字(留记录,不渲染)
  static?: boolean;     // 降级页:原图定格,不做逐笔绘制(积分不足兜底)
  durationInFrames: number;
};

export type ReelProps = {
  scenes: ReelScene[];
  transition: "fade" | "slide" | "wipe";
  transitionFrames: number;
  width: number;
  height: number;
  fps: number;
  gtHoldSec: number;
};

const presentationOf = (t: ReelProps["transition"]) =>
  t === "slide" ? slide() : t === "wipe" ? wipe() : fade();

/** 单幕:useCurrentFrame() 在 TransitionSeries.Sequence 内是「幕内局部帧」,配合本幕时长驱动绘制。 */
const SceneClip: React.FC<{ scene: ReelScene; gtHoldSec: number; transitionFrames: number }> = ({ scene, gtHoldSec, transitionFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <>
      {scene.audioUrl && (
        <Audio
          src={staticFile(scene.audioUrl)}
          volume={(f) =>
            interpolate(
              f,
              [Math.max(0, scene.durationInFrames - transitionFrames), scene.durationInFrames],
              [1, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            )
          }
        />
      )}
      {scene.static ? (
        // 降级页:白底 + 原图定格(objectFit:contain,与绘制幕的 GT 层一致),不逐笔绘制。
        <AbsoluteFill style={{ background: "white" }}>
          <Img src={staticFile(scene.gtImageUrl)} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
        </AbsoluteFill>
      ) : (
        <HandDrawLayout
          frame={frame}
          fps={fps}
          durationInFrames={scene.durationInFrames}
          editing={false}
          theme={{} as Theme}
          styleOverrides={{}}
          slots={{
            svgDataUrl: staticFile(scene.svgDataUrl as string),
            gtImageUrl: staticFile(scene.gtImageUrl),
            gtHoldSec,
          }}
        />
      )}
    </>
  );
};

export const HandDrawReel: React.FC<ReelProps> = ({ scenes, transition, transitionFrames, gtHoldSec }) => {
  const present = presentationOf(transition);
  const timing = linearTiming({ durationInFrames: transitionFrames });
  return (
    <TransitionSeries>
      {scenes.flatMap((s, i) => {
        const seq = (
          <TransitionSeries.Sequence key={`s${i}`} durationInFrames={s.durationInFrames}>
            <SceneClip scene={s} gtHoldSec={gtHoldSec} transitionFrames={transitionFrames} />
          </TransitionSeries.Sequence>
        );
        if (i === scenes.length - 1) return [seq];
        return [
          seq,
          <TransitionSeries.Transition key={`t${i}`} presentation={present} timing={timing} />,
        ];
      })}
    </TransitionSeries>
  );
};

/** 动态算总时长/尺寸:总帧 = Σ幕时长 − (幕数−1)×转场帧(转场是相邻幕重叠)。 */
export const calcReelMetadata = ({ props }: { props: ReelProps }) => {
  const n = props.scenes.length;
  const sum = props.scenes.reduce((a, s) => a + s.durationInFrames, 0);
  const total = Math.max(1, sum - Math.max(0, n - 1) * props.transitionFrames);
  return { durationInFrames: total, width: props.width, height: props.height, fps: props.fps };
};
