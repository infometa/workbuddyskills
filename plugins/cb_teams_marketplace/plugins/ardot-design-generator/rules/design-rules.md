---
name: design-rules
description: Single source of truth for ardot design editing — editing principles, coordinates, flexbox layout, text nodes, components/instances, colors/fills, design variables, tables, images, effects, property quick reference, troubleshooting, post-generation validation pattern, and node property schema.
metadata:
  tags: ardot, design, rules, flexbox, components, schema, validation
---

# Design Rules & Property Reference

Comprehensive rules for creating and editing .ardot designs. This is the single source of truth for editing principles, property rules, code patterns, node schema, and troubleshooting.

## Editing Principles

- After generating, validate with the schema and proceed or correct as needed.
- Use `capture_layout` and `capture_screenshot` periodically and at the end to verify design changes.
- Be thorough — make sure all task requirements are met. Verify after finishing.
- Follow `gap` and `padding` layout properties exactly on each component (buttons, tables, cards, etc.).
- If a property is not defined, treat it as 0 — do NOT hallucinate values.
- Combine multiple changes into a single tool call when possible.
- Keep each `batch_edit` call to **maximum 25 operations**. Split complex screens by logical sections.
- Favor copying existing content and updating it, rather than generating from scratch.
- Always place created/copied screens or components in empty areas. Never overlap.
- **IMPORTANT:** Every created node must have a meaningful `name`.
- **IMPORTANT:** Always call `locate_available_space` before inserting a node on the root page.

## Planning and Validation

- Create icons as components first, then insert instances with `I(parentId, {type: "ref", ref: "iconId"})`.
- Create reusable components as building blocks before assembling the main design.
- Create reusable variables for easier theme changes.
- After assembling design JSON, perform schema validation: check required properties, value constraints, and object relationships.
- Use `batch_read` to list reusable nodes in a design system frame to understand available components.

## Coordinates

- All coordinates are relative to the parent's top-left corner.
- `x` increases to the right, `y` increases downward.
- Child coordinates are always relative to their parent.

## Flexbox Layout

- **Always prefer flexbox layout** for arranging and sizing objects.
- When inserting a new frame, always explicitly set `width` and `height` — never assume auto layout.
- When only setting `layout` to `horizontal` or `vertical`, the default sizing mode for both `width` and `height` is `FIXED`. If dynamic sizing is needed, you must explicitly set `width` and `height`.
- Frames default to horizontal layout and `hug_contents` sizing.
- Prefer `fill_container` or `hug_contents` over hardcoded pixel values.
- When using flexbox, **x/y on children are completely ignored**. To position a child in a flexbox container, set the child's `layoutPositioning` to `ABSOLUTE` (default is `AUTO`).
- `fill_container` is only valid when parent has flexbox layout.
- `hug_contents` is only valid on a node that itself has flexbox layout.
- A parent cannot use `hug_contents` if **all** direct children use `fill_container` — circular dependency.
- Padding affects ALL children uniformly. To offset one child, wrap it in a frame with padding (no margin in flexbox).
- `layout: "none"` makes children use absolute positioning — avoid unless necessary.
- Use `primaryAxisAlignItems: "CENTER"` + `counterAxisAlignItems: "CENTER"` to center children.
- Use `layoutGrow: 1` to make a child fill remaining space along the primary axis.
- Use `primaryAxisAlignItems: "SPACE_BETWEEN"` to distribute children to opposite ends.
- Setting layout to `"none"` will make all children use absolute positioning. Avoid using absolute positioning unless absolutely necessary.

### Layout Code Example


```javascript
parent=I(document, {type: "frame",name: "Parent Frame", layout: "vertical", width: 1920, height: 1080})
container=I(parent, {
  type: "frame",
  name: "Content Container",
  layout: "vertical",        // or "horizontal" or "none" for absolute
  gap: 16,                    // spacing between children
  padding: 24,                // uniform padding
  primaryAxisAlignItems: "CENTER",      // main axis alignment
  counterAxisAlignItems: "CENTER",      // cross axis alignment
  width: "fill_container",
  height: "hug_contents"
})
```

## Text Nodes

- **Text has no color by default** — always set `fill` for visibility.
- For wrapping text, set **both** `textAutoResize: "HEIGHT"` **and** `width: "fill_container"` (or fixed width). Default `"WIDTH_AND_HEIGHT"` causes horizontal expansion.
- Prefer `width: "fill_container"` + `height: "hug_contents"` for auto-wrap.
- Avoid `maxLines: 1` with `textAutoResize: "HEIGHT"` unless single-line truncation is intentional.
- `textAlignHorizontal` / `textAlignVertical` align text within the bounding box (only effective when `textAutoResize` is `"HEIGHT"` or `"NONE"`).
- `textAlignHorizontal` values: `LEFT`, `RIGHT`, `CENTER`. `textAlignVertical` values: `TOP`, `CENTER`, `BOTTOM`.
- Setting `textAlignHorizontal`/`textAlignVertical` does NOT change the text bounding box position — use flexbox layout for that.
- `lineHeight`: Set `lineHeight: "AUTO"` for automatic, or `lineHeight: 22` for explicit line spacing.
- Default font: `Inter`. Always specify `fontName` when creating text.

