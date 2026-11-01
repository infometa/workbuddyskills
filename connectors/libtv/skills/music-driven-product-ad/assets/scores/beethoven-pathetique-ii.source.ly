\version "2.14.2"

\header {
 title = "Sonata No. 8 \"Pathétique\""
 subtitle = "2nd Movement"
 composer = "L. van Beethoven"
 opus = "Op. 13"
 piece = "Adagio cantabile"

 mutopiatitle = "Sonata No. 8 “Pathétique” (2nd Movement: Adagio cantabile)"
 mutopiacomposer = "BeethovenLv"
 mutopiainstrument = "Piano"
 source = "Berners, 1908 (edited by A. Winterberger); Peters, 1910"
 
 % Chris Sawer (2003):
 % I haven't typeset all of Winterberger's additions, by a long way - no
 % fingering is included, and much of the phrasing, dynamics and performance
 % directions have also been omitted.
 
 % Javier Ruiz-Alma (6-Sep-2011):
 % updated lilypond source to version 2.14.2
 % fingering, addt'l dynamics, and reformatting to accomodate updates.
 % Source: Köhler & Ruthardt, Edition Peters, 1910. IMSLP#30364.
 
 style = "Classical"
 copyright = "Public Domain"

 filename = "pathetique-2.ly"
 maintainer = "Chris Sawer"
 maintainerEmail = "chris@mutopiaproject.org"
 maintainerWeb = "http://cjsawer.whitewillow.co.uk/"

 footer = "Mutopia-2011/10/25-295"
 tagline = \markup { \override #'(box-padding . 1.0) \override #'(baseline-skip . 2.7) \box \center-column { \small \line { Sheet music from \with-url #"http://www.MutopiaProject.org" \line { \teeny www. \hspace #-1.0 MutopiaProject \hspace #-1.0 \teeny .org \hspace #0.5 } • \hspace #0.5 \italic Free to download, with the \italic freedom to distribute, modify and perform. } \line { \small \line { Typeset using \with-url #"http://www.LilyPond.org" \line { \teeny www. \hspace #-1.0 LilyPond \hspace #-1.0 \teeny .org } by \maintainer \hspace #-1.0 . \hspace #0.5 Reference: \footer } } \line { \teeny \line { This sheet music has been placed in the public domain by the typesetter, for details see: \hspace #-0.5 \with-url #"http://creativecommons.org/licenses/publicdomain" http://creativecommons.org/licenses/publicdomain } } } }
}

\paper{
	%#(set-paper-size "a4")      %uncomment to test specific paper size
	%#(set-paper-size "letter")  %uncomment to test specific paper size
	  top-margin = 8\mm
	  bottom-margin = 8\mm
	  ragged-last-bottom = ##f
	  print-first-page-number = ##t
	  evenHeaderMarkup = \oddHeaderMarkup %force pages to have same header (i.e. page number to right)
}

%Command shortcuts
hideTempo = \set Score.tempoHideNote = ##t
fingerLeft = \set fingeringOrientations = #'(left)
fingerRight = \set fingeringOrientations = #'(right)
fingerUp = \set fingeringOrientations = #'(up)
fingerDown = \set fingeringOrientations = #'(down)
fingerUpDown = \set fingeringOrientations = #'(up down)
allowScriptUnderSlur = {
	\once \override TextScript #'avoid-slur = #'inside
	\once \override TextScript #'outside-staff-priority = ##f}
lengthenStems = \override Stem #'(details beamed-lengths) = #'(5)
revertStemLenghts = \revert Stem #'(details beamed-lengths)
hideTupletNumber = \override TupletNumber #'stencil = ##f
unhideTupletNumber = \revert TupletNumber #'stencil 
hideTupletBracket = \override TupletBracket #'bracket-visibility = ##f


topmain = \relative c' {

 \key as \major
 \time 2/4
 \tempo 4=36 \hideTempo
 \clef bass
 \stemUp
 
 <c-4>4( <bes-3> |\noBreak			%1
  es4. <des-4>8) |\noBreak
  <c-3>[( <es-4> as  bes)] |\noBreak
  es,4.-3( <e-4>8 |
  f4) <bes,^2^4>8.( \lengthenStems <c-5>32  <des!-4>) \revertStemLenghts |	%5
 es!4( <a,^4> |
  des) c16^.^5( bes^. as!^.  g)^. |
 <bes g>4-3-5(  as8-4) \clef treble s |
 \fingerUp c'4( <bes-4> |			%9
 es4. <des-4>8) |
 <c-3>[( <es-4> as  bes)] |
 es,4.-3(  <e-4>8 |
  f4) \lengthenStems <bes,-4>8.( <c-5>32  <des-4>) \revertStemLenghts |	%13
 es!4( <a,-4> |
  des) c16^5^.( bes^4^. as!^4^.  g^3)^. |
 <bes-5>4(  <as-4>8) b16.\rest c,32 |
\stemNeutral
c'4^\markup{\finger "5-1"}~ c16( as'-4 g  f-2) |		%17
 c'4 ~ c16( <as-4> g  f-2) |
 c4 ~ c16( as'-4 g  f-1) |
 <es-2>8(  d)~  
 \allowScriptUnderSlur
 d8[(^\markup \tiny \override #'(baseline-skip . 1) {
    \halign #-4
    \center-column {
      \musicglyph #"scripts.turn"
      	 }}^\markup{\halign #-2 \finger "3212"} 
 f16.-4  es32)] |
 es4^4  
 <f,^1>8.[_(^\markup{ 
  	\halign #-3  \center-column {
  		\general-align #Y #0.2 \finger "4321"
		\general-align #Y #-2 \tiny \musicglyph #"scripts.turn"
		\general-align #Y #-3 \teeny \natural	}
       }  as32^2  c_)] |		%21
 \grace {\stemUp \scaleDurations #' (1 . 6) {b16[_(^1 c^2 d_)^4] } \stemNeutral}
 c32(^3 bes!)^2 g'16(~^5 g f32 es \stemDown d![ c bes^3 a c bes as  f)]^1 |
 \stemNeutral es8-2 b'16\rest \clef bass bes,-3( g-1 bes-4 g-2  es-1) |
 \stemUp <as f>8[ <as f>^3^5 <as f>^4^5 <as f d>^3^4^5] |
 s8*3 \stemDown bes16.-2(  es32-4) \stemUp |			%25
 es16-5(  d) d-5(  c) c-5(  ces) ces-5(  bes-3)|
 <bes g>2~^4^5 |
 <bes^5 g^4> |
 <c as>4( <bes-3> |			%29
 es4.  <des-4>8) |
 <c-3>[( <es-4> as  bes)] |
 \fingerUp <es,-3>4.( <e-4>8 |
  f4) \lengthenStems <bes,^2^4>8.( <c-5>32  <des!-4>) \revertStemLenghts|	%33
 es!4( \fingerUp <a,-2-4> |
  des)  <c-5>16^.( bes^. as!^.  g)^. |
 <bes-5 g-3>4(  as8-4)\noBeam \clef treble <es'-2> |
 \lengthenStems <as-4>[( ces \allowScriptUnderSlur bes^\markup{\vspace #1 \finger "4-5"}  <as-4>)] \revertStemLenghts |	%37
 <g-3>(  des') r4 |
  \lengthenStems as8[( ces \allowScriptUnderSlur bes^\markup{\vspace #1 \finger "4-5"}  <as-4>)] \revertStemLenghts |
   as-5(  g-4) d'4\rest |
   \lengthenStems <as-4>8[( ces \allowScriptUnderSlur bes^\markup{\vspace #1 \finger "4-5"}  <as-4>)] \revertStemLenghts|		%41
 \stemNeutral
  
 <fis' fis,>-5~\sf \times 2/3 {  fis16[ <dis-4>-. <b-2>-.] } <b' b,>8~\sf \times 2/3 {  b16[ <gis-4>-. <e-2>-.] } |
 \hideTupletNumber \hideTupletBracket
 <e'e,>8~\sf \times 2/3 {  e16[ <cis-4>-. <ais-3>-.] } <b b,>8-.\noBeam \clef bass <dis,, b a fis>-. |
 \times 2/3 { <e-5  b-3 gis-2>16[\fp <b-2 gis-1> <b gis>] <b gis>[ <b gis> <b gis>]
   <b gis>[_\markup{\vspace #.5 \italic "decresc."} <b gis> <b gis>] <b gis>[ <b gis> <b gis>] } | \noBreak
 \stemUp
 e8-4[( gis \allowScriptUnderSlur fis^\markup{\vspace #-1.9 \finger "4-5"}  e-4)] |		%45
 <dis^3>(  a') r4 |
  <e-4>8[( gis <e-4>  <dis-3>)] |
 <d-4-5>4. d8 |
 d4. d8 |			%49
 des!4. des8 |
 c!4( <bes-3> |
 es4.  <des-4>8) |
  <c-3>[( <es-4> as  bes)] |		%53
 <es,-3>4.( <e-4>8 |
  \lengthenStems f4) <bes,-4>8.( <c-5>32  <des-4>) \revertStemLenghts|
 es4( <a,-4> |
  des) \times 2/3 {  des16-5[(  c-4) bes-3-.]  bes-4[(  as!) g-.] } |	%57
 <bes-5 g-3>4(  as8-4) \clef treble s |
 c'4( <bes-4> |
 es4.  <des-4>8) |
  <c-3>[( <es-4> as  bes)] |					%61
 <es,-3>4.( <e-4>8 |
  f4) \lengthenStems <bes,-2-4>8.( <c-5>32  <des-4>) \revertStemLenghts|
 es4( <a,-4> |
  des) \times 2/3 {des16^5[( c^4) bes^3-.]  bes^5[(  as!) g-.] } |	%65
 \stemNeutral
 \slurNeutral
 \tieNeutral
 <as  c,>8 b\rest b\rest <es-2>16.(  e32) |
 f8~_\< \times 2/3 {  f16[(  es!) des-.(]  c[-._\! bes-.^3_\>  as)-.] }  g32[( des' bes  g)]_\! |
  %\allowScriptUnderSlur
  as16.-2([^\markup \tiny  \override #'(baseline-skip . 1) {
    \halign #-2  \center-column { 
    	 \finger "3213"
	 \musicglyph #"scripts.turn"}}
  c32^5]  es,8^1) r <es'' es,>16.-4( <e e,>32) |
 <f f,>8~ \times 2/3 { <f f,>16[( <es! es,!>-4) <des des,>-4-.(]
   <c c,>[-. <bes bes,>-4-. <as as,>-4)-.] <g g,-5>[( <des'-4 des,> <g,-5 g,>)] } |	%69
   <as as,>8-4 b,\rest \grace{ \override Stem  #'stroke-style = #"grace" {\stemUp es8^3_(_\markup{\dynamic rf} \stemNeutral}
   \revert Stem #'stroke-style }
   \unhideTupletNumber
   \times 2/3 {des16)[( c  des)]} \times 2/3{ f[(  es) des-.] } \hideTupletNumber|
 c8 b\rest \stemUp \grace {
\override Stem   #'stroke-style = #"grace"
   c8^4( 
  \revert Stem #'stroke-style }
 \times 2/3 {
     bes16)[_\markup{ \dynamic rf}( a  bes)]  des[(  c) bes_.] } |
 s4 \clef bass \grace {
\override Stem   #'stroke-style = #"grace"
   c,8^4( 
  \revert Stem #'stroke-style }
 \times 2/3 {
     bes16)[_\markup{\dynamic rf}( a  bes)]  des[(  c) bes_.] } |
 \stemDown
 as!16 \pp d,\rest <as'^4 es c> d,\rest \fingerLeft <as'-5 c, as>4^\markup{" "}^\fermata \bar "|."		%73
}

topsecondary =  \relative c' {
 \set Voice.tupletNumberFormatFunction = #'()
 \stemDown
 as16 \p es as es g es g es |		%1
 as es as es bes'-3 es, bes'-2 es, |
 as es bes' es, c' as d as |
 g bes g bes g bes g bes |
 g bes_2 g bes_3 g es g es |		%5
 as es as es es_2 c es c |
 f des f des des des des des |
 des( es des  es)

  \hideTupletBracket
  \unhideTupletNumber
 \times 2/3 { c[^. es^. as^.] }
 \times 2/3 { \stemNeutral \hideTupletNumber
 c^\markup{\finger 1}[-. es-. as-.] \stemDown }
 c,16 es c es bes es bes es |		%9
 es as es as es bes'-2 es, bes' |
 es, as es bes' as c as d-2 |
 g, bes g bes g bes g bes |
 g bes_2 g bes_3 g es g es |		%13
 as es as es es c es c |
 f des f des des des des des |
 des es des es c8 s |
 s2*7					%17 - 23
 es,16(_2_\markup{\vspace #.5 \italic "cresc."}  d) d_2(  c) c_2(  b)_\markup{\italic "(m.s.)"} b_2(  bes_1) |
 <g' es bes>8^\markup{\finger 2}^\markup{\finger 4}^\markup{\finger 5} e\rest e\rest s |		%25
 <as f>4_\markup{\vspace #.5 \italic "cresc."} <as f> |
 f16-2(_\p  fes-1)^\< fes-2(  es-1) es-2(  d) d-2(  es-3)^\! |
 es_2(  <fes^1>)^\> <fes^2>(  <es^1>) <es^2>(_\markup{\dynamic "pp"}  <d^1>) <d^2>(  <des^1>)^\! |
 \fingerUp c( \p es <as-3> <es-1>) g( es g  es) |		%29
 as es as es bes'-3 es, bes'-2 es, |
 as es bes' es, c' as d as |
 g bes g bes g bes g bes |
 g <bes_2> g <bes_3> g es g es |		%33
 as es as es es c es c |
 f des f des des des des des |
 des es des es c8 r |
  \unhideTupletNumber
 \times 2/3 { <es'  ces>16[\pp <es ces> <es ces>]} 
 \times 2/3 {<es ces>[ <es ces> <es ces>]}
 \times 2/3 {<es ces>[ <es ces> <es ces>]}
 \times 2/3 { <es ces>[ <es ces> <es ces>]} |		%37
  \hideTupletNumber
  \times 2/3 {
  <es des>[ <es des> <es des>] <es des>[ <es des> <es des>]
    <es des>[ <es des> <es des>] <es des>[ <es des> <es des>] |
  <es ces>[ <es ces> <es ces>] <es ces>[ <es ces> <es ces>]
    <es ces>[ <es ces> <es ces>] <es ces>[ <es ces> <es ces>] |
  <es bes>[ <es bes> <es bes>] <es bes>[ <es bes> <es bes>]
    <es bes g>[ <es bes g> <es bes g>] <es bes g>[ <es bes g> <es bes g>] |
  <es ces>[ <es ces> <es ces>] <es ces>[_\markup{\vspace #.5 \italic "cresc."} <es ces> <es ces>]
    <es ces>[ <es ces> <es ces>] <es ces>[ <es ces> <es ces>] |		%41
 }
 s2*3 |
 \times 2/3 {
  <b  gis>16[\pp <b gis> <b gis>] <b gis>[ <b gis> <b gis>]
    <b gis>[ <b gis> <b gis>] <b gis>[ <b gis> <b gis>] | \noBreak	%45
  <b a>[ <b a> <b a>] <b a>[ <b a> <b a>]
    <b a>[ <b a> <b a>] <b a>[ <b a> <b a>] |
  <b gis>[ <b gis> <b gis>] <b gis>[ <b gis> <b gis>]
    <b gis>[ <b gis> <b gis>] <b gis>[ <b gis> <b gis>] | \noBreak
  <ces as! d,>[ <ces as d,> <ces as d,>] <ces as d,>[ <ces as d,> <ces as d,>]
    <ces as d,>[ <ces as d,> <ces as d,>] <ces as d,>[ <ces as d,> <ces as d,>] | \noBreak
  <ces as d,>[ <ces as d,> <ces as d,>] <ces as d,>[ <ces as d,> <ces as d,>]
    <ces as d,>[ <ces as d,> <ces as d,>] <ces as d,>[ <ces as d,> <ces as d,>] |	%49
  
  <bes! as des,!>[_\markup{\vspace #.8 \italic "cresc."} <bes as des,> <bes as des,>]
    <bes as des,>[ <bes as des,> <bes as des,>]
    <bes g des>[ <bes g des> <bes g des>] <bes g es des>[ <bes g es des> <bes g es des>] |
   c,![(\p  <es-2>)_. <es-1>_.]  <as-3>[(  <es-2>)_. <es-1>_.]  g[(  es)_. es_.]  g[(  es)_. es_.] |
   as[(  es)_. es_.]  as[(  es)_. es_.]  <bes'-3>[(  es,)_. es_.] 
   \once \override Fingering #'staff-padding = #'()
   <bes'_2>[(  es,)_. es_.] |
   as[(  es)_. es_.]  bes'[(  es,)_. es_.]  c'[(  as)_. as_.]  d[(  as)_. as_.] |	%53
   g[(  bes)_. bes_.]  g[(  bes)_. bes_.]  g[(  bes)_. bes_.]  g[(  bes)_. bes_.] |
   g[(  bes) bes]  g[(  <bes-2>) <bes-3>]  g_2[(  es) es]  g[(  es) es] |
   as[(  es) es]  as[(  es) es]  es[(  c) c]  es[(  c) c] |
   f[(  des) des]  f[(  des) des]  g[(  des) des]  des[(  des) des] |			%57
   des[(  es) es]  des[(  es) es]  c[^. es^. as^.] \stemNeutral  <c^1>[-. es-. as-.] \stemDown |
   c,[(  es) es]  c[(  es) es]  bes[(  es) es]  bes[(  es) es] |
   es[(  as) as]  es[(  as) as]  es[(  <bes'-3>) <bes-2>]  es,[(  bes') bes] |
   es,[(  as) as]  es[(  bes') bes]  as[(  c) c]  as[(  d) d] |			%61
   g,[(  bes) bes]  g[(  bes) bes]  g[(  bes) bes]  g[(  bes) bes] |
   g[(  bes) bes]  g[(  <bes^2>) <bes^3>]  g[(  es) es]  g[(  es) es] |
   as[(  es) es]  as[(  es) es]  es[(  c) c]  es[(  c) c] |
   f[(  des) des]  f[(  des) des]  g[(  des) des]  des[( des) des] |		%65
 }
 s2*5									%66 - %70
 s4 g4( |
  \stemNeutral  as!8) b\rest \stemDown g,4 |
 
 \stemNeutral
}


bottom = \relative c {
 \hideTupletNumber
 \hideTupletBracket
 \key as \major
 \time 2/4
 \clef bass
 
 as4_4( des_2 |		%1
 c_1  g_4) |
  as8[( g f  f')] |
  es4(^\markup{\finger "2-1"} es,^4 |
 des!  des')^\markup{\finger "1-2"} |		%5
 c^1( f,^2 |
 bes,^5  es)^2 |
 as,8 as' as, r |
 << {
  as''16 es as es g es g es |	%9 (1)
  as es as es g es g es |
  as es g es f \fingerDown <as,-4> f' <as,-3> |
 } \\ {
  \fingerDown 
  as4( <des-3> |			%9 (2)
  <c-4>  g) |
 <as-4>8[( g  f) f] |
 } >>
 es16( \fingerDown <g-4> <bes-2> <es-1> \fingerUp <g-2> bes g  bes) |
 \fingerDown <des,,-5>( <g-3> bes <des-1> \fingerUp <g-2> bes g  <des-4>) | %13
 << {
 \fingerDown c16 <es-2> <c-3> <es-1> c f c f |
  des f des f bes, es bes es |
  r es g es as8 r |
 } \\ {
  \fingerDown <c,-5>4 f,( |
  <bes-3>  es,) |
  <as-5>4. r8 |
 } >>
 r16 c'^3 c^2 c^1 c^2 c^1 c^2 c^1 |		%17
 <c g e>_5 <c g e> <c g e> <c g e> <c as f>_4 <c as f> <c as f> <c as f> |
 <e bes g>_5 <e bes g> <e bes g> <e bes g> <f c as>_4 <f c as> <f c as> <f c as> \clef treble |
 <as f bes,> <as f bes,> <as f bes,> <as f bes,> <as f b,> <as f b,> <as d, b>_3_5 <as d, b> |
 <g es c>_4 <g es c> <g es c> <g es c> <es as,>^2 <es as,> <es as,> <es as,> |		%21
 r <g es bes>_4 <g es bes> <g es bes> r \clef bass <as, d, bes> <as d, bes> <as d, bes> |
 <g es>8_1_2 r r4 |
 bes,,2_4 |
 <es_2>8 r16 bes'_1( g_2 bes g  es_3) |	%25
 bes4 bes' |
 es,2~_\markup{\finger "3-2"} |
 es |
 <as as,>4^\markup{\finger "1-4"}_( des^2 |		%29
 c^1  g^4) |
  as8[( g f  f')] |
 es4_(^\markup{\finger "2-1"} es,^4 |
 des  des'^\markup{\finger "1-2"}_) |			%33
 c^1( f,^2 |
 bes,  <es-2>) |
 as,8 as' as, r |
 <as'' as,>4 r |		%37
 \fingerDown bes8-2~ \unhideTupletNumber 
  \times 2/3 {bes16[ \fingerUp <bes-3>( a]} \times 2/3 {bes)[-. <bes-2>-.(  as)-.]}
  \times 2/3 {<g-1>[-.( f-. es)-.]} \hideTupletNumber|
 \fingerDown <as-1>8 r r4 |
 es8_3~ \times 2/3 {  es16[ es_2( d]   es)[-. fes-.(  es)-.]  des[-.( <ces-1>-.  bes)-.] } |
 as8 r r4 |			%41
 \times 2/3 {
  <fis' dis b a>16_5[ <fis dis b a> <fis dis b a>] <fis dis b a>[ <fis dis b a> <fis dis b a>]
    <gis e b gis>[ <gis e b gis> <gis e b gis>] <gis e b gis>[ <gis e b gis> <gis e b gis>] |
  <ais fis e cis>[ <ais fis e cis> <ais fis e cis>] <ais fis e cis>[ <ais fis e cis> <ais fis e cis>]
    <b gis e b>[ <b gis e b> <b gis e b>] <b, b,>[ <b b,> <b b,>] |
 }
 <e e,>8 r r4 |
 <e e,> r |			%45
 <fis>8_2~ \times 2/3 {  fis16[ fis^3( eis]   fis)[-. fis-2-.(  e-1)-.]  dis[-.( cis-.  b)-.] } |
 <e-1>8 r r4 |
 \times 2/3 { r16 \fingerUp <f,,!-5>[-. <as!-4>-.]  <ces-3>[-. <d-2>-. <f!-1>-.] } <as!-2>8 r |
 \times 2/3 { r16  <f,-5>[-. <as-4>-.]  ces[-. d-. <f-1>-.] } <as-2>8 r |		%49
 \times 2/3 { r16  fes_4[-. as-.] } bes!8-. \times 2/3 { r16  es,_4[-. g-.] } bes8-. |
 <as as,>4^\markup{\finger "1-4"}( des_2 |
 c_1  g_4) |
  as8[( g f  f')] |		%53
  es4(_\markup{\finger "2-1"} es,_4 |
  des  des'_\markup{\finger "1-2"}) |
 \fingerDown <c-1>( <f,-2> |
 bes,  <es-2>) |			%57
 as,8 as' as, r |
 << {
  \times 2/3 {
    \hideTupletBracket
    \hideTupletNumber
    as''16[(  es) es]  as[(  es) es]  g[(  es) es]  g[(  es) es] |
    as[(  es) es]  as[(  es) es]  g[(  es) es]  g[(  es) es] |
    as[(  es) es]  g[(  es) es]  f[(  as,) as]  f'[(  <as,_3>) <as_2>] |%61 (1)
  }
 } \\ {
  \fingerDown
  as4( <des-3> |
  <c-4> g) |
   as8[( g  f) f] |		% 61 (2)
 } >>
 \times 2/3 {  es16[-. <g-4>-. bes-.]  <es^1>[-. <g^4>-. bes-.] } <es^1>4 |
 \times 2/3 {  <des,,-5>16[-. <g-3>-. bes-.]  <des^1>[-. <g^3>-. bes-.] } des4^\markup{\finger "1-2"} |
 <c^1>( \allowScriptUnderSlur f,^\markup{\finger "3-1"} |
  <bes,_3>) << { \times 2/3 { 
  \hideTupletBracket
  \hideTupletNumber
 bes16[(  es) es]  es,[(  es') es] } } \\ { es,8 es } >> |	%65
  \hideTupletNumber
 \times 2/3 {
 \stemDown as16_3[ es'_1-.(^\markup{\vspace #-.3 \halign #0.7 \dynamic "pp"}  es_2)-.]
 \stemNeutral es_3[-.( es_2-.  es_1)-.]  es_3[ es_2 es_1]  es[ es es] |
  <es des es,>[ <es des es,> <es des es,>] <es des es,>[ <es des es,> <es des es,>]
    <es des es,>[ <es des es,> <es des es,>] <es des es,>[ <es des es,> <es des es,>] |
  \stemDown <es c as>[_4 es-._1(  es)_2-.] \stemNeutral es[-._3( es-._2  es)-._1]  es_3[ es_2 es_1]  es[ es es] |
  <es des es,>[^\< <es des es,> <es des es,>] <es des es,>[ <es des es,> <es des es,>]_\!
    <es des es,>[^\> <es des es,> <es des es,>] <es des es,>[ <es des es,> <es des es,>]\! |	%69
 }
 <es c as>8_4 r \clef treble <g' es>4_1_2( \hideTupletNumber|
 <as as,>8 r) \clef bass <des, es,>4^1_( |
 <c^2 as_3>8) r <des,^1 es,>4_( |
 <c^2 as_3>16 r) as,_4 r \fingerLeft <as-5>4_\markup{" "}_\fermata \bar "|."	%73
}

\score {
	  \context PianoStaff <<
		  \context Staff = "up" <<
		   \set Staff.midiInstrument = #"acoustic grand"
		   \context Voice = VA { \voiceOne \topmain }
		   \context Voice = VB { \voiceTwo \topsecondary }
		   >>
	  \context Staff = "down" <<
		   \set Staff.midiInstrument = #"acoustic grand"
		   \bottom
		   >>
	  >>
	 \layout{}
	 \midi {  
		 \context{
		 	 \Voice
		 	 	\remove "Dynamic_performer"
		 }
	}
}
