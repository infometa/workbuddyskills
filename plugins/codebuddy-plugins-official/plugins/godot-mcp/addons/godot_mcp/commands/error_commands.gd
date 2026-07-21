@tool
class_name MCPErrorCommands
extends MCPBaseCommandProcessor
## Error detection and validation commands for auto-fix workflow
## Enables AI to detect compilation errors and fix them automatically

func process_command(client_id: int, command_type: String, params: Dictionary, command_id: String) -> bool:
	match command_type:
		"validate_script":
			_validate_script(client_id, params, command_id)
			return true
		"validate_all_scripts":
			_validate_all_scripts(client_id, params, command_id)
			return true
		"get_script_errors":
			_get_script_errors(client_id, params, command_id)
			return true
	return false

## Validate a single GDScript file for compilation errors
func _validate_script(client_id: int, params: Dictionary, command_id: String) -> void:
	var script_path: String = params.get("script_path", "")
	
	if script_path.is_empty():
		return _send_error(client_id, "Script path cannot be empty", command_id)
	
	if not script_path.begins_with("res://"):
		script_path = "res://" + script_path
	
	# Check if file exists
	if not FileAccess.file_exists(script_path):
		return _send_error(client_id, "Script file not found: " + script_path, command_id)
	
	# Read script content
	var file = FileAccess.open(script_path, FileAccess.READ)
	if file == null:
		return _send_error(client_id, "Cannot open file: " + script_path, command_id)
	
	var content = file.get_as_text()
	file = null
	
	# Validate the script
	var validation_result = _validate_gdscript(script_path, content)
	
	_send_success(client_id, {
		"script_path": script_path,
		"is_valid": validation_result.is_valid,
		"errors": validation_result.errors,
		"error_count": validation_result.errors.size()
	}, command_id)

## Validate all GDScript files in the project
func _validate_all_scripts(client_id: int, params: Dictionary, command_id: String) -> void:
	var directory: String = params.get("directory", "res://")
	var exclude_addons: bool = params.get("exclude_addons", true)
	
	var results = {
		"total_scripts": 0,
		"valid_scripts": 0,
		"invalid_scripts": 0,
		"total_errors": 0,
		"files_with_errors": []
	}
	
	# Find all .gd files
	var scripts = _find_all_scripts(directory, exclude_addons)
	results.total_scripts = scripts.size()
	
	for script_path in scripts:
		var file = FileAccess.open(script_path, FileAccess.READ)
		if file == null:
			results.invalid_scripts += 1
			results.total_errors += 1
			results.files_with_errors.append({
				"path": script_path,
				"errors": [{"line": 0, "message": "Cannot open file", "type": "file_error"}]
			})
			continue
		
		var content = file.get_as_text()
		file = null
		
		var validation = _validate_gdscript(script_path, content)
		
		if validation.is_valid:
			results.valid_scripts += 1
		else:
			results.invalid_scripts += 1
			results.total_errors += validation.errors.size()
			results.files_with_errors.append({
				"path": script_path,
				"errors": validation.errors
			})
	
	_send_success(client_id, results, command_id)

## Get detailed error information for a script
func _get_script_errors(client_id: int, params: Dictionary, command_id: String) -> void:
	var script_path: String = params.get("script_path", "")
	var include_warnings: bool = params.get("include_warnings", true)
	
	if script_path.is_empty():
		return _send_error(client_id, "Script path cannot be empty", command_id)
	
	if not script_path.begins_with("res://"):
		script_path = "res://" + script_path
	
	if not FileAccess.file_exists(script_path):
		return _send_error(client_id, "Script file not found: " + script_path, command_id)
	
	# Read the script
	var file = FileAccess.open(script_path, FileAccess.READ)
	if file == null:
		return _send_error(client_id, "Cannot open file: " + script_path, command_id)
	
	var content = file.get_as_text()
	var lines = content.split("\n")
	file = null
	
	# Get errors
	var validation = _validate_gdscript(script_path, content)
	var errors = validation.errors
	var warnings: Array[Dictionary] = []
	
	# Add code snippets and suggestions
	for i in range(errors.size()):
		var error = errors[i]
		var line_num = error.get("line", 0)
		
		# Add code snippet if line number is valid
		if line_num > 0 and line_num <= lines.size():
			error["code_snippet"] = lines[line_num - 1].strip_edges()
			
			# Add context lines
			var context_start = max(0, line_num - 3)
			var context_end = min(lines.size(), line_num + 2)
			var context_lines: Array[String] = []
			for j in range(context_start, context_end):
				var prefix = ">>> " if j == line_num - 1 else "    "
				context_lines.append("%s%d: %s" % [prefix, j + 1, lines[j]])
			error["context"] = "\n".join(context_lines)
		
		# Add fix suggestions based on error type
		error["suggestion"] = _get_fix_suggestion(error)
	
	_send_success(client_id, {
		"script_path": script_path,
		"errors": errors,
		"warnings": warnings if include_warnings else [],
		"total_lines": lines.size(),
		"content": content
	}, command_id)