### Typography Code Example

```javascript
title=I("parent", {type: "text", name: "Page Title", content: "Welcome", fontSize: 32, fontName: {family: "Inter", style: "Bold"}, fill: "#18191C", textAlignHorizontal: "LEFT", textAutoResize: "HEIGHT", width: "fill_container"})
```

## Components and Instances

- `COMPONENT` or `COMPONENT_SET` nodes are reusable (symbols).
- Insert instances with `type: "ref"` pointing to component/componentSet ID.
- For Component/ComponentSet: call `batch_read` with the ID to get `componentPropertyDefinitions`, then `batch_edit` to update instance properties.
- **Instance overrides**:
  - Root properties: set directly on the `ref` object
  - Descendant properties: use `descendants` map — `{descendants: {"childId": {content: "New"}}}`
  - Nested instances: slash-separated paths — `instanceId/nestedInstanceId/childId`
  - Replace subtree: include `type` in descendant override
  - "Delete" descendant: override `visible: false`
- When using `descendants`, paths can access multi-level descendant nodes — use paths in `descendants` keys, DO NOT create multiple levels of `descendants` objects.
- **Prefer updating the component** over individual instances for shared changes.
- ID formats: rendered tree uses **semicolons** (`instanceId;childId`), batch_edit uses **binding + nodeID** (`card+"childId"`). Fall back to semicolon ID if binding fails.
- Reuse existing components instead of creating duplicates.
- Instead of duplicating the same component multiple times with small tweaks, try to make them more generic so instances can reuse in more places.
- Cannot reference components across files — copy them over.
- Place reusable components on the side, next to the main design.
- Overrides are applied only to the overridden object — changes will NOT be inherited to all children.
- When parsing designs, treat "component" broadly — some are formal symbols, others are ad-hoc groupings visually behaving like components (sometimes prefixed "component/").

Use `descendants` property to override the child nodes inside the component.
``` javascript
butt=I("86:1", {type:"ref", ref: "85:67", descendants: { "85:68": { content: "Google"}, "85:69": { content: "$34.56"}}})
```

Or use `U()` to update the instance child nodes by combining the instance ID and the child node ID.
``` javascript
butt=I("86:1", {type:"ref", ref: "85:67"})
U(butt+"85:68", { content: "TECH"})
```

For an already created instance, if you want to update its source component, you can use `U(instance, {mainComponent: "newComponentId"})`, including nested instances which can also be changed in the same way.
**Swap Instance**:
``` javascript
butt=I("86:1", {type:"ref", ref: "85:67"})
U(butt, {mainComponent: "85:68"})
```

### Component Property Definitions

Use `componentPropertyDefinitions` in U() or I() to add, edit, or delete component properties on a Component or ComponentSet node. Pass an array of action objects:

**add** — Add a new property. Supports `BOOLEAN`, `TEXT`, `INSTANCE_SWAP`, and `VARIANT` types.
> `VARIANT` is only supported for nodes of type `COMPONENT_SET`.

```javascript
U("componentId", {componentPropertyDefinitions: [{action: "add", name: "Show Icon", type: "BOOLEAN", defaultValue: true}, {action: "add", name: "Label", type: "TEXT", defaultValue: "Button"}, {action: "add", name: "Size", type: "VARIANT", defaultValue: "Medium"}, {action: "add", name: "Icon", type: "INSTANCE_SWAP", defaultValue: "", options: {preferredValues: [{type: "COMPONENT", key: "iconCompKey"}]}}]})
```

The response `returnInfo` contains the added property IDs.

**edit** — Modify an existing property's name, default value, or preferred values.
- `name` is supported for all property types
- `defaultValue` is supported for `BOOLEAN`, `TEXT`, and `INSTANCE_SWAP`, but **NOT** for `VARIANT`
- `preferredValues` is only supported for `INSTANCE_SWAP`

```javascript
U("componentId", {componentPropertyDefinitions: [
  {action: "edit", name: "Label", newValue: {defaultValue: "Submit"}},
  {action: "edit", name: "Size", newValue: {name: "Variant"}},
  {action: "edit", name: "Show Icon", newValue: {name: "Has Icon", defaultValue: false}}
]})
```

**delete** — Remove an existing property. Only supports `BOOLEAN`, `TEXT`, and `INSTANCE_SWAP`. Cannot delete `VARIANT` properties.

