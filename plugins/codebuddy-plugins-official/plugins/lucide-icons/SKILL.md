# Lucide Icons Skill

Search, download, and customize Lucide icons (1000+ beautiful SVG icons).

## Quick Start

```bash
# Search for icons
node ./scripts/lucide.js search heart

# Download an icon
node ./scripts/lucide.js download heart --output ./icons/

# Download with React component
node ./scripts/lucide.js download heart --output ./icons/ --format svg,react

# Customize icon
node ./scripts/lucide.js download star --color "#ffd700" --size 32
```

## Commands

### search `<keyword>`
Search for icons by name or keyword.

```bash
lucide search heart --limit 10
```

### download `<icon-name>`
Download a single icon with optional customization.

Options:
- `-o, --output <dir>` - Output directory (default: current directory)
- `-f, --format <formats>` - Output formats: `svg`, `react` (default: `svg`)
- `-c, --color <color>` - Icon color (default: `currentColor`)
- `-s, --size <size>` - Icon size in pixels (default: `24`)
- `-w, --stroke-width <width>` - Stroke width (default: `2`)
- `--overwrite` - Overwrite existing files

### list
List all available icons.

```bash
lucide list --limit 50
```

### info `<icon-name>`
Show detailed information about an icon.

```bash
lucide info heart
```

### refresh
Refresh the icon metadata cache.

```bash
lucide refresh
```

## Installation

Before first use, install dependencies:

```bash
cd ./scripts && npm install
```

## Output Formats

### SVG
Standard SVG file with optional customization (color, size, stroke-width).

### React (TypeScript)
Generates a fully-typed React component with props:
- `size` - Icon size
- `color` - Icon color
- `strokeWidth` - Stroke width
- `className` - CSS classes
- `style` - Inline styles
- `aria-label` - Accessibility label

## Examples

```bash
# Download heart icon to src/icons/
lucide download heart -o ./src/icons/

# Download with custom color and size
lucide download star --color "#ffd700" --size 32 -o ./icons/

# Generate both SVG and React component
lucide download check-circle --format svg,react -o ./src/components/icons/

# Search for arrow icons
lucide search arrow --limit 20
```

## Data Source

Icons are fetched from the official [Lucide repository](https://github.com/lucide-icons/lucide).

## More Information

See [README.md](./README.md) for detailed documentation.
