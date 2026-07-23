// 手绘渲染所需的最小布局接口(从渲染引擎抽出的自洽子集)。
export type Theme = unknown;

export interface LayoutProps {
  slots: Record<string, any>;
  theme: Theme;
  frame: number;
  fps: number;
  durationInFrames: number;
  styleOverrides?: Record<string, Record<string, any>>;
  editing?: boolean;
}
