import { runCapability, evaluateCapability } from '../capability-runtime.mjs';

export const capabilityId = 'continuation-recovery';
export const run = (input = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) => runCapability(capabilityId, input, context);
export const evaluate = (result, input = {}, context = { connectorAvailable: false, externalWriteAuthorized: false }) => evaluateCapability(capabilityId, result, input, context);
