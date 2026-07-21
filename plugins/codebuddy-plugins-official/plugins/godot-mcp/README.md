# Godot MCP (Model Context Protocol)

A comprehensive integration between Godot Engine and AI assistants using the Model Context Protocol (MCP). This plugin allows AI assistants to interact with your Godot projects, providing powerful capabilities for code assistance, scene manipulation, and project management.

## Features

- **Full Godot Project Access**: AI assistants can access and modify scripts, scenes, nodes, and project resources
- **Two-way Communication**: Send project data to AI and apply suggested changes directly in the editor
- **Command Categories**:
  - **Node Commands**: Create, modify, and manage nodes in your scenes
  - **Script Commands**: Edit, analyze, and create GDScript files
  - **Scene Commands**: Manipulate scenes and their structure
  - **Project Commands**: Access project settings and resources
  - **Editor Commands**: Control various editor functionality

## Quick Setup

### Environment Configuration

Godot MCP supports multiple environment configurations (development/production) with different backend URLs. See [CONFIG.md](CONFIG.md) for detailed instructions on:
- Environment setup and switching
- Backend service URLs
- API key configuration

**Quick switch:**
```bash
# Switch to development environment
./switch-env.sh dev

# Switch to production environment  
./switch-env.sh prod
```

### Option A: One-Click Deploy (Recommended)

```bash
cd server
npm install
npm run deploy
```

This will automatically:
- Build the MCP server
- Detect your Claude Desktop config location
- Inject the `godot-mcp` configuration
- Show next steps for Godot plugin setup

For advanced options:
```bash
# Dry run (preview changes without writing)
npm run deploy -- --dry-run

# Also copy plugin to your Godot project
npm run deploy -- --godot-project "C:\Games\MyProject"

# Check deployment status
npm run status
```

### Option B: Manual Setup

### Option B: Manual Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/anengyuki/Godot-mcp.git
cd Godot-mcp
```

#### 2. Set Up the MCP Server

```bash
cd server
npm install
npm run build
# Return to project root
cd ..
```

#### 3. Set Up Claude Desktop

1. Edit or create the Claude Desktop config file:
   ```bash
   # For macOS
   nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add the following configuration (or use the included `claude_desktop_config.json` as a reference):
   ```json
   {
	 "mcpServers": {
	   "godot-mcp": {
		 "command": "node",
		 "args": [
		   "PATH_TO_YOUR_PROJECT/server/dist/index.js"
		 ],
		 "env": {
		   "MCP_TRANSPORT": "stdio"
		 }
	   }
	 }
   }
   ```
   > **Note**: Replace `PATH_TO_YOUR_PROJECT` with the absolute path to where you have this repository stored.

3. Restart Claude Desktop

#### 4. Open the Example Project in Godot

1. Open Godot Engine
2. Select "Import" and navigate to the cloned repository
3. Open the `project.godot` file
4. The MCP plugin is already enabled in this example project

## Using MCP with Claude

After setup, you can work with your Godot project directly from Claude using natural language. Here are some examples:

### Example Prompts

```
@mcp godot-mcp read godot/script

I need help optimizing my player movement code. Can you suggest improvements?
```

```
@mcp godot-mcp run list_nodes

Add a cube in the middle of the scene and then make a camera that is looking at the cube.
```

```
@mcp godot-mcp read godot/scene/current

Create an enemy AI that patrols between waypoints and attacks the player when in range.
```

### Natural Language Tasks Claude Can Perform

- "Create a main menu with play, options, and quit buttons"
- "Add collision detection to the player character"
- "Implement a day/night cycle system"
- "Refactor this code to use signals instead of direct references"
- "Debug why my player character falls through the floor sometimes"

## Available Resources and Commands

### Resource Endpoints:
- `godot/script` - The currently open script content
- `godot/script/metadata` - Metadata of the currently open script
- `godot/scripts` - List of all scripts in the project
- `godot/scene/current` - The currently open scene with structure
- `godot/scenes` - List of all scenes in the project
- `godot/project/structure` - Project directory structure
- `godot/project/settings` - Project settings
- `godot/project/resources` - List of project resources
- `godot/editor/state` - Current editor state
- `godot/editor/selected_node` - Currently selected node info
- `godot/editor/current_script` - Currently edited script

### Command Categories:

#### Node Commands
- `list_nodes` - List child nodes under a parent
- `get_node_properties` - Gets properties of a specific node
- `create_node` - Creates a new node
- `delete_node` - Deletes a node
- `update_node_property` - Updates a node property

#### Script Commands
- `create_script` - Creates a new script file
- `edit_script` - Updates script content
- `get_script` - Gets script content by path or node
- `create_script_template` - Generates a script template

#### Scene Commands
- `create_scene` - Creates a new scene
- `open_scene` - Opens a scene in the editor
- `save_scene` - Saves current scene
- `get_current_scene` - Gets current scene info

#### Project Commands
- `get_project_info` - Gets project info and Godot version
- `get_project_settings` - Gets project settings
- `list_project_files` - Lists project files by extension
- `list_project_resources` - Lists categorized project resources

#### Editor Commands
- `get_editor_state` - Gets current editor state
- `get_selected_nodes` - Gets selected node info
- `run_project` - Runs the project
- `stop_project` - Stops the running project
- `execute_editor_script` - Executes GDScript in editor context
- `create_resource` - Creates a new resource file

## Troubleshooting

### Quick Diagnosis

```bash
cd server
npm run status:diagnose
```

### Connection Issues
- Ensure the plugin is enabled in Godot's Project Settings
- Check the Godot console for any error messages
- Verify the server is running when Claude Desktop launches it

### Plugin Not Working
- Reload Godot project after any configuration changes
- Check for error messages in the Godot console
- Make sure all paths in your Claude Desktop config are absolute and correct

For detailed troubleshooting steps, see [Troubleshooting Guide](docs/troubleshooting-guide.md).

## Adding the Plugin to Your Own Godot Project

If you want to use the MCP plugin in your own Godot project:

1. Copy the `addons/godot_mcp` folder to your Godot project's `addons` directory
2. Open your project in Godot
3. Go to Project > Project Settings > Plugins
4. Enable the "Godot MCP" plugin

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Documentation

For more detailed information, check the documentation in the `docs` folder:

- [Getting Started](docs/getting-started.md)
- [Installation Guide](docs/installation-guide.md)
- [Command Reference](docs/command-reference.md)
- [Troubleshooting Guide](docs/troubleshooting-guide.md)
- [Architecture](docs/architecture.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
