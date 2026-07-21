@tool
class_name MCPGameCommands
extends MCPBaseCommandProcessor
## High-level game creation commands that combine multiple operations
## These make it much easier for AI to create complete game elements

func process_command(client_id: int, command_type: String, params: Dictionary, command_id: String) -> bool:
	match command_type:
		"create_game_scene":
			_create_game_scene(client_id, params, command_id)
			return true
		"create_fps_player":
			_create_fps_player(client_id, params, command_id)
			return true
		"create_enemy":
			_create_enemy(client_id, params, command_id)
			return true
		"create_weapon":
			_create_weapon(client_id, params, command_id)
			return true
		"setup_game_world":
			_setup_game_world(client_id, params, command_id)
			return true
		"batch_update_properties":
			_batch_update_properties(client_id, params, command_id)
			return true
	return false

func _create_game_scene(client_id: int, params: Dictionary, command_id: String) -> void:
	var scene_path: String = params.get("scene_path", "res://scenes/new_scene.tscn")
	var root_type: String = params.get("root_type", "Node3D")
	var root_name: String = params.get("root_name", "")
	var nodes: Array = params.get("nodes", [])
	
	# Ensure path format
	if not scene_path.begins_with("res://"):
		scene_path = "res://" + scene_path
	if not scene_path.ends_with(".tscn"):
		scene_path += ".tscn"
	
	# Create root node
	var root = _create_node_by_type(root_type)
	if not root:
		return _send_error(client_id, "Failed to create root node of type: " + root_type, command_id)
	
	# Set root name
	if root_name.is_empty():
		root_name = scene_path.get_file().get_basename()
	root.name = root_name
	
	# Create all child nodes
	var node_map: Dictionary = {"/": root, "": root}
	
	for node_def in nodes:
		var node_name: String = node_def.get("name", "Node")
		var node_type: String = node_def.get("type", "Node")
		var parent_path: String = node_def.get("parent", "")
		var properties: Dictionary = node_def.get("properties", {})
		var script_content: String = node_def.get("script", "")
		
		# Create the node
		var node = _create_node_by_type(node_type)
		if not node:
			push_warning("Failed to create node: " + node_name + " of type: " + node_type)
			continue
		
		node.name = node_name
		
		# Find parent
		var parent = root
		if not parent_path.is_empty() and parent_path != "/":
			if node_map.has(parent_path):
				parent = node_map[parent_path]
			else:
				# Try to find by traversing
				var found = root.get_node_or_null(parent_path)
				if found:
					parent = found
		
		parent.add_child(node)
		node.owner = root
		
		# Store in map for later reference
		var full_path = parent_path + "/" + node_name if parent_path else node_name
		node_map[full_path] = node
		node_map[node_name] = node
		
		# Set properties
		for prop_name in properties:
			_set_property_smart(node, prop_name, properties[prop_name])
		
		# Attach script if provided
		if not script_content.is_empty():
			var script = GDScript.new()
			script.source_code = script_content
			script.reload()
			node.set_script(script)
	
	# Ensure directory exists
	var dir_path = scene_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir_path.replace("res://", ProjectSettings.globalize_path("res://")))
	
	# Pack and save
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(root)
	if result != OK:
		root.queue_free()
		return _send_error(client_id, "Failed to pack scene", command_id)
	
	result = ResourceSaver.save(packed_scene, scene_path)
	root.queue_free()
	
	if result != OK:
		return _send_error(client_id, "Failed to save scene", command_id)
	
	_send_success(client_id, {
		"scene_path": scene_path,
		"node_count": nodes.size() + 1
	}, command_id)

