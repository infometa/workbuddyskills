@tool
class_name MCPNodeCommands
extends MCPBaseCommandProcessor

func process_command(client_id: int, command_type: String, params: Dictionary, command_id: String) -> bool:
	match command_type:
		"create_node":
			_create_node(client_id, params, command_id)
			return true
		"delete_node":
			_delete_node(client_id, params, command_id)
			return true
		"update_node_property":
			_update_node_property(client_id, params, command_id)
			return true
		"get_node_properties":
			_get_node_properties(client_id, params, command_id)
			return true
		"list_nodes":
			_list_nodes(client_id, params, command_id)
			return true
	return false  # Command not handled

func _create_node(client_id: int, params: Dictionary, command_id: String) -> void:
	var parent_path = params.get("parent_path", "/root")
	var node_type = params.get("node_type", "Node")
	var node_name = params.get("node_name", "NewNode")
	
	# Validation
	if not ClassDB.class_exists(node_type):
		return _send_error(client_id, "Invalid node type: %s" % node_type, command_id)
	
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	var edited_scene_root = editor_interface.get_edited_scene_root()
	
	if not edited_scene_root:
		return _send_error(client_id, "No scene is currently being edited", command_id)
	
	# Get the parent node using the editor node helper
	var parent = _get_editor_node(parent_path)
	if not parent:
		return _send_error(client_id, "Parent node not found: %s" % parent_path, command_id)
	
	# Create the node
	var node
	if ClassDB.can_instantiate(node_type):
		node = ClassDB.instantiate(node_type)
	else:
		return _send_error(client_id, "Cannot instantiate node of type: %s" % node_type, command_id)
	
	if not node:
		return _send_error(client_id, "Failed to create node of type: %s" % node_type, command_id)
	
	# Set the node name
	node.name = node_name
	
	# Add the node to the parent
	parent.add_child(node)
	
	# Set owner for proper serialization
	node.owner = edited_scene_root
	
	# Mark the scene as modified
	_mark_scene_modified()
	
	_send_success(client_id, {
		"node_path": parent_path + "/" + node_name
	}, command_id)

func _delete_node(client_id: int, params: Dictionary, command_id: String) -> void:
	var node_path = params.get("node_path", "")
	
	# Validation
	if node_path.is_empty():
		return _send_error(client_id, "Node path cannot be empty", command_id)
	
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	var edited_scene_root = editor_interface.get_edited_scene_root()
	
	if not edited_scene_root:
		return _send_error(client_id, "No scene is currently being edited", command_id)
	
	# Get the node using the editor node helper
	var node = _get_editor_node(node_path)
	if not node:
		return _send_error(client_id, "Node not found: %s" % node_path, command_id)
	
	# Cannot delete the root node
	if node == edited_scene_root:
		return _send_error(client_id, "Cannot delete the root node", command_id)
	
	# Get parent for operation
	var parent = node.get_parent()
	if not parent:
		return _send_error(client_id, "Node has no parent: %s" % node_path, command_id)
	
	# Remove the node
	parent.remove_child(node)
	node.queue_free()
	
	# Mark the scene as modified
	_mark_scene_modified()
	
	_send_success(client_id, {
		"deleted_node_path": node_path
	}, command_id)

func _update_node_property(client_id: int, params: Dictionary, command_id: String) -> void:
	var node_path = params.get("node_path", "")
	var property_name = params.get("property", "")
	var property_value = params.get("value")
	
	# Validation
	if node_path.is_empty():
		return _send_error(client_id, "Node path cannot be empty", command_id)
	
	if property_name.is_empty():
		return _send_error(client_id, "Property name cannot be empty", command_id)
	
	if property_value == null:
		return _send_error(client_id, "Property value cannot be null", command_id)
	
	# Get editor plugin and interfaces
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found in Engine metadata", command_id)
	
	# Get the node using the editor node helper
	var node = _get_editor_node(node_path)
	if not node:
		return _send_error(client_id, "Node not found: %s" % node_path, command_id)
	
	# Check if the property exists
	if not property_name in node:
		return _send_error(client_id, "Property %s does not exist on node %s" % [property_name, node_path], command_id)
	
	# Get current property value for type inference and undo
	var old_value = node.get(property_name)
	var old_type = typeof(old_value)
	
	# Parse property value based on target property type
	var parsed_value = _parse_property_value_with_type_hint(property_value, old_type, old_value)
	
	print("[MCP] Updating property '%s' on node '%s'" % [property_name, node_path])
	print("[MCP] Input value: %s (type: %s)" % [str(property_value), typeof(property_value)])
	print("[MCP] Parsed value: %s (type: %s)" % [str(parsed_value), typeof(parsed_value)])
	print("[MCP] Old value: %s (type: %s)" % [str(old_value), old_type])
	
	# Get undo/redo system
	var undo_redo = _get_undo_redo()
	if not undo_redo:
		# Fallback method if we can't get undo/redo
		node.set(property_name, parsed_value)
		_mark_scene_modified()
	else:
		# Use undo/redo for proper editor integration
		undo_redo.create_action("Update Property: " + property_name)
		undo_redo.add_do_property(node, property_name, parsed_value)
		undo_redo.add_undo_property(node, property_name, old_value)
		undo_redo.commit_action()
	
	# Mark the scene as modified
	_mark_scene_modified()
	
	_send_success(client_id, {
		"node_path": node_path,
		"property": property_name,
		"value": property_value,
		"parsed_value": str(parsed_value),
		"old_value": str(old_value)
	}, command_id)

