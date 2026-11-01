#!/usr/bin/env python3
"""Read bundled repertoire and prepare note data; never synthesize or play audio."""

import argparse
import json
import math
import re
import struct
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets/scores/catalog.json"
PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def normalize(value):
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(c for c in value if c.isalnum())


def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))["pieces"]


def resolve_piece(query):
    matches = [p for p in catalog() if normalize(query) in
               {normalize(s) for s in [p["id"], p["title"], *p["aliases"]]}]
    if len(matches) != 1:
        raise ValueError("Unknown or ambiguous piece; use the list command for titles and IDs.")
    return matches[0]


def note_name(midi):
    return PITCH_NAMES[midi % 12] + str(midi // 12 - 1)


def midi_bytes(notes, bpm):
    """Write a piano-only SMF with independent note releases and chord onsets."""
    ppq = 960
    tempo = round(60000000 / bpm)
    if not 1 <= tempo <= 0xFFFFFF:
        raise ValueError("Tempo is outside the Standard MIDI File range")

    def vlq(value):
        chunks = [value & 127]
        value >>= 7
        while value:
            chunks.insert(0, (value & 127) | 128)
            value >>= 7
        if len(chunks) > 4:
            raise ValueError("MIDI delta time is too large")
        return bytes(chunks)

    events = []
    for note in notes:
        pitch_class, octave = re.fullmatch(r"([A-G]#?)(-?\d+)", note["note"]).groups()
        pitch = PITCH_NAMES.index(pitch_class) + (int(octave) + 1) * 12
        start = round(note["timestamp"] * 1000 * ppq / tempo)
        end = max(start + 1, round((note["timestamp"] + note["duration"]) * 1000 * ppq / tempo))
        velocity = max(1, min(127, round(note["velocity"] * 127)))
        events.append((start, 1, bytes((0x90, pitch, velocity))))
        events.append((end, 0, bytes((0x80, pitch, 0))))
    # A note-off precedes a new attack at the same tick.
    events.sort(key=lambda e: (e[0], e[1], e[2]))
    track = bytearray(b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big") + b"\x00\xc0\x00")
    previous = 0
    for tick, _priority, event in events:
        track.extend(vlq(tick - previous) + event)
        previous = tick
    track.extend(b"\x00\xff\x2f\x00")
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, ppq) + b"MTrk" + struct.pack(">I", len(track)) + track


def prepare(piece, *, start=0, seconds=None, speed=1, transpose=0,
            range_policy="keep", tail="natural"):
    if not math.isfinite(start) or start < 0:
        raise ValueError("start must be finite and nonnegative")
    if not math.isfinite(speed) or speed <= 0:
        raise ValueError("speed must be finite and positive")
    if seconds is not None and (not math.isfinite(seconds) or seconds <= 0):
        raise ValueError("seconds must be finite and positive")
    if range_policy not in ("keep", "error", "octave") or tail not in ("natural", "clip"):
        raise ValueError("Invalid range or tail policy")
    score = json.loads((ROOT / piece["score_file"]).read_text(encoding="utf-8"))
    ms_per_tick = 60000 / score["default_quarter_bpm"] / score["ticks_per_quarter"]
    left = start * 1000
    right = math.inf if seconds is None else left + seconds * 1000 * speed
    notes, moved, outside = [], [], []
    for tick, length, original_pitch, velocity, _track, _channel in score["notes"]:
        onset, end = tick * ms_per_tick, (tick + length) * ms_per_tick
        if onset >= right or end <= left:
            continue
        pitch = original_pitch + transpose
        if not 0 <= pitch <= 127:
            raise ValueError("Transposition exceeds the MIDI pitch range")
        if not 36 <= pitch <= 96:
            outside.append(note_name(pitch))
            if range_policy == "error":
                raise ValueError(f"{note_name(pitch)} is outside the observed C2–C7 keyboard")
            if range_policy == "octave":
                before = pitch
                while pitch < 36:
                    pitch += 12
                while pitch > 96:
                    pitch -= 12
                moved.append({"from": note_name(before), "to": note_name(pitch)})
        if tail == "clip":
            end = min(end, right)
        timestamp = round((max(left, onset) - left) / speed, 3)
        duration = round((end - max(left, onset)) / speed, 3)
        if duration <= 0:
            continue
        notes.append({"note": note_name(pitch), "timestamp": timestamp,
                      "duration": duration, "velocity": round(velocity / 127, 6)})
    if not notes:
        raise ValueError("Requested excerpt contains no notes")
    notes.sort(key=lambda n: (n["timestamp"], n["note"]))
    info = {
        "piece": piece["title"], "arrangement": piece["arrangement"],
        "scope": "full saved sequence" if start == 0 and seconds is None else "excerpt",
        "note_count": len(notes), "duration_seconds": round(max(
            n["timestamp"] + n["duration"] for n in notes) / 1000, 3),
        "quarter_bpm": score["default_quarter_bpm"] * speed,
        "outside_keyboard_before_octave_fit": sorted(set(outside)),
        "octave_adjusted_note_events": len(moved), "transpose_semitones": transpose,
        "pedal": "Not encoded in note JSON; source MIDI retains controller events",
        "source": piece["source_page"], "license": piece["license"],
    }
    return notes, info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List the bundled scores and their scope")
    build = sub.add_parser("build", help="Prepare local note events for direct piano-key performance")
    build.add_argument("piece", help="Chinese title, supported alias, or preset ID")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--start", type=float, default=0, help="Seconds at the saved default tempo")
    build.add_argument("--seconds", type=float, help="Output attack-window length; omit for remaining piece")
    build.add_argument("--speed", type=float, default=1, help="Scale onset times and durations together")
    build.add_argument("--transpose", type=int, default=0, help="Semitones; default preserves original key")
    build.add_argument("--range-policy", choices=("keep", "error", "octave"), default="keep")
    build.add_argument("--tail", choices=("natural", "clip"), default="natural")
    build.add_argument("--format", choices=("midi", "zen", "events"), default="events")
    args = parser.parse_args()
    try:
        if args.command == "list":
            print(json.dumps([{k: p[k] for k in (
                "id", "title", "aliases", "arrangement", "default_quarter_bpm",
                "duration_seconds", "note_count", "midi_range", "out_of_61_key_range")}
                for p in catalog()], ensure_ascii=False, indent=2))
            return
        piece = resolve_piece(args.piece)
        notes, info = prepare(piece, start=args.start, seconds=args.seconds,
                              speed=args.speed, transpose=args.transpose,
                              range_policy=args.range_policy, tail=args.tail)
        if args.format == "midi":
            data = midi_bytes(notes, info["quarter_bpm"])
        elif args.format == "zen":
            data = {"notes": notes, "timestamp": datetime.now(timezone.utc).isoformat(
                timespec="milliseconds").replace("+00:00", "Z"), "version": "1.0"}
        else:
            data = {"metadata": info, "time_unit": "milliseconds", "notes": notes}
        # Exclusive creation protects earlier recordings and prepared excerpts.
        if args.format == "midi":
            with args.output.open("xb") as handle:
                handle.write(data)
        else:
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        print(json.dumps({"output": str(args.output.resolve()), **info}, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