## Core validation function - validates GDScript content
func _validate_gdscript(script_path: String, content: String) -> Dictionary:
	var result = {
		"is_valid": true,
		"errors": []
	}
	
	# Method 1: Try to compile using GDScript.new()
	var test_script = GDScript.new()
	test_script.source_code = content
	
	# reload() returns an error code
	var err = test_script.reload(false)  # false = don't keep state
	
	if err != OK:
		result.is_valid = false
		
		# Try to get more detailed error info
		var error_info = _parse_compilation_error(err, content, script_path)
		result.errors.append(error_info)
	
	# Method 2: Basic syntax checks
	var syntax_errors = _check_basic_syntax(content, script_path)
	if syntax_errors.size() > 0:
		result.is_valid = false
		result.errors.append_array(syntax_errors)
	
	return result

## Parse compilation error code to get detailed info
func _parse_compilation_error(err: int, content: String, path: String) -> Dictionary:
	var error_names = {
		ERR_PARSE_ERROR: "Parse error - syntax is invalid",
		ERR_COMPILATION_FAILED: "Compilation failed",
		ERR_INVALID_DATA: "Invalid script data",
		ERR_FILE_CORRUPT: "Script file is corrupt",
		ERR_CANT_OPEN: "Cannot open script",
		ERR_INVALID_DECLARATION: "Invalid declaration",
	}
	
	var message = error_names.get(err, "Unknown error (code: %d)" % err)
	
	# Try to find the error line by looking for common issues
	var lines = content.split("\n")
	var error_line = _find_error_line(lines)
	
	return {
		"type": "compile_error",
		"error_code": err,
		"message": message,
		"file": path,
		"line": error_line,
		"column": 0
	}

## Try to find which line caused the error
func _find_error_line(lines: Array) -> int:
	var bracket_stack: Array[Dictionary] = []
	
	for i in range(lines.size()):
		var line = lines[i]
		var stripped = line.strip_edges()
		
		# Skip comments and empty lines
		if stripped.begins_with("#") or stripped.is_empty():
			continue
		
		# Track brackets
		for j in range(line.length()):
			var c = line[j]
			if c in ["(", "[", "{"]:
				bracket_stack.push_back({"char": c, "line": i + 1})
			elif c == ")":
				if bracket_stack.is_empty() or bracket_stack.back().char != "(":
					return i + 1
				bracket_stack.pop_back()
			elif c == "]":
				if bracket_stack.is_empty() or bracket_stack.back().char != "[":
					return i + 1
				bracket_stack.pop_back()
			elif c == "}":
				if bracket_stack.is_empty() or bracket_stack.back().char != "{":
					return i + 1
				bracket_stack.pop_back()
	
	# If there are unclosed brackets, return the line where they started
	if not bracket_stack.is_empty():
		return bracket_stack.back().line
	
	return 1  # Default to first line

