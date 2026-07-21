# Instructions when generating code from design files

- IMPORTANT: Make sure to use the frontend frameworks that are already used in the project. For example, if the project is using React, always generate compliant React code.
- IMPORTANT: After generating code, DO NOT output Markdown files of the changes. Just stick to generating code and nothing else.
- IMPORTANT: Make sure to use and leverage the CSS libraries, design systems and other UI coding utilities that are already used in the project. For example, if the project is using Tailwind, make sure to style your code using Tailwind.
- IMPORTANT: Make sure when using CSS libraries and frameworks that you identify the installed version and always use the correct APIs that are supported by the installed versions.
- IMPORTANT: When generating code from .ardot designs, always make sure to use the same text labels, icons ans spacing as what is in the design.
- DO NOT create documentations for the changes when generating code from design.
- Explore the workspace to find if the design elements you are translating to code are already exist in the code base.
- Make sure to awlays use the correct font, icons, and UI details like border radius when generating the code from a design.
- If you are not sure what frontend frameworks and UI libraries are used in the project, explore it in the workspace.
- If the UI design element you are turning code into already exist in the codebase, update it, not generate a new one.
- When changing existing components and UI elements in the code, make sure to not break the functionality.

## Initial Setup

### Project Initialization

- Identify the frontend framework and language used in the project (e.g., React, Vue, Angular, Svelte, etc.)
- Use the same framework, language, and conventions as the existing project
- Identify the styling approach (e.g., Tailwind, CSS Modules, styled-components, etc.)
- If using Tailwind, refer to 'tailwind' topic for implementation details

### Pre-Implementation Verification

- Ensure CSS/styles compile without errors
- Verify all CSS variables are accessible (if using CSS custom properties)
- Confirm styling system is properly configured and loaded

## Component Implementation Workflow

### Step 1: Component Analysis and Extraction

#### 1A. Identify Required Components

- Read the target frame/design
- Identify which reusable components (refs) are used in this specific frame
- **IMPORTANT**: Only process components that appear in the current frame
- Count instances of each component (helps catch missing instances later)
- Document: "Component X used N times"

#### 1B. Extract Component Definitions

- Use `batch_read` to get component structure
- Extract full component tree with all nested children
- Process components ONE AT A TIME:
  1. Extract component with full depth
  2. Recreate in React (Step 2)
  3. Validate (Step 3)
  4. Move to next component only after validation passes

#### 1C. Map Component Instances

- Read the target frame structure
- For each component, identify ALL instances
- Document for each instance:
  * Instance ID and location
  * Nested component overrides (`descendants` map)
  * Props/values being passed
- **Nested Component Analysis**:
  * Check base component definition: Does it always include nested components?
  * Check all instances: Do any override/hide nested components?
  * **Decision Rule**:
    - If NO instances override away → Nested component is REQUIRED (always render)
    - If ANY instances override away → Nested component is OPTIONAL (conditional render)
  * Verify each nested component ref in base definition against all instances
- **Visual Verification**:
  * Use `capture_screenshot` on instances in context (not just base definition)
  * Verify visible elements (borders, backgrounds, shadows)
  * Check if styling should be on outer container or nested elements
  * Match visual appearance in frame context

### Step 2: React Component Creation

#### Component Structure

- Create `.tsx` file in `src/components/` with component name
- Use named exports
- Define TypeScript interfaces for all props

#### Props Interface Design

- Review ALL instances from Step 1C mapping
- Support all properties used by any instance (including optional ones)
- **Nested Component Rendering**:
  * Apply decision rule from Step 1C:
    - NO instances override away → Always render (required)
    - ANY instances override away → Conditional render (optional)
  * Verify against instance mapping before making props optional
- Document required vs optional props based on actual usage
- Cross-reference with instance mapping to ensure completeness

#### Style Implementation

- Use Tailwind classes exclusively (NO inline styles)
- Refer to guidelines-tailwind.md sections: "Layout Conversion", "Style Implementation", "CSS Custom Properties and Font Stacks"
- Match design values exactly (use arbitrary values when needed)
- Use CSS variables for colors (no hardcoded values)

#### SVG Path Implementation

When implementing SVG elements from the design:

**1. Extract Exact Geometry**
- Use `batch_read` with `includePathGeometry: true`
- NEVER approximate paths - extract exact `geometry` property from design

**2. Properties to Extract**
- `geometry` - use as `d` attribute in `<path>`
- `fill` - convert design variables to CSS variables (e.g., `$primary` → `var(--primary)`)
- `stroke` properties if present (`strokeColor`, `strokeThickness`)
- `width` and `height` for viewBox calculation

**3. Implementation**
- Use exact geometry string in `d` attribute
- Set `viewBox="0 0 {width} {height}"`
- Preserve all stroke properties
- For styling, see guidelines-tailwind.md "SVG Styling" section for Tailwind-specific syntax

**4. Logos and Complex Icons**
- Extract complete geometry even if very long
- Don't simplify or approximate
- Maintain precision for brand assets

### Step 3: Component Validation

1. **Visual Verification**:
   - Use `capture_screenshot` on design component
   - Compare with rendered React component
   - Verify pixel-perfect match

2. **Style Verification**:
   - Inspect computed CSS properties
   - Verify dimensions, spacing, colors, typography match design
   - Ensure CSS variables resolve correctly

3. **Behavior Verification**:
   - Test fill_container elements expand properly
   - Test hug_contents elements size to content
   - Verify no overflow issues

4. **Iterative Fixing**:
   - Fix discrepancies immediately
   - Re-validate after each fix
   - Only proceed to next component when current is perfect

### Step 4: Frame Integration

#### Pre-Integration Analysis

- Read complete target frame with `maxDepth: 10`
- Map component tree structure
- Identify all component instances

#### Instance Configuration

- Document all property overrides for each instance
- Verify nested component overrides
- Create instance mapping with exact props
- **Layout Context**:
  * Check parent container layout mode
  * If flex container with multiple `fill_container` children → each needs `flex-1`
  * Document which components need `flex-1` based on parent layout

#### Completeness Verification

- Count component instances in design vs implementation
- Verify all props match design overrides
- Confirm nested components follow required/optional decision from Step 1C
- Use checklist:
  * [ ] All instances accounted for
  * [ ] All props match overrides
  * [ ] Nested components render correctly (always vs conditional)
  * [ ] Layout classes applied correctly (`flex-1`, etc.)

### Step 5: Final Validation

- Verify component positions and spacing match design
- Verify colors resolve correctly
- Verify typography matches
- Verify responsive behavior:
  * Layout adapts to different viewport sizes
  * Scrollable areas work when content exceeds space
  * No horizontal overflow
  * `fill_container` elements expand properly
  * `hug_contents` elements size to content
- Verify no console errors
- Verify all interactive elements function correctly

## Key Principles

- Use the project's styling system consistently (avoid inline styles when possible)
- If using Tailwind, see guidelines-tailwind.md for Tailwind-specific implementation details
- Match design values exactly
- Use the project's color system (CSS variables, design tokens, theme files, etc.) - avoid hardcoded values
- Process components one at a time with validation
- Verify nested component rendering requirements
- Ensure proper styling and layout based on parent context
