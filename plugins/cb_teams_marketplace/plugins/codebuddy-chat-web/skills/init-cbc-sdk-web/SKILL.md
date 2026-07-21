---
name: init-cbc-sdk-web
description: Initialize a complete web-based chat application powered by CodeBuddy Agent SDK with React frontend and Express backend
---

# init-cbc-sdk-web

Initialize a complete web-based chat application powered by CodeBuddy Agent SDK.

## Description

This skill scaffolds a full-stack chat application with:
- **Backend**: Express server with SSE support and CodeBuddy Agent SDK integration
- **Frontend**: React application with Vite, TypeScript, TDesign React, and Tailwind CSS
- **Real-time Communication**: SSE-based streaming with multi-chat support
- **Database**: SQLite for session and message persistence
- **Modern Stack**: TypeScript, React 18, TDesign React, Express 4, Vite 5

## When to use this skill

Use this skill when you need to:
- Create a new chat application powered by AI agents
- Build a web interface for CodeBuddy Agent SDK
- Set up a starter project for agent-based conversations
- Prototype AI-powered chat features
- Learn how to integrate CodeBuddy Agent SDK in a web application

## How to use this skill

### Interactive Mode
```bash
/init-cbc-sdk-web
```
The skill will ask you for a project name.

### Direct Mode
```bash
/init-cbc-sdk-web my-chat-app
```
Provide the project name directly as an argument.

## Implementation Details

**⚠️ This skill uses a template-based approach - DO NOT write code from scratch!**

When implementing this skill, you MUST use the provided `copy-template.sh` script:

1. **Locate the skill directory**:
   - Check `~/.codebuddy/skills/init-cbc-sdk-web/`
   - Or check `.codebuddy/skills/init-cbc-sdk-web/` in current directory

2. **Use the copy script**:
   ```bash
   bash <skill-directory>/copy-template.sh <project-name>
   ```

3. **The script will**:
   - Copy the complete template from `templates/` directory
   - Update package.json with the project name
   - Display next steps for the user

**DO NOT** manually read and write each template file. The script handles everything.

## What this skill does

1. **Creates project directory** with the specified name
2. **Scaffolds complete application** including:
   - Express backend with REST API and SSE server
   - React frontend with TDesign React UI components
   - TypeScript configuration
   - TDesign React + Tailwind CSS styling
   - SQLite database setup
   - Build and development scripts
3. **Provides ready-to-use code** for:
   - Agent SDK integration (query, unstable_v2_createSession, unstable_v2_authenticate)
   - Chat session management with persistence
   - Real-time message streaming via SSE
   - Multi-chat support with SQLite storage
   - Permission control system
   - Custom agent configuration
   - Theme switching (light/dark)

## Project Structure

```
your-project-name/
├── server/                 # Backend code
│   ├── index.ts           # Express + SSE server
│   ├── index.d.ts         # Type definitions
│   └── db.ts              # SQLite database operations
├── src/                    # Frontend code
│   ├── App.tsx            # Main React app
│   ├── components/        # UI components
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── ChatMessages.tsx
│   │   ├── ChatInput.tsx
│   │   ├── ToolCallsCollapse.tsx
│   │   ├── AgentConfigDialog.tsx
│   │   ├── PermissionDialog.tsx
│   │   ├── NewChatDialog.tsx
│   │   ├── NewChatView.tsx
│   │   └── SettingsPage.tsx
│   ├── hooks/             # React hooks
│   │   ├── useChat.ts
│   │   ├── useSessions.ts
│   │   ├── useAgents.ts
│   │   ├── useModels.ts
│   │   └── useTheme.ts
│   ├── pages/             # Page components
│   │   └── ChatPage.tsx
│   ├── utils/             # Utilities
│   │   └── iconMap.ts
│   ├── types.ts           # Type definitions
│   ├── config.ts          # Configuration
│   ├── main.tsx           # Entry point
│   └── index.css          # Global styles
├── data/                   # Data storage
│   └── chat.db            # SQLite database
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── vite.config.ts         # Vite config
├── tailwind.config.js     # Tailwind config
├── index.html             # HTML template
├── README.md              # Documentation
└── DEVELOPMENT.md         # Development guide
```

## Next Steps

After running this skill:

1. **Navigate to project directory**:
   ```bash
   cd your-project-name
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your `CODEBUDDY_API_KEY`

4. **Start development server**:
   ```bash
   npm run dev
   ```
   This starts both backend (port 3001) and frontend (port 5173)

5. **Open in browser**:
   Navigate to `http://localhost:5173`

## Features

- **Multi-chat support**: Create and manage multiple chat conversations with SQLite persistence
- **Real-time streaming**: See AI responses as they're generated via SSE
- **Tool call visualization**: View when the agent uses tools with expandable details
- **Permission control**: Support for multiple permission modes (default, acceptEdits, plan, bypassPermissions)
- **Custom agents**: Create and manage multiple agent configurations
- **Theme switching**: Support for light/dark themes
- **Session persistence**: Chat history and agent sessions stored in SQLite database
- **Modern UI**: Clean, responsive interface with TDesign React components
- **TypeScript**: Full type safety across frontend and backend

## Keywords

chat, web, agent-sdk, react, express, websocket, typescript, vite, tailwind, ai, assistant, conversation, real-time, streaming

## Requirements

- Node.js 18 or higher
- CodeBuddy API key (get from https://www.codebuddy.cn)
- Modern web browser

## Customization

After initialization, you can customize:
- Agent configurations (system prompt, model, permissions) in Settings page or code
- UI components in `src/components/`
- Styling in `src/index.css`, TDesign theme, and Tailwind config
- Server configuration in `server/index.ts`
- Database schema in `server/db.ts`
- Permission modes and tool allowances in agent settings

## Learn More

- **TypeScript SDK Documentation**: https://www.codebuddy.ai/docs/zh/cli/sdk-typescript
- **General SDK Documentation**: https://www.codebuddy.ai/docs/zh/cli/sdk
- Project README.md for detailed setup instructions
- SDK guide in plugin rules for best practices
