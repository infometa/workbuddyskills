import fs from 'fs';
import path from 'path';
import net from 'net';

export interface ProjectConfig {
  name: string;
  port: number;
  path: string;
  createdAt: string;
}

interface RegistryData {
  activeProject: string | null;
  projects: Record<string, ProjectConfig>;
  nextPort: number;
}

const DEFAULT_START_PORT = 9080;

function getRegistryPath(): string {
  const dataDir = process.env.CODEBUDDY_PLUGIN_DATA
    || process.env.CLAUDE_PLUGIN_DATA
    || path.join(process.cwd(), '.godot-mcp');

  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }
  return path.join(dataDir, 'projects.json');
}

function loadData(): RegistryData {
  const filePath = getRegistryPath();
  if (!fs.existsSync(filePath)) {
    return { activeProject: null, projects: {}, nextPort: DEFAULT_START_PORT };
  }
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return { activeProject: null, projects: {}, nextPort: DEFAULT_START_PORT };
  }
}

function saveData(data: RegistryData): void {
  fs.writeFileSync(getRegistryPath(), JSON.stringify(data, null, 2), 'utf8');
}

/**
 * Check whether a TCP port is available on localhost.
 */
function isPortAvailable(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.once('error', () => resolve(false));
    srv.once('listening', () => { srv.close(); resolve(true); });
    srv.listen(port, '127.0.0.1');
  });
}

export class ProjectRegistry {
  private data: RegistryData;

  constructor() {
    this.data = loadData();
  }

  reload(): void {
    this.data = loadData();
  }

  save(): void {
    saveData(this.data);
  }

  listProjects(): ProjectConfig[] {
    return Object.values(this.data.projects);
  }

  getProject(name: string): ProjectConfig | undefined {
    return this.data.projects[name];
  }

  getActiveProject(): string | null {
    return this.data.activeProject;
  }

  setActiveProject(name: string): void {
    if (!this.data.projects[name]) {
      throw new Error(`Project "${name}" not found in registry`);
    }
    this.data.activeProject = name;
    this.save();
  }

  async allocatePort(): Promise<number> {
    let port = this.data.nextPort;
    const usedPorts = new Set(Object.values(this.data.projects).map(p => p.port));

    while (usedPorts.has(port) || !(await isPortAvailable(port))) {
      port++;
      if (port > 65535) {
        throw new Error('No available port found');
      }
    }

    this.data.nextPort = port + 1;
    return port;
  }

  async addProject(name: string, projectPath: string, port?: number): Promise<ProjectConfig> {
    if (this.data.projects[name]) {
      throw new Error(`Project "${name}" already registered`);
    }

    const assignedPort = port ?? await this.allocatePort();
    const config: ProjectConfig = {
      name,
      port: assignedPort,
      path: path.resolve(projectPath),
      createdAt: new Date().toISOString(),
    };

    this.data.projects[name] = config;

    if (!this.data.activeProject) {
      this.data.activeProject = name;
    }

    this.save();
    return config;
  }

  removeProject(name: string): void {
    if (!this.data.projects[name]) {
      throw new Error(`Project "${name}" not found in registry`);
    }
    delete this.data.projects[name];

    if (this.data.activeProject === name) {
      const remaining = Object.keys(this.data.projects);
      this.data.activeProject = remaining.length > 0 ? remaining[0] : null;
    }
    this.save();
  }
}

let registryInstance: ProjectRegistry | null = null;

export function getProjectRegistry(): ProjectRegistry {
  if (!registryInstance) {
    registryInstance = new ProjectRegistry();
  }
  return registryInstance;
}
