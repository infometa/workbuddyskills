# Music Direction

Use this reference to translate an advertising brief into a Zen Piano performance using original material or an identified repertoire arrangement. Style, rhythm, and the available instrument vary with the advertisement; the Zen Piano performance and verified WAV route remains fixed.

The final cue defaults to 20 seconds, but its tempo, meter, groove, phrasing, accent pattern, and density come from the advertising brief rather than a fixed edit grid. Short auditions develop the musical direction; derive the product release, vertical hard-edge crossings, action accents, catch, and camera stop only from the verified final performance.

## Material, Instrument, and Saved Presets

- **Original cue:** the default when the brief does not call for an existing piece. Develop a motif, harmonic movement, rhythmic identity, and ending that fit the product and audience.
- **Saved repertoire:** when requested or clearly suitable, read [repertoire.md](repertoire.md) and use the bundled `assets/scores/catalog.json` and `scripts/score_preset.py`. The library includes C大调前奏曲、小狗圆舞曲、雨滴前奏曲、裸体歌舞 No.1、致爱丽丝、婚礼进行曲、G大调小步舞曲、悲怆奏鸣曲第二乐章. Use the catalog for aliases, exact versions, tempo units, note range, source attribution, and arrangement limitations. Identify an adaptation as an adaptation and retain the selected score's recognizable melody, rhythm, and accompaniment unless a change is requested.
- **Target-duration arrangement:** choose a coherent passage and compose or arrange a compatible close with room for decay. The helper's `--seconds 20` selects an attack window; it does not by itself create a cadence or guarantee a 20-second rendered WAV. Do not rush a whole piece, loop five seconds mechanically, or cut a sounding final note merely to fill the ad duration.
- **Reference audio:** distinguish timbre, rhythmic onsets, accents, register, phrasing, and release before choosing what to emulate. State which traits are being adapted. A rough groove adaptation is not a verified note-for-note transcription.
- **Instrument:** honor the user's selection; otherwise match the brief and available Zen timbres. Grand piano, electric guitar, and electric bass are valid choices when available. Use an electronic/synth-like option only if the current UI actually offers it. Choose the instrument explicitly before applying the bundled recording workflow's fallback.
- **Smooth grand piano:** for a connected piano direction, use **三角钢琴顺滑预设** from [zen-piano-production.md](zen-piano-production.md). Read the saved control values and caveats there. Do not impose this piano sound on an electric-guitar/bass request or impose a youthful mood on a fashion/performance brief.

## Category Starting Points

| Product/ad character | Musical direction and candidate timbre | Typical BPM | Zen performance language | Rhythmic character |
|---|---|---:|---|---|
| Technology / consumer electronics | minimal-electronic or glitch-inspired; electric bass, guitar, or an available electronic timbre | 95–125 | defined attacks, low ostinato, upper motif, intentional rests, connected releases where appropriate | precise, modular, controlled acceleration |
| Sports / outdoor / performance | trap/DnB-like energy; electric bass/guitar or percussive piano | 125–155 or playable half-time | octave motion, syncopated accents, rapid figures, dynamic hits | forward drive, hard accents, short recoveries |
| Luxury / fashion / jewelry | ambient, downtempo, modern classical, or a sleek guitar/bass groove | 70–110 | spacious chord voicing, selective lead notes, controlled sustain, clear bass pulse | deliberate, spacious, selective accents |
| Beauty / skincare / wellness | organic-ambient or light-electronic; smooth grand piano or a suitable soft timbre | 75–105 | rolling broken chords, gentle lead, flowing note lengths, clear harmonic changes | fluid, tactile, low-density pulse |
| Automotive / mobility | cinematic-hybrid or techno-like drive; electric bass/guitar or weighty piano | 100–140 | persistent low pulse, widening registers, rising density, impact voicings | sustained drive, build, reveal hits |
| Food / beverage | funk/house/acoustic-pop; rhythmic guitar, bass, or piano | 100–128 | syncopated pulse, light chords, call-and-response, intentional articulation | appetizing bounce, clean syncopation, quick rewards |
| Home / furniture / architecture | warm minimal; smooth grand piano or an available warm plucked sound | 70–115 | open fifths, gentle broken chords, long breathing phrases | calm geometry, tactile micro-accents |
| Finance / professional services | understated minimal or modern classical; restrained grand piano | 80–120 | stable bass, ascending voicings, measured pulse, restrained cadence | assured, legible, progressively confident |

These are starting points, not fixed genre or instrument rules. Brand tone and the user's reference take priority; a fashion ad can need an assertive electric-bass groove rather than a soft classical cue.

## Match by Objective

