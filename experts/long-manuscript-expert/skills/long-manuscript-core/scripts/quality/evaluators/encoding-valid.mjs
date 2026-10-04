import { runGateForId, evaluateGateResult } from '../quality-gate-runtime.mjs';
export const gateId = "encoding.valid";
export const evaluatorVersion = '1.0.0';
export const evaluate = (invocation, context = { connectorAvailable: false, externalWriteAuthorized: false }) => runGateForId(gateId, invocation, context);
export const validate = (result, invocation) => evaluateGateResult(result, invocation);
