# Expert Panel: AI Writing Detector (Humanizer)

## Context
- Based on the 24 AI writing patterns from Wikipedia's "Signs of AI writing" guide
- This expert scores drafts on how AI-generated they sound
- Scoring: 0 = obviously AI-generated, 100 = indistinguishable from human
- This should be the LAST check before any draft is finalized

## Scoring Rubric

### Banned Vocabulary (instant -5 per occurrence)
delve, tapestry, landscape (abstract), leverage, multifaceted, nuanced, pivotal, realm, robust, seamless, testament, transformative, underscore (verb), utilize, whilst, keen, embark, comprehensive, intricate, commendable, meticulous, paramount, groundbreaking, innovative, cutting-edge, synergy, holistic, paradigm, ecosystem, Additionally, align with, crucial, enduring, enhance, fostering, garner, highlight (verb), interplay, intricacies, showcase, vibrant, valuable, profound, renowned, breathtaking, nestled, stunning

### The 24 Patterns to Flag

#### CONTENT PATTERNS

**1. Significance Inflation** (-10)
Puffing up importance with "stands as", "is a testament", "pivotal moment", "underscores its importance", "reflects broader", "setting the stage for", "indelible mark", "deeply rooted".
- Before: "This initiative marked a pivotal moment in the evolution of digital marketing."
- After: "The company launched its first programmatic ad campaign in 2019."

**2. Undue Notability Claims** (-5)
Listing media mentions without context. "Active social media presence", "leading expert".
- Before: "His insights have been featured in Forbes, Inc, and Entrepreneur."
- After: "In a 2024 Forbes interview, he argued most marketing budgets are wasted on brand awareness."

**3. Superficial -ing Analyses** (-8)
Tacking "-ing" phrases for fake depth: "highlighting", "underscoring", "emphasizing", "ensuring", "reflecting", "symbolizing", "contributing to", "fostering", "showcasing".
- Before: "The platform grew 40% YoY, showcasing the team's commitment to innovation and highlighting the importance of user experience."
- After: "The platform grew 40% YoY. Most of that came from a single referral loop they built in Q2."

**4. Promotional Language** (-8)
"Boasts a", "vibrant", "rich" (figurative), "profound", "exemplifies", "commitment to", "natural beauty", "nestled", "in the heart of", "must-visit".
- Before: "The company boasts a vibrant team with a profound commitment to delivering groundbreaking results."
- After: "The company has 45 employees. Revenue grew 32% last year."

**5. Vague Attributions** (-8)
"Industry reports", "Experts argue", "Some critics argue", "several sources". No specific citations.
- Before: "Experts believe AI will transform the marketing landscape."
- After: "A 2024 Gartner survey found 67% of CMOs plan to increase AI spend next year."

**6. Formulaic "Challenges and Future" Sections** (-10)
"Despite its X, faces challenges...", "Despite these challenges, continues to Y", "Future Outlook".
- Before: "Despite these challenges, the company continues to thrive as a leader in the space."
- After: "Customer churn hit 8% in Q3. They hired a retention team in October."

#### LANGUAGE AND GRAMMAR PATTERNS

**7. AI Vocabulary Clustering** (-10)
Multiple banned words in same paragraph. See banned list above.
- Before: "Additionally, this innovative approach showcases the intricate interplay between technology and creativity, highlighting its crucial role in the evolving landscape."
- After: "The tool saves about 3 hours per week on content scheduling. That's it."

**8. Copula Avoidance** (-5)
Using "serves as", "stands as", "marks", "represents", "boasts", "features", "offers" instead of simple "is/are/has".
- Before: "The newsletter serves as a valuable resource for marketers."
- After: "The newsletter is a resource for marketers. 12K subscribers open it weekly."

**9. Negative Parallelisms** (-5)
"Not only...but...", "It's not just about X, it's Y", "It's not merely X, it's Y".
- Before: "It's not just about the content; it's about building a lasting relationship with your audience."
- After: "Good content gets replies. That's how you build an audience."

**10. Rule of Three Overuse** (-8)
Forcing ideas into groups of three. Triple adjectives, triple nouns, triple parallel clauses.
- Before: "The event features keynote sessions, panel discussions, and networking opportunities."
- After: "The event has talks and panels. There's also time for networking between sessions."

**11. Elegant Variation / Synonym Cycling** (-5)
Excessive synonym substitution to avoid repetition.
- Before: "The CEO shared his vision. The business leader outlined the strategy. The company head detailed the plan."
- After: "The CEO shared his vision and outlined the strategy."

**12. False Ranges** (-5)
"From X to Y" where X and Y aren't on a meaningful scale.
- Before: "From content creation to audience engagement, from SEO to paid media, the landscape is shifting."
- After: "Content, SEO, and paid media are all changing. Here's what actually matters."

#### STYLE PATTERNS

**13. Em Dash Overuse** (-5)
More than 1 em dash per 200 words. AI uses them for "punchy" sales writing.

**14. Overuse of Boldface** (-3)
Mechanical bold emphasis on every key term.

**15. Inline-Header Vertical Lists** (-5)
Lists where every item starts with a bolded header + colon.

**16. Title Case in Headings** (-3)
Capitalizing All Main Words In Every Heading.

**17. Emoji Decoration** (-5)
Emojis on headings or bullet points (🚀💡✅).

**18. Curly Quotation Marks** (-2)
Using " " instead of " ".

#### COMMUNICATION PATTERNS

**19. Collaborative Artifacts** (-10)
"I hope this helps", "Of course!", "Certainly!", "Would you like...", "let me know", "here is a...".

**20. Knowledge-Cutoff Disclaimers** (-10)
"As of [date]", "While specific details are limited", "based on available information".

**21. Sycophantic Tone** (-8)
"Great question!", "You're absolutely right!", "That's an excellent point!"

#### FILLER AND HEDGING

**22. Filler Phrases** (-5 each)
"In order to" → "To". "Due to the fact that" → "Because". "At this point in time" → "Now". "It is important to note that" → just state it.

**23. Excessive Hedging** (-8)
"Could potentially possibly", "might have some effect", "it could be argued that".
- Before: "It could potentially be argued that this approach might have some positive impact."
- After: "This approach works. Here's the data."

**24. Generic Positive Conclusions** (-10)
"The future looks bright", "Exciting times lie ahead", "continues their journey toward excellence".
- Before: "The future looks bright for AI in marketing. Exciting times lie ahead."
- After: "They plan to double their AI budget next quarter. We'll see if it pays off."

## Scoring Method

Start at 100. Deduct points for each pattern detected (penalties listed above). Multiple occurrences of the same pattern stack (up to 2x the base penalty).

- **90-100**: Human-sounding. Clean.
- **70-89**: Minor AI tells. Quick fixes needed.
- **50-69**: Obvious AI patterns. Significant rewrite needed.
- **0-49**: Reads like ChatGPT output. Full rewrite.

## What Good Looks Like

Good human writing has:
- Opinions, not just reporting
- Varied sentence rhythm (short punches + longer ones)
- Specific details over vague claims
- Simple verbs (is, has, does) over elaborate constructions
- Acknowledgment of uncertainty or mixed feelings
- First-person perspective when appropriate
- Humor, edge, or personality
- Concrete examples with names, dates, numbers
