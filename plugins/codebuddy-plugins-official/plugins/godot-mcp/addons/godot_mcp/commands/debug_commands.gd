@tool
class_name MCPDebugCommands
extends MCPBaseCommandProcessor
## Debug monitoring and auto-fix workflow commands
## Enables automatic error detection, log capture, and push-to-IDE debug cycles

var _monitor_active: bool = false
var _monitor_timer: Timer = null
var _last_log_position: int = 0
var _error_buffer: Array[Dictionary] = []
var _last_error_hash: String = ""
var _monitor_client_id: int = -1
var _monitor_command_id: String = ""

func process_command(client_id: int, command_type: String, params: Dictionary, command_id: String) -> bool:
	match command_type:
		"start_debug_monitor":
			_start_debug_monitor(client_id, params, command_id)
			return true
		"stop_debug_monitor":
			_stop_debug_monitor(client_id, params, command_id)
			return true
		"get_debug_errors":
			_get_debug_errors(client_id, params, command_id)
			return true
		"get_debug_output":
			_get_debug_output(client_id, params, command_id)
			return true
		"get_runtime_errors":
			_get_runtime_errors(client_id, params, command_id)
			return true
	return false

## Start the debug monitor - polls for errors and pushes them to the client
func _start_debug_monitor(client_id: int, params: Dictionary, command_id: String) -> void:
	if _monitor_active:
		return _send_success(client_id, {
			"status": "already_active",
			"message": "Debug monitor is already running"
		}, command_id)
	
	var interval: float = params.get("interval", 3.0)
	interval = clampf(interval, 1.0, 30.0)
	
	_monitor_client_id = client_id
	_monitor_command_id = command_id
	_monitor_active = true
	_error_buffer.clear()
	_last_error_hash = ""
	
	# Reset log position to current end
	_last_log_position = _get_log_file_size()
	
	# Create polling timer
	if _monitor_timer:
		_monitor_timer.queue_free()
	
	_monitor_timer = Timer.new()
	_monitor_timer.wait_time = interval
	_monitor_timer.autostart = true
	_monitor_timer.timeout.connect(_on_monitor_tick)
	add_child(_monitor_timer)
	
	# Also connect to filesystem changes for event-driven detection
	var fs = EditorInterface.get_resource_filesystem()
	if fs and not fs.filesystem_changed.is_connected(_on_filesystem_changed):
		fs.filesystem_changed.connect(_on_filesystem_changed)
	
	_send_success(client_id, {
		"status": "started",
		"interval": interval,
		"message": "Debug monitor started, polling every %.1f seconds" % interval
	}, command_id)

## Stop the debug monitor
func _stop_debug_monitor(client_id: int, params: Dictionary, command_id: String) -> void:
	if not _monitor_active:
		return _send_success(client_id, {
			"status": "not_active",
			"message": "Debug monitor is not running"
		}, command_id)
	
	_cleanup_monitor()
	
	_send_success(client_id, {
		"status": "stopped",
		"message": "Debug monitor stopped",
		"errors_captured": _error_buffer.size()
	}, command_id)

## Get all current errors (compile + runtime) - one-shot pull
func _get_debug_errors(client_id: int, params: Dictionary, command_id: String) -> void:
	var include_log_errors: bool = params.get("include_log_errors", true)
	var directory: String = params.get("directory", "res://")
	var exclude_addons: bool = params.get("exclude_addons", true)
	
	var all_errors: Array[Dictionary] = []
	
	# 1. Get script compilation errors
	var script_errors = _collect_script_errors(directory, exclude_addons)
	all_errors.append_array(script_errors)
	
	# 2. Get log errors if requested
	var log_errors: Array[Dictionary] = []
	if include_log_errors:
		log_errors = _read_new_log_errors()
		all_errors.append_array(log_errors)
	
	_send_success(client_id, {
		"errors": all_errors,
		"total_errors": all_errors.size(),
		"compile_errors": script_errors.size(),
		"log_errors": log_errors.size(),
		"timestamp": Time.get_datetime_string_from_system()
	}, command_id)

