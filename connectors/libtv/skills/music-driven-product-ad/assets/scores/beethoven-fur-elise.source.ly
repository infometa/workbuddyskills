\version "2.18.2"

 \header {
  title = "Für Elise"
  subtitle = "Clavierstuck in A Minor - WoO 59"
  composer = "Ludwig van Beethoven"
  mutopiatitle = "Für Elise"
  mutopiacomposer = "BeethovenLv"
  mutopiaopus = "WoO 59"
  mutopiainstrument = "Piano"
  date = "1810"
  source = "Breitkopf & Härtel, 1888"
  style = "Classical"
  license = "Public Domain"
  maintainer = "Stelios Samelis"
  moreInfo = "keywords: fur elise, bagatelle no.25"

 footer = "Mutopia-2015/08/18-931"
 copyright =  \markup { \override #'(baseline-skip . 0 ) \right-column { \sans \bold \with-url #"http://www.MutopiaProject.org" { \abs-fontsize #9  "Mutopia " \concat { \abs-fontsize #12 \with-color #white \char ##x01C0 \abs-fontsize #9 "Project " } } } \override #'(baseline-skip . 0 ) \center-column { \abs-fontsize #11.9 \with-color #grey \bold { \char ##x01C0 \char ##x01C0 } } \override #'(baseline-skip . 0 ) \column { \abs-fontsize #8 \sans \concat { " Typeset using " \with-url #"http://www.lilypond.org" "LilyPond" " by " \maintainer " " \char ##x2014 " " \footer } \concat { \concat { \abs-fontsize #8 \sans{ " Placed in the " \with-url #"http://creativecommons.org/licenses/publicdomain" "public domain" " by the typesetter " \char ##x2014 " free to distribute, modify, and perform" } } \abs-fontsize #13 \with-color #white \char ##x01C0 } } }
 tagline = ##f
}

\paper {
  top-margin = 8\mm
  bottom-margin = 9\mm
  top-system-spacing.basic-distance = #12
  ragged-last-bottom = ##f
}

%----definitions
hideTupletNumber = \override TupletNumber.transparent = ##t
posPedal = \once \override SustainPedal.extra-offset = #'(0.4 . 0)
posDynTxt = \once \override DynamicText.extra-offset = #'(0.4 . 0)

\score {

 \new PianoStaff
 <<
 \new Staff = "up" {
 \clef treble
 \key a \minor
 \time 3/8
 \override Score.MetronomeMark.transparent = ##t
 \tempo 4 = 72
 \repeat volta 2 {
 \partial 8 e''16\pp^\markup { \bold "Poco moto." }
 dis'' e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' gis' b'
 c''8 r16 e'_[ e'' dis''] e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' c'' b' }
 \alternative { { a'4 } { a'8 \bar "" r16 b' \set Timing.measurePosition = #(ly:make-moment -1/8) c''16 d'' } 
 }
 \repeat volta 2 {
 e''8. g'16[ f'' e''] d''8. f'16[ e'' d''] c''8. e'16[ d'' c''] b'8 r16 e'_[ e''] r r e''[ e'''] r r dis''
 e''8 r16 dis'' e'' dis'' e''16 dis'' e'' b' d'' c''
 a'8 r16 c' e' a' b'8 r16 e' gis' b' c''8 r16 e'_[ e'' dis''] e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' c'' b'} 
 \alternative { { a'8 r16 b'[ c'' d''] } { a'8 r16 <e' c''>[ <f' c''> <e' g' c''>] } }
 

 \grace { f'16[ a'] } c''4 f''16. e''32 e''8([ d'']) bes''16. a''32 a''16( g'' f'' e'' d'' c'')
 bes'8[ a'] \appoggiatura bes'32 a'32[ g' a' bes'] c''4 d''16[ dis''] e''8. e''16[ f'' a'] c''4 d''16. b'32
 c''32[ g'' g' g''] a'[ g'' b' g''] c''[ g'' d'' g''] e''[ g'' c''' b''] a''[ g'' f'' e''] d''[ g'' f'' d'']
 c''32[ g'' g' g''] a'[ g'' b' g''] c''[ g'' d'' g''] e''[ g'' c''' b''] a''[ g'' f'' e''] d''[ g'' f'' d'']
 e''32[ f'' e'' dis''] e''[ b' e'' dis''] e''[ b' e'' dis''] e''8. b'16[ e'' dis'']
 e''8. b'16([ e'']) dis''( e'') dis''([ e'']) dis''([ e'']) dis''( e'') dis'' e'' b' d'' c''
 a'8 r16 c' e' a' b'8 r16 e' gis' b' c''8 r16 e'_[ e'' dis''] e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' c'' b'
 a'8 r16 b'16 c'' d'' e''8. g'16[ f'' e''] d''8. f'16[ e'' d''] c''8. e'16[ d'' c''] b'8 r16 e'_[( e'']) r
 r16 e''[( e''']) r r dis''( e'') r r dis''[ e'' dis''] e'' dis'' e'' b' d'' c''
 a'8 r16 c' e' a' b'8 r16 e' gis' b' c''8 r16 e' e'' dis'' e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' c'' b'

 a'8 r r <e' g' bes' cis''>4. <f' a' d''>4 <cis'' e''>16[ <d'' f''>] <gis' d'' f''>4 <gis' d'' f''>8 <a' c''! e''>4.
 <f' d''>4 <e' c''>16[ <d' b'>] <c' fis' a'>4 <c' a'>8 <c' a'>8[ <e' c''> <d' b'>] <c' a'>4.
 <e' g' bes' cis''>4. <f' a' d''>4 <cis'' e''>16[ <d'' f''>] <d'' f''>4 <d'' f''>8 <d'' f''>4.
 <g' ees''>4 <f' d''>16[ <ees' c''>] <d' f' bes'>4 <d' f' a'>8 <d' f' gis'>4 <d' f' gis'>8 <c' e'! a'>4 r8 <e' b'>8 r r
 \tupletSpan 8 
 \tuplet 3/2 { \posDynTxt a16\pp [ c' e'] a'[ c'' e''] d''[ c'' b'] \hideTupletNumber a'[ c'' e''] a''[ c''' e'''] d'''[ c''' b''] \ottava #1 \set Staff.ottavation = \markup {8}
 a''[ c''' e'''] a'''[ c'''' e''''] d''''[ c'''' b'''] bes'''[ a''' gis'''] g'''  [  \ottava #0 fis''' f'''] e'''[ dis''' d''']
 cis'''[ c''' b''] bes''[ a'' gis''] g''[ fis'' f''] }

 e''16 dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' gis' b'
 c''8 r16 e'_[ e'' dis''] e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' c'' b'
 a'8 r16 b'16 c'' d'' e''8. g'16[ f'' e''] d''8. f'16[ e'' d''] c''8. e'16[ d'' c''] b'8 r16 e'_[( e'']) r
 r16 e''[( e''']) r r dis''( e'') r r dis''[ e'' dis''] e'' dis'' e'' b' d'' c''
 a'8 r16 c' e' a' b'8 r16 e' gis' b' c''8 r16 e'_[ e'' dis''] e'' dis'' e'' b' d'' c'' a'8 r16 c' e' a' b'8 r16 e' c'' b'
 a'8 r \bar "|."
}

 \new Staff = "down" {
 \clef bass
 \key a \minor
 \time 3/8
 \repeat volta 2 {
   
 \partial 8 r8\pp R4. a,16 e a r16 r8 e,16 e gis r r8
 a,16 e a r r8 R4. a,16 e a r r8
 e,16 e gis r r8 }
 \alternative { { a,16 e a r } { a,16[ e \bar "" a16] r \set Timing.measurePosition = #(ly:make-moment -1/8) r8 } }
 \repeat volta 2 {
 c16 g c' r r8 g,16 g b r r8
 a,16 e a r r8 e,16 e e' r r \clef treble e'16_[( e'']) r r dis''[ e''] r r16 dis''[ e''] r r8 R4.
 \clef bass a,16 e a r16 r8 e,16 e gis r r8
 a,16 e a r r8 R4. a,16 e a r r8
 e,16 e gis r r8 }
 \alternative { { a,16 e a r r8 } { a,16[ e a] <bes c'>[ <a c'> <g bes c'>] } }

 f16 a c' a c' a f bes d' bes d' bes f e' <f g bes> e' <f g bes> e' f a c' a c' a f a c' a c' a e a c' a <d d'> f
 g16 e' g e' g f' \clef treble <c' e'>8 r16 <f' g'>[ <e' g'> <d' f' g'>] <c' e' g'>8 \clef bass <f a>8[ <g b>]
 \clef treble c'8 r16 <f' g'>[ <e' g'> <d' f' g'>] <c' e' g'>8 \clef bass <f a>8[ <g b>] <gis b>8 r r R4.
 R4. R4. R4. a,16 e a r16 r8 e,16 e gis r r8 a,16 e a r r8
 R4. a,16 e a r r8 e,16 e gis r r8 a,16 e a r r8
 c16 g c' r r8 g,16 g b r r8 a,16 e a r r8 e,16 e e' r r
 \clef treble e'16(_[ e'']) r r dis''([ e'']) r r dis''([ e'']) r r8 R4.
 \clef bass a,16 e a r16 r8 e,16 e gis r r8 a,16 e a r r8 R4. a,16 e a r r8 e,16 e gis r r8

 a,16 a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a,
 <d, a,> <d, a,> <d, a,> <d, a,> <d, a,> <d, a,> <dis, a,> <dis, a,> <dis, a,> <dis, a,> <dis, a,> <dis, a,>
 <e, a,> <e, a,> <e, a,> <e, a,> <e, gis,> <e, gis,> <a,, a,> a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a, a,
 bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes, bes,
 b,! b, b, b, b, b, c4 r8 <e gis>8 r r
 a,,8 r <a c' e'> <a c' e'> r <a c' e'> <a c' e'> r <a c' e'> <a c' e'> r r R4.

 R4. a,16 e a r r8 e,16 e gis r r8
 a,16 e a r r8 R4.
 a,16 e a r r8 e,16 e gis r r8 a,16 e a r r8
 c16 g c' r r8 g,16 g b r r8
 a,16 e a r r8 e,16 e( e') r r
 \clef treble e'16(_[ e'']) r r dis''([ e'']) r r dis''([ e'']) r r8 R4.
 \clef bass a,16 e a r16 r8 e,16 e gis r r8 a,16 e a r r8 R4.
 a,16  e a r r8 e,16  e gis r r8  <a,, a,>8 r \bar  "|."
}

\new Dynamics = "pedalOne" {
  \repeat volta 2 {
  \partial 8  s8
    s4.
    s4\sustainOn s16. s32\sustainOff
    \posPedal s4\sustainOn s16. s32\sustainOff
    \posPedal s4\sustainOn s16. s32\sustainOff
    s4.
    s4\sustainOn s16. s32\sustainOff
    \posPedal s4\sustainOn s16. s32\sustainOff
  }
  \alternative{ { s4 } { s4. } }
  \repeat volta 2 {
    s4\sustainOn s16. s32\sustainOff
    \posPedal s4\sustainOn s16. s32\sustainOff
    s4.\sustainOn
    s4.
    s4 s16. s32\sustainOff
    s4.
    s4.
    s4\sustainOn s16. s32\sustainOff
    s4\sustainOn s16. s32\sustainOff
    \posPedal s4\sustainOn s16. s32\sustainOff
    s4.
    s4\sustainOn s16. s32\sustainOff
    s4.
  }
  \alternative { { s4. }  { s4. } }
  \repeat unfold 17 { s4. }
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  s4.
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  s4.
  s4\sustainOn s16. s32\sustainOff
  s4.
  s4.
  s4.\sustainOn
  s4 s16. s32\sustainOff
  \repeat unfold 26 { s4. }
  s4.\sustainOn
  \repeat unfold 3 { s4. }
  s4 s16. s32\sustainOff
  s4.
  s4\sustainOn s16. s32\sustainOff
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  s4.
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  s4.
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  \posPedal s4.\sustainOn
  s4 s16. s32\sustainOff
  s4.
  s4.
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  s4.
  s4.
  s4\sustainOn s16. s32\sustainOff
  \posPedal s4\sustainOn s16. s32\sustainOff
  s4
}
>>

 \layout { }

 \midi { }

}
