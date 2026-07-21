export interface ProjectConfig {
    name: string;
    port: number;
    path: string;
    createdAt: string;
}
export declare class ProjectRegistry {
    private data;
    constructor();
    reload(): void;
    save(): void;
    listProjects(): ProjectConfig[];
    getProject(name: string): ProjectConfig | undefined;
    getActiveProject(): string | null;
    setActiveProject(name: string): void;
    allocatePort(): Promise<number>;
    addProject(name: string, projectPath: string, port?: number): Promise<ProjectConfig>;
    removeProject(name: string): void;
}
export declare function getProjectRegistry(): ProjectRegistry;