func _create_fps_player(client_id: int, params: Dictionary, command_id: String) -> void:
	var scene_path: String = params.get("scene_path", "res://scenes/player.tscn")
	var player_height: float = params.get("player_height", 1.8)
	var include_weapon_holder: bool = params.get("include_weapon_holder", true)
	var first_person_arms_only: bool = params.get("first_person_arms_only", false)
	var script_content: String = params.get("script_content", "")
	
	# Appearance colors (RGB arrays)
	var hair_color: Array = params.get("hair_color", [0.15, 0.1, 0.05])
	var skin_color: Array = params.get("skin_color", [0.87, 0.72, 0.53])
	var shirt_color: Array = params.get("shirt_color", [0.2, 0.4, 0.8])
	var pants_color: Array = params.get("pants_color", [0.2, 0.2, 0.25])
	var shoes_color: Array = params.get("shoes_color", [0.1, 0.1, 0.1])
	
	# Ensure path format
	if not scene_path.begins_with("res://"):
		scene_path = "res://" + scene_path
	if not scene_path.ends_with(".tscn"):
		scene_path += ".tscn"
	
	# Create player structure
	var player = CharacterBody3D.new()
	player.name = "Player"
	player.add_to_group("player")
	
	# Camera at eye level
	var camera = Camera3D.new()
	camera.name = "Camera3D"
	camera.position.y = player_height * 0.9
	camera.current = true
	player.add_child(camera)
	camera.owner = player
	
	# Weapon holder (child of camera)
	if include_weapon_holder:
		var weapon_holder = Node3D.new()
		weapon_holder.name = "WeaponHolder"
		weapon_holder.position = Vector3(0.3, -0.2, -0.5)
		camera.add_child(weapon_holder)
		weapon_holder.owner = player
	
	# Collision shape
	var collision = CollisionShape3D.new()
	collision.name = "CollisionShape3D"
	var capsule = CapsuleShape3D.new()
	capsule.height = player_height
	capsule.radius = 0.3
	collision.shape = capsule
	collision.position.y = player_height / 2
	player.add_child(collision)
	collision.owner = player
	
	# === CREATE FULL BODY ===
	var body = Node3D.new()
	body.name = "Body"
	player.add_child(body)
	body.owner = player
	
	# Create materials
	var hair_mat = _create_material(hair_color)
	var skin_mat = _create_material(skin_color)
	var shirt_mat = _create_material(shirt_color)
	var pants_mat = _create_material(pants_color)
	var shoes_mat = _create_material(shoes_color)
	
	# Body proportions based on height
	var head_radius = player_height * 0.08
	var torso_height = player_height * 0.3
	var torso_width = player_height * 0.2
	var arm_length = player_height * 0.25
	var arm_radius = player_height * 0.035
	var leg_length = player_height * 0.28
	var leg_radius = player_height * 0.045
	var foot_height = player_height * 0.05
	
	# HEAD (with hair on top)
	var head = Node3D.new()
	head.name = "Head"
	head.position.y = player_height * 0.85
	body.add_child(head)
	head.owner = player
	
	# Face (sphere)
	var face_mesh = MeshInstance3D.new()
	face_mesh.name = "Face"
	var face_sphere = SphereMesh.new()
	face_sphere.radius = head_radius
	face_sphere.height = head_radius * 2
	face_mesh.mesh = face_sphere
	face_mesh.material_override = skin_mat
	head.add_child(face_mesh)
	face_mesh.owner = player
	
	# Hair (slightly larger sphere on top)
	var hair_mesh = MeshInstance3D.new()
	hair_mesh.name = "Hair"
	var hair_sphere = SphereMesh.new()
	hair_sphere.radius = head_radius * 1.1
	hair_sphere.height = head_radius * 1.2
	hair_mesh.mesh = hair_sphere
	hair_mesh.position.y = head_radius * 0.3
	hair_mesh.material_override = hair_mat
	head.add_child(hair_mesh)
	hair_mesh.owner = player
	
	# TORSO
	var torso = MeshInstance3D.new()
	torso.name = "Torso"
	var torso_box = BoxMesh.new()
	torso_box.size = Vector3(torso_width, torso_height, torso_width * 0.6)
	torso.mesh = torso_box
	torso.position.y = player_height * 0.6
	torso.material_override = shirt_mat
	body.add_child(torso)
	torso.owner = player
	
	# LEFT ARM
	var left_arm = _create_arm("LeftArm", -torso_width/2 - arm_radius, player_height * 0.7, 
							   arm_length, arm_radius, skin_mat, shirt_mat, player, body)
	
	# RIGHT ARM  
	var right_arm = _create_arm("RightArm", torso_width/2 + arm_radius, player_height * 0.7,
							   arm_length, arm_radius, skin_mat, shirt_mat, player, body)
	
	# LEFT LEG
	var left_leg = _create_leg("LeftLeg", -torso_width/4, player_height * 0.28,
							  leg_length, leg_radius, foot_height, pants_mat, shoes_mat, player, body)
	
	# RIGHT LEG
	var right_leg = _create_leg("RightLeg", torso_width/4, player_height * 0.28,
							   leg_length, leg_radius, foot_height, pants_mat, shoes_mat, player, body)
	
	# === ANIMATION PLAYER ===
	var anim_player = AnimationPlayer.new()
	anim_player.name = "AnimationPlayer"
	body.add_child(anim_player)
	anim_player.owner = player
	
	# Create animation library
	var anim_lib = AnimationLibrary.new()
	
	# Idle animation
	var idle_anim = _create_idle_animation(player_height)
	anim_lib.add_animation("idle", idle_anim)
	
	# Walk animation
	var walk_anim = _create_walk_animation(player_height)
	anim_lib.add_animation("walk", walk_anim)
	
	# Run animation
	var run_anim = _create_run_animation(player_height)
	anim_lib.add_animation("run", run_anim)
	
	# Jump animation
	var jump_anim = _create_jump_animation(player_height)
	anim_lib.add_animation("jump", jump_anim)
	
	anim_player.add_animation_library("", anim_lib)
	
	# Attach script
	if not script_content.is_empty():
		var script = GDScript.new()
		script.source_code = script_content
		var err = script.reload()
		if err == OK:
			player.set_script(script)
	
	# Ensure directory exists
	var dir_path = scene_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir_path.replace("res://", ProjectSettings.globalize_path("res://")))
	
	# Save scene
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(player)
	if result != OK:
		player.queue_free()
		return _send_error(client_id, "Failed to pack player scene", command_id)
	
	result = ResourceSaver.save(packed_scene, scene_path)
	player.queue_free()
	
	if result != OK:
		return _send_error(client_id, "Failed to save player scene", command_id)
	
	_send_success(client_id, {
		"scene_path": scene_path,
		"player_height": player_height,
		"has_animations": true,
		"body_parts": ["Head", "Hair", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]
	}, command_id)

