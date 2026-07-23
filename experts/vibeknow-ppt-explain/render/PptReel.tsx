/**
 * PptReel:把多页文档幕按序串成讲解成片,幕间用 @remotion/transitions 转场。
 * 每幕 = 整页文档图 + Ken Burns 运镜 + 底部字幕(PptExplainLayout),时长由旁白音频驱动。
 */
import React from "react";
import { AbsoluteFill, Audio, staticFile, interpolate, useCurrentFrame } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import { wipe } from "@remotion/transitions/wipe";
import { PptExplainLayout } from "./layout/PptExplainLayout";

export type ReelScene = {
  gtImageUrl: string;    // 整页文档图(public 相对路径)
  audioUrl?: string;     // 可选:本幕旁白音频
  narration?: string;    // 可选:本幕旁白文字 → 底部字幕
  durationInFrames: number;
};

export type ReelProps = {
  scenes: ReelScene[];
  transition: "fade" | "slide" | "wipe";
  transitionFrames: number;
  subtitle: boolean;     // 全局字幕开关
  width: number;
  height: number;
  fps: number;
};

const presentationOf = (t: ReelProps["transition"]) =>
  t === "slide" ? slide() : t === "wipe" ? wipe() : fade();

const SceneClip: React.FC<{ scene: ReelScene; subtitle: boolean; transitionFrames: number }> = ({
  scene,
  subtitle,
  transitionFrames,
}) => {
  const frame = useCurrentFrame();
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
      <PptExplainLayout
        frame={frame}
        durationInFrames={scene.durationInFrames}
        slots={{
          gtImageUrl: staticFile(scene.gtImageUrl),
          narration: scene.narration,
          subtitle,
        }}
      />
    </>
  );
};

export const PptReel: React.FC<ReelProps> = ({ scenes, transition, transitionFrames, subtitle }) => {
  const present = presentationOf(transition);
  const timing = linearTiming({ durationInFrames: transitionFrames });
  return (
    <AbsoluteFill style={{ background: "#111318" }}>
      <TransitionSeries>
        {scenes.flatMap((s, i) => {
          const seq = (
            <TransitionSeries.Sequence key={`s${i}`} durationInFrames={s.durationInFrames}>
              <SceneClip scene={s} subtitle={subtitle} transitionFrames={transitionFrames} />
            </TransitionSeries.Sequence>
          );
          if (i === scenes.length - 1) return [seq];
          return [
            seq,
            <TransitionSeries.Transition key={`t${i}`} presentation={present} timing={timing} />,
          ];
        })}
      </TransitionSeries>
    </AbsoluteFill>
  );
};

/** 总时长 = Σ幕时长 − (幕数−1)×转场帧(转场是相邻幕重叠)。 */
export const calcReelMetadata = ({ props }: { props: ReelProps }) => {
  const n = props.scenes.length;
  const sum = props.scenes.reduce((a, s) => a + s.durationInFrames, 0);
  const total = Math.max(1, sum - Math.max(0, n - 1) * props.transitionFrames);
  return { durationInFrames: total, width: props.width, height: props.height, fps: props.fps };
};