## Get raw debug output from Godot log
func _get_debug_output(client_id: int, params: Dictionary, command_id: String) -> void:
	var lines_count: int = params.get("lines", 50)
	var filter: String = params.get("filter", "")
	
	var log_content = _read_godot_log_tail(lines_count)
	
	if not filter.is_empty():
		var filtered: Array[String] = []
		for line in log_content:
			if line.to_lower().contains(filter.to_lower()):
				filtered.append(line)
		log_content = filtered
	
	_send_success(client_id, {
		"output": log_content,
		"line_count": log_content.size(),
		"log_path": _get_log_path()
	}, command_id)

## Get runtime errors from log (errors that occurred during game execution)
func _get_runtime_errors(client_id: int, params: Dictionary, command_id: String) -> void:
	var log_lines = _read_godot_log_tail(200)
	var runtime_errors: Array[Dictionary] = []
	
	for i in range(log_lines.size()):
		var line = log_lines[i]
		var error_info = _parse_log_line_for_error(line, i)
		if error_info:
			# Add surrounding context
			var context_before: Array[String] = []
			var context_after: Array[String] = []
			for j in range(max(0, i - 3), i):
				context_before.append(log_lines[j])
			for j in range(i + 1, min(log_lines.size(), i + 4)):
				context_after.append(log_lines[j])
			error_info["context_before"] = context_before
			error_info["context_after"] = context_after
			runtime_errors.append(error_info)
	
	_send_success(client_id, {
		"runtime_errors": runtime_errors,
		"total": runtime_errors.size(),
		"timestamp": Time.get_datetime_string_from_system()
	}, command_id)

# ─── Internal: Monitor tick ───

func _on_monitor_tick() -> void:
	if not _monitor_active:
		return
	
	var new_errors = _collect_all_new_errors()
	if new_errors.is_empty():
		return
	
	# Hash to detect if errors actually changed
	var error_hash = str(new_errors).md5_text()
	if error_hash == _last_error_hash:
		return
	_last_error_hash = error_hash
	
	# Store in buffer
	_error_buffer.append_array(new_errors)
	
	# Push to client via debug_event
	_push_debug_event(new_errors)

func _on_filesystem_changed() -> void:
	if not _monitor_active:
		return
	# Debounce: wait a bit for files to settle
	await get_tree().create_timer(0.5).timeout
	_on_monitor_tick()

func _push_debug_event(errors: Array[Dictionary]) -> void:
	if _monitor_client_id < 0 or not _websocket_server:
		return
	
	var event = {
		"type": "debug_event",
		"event": "errors_detected",
		"data": {
			"timestamp": Time.get_datetime_string_from_system(),
			"errors": errors,
			"summary": {
				"total_errors": errors.size(),
				"files_affected": _count_unique_files(errors)
			}
		}
	}
	
	_websocket_server.send_response(_monitor_client_id, event)
	print("[DebugMonitor] Pushed %d errors to client" % errors.size())

# ─── Internal: Error collection ───

func _collect_all_new_errors() -> Array[Dictionary]:
	var errors: Array[Dictionary] = []
	errors.append_array(_collect_script_errors("res://", true))
	errors.append_array(_read_new_log_errors())
	return errors

func _collect_script_errors(directory: String, exclude_addons: bool) -> Array[Dictionary]:
	var errors: Array[Dictionary] = []
	var scripts = _find_all_scripts(directory, exclude_addons)
	
	for script_path in scripts:
		var file = FileAccess.open(script_path, FileAccess.READ)
		if file == null:
			errors.append({
				"type": "file_error",
				"file": script_path,
				"line": 0,
				"message": "Cannot open file",
				"severity": "error"
			})
			continue
		
		var content = file.get_as_text()
		file = null
		
		var validation = _validate_gdscript_quick(script_path, content)
		if not validation.is_valid:
			for err in validation.errors:
				errors.append({
					"type": err.get("type", "compile_error"),
					"file": script_path,
					"line": err.get("line", 0),
					"message": err.get("message", "Unknown error"),
					"severity": "error"
				})
	
	return errors

func _validate_gdscript_quick(script_path: String, content: String) -> Dictionary:
	var result = {"is_valid": true, "errors": []}
	
	var test_script = GDScript.new()
	test_script.source_code = content
	var err = test_script.reload(false)
	
	if err != OK:
		result.is_valid = false
		result.errors.append({
			"type": "compile_error",
			"message": "Compilation failed (error code: %d)" % err,
			"line": _find_error_line_quick(content),
			"file": script_path
		})
	
	return result