# Helper: Create a material from RGB array
func _create_material(color_array: Array) -> StandardMaterial3D:
	var mat = StandardMaterial3D.new()
	mat.albedo_color = Color(color_array[0], color_array[1], color_array[2])
	return mat

# Helper: Create an arm (upper arm + forearm + hand)
func _create_arm(name: String, x_pos: float, y_pos: float, length: float, radius: float, 
				 skin_mat: Material, shirt_mat: Material, owner_node: Node, parent: Node) -> Node3D:
	var arm = Node3D.new()
	arm.name = name
	arm.position = Vector3(x_pos, y_pos, 0)
	parent.add_child(arm)
	arm.owner = owner_node
	
	# Upper arm (shirt sleeve)
	var upper_arm = MeshInstance3D.new()
	upper_arm.name = "UpperArm"
	var upper_capsule = CapsuleMesh.new()
	upper_capsule.radius = radius
	upper_capsule.height = length * 0.5
	upper_arm.mesh = upper_capsule
	upper_arm.position.y = -length * 0.25
	upper_arm.material_override = shirt_mat
	arm.add_child(upper_arm)
	upper_arm.owner = owner_node
	
	# Forearm (skin)
	var forearm = MeshInstance3D.new()
	forearm.name = "Forearm"
	var fore_capsule = CapsuleMesh.new()
	fore_capsule.radius = radius * 0.9
	fore_capsule.height = length * 0.45
	forearm.mesh = fore_capsule
	forearm.position.y = -length * 0.7
	forearm.material_override = skin_mat
	arm.add_child(forearm)
	forearm.owner = owner_node
	
	# Hand
	var hand = MeshInstance3D.new()
	hand.name = "Hand"
	var hand_sphere = SphereMesh.new()
	hand_sphere.radius = radius * 1.2
	hand.mesh = hand_sphere
	hand.position.y = -length
	hand.material_override = skin_mat
	arm.add_child(hand)
	hand.owner = owner_node
	
	return arm

# Helper: Create a leg (thigh + shin + foot)
func _create_leg(name: String, x_pos: float, y_pos: float, length: float, radius: float,
				 foot_height: float, pants_mat: Material, shoes_mat: Material, 
				 owner_node: Node, parent: Node) -> Node3D:
	var leg = Node3D.new()
	leg.name = name
	leg.position = Vector3(x_pos, y_pos, 0)
	parent.add_child(leg)
	leg.owner = owner_node
	
	# Thigh (upper leg - pants)
	var thigh = MeshInstance3D.new()
	thigh.name = "Thigh"
	var thigh_capsule = CapsuleMesh.new()
	thigh_capsule.radius = radius
	thigh_capsule.height = length * 0.55
	thigh.mesh = thigh_capsule
	thigh.position.y = -length * 0.25
	thigh.material_override = pants_mat
	leg.add_child(thigh)
	thigh.owner = owner_node
	
	# Shin (lower leg - pants)
	var shin = MeshInstance3D.new()
	shin.name = "Shin"
	var shin_capsule = CapsuleMesh.new()
	shin_capsule.radius = radius * 0.85
	shin_capsule.height = length * 0.5
	shin.mesh = shin_capsule
	shin.position.y = -length * 0.75
	shin.material_override = pants_mat
	leg.add_child(shin)
	shin.owner = owner_node
	
	# Foot (shoe)
	var foot = MeshInstance3D.new()
	foot.name = "Foot"
	var foot_box = BoxMesh.new()
	foot_box.size = Vector3(radius * 2, foot_height, radius * 3)
	foot.mesh = foot_box
	foot.position = Vector3(0, -length - foot_height/2, radius * 0.5)
	foot.material_override = shoes_mat
	leg.add_child(foot)
	foot.owner = owner_node
	
	return leg

