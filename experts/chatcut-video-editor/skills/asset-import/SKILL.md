---
name: asset-import
description: Import local or attached media files, readable user-provided paths, existing ChatCut assets, and public media URLs into a ChatCut project from WorkBuddy.
---

# Asset Import for WorkBuddy

## Choose the source path

1. First inspect the targeted project's asset library with `read_project` `view:"assets"`; reuse a matching existing asset when possible.
2. For a public media URL, use the current ChatCut download/import tool and verify the returned asset.
3. For a local attachment or path readable by WorkBuddy, use the package command `chatcut-upload-media` with an `import_media` session.
4. If WorkBuddy cannot read the file or execute Node, ask the user to upload it through the ChatCut editor and then re-read the project assets.

Do not bulk-import a large folder without editorial need. When selection matters, inspect a bounded sample and choose the originals needed for the requested edit. Do not locally concatenate, pre-trim, burn captions, or flatten source files before importing them.

`chatcut-upload-media` is the only supported local upload command in this WorkBuddy expert. WorkBuddy adds the package `bin/` directory to `PATH`, so invoke the command by name from any working directory. Do not search the filesystem for `upload-media.mjs`, do not guess the plugin installation directory, and never use `direct-uploader`, `curl`, or a hand-written presigned-upload flow.

## Local file flow

`chatcut-upload-media` requires `ffmpeg` and `ffprobe` on `PATH`. Before running it, ask the user to install FFmpeg if either command is unavailable:

- macOS: download FFmpeg from OS X Experts: https://www.osxexperts.net/
- Windows: download an FFmpeg build from Gyan: https://www.gyan.dev/ffmpeg/builds/
- Linux: install the distribution's FFmpeg package.

After installation, ensure both `ffmpeg` and `ffprobe` are available in the shell running WorkBuddy. Do not download or install FFmpeg on the user's behalf.

1. Call `import_media` with `{"action":"create_session"}`.
2. Use the returned short-lived import `token` and `endpoint`. The token is only for this helper; never print it to the user or save it in the package.
3. Run the package command directly. On Windows PowerShell:

```powershell
chatcut-upload-media --token "<token>" --endpoint "<endpoint>" "C:\absolute\path\source-1.mp4" "C:\absolute\path\source-2.wav" --json-out "$env:TEMP\chatcut-imports.json"
```

On macOS or Linux:

```bash
chatcut-upload-media --token "<token>" --endpoint "<endpoint>" "/absolute/path/source-1.mp4" "/absolute/path/source-2.wav" --json-out "${TMPDIR:-/tmp}/chatcut-imports.json"
```

4. Read the JSON output and use each returned `assetId`. A registered placeholder may be available before all bytes finish uploading.
5. Use `track_progress` with `target:"transcription"` before transcript/caption work, and `target:"upload"` before byte-dependent frame decode or cloud export.
6. Verify with `read_project` `view:"assets"`.

The command invokes this package's official `skills/asset-import/scripts/upload-media.mjs` helper. If `chatcut-upload-media` is not found, do not search for the helper or improvise a second upload protocol: report that the WorkBuddy expert installation is incomplete or outdated, ask the user to reinstall the latest package, or use the ChatCut editor upload UI.

If the user says the source must not be uploaded, stop before this flow and explain that the hosted WorkBuddy connector cannot perform a cloud-ready ChatCut edit with those bytes.
