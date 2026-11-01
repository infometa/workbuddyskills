#!/usr/bin/env node

import readline from "node:readline";

const UPSTREAM_URL = "https://api.tourmind.com/mcp/toc";
const UPSTREAM_TIMEOUT_MS = 110_000;
const CONNECTOR_VERSION = "1.0.9";
const configuredUserKey = (process.env.TOURMIND_USER_KEY || "").trim();
const USER_KEY = configuredUserKey.startsWith("uk_") && configuredUserKey.length >= 11
  ? configuredUserKey
  : "";

let upstreamSessionId;
let upstreamProtocolVersion;
let lastInitializeRequest;
let lastInitializedNotification;
let sessionRecoveryPromise;
let sessionNeedsRecovery = false;
let lifecycleBarrier = Promise.resolve();
let closing = false;
const activeRequests = new Map();
const activeOperations = new Set();
const inFlightTasks = new Set();
const jsonRpcEnvelopeKeys = new Set(["jsonrpc", "id", "method", "params", "result", "error"]);
const exposedTools = new Set([
  "search_location",
  "search_hotels",
  "get_hotel_detail",
  "query_room_rates",
  "batch_query_room_rates",
  "check_room_availability",
  "create_booking",
  "query_booking",
  "cancel_booking",
  "pay_order"
]);
const authenticatedTools = new Set([
  "create_booking",
  "query_booking",
  "cancel_booking",
  "pay_order"
]);

function redactCredential(value) {
  if (!USER_KEY) return value;
  if (typeof value === "string") return value.split(USER_KEY).join("[REDACTED]");
  if (Array.isArray(value)) return value.map(redactCredential);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        jsonRpcEnvelopeKeys.has(key) ? key : redactCredential(key),
        redactCredential(item)
      ])
    );
  }
  return value;
}

function writeMessage(message) {
  process.stdout.write(`${JSON.stringify(redactCredential(message))}\n`);
}

function jsonRpcError(id, code, message) {
  return {
    jsonrpc: "2.0",
    id: id ?? null,
    error: { code, message }
  };
}

class UpstreamHttpError extends Error {
  constructor(status, detail, usedSessionId) {
    const safeDetail = typeof detail === "string" ? redactCredential(detail) : "";
    super(`TourMind MCP returned HTTP ${status}${safeDetail ? `: ${safeDetail.slice(0, 300)}` : ""}`);
    this.name = "UpstreamHttpError";
    this.status = status;
    this.usedSessionId = usedSessionId;
  }
}

class LocalRequestError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "LocalRequestError";
    this.code = code;
  }
}

function createOperation(timeoutMs = UPSTREAM_TIMEOUT_MS) {
  const controller = new AbortController();
  const operation = {
    controller,
    timedOut: false,
    finish() {
      clearTimeout(timer);
      activeOperations.delete(operation);
    }
  };
  const timer = setTimeout(() => {
    operation.timedOut = true;
    controller.abort();
  }, timeoutMs);
  timer.unref?.();
  activeOperations.add(operation);
  return operation;
}

function errorMessage(error, operation) {
  if (operation?.timedOut) return "TourMind MCP request timed out.";
  if (error?.name === "AbortError") return "TourMind MCP request was cancelled.";
  return error instanceof Error ? error.message : "TourMind MCP adapter error";
}

async function waitWithSignal(promise, signal) {
  if (signal.aborted) throw signal.reason;

  let onAbort;
  const aborted = new Promise((_, reject) => {
    onAbort = () => reject(signal.reason);
    signal.addEventListener("abort", onAbort, { once: true });
  });
  try {
    return await Promise.race([promise, aborted]);
  } finally {
    signal.removeEventListener("abort", onAbort);
  }
}

function parseSse(text) {
  const messages = [];
  let dataLines = [];

  const flush = () => {
    if (dataLines.length === 0) return;
    const payload = dataLines.join("\n").trim();
    dataLines = [];
    if (!payload || payload === "[DONE]") return;
    messages.push(JSON.parse(payload));
  };

  for (const rawLine of text.split(/\r?\n/)) {
    if (rawLine === "") {
      flush();
    } else if (rawLine.startsWith("data:")) {
      dataLines.push(rawLine.slice(5).trimStart());
    }
  }
  flush();
  return messages;
}