# Animation: Idle (subtle breathing motion)
func _create_idle_animation(height: float) -> Animation:
	var anim = Animation.new()
	anim.length = 2.0
	anim.loop_mode = Animation.LOOP_LINEAR
	
	# Subtle torso breathing
	var torso_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(torso_track, "Body/Torso:scale")
	anim.track_insert_key(torso_track, 0.0, Vector3(1, 1, 1))
	anim.track_insert_key(torso_track, 1.0, Vector3(1.02, 1.01, 1.02))
	anim.track_insert_key(torso_track, 2.0, Vector3(1, 1, 1))
	
	return anim

# Animation: Walk cycle
func _create_walk_animation(height: float) -> Animation:
	var anim = Animation.new()
	anim.length = 0.8
	anim.loop_mode = Animation.LOOP_LINEAR
	
	var swing = 0.3  # Arm/leg swing amount
	
	# Left arm swing (opposite to left leg)
	var left_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_arm_track, "Body/LeftArm:rotation")
	anim.track_insert_key(left_arm_track, 0.0, Vector3(swing, 0, 0))
	anim.track_insert_key(left_arm_track, 0.4, Vector3(-swing, 0, 0))
	anim.track_insert_key(left_arm_track, 0.8, Vector3(swing, 0, 0))
	
	# Right arm swing
	var right_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_arm_track, "Body/RightArm:rotation")
	anim.track_insert_key(right_arm_track, 0.0, Vector3(-swing, 0, 0))
	anim.track_insert_key(right_arm_track, 0.4, Vector3(swing, 0, 0))
	anim.track_insert_key(right_arm_track, 0.8, Vector3(-swing, 0, 0))
	
	# Left leg swing
	var left_leg_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_leg_track, "Body/LeftLeg:rotation")
	anim.track_insert_key(left_leg_track, 0.0, Vector3(-swing, 0, 0))
	anim.track_insert_key(left_leg_track, 0.4, Vector3(swing, 0, 0))
	anim.track_insert_key(left_leg_track, 0.8, Vector3(-swing, 0, 0))
	
	# Right leg swing
	var right_leg_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_leg_track, "Body/RightLeg:rotation")
	anim.track_insert_key(right_leg_track, 0.0, Vector3(swing, 0, 0))
	anim.track_insert_key(right_leg_track, 0.4, Vector3(-swing, 0, 0))
	anim.track_insert_key(right_leg_track, 0.8, Vector3(swing, 0, 0))
	
	return anim

# Animation: Run cycle (faster, larger swing)
func _create_run_animation(height: float) -> Animation:
	var anim = Animation.new()
	anim.length = 0.5
	anim.loop_mode = Animation.LOOP_LINEAR
	
	var swing = 0.5  # Larger swing for running
	
	# Left arm
	var left_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_arm_track, "Body/LeftArm:rotation")
	anim.track_insert_key(left_arm_track, 0.0, Vector3(swing, 0, 0))
	anim.track_insert_key(left_arm_track, 0.25, Vector3(-swing, 0, 0))
	anim.track_insert_key(left_arm_track, 0.5, Vector3(swing, 0, 0))
	
	# Right arm
	var right_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_arm_track, "Body/RightArm:rotation")
	anim.track_insert_key(right_arm_track, 0.0, Vector3(-swing, 0, 0))
	anim.track_insert_key(right_arm_track, 0.25, Vector3(swing, 0, 0))
	anim.track_insert_key(right_arm_track, 0.5, Vector3(-swing, 0, 0))
	
	# Left leg
	var left_leg_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_leg_track, "Body/LeftLeg:rotation")
	anim.track_insert_key(left_leg_track, 0.0, Vector3(-swing, 0, 0))
	anim.track_insert_key(left_leg_track, 0.25, Vector3(swing, 0, 0))
	anim.track_insert_key(left_leg_track, 0.5, Vector3(-swing, 0, 0))
	
	# Right leg
	var right_leg_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_leg_track, "Body/RightLeg:rotation")
	anim.track_insert_key(right_leg_track, 0.0, Vector3(swing, 0, 0))
	anim.track_insert_key(right_leg_track, 0.25, Vector3(-swing, 0, 0))
	anim.track_insert_key(right_leg_track, 0.5, Vector3(swing, 0, 0))
	
	return anim