```javascript
U("componentId", {componentPropertyDefinitions: [
  {action: "delete", name: "Show Icon"},
  {action: "delete", name: "Label"}
]})
```

### Bind Component Properties to Nodes

Use `componentPropertyReferences` in U() or I() to bind component properties to child node properties:

- `visible` — Reference to a boolean property controlling visibility.
- `characters` — Reference to a text property controlling text content.
- `mainComponent` — Reference to an instance swap property controlling the main component of an instance node.

**Important:** Use the property name defined in `componentPropertyDefinitions`. Before binding, ensure the property exists and the binding node is a child of the component.

```javascript
component=I("223:1",{type:"component", name: "component", layout: "horizontal", width: "hug_contents", height: "hug_contents", padding: 20, gap: 20, primaryAxisAlignItems: "CENTER", counterAxisAlignItems: "CENTER",componentPropertyDefinitions: [{action: "add", name: "Show Icon", type: "BOOLEAN", defaultValue: true}, {action: "add", name: "Label", type: "TEXT", defaultValue: "Button"}, {action: "add", name: "Icon", type: "INSTANCE_SWAP", defaultValue: "228:19"}]})
icon=I(component,{type:"ref", ref: "228:19", componentPropertyReferences: {visible: "Show Icon", mainComponent: "Icon"}})
text=I(component,{type:"text", text: "Text", fontSize: 24, componentPropertyReferences: {characters: "Label"}})
```

### Update Component Properties on Instance

**Important:** use the property name which is defined in `componentPropertyDefinitions` to set new value.

already exist three component nodes: `3:5` and `3:7`, and `3:11`, `3:11` has three component properties: Boolean Property: `Show Icon#252:1`, Text Property: `Label#252:2` and Instance Swap Property: `Icon#252:3`.

``` javascript
item1=I("35:2", {type: "ref", ref: "3:11", componentProperties: {"Show Icon#252:1": true, "Label#252:2": "Text1"}})
item2=I("35:2", {type: "ref", ref: "3:11"})
U(item2, {componentProperties: {"Show Icon#252:1": false, "Label#252:2": "Text2"}})
item3=I("35:2", {type: "ref", ref: "3:11", componentProperties: {"Show Icon#252:1": true, "Label#252:2": "Text3", "Icon#252:3": "3:7"}})
```

### Update Variant Properties on Instance

**Important:** use the property name which is defined in `componentPropertyDefinitions` to set new value.
**Important:** use the property value which is provided in `variantOptions` to switch variant.

already exist a componentSet nodes: `55:2`, has three Variant properties: 
``` json
{"Type": {"type": "VARIANT","defaultValue": "Circle","variantOptions": ["Circle", "Rectangle"]},
"Size": {"type": "VARIANT", "defaultValue": "small", "variantOptions": ["big", "small"]},
"Color": {"type": "VARIANT", "defaultValue": "blue", "variantOptions": ["red", "blue"]}}
```

only use provided `variantOptions` to switch variant.

``` javascript
item1=I("45:2", {type: "ref", ref: "55:2", componentProperties: {"Type": "Rectangle", "Size": "small"}})
item2=I("45:2", {type: "ref", ref: "55:2", componentProperties: {"Type": "Circle", "Size": "small", "Color": "blue"}})
U(item2, {componentProperties: {"Show Icon": false, "Label": "Text2"}})
item3=I("45:2", {type: "ref", ref: "55:2", componentProperties: {"Type": "Rectangle", "Size": "big", "Color": "red"}})
```

## Colors and Fills、Strokes

**IMPORTANT:** if fills/strokes type is `SOLID`, color only supports `r`, `g`, `b` fields.
**IMPORTANT:** if fills/strokes type is `GRADIENT_*`, color must provide `r`, `g`, `b` and `a` fields.

```javascript
// Simple fill using hex shorthand
U("nodeId", {fill: "#FF5733"})

// Detailed fill with opacity
U("nodeId", {fills: [{type: "SOLID", color: {r: 0.25, g: 0.48, b: 0.88}, opacity: 0.85, visible: true, blendMode: "NORMAL"}]})
// Detailed stroke
U("nodeId", {strokes: [{type: "SOLID", color: {r: 0.25, g: 0.48, b: 0.88}, opacity: 1, visible: true, blendMode: "NORMAL"}], strokeWeight: 5, strokeAlign: "INSIDE"})

// Linear gradient fill
U("nodeId", {fills: [{
  type: "GRADIENT_LINEAR",
  gradientStops: [
    {color: {r: 0.2, g: 0.4, b: 1.0, a: 1}, position: 0, boundVariables: {}},
    {color: {r: 1.0, g: 0.4, b: 0.3, a: 1}, position: 1, boundVariables: {}}
  ],
  gradientTransform: [[1, 0, 0], [0, 1, 0]],
  opacity: 1, visible: true, blendMode: "NORMAL"
}]})
```

