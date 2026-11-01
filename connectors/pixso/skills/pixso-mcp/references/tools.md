# Pixso remote MCP tool routing

Use the live MCP tool schema as the authority for parameters and return types. This reference explains selection and safety only.

## Generate and convert

- `design_to_code`: Generate frontend code from one or more Pixso nodes. Preserve the user's node order and requested framework.
- `refine_generated_code`: Use only when offered by the server after code generation or when the user asks for the supported refinement.
- `code_to_design`: Convert supported code or web artifacts into editable Pixso design content. Treat creation in a Pixso file as a write.

## Inspect and navigate

- `fetch_context`: Get the current canvas, selection, and available design-resource context.
- `get_top_level_frames`: List pages and top-level frames before a scoped query.
- `query_nodes`: Search for nodes or read selected node properties.
- `get_node_dsl`: Read detailed node structure. Prefer a compact response first and resolve referenced data only when needed.
- `get_export_image`: Export image or vector resources from a design node.
- `read_component_config_data`: Read component configuration data for design-to-code mapping.

## Read design resources

- `read_comments`: Read and summarize comment threads; it does not reply to, delete, or resolve comments.
- `read_components`: Read reusable components and component sets.
- `read_styles`: Read local and shared styles.
- `read_variables`: Read variables and variable collections.
- `query_all_unique_props`: Audit colors, typography, spacing, radii, and other distinct properties.

## Guidance and verification

- `load_guidelines`: Load design guidance for the requested scenario.
- `list_style_tags`: List available visual-style tags.
- `get_style_guide`: Retrieve a style guide for selected tags.
- `check_layout`: Detect layout, alignment, nesting, and structural issues.
- `take_screenshot`: Capture one or more nodes for visual verification.

## Modify design resources

- `write_styles`: Create, update, rename, or delete shared styles.
- `write_variables`: Create, update, rename, or delete variables and collections.
- `apply_design`: Create, modify, move, organize, or delete design nodes.
- `replace_props`: Bulk-replace colors, typography, radii, or other properties.
- `eval_script`: Execute Pixso Plugin API JavaScript. The script can read or modify a file, and failures may not roll back completed changes.

For every modifying tool, limit the operation to the user-approved scope. Confirm immediately before deletions, broad replacements, or script-based writes. After a write, inspect the affected nodes and verify visually or structurally when appropriate.
