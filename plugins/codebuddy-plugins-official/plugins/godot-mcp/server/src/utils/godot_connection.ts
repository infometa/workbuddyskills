import WebSocket from 'ws';

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
export class GodotConnection {
  private ws: WebSocket | null = null;
  private connected = false;
  private commandQueue: Map<string, { 
    resolve: (value: any) => void;
    reject: (reason: any) => void;
    timeout: NodeJS.Timeout;
  }> = new Map();
  private commandId = 0;
  private eventListeners: Map<string, Array<(data: any) => void>> = new Map();
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnecting = false;
  private manualDisconnect = false;  // Track if user manually disconnected
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 999999;  // Essentially unlimited reconnect attempts
  private baseReconnectDelay = 1000;  // Start with 1 second
  private maxReconnectDelay = 30000;  // Max 30 seconds between attempts
  
  /**
   * Creates a new Godot connection
   * @param url WebSocket URL for the Godot server
   * @param timeout Command timeout in ms
   */
  constructor(
    private url: string = 'ws://localhost:9080',
    private timeout: number = 30000  // Increased timeout for commands
  ) {
    console.error('GodotConnection created with URL:', this.url);
  }
  
  /**
   * Connects to the Godot WebSocket server
   */
  async connect(): Promise<void> {
    // If already connected and working, return immediately
    if (this.connected && this.ws?.readyState === WebSocket.OPEN) {
      return;
    }
    
    // If currently reconnecting, wait for that to complete
    if (this.reconnecting) {
      console.error('Already reconnecting, waiting...');
      return new Promise((resolve, reject) => {
        const checkInterval = setInterval(() => {
          if (this.connected && this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(checkInterval);
            resolve();
          } else if (!this.reconnecting) {
            clearInterval(checkInterval);
            reject(new Error('Reconnection failed'));
          }
        }, 500);
        
        // Timeout after 30 seconds
        setTimeout(() => {
          clearInterval(checkInterval);
          reject(new Error('Reconnection timeout'));
        }, 30000);
      });
    }
    
    // Reset manual disconnect flag when explicitly connecting
    this.manualDisconnect = false;
    
    // Clean up any existing broken connection
    this.cleanupConnection();
    
    return this.establishConnection();
  }
  