Supported gradient types: `GRADIENT_LINEAR`, `GRADIENT_RADIAL`, `GRADIENT_ANGULAR`, `GRADIENT_DIAMOND`.

Note: `gradientStops` array must have at least two elements, and `boundVariables` can be empty but must be present.

### Gradient Fills as Image Placeholders

When image generation (G operation) is unavailable, use `GRADIENT_LINEAR` fills as visually appealing placeholders:
**IMPORTANT:** if fills/strokes type is `GRADIENT_*`, color must provide `r`, `g`, `b` and `a` fields.

```javascript
U("imageFrame", {fills: [{type: "GRADIENT_LINEAR",
  gradientStops: [
    {color: {r: 0.29, g: 0.73, b: 0.56, a: 1}, position: 0, boundVariables: {}},
    {color: {r: 0.16, g: 0.50, b: 0.73, a: 1}, position: 1, boundVariables: {}}
  ],
  gradientTransform: [[0.7, 0.7, 0], [-0.7, 0.7, 0.3]],
  opacity: 1, visible: true, blendMode: "NORMAL"}]})
```

Use different color schemes for different cards/sections to maintain visual distinction.

## Working with Design Variables

Bind reusable design tokens to node properties with the **`$:<SetName>:<VariableName>`** syntax. The `SetName` is the variable set (collection) name and `VariableName` is the variable name within that set. Use `get_editor_state` to discover available variables (`usableVariables`), or `set_variables` to create new ones. Variable types: `FLOAT`, `COLOR`, `BOOLEAN`, `STRING`.

```javascript
card=I(container, {type: "frame", width: "$:Primitives:card-width", cornerRadius: "$:Primitives:radius-lg", padding: "$:Primitives:spacing-md", fill: "$:Semantic:bg-color", visible: "$:Flags:show-card"})
title=I(card, {type: "text", content: "$:Content:app-title", fontSize: "$:Primitives:heading-size", fontFamily: "$:Primitives:body-font", fill: "$:Semantic:text-primary"})
```

### Supported Variable Binding Properties

**FLOAT** (Node) — `width`, `height`, `minWidth`, `maxWidth`, `minHeight`, `maxHeight`, `itemSpacing`, `counterAxisSpacing`, `paddingLeft`, `paddingRight`, `paddingTop`, `paddingBottom`, `padding` (binds all four sides), `cornerRadius`, `topLeftRadius`, `topRightRadius`, `bottomLeftRadius`, `bottomRightRadius`, `strokeWeight`, `strokeTopWeight`, `strokeRightWeight`, `strokeBottomWeight`, `strokeLeftWeight`, `opacity`, `gridRowGap`, `gridColumnGap`

**FLOAT** (Text) — `fontSize`, `letterSpacing`, `lineHeight`, `paragraphSpacing`, `paragraphIndent`

**STRING** — `content` (also accepts FLOAT, auto-stringified)

**BOOLEAN** — `visible`

**COLOR** — `fill`, `stroke` (shorthand for single solid paint), or `color: "$:Set:var"` inside `fills`/`strokes` arrays:

```javascript
// Shorthand single-color binding (preferred)
U("nodeId", {fill: "$:Semantic:bg-color", stroke: "$:Semantic:border-color"})

// Inside fills/strokes array (for multiple paints or gradient stops)
U("nodeId", {fills: [{type: "SOLID", color: "$:Semantic:surface-color"}]})
U("nodeId", {fills: [{type: "GRADIENT_LINEAR", gradientStops: [{color: "$:Brand:brand-start", position: 0}, {color: "$:Brand:brand-end", position: 1}], gradientTransform: [[1, 0, 0], [0, 1, 0]]}]})
```

### Variable Rules

- Variable reference format: `$:<SetName>:<VariableName>` — starts with `$:` prefix, followed by SetName and VariableName separated by `:`. Both SetName and VariableName must be non-empty.
- Variable set names and variable names must NOT contain `$` or `:` characters.
- Strings like `$99.99`, `$HOME`, `$(document)` are treated as plain text, not variable references.
- Type must match: FLOAT for number properties, COLOR for fill/stroke, BOOLEAN for visible, STRING for content/fontFamily.
- Variable references on unsupported properties (e.g., `x`, `y`, `rotation`) are skipped with a warning.
- `padding: "$:Set:var"` binds all four padding sides simultaneously.
- COLOR binding uses the variable's current color as fallback; if unavailable, a warning is reported.

### Unbinding Variables

To remove an existing variable binding from a property, set the property value to `null`:

