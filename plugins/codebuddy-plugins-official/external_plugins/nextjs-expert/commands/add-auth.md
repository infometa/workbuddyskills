---
description: Add authentication to a Next.js application
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Skill
  - AskUserQuestion
---

# Add Authentication to Next.js App

You are adding authentication to a Next.js application using Auth.js (NextAuth.js v5).

## Workflow

### Step 1: Assess Current State

1. Check if authentication already exists:
   - Look for `auth.ts` or `auth.config.ts`
   - Check for `next-auth` in `package.json`
   - Look for existing middleware

2. Identify database setup:
   - Check for Prisma schema
   - Identify existing User model

### Step 2: Ask About Requirements

Use AskUserQuestion to clarify:
- **Providers**: Which OAuth providers? (GitHub, Google, Email/Password)
- **Session strategy**: JWT or database sessions?
- **Protected routes**: Which routes need protection?
- **Role-based access**: Is RBAC needed?

### Step 3: Install Dependencies

```bash
npm install next-auth@beta @auth/prisma-adapter
```

If using credentials:
```bash
npm install bcryptjs
npm install -D @types/bcryptjs
```

### Step 4: Create Auth Configuration

Apply the `auth-patterns` skill and create:

1. **`auth.ts`** - Main auth configuration with:
   - Provider setup
   - Adapter configuration
   - Session callbacks
   - JWT callbacks

2. **`app/api/auth/[...nextauth]/route.ts`** - Route handler

### Step 5: Add Middleware

Create `middleware.ts` with:
- Route protection logic
- Redirect rules for auth pages
- Public route exceptions

### Step 6: Update Database Schema

If using Prisma, add/update models:
- User
- Account
- Session
- VerificationToken

### Step 7: Create Auth Components

1. **Login form** - Credentials + OAuth buttons
2. **Register form** - If using credentials
3. **User menu** - Session-aware navigation
4. **Session provider** - Client-side wrapper

### Step 8: Environment Variables

Create/update `.env.local`:
```
AUTH_SECRET=generated-secret
AUTH_URL=http://localhost:3000
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

## Implementation Checklist

- [ ] Install next-auth@beta
- [ ] Create auth.ts configuration
- [ ] Create API route handler
- [ ] Add middleware for route protection
- [ ] Update Prisma schema (if using database)
- [ ] Create login/register pages
- [ ] Add SessionProvider to layout
- [ ] Create auth-related components
- [ ] Set up environment variables
- [ ] Test authentication flow

## Files to Create

| File | Purpose |
|------|---------|
| `auth.ts` | Auth configuration |
| `app/api/auth/[...nextauth]/route.ts` | NextAuth route handler |
| `middleware.ts` | Route protection |
| `app/login/page.tsx` | Login page |
| `app/register/page.tsx` | Registration page (if credentials) |
| `components/login-form.tsx` | Login form component |
| `components/oauth-buttons.tsx` | OAuth sign-in buttons |
| `components/user-menu.tsx` | User dropdown menu |
| `app/providers.tsx` | SessionProvider wrapper |
| `types/next-auth.d.ts` | Extended types |
| `lib/auth-helpers.ts` | Auth utility functions |

## Security Considerations

- Use `AUTH_SECRET` from environment
- Set `httpOnly` cookies
- Implement CSRF protection
- Hash passwords with bcrypt (min 12 rounds)
- Validate all inputs
- Rate limit authentication endpoints
