@tool
extends Control

var websocket_server: MCPWebSocketServer
var status_label: Label
var port_input: SpinBox
var start_button: Button
var stop_button: Button
var connection_count_label: Label
var log_text: TextEdit

func _ready():
	status_label = $VBoxContainer/StatusContainer/StatusLabel
	port_input = $VBoxContainer/PortContainer/PortSpinBox
	start_button = $VBoxContainer/ButtonsContainer/StartButton
	stop_button = $VBoxContainer/ButtonsContainer/StopButton
	connection_count_label = $VBoxContainer/ConnectionsContainer/CountLabel
	log_text = $VBoxContainer/LogContainer/LogText
	
	start_button.pressed.connect(_on_start_button_pressed)
	stop_button.pressed.connect(_on_stop_button_pressed)
	port_input.value_changed.connect(_on_port_changed)
	
	# Initial UI setup
	_update_ui()
	
	# Setup server signals once it's available
	await get_tree().process_frame
	if websocket_server:
		websocket_server.connect("client_connected", Callable(self, "_on_client_connected"))
		websocket_server.connect("client_disconnected", Callable(self, "_on_client_disconnected"))
		websocket_server.connect("command_received", Callable(self, "_on_command_received"))
		
		port_input.value = websocket_server.get_port()

func _update_ui():
	if not websocket_server:
		status_label.text = "Server: Not initialized"
		start_button.disabled = true
		stop_button.disabled = true
		port_input.editable = true
		connection_count_label.text = "0"
		return
	
	var is_active = websocket_server.is_server_active()
	
	status_label.text = "Server: " + ("Running" if is_active else "Stopped")
	start_button.disabled = is_active
	stop_button.disabled = not is_active
	port_input.editable = not is_active
	
	if is_active:
		connection_count_label.text = str(websocket_server.get_client_count())
	else:
		connection_count_label.text = "0"

func _on_start_button_pressed():
	if websocket_server:
		var result = websocket_server.start_server()
		if result == OK:
			_log_message("Server started on port " + str(websocket_server.get_port()))
		else:
			_log_message("Failed to start server: " + str(result))
		_update_ui()

func _on_stop_button_pressed():
	if websocket_server:
		websocket_server.stop_server()
		_log_message("Server stopped")
		_update_ui()

func _on_port_changed(new_port: float):
	if websocket_server:
		websocket_server.set_port(int(new_port))
		_log_message("Port changed to " + str(int(new_port)))

func _on_client_connected(client_id: int):
	_log_message("Client connected: " + str(client_id))
	_update_ui()

func _on_client_disconnected(client_id: int):
	_log_message("Client disconnected: " + str(client_id))
	_update_ui()

func _on_command_received(client_id: int, command: Dictionary):
	var command_type = command.get("type", "unknown")
	var command_id = command.get("commandId", "no-id")
	_log_message("Received command: " + command_type + " (ID: " + command_id + ") from client " + str(client_id))

func _log_message(message: String):
	var timestamp = Time.get_datetime_string_from_system()
	log_text.text += "[" + timestamp + "] " + message + "\n"
	# Auto-scroll to bottom
	log_text.scroll_vertical = log_text.get_line_count()