```javascript
// Unbind opacity
U("nodeId", {opacity: null})

// Unbind all four padding sides at once
U("nodeId", {padding: null})

// Unbind specific fields
U("nodeId", {cornerRadius: null, strokeWeight: null, visible: null})
```

## Tables

Strict hierarchy: **Table (frame) → Row (frame) → Cell (frame) → Content**

Each cell must be a frame wrapping content. Never put text directly in a row.

```javascript
// ✅ Correct
tableRow=I("tableId", {type: "frame", name: "Row", layout: "horizontal", width: "fill_container"})
cell1=I(tableRow, {type: "frame", name: "Cell", width: "fill_container"})
text1=I(cell1, {type: "text", name: "Name", content: "John", fill: "#18191C"})

// ❌ Wrong — text directly in row, missing cell frame
badRow=I("tableId", {type: "frame", layout: "horizontal"})
badText=I(badRow, {type: "text", content: "John"})
```

## Images

- NO `image` node type. Images are **fills** on frame/rectangle nodes.
- Use `G()` for images — never generate random URLs.
- Prefer `"stock"` over `"ai"` type.
- Pattern: Insert frame → apply G() as fill.
- When G() is unavailable, use `GRADIENT_LINEAR` fills as placeholders with different color schemes per section.

## Effects

Supported types: `DROP_SHADOW`, `INNER_SHADOW`, `LAYER_BLUR`, `BACKGROUND_BLUR`.

```javascript
// Drop shadow
U("cardId", {effects: [{type: "DROP_SHADOW", color: {r: 0, g: 0, b: 0, a: 0.3}, offset: {x: 0, y: 20}, radius: 40, spread: -8, visible: true, blendMode: "NORMAL", showShadowBehindNode: true, boundVariables: {}}]})

// Inner shadow
U("cardId", {effects: [{type: "INNER_SHADOW", color: {r: 0, g: 0, b: 0, a: 0.3}, offset: {x: 0, y: 20}, radius: 40, spread: -8, visible: true, blendMode: "NORMAL", showShadowBehindNode: true, boundVariables: {}}]})

// Layer blur
U("cardId", {effects: [{type: "LAYER_BLUR", radius: 20, visible: true, boundVariables: {}}]})

// Background blur
U("cardId", {effects: [{type: "BACKGROUND_BLUR", radius: 10, visible: true, boundVariables: {}}]})
```

Multi-layer shadow for realistic elevation:

```javascript
U("cardId", {effects: [
  {type: "DROP_SHADOW", color: {r: 0, g: 0, b: 0, a: 0.3}, offset: {x: 0, y: 20}, radius: 40, spread: -8, visible: true, blendMode: "NORMAL", showShadowBehindNode: true, boundVariables: {}},
  {type: "DROP_SHADOW", color: {r: 0, g: 0, b: 0, a: 0.6}, offset: {x: 0, y: 8}, radius: 24, spread: -4, visible: true, blendMode: "NORMAL", showShadowBehindNode: true, boundVariables: {}},
  {type: "DROP_SHADOW", color: {r: 0, g: 0, b: 0, a: 0.9}, offset: {x: 0, y: 4}, radius: 4, spread: 0, visible: true, blendMode: "NORMAL", showShadowBehindNode: false, boundVariables: {}}
]})
```

- Layer 1 (near): small offset, tight blur — edge definition
- Layer 2 (mid): medium offset, wide blur — depth cue
- Layer 3 (far): large offset, very wide blur — ambient glow
- If you need to create a frosted glass effect, set all `fills`'s `opacity` below 0.5.

## SVG Icons

- Prefer SVG nodes over icon fonts.
- Use `type: "frame"` with `svg` property containing full SVG markup.
- When creating icon from frame, must set `layout: "none"`.
- Always `capture_screenshot()` after creating SVG icons to verify.

```javascript
icon=I("parent", {
  type: "frame",
  name: "Search Icon",
  svg: "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><circle cx=\"11\" cy=\"11\" r=\"7\" stroke=\"#333\" stroke-width=\"2\"/><path d=\"M16 16L20 20\" stroke=\"#333\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>",
  width: 24,
  height: 24
})
```

## Icon Components

- Always create icon as a component, then use `I(parentId, {type: "ref", ref: "iconId"})` to insert the icon instance.
- When creating icon from frame, must set `layout: "none"`.
- After creating icons, must run `capture_screenshot()` to verify the icon is correct.

## Frames

- Default Frame has a white background fill. To remove the background, set `fills: []`.
- Frames can be nested within other frames and serve as containers for child objects.
- When creating multiple screens, represent each one as a top-level frame.

