#!/bin/bash

# analyze-plugin-info.sh
# Analyzes a plugin directory and extracts comprehensive component information
# Usage: analyze-plugin-info.sh <plugin-directory>

set -euo pipefail

PLUGIN_DIR="$1"

if [[ ! -d "$PLUGIN_DIR" ]]; then
  echo "Error: Plugin directory not found: $PLUGIN_DIR" >&2
  exit 1
fi

# Helper function to extract YAML frontmatter value
extract_yaml_field() {
  local file="$1"
  local field="$2"
  
  if [[ ! -f "$file" ]]; then
    echo ""
    return
  fi
  
  # Extract value between --- frontmatter markers
  awk -v field="$field" '
    BEGIN { in_frontmatter=0; }
    /^---$/ { 
      if (in_frontmatter == 0) in_frontmatter=1; 
      else in_frontmatter=0; 
      next; 
    }
    in_frontmatter && $0 ~ "^" field ":" {
      sub("^" field ":[[:space:]]*", "");
      print;
      exit;
    }
  ' "$file"
}

# Helper function to extract description from markdown (first paragraph after frontmatter)
extract_description() {
  local file="$1"
  
  if [[ ! -f "$file" ]]; then
    echo ""
    return
  fi
  
  awk '
    BEGIN { in_frontmatter=0; frontmatter_ended=0; found_desc=0; }
    /^---$/ { 
      if (in_frontmatter == 0) in_frontmatter=1; 
      else { in_frontmatter=0; frontmatter_ended=1; }
      next; 
    }
    frontmatter_ended && !found_desc && NF > 0 && !/^#/ {
      print;
      found_desc=1;
      exit;
    }
  ' "$file"
}

# Read plugin.json
PLUGIN_JSON="$PLUGIN_DIR/.codebuddy-plugin/plugin.json"
if [[ ! -f "$PLUGIN_JSON" ]]; then
  echo "Error: plugin.json not found in $PLUGIN_DIR/.codebuddy-plugin/" >&2
  exit 1
fi

# Extract basic info from plugin.json
PLUGIN_NAME=$(jq -r '.name // "unknown"' "$PLUGIN_JSON")
PLUGIN_VERSION=$(jq -r '.version // "unknown"' "$PLUGIN_JSON")
PLUGIN_DESC=$(jq -r '.description // ""' "$PLUGIN_JSON")
PLUGIN_AUTHOR=$(jq -r '.author.name // "unknown"' "$PLUGIN_JSON")
PLUGIN_KEYWORDS=$(jq -r '.keywords // [] | join(", ")' "$PLUGIN_JSON")

# Start JSON output
echo "{"
echo "  \"name\": \"$PLUGIN_NAME\","
echo "  \"version\": \"$PLUGIN_VERSION\","
echo "  \"description\": \"$PLUGIN_DESC\","
echo "  \"author\": \"$PLUGIN_AUTHOR\","
echo "  \"keywords\": \"$PLUGIN_KEYWORDS\","

