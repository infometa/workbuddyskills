import { GodotConnection } from './godot_connection.js';
import { getProjectRegistry, ProjectConfig } from './project_registry.js';

export class GodotConnectionManager {
  private connections: Map<string, GodotConnection> = new Map();

  getConnection(projectName?: string): GodotConnection {
    const registry = getProjectRegistry();
    const name = projectName ?? registry.getActiveProject();

    if (!name) {
      // Fallback: no project registered — use default single connection
      if (!this.connections.has('__default__')) {
        const defaultPort = parseInt(process.env.GODOT_WS_PORT || '9080', 10);
        this.connections.set('__default__', new GodotConnection(`ws://localhost:${defaultPort}`));
      }
      return this.connections.get('__default__')!;
    }

    if (this.connections.has(name)) {
      return this.connections.get(name)!;
    }

    const project = registry.getProject(name);
    if (!project) {
      throw new Error(`Project "${name}" not found in registry`);
    }

    const conn = new GodotConnection(`ws://localhost:${project.port}`);
    this.connections.set(name, conn);
    return conn;
  }

  addProject(config: ProjectConfig): void {
    if (this.connections.has(config.name)) {
      return;
    }
    this.connections.set(
      config.name,
      new GodotConnection(`ws://localhost:${config.port}`),
    );
  }

  removeProject(name: string): void {
    const conn = this.connections.get(name);
    if (conn) {
      conn.disconnect();
      this.connections.delete(name);
    }
  }

  async connectAll(): Promise<void> {
    const registry = getProjectRegistry();
    for (const project of registry.listProjects()) {
      try {
        const conn = this.getConnection(project.name);
        await conn.connect();
        console.error(`Connected to project "${project.name}" on port ${project.port}`);
      } catch (err) {
        console.warn(`Could not connect to project "${project.name}": ${(err as Error).message}`);
      }
    }
  }

  disconnectAll(): void {
    this.connections.forEach((conn) => {
      conn.disconnect();
    });
    this.connections.clear();
  }

  getStatus(): Array<{ name: string; port: number; connected: boolean }> {
    const registry = getProjectRegistry();
    const projects = registry.listProjects();

    if (projects.length === 0) {
      const def = this.connections.get('__default__');
      if (def) {
        const port = parseInt(process.env.GODOT_WS_PORT || '9080', 10);
        return [{ name: '__default__', port, connected: def.isConnected() }];
      }
      return [];
    }

    return projects.map(p => {
      const conn = this.connections.get(p.name);
      return { name: p.name, port: p.port, connected: conn?.isConnected() ?? false };
    });
  }
}

let managerInstance: GodotConnectionManager | null = null;

export function getConnectionManager(): GodotConnectionManager {
  if (!managerInstance) {
    managerInstance = new GodotConnectionManager();
  }
  return managerInstance;
}
