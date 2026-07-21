# Usage Examples

This document provides practical examples for using the CodeBuddy Chat Web plugin.

## Basic Usage

### Example 1: Create a Simple Chat App

```bash
/init-cbc-sdk-web my-first-chat
cd my-first-chat
npm install
cp .env.example .env
# Edit .env and add your CODEBUDDY_API_KEY
npm run dev
```

Open `http://localhost:5173` and start chatting!

## Customization Examples

### Example 2: Custom System Prompt

Edit `server/agent.ts` to customize the AI assistant's behavior:

```typescript
const SYSTEM_PROMPT = `You are a coding assistant specialized in JavaScript and TypeScript.
Focus on providing clear, concise code examples with explanations.`;
```

### Example 3: Change Server Ports

Edit `server/config.ts`:

```typescript
export const config = {
  server: {
    port: 4000,  // Changed from 3001
    wsPath: "/ws"
  }
};
```

Also update `client/App.tsx`:

```typescript
const WS_URL = `ws://${window.location.hostname}:4000/ws`;
```

### Example 4: Customize UI Theme

Edit `client/globals.css` to change colors:

```css
:root {
  --primary: #3b82f6;
  --secondary: #8b5cf6;
  --background: #ffffff;
  --foreground: #1f2937;
}
```

### Example 5: Limit Agent Tools

Edit `server/agent.ts` to restrict tool access:

```typescript
allowedTools: ["Read", "Grep", "WebSearch"],  // Only allow these tools
```

## Common Use Cases

### Use Case 1: Customer Support Bot

Create a chat app for customer support:

1. Initialize project: `/init-cbc-sdk-web support-bot`
2. Customize system prompt for support scenarios
3. Add company-specific knowledge to the prompt
4. Deploy to your infrastructure

### Use Case 2: Code Review Assistant

Build a chat app for code reviews:

1. Initialize: `/init-cbc-sdk-web code-reviewer`
2. Set system prompt to focus on code quality
3. Configure allowed tools for code analysis
4. Integrate with your development workflow

### Use Case 3: Learning Platform

Create an educational chat interface:

1. Initialize: `/init-cbc-sdk-web learning-assistant`
2. Customize UI for educational content
3. Add progress tracking features
4. Deploy for students

## Integration Patterns

### Pattern 1: Add Authentication

Integrate user authentication:

```typescript
// In server/server.ts
import jwt from 'jsonwebtoken';

app.use((req, res, next) => {
  const token = req.headers.authorization;
  // Verify token
  next();
});
```

### Pattern 2: Database Integration

Replace in-memory storage with database:

```typescript
// In server/store.ts
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const chatStore = {
  async createChat(title?: string) {
    return await prisma.chat.create({ data: { title } });
  }
};
```

### Pattern 3: Rate Limiting

Add rate limiting for API protection:

```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});

app.use('/api/', limiter);
```

## Tips

- Start with the default configuration and customize incrementally
- Test changes locally before deploying
- Monitor API usage and costs
- Implement proper error handling for production
- Use environment variables for sensitive configuration
