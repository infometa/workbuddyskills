#!/usr/bin/env python3
"""Trim long edge silence from a 16-bit PCM WAV while preserving its format."""

from __future__ import annotations

import argparse
import array
import math
import sys
import wave
from pathlib import Path


def rms_16le(block: bytes) -> float:
    samples = array.array("h")
    samples.frombytes(block)
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Trim leading/trailing silence from a 16-bit PCM WAV."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--window-ms", type=int, default=100)
    parser.add_argument("--threshold-percent", type=float, default=1.0)
    parser.add_argument("--keep-before", type=float, default=0.25)
    parser.add_argument("--keep-after", type=float, default=1.5)
    parser.add_argument("--target-seconds", type=float, help="Pad the complete trimmed cue to this duration; never cut to fit")
    args = parser.parse_args()

    if args.source.resolve() == args.destination.resolve():
        parser.error("source and destination must differ; preserve the original download")
    if args.destination.exists():
        parser.error(f"destination already exists: {args.destination}")
    if args.window_ms <= 0 or not math.isfinite(args.threshold_percent) or args.threshold_percent <= 0:
        parser.error("window and threshold values must be positive")
    if not all(math.isfinite(v) and v >= 0 for v in (args.keep_before, args.keep_after)):
        parser.error("silence margins must be finite and nonnegative")
    if args.target_seconds is not None and (not math.isfinite(args.target_seconds) or args.target_seconds <= 0):
        parser.error("target duration must be finite and positive")

    with wave.open(str(args.source), "rb") as reader:
        params = reader.getparams()
        if params.sampwidth != 2 or params.comptype != "NONE":
            parser.error("only uncompressed 16-bit PCM WAV files are supported")
        frames = reader.readframes(params.nframes)

    bytes_per_frame = params.nchannels * params.sampwidth
    window_frames = max(1, round(params.framerate * args.window_ms / 1000))
    window_bytes = window_frames * bytes_per_frame
    levels = [
        rms_16le(frames[offset : offset + window_bytes])
        for offset in range(0, len(frames), window_bytes)
    ]
    peak = max(levels, default=0.0)
    if peak == 0:
        parser.error("the WAV is completely silent")

    threshold = max(30.0, peak * args.threshold_percent / 100.0)
    active = [index for index, level in enumerate(levels) if level > threshold]
    if not active:
        parser.error("no audio exceeded the silence threshold")

    start_frame = max(
        0, active[0] * window_frames - round(args.keep_before * params.framerate)
    )
    end_frame = min(
        params.nframes,
        (active[-1] + 1) * window_frames + round(args.keep_after * params.framerate),
    )
    trimmed = frames[start_frame * bytes_per_frame : end_frame * bytes_per_frame]
    output_frames = end_frame - start_frame
    if args.target_seconds is not None:
        target_frames = round(args.target_seconds * params.framerate)
        if target_frames < output_frames:
            parser.error("complete trimmed cue exceeds target; inspect edge silence or revise the performance, do not cut the cadence")
        trimmed += b"\0" * ((target_frames - output_frames) * bytes_per_frame)
        output_frames = target_frames

    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with args.destination.open("xb") as handle:
        with wave.open(handle, "wb") as writer:
            writer.setparams(params)
            writer.writeframes(trimmed)

    original_seconds = params.nframes / params.framerate
    trimmed_seconds = output_frames / params.framerate
    print(
        f"trimmed {original_seconds:.3f}s to {trimmed_seconds:.3f}s; "
        f"threshold={threshold:.1f} RMS; output={args.destination}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