```javascript
card=I("parent", {
  type: "frame",
  name: "Card",
  width: 320,
  height: 200,
  fill: "#FFFFFF",
  cornerRadius: 12,
  stroke: "#E0E0E0",
  strokeWeight: 1,
  effects: [{type: "DROP_SHADOW", color: {r: 0, g: 0, b: 0, a: 0.1}, offset: {x: 0, y: 2}, radius: 8, visible: true, blendMode: "NORMAL", showShadowBehindNode: true, boundVariables: {}}],
  placeholder: true,
  layout: "vertical",
  padding: 16,
  gap: 12
})
```

## Property Quick Reference

### Common Mistakes

| Wrong | Correct | Notes |
|---|---|---|
| `textColor: "#FFF"` | `fill: "#FFFFFF"` | Text color via `fill` |
| `backgroundColor: "#FFF"` | `fill: "#FFFFFF"` | Background via `fill` on frame |
| `color: "#FFF"` | `fill: "#FFFFFF"` | Always use `fill` |
| `fillColor: "#FFF"` | `fill: "#FFFFFF"` | Use `fill` |
| `borderRadius: 8` | `cornerRadius: 8` | Use `cornerRadius` |
| `fontWeight: "bold"` | `fontWeight: "700"` | Numeric strings only |
| `fontWeight: "semibold"` | `fontWeight: "600"` | Numeric strings only |
| `fontWeight: "medium"` | `fontWeight: "500"` | Numeric strings only |
| `alignItems: "center"` | `counterAxisAlignItems: "CENTER"` | Uppercase enum |
| `justifyContent: "center"` | `primaryAxisAlignItems: "CENTER"` | Uppercase enum |
| `verticalAlign: "center"` | `counterAxisAlignItems: "CENTER"` | Uppercase enum |

### Alignment

| Purpose | Property | Valid Values |
|---|---|---|
| Main axis | `primaryAxisAlignItems` | `"MIN"`, `"CENTER"`, `"MAX"`, `"SPACE_BETWEEN"`, `"SPACE_EVENLY"` |
| Cross axis | `counterAxisAlignItems` | `"MIN"`, `"CENTER"`, `"MAX"`, `"BASELINE"` |
| Cross axis content | `counterAxisAlignContent` | `"AUTO"`, `"SPACE_BETWEEN"` |

### Size Values

| Value | Behavior |
|---|---|
| Numeric (`400`) | Exact pixel size |
| `"fill_container"` | Stretch to fill parent |
| `"fill_container(200)"` | Fill with 200px minimum |
| `"hug_contents"` | Shrink-wrap to fit children |
| `"hug_contents(600)"` | Hug with 600px minimum |

### Font Weight

| Value | Style |
|---|---|
| `"100"` | Thin |
| `"200"` | Extra Light |
| `"300"` | Light |
| `"400"` | Regular (default) |
| `"500"` | Medium |
| `"600"` | Semi Bold |
| `"700"` | Bold |
| `"800"` | Extra Bold |
| `"900"` | Black |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Text invisible | Missing `fill` | Add `fill: "#000000"` |
| Text overflows | `textAutoResize: "WIDTH_AND_HEIGHT"` | Set `textAutoResize: "HEIGHT"` + `width: "fill_container"` |
| Instance text garbled | Font/resize issue in instance | Re-set `textAutoResize`, `width`, `fontName` on **component** |
| Instance no background | `fills` empty | Explicitly set `fill` on instance |
| Child path not found | Wrong ID format | `batch_read` with `resolveInstances: true` for semicolon IDs |
| Content clipped | `clipsContent: true` + fixed height | Set `height: "hug_contents"` or increase |
| Shadows not visible | `visible: false` or `a: 0` | Set `visible: true`, alpha > 0 |
| Font different | Unavailable style | Use "Regular", "Medium", "Bold" for Inter |
| Children misaligned | Wrong axis prop | `counterAxisAlignItems: "CENTER"` for cross-axis |
| Children not spread | No distribution | `primaryAxisAlignItems: "SPACE_BETWEEN"` |

## General Best Practices

- If a property is not defined, treat it as 0 — do not hallucinate values.
- Exclude default property values unless overriding a non-default inside an instance.
- Avoid `width: 0` and `height: 0`.
- Keep color float values to 2 decimal places.
- Favor copying existing content + updating over generating from scratch.
- Always validate with **tiered validation** after design changes (see Post-Generation Validation Pattern below) — not every batch needs a full screenshot+layout check.
- Always need call `locate_available_space` tool before inserting a node on root page.
- If possible, first create reusable components that will be used as building blocks. Place these separately on the canvas.
- If possible, first create reusable variables that will make the design easier to change themes.
- Use `batch_read` by listing reusable nodes in a design system frame, when working with a design system or design kit frame, to understand what components are available.

## Post-Generation Validation Pattern

