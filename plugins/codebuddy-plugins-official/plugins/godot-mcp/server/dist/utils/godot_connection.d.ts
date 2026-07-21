/**
 * Response from Godot server
 */
export interface GodotResponse {
    status: 'success' | 'error';
    result?: any;
    message?: string;
    commandId?: string;
}
/**
 * Command to send to Godot
 */
export interface GodotCommand {
    type: string;
    params: Record<string, any>;
    commandId: string;
}
/**
 * Manages WebSocket connection to the Godot editor
 * Designed for long-running persistent connections
 */
export declare class GodotConnection {
    private url;
    private timeout;
    private ws;
    private connected;
    private commandQueue;
    private commandId;
    private eventListeners;
    private heartbeatInterval;
    private reconnectTimer;
    private reconnecting;
    private manualDisconnect;
    private reconnectAttempts;
    private maxReconnectAttempts;
    private baseReconnectDelay;
    private maxReconnectDelay;
    /**
     * Creates a new Godot connection
     * @param url WebSocket URL for the Godot server
     * @param timeout Command timeout in ms
     */
    constructor(url?: string, timeout?: number);
    /**
     * Connects to the Godot WebSocket server
     */
    connect(): Promise<void>;
    /**
     * Establishes a new WebSocket connection
     */
    private establishConnection;
    /**
     * Handles incoming WebSocket messages
     */
    private handleMessage;
    /**
     * Register a listener for Godot-pushed events (e.g. debug_event)
     */
    onEvent(eventType: string, handler: (data: any) => void): void;
    /**
     * Remove an event listener
     */
    offEvent(eventType: string, handler: (data: any) => void): void;
    private emitEvent;
    /**
     * Schedules an automatic reconnection attempt
     */
    private scheduleReconnect;
    /**
     * Sends a command to Godot and waits for a response
     */
    sendCommand<T = any>(type: string, params?: Record<string, any>): Promise<T>;
    /**
     * Cleans up the connection without affecting reconnect state
     */
    private cleanupConnection;
    /**
     * Full cleanup including pending commands and reconnect timers
     */
    private fullCleanup;
    /**
     * Starts the heartbeat to keep connection alive
     */
    private startHeartbeat;
    /**
     * Stops the heartbeat
     */
    private stopHeartbeat;
    /**
     * Manually disconnects from the Godot WebSocket server
     * This will stop auto-reconnect
     */
    disconnect(): void;
    /**
     * Resets the connection - useful after manual disconnect to allow reconnection
     */
    reset(): void;
    /**
     * Checks if connected to Godot
     */
    isConnected(): boolean;
    /**
     * Gets the current connection status
     */
    getStatus(): {
        connected: boolean;
        reconnecting: boolean;
        attempts: number;
    };
}
/**
 * Gets a GodotConnection for the given project, or the active project if omitted.
 * Backward-compatible: calling without arguments behaves like the old singleton.
 */
export declare function getGodotConnection(projectName?: string): GodotConnection;