- **Prestige:** reduce rhythmic density, preserve headroom, use fewer but more meaningful accents.
- **Feature proof:** use a stable pulse and clear motif so demonstrations remain legible.
- **Launch/reveal:** create withheld energy, a decisive arrival, then a controlled release.
- **Conversion/social:** reach the hook early, use readable accents, and leave space for copy or voiceover.
- **Sensory appeal:** favor texture, micro-transients, close-recorded materials, and slower harmonic change.
- **Performance:** favor propulsion, contrast, and motion-aligned accents without changing the fixed camera or introducing cuts.

## Music Director Brief

Always state:

1. genre family and 3–5 tonal adjectives;
2. BPM range and whether the tempo should feel half-time, straight, swung, or syncopated;
3. meter and groove density;
4. original material or exact saved piece/arrangement; selected available timbre, register roles, pulse, motif, voicing, note lengths, dynamics, and sustain;
5. energy curve by time or percentage;
6. major hit, break, reveal, and ending behavior with measured timestamps from the final performance;
7. negative performance constraints, such as no sentimental rubato, no dense sustain, no cheerful bounce, no harsh repeated highs, or no overfilled bass register.

## Energy Curves

- **Reveal ramp:** restrained opening → accumulating pulse → major reveal → clean brand resolve.
- **Pulse plateau:** immediate hook → steady energy → feature accents → short signature ending.
- **Contrast arc:** quiet tactile detail → sharp kinetic burst → quiet premium hold.
- **Wave arc:** alternating build and release aligned with feature groups or environments.

Do not confuse “高级感” with one genre. Premium character can come from restraint, voicing, touch, timing, dynamics, pedal control, silence, or editorial confidence.

## Five-Second Auditions and Connected Notes

For this user's iterative comparisons, start with roughly **5 seconds per version**, or their requested duration. Compare the same motif and pulse while changing a timbre or sound setting. When their feedback concerns arrangement, change voicing or note lengths deliberately. An already accepted instrument or preset can be reused; do not make every audition a new permission checkpoint.

Respond to the specific audible issue:

- **Wrong timbre / insufficient impact:** choose another available instrument, attack, register, or accent pattern before changing the tune. Preserve a reference's rhythmic identity when it is the part the user likes.
- **Dry or chopped notes:** check actual note duration, release behavior, overlapping voices, and the selected instrument's decay. Keep the bundled workflow's distinction between manual playing and autoplay Release. Do not claim a slider adjustment fixed the sound without replay evidence.
- **Thin single-note texture:** use fitting block chords or broken chords beneath the motif, with independent melody and bass durations. An electric-bass arrangement usually benefits from roots, octaves, and occasional fifths rather than dense low-register chords.
- **Muddy or rhythmically blurred texture:** reduce low-register density or overlap at harmonic changes. Connected phrasing should retain clear attacks and deliberate rests.
- **Requested transposition:** move all intended voices consistently and check the available range. Raising the key changes register and brightness; it is not a universal recipe for premium character.

Represent every note with an onset and a duration; simultaneous chord notes share their onset while voices may release at different times. Scale both onset spacing and duration when changing tempo. Use supported controls for holds, dynamics, and sustain, and inspect the resulting recording. Uniform short key taps cannot stand in for held bass notes, ties, or legato merely because the sound preset says “smooth.” Preserve the site's actual timbre by directly playing its piano keyboard; prepared note data alone is not the soundtrack. Follow the direct-performance workflow in [zen-piano-production.md](zen-piano-production.md).

After the direction is settled, develop it into a naturally structured cue lasting **D seconds** with a beginning, contrast or progression, and a fitting close. Budget the ending's decay inside the master. Use short auditions for comparison, then verify the complete recorded cue before video planning.

## Fixed Production Route

1. Match the brief to original material or an identified saved piece, an available Zen instrument, and a suitable BPM range.
2. Audition a short passage when selecting a new direction; refine timbre, chord voicing, and real note lengths from the result.
3. Compose or arrange the final playable D-second cue without forcing a fixed segment grid or visual cut interval.
4. Perform and record it at `https://zenpiano.art/play` using the bundled [Zen Piano production workflow](zen-piano-production.md) and selected sound preset.
5. Download and verify the final WAV, including duration, musical content, connected releases, rhythmic clarity, and the ending.
6. Analyze that WAV and build the final timestamp map from its real phrases, downbeats, transients, rests, and energy changes.
7. Upload that verified WAV to LibTV as the sole final music bed; retain only suitable environmental sounds from the generated video.

Do not offer soundtrack-source choices and do not generate the soundtrack in LibTV. If Zen Piano is unavailable or export cannot be verified, stop and preserve the workflow state rather than substituting another source.
