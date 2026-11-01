import Foundation
import AVFoundation
enum InputError: Error { case invalid(String) }
@main struct Main {
 static func main() async throws {
    let a=CommandLine.arguments
    guard a.count == 5 else { throw InputError.invalid("Usage: trim_screen_macos INPUT.mp4 OUTPUT.mp4 START_SECONDS DURATION_SECONDS") }
    guard let start=Double(a[3]), let duration=Double(a[4]), start.isFinite, duration.isFinite, start >= 0, duration > 0 else { throw InputError.invalid("Invalid trim range") }
    let output=URL(fileURLWithPath:a[2]); guard !FileManager.default.fileExists(atPath:output.path) else { throw InputError.invalid("Output exists") }
    let asset=AVURLAsset(url:URL(fileURLWithPath:a[1]))
    let total=CMTimeGetSeconds(try await asset.load(.duration))
    guard start+duration <= total+0.0001 else { throw InputError.invalid("Trim exceeds source playback duration") }
    guard let source=try await asset.loadTracks(withMediaType:.video).first else { throw InputError.invalid("No video track") }
    let composition=AVMutableComposition()
    let track=composition.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid)!
    try track.insertTimeRange(CMTimeRange(start:CMTime(seconds:start,preferredTimescale:60000),duration:CMTime(seconds:duration,preferredTimescale:60000)),of:source,at:.zero)
    track.preferredTransform=try await source.load(.preferredTransform)
    guard let export=AVAssetExportSession(asset:composition,presetName:AVAssetExportPresetHighestQuality) else { throw InputError.invalid("Exporter unavailable") }
    try await export.export(to:output,as:.mp4)
    let result=AVURLAsset(url:output)
    let audioTracks=try await result.loadTracks(withMediaType:.audio)
    let resultDuration=CMTimeGetSeconds(try await result.load(.duration))
    guard audioTracks.isEmpty, abs(resultDuration-duration)<0.05 else { throw InputError.invalid("Export duration or audio-track check failed") }
    print("SCREEN_ONLY duration=\(resultDuration) audioTracks=0")
 }
}