async function postUpstream(message, signal, { useSession = true } = {}) {
  const usedSessionId = useSession ? upstreamSessionId : undefined;
  const headers = {
    Accept: "application/json, text/event-stream",
    "Content-Type": "application/json"
  };
  if (usedSessionId) headers["Mcp-Session-Id"] = usedSessionId;
  if (upstreamProtocolVersion) {
    headers["MCP-Protocol-Version"] = upstreamProtocolVersion;
  }

  const response = await fetch(UPSTREAM_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(message),
    redirect: "error",
    signal
  });

  if (!response.ok) {
    const detail = (await response.text()).trim();
    throw new UpstreamHttpError(response.status, detail, usedSessionId);
  }

  const nextSessionId = response.headers.get("mcp-session-id");
  if (nextSessionId && message.method === "initialize") {
    upstreamSessionId = nextSessionId;
  }

  if (response.status === 202 || response.status === 204) return [];
  const body = await response.text();
  if (!body.trim()) return [];

  const contentType = response.headers.get("content-type") || "";
  let messages;
  if (contentType.includes("text/event-stream")) {
    messages = parseSse(body);
  } else {
    const parsed = JSON.parse(body);
    messages = Array.isArray(parsed) ? parsed : [parsed];
  }
  if (!messages.every(isJsonRpcMessage)) {
    throw new Error("TourMind MCP returned an invalid JSON-RPC message.");
  }
  return messages;
}

function recordInitializeResponse(messages, requestId) {
  const initializeResponse = messages.find(
    (message) => message?.id === requestId && typeof message?.result?.protocolVersion === "string"
  );
  if (initializeResponse) upstreamProtocolVersion = initializeResponse.result.protocolVersion;
}

async function recoverSession(staleSessionId) {
  if (sessionRecoveryPromise) return sessionRecoveryPromise;
  if (upstreamSessionId && upstreamSessionId !== staleSessionId) return;
  if (!lastInitializeRequest) throw new Error("TourMind MCP session expired; reconnect the Connector.");

  const recovery = (async () => {
    sessionNeedsRecovery = true;
    if (!upstreamSessionId || upstreamSessionId === staleSessionId) {
      upstreamSessionId = undefined;
      upstreamProtocolVersion = undefined;
    }

    const operation = createOperation();
    try {
      const initializeMessages = await postUpstream(lastInitializeRequest, operation.controller.signal, {
        useSession: false
      });
      recordInitializeResponse(initializeMessages, lastInitializeRequest.id);
      await postUpstream(
        lastInitializedNotification || { jsonrpc: "2.0", method: "notifications/initialized" },
        operation.controller.signal
      );
      sessionNeedsRecovery = false;
    } catch (error) {
      upstreamSessionId = undefined;
      upstreamProtocolVersion = undefined;
      sessionNeedsRecovery = true;
      throw new Error(errorMessage(error, operation));
    } finally {
      operation.finish();
    }
  })();

  sessionRecoveryPromise = recovery;
  try {
    await recovery;
  } finally {
    if (sessionRecoveryPromise === recovery) sessionRecoveryPromise = undefined;
  }
}

async function callUpstream(message, signal) {
  if (message.method !== "initialize" && (sessionRecoveryPromise || sessionNeedsRecovery)) {
    const recovery = sessionRecoveryPromise || recoverSession(upstreamSessionId);
    await waitWithSignal(recovery, signal);
  }

  try {
    return await postUpstream(message, signal);
  } catch (error) {
    const canRecover = error instanceof UpstreamHttpError
      && error.status === 404
      && Boolean(error.usedSessionId)
      && typeof message.method === "string"
      && message.method !== "initialize";
    if (!canRecover) throw error;

    sessionNeedsRecovery = true;
    await waitWithSignal(recoverSession(error.usedSessionId), signal);
    return postUpstream(message, signal);
  }
}

