var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
import WebSocket from 'ws';
/**
 * Manages WebSocket connection to the Godot editor
 * Designed for long-running persistent connections
 */
var GodotConnection = /** @class */ (function () {
    /**
     * Creates a new Godot connection
     * @param url WebSocket URL for the Godot server
     * @param timeout Command timeout in ms
     */
    function GodotConnection(url, timeout // Increased timeout for commands
    ) {
        if (url === void 0) { url = 'ws://localhost:9080'; }
        if (timeout === void 0) { timeout = 30000; }
        this.url = url;
        this.timeout = timeout;
        this.ws = null;
        this.connected = false;
        this.commandQueue = new Map();
        this.commandId = 0;
        this.eventListeners = new Map();
        this.heartbeatInterval = null;
        this.reconnectTimer = null;
        this.reconnecting = false;
        this.manualDisconnect = false; // Track if user manually disconnected
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 999999; // Essentially unlimited reconnect attempts
        this.baseReconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds between attempts
        console.error('GodotConnection created with URL:', this.url);
    }
    /**
     * Connects to the Godot WebSocket server
     */
    GodotConnection.prototype.connect = function () {
        return __awaiter(this, void 0, void 0, function () {
            var _this = this;
            var _a;
            return __generator(this, function (_b) {
                // If already connected and working, return immediately
                if (this.connected && ((_a = this.ws) === null || _a === void 0 ? void 0 : _a.readyState) === WebSocket.OPEN) {
                    return [2 /*return*/];
                }
                // If currently reconnecting, wait for that to complete
                if (this.reconnecting) {
                    console.error('Already reconnecting, waiting...');
                    return [2 /*return*/, new Promise(function (resolve, reject) {
                            var checkInterval = setInterval(function () {
                                var _a;
                                if (_this.connected && ((_a = _this.ws) === null || _a === void 0 ? void 0 : _a.readyState) === WebSocket.OPEN) {
                                    clearInterval(checkInterval);
                                    resolve();
                                }
                                else if (!_this.reconnecting) {
                                    clearInterval(checkInterval);
                                    reject(new Error('Reconnection failed'));
                                }
                            }, 500);
                            // Timeout after 30 seconds
                            setTimeout(function () {
                                clearInterval(checkInterval);
                                reject(new Error('Reconnection timeout'));
                            }, 30000);
                        })];
                }
                // Reset manual disconnect flag when explicitly connecting
                this.manualDisconnect = false;
                // Clean up any existing broken connection
                this.cleanupConnection();
                return [2 /*return*/, this.establishConnection()];
            });
        });
    };
    /**
     * Establishes a new WebSocket connection
     */
    GodotConnection.prototype.establishConnection = function () {
        var _this = this;
        return new Promise(function (resolve, reject) {
            console.error("Connecting to Godot WebSocket server at ".concat(_this.url, "..."));
            try {
                _this.ws = new WebSocket(_this.url, {
                    protocol: 'json',
                    handshakeTimeout: 10000,
                    perMessageDeflate: false
                });
            }
            catch (error) {
                console.error('Failed to create WebSocket:', error);
                reject(error);
                return;
            }
            var connectionTimeout = setTimeout(function () {
                var _a;
                if (((_a = _this.ws) === null || _a === void 0 ? void 0 : _a.readyState) !== WebSocket.OPEN) {
                    console.error('Connection timeout');
                    _this.cleanupConnection();
                    reject(new Error('Connection timeout'));
                }
            }, 15000);
            _this.ws.on('open', function () {
                clearTimeout(connectionTimeout);
                _this.connected = true;
                _this.reconnecting = false;
                _this.reconnectAttempts = 0;
                console.error('✓ Connected to Godot WebSocket server');
                _this.startHeartbeat();
                resolve();
            });
            _this.ws.on('message', function (data) {
                _this.handleMessage(data);
            });
            _this.ws.on('pong', function () {
                // Connection is alive, reset any reconnect logic
                _this.reconnectAttempts = 0;
            });
            _this.ws.on('error', function (error) {
                console.error('WebSocket error:', error.message);
                // Don't reject here - let close handler deal with it
            });
            _this.ws.on('close', function (code, reason) {
                clearTimeout(connectionTimeout);
                var wasConnected = _this.connected;
                console.error("WebSocket closed. Code: ".concat(code, ", Reason: ").concat((reason === null || reason === void 0 ? void 0 : reason.toString()) || 'none'));
                _this.connected = false;
                _this.stopHeartbeat();
                // If we were connected and this wasn't a manual disconnect, try to reconnect
                if (wasConnected && !_this.manualDisconnect) {
                    console.error('Connection lost, will auto-reconnect...');
                    _this.scheduleReconnect();
                }
                else if (!wasConnected) {
                    // Connection failed during establishment
                    reject(new Error("Connection failed: ".concat((reason === null || reason === void 0 ? void 0 : reason.toString()) || 'unknown')));
                }
            });
        });
    };
    /**
     * Handles incoming WebSocket messages
     */
    GodotConnection.prototype.handleMessage = function (data) {
        try {
            var parsed = JSON.parse(data.toString());
            // Handle debug events (server-push from Godot)
            if (parsed.type === 'debug_event' && parsed.event) {
                this.emitEvent(parsed.event, parsed.data);
                return;
            }
            var response = parsed;
            // Handle command responses
            if ('commandId' in response) {
                var commandId = response.commandId;
                var pendingCommand = this.commandQueue.get(commandId);
                if (pendingCommand) {
                    clearTimeout(pendingCommand.timeout);
                    this.commandQueue.delete(commandId);
                    if (response.status === 'success') {
                        pendingCommand.resolve(response.result);
                    }
                    else {
                        pendingCommand.reject(new Error(response.message || 'Unknown error'));
                    }
                }
            }
        }
        catch (error) {
            console.error('Error parsing response:', error);
        }
    };
    /**
     * Register a listener for Godot-pushed events (e.g. debug_event)
     */
    GodotConnection.prototype.onEvent = function (eventType, handler) {
        if (!this.eventListeners.has(eventType)) {
            this.eventListeners.set(eventType, []);
        }
        this.eventListeners.get(eventType).push(handler);
    };
    /**
     * Remove an event listener
     */
    GodotConnection.prototype.offEvent = function (eventType, handler) {
        var listeners = this.eventListeners.get(eventType);
        if (listeners) {
            var index = listeners.indexOf(handler);
            if (index >= 0)
                listeners.splice(index, 1);
        }
    };
    GodotConnection.prototype.emitEvent = function (eventType, data) {
        var listeners = this.eventListeners.get(eventType);
        if (listeners) {
            for (var _i = 0, listeners_1 = listeners; _i < listeners_1.length; _i++) {
                var handler = listeners_1[_i];
                try {
                    handler(data);
                }
                catch (error) {
                    console.error("Error in event handler for ".concat(eventType, ":"), error);
                }
            }
        }
        console.error("[DebugEvent] ".concat(eventType, ": ").concat(JSON.stringify(data).substring(0, 200)));
    };
    /**
     * Schedules an automatic reconnection attempt
     */
    GodotConnection.prototype.scheduleReconnect = function () {
        var _this = this;
        if (this.manualDisconnect || this.reconnecting) {
            return;
        }
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            return;
        }
        this.reconnecting = true;
        // Exponential backoff with jitter
        var delay = Math.min(this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts) + Math.random() * 1000, this.maxReconnectDelay);
        this.reconnectAttempts++;
        console.error("Scheduling reconnect attempt ".concat(this.reconnectAttempts, " in ").concat(Math.round(delay), "ms..."));
        this.reconnectTimer = setTimeout(function () { return __awaiter(_this, void 0, void 0, function () {
            var error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (this.manualDisconnect) {
                            this.reconnecting = false;
                            return [2 /*return*/];
                        }
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        this.cleanupConnection();
                        return [4 /*yield*/, this.establishConnection()];
                    case 2:
                        _a.sent();
                        console.error('✓ Reconnected successfully');
                        return [3 /*break*/, 4];
                    case 3:
                        error_1 = _a.sent();
                        console.error('Reconnect failed:', error_1.message);
                        this.reconnecting = false;
                        // Schedule another reconnect
                        this.scheduleReconnect();
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        }); }, delay);
    };
    /**
     * Sends a command to Godot and waits for a response
     */
    GodotConnection.prototype.sendCommand = function (type_1) {
        return __awaiter(this, arguments, void 0, function (type, params) {
            var _this = this;
            if (params === void 0) { params = {}; }
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        if (!!this.isConnected()) return [3 /*break*/, 2];
                        console.error('Not connected, attempting to connect before sending command...');
                        return [4 /*yield*/, this.connect()];
                    case 1:
                        _a.sent();
                        _a.label = 2;
                    case 2:
                        // Double-check connection after connect attempt
                        if (!this.isConnected()) {
                            throw new Error('Failed to establish connection to Godot');
                        }
                        return [2 /*return*/, new Promise(function (resolve, reject) {
                                var _a;
                                var commandId = "cmd_".concat(_this.commandId++);
                                var command = {
                                    type: type,
                                    params: params,
                                    commandId: commandId
                                };
                                // Set timeout for command
                                var timeoutId = setTimeout(function () {
                                    if (_this.commandQueue.has(commandId)) {
                                        _this.commandQueue.delete(commandId);
                                        reject(new Error("Command timed out: ".concat(type)));
                                    }
                                }, _this.timeout);
                                // Store the promise resolvers
                                _this.commandQueue.set(commandId, {
                                    resolve: resolve,
                                    reject: reject,
                                    timeout: timeoutId
                                });
                                // Send the command
                                try {
                                    if (((_a = _this.ws) === null || _a === void 0 ? void 0 : _a.readyState) === WebSocket.OPEN) {
                                        console.error("Sending command: ".concat(type));
                                        _this.ws.send(JSON.stringify(command));
                                    }
                                    else {
                                        clearTimeout(timeoutId);
                                        _this.commandQueue.delete(commandId);
                                        reject(new Error('WebSocket not connected'));
                                    }
                                }
                                catch (error) {
                                    clearTimeout(timeoutId);
                                    _this.commandQueue.delete(commandId);
                                    reject(error);
                                }
                            })];
                }
            });
        });
    };
    /**
     * Cleans up the connection without affecting reconnect state
     */
    GodotConnection.prototype.cleanupConnection = function () {
        this.stopHeartbeat();
        this.connected = false;
        if (this.ws) {
            try {
                // Remove all listeners to prevent duplicate handlers
                this.ws.removeAllListeners();
                if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
                    this.ws.terminate();
                }
            }
            catch (e) {
                // Ignore errors during cleanup
            }
            this.ws = null;
        }
    };
    /**
     * Full cleanup including pending commands and reconnect timers
     */
    GodotConnection.prototype.fullCleanup = function () {
        this.cleanupConnection();
        // Clear reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        // Reject all pending commands
        this.commandQueue.forEach(function (command) {
            clearTimeout(command.timeout);
            command.reject(new Error('Connection closed'));
        });
        this.commandQueue.clear();
        this.reconnecting = false;
        this.reconnectAttempts = 0;
    };
    /**
     * Starts the heartbeat to keep connection alive
     */
    GodotConnection.prototype.startHeartbeat = function () {
        var _this = this;
        this.stopHeartbeat();
        // Send a ping every 15 seconds to keep the connection alive
        this.heartbeatInterval = setInterval(function () {
            var _a;
            if (((_a = _this.ws) === null || _a === void 0 ? void 0 : _a.readyState) === WebSocket.OPEN) {
                try {
                    _this.ws.ping();
                }
                catch (e) {
                    console.error('Heartbeat ping failed:', e);
                }
            }
        }, 15000);
    };
    /**
     * Stops the heartbeat
     */
    GodotConnection.prototype.stopHeartbeat = function () {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    };
    /**
     * Manually disconnects from the Godot WebSocket server
     * This will stop auto-reconnect
     */
    GodotConnection.prototype.disconnect = function () {
        console.error('Manual disconnect requested');
        this.manualDisconnect = true;
        this.fullCleanup();
    };
    /**
     * Resets the connection - useful after manual disconnect to allow reconnection
     */
    GodotConnection.prototype.reset = function () {
        this.manualDisconnect = false;
        this.reconnectAttempts = 0;
    };
    /**
     * Checks if connected to Godot
     */
    GodotConnection.prototype.isConnected = function () {
        var _a;
        return this.connected && ((_a = this.ws) === null || _a === void 0 ? void 0 : _a.readyState) === WebSocket.OPEN;
    };
    /**
     * Gets the current connection status
     */
    GodotConnection.prototype.getStatus = function () {
        return {
            connected: this.isConnected(),
            reconnecting: this.reconnecting,
            attempts: this.reconnectAttempts
        };
    };
    return GodotConnection;
}());
export { GodotConnection };
import { getConnectionManager } from './connection_manager.js';
/**
 * Gets a GodotConnection for the given project, or the active project if omitted.
 * Backward-compatible: calling without arguments behaves like the old singleton.
 */
export function getGodotConnection(projectName) {
    return getConnectionManager().getConnection(projectName);
}
//# sourceMappingURL=godot_connection.js.map