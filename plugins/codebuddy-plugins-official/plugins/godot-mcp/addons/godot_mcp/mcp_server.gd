@tool
extends EditorPlugin

const DEFAULT_PORT := 9080
const SETTING_KEY := "godot_mcp/server_port"

var tcp_server := TCPServer.new()
var port := DEFAULT_PORT
var handshake_timeout := 3000 # ms
var debug_mode := true
var log_detailed := true
var command_handler = null

signal client_connected(id)
signal client_disconnected(id)
signal command_received(client_id, command)

class WebSocketClient:
	var tcp: StreamPeerTCP
	var id: int
	var ws: WebSocketPeer
	var state: int = -1 # -1: handshaking, 0: connected, 1: error/closed
	var handshake_time: int
	var last_poll_time: int
	
	func _init(p_tcp: StreamPeerTCP, p_id: int):
		tcp = p_tcp
		id = p_id
		handshake_time = Time.get_ticks_msec()
	
	func upgrade_to_websocket() -> bool:
		ws = WebSocketPeer.new()
		var err = ws.accept_stream(tcp)
		return err == OK

var clients := {}
var next_client_id := 1

func _enter_tree():
	# Store plugin instance for EditorInterface access
	Engine.set_meta("GodotMCPPlugin", self)
	
	print("\n=== MCP SERVER STARTING ===")
	
	# Register and read port from ProjectSettings
	if not ProjectSettings.has_setting(SETTING_KEY):
		ProjectSettings.set_setting(SETTING_KEY, DEFAULT_PORT)
	ProjectSettings.set_initial_value(SETTING_KEY, DEFAULT_PORT)
	ProjectSettings.add_property_info({
		"name": SETTING_KEY,
		"type": TYPE_INT,
		"hint": PROPERTY_HINT_RANGE,
		"hint_string": "1024,65535"
	})
	port = ProjectSettings.get_setting(SETTING_KEY, DEFAULT_PORT)
	
	# Initialize the command handler
	print("Creating command handler...")
	command_handler = preload("res://addons/godot_mcp/command_handler.gd").new()
	command_handler.name = "CommandHandler"
	add_child(command_handler)
	
	# Connect signals
	print("Connecting command handler signals...")
	self.connect("command_received", Callable(command_handler, "_handle_command"))
	
	# Start WebSocket server
	var err = tcp_server.listen(port)
	if err == OK:
		print("Listening on port", port)
		set_process(true)
	else:
		printerr("Failed to listen on port", port, "error:", err)
	
	print("=== MCP SERVER INITIALIZED ===\n")

func _exit_tree():
	# Remove plugin instance from Engine metadata
	if Engine.has_meta("GodotMCPPlugin"):
		Engine.remove_meta("GodotMCPPlugin")
	
	if tcp_server and tcp_server.is_listening():
		tcp_server.stop()
	
	clients.clear()
	
	print("=== MCP SERVER SHUTDOWN ===")

func _log(client_id, message):
	if log_detailed:
		print("[Client ", client_id, "] ", message)

