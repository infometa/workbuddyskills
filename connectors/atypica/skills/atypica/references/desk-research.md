# Desk research

One call that searches the web and X (Twitter) for what is already known about a question and returns a written summary. Use it for facts, trends, what people say online, or a quick overview before a study. It asks no consumers and no real people, and it produces no report page.

Tool: `atypica_desk_research({ query })` → `plainText`.

- Pass the user's question in the user's language. Leave `expert` at its default unless the user asks for a specific source.
- The call takes up to a few minutes and streams progress if the client supports it. Nothing to poll.
- Present `plainText` as what was found online, not as atypica.AI's own finding.

## When to switch mode

- How consumers would react, not what has been written → user research.
- Real people's own answers → human interview.
- The landscape before a study → desk research first, then a study.