function adaptDescription(description = "") {
  return description
    .replace(/owned by the user_key account/gi, "owned by the connected TourMind account")
    .replace(/A valid user_key is required\.?/gi, "Uses the connected TourMind account.")
    .replace(/user_key/gi, "connected account credential");
}

function stripUserKey(value) {
  if (Array.isArray(value)) return value.map(stripUserKey);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => key !== "user_key")
        .map(([key, item]) => [key, stripUserKey(item)])
    );
  }
  return value;
}

function adaptTool(tool) {
  const inputSchema = structuredClone(tool.inputSchema || { type: "object" });
  if (inputSchema.properties?.user_key) {
    delete inputSchema.properties.user_key;
  }
  if (Array.isArray(inputSchema.required)) {
    inputSchema.required = inputSchema.required.filter((field) => field !== "user_key");
  }

  return {
    ...tool,
    description: adaptDescription(tool.description),
    inputSchema
  };
}

function adaptUpstreamMessage(message, request) {
  if (message?.id !== request?.id || !message?.result) return message;

  if (request.method === "initialize") {
    const capabilities = {};
    for (const capability of ["tools", "logging"]) {
      if (message.result.capabilities?.[capability]) {
        capabilities[capability] = message.result.capabilities[capability];
      }
    }
    return {
      ...message,
      result: {
        ...message.result,
        capabilities,
        instructions: "Use TourMind tools for hotel discovery, live rates, booking, order management, cancellation, and payment. The WorkBuddy connector supplies the connected account credential automatically; never ask the user to paste it into chat and never include a user_key argument.",
        serverInfo: {
          ...message.result.serverInfo,
          name: "tourmind-hotel-booking-workbuddy",
          title: "TourMind Hotel Booking for WorkBuddy",
          version: CONNECTOR_VERSION
        }
      }
    };
  }

  if (request.method === "tools/list" && Array.isArray(message.result.tools)) {
    return {
      ...message,
      result: {
        ...message.result,
        tools: message.result.tools
          .filter((tool) => exposedTools.has(tool.name))
          .map(adaptTool)
      }
    };
  }

  return message;
}

function adaptLocalRequest(message) {
  if (message?.method === "initialize") {
    return {
      ...message,
      params: {
        ...message.params,
        capabilities: {}
      }
    };
  }
  if (message?.method !== "tools/call") return message;

  if (!message.params || typeof message.params !== "object" || Array.isArray(message.params)) {
    throw new LocalRequestError(-32602, "Invalid tools/call parameters.");
  }
  const toolName = message.params?.name;
  if (typeof toolName !== "string" || !exposedTools.has(toolName)) {
    const detail = toolName === "check_skill_update"
      ? "Skill updates are delivered through the WorkBuddy Connector marketplace."
      : "This tool is not exposed by the TourMind WorkBuddy Connector.";
    throw new LocalRequestError(-32602, detail);
  }

  const incomingArguments = message.params.arguments;
  if (
    incomingArguments !== undefined
    && (!incomingArguments || typeof incomingArguments !== "object" || Array.isArray(incomingArguments))
  ) {
    throw new LocalRequestError(-32602, "Tool arguments must be an object.");
  }
  const cleanArguments = stripUserKey(incomingArguments || {});

  if (authenticatedTools.has(toolName)) {
    if (!USER_KEY) {
      const reason = configuredUserKey ? "is invalid" : "is not configured";
      throw new Error(`TourMind user_key ${reason}. Update the Connector credential in WorkBuddy and reconnect.`);
    }
    cleanArguments.user_key = USER_KEY;
  }

  return {
    ...message,
    params: {
      ...message.params,
      arguments: cleanArguments
    }
  };
}

