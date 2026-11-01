# Optional Zen Piano screen recording

Read only when the user requests a recording of the playing interface. Keep the site's recorder as the audio source. Save two separate deliverables: the downloaded WAV and a **screen-only MP4 with no audio track**. Do not enable microphone/system sound or add the WAV to the screen recording unless the user explicitly changes this choice.

## Select and frame the window

1. Identify the exact piano tab from the current browser inventory. Reuse the task's piano tab; another tab at the same URL can belong to another task. Select that exact tab in its Chrome window before capture or native key events.
2. Read the current Chrome process/window identity through permitted native inspection. A browser tab ID, Chrome scripting window ID, and Core Graphics window ID are different identifiers. The recorder takes the **Core Graphics window ID**. Never reuse an ID from a prior session.
3. Preview the selected window using the available WorkBuddy computer/browser tools. Crop the browser chrome if helpful, while retaining the complete piano keyboard and visible recording controls. Use current window dimensions and page bounds, not saved pixel coordinates. Preserve a LibTV canvas tab only when the user or a `makeVisible=true` handoff requested it; do not assume an embedded panel exists.
4. Start capture before playing; wait for `RECORDING_STARTED`. Start the **site recorder**, perform the note plan, allow the closing sound to decay, then stop the site recorder. Capture a little pre-roll and post-roll so tool latency cannot truncate the performance.

## macOS helper

The optional helpers require macOS 15+ and a Swift SDK containing `SCRecordingOutput`. They use existing Screen Recording permission, do not modify permission settings, and refuse existing output files. Compile outside the skill directory:

```sh
swiftc -parse-as-library scripts/record_piano_window_macos.swift -o "$capture_build_dir/record-piano-window"
swiftc -parse-as-library scripts/trim_screen_macos.swift -o "$capture_build_dir/trim-piano-screen"
```

Create a fresh `capture_build_dir` and output paths first. Recorder arguments:

```text
record-piano-window WINDOW_ID OUTPUT.mp4 CAPTURE_SECONDS [CROP_X CROP_Y CROP_WIDTH CROP_HEIGHT]
trim-piano-screen INPUT.mp4 OUTPUT.mp4 START_SECONDS DURATION_SECONDS
```

Crop coordinates use points relative to the selected window. Omitting the crop records the whole selected window. `capturesAudio` is fixed to `false`. The recorder prints observed start/finish times and verifies zero audio tracks. It may finish a little beyond the requested wall-clock capture interval; trim the saved capture after inspecting where the first and last key events appear.

The trim helper copies only the video track into a new composition. It validates the **presentation duration** and absence of audio after export. Raw MP4 media-track durations can include codec pre-roll hidden by edit lists; do not mistake those values for player duration.

If the helper is unavailable, use an already available screen recorder that can isolate the requested window/region and disable all audio. Do not substitute a slideshow of screenshots for an actual screen recording.

## Verify and deliver

- Inspect the saved recording near the start, during held notes, and after the final release. Verify the page is the correct piano and the key states actually change; a successful file write alone is insufficient.
- Verify the screen file contains one video track and **zero audio tracks**, and report its playback duration. If trimmed to D, preserve the full raw capture.
- Export the music through **Zen Piano → 下载录音 → 下载为 WAV**, verify it independently, and preserve its original download. Screen capture never replaces this step.
- Return separate absolute file links for the screen-only MP4 and site WAV. Use the current browser/player for real playback and show previews only when WorkBuddy actually supports them. Do not claim frame-perfect synchronization from wall-clock timestamps alone.