> **Guiding principle**: validation exists to catch real defects, not to re-inspect already-good work. Every extra `capture_screenshot` / `capture_layout` call costs a round-trip. Validate with the lightest tool that can catch the failure modes of the batch you just ran, and stop as soon as the design is acceptable.

### Tiered Validation (apply per batch_edit)

Pick the tier that matches what the batch changed. **Do not run full dual-verification after every batch.**

| Batch type | What it changed | Validation |
|---|---|---|
| **T1 — Structural scaffold** | New frames, layout mode, padding, hierarchy | `capture_layout(problemsOnly: true)` only — screenshot not useful yet |
| **T2 — Content fill** | Text content, token binding, component instance props | **Skip validation**; defer to the next style/phase batch |
| **T3 — Visual/style** | `fill`, typography, effects, cornerRadius, strokes | `capture_screenshot` only |
| **T4 — Section complete** | A whole logical section (hero, features, footer) is done | Run **both** `capture_screenshot` + `capture_layout(problemsOnly: true)` **once** |
| **T5 — Final page** | All sections merged | One final `capture_screenshot` of the full page |

Rules of thumb:
- If two consecutive batches are both T2 or T3, validate **once at the end**, not after each.
- Prefer batching corrective fixes: accumulate issues and fix them in **one** `batch_edit`, then re-validate once.
- `capture_screenshot` for nodes > 2000px tall: screenshot sections, not the whole node.

### Convergence Threshold — When to Stop Iterating

Validation loops must **terminate**. Apply these stop conditions:

1. **Hard cap**: at most **2 fix iterations** per section. If a third pass is about to start, record the remaining issue as a known limitation in your final summary and move on — do not keep looping.
2. **Ignore cosmetic noise** from `capture_layout`:
   - Spacing deltas ≤ 4px
   - Sub-pixel misalignment (< 1px)
   - Non-critical overflow in decorative/background nodes
   - Problems on nodes outside the section currently being built
3. **No subjective re-polishing**: once a section matches the style guide and has no structural problems, **do not** run additional screenshots "to double-check" or to hunt for aesthetic improvements. Ship it.
4. **Only fix what the tool reported**: don't invent new issues from a screenshot when `capture_layout` came back clean.

### Corrective Fix Protocol

When a tier's validation does surface real issues:
1. Accumulate **all** issues from the validation call.
2. Issue **one** corrective `batch_edit` that addresses them together.
3. Re-run **only the same tier's validation** (don't upgrade to full dual-verification just because you fixed something).
4. If still failing and you're at iteration 2 → stop, note the issue, proceed.

### Common Post-Verification Fixes

| Issue | Fix |
|-------|-----|
| Text invisible on sub-frame | Set `fills: []` on the sub-frame so parent bg shows through |
| Font style not found | Call `get_available_fonts` and update with exact style name |
| Cards overlapping | Check parent has `layout: "horizontal"` or `"vertical"` |
| Elements misaligned | Set `counterAxisAlignItems: "CENTER"` on parent |
| Content clipped | Set parent `height: "hug_contents"` or increase height |

---

## Node Property Schema

> 节点类型及其支持的属性，基于 Mixin 组合模式构建。

### Node Types

`DOCUMENT` | `PAGE` | `FRAME` | `GROUP` | `COMPONENT_SET` | `COMPONENT` | `INSTANCE` | `SECTION` | `TEXT` | `VECTOR` | `RECTANGLE` | `ELLIPSE` | `LINE` | `STAR` | `BOOLEAN_OPERATION`

### Property Mixins

**Base** (所有节点): `id`, `parent`, `name`, `type`, `removed`, `isAsset`

**Scene** (可见节点，除 DOCUMENT/PAGE): `visible` (default `true`), `locked` (default `false`), `stuckNodes`, `attachedConnectors`, `componentPropertyReferences`, `boundVariables`, `inferredVariables`, `resolvedVariableModes`

**Dimension & Position**: `x`, `y`, `width`, `height`, `minWidth`, `maxWidth`, `minHeight`, `maxHeight`, `absoluteBoundingBox`

**Layout**: `rotation` (default `0`), `layoutSizingHorizontal` (`FIXED`/`HUG`/`FILL`, default `FIXED`), `layoutSizingVertical` (same)

**Auto Layout Children**: `layoutAlign`, `layoutGrow`, `layoutPositioning` (`AUTO`/`ABSOLUTE`, default `AUTO`)

**Auto Layout** (Frame 类): `layoutMode` (`NONE`/`HORIZONTAL`/`VERTICAL`), `primaryAxisAlignItems` (`MIN`/`CENTER`/`MAX`/`SPACE_BETWEEN`), `counterAxisAlignItems` (`MIN`/`CENTER`/`MAX`/`BASELINE`), `counterAxisAlignContent`, `primaryAxisSizingMode`, `counterAxisSizingMode`, `itemSpacing`, `counterAxisSpacing`, `paddingTop/Right/Bottom/Left`, `layoutWrap` (`NO_WRAP`/`WRAP`), `strokesIncludedInLayout`, `itemReverseZIndex`

