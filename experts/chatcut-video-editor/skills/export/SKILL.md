---
name: export
description: Export, render, download, or deliver a ChatCut timeline from WorkBuddy as video, audio, subtitles, NLE XML, or a motion-graphic render.
---

# Export from WorkBuddy

Export only when the user explicitly asks to export, render, download, share, or finalize. A normal edit ends with the editable timeline ready for review.

## Durable export

Use `submit_export`. Common video defaults are H.264 MP4 at 1080p, with fps omitted to match the timeline unless the user specifies otherwise:

```json
{
  "format": "video",
  "codec": "h264",
  "resolution": "1080p",
  "name": "final-cut"
}
```

Video codecs are `h264` and `vp8`; supported fps values are `24`, `25`, `30`, `50`, and `60`. Audio export uses `format:"audio"`. Subtitle files use `format:"subtitles"` with `subtitleFormat:"srt"` or `"txt"`. NLE XML uses `format:"xml"` with the current `nleFormat` value from the tool schema.

`submit_export` returns a durable render ID or an immediate download URL. For asynchronous work, call `track_export` until the requested render completes. Then provide the returned download URL and concise render metadata. Do not report completion while the render is pending or failed.

If cloud export is blocked by local-only/unavailable media, import cloud-readable originals when the user's intent allows upload. Otherwise explain the blocker; do not silently create a flattened local substitute.
