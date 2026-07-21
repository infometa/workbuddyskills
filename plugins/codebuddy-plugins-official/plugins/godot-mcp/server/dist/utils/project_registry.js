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
import fs from 'fs';
import path from 'path';
import net from 'net';
var DEFAULT_START_PORT = 9080;
function getRegistryPath() {
    var dataDir = process.env.CODEBUDDY_PLUGIN_DATA
        || process.env.CLAUDE_PLUGIN_DATA
        || path.join(process.cwd(), '.godot-mcp');
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
    }
    return path.join(dataDir, 'projects.json');
}
function loadData() {
    var filePath = getRegistryPath();
    if (!fs.existsSync(filePath)) {
        return { activeProject: null, projects: {}, nextPort: DEFAULT_START_PORT };
    }
    try {
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
    catch (_a) {
        return { activeProject: null, projects: {}, nextPort: DEFAULT_START_PORT };
    }
}
function saveData(data) {
    fs.writeFileSync(getRegistryPath(), JSON.stringify(data, null, 2), 'utf8');
}
/**
 * Check whether a TCP port is available on localhost.
 */
function isPortAvailable(port) {
    return new Promise(function (resolve) {
        var srv = net.createServer();
        srv.once('error', function () { return resolve(false); });
        srv.once('listening', function () { srv.close(); resolve(true); });
        srv.listen(port, '127.0.0.1');
    });
}
var ProjectRegistry = /** @class */ (function () {
    function ProjectRegistry() {
        this.data = loadData();
    }
    ProjectRegistry.prototype.reload = function () {
        this.data = loadData();
    };
    ProjectRegistry.prototype.save = function () {
        saveData(this.data);
    };
    ProjectRegistry.prototype.listProjects = function () {
        return Object.values(this.data.projects);
    };
    ProjectRegistry.prototype.getProject = function (name) {
        return this.data.projects[name];
    };
    ProjectRegistry.prototype.getActiveProject = function () {
        return this.data.activeProject;
    };
    ProjectRegistry.prototype.setActiveProject = function (name) {
        if (!this.data.projects[name]) {
            throw new Error("Project \"".concat(name, "\" not found in registry"));
        }
        this.data.activeProject = name;
        this.save();
    };
    ProjectRegistry.prototype.allocatePort = function () {
        return __awaiter(this, void 0, void 0, function () {
            var port, usedPorts, _a;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        port = this.data.nextPort;
                        usedPorts = new Set(Object.values(this.data.projects).map(function (p) { return p.port; }));
                        _b.label = 1;
                    case 1:
                        _a = usedPorts.has(port);
                        if (_a) return [3 /*break*/, 3];
                        return [4 /*yield*/, isPortAvailable(port)];
                    case 2:
                        _a = !(_b.sent());
                        _b.label = 3;
                    case 3:
                        if (!_a) return [3 /*break*/, 4];
                        port++;
                        if (port > 65535) {
                            throw new Error('No available port found');
                        }
                        return [3 /*break*/, 1];
                    case 4:
                        this.data.nextPort = port + 1;
                        return [2 /*return*/, port];
                }
            });
        });
    };
    ProjectRegistry.prototype.addProject = function (name, projectPath, port) {
        return __awaiter(this, void 0, void 0, function () {
            var assignedPort, _a, config;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        if (this.data.projects[name]) {
                            throw new Error("Project \"".concat(name, "\" already registered"));
                        }
                        if (!(port !== null && port !== void 0)) return [3 /*break*/, 1];
                        _a = port;
                        return [3 /*break*/, 3];
                    case 1: return [4 /*yield*/, this.allocatePort()];
                    case 2:
                        _a = _b.sent();
                        _b.label = 3;
                    case 3:
                        assignedPort = _a;
                        config = {
                            name: name,
                            port: assignedPort,
                            path: path.resolve(projectPath),
                            createdAt: new Date().toISOString(),
                        };
                        this.data.projects[name] = config;
                        if (!this.data.activeProject) {
                            this.data.activeProject = name;
                        }
                        this.save();
                        return [2 /*return*/, config];
                }
            });
        });
    };
    ProjectRegistry.prototype.removeProject = function (name) {
        if (!this.data.projects[name]) {
            throw new Error("Project \"".concat(name, "\" not found in registry"));
        }
        delete this.data.projects[name];
        if (this.data.activeProject === name) {
            var remaining = Object.keys(this.data.projects);
            this.data.activeProject = remaining.length > 0 ? remaining[0] : null;
        }
        this.save();
    };
    return ProjectRegistry;
}());
export { ProjectRegistry };
var registryInstance = null;
export function getProjectRegistry() {
    if (!registryInstance) {
        registryInstance = new ProjectRegistry();
    }
    return registryInstance;
}
//# sourceMappingURL=project_registry.js.map