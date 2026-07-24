"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadPolicyContext = loadPolicyContext;
const fs_1 = __importDefault(require("fs"));
const constants_1 = require("./constants");
const build_capabilities_1 = require("./build-capabilities");
const policy_types_1 = require("./policy-types");
function buildEvaluator(policy) {
    return {
        policy,
        packageScope: build_capabilities_1.PACKAGE_SCOPE,
    };
}
function warnPolicyFallback(message) {
    console.error(`⚠ CLI policy: ${message}`);
}
function loadPolicyContext() {
    if (!build_capabilities_1.POLICY_ENABLED) {
        return {
            enabled: false,
            source: 'disabled',
            policy: policy_types_1.BOOTSTRAP_POLICY,
            evaluator: buildEvaluator(policy_types_1.BOOTSTRAP_POLICY),
        };
    }
    try {
        const policyFile = (0, constants_1.resolveCliPolicyFile)();
        if (!fs_1.default.existsSync(policyFile)) {
            warnPolicyFallback('policy file missing, using bootstrap policy');
            return {
                enabled: true,
                source: 'bootstrap',
                policy: policy_types_1.BOOTSTRAP_POLICY,
                evaluator: buildEvaluator(policy_types_1.BOOTSTRAP_POLICY),
            };
        }
        const raw = fs_1.default.readFileSync(policyFile, 'utf-8');
        let parsed;
        try {
            parsed = JSON.parse(raw);
        }
        catch {
            warnPolicyFallback('policy file is not valid JSON, using bootstrap policy');
            return {
                enabled: true,
                source: 'bootstrap',
                policy: policy_types_1.BOOTSTRAP_POLICY,
                evaluator: buildEvaluator(policy_types_1.BOOTSTRAP_POLICY),
            };
        }
        try {
            const policy = (0, policy_types_1.parseCliPolicy)(parsed);
            return {
                enabled: true,
                source: 'local',
                policy,
                evaluator: buildEvaluator(policy),
            };
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            warnPolicyFallback(`policy schema invalid (${message}), using bootstrap policy`);
            return {
                enabled: true,
                source: 'bootstrap',
                policy: policy_types_1.BOOTSTRAP_POLICY,
                evaluator: buildEvaluator(policy_types_1.BOOTSTRAP_POLICY),
            };
        }
    }
    catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        warnPolicyFallback(`failed to load policy (${message}), using bootstrap policy`);
        return {
            enabled: true,
            source: 'bootstrap',
            policy: policy_types_1.BOOTSTRAP_POLICY,
            evaluator: buildEvaluator(policy_types_1.BOOTSTRAP_POLICY),
        };
    }
}
