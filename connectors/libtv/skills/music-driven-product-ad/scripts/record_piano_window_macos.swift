// Optional screen-only recorder; never records microphone or system audio.
import Foundation
import AppKit
import ScreenCaptureKit
import AVFoundation

final class RecordingDelegate: NSObject, SCRecordingOutputDelegate {
    var recordingError: Error?
    func recordingOutputDidStartRecording(_ output: SCRecordingOutput) { print("RECORDING_STARTED \(Date().timeIntervalSince1970)"); fflush(stdout) }
    func recordingOutput(_ output: SCRecordingOutput, didFailWithError error: Error) { recordingError=error; fputs("Recording failed: \(error)\n",stderr) }
    func recordingOutputDidFinishRecording(_ output: SCRecordingOutput) { print("RECORDING_FINISHED \(Date().timeIntervalSince1970)"); fflush(stdout) }
}
enum InputError: Error { case invalid(String) }
@main struct Main {
 static func main() async throws {
    _ = NSApplication.shared
    let a=CommandLine.arguments
    guard a.count == 4 || a.count == 8 else { throw InputError.invalid("Usage: record_piano_window_macos WINDOW_ID OUTPUT.mp4 SECONDS [X Y WIDTH HEIGHT]") }
    guard let wid=UInt32(a[1]), let seconds=Double(a[3]), seconds.isFinite, seconds > 0 else { throw InputError.invalid("Invalid window ID or duration") }
    let url=URL(fileURLWithPath:a[2])
    guard !FileManager.default.fileExists(atPath:url.path) else { throw InputError.invalid("Output exists; choose a new filename") }
    guard CGPreflightScreenCaptureAccess() else { throw InputError.invalid("Screen Recording permission is unavailable") }
    let content=try await SCShareableContent.excludingDesktopWindows(true,onScreenWindowsOnly:false)
    guard let win=content.windows.first(where:{$0.windowID == wid}), win.owningApplication?.bundleIdentifier == "com.google.Chrome" else { throw InputError.invalid("The selected Chrome window is unavailable") }
    var crop=CGRect(origin:.zero,size:win.frame.size)
    if a.count == 8 {
        let v=a[4...7].compactMap(Double.init)
        guard v.count == 4, v.allSatisfy({$0.isFinite}), v[0] >= 0, v[1] >= 0, v[2] >= 2, v[3] >= 2 else { throw InputError.invalid("Invalid crop rectangle") }
        crop=CGRect(x:v[0],y:v[1],width:v[2],height:v[3])
        guard crop.maxX <= win.frame.width, crop.maxY <= win.frame.height else { throw InputError.invalid("Crop exceeds the selected window") }
    }
    let config=SCStreamConfiguration()
    config.width=Int(crop.width)/2*2; config.height=Int(crop.height)/2*2
    config.sourceRect=crop; config.minimumFrameInterval=CMTime(value:1,timescale:30)
    config.showsCursor=false; config.capturesAudio=false
    let outputConfig=SCRecordingOutputConfiguration()
    outputConfig.outputURL=url; outputConfig.outputFileType = .mp4; outputConfig.videoCodecType = .h264
    let delegate=RecordingDelegate()
    let output=SCRecordingOutput(configuration:outputConfig,delegate:delegate)
    let stream=SCStream(filter:SCContentFilter(desktopIndependentWindow:win),configuration:config,delegate:nil)
    try stream.addRecordingOutput(output)
    try await stream.startCapture()
    do { try await Task.sleep(for:.seconds(seconds)) } catch { try? await stream.stopCapture(); throw error }
    try await stream.stopCapture()
    try await Task.sleep(for:.seconds(1))
    if let error=delegate.recordingError { throw error }
    let asset=AVURLAsset(url:url)
    let audioTracks=try await asset.loadTracks(withMediaType:.audio)
    guard audioTracks.isEmpty else { throw InputError.invalid("Unexpected audio track in screen-only output") }
    print("SCREEN_ONLY duration=\(CMTimeGetSeconds(try await asset.load(.duration))) audioTracks=0")
 }
}