func _process(_delta):
	if not tcp_server.is_listening():
		return
	
	# Poll for new connections
	if tcp_server.is_connection_available():
		var tcp = tcp_server.take_connection()
		var id = next_client_id
		next_client_id += 1
		
		var client = WebSocketClient.new(tcp, id)
		clients[id] = client
		
		print("[Client ", id, "] New TCP connection")
		
		# Try to upgrade immediately
		if client.upgrade_to_websocket():
			print("[Client ", id, "] WebSocket handshake started")
		else:
			print("[Client ", id, "] Failed to start WebSocket handshake")
			clients.erase(id)
	
	# Update clients
	var current_time = Time.get_ticks_msec()
	var ids_to_remove := []
	
	for id in clients:
		var client = clients[id]
		client.last_poll_time = current_time
		
		# Process client based on its state
		if client.state == -1: # Handshaking
			if client.ws != null:
				# Poll the WebSocket peer
				client.ws.poll()
				
				# Check WebSocket state
				var ws_state = client.ws.get_ready_state()
				if debug_mode:
					_log(id, "State: " + str(ws_state))
					
				if ws_state == WebSocketPeer.STATE_OPEN:
					print("[Client ", id, "] WebSocket handshake completed")
					client.state = 0
					
					# Emit connected signal
					emit_signal("client_connected", id)
					
					# Send welcome message
					var msg = JSON.stringify({
						"type": "welcome",
						"message": "Welcome to Godot MCP WebSocket Server"
					})
					client.ws.send_text(msg)
					
				elif ws_state != WebSocketPeer.STATE_CONNECTING:
					print("[Client ", id, "] WebSocket handshake failed, state: ", ws_state)
					ids_to_remove.append(id)
				
				# Check for handshake timeout
				elif current_time - client.handshake_time > handshake_timeout:
					print("[Client ", id, "] WebSocket handshake timed out")
					ids_to_remove.append(id)
			else:
				# If TCP is still connected, try upgrading
				if client.tcp.get_status() == StreamPeerTCP.STATUS_CONNECTED:
					if client.upgrade_to_websocket():
						print("[Client ", id, "] WebSocket handshake started")
					else:
						print("[Client ", id, "] Failed to start WebSocket handshake")
						ids_to_remove.append(id)
				else:
					print("[Client ", id, "] TCP disconnected during handshake")
					ids_to_remove.append(id)
		
		elif client.state == 0: # Connected
			# Poll the WebSocket
			client.ws.poll()
			
			# Check state
			var ws_state = client.ws.get_ready_state()
			if ws_state != WebSocketPeer.STATE_OPEN:
				print("[Client ", id, "] WebSocket connection closed, state: ", ws_state)
				emit_signal("client_disconnected", id)
				ids_to_remove.append(id)
				continue
			
			# Process messages
			while client.ws.get_available_packet_count() > 0:
				var packet = client.ws.get_packet()
				var text = packet.get_string_from_utf8()
				
				print("[Client ", id, "] RECEIVED RAW DATA: ", text)
				
				# Parse as JSON
				var json = JSON.new()
				var parse_result = json.parse(text)
				_log(id, "JSON parse result: " + str(parse_result))
				
				if parse_result == OK:
					var data = json.get_data()
					_log(id, "Parsed JSON: " + str(data))
					
					# Handle JSON-RPC protocol
					if data.has("jsonrpc") and data.get("jsonrpc") == "2.0":
						# Handle ping method
						if data.has("method") and data.get("method") == "ping":
							print("[Client ", id, "] Received PING with id: ", data.get("id"))
							var response = {
								"jsonrpc": "2.0",
								"id": data.get("id"),
								"result": null  # FastMCP expects null result for pings
							}
							var response_text = JSON.stringify(response)
							var send_result = client.ws.send_text(response_text)
							print("[Client ", id, "] SENDING PING RESPONSE: ", response_text, " (result: ", send_result, ")")
						
						# Handle other MCP commands
						elif data.has("method"):
							var method_name = data.get("method")
							var params = data.get("params", {})
							var req_id = data.get("id")
							
							print("[Client ", id, "] Processing JSON-RPC method: ", method_name)
							
							# For now, just send a generic success response
							# TODO: Route these to command handler as well
							var response = {
								"jsonrpc": "2.0",
								"id": req_id,
								"result": {
									"status": "success",
									"message": "Command processed"
								}
							}
							
							var response_text = JSON.stringify(response)
							var send_result = client.ws.send_text(response_text)
							print("[Client ", id, "] SENT RESPONSE: ", response_text, " (result: ", send_result, ")")
					
					# Handle legacy command format - This is what Claude Code uses
					elif data.has("type"):
						var cmd_type = data.get("type")
						var params = data.get("params", {})
						var cmd_id = data.get("commandId", "")
						
						print("[Client ", id, "] Processing command: ", cmd_type)
						
						# Route command to command handler via signal
						# The command handler will handle the response via send_response
						emit_signal("command_received", id, data)
				else:
					print("[Client ", id, "] Failed to parse JSON: ", json.get_error_message())
	
	# Remove clients that need to be removed
	for id in ids_to_remove:
		clients.erase(id)

# Function for command handler to send responses back to clients
func send_response(client_id: int, response: Dictionary) -> int:
	if not clients.has(client_id):
		print("Error: Client %d not found" % client_id)
		return ERR_DOES_NOT_EXIST
	
	var client = clients[client_id]
	var json_text = JSON.stringify(response)
	
	print("Sending response to client %d: %s" % [client_id, json_text])
	
	if client.ws.get_ready_state() != WebSocketPeer.STATE_OPEN:
		print("Error: Client %d connection not open" % client_id)
		return ERR_UNAVAILABLE
	
	var result = client.ws.send_text(json_text)
	if result != OK:
		print("Error sending response to client %d: %d" % [client_id, result])
	
	return result

func is_server_active() -> bool:
	return tcp_server.is_listening()

func stop_server() -> void:
	if is_server_active():
		tcp_server.stop()
		clients.clear()
		print("MCP WebSocket server stopped")
		
func get_port() -> int:
	return port