# Parse property value with type hint from the existing property
func _parse_property_value_with_type_hint(value, target_type: int, old_value) -> Variant:
	# If value is already the correct type, return it
	if typeof(value) == target_type:
		return value
	
	# Handle arrays - convert based on target type
	if typeof(value) == TYPE_ARRAY:
		var arr = value as Array
		match target_type:
			TYPE_VECTOR2:
				if arr.size() >= 2:
					return Vector2(arr[0], arr[1])
			TYPE_VECTOR2I:
				if arr.size() >= 2:
					return Vector2i(int(arr[0]), int(arr[1]))
			TYPE_VECTOR3:
				if arr.size() >= 3:
					return Vector3(arr[0], arr[1], arr[2])
			TYPE_VECTOR3I:
				if arr.size() >= 3:
					return Vector3i(int(arr[0]), int(arr[1]), int(arr[2]))
			TYPE_VECTOR4:
				if arr.size() >= 4:
					return Vector4(arr[0], arr[1], arr[2], arr[3])
			TYPE_VECTOR4I:
				if arr.size() >= 4:
					return Vector4i(int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3]))
			TYPE_COLOR:
				if arr.size() >= 3:
					var a = arr[3] if arr.size() >= 4 else 1.0
					return Color(arr[0], arr[1], arr[2], a)
			TYPE_QUATERNION:
				if arr.size() >= 4:
					return Quaternion(arr[0], arr[1], arr[2], arr[3])
			TYPE_RECT2:
				if arr.size() >= 4:
					return Rect2(arr[0], arr[1], arr[2], arr[3])
			TYPE_RECT2I:
				if arr.size() >= 4:
					return Rect2i(int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3]))
			TYPE_TRANSFORM2D:
				if arr.size() >= 6:
					return Transform2D(Vector2(arr[0], arr[1]), Vector2(arr[2], arr[3]), Vector2(arr[4], arr[5]))
			TYPE_BASIS:
				if arr.size() >= 9:
					return Basis(Vector3(arr[0], arr[1], arr[2]), Vector3(arr[3], arr[4], arr[5]), Vector3(arr[6], arr[7], arr[8]))
		# Fallback to generic parsing
		return _parse_property_value(value)
	
	# Handle dictionaries
	if typeof(value) == TYPE_DICTIONARY:
		var dict = value as Dictionary
		match target_type:
			TYPE_VECTOR2:
				if dict.has("x") and dict.has("y"):
					return Vector2(dict["x"], dict["y"])
			TYPE_VECTOR2I:
				if dict.has("x") and dict.has("y"):
					return Vector2i(int(dict["x"]), int(dict["y"]))
			TYPE_VECTOR3:
				if dict.has("x") and dict.has("y") and dict.has("z"):
					return Vector3(dict["x"], dict["y"], dict["z"])
			TYPE_VECTOR3I:
				if dict.has("x") and dict.has("y") and dict.has("z"):
					return Vector3i(int(dict["x"]), int(dict["y"]), int(dict["z"]))
			TYPE_COLOR:
				if dict.has("r") and dict.has("g") and dict.has("b"):
					var a = dict.get("a", 1.0)
					return Color(dict["r"], dict["g"], dict["b"], a)
			TYPE_QUATERNION:
				if dict.has("x") and dict.has("y") and dict.has("z") and dict.has("w"):
					return Quaternion(dict["x"], dict["y"], dict["z"], dict["w"])
		# Fallback to generic parsing
		return _parse_property_value(value)
	
	# Handle numeric conversions for rotation (degrees to radians)
	if target_type == TYPE_FLOAT and (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT):
		# Check if this might be a rotation property and the value seems to be in degrees
		return float(value)
	
	# Use generic parsing as fallback
	return _parse_property_value(value)

func _get_node_properties(client_id: int, params: Dictionary, command_id: String) -> void:
	var node_path = params.get("node_path", "")
	
	# Validation
	if node_path.is_empty():
		return _send_error(client_id, "Node path cannot be empty", command_id)
	
	# Get the node using the editor node helper
	var node = _get_editor_node(node_path)
	if not node:
		return _send_error(client_id, "Node not found: %s" % node_path, command_id)
	
	# Get all properties
	var properties = {}
	var property_list = node.get_property_list()
	
	for prop in property_list:
		var name = prop["name"]
		if not name.begins_with("_"):  # Skip internal properties
			properties[name] = node.get(name)
	
	_send_success(client_id, {
		"node_path": node_path,
		"properties": properties
	}, command_id)

func _list_nodes(client_id: int, params: Dictionary, command_id: String) -> void:
	var parent_path = params.get("parent_path", "/root")
	
	# Get the parent node using the editor node helper
	var parent = _get_editor_node(parent_path)
	if not parent:
		return _send_error(client_id, "Parent node not found: %s" % parent_path, command_id)
	
	# Get children
	var children = []
	for child in parent.get_children():
		children.append({
			"name": child.name,
			"type": child.get_class(),
			"path": str(child.get_path()).replace(str(parent.get_path()), parent_path)
		})
	
	_send_success(client_id, {
		"parent_path": parent_path,
		"children": children
	}, command_id)
