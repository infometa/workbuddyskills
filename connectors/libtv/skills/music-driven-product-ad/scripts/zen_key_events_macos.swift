// Native keyboard performance only. Audio is produced and recorded by Zen Piano.
import Foundation
import AppKit
import ApplicationServices

struct Note: Decodable { let timestamp: Double; let duration: Double; let key: String?; let note: String? }
struct Score: Decodable { let time_unit: String; let notes: [Note] }
struct Event { let time: Double; let key: Character; let down: Bool }
func fail(_ message: String) -> Never { fputs("Error: \(message)\n", stderr); exit(2) }
let args = CommandLine.arguments
guard args.count == 3 || (args.count == 4 && args[3] == "--dry-run") else {
    fail("Usage: zen_key_events_macos PLAN.json CHROME_PID [--dry-run]")
}
guard let pid = Int32(args[2]), pid > 0 else { fail("PID must be a positive integer") }
let score: Score
do { score = try JSONDecoder().decode(Score.self, from: Data(contentsOf: URL(fileURLWithPath:args[1]))) }
catch { fail("Cannot read plan: \(error)") }
guard ["seconds", "milliseconds"].contains(score.time_unit) else { fail("Explicit time_unit must be seconds or milliseconds") }
guard !score.notes.isEmpty else { fail("The plan contains no notes") }
let divisor = score.time_unit == "milliseconds" ? 1000.0 : 1.0
let whites = Array("1234567890qwertyuiopasdfghjklzxcvbnm")
let blacks = Array("!@$%^*(QWETYIOPSDGHJLZCVB")
let pitchClasses = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
var noteKeys: [String: Character] = [:]; var wi=0; var bi=0
for pitch in 36...96 {
    let black = [1,3,6,8,10].contains(pitch % 12)
    noteKeys[pitchClasses[pitch % 12] + String(pitch / 12 - 1)] = black ? blacks[bi] : whites[wi]
    if black { bi += 1 } else { wi += 1 }
}
let allowed = Set(noteKeys.values)
let codes: [Character: CGKeyCode] = ["1":18,"2":19,"3":20,"4":21,"5":23,"6":22,"7":26,"8":28,"9":25,"0":29,"q":12,"w":13,"e":14,"r":15,"t":17,"y":16,"u":32,"i":34,"o":31,"p":35,"a":0,"s":1,"d":2,"f":3,"g":5,"h":4,"j":38,"k":40,"l":37,"z":6,"x":7,"c":8,"v":9,"b":11,"n":45,"m":46]
let symbols: [Character: Character] = ["!":"1","@":"2","$":"4","%":"5","^":"6","*":"8","(":"9"]
var events: [Event] = []; var spans: [Character: [(Double,Double)]] = [:]
for n in score.notes {
    let start=n.timestamp/divisor; let duration=n.duration/divisor
    guard start.isFinite, duration.isFinite, start >= 0, duration > 0, (start+duration).isFinite else { fail("Invalid note timing") }
    let key: Character
    if let k=n.key, k.count == 1, let c=k.first, allowed.contains(c) { key=c }
    else if let name=n.note, let c=noteKeys[name] { key=c }
    else { fail("Unknown or out-of-range note; inspect the current keyboard and identify any octave adaptation") }
    events.append(Event(time:start,key:key,down:true)); events.append(Event(time:start+duration,key:key,down:false))
    spans[key,default:[]].append((start,start+duration))
}
for (key, intervals) in spans {
    let ordered=intervals.sorted {$0.0 < $1.0}
    for (a,b) in zip(ordered,ordered.dropFirst()) where a.1 > b.0 + 0.000001 {
        fail("Overlapping events for key \(key); resolve the intended re-articulation in the plan before playing")
    }
}
events.sort { $0.time == $1.time ? (!$0.down && $1.down) : $0.time < $1.time }
print("Validated \(score.notes.count) notes; key release ends at \(events.last!.time) seconds")
if args.count == 4 { exit(0) }
guard AXIsProcessTrusted(), CGPreflightPostEventAccess() else { fail("Native keyboard-event permission is unavailable; do not send keys") }
guard let app=NSRunningApplication(processIdentifier:pid), app.bundleIdentifier == "com.google.Chrome" else { fail("PID is not a running Google Chrome process") }
// The caller must select the exact verified piano tab in this process first.
// Targeting the PID prevents keystrokes from landing in Codex when focus changes.
let source=CGEventSource(stateID:.hidSystemState)
let start=ProcessInfo.processInfo.systemUptime
print("PERFORMANCE_START \(Date().timeIntervalSince1970)"); fflush(stdout)
for e in events {
    let delay=start+e.time-ProcessInfo.processInfo.systemUptime
    if delay > 0 { Thread.sleep(forTimeInterval:delay) }
    let lower=Character(String(e.key).lowercased()); let base=symbols[e.key] ?? lower
    let event=CGEvent(keyboardEventSource:source,virtualKey:codes[base]!,keyDown:e.down)!
    event.flags = (e.key != lower || symbols[e.key] != nil) ? .maskShift : []
    // Explicit characters are necessary for black keys such as '(' on the tested setup.
    var units=Array(String(e.key).utf16)
    event.keyboardSetUnicodeString(stringLength:units.count,unicodeString:&units)
    event.postToPid(pid)
}
print("PERFORMANCE_END \(Date().timeIntervalSince1970)"); fflush(stdout)
