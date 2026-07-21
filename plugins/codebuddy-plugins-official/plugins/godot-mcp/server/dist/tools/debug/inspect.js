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
import { z } from 'zod';
import { getGodotConnection } from '../../utils/godot_connection.js';
/**
 * Debug group: minimal toolkit for the debug-fix loop.
 *   1. get_debug_errors    → one-shot scan of the whole project
 *   2. get_script_errors   → drill into a single script for fix details
 *   3. get_editor_output   → raw editor log tail for runtime issues
 */
export var debugTools = [
    {
        name: 'get_debug_errors',
        description: 'One-shot project scan: returns ALL current GDScript compilation errors plus errors ' +
            'extracted from the Godot editor log. Primary entry point for the debug-fix cycle:\n' +
            '1) call get_debug_errors → 2) for each error call get_script_errors for fix context → ' +
            '3) operate_script(action="edit") to apply the fix → 4) repeat until no errors.',
        parameters: z.object({
            include_log_errors: z.boolean().optional().describe('Include errors from Godot log file (default: true)'),
            directory: z.string().optional().describe('Root directory to scan (default: "res://")'),
            exclude_addons: z.boolean().optional().describe('Skip addons/ directory (default: true)'),
            project: z.string().optional().describe('Target project (defaults to active)'),
        }),
        execute: function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
            var godot, result, output, i, err, error_1;
            var include_log_errors = _b.include_log_errors, directory = _b.directory, exclude_addons = _b.exclude_addons, project = _b.project;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        godot = getGodotConnection(project);
                        _c.label = 1;
                    case 1:
                        _c.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, godot.sendCommand('get_debug_errors', {
                                include_log_errors: include_log_errors !== null && include_log_errors !== void 0 ? include_log_errors : true,
                                directory: directory !== null && directory !== void 0 ? directory : 'res://',
                                exclude_addons: exclude_addons !== null && exclude_addons !== void 0 ? exclude_addons : true,
                            })];
                    case 2:
                        result = _c.sent();
                        if (result.total_errors === 0) {
                            return [2 /*return*/, "\u2713 No errors found in the project.\n\nTimestamp: ".concat(result.timestamp)];
                        }
                        output = "\u2717 Found ".concat(result.total_errors, " error(s) (").concat(result.compile_errors, " compile, ").concat(result.log_errors, " log)\n");
                        output += "Timestamp: ".concat(result.timestamp, "\n\n");
                        for (i = 0; i < result.errors.length; i++) {
                            err = result.errors[i];
                            output += "\u2500\u2500 Error ".concat(i + 1, " \u2500\u2500\n");
                            output += "Type: ".concat(err.type, "\nSeverity: ").concat(err.severity, "\nMessage: ").concat(err.message, "\n");
                            if (err.file) {
                                output += "File: ".concat(err.file);
                                if (err.line > 0)
                                    output += ":".concat(err.line);
                                output += '\n';
                            }
                            output += '\n';
                        }
                        output += "\nNext: call get_script_errors(script_path) for fix context, then operate_script(action=\"edit\") to apply.";
                        return [2 /*return*/, output];
                    case 3:
                        error_1 = _c.sent();
                        throw new Error("Failed to get debug errors: ".concat(error_1.message));
                    case 4: return [2 /*return*/];
                }
            });
        }); },
    },
    {
        name: 'get_script_errors',
        description: 'Get DETAILED error information for a single script: exact line/column, code snippet, ' +
            'surrounding context, fix suggestions, and the full script content. ' +
            'Use after get_debug_errors to obtain the context needed to apply a fix.',
        parameters: z.object({
            script_path: z.string().describe('Path to the script (e.g. "res://scripts/player.gd")'),
            include_warnings: z.boolean().optional().describe('Include warnings (default: true)'),
            project: z.string().optional().describe('Target project (defaults to active)'),
        }),
        execute: function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
            var godot, result, output, i, e, _i, _c, w, error_2;
            var script_path = _b.script_path, _d = _b.include_warnings, include_warnings = _d === void 0 ? true : _d, project = _b.project;
            return __generator(this, function (_e) {
                switch (_e.label) {
                    case 0:
                        godot = getGodotConnection(project);
                        _e.label = 1;
                    case 1:
                        _e.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, godot.sendCommand('get_script_errors', {
                                script_path: script_path,
                                include_warnings: include_warnings,
                            })];
                    case 2:
                        result = _e.sent();
                        output = "Detailed Error Report: ".concat(script_path, "\n").concat('═'.repeat(50), "\n\n");
                        output += "Total Lines: ".concat(result.total_lines, "\nErrors: ").concat(result.errors.length, "\n");
                        if (include_warnings)
                            output += "Warnings: ".concat(result.warnings.length, "\n");
                        output += '\n';
                        if (result.errors.length === 0 && result.warnings.length === 0) {
                            return [2 /*return*/, output + "\u2713 No issues found.\n"];
                        }
                        if (result.errors.length > 0) {
                            output += "Errors:\n".concat('─'.repeat(50), "\n\n");
                            for (i = 0; i < result.errors.length; i++) {
                                e = result.errors[i];
                                output += "[Error ".concat(i + 1, "] ").concat(e.message, "\nLocation: Line ").concat(e.line);
                                if (e.column)
                                    output += ", Column ".concat(e.column);
                                output += '\n';
                                if (e.context)
                                    output += "\nContext:\n".concat(e.context, "\n");
                                if (e.suggestion)
                                    output += "\nSuggestion: ".concat(e.suggestion, "\n");
                                output += '\n';
                            }
                        }
                        if (include_warnings && result.warnings.length > 0) {
                            output += "Warnings:\n".concat('─'.repeat(50), "\n");
                            for (_i = 0, _c = result.warnings; _i < _c.length; _i++) {
                                w = _c[_i];
                                output += "Line ".concat(w.line, ": ").concat(w.message, "\n");
                            }
                            output += '\n';
                        }
                        output += "\nFull Script Content:\n".concat('─'.repeat(50), "\n```gdscript\n").concat(result.content, "\n```\n");
                        return [2 /*return*/, output];
                    case 3:
                        error_2 = _e.sent();
                        throw new Error("Failed to get script errors: ".concat(error_2.message));
                    case 4: return [2 /*return*/];
                }
            });
        }); },
    },
    {
        name: 'get_editor_output',
        description: 'Read the raw Godot editor Output panel log (errors, warnings, print() output). ' +
            'Use to diagnose runtime issues that do not surface as compile errors.',
        parameters: z.object({
            lines: z.number().int().min(1).max(1000).optional()
                .describe('Number of recent lines (default: 100)'),
            filter: z.enum(['all', 'errors', 'warnings']).optional()
                .describe('Filter: all | errors | warnings (default: all)'),
            project: z.string().optional().describe('Target project (defaults to active)'),
        }),
        execute: function (_a) { return __awaiter(void 0, [_a], void 0, function (_b) {
            var godot, result, output, _i, _c, err, error_3;
            var lines = _b.lines, filter = _b.filter, project = _b.project;
            return __generator(this, function (_d) {
                switch (_d.label) {
                    case 0:
                        godot = getGodotConnection(project);
                        _d.label = 1;
                    case 1:
                        _d.trys.push([1, 3, , 4]);
                        return [4 /*yield*/, godot.sendCommand('get_editor_output', {
                                lines: lines !== null && lines !== void 0 ? lines : 100,
                                filter: filter !== null && filter !== void 0 ? filter : 'all',
                            })];
                    case 2:
                        result = _d.sent();
                        output = "Godot Editor Output (".concat(result.filter, " | last ").concat(result.returned_lines, " of ").concat(result.total_lines, " lines)\n");
                        output += "Log file: ".concat(result.log_path, "\n").concat('─'.repeat(60), "\n");
                        output += result.output || '(empty)';
                        if (result.script_errors && result.script_errors.length > 0) {
                            output += '\n\n── Script Compilation Errors ──\n';
                            for (_i = 0, _c = result.script_errors; _i < _c.length; _i++) {
                                err = _c[_i];
                                output += "  ".concat(err.script, ": ").concat(err.status, "\n");
                            }
                        }
                        return [2 /*return*/, output];
                    case 3:
                        error_3 = _d.sent();
                        throw new Error("Failed to get editor output: ".concat(error_3.message));
                    case 4: return [2 /*return*/];
                }
            });
        }); },
    },
];
//# sourceMappingURL=inspect.js.map