  /**
   * Establishes a new WebSocket connection
   */
  private establishConnection(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      console.error(`Connecting to Godot WebSocket server at ${this.url}...`);
      
      try {
        this.ws = new WebSocket(this.url, {
          protocol: 'json',
          handshakeTimeout: 10000,
          perMessageDeflate: false
        });
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
        return;
      }
      
      const connectionTimeout = setTimeout(() => {
        if (this.ws?.readyState !== WebSocket.OPEN) {
          console.error('Connection timeout');
          this.cleanupConnection();
          reject(new Error('Connection timeout'));
        }
      }, 15000);
      
      this.ws.on('open', () => {
        clearTimeout(connectionTimeout);
        this.connected = true;
        this.reconnecting = false;
        this.reconnectAttempts = 0;
        console.error('✓ Connected to Godot WebSocket server');
        this.startHeartbeat();
        resolve();
      });
      
      this.ws.on('message', (data: Buffer) => {
        this.handleMessage(data);
      });
      
      this.ws.on('pong', () => {
        // Connection is alive, reset any reconnect logic
        this.reconnectAttempts = 0;
      });
      
      this.ws.on('error', (error) => {
        console.error('WebSocket error:', error.message);
        // Don't reject here - let close handler deal with it
      });
      
      this.ws.on('close', (code, reason) => {
        clearTimeout(connectionTimeout);
        const wasConnected = this.connected;
        console.error(`WebSocket closed. Code: ${code}, Reason: ${reason?.toString() || 'none'}`);
        
        this.connected = false;
        this.stopHeartbeat();
        
        // If we were connected and this wasn't a manual disconnect, try to reconnect
        if (wasConnected && !this.manualDisconnect) {
          console.error('Connection lost, will auto-reconnect...');
          this.scheduleReconnect();
        } else if (!wasConnected) {
          // Connection failed during establishment
          reject(new Error(`Connection failed: ${reason?.toString() || 'unknown'}`));
        }
      });
    });
  }
  
  /**
   * Handles incoming WebSocket messages
   */
  private handleMessage(data: Buffer): void {
    try {
      const parsed = JSON.parse(data.toString());
      
      // Handle debug events (server-push from Godot)
      if (parsed.type === 'debug_event' && parsed.event) {
        this.emitEvent(parsed.event, parsed.data);
        return;
      }
      
      const response: GodotResponse = parsed;
      
      // Handle command responses
      if ('commandId' in response) {
        const commandId = response.commandId as string;
        const pendingCommand = this.commandQueue.get(commandId);
        
        if (pendingCommand) {
          clearTimeout(pendingCommand.timeout);
          this.commandQueue.delete(commandId);
          
          if (response.status === 'success') {
            pendingCommand.resolve(response.result);
          } else {
            pendingCommand.reject(new Error(response.message || 'Unknown error'));
          }
        }
      }
    } catch (error) {
      console.error('Error parsing response:', error);
    }
  }
  
  /**
   * Register a listener for Godot-pushed events (e.g. debug_event)
   */
  onEvent(eventType: string, handler: (data: any) => void): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    this.eventListeners.get(eventType)!.push(handler);
  }
  
  /**
   * Remove an event listener
   */
  offEvent(eventType: string, handler: (data: any) => void): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(handler);
      if (index >= 0) listeners.splice(index, 1);
    }
  }
  
  private emitEvent(eventType: string, data: any): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      for (const handler of listeners) {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${eventType}:`, error);
        }
      }
    }
    console.error(`[DebugEvent] ${eventType}: ${JSON.stringify(data).substring(0, 200)}`);
  }
  
  /**
   * Schedules an automatic reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.manualDisconnect || this.reconnecting) {
      return;
    }
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }
    
    this.reconnecting = true;
    
    // Exponential backoff with jitter
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(1.5, this.reconnectAttempts) + Math.random() * 1000,
      this.maxReconnectDelay
    );
    
    this.reconnectAttempts++;
    console.error(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${Math.round(delay)}ms...`);
    
    this.reconnectTimer = setTimeout(async () => {
      if (this.manualDisconnect) {
        this.reconnecting = false;
        return;
      }
      
      try {
        this.cleanupConnection();
        await this.establishConnection();
        console.error('✓ Reconnected successfully');
      } catch (error) {
        console.error('Reconnect failed:', (error as Error).message);
        this.reconnecting = false;
        // Schedule another reconnect
        this.scheduleReconnect();
      }
    }, delay);
  }
  
  /**
   * Sends a command to Godot and waits for a response
   */
  async sendCommand<T = any>(type: string, params: Record<string, any> = {}): Promise<T> {
    // Ensure we're connected before sending
    if (!this.isConnected()) {
      console.error('Not connected, attempting to connect before sending command...');
      await this.connect();
    }
    
    // Double-check connection after connect attempt
    if (!this.isConnected()) {
      throw new Error('Failed to establish connection to Godot');
    }
    
    return new Promise<T>((resolve, reject) => {
      const commandId = `cmd_${this.commandId++}`;
      
      const command: GodotCommand = {
        type,
        params,
        commandId
      };
      
      // Set timeout for command
      const timeoutId = setTimeout(() => {
        if (this.commandQueue.has(commandId)) {
          this.commandQueue.delete(commandId);
          reject(new Error(`Command timed out: ${type}`));
        }
      }, this.timeout);
      
      // Store the promise resolvers
      this.commandQueue.set(commandId, {
        resolve,
        reject,
        timeout: timeoutId
      });
      
      // Send the command
      try {
        if (this.ws?.readyState === WebSocket.OPEN) {
          console.error(`Sending command: ${type}`);
          this.ws.send(JSON.stringify(command));
        } else {
          clearTimeout(timeoutId);
          this.commandQueue.delete(commandId);
          reject(new Error('WebSocket not connected'));
        }
      } catch (error) {
        clearTimeout(timeoutId);
        this.commandQueue.delete(commandId);
        reject(error);
      }
    });
  }
  
  /**
   * Cleans up the connection without affecting reconnect state
   */
  private cleanupConnection(): void {
    this.stopHeartbeat();
    this.connected = false;
    
    if (this.ws) {
      try {
        // Remove all listeners to prevent duplicate handlers
        this.ws.removeAllListeners();
        if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
          this.ws.terminate();
        }
      } catch (e) {
        // Ignore errors during cleanup
      }
      this.ws = null;
    }
  }
  
  /**
   * Full cleanup including pending commands and reconnect timers
   */
  private fullCleanup(): void {
    this.cleanupConnection();
    
    // Clear reconnect timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    // Reject all pending commands
    this.commandQueue.forEach((command) => {
      clearTimeout(command.timeout);
      command.reject(new Error('Connection closed'));
    });
    this.commandQueue.clear();
    
    this.reconnecting = false;
    this.reconnectAttempts = 0;
  }
  
  /**
   * Starts the heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    // Send a ping every 15 seconds to keep the connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        try {
          this.ws.ping();
        } catch (e) {
          console.error('Heartbeat ping failed:', e);
        }
      }
    }, 15000);
  }
  
  /**
   * Stops the heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  /**
   * Manually disconnects from the Godot WebSocket server
   * This will stop auto-reconnect
   */
  disconnect(): void {
    console.error('Manual disconnect requested');
    this.manualDisconnect = true;
    this.fullCleanup();
  }
  
  /**
   * Resets the connection - useful after manual disconnect to allow reconnection
   */
  reset(): void {
    this.manualDisconnect = false;
    this.reconnectAttempts = 0;
  }
  
  /**
   * Checks if connected to Godot
   */
  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }
  
  /**
   * Gets the current connection status
   */
  getStatus(): { connected: boolean; reconnecting: boolean; attempts: number } {
    return {
      connected: this.isConnected(),
      reconnecting: this.reconnecting,
      attempts: this.reconnectAttempts
    };
  }
}

import { getConnectionManager } from './connection_manager.js';

/**
 * Gets a GodotConnection for the given project, or the active project if omitted.
 * Backward-compatible: calling without arguments behaves like the old singleton.
 */
export function getGodotConnection(projectName?: string): GodotConnection {
  return getConnectionManager().getConnection(projectName);
}