# Animation: Jump
func _create_jump_animation(height: float) -> Animation:
	var anim = Animation.new()
	anim.length = 0.5
	anim.loop_mode = Animation.LOOP_NONE
	
	# Arms go up
	var left_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_arm_track, "Body/LeftArm:rotation")
	anim.track_insert_key(left_arm_track, 0.0, Vector3(0, 0, 0))
	anim.track_insert_key(left_arm_track, 0.2, Vector3(-0.5, 0, 0.3))
	anim.track_insert_key(left_arm_track, 0.5, Vector3(0, 0, 0))
	
	var right_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_arm_track, "Body/RightArm:rotation")
	anim.track_insert_key(right_arm_track, 0.0, Vector3(0, 0, 0))
	anim.track_insert_key(right_arm_track, 0.2, Vector3(-0.5, 0, -0.3))
	anim.track_insert_key(right_arm_track, 0.5, Vector3(0, 0, 0))
	
	return anim

func _create_enemy(client_id: int, params: Dictionary, command_id: String) -> void:
	var scene_path: String = params.get("scene_path", "res://scenes/enemy.tscn")
	var enemy_type: String = params.get("enemy_type", "zombie")
	var script_content: String = params.get("script_content", "")
	
	# Enemy appearance - zombies have green/gray skin, torn clothes
	var skin_color: Array = params.get("skin_color", [0.4, 0.5, 0.35])  # Greenish zombie skin
	var shirt_color: Array = params.get("shirt_color", [0.3, 0.25, 0.2])  # Torn brown shirt
	var pants_color: Array = params.get("pants_color", [0.2, 0.2, 0.15])  # Dark torn pants
	var hair_color: Array = params.get("hair_color", [0.15, 0.15, 0.1])  # Dark messy hair
	
	# Set colors based on enemy type
	match enemy_type:
		"zombie":
			skin_color = [0.4, 0.55, 0.35]  # Green zombie
		"zombie_fast":
			skin_color = [0.5, 0.45, 0.35]  # Yellowish fast zombie
		"zombie_tank":
			skin_color = [0.35, 0.4, 0.45]  # Grayish tank zombie
	
	var enemy_height: float = 1.8
	
	# Ensure path format
	if not scene_path.begins_with("res://"):
		scene_path = "res://" + scene_path
	if not scene_path.ends_with(".tscn"):
		scene_path += ".tscn"
	
	# Create enemy
	var enemy = CharacterBody3D.new()
	enemy.name = "Enemy"
	enemy.add_to_group("enemies")
	
	# Collision shape
	var collision = CollisionShape3D.new()
	collision.name = "CollisionShape3D"
	var capsule = CapsuleShape3D.new()
	capsule.height = enemy_height
	capsule.radius = 0.4
	collision.shape = capsule
	collision.position.y = enemy_height / 2
	enemy.add_child(collision)
	collision.owner = enemy
	
	# === CREATE ZOMBIE BODY ===
	var body = Node3D.new()
	body.name = "Body"
	enemy.add_child(body)
	body.owner = enemy
	
	# Create materials
	var hair_mat = _create_material(hair_color)
	var skin_mat = _create_material(skin_color)
	var shirt_mat = _create_material(shirt_color)
	var pants_mat = _create_material(pants_color)
	var shoes_mat = _create_material([0.1, 0.1, 0.08])
	
	# Body proportions
	var head_radius = enemy_height * 0.08
	var torso_height = enemy_height * 0.3
	var torso_width = enemy_height * 0.22  # Slightly wider for zombie
	var arm_length = enemy_height * 0.28
	var arm_radius = enemy_height * 0.04
	var leg_length = enemy_height * 0.28
	var leg_radius = enemy_height * 0.05
	var foot_height = enemy_height * 0.05
	
	# HEAD (tilted for zombie look)
	var head = Node3D.new()
	head.name = "Head"
	head.position.y = enemy_height * 0.85
	head.rotation.z = 0.1  # Slight head tilt
	body.add_child(head)
	head.owner = enemy
	
	# Face
	var face_mesh = MeshInstance3D.new()
	face_mesh.name = "Face"
	var face_sphere = SphereMesh.new()
	face_sphere.radius = head_radius
	face_sphere.height = head_radius * 2
	face_mesh.mesh = face_sphere
	face_mesh.material_override = skin_mat
	head.add_child(face_mesh)
	face_mesh.owner = enemy
	
	# Messy hair
	var hair_mesh = MeshInstance3D.new()
	hair_mesh.name = "Hair"
	var hair_sphere = SphereMesh.new()
	hair_sphere.radius = head_radius * 1.15
	hair_sphere.height = head_radius * 1.0
	hair_mesh.mesh = hair_sphere
	hair_mesh.position.y = head_radius * 0.35
	hair_mesh.material_override = hair_mat
	head.add_child(hair_mesh)
	hair_mesh.owner = enemy
	
	# TORSO (hunched)
	var torso = MeshInstance3D.new()
	torso.name = "Torso"
	var torso_box = BoxMesh.new()
	torso_box.size = Vector3(torso_width, torso_height, torso_width * 0.6)
	torso.mesh = torso_box
	torso.position.y = enemy_height * 0.58
	torso.rotation.x = 0.15  # Hunched forward
	torso.material_override = shirt_mat
	body.add_child(torso)
	torso.owner = enemy
	
	# ARMS (slightly forward, zombie pose)
	var left_arm = _create_arm("LeftArm", -torso_width/2 - arm_radius, enemy_height * 0.68, 
							   arm_length, arm_radius, skin_mat, shirt_mat, enemy, body)
	left_arm.rotation.x = -0.3  # Arms reaching forward
	
	var right_arm = _create_arm("RightArm", torso_width/2 + arm_radius, enemy_height * 0.68,
							   arm_length, arm_radius, skin_mat, shirt_mat, enemy, body)
	right_arm.rotation.x = -0.4  # Slightly different for asymmetry
	
	# LEGS
	var left_leg = _create_leg("LeftLeg", -torso_width/4, enemy_height * 0.28,
							  leg_length, leg_radius, foot_height, pants_mat, shoes_mat, enemy, body)
	
	var right_leg = _create_leg("RightLeg", torso_width/4, enemy_height * 0.28,
							   leg_length, leg_radius, foot_height, pants_mat, shoes_mat, enemy, body)
	
	# === ANIMATION PLAYER ===
	var anim_player = AnimationPlayer.new()
	anim_player.name = "AnimationPlayer"
	body.add_child(anim_player)
	anim_player.owner = enemy
	
	var anim_lib = AnimationLibrary.new()
	
	# Zombie idle (swaying)
	var idle_anim = _create_zombie_idle_animation()
	anim_lib.add_animation("idle", idle_anim)
	
	# Zombie walk (shambling)
	var walk_anim = _create_zombie_walk_animation()
	anim_lib.add_animation("walk", walk_anim)
	
	# Zombie attack
	var attack_anim = _create_zombie_attack_animation()
	anim_lib.add_animation("attack", attack_anim)
	
	anim_player.add_animation_library("", anim_lib)
	
	# Attach script
	if not script_content.is_empty():
		var script = GDScript.new()
		script.source_code = script_content
		var err = script.reload()
		if err == OK:
			enemy.set_script(script)
	
	# Ensure directory
	var dir_path = scene_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir_path.replace("res://", ProjectSettings.globalize_path("res://")))
	
	# Save
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(enemy)
	if result != OK:
		enemy.queue_free()
		return _send_error(client_id, "Failed to pack enemy scene", command_id)
	
	result = ResourceSaver.save(packed_scene, scene_path)
	enemy.queue_free()
	
	if result != OK:
		return _send_error(client_id, "Failed to save enemy scene", command_id)
	
	_send_success(client_id, {
		"scene_path": scene_path,
		"enemy_type": enemy_type,
		"has_animations": true,
		"body_parts": ["Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]
	}, command_id)

# Zombie-specific animations
func _create_zombie_idle_animation() -> Animation:
	var anim = Animation.new()
	anim.length = 3.0
	anim.loop_mode = Animation.LOOP_LINEAR
	
	# Swaying motion
	var body_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(body_track, "Body:rotation")
	anim.track_insert_key(body_track, 0.0, Vector3(0, 0, 0.05))
	anim.track_insert_key(body_track, 1.5, Vector3(0, 0, -0.05))
	anim.track_insert_key(body_track, 3.0, Vector3(0, 0, 0.05))
	
	# Head bobbing
	var head_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(head_track, "Body/Head:rotation")
	anim.track_insert_key(head_track, 0.0, Vector3(0, 0, 0.1))
	anim.track_insert_key(head_track, 1.0, Vector3(0.1, 0.1, 0.1))
	anim.track_insert_key(head_track, 2.0, Vector3(-0.05, -0.1, 0.1))
	anim.track_insert_key(head_track, 3.0, Vector3(0, 0, 0.1))
	
	return anim

func _create_zombie_walk_animation() -> Animation:
	var anim = Animation.new()
	anim.length = 1.2  # Slower, shambling walk
	anim.loop_mode = Animation.LOOP_LINEAR
	
	var swing = 0.25
	
	# Shambling leg movement
	var left_leg_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_leg_track, "Body/LeftLeg:rotation")
	anim.track_insert_key(left_leg_track, 0.0, Vector3(-swing, 0, 0))
	anim.track_insert_key(left_leg_track, 0.6, Vector3(swing * 0.8, 0, 0.1))  # Dragging
	anim.track_insert_key(left_leg_track, 1.2, Vector3(-swing, 0, 0))
	
	var right_leg_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_leg_track, "Body/RightLeg:rotation")
	anim.track_insert_key(right_leg_track, 0.0, Vector3(swing, 0, 0))
	anim.track_insert_key(right_leg_track, 0.6, Vector3(-swing * 0.8, 0, -0.1))
	anim.track_insert_key(right_leg_track, 1.2, Vector3(swing, 0, 0))
	
	# Arms reaching forward
	var left_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_arm_track, "Body/LeftArm:rotation")
	anim.track_insert_key(left_arm_track, 0.0, Vector3(-0.4, 0, 0))
	anim.track_insert_key(left_arm_track, 0.6, Vector3(-0.3, 0.1, 0))
	anim.track_insert_key(left_arm_track, 1.2, Vector3(-0.4, 0, 0))
	
	var right_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_arm_track, "Body/RightArm:rotation")
	anim.track_insert_key(right_arm_track, 0.0, Vector3(-0.3, 0, 0))
	anim.track_insert_key(right_arm_track, 0.6, Vector3(-0.5, -0.1, 0))
	anim.track_insert_key(right_arm_track, 1.2, Vector3(-0.3, 0, 0))
	
	return anim

