@tool
class_name MCPEditorCommands
extends MCPBaseCommandProcessor

func process_command(client_id: int, command_type: String, params: Dictionary, command_id: String) -> bool:
	match command_type:
		"get_editor_state":
			_get_editor_state(client_id, params, command_id)
			return true
		"get_selected_node":
			_get_selected_node(client_id, params, command_id)
			return true
		"create_resource":
			_create_resource(client_id, params, command_id)
			return true
		"run_project":
			_run_project(client_id, params, command_id)
			return true
		"stop_project":
			_stop_project(client_id, params, command_id)
			return true
		"get_editor_output":
			_get_editor_output(client_id, params, command_id)
			return true
	return false  # Command not handled

func _get_editor_state(client_id: int, params: Dictionary, command_id: String) -> void:
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	
	var state = {
		"current_scene": "",
		"current_script": "",
		"selected_nodes": [],
		"is_playing": editor_interface.is_playing_scene()
	}
	
	# Get current scene
	var edited_scene_root = editor_interface.get_edited_scene_root()
	if edited_scene_root:
		state["current_scene"] = edited_scene_root.scene_file_path
	
	# Get current script if any is being edited
	var script_editor = editor_interface.get_script_editor()
	var current_script = script_editor.get_current_script()
	if current_script:
		state["current_script"] = current_script.resource_path
	
	# Get selected nodes
	var selection = editor_interface.get_selection()
	var selected_nodes = selection.get_selected_nodes()
	
	for node in selected_nodes:
		state["selected_nodes"].append({
			"name": node.name,
			"path": str(node.get_path())
		})
	
	_send_success(client_id, state, command_id)

func _get_selected_node(client_id: int, params: Dictionary, command_id: String) -> void:
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	var selection = editor_interface.get_selection()
	var selected_nodes = selection.get_selected_nodes()
	
	if selected_nodes.size() == 0:
		return _send_success(client_id, {
			"selected": false,
			"message": "No node is currently selected"
		}, command_id)
	
	var node = selected_nodes[0]  # Get the first selected node
	
	# Get node info
	var node_data = {
		"selected": true,
		"name": node.name,
		"type": node.get_class(),
		"path": str(node.get_path())
	}
	
	# Get script info if available
	var script = node.get_script()
	if script:
		node_data["script_path"] = script.resource_path
	
	# Get important properties
	var properties = {}
	var property_list = node.get_property_list()
	
	for prop in property_list:
		var name = prop["name"]
		if not name.begins_with("_"):  # Skip internal properties
			# Only include some common properties to avoid overwhelming data
			if name in ["position", "rotation", "scale", "visible", "modulate", "z_index"]:
				properties[name] = node.get(name)
	
	node_data["properties"] = properties
	
	_send_success(client_id, node_data, command_id)

func _create_resource(client_id: int, params: Dictionary, command_id: String) -> void:
	var resource_type = params.get("resource_type", "")
	var resource_path = params.get("resource_path", "")
	var properties = params.get("properties", {})
	
	# Validation
	if resource_type.is_empty():
		return _send_error(client_id, "Resource type cannot be empty", command_id)
	
	if resource_path.is_empty():
		return _send_error(client_id, "Resource path cannot be empty", command_id)
	
	# Make sure we have an absolute path
	if not resource_path.begins_with("res://"):
		resource_path = "res://" + resource_path
	
	# Get editor interface
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	
	# Create the resource
	var resource
	
	if ClassDB.class_exists(resource_type):
		if ClassDB.is_parent_class(resource_type, "Resource"):
			resource = ClassDB.instantiate(resource_type)
			if not resource:
				return _send_error(client_id, "Failed to instantiate resource: %s" % resource_type, command_id)
		else:
			return _send_error(client_id, "Type is not a Resource: %s" % resource_type, command_id)
	else:
		return _send_error(client_id, "Invalid resource type: %s" % resource_type, command_id)
	
	# Set properties
	for key in properties:
		resource.set(key, properties[key])
	
	# Create directory if needed
	var dir = resource_path.get_base_dir()
	if not DirAccess.dir_exists_absolute(dir):
		var err = DirAccess.make_dir_recursive_absolute(dir)
		if err != OK:
			return _send_error(client_id, "Failed to create directory: %s (Error code: %d)" % [dir, err], command_id)
	
	# Save the resource
	var result = ResourceSaver.save(resource, resource_path)
	if result != OK:
		return _send_error(client_id, "Failed to save resource: %d" % result, command_id)
	
	# Refresh the filesystem
	editor_interface.get_resource_filesystem().scan()
	
	_send_success(client_id, {
		"resource_path": resource_path,
		"resource_type": resource_type
	}, command_id)

func _run_project(client_id: int, params: Dictionary, command_id: String) -> void:
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	
	# Check if already running
	if editor_interface.is_playing_scene():
		return _send_success(client_id, {
			"message": "Project is already running"
		}, command_id)
	
	# Play the project
	editor_interface.play_main_scene()
	
	_send_success(client_id, {
		"message": "Project started"
	}, command_id)

func _stop_project(client_id: int, params: Dictionary, command_id: String) -> void:
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	
	# Check if not running
	if not editor_interface.is_playing_scene():
		return _send_success(client_id, {
			"message": "Project is not running"
		}, command_id)
	
	# Stop the project
	editor_interface.stop_playing_scene()
	
	_send_success(client_id, {
		"message": "Project stopped"
	}, command_id)

func _get_editor_output(client_id: int, params: Dictionary, command_id: String) -> void:
	var lines_count: int = params.get("lines", 100)
	var filter_type: String = params.get("filter", "all")
	
	# Godot 4 log file: user://logs/godot.log
	var log_dir = OS.get_user_data_dir().path_join("logs")
	var log_path = log_dir.path_join("godot.log")
	
	if not FileAccess.file_exists(log_path):
		return _send_error(client_id, "Log file not found at: %s" % log_path, command_id)
	
	var file = FileAccess.open(log_path, FileAccess.READ)
	if not file:
		return _send_error(client_id, "Cannot open log file: %s" % log_path, command_id)
	
	var content = file.get_as_text()
	file.close()
	
	var all_lines = content.split("\n")
	var filtered_lines: PackedStringArray = []
	
	for line in all_lines:
		if filter_type == "all":
			filtered_lines.append(line)
		elif filter_type == "errors":
			var lower = line.to_lower()
			if lower.contains("error") or lower.contains("script error") \
				or lower.contains("failed") or lower.contains("invalid") \
				or line.begins_with("  ") and filtered_lines.size() > 0:
				filtered_lines.append(line)
		elif filter_type == "warnings":
			var lower = line.to_lower()
			if lower.contains("warning") or lower.contains("warn"):
				filtered_lines.append(line)
	
	# Return last N lines
	var start_idx = max(0, filtered_lines.size() - lines_count)
	var output_lines = filtered_lines.slice(start_idx)
	
	# Also collect script errors from the script editor
	var script_errors: Array = []
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if plugin:
		var editor_interface = plugin.get_editor_interface()
		var script_editor = editor_interface.get_script_editor()
		var open_scripts = script_editor.get_open_scripts()
		for s in open_scripts:
			if s is GDScript:
				var err_list = s.get_script_signal_list()
				if not s.is_tool() and not s.can_instantiate():
					script_errors.append({
						"script": s.resource_path,
						"status": "has_errors"
					})
	
	_send_success(client_id, {
		"log_path": log_path,
		"total_lines": all_lines.size(),
		"returned_lines": output_lines.size(),
		"filter": filter_type,
		"output": "\n".join(output_lines),
		"script_errors": script_errors
	}, command_id)