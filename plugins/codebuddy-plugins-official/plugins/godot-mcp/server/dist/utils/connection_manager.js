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
import { GodotConnection } from './godot_connection.js';
import { getProjectRegistry } from './project_registry.js';
var GodotConnectionManager = /** @class */ (function () {
    function GodotConnectionManager() {
        this.connections = new Map();
    }
    GodotConnectionManager.prototype.getConnection = function (projectName) {
        var registry = getProjectRegistry();
        var name = projectName !== null && projectName !== void 0 ? projectName : registry.getActiveProject();
        if (!name) {
            // Fallback: no project registered — use default single connection
            if (!this.connections.has('__default__')) {
                var defaultPort = parseInt(process.env.GODOT_WS_PORT || '9080', 10);
                this.connections.set('__default__', new GodotConnection("ws://localhost:".concat(defaultPort)));
            }
            return this.connections.get('__default__');
        }
        if (this.connections.has(name)) {
            return this.connections.get(name);
        }
        var project = registry.getProject(name);
        if (!project) {
            throw new Error("Project \"".concat(name, "\" not found in registry"));
        }
        var conn = new GodotConnection("ws://localhost:".concat(project.port));
        this.connections.set(name, conn);
        return conn;
    };
    GodotConnectionManager.prototype.addProject = function (config) {
        if (this.connections.has(config.name)) {
            return;
        }
        this.connections.set(config.name, new GodotConnection("ws://localhost:".concat(config.port)));
    };
    GodotConnectionManager.prototype.removeProject = function (name) {
        var conn = this.connections.get(name);
        if (conn) {
            conn.disconnect();
            this.connections.delete(name);
        }
    };
    GodotConnectionManager.prototype.connectAll = function () {
        return __awaiter(this, void 0, void 0, function () {
            var registry, _i, _a, project, conn, err_1;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        registry = getProjectRegistry();
                        _i = 0, _a = registry.listProjects();
                        _b.label = 1;
                    case 1:
                        if (!(_i < _a.length)) return [3 /*break*/, 6];
                        project = _a[_i];
                        _b.label = 2;
                    case 2:
                        _b.trys.push([2, 4, , 5]);
                        conn = this.getConnection(project.name);
                        return [4 /*yield*/, conn.connect()];
                    case 3:
                        _b.sent();
                        console.error("Connected to project \"".concat(project.name, "\" on port ").concat(project.port));
                        return [3 /*break*/, 5];
                    case 4:
                        err_1 = _b.sent();
                        console.warn("Could not connect to project \"".concat(project.name, "\": ").concat(err_1.message));
                        return [3 /*break*/, 5];
                    case 5:
                        _i++;
                        return [3 /*break*/, 1];
                    case 6: return [2 /*return*/];
                }
            });
        });
    };
    GodotConnectionManager.prototype.disconnectAll = function () {
        this.connections.forEach(function (conn) {
            conn.disconnect();
        });
        this.connections.clear();
    };
    GodotConnectionManager.prototype.getStatus = function () {
        var _this = this;
        var registry = getProjectRegistry();
        var projects = registry.listProjects();
        if (projects.length === 0) {
            var def = this.connections.get('__default__');
            if (def) {
                var port = parseInt(process.env.GODOT_WS_PORT || '9080', 10);
                return [{ name: '__default__', port: port, connected: def.isConnected() }];
            }
            return [];
        }
        return projects.map(function (p) {
            var _a;
            var conn = _this.connections.get(p.name);
            return { name: p.name, port: p.port, connected: (_a = conn === null || conn === void 0 ? void 0 : conn.isConnected()) !== null && _a !== void 0 ? _a : false };
        });
    };
    return GodotConnectionManager;
}());
export { GodotConnectionManager };
var managerInstance = null;
export function getConnectionManager() {
    if (!managerInstance) {
        managerInstance = new GodotConnectionManager();
    }
    return managerInstance;
}
//# sourceMappingURL=connection_manager.js.map