# Analyze Commands
echo "  \"commands\": ["
FIRST_CMD=true
if [[ -d "$PLUGIN_DIR/commands" ]]; then
  for cmd_file in "$PLUGIN_DIR/commands"/*.md; do
    if [[ -f "$cmd_file" ]]; then
      cmd_name=$(basename "$cmd_file" .md)
      cmd_desc=$(extract_yaml_field "$cmd_file" "description")
      cmd_args=$(extract_yaml_field "$cmd_file" "argument-hint")
      
      if [[ "$FIRST_CMD" == "false" ]]; then
        echo ","
      fi
      FIRST_CMD=false
      
      echo -n "    {"
      echo -n "\"name\": \"$cmd_name\", "
      echo -n "\"description\": \"${cmd_desc:-No description}\", "
      echo -n "\"arguments\": \"${cmd_args:-none}\""
      echo -n "}"
    fi
  done
fi
echo ""
echo "  ],"

# Analyze Agents
echo "  \"agents\": ["
FIRST_AGENT=true
if [[ -d "$PLUGIN_DIR/agents" ]]; then
  for agent_file in "$PLUGIN_DIR/agents"/*.md; do
    if [[ -f "$agent_file" ]]; then
      agent_name=$(basename "$agent_file" .md)
      agent_desc=$(extract_yaml_field "$agent_file" "description")
      when_to_use=$(extract_yaml_field "$agent_file" "whenToUse")
      
      if [[ "$FIRST_AGENT" == "false" ]]; then
        echo ","
      fi
      FIRST_AGENT=false
      
      echo -n "    {"
      echo -n "\"name\": \"$agent_name\", "
      echo -n "\"description\": \"${agent_desc:-No description}\", "
      echo -n "\"whenToUse\": \"${when_to_use:-Not specified}\""
      echo -n "}"
    fi
  done
fi
echo ""
echo "  ],"

# Analyze Skills
echo "  \"skills\": ["
FIRST_SKILL=true
if [[ -d "$PLUGIN_DIR/skills" ]]; then
  for skill_dir in "$PLUGIN_DIR/skills"/*; do
    if [[ -d "$skill_dir" ]] && [[ -f "$skill_dir/SKILL.md" ]]; then
      skill_name=$(basename "$skill_dir")
      skill_desc=$(extract_description "$skill_dir/SKILL.md")
      
      if [[ "$FIRST_SKILL" == "false" ]]; then
        echo ","
      fi
      FIRST_SKILL=false
      
      echo -n "    {"
      echo -n "\"name\": \"$skill_name\", "
      echo -n "\"description\": \"${skill_desc:-No description}\""
      echo -n "}"
    fi
  done
fi
echo ""
echo "  ],"

# Analyze Hooks
echo "  \"hooks\": ["
FIRST_HOOK=true
if [[ -f "$PLUGIN_DIR/hooks/hooks.json" ]]; then
  # Extract hook events from hooks.json (handles nested structure)
  # Structure: { "hooks": { "EventName": [...] } }
  HOOK_EVENTS=$(jq -r '.hooks | keys | .[]' "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null || echo "")
  
  for event in $HOOK_EVENTS; do
    # Get hook details from nested structure
    hook_count=$(jq -r ".hooks[\"$event\"] | length" "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null || echo "0")
    hook_names=$(jq -r ".hooks[\"$event\"][].name // \"unnamed\"" "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null | paste -sd "," -)
    hook_type=$(jq -r ".hooks[\"$event\"][0].hooks[0].type // \"unknown\"" "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null)
    
    if [[ "$FIRST_HOOK" == "false" ]]; then
      echo ","
    fi
    FIRST_HOOK=false
    
    echo -n "    {"
    echo -n "\"event\": \"$event\", "
    echo -n "\"type\": \"$hook_type\", "
    echo -n "\"count\": $hook_count, "
    echo -n "\"names\": \"$hook_names\", "
    echo -n "\"description\": \"Triggers on $event event\""
    echo -n "}"
  done
fi
echo ""
echo "  ],"

# Analyze MCP servers
echo "  \"mcp\": ["
FIRST_MCP=true
if [[ -f "$PLUGIN_DIR/.mcp.json" ]]; then
  # Extract MCP server names
  MCP_SERVERS=$(jq -r '.mcpServers | keys | .[]' "$PLUGIN_DIR/.mcp.json" 2>/dev/null || echo "")
  
  for server in $MCP_SERVERS; do
    server_type=$(jq -r ".mcpServers[\"$server\"].type // \"unknown\"" "$PLUGIN_DIR/.mcp.json")
    
    if [[ "$FIRST_MCP" == "false" ]]; then
      echo ","
    fi
    FIRST_MCP=false
    
    echo -n "    {"
    echo -n "\"name\": \"$server\", "
    echo -n "\"type\": \"$server_type\""
    echo -n "}"
  done
fi
echo ""
echo "  ],"

# Component counts
CMD_COUNT=$(find "$PLUGIN_DIR/commands" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
AGENT_COUNT=$(find "$PLUGIN_DIR/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find "$PLUGIN_DIR/skills" -maxdepth 1 -type d 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
HOOK_COUNT=0
if [[ -f "$PLUGIN_DIR/hooks/hooks.json" ]]; then
  # Count total hook events (top-level keys under "hooks")
  HOOK_COUNT=$(jq '.hooks | keys | length' "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null || echo "0")
fi
MCP_COUNT=0
if [[ -f "$PLUGIN_DIR/.mcp.json" ]]; then
  MCP_COUNT=$(jq '.mcpServers | keys | length' "$PLUGIN_DIR/.mcp.json" 2>/dev/null || echo "0")
fi

echo "  \"counts\": {"
echo "    \"commands\": $CMD_COUNT,"
echo "    \"agents\": $AGENT_COUNT,"
echo "    \"skills\": $SKILL_COUNT,"
echo "    \"hooks\": $HOOK_COUNT,"
echo "    \"mcp\": $MCP_COUNT"
echo "  }"

echo "}"