func _find_error_line_quick(content: String) -> int:
	# Simple heuristic: find first line with obvious syntax issue
	var lines = content.split("\n")
	var bracket_count = 0
	for i in range(lines.size()):
		var line = lines[i].strip_edges()
		if line.begins_with("#") or line.is_empty():
			continue
		bracket_count += line.count("(") - line.count(")")
		if bracket_count < 0:
			return i + 1
	return 1

# ─── Internal: Log reading ───

func _get_log_path() -> String:
	return OS.get_user_data_dir().path_join("logs/godot.log")

func _get_log_file_size() -> int:
	var path = _get_log_path()
	if not FileAccess.file_exists(path):
		return 0
	var f = FileAccess.open(path, FileAccess.READ)
	if not f:
		return 0
	var size = f.get_length()
	return size

func _read_new_log_errors() -> Array[Dictionary]:
	var errors: Array[Dictionary] = []
	var path = _get_log_path()
	
	if not FileAccess.file_exists(path):
		return errors
	
	var f = FileAccess.open(path, FileAccess.READ)
	if not f:
		return errors
	
	# Seek to last known position
	if _last_log_position > 0 and _last_log_position < f.get_length():
		f.seek(_last_log_position)
	elif _last_log_position >= f.get_length():
		return errors  # No new content
	
	var new_content = f.get_as_text()
	_last_log_position = f.get_length()
	
	# Parse error lines
	var lines = new_content.split("\n")
	for i in range(lines.size()):
		var error_info = _parse_log_line_for_error(lines[i], i)
		if error_info:
			errors.append(error_info)
	
	return errors

func _read_godot_log_tail(num_lines: int) -> Array[String]:
	var path = _get_log_path()
	if not FileAccess.file_exists(path):
		return []
	
	var f = FileAccess.open(path, FileAccess.READ)
	if not f:
		return []
	
	var content = f.get_as_text()
	var all_lines = content.split("\n")
	
	var start = max(0, all_lines.size() - num_lines)
	var result: Array[String] = []
	for i in range(start, all_lines.size()):
		result.append(all_lines[i])
	return result

func _parse_log_line_for_error(line: String, line_index: int) -> Variant:
	var lower = line.to_lower()
	
	# Match common Godot error patterns
	if lower.contains("error") or lower.contains("script_error") or lower.begins_with("e "):
		var file_match = ""
		var line_num = 0
		
		# Try to extract file:line pattern like "res://scripts/player.gd:42"
		var regex = RegEx.new()
		regex.compile("(res://[^:]+\\.gd):(\\d+)")
		var result = regex.search(line)
		if result:
			file_match = result.get_string(1)
			line_num = result.get_string(2).to_int()
		
		return {
			"type": "runtime_error",
			"file": file_match,
			"line": line_num,
			"message": line.strip_edges(),
			"severity": "error"
		}
	
	if lower.contains("warning") or lower.begins_with("w "):
		return {
			"type": "runtime_warning",
			"file": "",
			"line": 0,
			"message": line.strip_edges(),
			"severity": "warning"
		}
	
	return null

# ─── Internal: Utilities ───

func _find_all_scripts(directory: String, exclude_addons: bool = true) -> Array[String]:
	var scripts: Array[String] = []
	var dir = DirAccess.open(directory)
	if dir == null:
		return scripts
	
	dir.list_dir_begin()
	var file_name = dir.get_next()
	while file_name != "":
		var full_path = directory.path_join(file_name)
		if dir.current_is_dir():
			if not file_name.begins_with("."):
				if not (exclude_addons and file_name == "addons"):
					scripts.append_array(_find_all_scripts(full_path, exclude_addons))
		elif file_name.ends_with(".gd"):
			scripts.append(full_path)
		file_name = dir.get_next()
	dir.list_dir_end()
	return scripts

func _count_unique_files(errors: Array[Dictionary]) -> int:
	var files = {}
	for err in errors:
		var f = err.get("file", "")
		if not f.is_empty():
			files[f] = true
	return files.size()

func _cleanup_monitor() -> void:
	_monitor_active = false
	_monitor_client_id = -1
	
	if _monitor_timer:
		_monitor_timer.stop()
		_monitor_timer.queue_free()
		_monitor_timer = null
	
	var fs = EditorInterface.get_resource_filesystem()
	if fs and fs.filesystem_changed.is_connected(_on_filesystem_changed):
		fs.filesystem_changed.disconnect(_on_filesystem_changed)