func _create_zombie_attack_animation() -> Animation:
	var anim = Animation.new()
	anim.length = 0.8
	anim.loop_mode = Animation.LOOP_NONE
	
	# Lunge forward with arms
	var left_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(left_arm_track, "Body/LeftArm:rotation")
	anim.track_insert_key(left_arm_track, 0.0, Vector3(-0.3, 0, 0))
	anim.track_insert_key(left_arm_track, 0.2, Vector3(-1.2, 0, 0))  # Swing down
	anim.track_insert_key(left_arm_track, 0.5, Vector3(-0.5, 0, 0))
	anim.track_insert_key(left_arm_track, 0.8, Vector3(-0.3, 0, 0))
	
	var right_arm_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(right_arm_track, "Body/RightArm:rotation")
	anim.track_insert_key(right_arm_track, 0.0, Vector3(-0.4, 0, 0))
	anim.track_insert_key(right_arm_track, 0.3, Vector3(-1.3, 0, 0))
	anim.track_insert_key(right_arm_track, 0.6, Vector3(-0.5, 0, 0))
	anim.track_insert_key(right_arm_track, 0.8, Vector3(-0.4, 0, 0))
	
	# Body lunge
	var body_track = anim.add_track(Animation.TYPE_VALUE)
	anim.track_set_path(body_track, "Body:position")
	anim.track_insert_key(body_track, 0.0, Vector3(0, 0, 0))
	anim.track_insert_key(body_track, 0.25, Vector3(0, 0, 0.3))
	anim.track_insert_key(body_track, 0.8, Vector3(0, 0, 0))
	
	return anim

