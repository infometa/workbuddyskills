#!/bin/bash
# content-repurposer/scripts/setup.sh — Initialize content repurposer config

set -euo pipefail

REPURPOSE_DIR="${REPURPOSE_DIR:-$HOME/.config/content-repurposer}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/content-repurposer-output}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "♻️  Content Repurposer Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create config directory
mkdir -p "$REPURPOSE_DIR"
echo "✓ Created $REPURPOSE_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "✓ Created $OUTPUT_DIR"

# Copy example config if none exists
if [ ! -f "$REPURPOSE_DIR/config.json" ]; then
  cp "$SKILL_DIR/config.example.json" "$REPURPOSE_DIR/config.json"
  echo "✓ Created config.json (edit with your voice and platform preferences)"
else
  echo "• config.json already exists (skipped)"
fi

# Create example content file
EXAMPLE_FILE="$OUTPUT_DIR/examples/sample-post.md"
mkdir -p "$OUTPUT_DIR/examples"
if [ ! -f "$EXAMPLE_FILE" ]; then
  cat > "$EXAMPLE_FILE" << 'EOF'
# The Power of Small Wins

We obsess over big launches and major milestones. But here's what I've learned after 10 years of building: momentum comes from small wins.

## Why Small Wins Matter

1. **Psychological fuel**: Each small win releases dopamine, keeping you motivated
2. **Compounding progress**: 1% better each day = 37x better in a year
3. **Reduced perfectionism**: Ship fast, learn fast, improve fast

## My Framework

Instead of waiting for the "perfect" launch:
- Ship the MVP version today
- Get one user's feedback
- Iterate tomorrow
- Repeat

## Real Example

Last month I built a simple automation tool in 2 hours. Not perfect. Not pretty. But it saved me 30 minutes every day. That's 15 hours/month. That's real progress.

## Your Turn

What's one small win you can ship TODAY? Not this week. Not "when it's ready." Today.

The big wins take care of themselves when you stack enough small ones.
EOF
  echo "✓ Created sample-post.md (test with: repurpose.sh examples/sample-post.md)"
else
  echo "• sample-post.md already exists (skipped)"
fi

# Create repurpose log file
if [ ! -f "$REPURPOSE_DIR/repurpose-log.json" ]; then
  echo '{"repurposings":[]}' > "$REPURPOSE_DIR/repurpose-log.json"
  echo "✓ Created repurpose-log.json"
else
  echo "• repurpose-log.json already exists (skipped)"
fi

echo ""
echo "Next steps:"
echo "  1. Edit $REPURPOSE_DIR/config.json with your voice settings"
echo "  2. Test with sample: $(dirname "$0")/repurpose.sh $OUTPUT_DIR/examples/sample-post.md"
echo "  3. Check output in: $OUTPUT_DIR/"
echo ""
echo "Pro tip: Set your voice.tone, personality, and user.primary_cta first."
echo ""
echo "♻️  Ready to repurpose content!"
