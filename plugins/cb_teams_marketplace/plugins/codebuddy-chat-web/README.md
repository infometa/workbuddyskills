# CodeBuddy Chat Web Plugin

Initialize a complete web-based chat application powered by CodeBuddy Agent SDK.

## Overview

This plugin provides a skill to quickly scaffold a full-stack chat application with:
- **Backend**: Express server with SSE (Server-Sent Events) and Agent SDK integration
- **Frontend**: React + Vite + TypeScript + TDesign React
- **Real-time**: SSE-based streaming responses
- **Multi-chat**: Support for multiple concurrent conversations with SQLite persistence

## Installation

### From Marketplace

```bash
codebuddy plugin install codebuddy-chat-web
```

### Manual Installation

Clone or copy this plugin to your CodeBuddy plugins directory:
```bash
cp -r plugins/codebuddy-chat-web ~/.codebuddy/plugins/
```

## Usage

### Quick Start

```bash
/init-cbc-sdk-web my-chat-app
```

This creates a new directory `my-chat-app` with a complete chat application.

### Interactive Mode

```bash
/init-cbc-sdk-web
```

The skill will prompt you for a project name.

## What Gets Created

The skill scaffolds a complete project with:

### Backend (server/)
- Express server with REST API
- SSE (Server-Sent Events) for real-time streaming
- Agent SDK integration
- Chat session management
- SQLite database for persistence

### Frontend (src/)
- React 18 application
- TDesign React UI components
  - Header, Sidebar, ChatMessages
  - ChatInput, ToolCallsCollapse
  - AgentConfigDialog, PermissionDialog
  - NewChatDialog, SettingsPage
- Custom hooks
  - useChat, useSessions, useAgents
  - useModels, useTheme
- Tailwind CSS + TDesign styling
- Responsive design

### Configuration
- TypeScript configuration
- Vite build setup
- TDesign + Tailwind CSS configuration
- SQLite database setup
- Package.json with all dependencies

## Next Steps After Initialization

1. **Navigate to project**:
   ```bash
   cd my-chat-app
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment** (可选):
   
   **方式一：使用 CodeBuddy CLI 登录**（推荐）
   ```bash
   codebuddy login
   ```
   
   **方式二：环境变量配置**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your configuration

4. **Start development server**:
   ```bash
   npm run dev
   ```
   This starts both backend (port 3000) and frontend (port 5173)

5. **Open browser**: Navigate to `http://localhost:5173`

## Features

- **Multi-chat support**: Create and manage multiple conversations
- **Real-time streaming**: See AI responses as they're generated via SSE
- **Tool call visualization**: View when the agent uses tools with expandable details
- **Permission control**: Support for multiple permission modes (default, acceptEdits, plan, bypassPermissions)
- **Custom agents**: Create and manage multiple agent configurations
- **Theme switching**: Support for light/dark themes
- **Session persistence**: SQLite-based data persistence
- **Modern UI**: TDesign React components with clean, responsive interface
- **TypeScript**: Full type safety across frontend and backend

## Requirements

- Node.js 18 or higher
- CodeBuddy API key (get from https://www.codebuddy.cn)
- Modern web browser

## Troubleshooting

### "CodeBuddy CLI not found"
Ensure CodeBuddy CLI is installed and in your PATH:
```bash
which codebuddy
```

### "Connection refused" on port 3000
Check if another process is using port 3000:
```bash
lsof -i :3000
```

### SSE connection fails
Verify the backend server is running and check browser console for errors.

### API key errors
Either:
- Login with CodeBuddy CLI: `codebuddy login`
- Or configure environment variables in `.env`
- Or configure in the Settings page within the app

## Customization

After initialization, you can customize:
- **Agent configuration**: Create custom agents in the Settings page or modify default in code
- **UI components**: Modify files in `src/components/`
- **Styling**: Update `src/index.css`, TDesign theme, and Tailwind config
- **Server config**: Change settings in `server/index.ts`
- **Database schema**: Modify `server/db.ts`
- **Permission modes**: Configure in agent settings

## Learn More

- **TypeScript SDK Documentation**: https://www.codebuddy.ai/docs/zh/cli/sdk-typescript
- **General SDK Documentation**: https://www.codebuddy.ai/docs/zh/cli/sdk
- [SDK Guide](./rules/cbc_sdk_web.md) - Key concepts and best practices
- [Usage Examples](./skills/init-cbc-sdk-web/examples/usage-example.md) - Common use cases

## License

MIT