## Basic syntax checking
func _check_basic_syntax(content: String, path: String) -> Array[Dictionary]:
	var errors: Array[Dictionary] = []
	var lines = content.split("\n")
	
	var bracket_stack: Array[Dictionary] = []
	var in_string = false
	var string_char = ""
	var in_multiline_string = false
	
	for i in range(lines.size()):
		var line = lines[i]
		var line_num = i + 1
		var stripped = line.strip_edges()
		
		# Skip pure comments
		if stripped.begins_with("#"):
			continue
		
		# Check for multiline string
		var triple_quote_count = line.count('"""')
		if triple_quote_count % 2 == 1:
			in_multiline_string = not in_multiline_string
		
		if in_multiline_string:
			continue
		
		# Process character by character for bracket matching
		var j = 0
		while j < line.length():
			var c = line[j]
			
			# Skip if inside a comment
			if j > 0 and line[j-1] == '#':
				break
			if c == '#' and not in_string:
				break
			
			# Handle strings
			if c in ["'", '"'] and not in_string:
				in_string = true
				string_char = c
			elif c == string_char and in_string:
				# Check for escape
				if j > 0 and line[j-1] != "\\":
					in_string = false
					string_char = ""
			
			# Only check brackets when not in string
			if not in_string:
				if c in ["(", "[", "{"]:
					bracket_stack.push_back({"char": c, "line": line_num, "col": j + 1})
				elif c == ")":
					if bracket_stack.is_empty() or bracket_stack.back().char != "(":
						errors.append({
							"type": "syntax_error",
							"message": "Unmatched closing parenthesis ')'",
							"line": line_num,
							"column": j + 1,
							"file": path
						})
					else:
						bracket_stack.pop_back()
				elif c == "]":
					if bracket_stack.is_empty() or bracket_stack.back().char != "[":
						errors.append({
							"type": "syntax_error",
							"message": "Unmatched closing bracket ']'",
							"line": line_num,
							"column": j + 1,
							"file": path
						})
					else:
						bracket_stack.pop_back()
				elif c == "}":
					if bracket_stack.is_empty() or bracket_stack.back().char != "{":
						errors.append({
							"type": "syntax_error",
							"message": "Unmatched closing brace '}'",
							"line": line_num,
							"column": j + 1,
							"file": path
						})
					else:
						bracket_stack.pop_back()
			
			j += 1
		
		# Reset string state at end of line (unless multiline)
		in_string = false
		string_char = ""
		
		# Check for common syntax issues
		
		# Missing colon after func/if/for/while/etc
		if stripped.begins_with("func ") and not stripped.ends_with(":") and not ":" in stripped:
			errors.append({
				"type": "syntax_error",
				"message": "Function definition missing colon ':'",
				"line": line_num,
				"column": stripped.length(),
				"file": path
			})
		
		if stripped.begins_with("if ") and not stripped.ends_with(":") and not "else" in stripped:
			if not stripped.contains("if ") or stripped.count(":") == 0:
				errors.append({
					"type": "syntax_error",
					"message": "If statement may be missing colon ':'",
					"line": line_num,
					"column": stripped.length(),
					"file": path
				})
		
		if stripped.begins_with("for ") and not stripped.ends_with(":"):
			errors.append({
				"type": "syntax_error",
				"message": "For loop missing colon ':'",
				"line": line_num,
				"column": stripped.length(),
				"file": path
			})
		
		if stripped.begins_with("while ") and not stripped.ends_with(":"):
			errors.append({
				"type": "syntax_error",
				"message": "While loop missing colon ':'",
				"line": line_num,
				"column": stripped.length(),
				"file": path
			})
	
	# Check for unclosed brackets
	for bracket in bracket_stack:
		var char_name = {
			"(": "parenthesis",
			"[": "bracket",
			"{": "brace"
		}
		errors.append({
			"type": "syntax_error",
			"message": "Unclosed %s '%s'" % [char_name.get(bracket.char, "bracket"), bracket.char],
			"line": bracket.line,
			"column": bracket.col,
			"file": path
		})
	
	return errors

## Get fix suggestion based on error
func _get_fix_suggestion(error: Dictionary) -> String:
	var error_type = error.get("type", "")
	var message = error.get("message", "").to_lower()
	
	if "parenthesis" in message or "bracket" in message or "brace" in message:
		if "unclosed" in message:
			return "Add the missing closing bracket"
		else:
			return "Remove the extra closing bracket or add the matching opening bracket"
	
	if "colon" in message:
		return "Add ':' at the end of the statement"
	
	if "parse error" in message or "syntax" in message:
		return "Check for typos, missing punctuation, or incorrect indentation"
	
	if "compilation failed" in message:
		return "Check for undefined variables, incorrect function calls, or type mismatches"
	
	return "Review the code at the indicated line for syntax issues"

## Recursively find all GDScript files
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
			# Skip hidden directories and optionally addons
			if not file_name.begins_with("."):
				if not (exclude_addons and file_name == "addons"):
					scripts.append_array(_find_all_scripts(full_path, exclude_addons))
		elif file_name.ends_with(".gd"):
			scripts.append(full_path)
		
		file_name = dir.get_next()
	
	dir.list_dir_end()
	return scripts