func _create_weapon(client_id: int, params: Dictionary, command_id: String) -> void:
	var scene_path: String = params.get("scene_path", "res://scenes/weapon.tscn")
	var weapon_type: String = params.get("weapon_type", "raycast")
	var script_content: String = params.get("script_content", "")
	
	# Ensure path format
	if not scene_path.begins_with("res://"):
		scene_path = "res://" + scene_path
	if not scene_path.ends_with(".tscn"):
		scene_path += ".tscn"
	
	# Create weapon
	var weapon = Node3D.new()
	weapon.name = "Weapon"
	
	# RayCast for hit detection
	var raycast = RayCast3D.new()
	raycast.name = "RayCast3D"
	raycast.target_position = Vector3(0, 0, -100)
	raycast.enabled = true
	weapon.add_child(raycast)
	raycast.owner = weapon
	
	# Muzzle point
	var muzzle = Marker3D.new()
	muzzle.name = "Muzzle"
	muzzle.position = Vector3(0, 0, -0.5)
	weapon.add_child(muzzle)
	muzzle.owner = weapon
	
	# Attach script
	if not script_content.is_empty():
		var script = GDScript.new()
		script.source_code = script_content
		var err = script.reload()
		if err == OK:
			weapon.set_script(script)
	
	# Ensure directory
	var dir_path = scene_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir_path.replace("res://", ProjectSettings.globalize_path("res://")))
	
	# Save
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(weapon)
	if result != OK:
		weapon.queue_free()
		return _send_error(client_id, "Failed to pack weapon scene", command_id)
	
	result = ResourceSaver.save(packed_scene, scene_path)
	weapon.queue_free()
	
	if result != OK:
		return _send_error(client_id, "Failed to save weapon scene", command_id)
	
	_send_success(client_id, {
		"scene_path": scene_path,
		"weapon_type": weapon_type
	}, command_id)

