import { GodotConnection } from './godot_connection.js';
import { ProjectConfig } from './project_registry.js';
export declare class GodotConnectionManager {
    private connections;
    getConnection(projectName?: string): GodotConnection;
    addProject(config: ProjectConfig): void;
    removeProject(name: string): void;
    connectAll(): Promise<void>;
    disconnectAll(): void;
    getStatus(): Array<{
        name: string;
        port: number;
        connected: boolean;
    }>;
}
export declare function getConnectionManager(): GodotConnectionManager;
