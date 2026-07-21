---
description: Scaffold Next.js components following best practices
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Skill
  - AskUserQuestion
---

# Scaffold Next.js Component

You are scaffolding a Next.js component or page following App Router best practices.

## Workflow

### Step 1: Gather Requirements

Ask the user what they want to scaffold:
- **Page**: A new route with page.tsx
- **Layout**: A shared layout for routes
- **Server Component**: A data-fetching component
- **Client Component**: An interactive component
- **API Route**: A route handler
- **Server Action**: A mutation function
- **Loading/Error**: Loading and error states

### Step 2: Analyze Existing Patterns

Before scaffolding, examine the codebase:

1. Check existing component structure:
   - Look at `app/` directory structure
   - Check `components/` organization
   - Note existing patterns for server vs client

2. Identify conventions:
   - TypeScript patterns used
   - Styling approach (Tailwind, CSS Modules, etc.)
   - Data fetching patterns
   - Error handling patterns

### Step 3: Apply Skills

Based on what the user wants, apply the appropriate skill:

- For pages and routing: Use `app-router` skill
- For component decisions: Use `server-components` skill
- For API routes: Use `route-handlers` skill
- For mutations: Use `server-actions` skill
- For protected routes: Use `auth-patterns` skill

### Step 4: Generate Code

Create the component following:
- Next.js 15 conventions
- Async params/searchParams (Promise-based)
- Proper TypeScript types
- Existing project patterns

### Step 5: Verify

After scaffolding:
1. Ensure imports are correct
2. Check TypeScript types
3. Confirm file placement matches App Router conventions

## Examples

### Scaffold a Page

When user asks: "Create a blog post page"

1. Create `app/blog/[slug]/page.tsx`:
```tsx
interface PageProps {
  params: Promise<{ slug: string }>
}

export default async function BlogPostPage({ params }: PageProps) {
  const { slug } = await params
  // ... fetch and render
}
```

2. Add `loading.tsx` and `error.tsx` if needed

### Scaffold a Client Component

When user asks: "Create a search filter component"

1. Create in `components/` with 'use client'
2. Keep it minimal - only client code that needs state
3. Follow existing naming conventions

### Scaffold an API Route

When user asks: "Create a users API endpoint"

1. Create `app/api/users/route.ts`
2. Include GET, POST as needed
3. Add proper error handling and validation