func _setup_game_world(client_id: int, params: Dictionary, command_id: String) -> void:
	var scene_path: String = params.get("scene_path", "res://scenes/world.tscn")
	var world_size: float = params.get("world_size", 100.0)
	var include_navigation: bool = params.get("include_navigation", true)
	var sky_type: String = params.get("sky_type", "procedural")
	var ambient_color: Array = params.get("ambient_light_color", [0.2, 0.2, 0.3])
	
	# Ensure path format
	if not scene_path.begins_with("res://"):
		scene_path = "res://" + scene_path
	if not scene_path.ends_with(".tscn"):
		scene_path += ".tscn"
	
	# Create world root
	var world = Node3D.new()
	world.name = "World"
	
	# DirectionalLight3D (sun)
	var sun = DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-45, -45, 0)
	sun.shadow_enabled = true
	world.add_child(sun)
	sun.owner = world
	
	# WorldEnvironment
	var world_env = WorldEnvironment.new()
	world_env.name = "WorldEnvironment"
	var env = Environment.new()
	env.background_mode = Environment.BG_SKY
	
	# Create sky
	var sky = Sky.new()
	var sky_material = ProceduralSkyMaterial.new()
	sky.sky_material = sky_material
	env.sky = sky
	
	# Ambient light
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_color = Color(ambient_color[0], ambient_color[1], ambient_color[2])
	
	world_env.environment = env
	world.add_child(world_env)
	world_env.owner = world
	
	# Ground plane
	var ground = StaticBody3D.new()
	ground.name = "Ground"
	world.add_child(ground)
	ground.owner = world
	
	var ground_collision = CollisionShape3D.new()
	ground_collision.name = "CollisionShape3D"
	var ground_shape = BoxShape3D.new()
	ground_shape.size = Vector3(world_size, 0.1, world_size)
	ground_collision.shape = ground_shape
	ground_collision.position.y = -0.05
	ground.add_child(ground_collision)
	ground_collision.owner = world
	
	var ground_mesh = MeshInstance3D.new()
	ground_mesh.name = "MeshInstance3D"
	var plane_mesh = BoxMesh.new()
	plane_mesh.size = Vector3(world_size, 0.1, world_size)
	ground_mesh.mesh = plane_mesh
	ground_mesh.position.y = -0.05
	ground.add_child(ground_mesh)
	ground_mesh.owner = world
	
	# Navigation (optional)
	if include_navigation:
		var nav_region = NavigationRegion3D.new()
		nav_region.name = "NavigationRegion3D"
		var nav_mesh = NavigationMesh.new()
		nav_region.navigation_mesh = nav_mesh
		world.add_child(nav_region)
		nav_region.owner = world
	
	# Ensure directory
	var dir_path = scene_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir_path.replace("res://", ProjectSettings.globalize_path("res://")))
	
	# Save
	var packed_scene = PackedScene.new()
	var result = packed_scene.pack(world)
	if result != OK:
		world.queue_free()
		return _send_error(client_id, "Failed to pack world scene", command_id)
	
	result = ResourceSaver.save(packed_scene, scene_path)
	world.queue_free()
	
	if result != OK:
		return _send_error(client_id, "Failed to save world scene", command_id)
	
	_send_success(client_id, {
		"scene_path": scene_path,
		"world_size": world_size
	}, command_id)

func _batch_update_properties(client_id: int, params: Dictionary, command_id: String) -> void:
	var updates: Array = params.get("updates", [])
	
	var plugin = Engine.get_meta("GodotMCPPlugin")
	if not plugin:
		return _send_error(client_id, "GodotMCPPlugin not found", command_id)
	
	var editor_interface = plugin.get_editor_interface()
	var edited_scene_root = editor_interface.get_edited_scene_root()
	
	if not edited_scene_root:
		return _send_error(client_id, "No scene is currently being edited", command_id)
	
	var updated_count = 0
	var errors: Array = []
	
	for update in updates:
		var node_path: String = update.get("node_path", "")
		var properties: Dictionary = update.get("properties", {})
		
		var node = edited_scene_root.get_node_or_null(node_path)
		if not node:
			errors.append("Node not found: " + node_path)
			continue
		
		for prop_name in properties:
			_set_property_smart(node, prop_name, properties[prop_name])
		
		updated_count += 1
	
	_send_success(client_id, {
		"updated_count": updated_count,
		"errors": errors
	}, command_id)

# Helper: Create node by type name
func _create_node_by_type(type_name: String) -> Node:
	if ClassDB.class_exists(type_name) and ClassDB.can_instantiate(type_name):
		return ClassDB.instantiate(type_name)
	return null

# Helper: Smart property setter that handles Godot types
func _set_property_smart(node: Node, prop_name: String, value) -> void:
	if value is Array:
		match value.size():
			2:
				node.set(prop_name, Vector2(value[0], value[1]))
			3:
				node.set(prop_name, Vector3(value[0], value[1], value[2]))
			4:
				node.set(prop_name, Color(value[0], value[1], value[2], value[3]))
			_:
				node.set(prop_name, value)
	else:
		node.set(prop_name, value)
