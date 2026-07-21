# Common Visual Contract

## WorkBuddy inline visual gate

Use an inline visual only when the current runtime exposes both `read_me` and `show_widget`.

1. Before the first visual call in the turn, call `read_me` with the `chart` module. Do not narrate this internal step.
2. Call `show_widget` with a specific Chinese title, a raw self-contained SVG or HTML fragment, and one to four short Chinese loading messages.
3. Keep the interpretation, evidence window, source and limitations in ordinary answer text beside the visual.

For the packaged numeric templates, `widget_code` must begin directly with `<svg` and end with `</script>`. Never wrap it in `<![CDATA[` / `]]>`, a Markdown code fence, an XML document, or an HTML document wrapper; WorkBuddy renders those wrappers as visible stray text.

If either tool is absent, choose the cross-client fallback. Do not ask the user to install a rendering tool and do not emit an unrendered code fence.

## Direct Widget path

For candlestick, line and event-return charts, load `references/widget-svg-runtime.md`, select exactly one family template, and use that template only.

1. Build one validated `chart-evidence/1` JSON payload from the current evidence.
2. Replace only `__TONGZHOU_CHART_PAYLOAD__` inside the selected template code block. Escape string values as JSON; do not add executable user text.
3. Pass the completed fragment directly in the `show_widget` call.

After the evidence bundle and packaged references are loaded, do not use Bash, Write, Edit, Python, Node CLI, heredoc or a temporary JSON/SVG/PNG/HTML file to render the chart. Do not hand-expand candles, bars, coordinates or moving-average paths in the tool arguments. The inline runtime performs those deterministic transforms inside the Widget.

## Fallback first

Prepare the summary and compact table from the normalized evidence before calling a visual tool. A visual tool unavailable state or render error changes only the presentation:

- Continue with the existing evidence answer.
- Do not repeat business-data calls just to redraw.
- Retry the same visual at most once when the failure is a correctable validation error.
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
- Use stable dimensions. A WorkBuddy raw SVG uses the host-required `viewBox="0 0 680 340"`, sets `display:block;width:100%;height:340px`, and keeps every plot band, axis, legend and note inside that visible content height. Do not rely on the SVG's natural aspect ratio because the host widget clips taller content.
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
