export type SvgData = {
  w: number;
  h: number;
  paths: { d: string; fill: string; t: [number, number] }[];
  order: number[];
  weights: number[];
};

export function cumulative(weights: number[]): number[] {
  const out: number[] = [];
  let acc = 0;
  for (const w of weights) {
    acc += w;
    out.push(acc);
  }
  return out;
}

export function revealState(
  p: number,
  cum: number[]
): { nDone: number; curFrac: number } {
  const pc = Math.min(1, Math.max(0, p));
  const n = cum.length;
  if (n === 0) return { nDone: 0, curFrac: 0 };
  if (pc >= 1) return { nDone: n, curFrac: 0 };
  let nDone = 0;
  while (nDone < n && cum[nDone] <= pc) nDone++;
  const lo = nDone === 0 ? 0 : cum[nDone - 1];
  const step = (cum[nDone] ?? 1) - lo;
  const curFrac = step > 0 ? (pc - lo) / step : 0;
  return { nDone, curFrac };
}
