# Data and permission disclosure

This package adds no remote endpoint, telemetry collector, downloads, or executable code. WorkBuddy launches the already installed NVIDIA bridge, which connects to the local NVIDIA backend. This does not assert that NVIDIA App itself has no network activity.

Tool results can reveal installed games/apps, driver versions, feature settings, process IDs and active game information. WorkBuddy may include those results in its conversation/model processing under its own service settings and privacy terms. Local MCP transport is not a promise that all conversation data stays on-device.

Six tools inspect state. Six can launch applications, change game/feature settings, or perform Overlay actions. Recording/screenshot/replay actions can create local media and capture visible or audible content using existing NVIDIA settings. These should be used only for the user's clearly requested action. This skill excludes enabling Desktop Capture and does not upload capture media.

Credentials are entered in WorkBuddy's password form and injected into the child process environment. The skill must not ask for them in chat. The native NVIDIA session token rotates on server restart; this adapter does not add narrower token scopes or automatic refresh.

To stop this integration, disconnect/disable it through WorkBuddy. To stop the NVIDIA MCP server for all clients, the user can disable its AI Agents and App Connections setting in NVIDIA App. Disconnecting the connector does not stop an existing recording, undo settings, or delete captured files; the user must request those actions separately.

For public submission, the publisher must provide an actual support contact and privacy statement covering its deployment and support practices. This technical disclosure is not a replacement for those publisher details.