async function handleMessage(localMessage, requestContext) {
  if (closing) return;
  const expectsResponse = typeof localMessage.method === "string" && Object.hasOwn(localMessage, "id");
  let operation = requestContext?.operation;
  if (requestContext?.cancelled) {
    operation.finish();
    if (activeRequests.get(localMessage.id) === requestContext) {
      activeRequests.delete(localMessage.id);
    }
    return;
  }
  try {
    const upstreamRequest = adaptLocalRequest(localMessage);
    if (localMessage.method === "initialize") {
      upstreamSessionId = undefined;
      upstreamProtocolVersion = undefined;
      sessionNeedsRecovery = false;
      lastInitializedNotification = undefined;
      lastInitializeRequest = structuredClone(upstreamRequest);
    } else if (localMessage.method === "notifications/initialized") {
      lastInitializedNotification = structuredClone(upstreamRequest);
    }

    operation ||= createOperation();
    if (expectsResponse && !requestContext) {
      requestContext = { operation, cancelled: false };
      activeRequests.set(localMessage.id, requestContext);
    }

    const upstreamMessages = await callUpstream(upstreamRequest, operation.controller.signal);
    if (localMessage.method === "initialize") {
      recordInitializeResponse(upstreamMessages, localMessage.id);
    }
    for (const upstreamMessage of upstreamMessages) {
      if (!closing) writeMessage(adaptUpstreamMessage(upstreamMessage, localMessage));
    }
  } catch (error) {
    if (localMessage.method === "notifications/initialized") sessionNeedsRecovery = true;
    if (expectsResponse && !requestContext?.cancelled && !closing) {
      const code = error instanceof LocalRequestError ? error.code : -32000;
      writeMessage(jsonRpcError(localMessage.id, code, errorMessage(error, operation)));
    }
  } finally {
    operation?.finish();
    if (expectsResponse && activeRequests.get(localMessage.id) === requestContext) {
      activeRequests.delete(localMessage.id);
    }
  }
}

const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });

function isJsonRpcMessage(message) {
  if (!message || typeof message !== "object" || Array.isArray(message) || message.jsonrpc !== "2.0") {
    return false;
  }
  if (typeof message.method === "string") return true;

  const isResponse = Object.hasOwn(message, "id")
    && (Object.hasOwn(message, "result") !== Object.hasOwn(message, "error"));
  return isResponse;
}

function cancelActiveRequest(message) {
  if (message.method !== "notifications/cancelled") return;
  const requestContext = activeRequests.get(message.params?.requestId);
  if (!requestContext) return;
  requestContext.cancelled = true;
  requestContext.operation.controller.abort();
}

function scheduleMessage(message) {
  const expectsResponse = typeof message.method === "string" && Object.hasOwn(message, "id");
  const requestContext = expectsResponse
    ? { operation: createOperation(), cancelled: false }
    : undefined;
  if (requestContext) activeRequests.set(message.id, requestContext);

  let task;
  if (message.method === "initialize") {
    task = handleMessage(message, requestContext);
    lifecycleBarrier = task;
  } else if (message.method === "notifications/initialized") {
    task = lifecycleBarrier.then(() => handleMessage(message, requestContext));
    lifecycleBarrier = task;
  } else if (typeof message.method === "string" && message.method !== "notifications/cancelled") {
    task = lifecycleBarrier.then(() => handleMessage(message, requestContext));
  } else {
    task = handleMessage(message, requestContext);
  }
  inFlightTasks.add(task);
  void task.then(
    () => inFlightTasks.delete(task),
    () => inFlightTasks.delete(task)
  );
}

input.on("line", (line) => {
  if (!line.trim()) return;
  let message;
  try {
    message = JSON.parse(line);
  } catch {
    writeMessage(jsonRpcError(null, -32700, "Invalid JSON"));
    return;
  }

  if (!isJsonRpcMessage(message)) {
    const id = message && typeof message === "object" && !Array.isArray(message) && Object.hasOwn(message, "id")
      ? message.id
      : null;
    writeMessage(jsonRpcError(id, -32600, "Invalid Request"));
    return;
  }

  cancelActiveRequest(message);
  scheduleMessage(message);
});

input.on("close", () => {
  closing = true;
  for (const operation of activeOperations) operation.controller.abort();
  void Promise.allSettled([...inFlightTasks]).then(() => {
    process.exitCode = 0;
  });
});
