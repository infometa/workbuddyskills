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
import { getGodotConnection } from '../utils/godot_connection.js';
/**
 * Resource that provides information about the current state of the Godot editor
 */
export var editorStateResource = {
    uri: 'godot/editor/state',
    name: 'Godot Editor State',
    mimeType: 'application/json',
    load: function () {
        return __awaiter(this, void 0, void 0, function () {
            var godot, result, error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        godot = getGodotConnection();
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, godot.sendCommand('get_editor_state')];
                    case 2:
                        result = _a.sent();
                        return [2 /*return*/, {
                                text: JSON.stringify(result)
                            }];
                    case 3:
                        error_1 = _a.sent();
                        console.error('Error fetching editor state:', error_1);
                        throw error_1;
                    case 4: return [2 /*return*/];
                }
            });
        });
    }
};
/**
 * Resource that provides information about the currently selected node
 */
export var selectedNodeResource = {
    uri: 'godot/editor/selected_node',
    name: 'Godot Selected Node',
    mimeType: 'application/json',
    load: function () {
        return __awaiter(this, void 0, void 0, function () {
            var godot, result, error_2;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        godot = getGodotConnection();
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, godot.sendCommand('get_selected_node')];
                    case 2:
                        result = _a.sent();
                        return [2 /*return*/, {
                                text: JSON.stringify(result)
                            }];
                    case 3:
                        error_2 = _a.sent();
                        console.error('Error fetching selected node:', error_2);
                        throw error_2;
                    case 4: return [2 /*return*/];
                }
            });
        });
    }
};
/**
 * Resource that provides information about the currently edited script
 */
export var currentScriptResource = {
    uri: 'godot/editor/current_script',
    name: 'Current Script in Editor',
    mimeType: 'text/plain',
    load: function () {
        return __awaiter(this, void 0, void 0, function () {
            var godot, result, error_3;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        godot = getGodotConnection();
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, godot.sendCommand('get_current_script')];
                    case 2:
                        result = _a.sent();
                        // If we got a script path, return script content and metadata
                        if (result && result.script_found && result.content) {
                            return [2 /*return*/, {
                                    text: result.content,
                                    metadata: {
                                        path: result.script_path,
                                        language: result.script_path.endsWith('.gd') ? 'gdscript' :
                                            result.script_path.endsWith('.cs') ? 'csharp' : 'unknown'
                                    }
                                }];
                        }
                        else {
                            return [2 /*return*/, {
                                    text: '',
                                    metadata: {
                                        error: 'No script currently being edited',
                                        script_found: false
                                    }
                                }];
                        }
                        return [3 /*break*/, 4];
                    case 3:
                        error_3 = _a.sent();
                        console.error('Error fetching current script:', error_3);
                        throw error_3;
                    case 4: return [2 /*return*/];
                }
            });
        });
    }
};
//# sourceMappingURL=editor_resources.js.map