**Blend**: `opacity` (default `1`), `blendMode` (default `NORMAL`), `isMask`, `maskType`, `effects`, `effectStyleId`

**Geometry**: `fills`, `fillStyleId`, `strokes`, `strokeStyleId`, `strokeWeight` (default `1`), `strokeAlign` (`INSIDE`/`OUTSIDE`/`CENTER`, default `INSIDE`), `strokeJoin`, `strokeCap`, `strokeMiterLimit`, `dashPattern`, `strokeGeometry`, `fillGeometry`

**Individual Strokes** (Frame 类): `strokeTopWeight`, `strokeBottomWeight`, `strokeLeftWeight`, `strokeRightWeight`

**Corner**: `cornerRadius`, `cornerSmoothing`, `topLeftRadius`, `topRightRadius`, `bottomLeftRadius`, `bottomRightRadius`

**Constraint**: `constraints`

**Text**: `characters`, `fontSize`, `fontName`, `fontWeight`, `lineHeight`, `letterSpacing`, `textAlignHorizontal`, `textAlignVertical`, `textAutoResize`, `textTruncation`, `maxLines`, `textCase`, `textDecoration`, `textStyleId`, `hyperlink`, `paragraphIndent`, `paragraphSpacing`, `leadingTrim`, `hasMissingFont`, `autoRename`

**Component**: `componentPropertyDefinitions`, `variantProperties`, `description`, `descriptionMarkdown`, `documentationLinks`, `remote`, `key`

**Instance**: `mainComponent`, `componentProperties`, `scaleFactor`, `exposedInstances`, `isExposedInstance`, `overrides`

**Other**: `children`, `expanded`, `clipsContent` (default `false`), `targetAspectRatio`, `exportSettings`, `reactions`, `devStatus`, `detachedInfo`, `layoutGrids`, `gridStyleId`, `guides`, `arcData`, `pointCount`, `innerRadius`, `booleanOperation`, `sectionContentsHidden`, `selection`

### Node → Mixin 组合

| Node Type | Mixin 组合 |
|-----------|-----------|
| **DOCUMENT** | Base |
| **PAGE** | Base + Export + `guides`, `selection` |
| **FRAME** | Base + Scene + Children + Container + Background + Geometry + Corner + RectCorner + Blend + Constraint + Layout + Export + IndividualStrokes + AutoLayout + AspectRatio + DevStatus + Reaction + `clipsContent`, `layoutGrids`, `guides` |
| **GROUP** | Base + Scene + Reaction + Children + Container + Background + Blend + Layout + Export + AspectRatio |
| **RECTANGLE** | DefaultShape + Constraint + Corner + RectCorner + IndividualStrokes + AspectRatio |
| **ELLIPSE** | DefaultShape + Constraint + Corner + AspectRatio + `arcData` |
| **LINE** | DefaultShape + Constraint |
| **STAR** | DefaultShape + Constraint + Corner + AspectRatio + `pointCount`, `innerRadius` |
| **VECTOR** | DefaultShape + Constraint + Corner + AspectRatio |
| **TEXT** | DefaultShape + Constraint + Text + AspectRatio |
| **COMPONENT_SET** | BaseFrame + Publishable + ComponentProperty |
| **COMPONENT** | DefaultFrame + Publishable + Variant + ComponentProperty |
| **INSTANCE** | DefaultFrame + Variant + `mainComponent`, `scaleFactor`, `componentProperties`, `exposedInstances`, `isExposedInstance`, `overrides` |
| **BOOLEAN_OPERATION** | DefaultShape + Children + Corner + Container + AspectRatio + `booleanOperation` |
| **SECTION** | Children + MinimalFills + Opaque + DevStatus + AspectRatio + `sectionContentsHidden` |

> **DefaultShape** = Base + Scene + Reaction + Blend + Geometry + Layout + Export
> **BaseFrame** = DefaultShape + Children + Container + Background + Corner + RectCorner + Constraint + IndividualStrokes + AutoLayout + AspectRatio + DevStatus
> **DefaultFrame** = BaseFrame + Reaction

### 属性默认值（省略优化）

序列化时，值等于默认值的属性会被省略：

```
visible: true, rotation: 0, opacity: 1, clipsContent: false,
locked: false, layoutPositioning: "AUTO", blendMode: "NORMAL",
strokeAlign: "INSIDE", strokeWeight: 1,
layoutSizingHorizontal: "FIXED", layoutSizingVertical: "FIXED"
```
