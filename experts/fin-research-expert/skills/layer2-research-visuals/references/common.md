# Common Visual Contract

## Host presentation gate

First check whether the current real tool result is already displayed through a negotiated MCP App. If it is, keep that App and do not call `show_widget` for the same evidence. A linked viewpoint App is the list/detail interaction surface; Widget does not recreate its navigation.

## WorkBuddy inline visual gate

Use an inline visual only when no MCP App already renders the result and the current runtime exposes both `read_me` and `show_widget`.

1. Before the first visual call in the turn, call `read_me` with the `chart` module. Do not narrate this internal step.
2. Call `show_widget` with a specific Chinese title, a raw self-contained SVG or HTML fragment, and one to four short Chinese loading messages.
3. Keep the interpretation, evidence window, source and limitations in ordinary answer text beside the visual.

For the packaged numeric templates, `widget_code` must begin directly with `<svg` and end with `</script>`. Never wrap it in `<![CDATA[` / `]]>`, a Markdown code fence, an XML document, or an HTML document wrapper; WorkBuddy renders those wrappers as visible stray text.

If either tool is absent, choose the cross-client fallback. Do not ask the user to install a rendering tool and do not emit an unrendered code fence.

## Direct Widget path

For numeric charts, load `references/widget-svg-runtime.md`, select exactly one family and use the packaged deterministic renderer.

1. Build one validated `chart-evidence/1` JSON payload from the current evidence.
2. Save only that normalized payload to an ephemeral JSON input. Resolve `scripts/render_widget.mjs` relative to this Skill directory and run `node scripts/render_widget.mjs --input <payload.json>`.
3. Parse stdout as the complete `show_widget` arguments object and pass it unchanged. Never copy, shorten, repair or regenerate `widget_code` in model text.

The packaged renderer is the only allowed normal-answer rendering script. It validates JSON, isolates payload data from executable JavaScript and selects the reviewed family runtime. A non-zero exit means no Widget call: keep the prepared table/text fallback. Do not hand-expand candles, bars, coordinates or moving-average paths in tool arguments.

`__TONGZHOU_CHART_PAYLOAD__` is an internal renderer token. The model must never replace it directly; only `scripts/render_widget.mjs` may materialize that token.

Remove the ephemeral input after the call. Do not retain temporary JSON/SVG/PNG/HTML artifacts in the conversation workspace.

## Fallback first

Prepare the summary and compact table from the normalized evidence before calling a visual tool. A visual tool unavailable state or render error changes only the presentation:

- Continue with the existing evidence answer.
- Do not repeat business-data calls just to redraw.
- Retry payload normalization at most once when the renderer reports a correctable validation error.
- Do not expose widget code, validation messages, tool parameters or internal route names.
- Mention that the current client could not display the chart only when that helps answer the user's request.

## Direction and color

Follow the Chinese market convention:

- Up, positive return or positive directional value: red `#d92d20`.
- Down, negative return or negative directional value: green `#079455`.
- Unchanged, neutral or unavailable: host secondary gray.

Color is not the only signal. Keep a sign, value label, candle direction, line pattern or textual label so the chart remains understandable without color.

## No external assets

- Do not load external scripts, CSS, images or fonts inside a widget.
- Use a self-contained SVG or HTML fragment in normal document flow.
- Do not include document wrapper tags, forms, fixed positioning, local storage or session storage.
- Do not include CDATA wrappers or standalone hidden-heading CSS. SVG `<title>` and `<desc>` provide the accessibility text.
- Do not use gradients, shadows, decorative blobs or animation that distracts from the evidence.
- Do not use a raster screenshot when the same evidence can be represented as a lightweight chart.
- Do not load the packaged template as an external browser resource. Its HTML and script are copied into the self-contained Widget fragment.

## Layout and accessibility

- One visual answers one main question. Do not place a dashboard of unrelated charts in a normal answer.
- Use stable dimensions. A WorkBuddy raw SVG starts with the host-required `viewBox="0 0 680 340"`, sets `display:block;width:100%;height:340px`, and keeps every plot band, axis, legend and note inside that visible content height. The packaged v2 runtime may expand the internal coordinate width to the measured 680-1280px container while retaining the fixed height; it must not stretch text through `preserveAspectRatio="none"`. Do not rely on the SVG's natural aspect ratio because the host widget clips taller content.
- HTML chart containers use an explicit height no greater than 340px. Prefer a compact price band plus volume band over a vertically scrollable chart.
- Include an accessible description naming the subject, chart type and evidence window.
- Use readable axis labels and rounded display values without changing underlying calculations.
- Thin date labels deterministically when the series is dense; do not hide data points.
- Verify common desktop content widths around 1280px and 720px. Titles, legends, axes, values and source notes must not overlap.

## Evidence and safety

- Copy chart values only from the current validated evidence bundle.
- Do not infer missing values or calculate unsupported forecasts.
- State source type and returned dates outside the widget so they remain visible if rendering fails.
- Preserve the normal distinction between fact, interpretation and unknown items.
- End financial answers with all four elements: AI 生成、仅基于公开信息整理、不构成投资建议、不构成个股推荐。
