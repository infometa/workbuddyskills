@tool
class_name MCPWebSocketServer
extends Node

signal client_connected(id)
signal client_disconnected(id)
signal command_received(client_id, command)

# Custom implementation of WebSocket server using TCP + WebSocketPeer
var tcp_server = TCPServer.new()
var peers = {}
var pending_peers = []
var _port = 9080
var refuse_new_connections = false
var handshake_timeout = 3000 # ms

class PendingPeer:
	var tcp: StreamPeerTCP
	var connection: StreamPeer
	var ws: WebSocketPeer = null
	var connect_time: int
	
	func _init(p_tcp: StreamPeerTCP):
		tcp = p_tcp
		connection = tcp
		connect_time = Time.get_ticks_msec()

func _ready():
	set_process(false)

func _process(_delta):
	poll()

func is_server_active() -> bool:
	return tcp_server.is_listening()

func start_server() -> int:
	if is_server_active():
		return ERR_ALREADY_IN_USE
	
	var err = tcp_server.listen(_port)
	if err == OK:
		set_process(true)
		print("MCP WebSocket server started on port %d" % _port)
	else:
		print("Failed to start MCP WebSocket server: %d" % err)
	
	return err

func stop_server() -> void:
	if is_server_active():
		tcp_server.stop()
		
		# Close all client connections
		for client_id in peers.keys():
			peers[client_id].close()
		peers.clear()
		pending_peers.clear()
		
		set_process(false)
		print("MCP WebSocket server stopped")

func poll() -> void:
	if not tcp_server.is_listening():
		return
		
	# Accept any incoming TCP connections
	while not refuse_new_connections and tcp_server.is_connection_available():
		var conn = tcp_server.take_connection()
		assert(conn != null)
		print("New TCP connection, starting WebSocket handshake...")
		pending_peers.append(PendingPeer.new(conn))
	
	# Process pending connections (handshake)
	var to_remove := []
	for p in pending_peers:
		if not _connect_pending(p):
			if p.connect_time + handshake_timeout < Time.get_ticks_msec():
				# Timeout
				print("WebSocket handshake timed out")
				to_remove.append(p)
			continue # Still pending
		to_remove.append(p)
	for r in to_remove:
		pending_peers.erase(r)
	to_remove.clear()
	
	# Process connected peers
	for id in peers:
		var p: WebSocketPeer = peers[id]
		p.poll()
		
		var state = p.get_ready_state()
		if state == WebSocketPeer.STATE_CLOSING or state == WebSocketPeer.STATE_CLOSED:
			print("Client %d disconnected (state: %d)" % [id, state])
			emit_signal("client_disconnected", id)
			to_remove.append(id)
			continue
		
		# Process incoming messages
		while p.get_available_packet_count() > 0:
			var packet = p.get_packet()
			var text = packet.get_string_from_utf8()
			
			# Parse the JSON command
			var json = JSON.new()
			var parse_result = json.parse(text)
			
			if parse_result == OK:
				var command = json.get_data()
				print("Received command from client %d: %s" % [id, command])
				emit_signal("command_received", id, command)
			else:
				print("Error parsing JSON from client %d: %s at line %d" % 
					[id, json.get_error_message(), json.get_error_line()])
	
	# Remove disconnected clients
	for r in to_remove:
		peers.erase(r)

func _connect_pending(p: PendingPeer) -> bool:
	if p.ws != null:
		# Poll websocket client if doing handshake
		p.ws.poll()
		var state = p.ws.get_ready_state()
		
		if state == WebSocketPeer.STATE_OPEN:
			var id = randi() % (1 << 30) + 1 # Generate a random ID
			peers[id] = p.ws
			print("Client %d WebSocket connection established" % id)
			emit_signal("client_connected", id)
			return true # Success.
		elif state != WebSocketPeer.STATE_CONNECTING:
			print("WebSocket handshake failed, state: %d" % state)
			return true # Failure.
		return false # Still connecting.
	else:
		if p.tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			print("TCP connection lost during handshake")
			return true # TCP disconnected.
		else:
			# TCP is ready, create WS peer
			print("TCP connected, upgrading to WebSocket...")
			p.ws = WebSocketPeer.new()
			p.ws.accept_stream(p.tcp)
			return false # WebSocketPeer connection is pending.

func send_response(client_id: int, response: Dictionary) -> int:
	if not peers.has(client_id):
		print("Error: Client %d not found" % client_id)
		return ERR_DOES_NOT_EXIST
	
	var peer = peers[client_id]
	var json_text = JSON.stringify(response)
	
	if peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		print("Error: Client %d connection not open" % client_id)
		return ERR_UNAVAILABLE
	
	var result = peer.send_text(json_text)
	if result != OK:
		print("Error sending response to client %d: %d" % [client_id, result])
	
	return result

func set_port(new_port: int) -> void:
	if is_server_active():
		push_error("Cannot change port while server is active")
		return
	_port = new_port

func get_port() -> int:
	return _port

func get_client_count() -> int:
	return peers.size()
