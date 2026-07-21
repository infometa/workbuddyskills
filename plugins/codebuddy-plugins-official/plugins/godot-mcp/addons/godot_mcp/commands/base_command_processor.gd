@tool
class_name MCPBaseCommandProcessor
extends Node

# Signal emitted when a command has completed processing
signal command_completed(client_id, command_type, result, command_id)

# Reference to the server - passed by the command handler
var _websocket_server = null

# Must be implemented by subclasses
func process_command(client_id: int, command_type: String, params: Dictionary, command_id: String) -> bool:
	push_error("BaseCommandProcessor.process_command called directly")
	return false

# Helper functions common to all command processors
func _send_success(client_id: int, result: Dictionary, command_id: String) -> void:
	var response = {
		"status": "success",
		"result": result
	}
	
	if not command_id.is_empty():
		response["commandId"] = command_id
	
	# Emit the signal for local processing (useful for testing)
	command_completed.emit(client_id, "success", result, command_id)
	
	# Send to websocket if available
	if _websocket_server:
		_websocket_server.send_response(client_id, response)

func _send_error(client_id: int, message: String, command_id: String) -> void:
	var response = {
		"status": "error",
		"message": message
	}
	
	if not command_id.is_empty():
		response["commandId"] = command_id
	
	# Emit the signal for local processing (useful for testing)
	var error_result = {"error": message}
	command_completed.emit(client_id, "error", error_result, command_id)
	
	# Send to websocket if available
	if _websocket_server:
		_websocket_server.send_response(client_id, response)
	print("Error: %s" % message)

# Common utility methods
func _get_editor_node(path: String) -> Node:
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		print("GodotMCPPlugin not found in Engine metadata")
		return null
		
	var editor_interface = plugin.get_editor_interface()
	var edited_scene_root = editor_interface.get_edited_scene_root()
	
	if not edited_scene_root:
		print("No edited scene found")
		return null
		
	# Handle absolute paths
	if path == "/root" or path == "":
		return edited_scene_root
		
	if path.begins_with("/root/"):
		path = path.substr(6)  # Remove "/root/"
	elif path.begins_with("/"):
		path = path.substr(1)  # Remove leading "/"
	
	# Try to find node as child of edited scene root
	return edited_scene_root.get_node_or_null(path)

# Helper function to mark a scene as modified
func _mark_scene_modified() -> void:
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		print("GodotMCPPlugin not found in Engine metadata")
		return
	
	var editor_interface = plugin.get_editor_interface()
	var edited_scene_root = editor_interface.get_edited_scene_root()
	
	if edited_scene_root:
		# This internally marks the scene as modified in the editor
		editor_interface.mark_scene_as_unsaved()

# Helper function to access the EditorUndoRedoManager
func _get_undo_redo():
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin or not plugin.has_method("get_undo_redo"):
		print("Cannot access UndoRedo from plugin")
		return null
		
	return plugin.get_undo_redo()

# Helper function to parse property values from string to proper Godot types
func _parse_property_value(value):
	# Handle arrays - convert to Vector2, Vector3, Color, etc.
	if typeof(value) == TYPE_ARRAY:
		var arr = value as Array
		match arr.size():
			2:
				# Could be Vector2 or Vector2i
				if typeof(arr[0]) == TYPE_INT and typeof(arr[1]) == TYPE_INT:
					return Vector2i(arr[0], arr[1])
				return Vector2(arr[0], arr[1])
			3:
				# Could be Vector3, Vector3i, or Euler angles (rotation)
				if typeof(arr[0]) == TYPE_INT and typeof(arr[1]) == TYPE_INT and typeof(arr[2]) == TYPE_INT:
					return Vector3i(arr[0], arr[1], arr[2])
				return Vector3(arr[0], arr[1], arr[2])
			4:
				# Could be Vector4, Color, or Quaternion
				# Assume Color if all values are between 0 and 1, otherwise Vector4
				var all_normalized = true
				for v in arr:
					if v < 0 or v > 1:
						all_normalized = false
						break
				if all_normalized:
					return Color(arr[0], arr[1], arr[2], arr[3])
				return Vector4(arr[0], arr[1], arr[2], arr[3])
		# For other array sizes, return as-is
		return arr
	
	# Handle dictionaries - could be Vector, Color, Transform, etc.
	if typeof(value) == TYPE_DICTIONARY:
		var dict = value as Dictionary
		# Check for Vector2 format {"x": ..., "y": ...}
		if dict.has("x") and dict.has("y") and dict.size() == 2:
			return Vector2(dict["x"], dict["y"])
		# Check for Vector3 format {"x": ..., "y": ..., "z": ...}
		if dict.has("x") and dict.has("y") and dict.has("z") and dict.size() == 3:
			return Vector3(dict["x"], dict["y"], dict["z"])
		# Check for Color format {"r": ..., "g": ..., "b": ..., "a": ...}
		if dict.has("r") and dict.has("g") and dict.has("b"):
			var a = dict.get("a", 1.0)
			return Color(dict["r"], dict["g"], dict["b"], a)
		# Check for rotation in degrees format {"degrees": ...} or {"deg": ...}
		if dict.has("degrees"):
			return deg_to_rad(dict["degrees"])
		if dict.has("deg"):
			return deg_to_rad(dict["deg"])
		# Check for Quaternion format
		if dict.has("x") and dict.has("y") and dict.has("z") and dict.has("w"):
			return Quaternion(dict["x"], dict["y"], dict["z"], dict["w"])
		# Return dict as-is for other cases
		return dict
	
	# Only try to parse strings that look like they could be Godot types
	if typeof(value) == TYPE_STRING and (
		value.begins_with("Vector") or 
		value.begins_with("Transform") or 
		value.begins_with("Rect") or 
		value.begins_with("Color") or
		value.begins_with("Quat") or
		value.begins_with("Basis") or
		value.begins_with("Plane") or
		value.begins_with("AABB") or
		value.begins_with("Projection") or
		value.begins_with("Callable") or
		value.begins_with("Signal") or
		value.begins_with("PackedVector") or
		value.begins_with("PackedString") or
		value.begins_with("PackedFloat") or
		value.begins_with("PackedInt") or
		value.begins_with("PackedColor") or
		value.begins_with("PackedByteArray") or
		value.begins_with("Dictionary") or
		value.begins_with("Array")
	):
		var expression = Expression.new()
		var error = expression.parse(value, [])
		
		if error == OK:
			var result = expression.execute([], null, true)
			if not expression.has_execute_failed():
				print("Successfully parsed %s as %s" % [value, result])
				return result
			else:
				print("Failed to execute expression for: %s" % value)
		else:
			print("Failed to parse expression: %s (Error: %d)" % [value, error])
	
	# Otherwise, return value as is
	return value
