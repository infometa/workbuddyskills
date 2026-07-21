# Next.js Expert Plugin

A comprehensive Claude Code plugin providing Next.js development expertise with skills for App Router, Server Components, Route Handlers, Server Actions, and authentication patterns.

## Features

- **5 Skills** covering core Next.js App Router concepts
- **3 Commands** for common development tasks
- **Progressive disclosure** with references and examples
- **Next.js 15** compatible patterns

## Installation

Add to your Claude Code settings:

```json
{
  "plugins": [
    "https://github.com/davepoon/buildwithclaude/tree/main/plugins/nextjs-expert"
  ]
}
```

## Skills

### app-router

File-based routing, layouts, metadata, and route organization for Next.js App Router.

**Topics covered:**
- File conventions (page.tsx, layout.tsx, loading.tsx, error.tsx)
- Dynamic routes and catch-all segments
- Parallel routes and intercepting routes
- Route groups and organization

### server-components

React Server Components patterns and when to use server vs client components.

**Topics covered:**
- Server vs Client component decision guide
- 'use client' boundaries
- Composition patterns
- Data fetching in server components

### route-handlers

API route handlers in the app directory.

**Topics covered:**
- HTTP method handlers (GET, POST, PUT, PATCH, DELETE)
- Request/response handling
- Streaming responses
- CORS and authentication

### server-actions

Server Actions for form handling and mutations.

**Topics covered:**
- 'use server' directive
- Form handling with useFormState
- Validation with Zod
- Revalidation patterns

### auth-patterns

Authentication patterns for Next.js applications.

**Topics covered:**
- NextAuth.js v5 setup
- Middleware-based route protection
- Session management
- Role-based access control

## Commands

### /nextjs-expert:scaffold

Scaffold Next.js components following best practices.

```
/nextjs-expert:scaffold
```

Scaffolds pages, components, API routes, and more following App Router conventions.

### /nextjs-expert:add-auth

Add authentication to a Next.js application.

```
/nextjs-expert:add-auth
```

Sets up NextAuth.js with providers, middleware, and protected routes.

### /nextjs-expert:optimize

Analyze and optimize Next.js application performance.

```
/nextjs-expert:optimize
```

Reviews component boundaries, data fetching, caching, and provides recommendations.

## Directory Structure

```
nextjs-expert/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── app-router/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── routing-conventions.md
│   │   │   ├── layouts-templates.md
│   │   │   └── loading-error-states.md
│   │   └── examples/
│   │       ├── dynamic-routes.md
│   │       └── parallel-routes.md
│   ├── server-components/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── server-vs-client.md
│   │   │   └── composition-patterns.md
│   │   └── examples/
│   │       └── data-fetching-patterns.md
│   ├── route-handlers/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── http-methods.md
│   │   │   └── streaming-responses.md
│   │   └── examples/
│   │       └── crud-api.md
│   ├── server-actions/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── form-handling.md
│   │   │   └── revalidation.md
│   │   └── examples/
│   │       └── mutation-patterns.md
│   └── auth-patterns/
│       ├── SKILL.md
│       ├── references/
│       │   ├── middleware-auth.md
│       │   └── session-management.md
│       └── examples/
│           └── nextauth-setup.md
├── commands/
│   ├── scaffold.md
│   ├── add-auth.md
│   └── optimize.md
└── README.md
```

## Usage Examples

### Building a new page

Ask Claude:
> "Create a blog post page with dynamic routing"

Claude will use the `app-router` and `server-components` skills to generate:
- `app/blog/[slug]/page.tsx` with proper async params
- Loading and error states
- Metadata generation

### Adding authentication

Ask Claude:
> "Add GitHub and Google authentication to my app"

Or use the command:
> "/nextjs-expert:add-auth"

Claude will use the `auth-patterns` skill to set up:
- NextAuth.js configuration
- Middleware protection
- Login/logout components

### Optimizing performance

Ask Claude:
> "Review my app for performance issues"

Or use the command:
> "/nextjs-expert:optimize"

Claude will analyze:
- Client/server component boundaries
- Data fetching patterns
- Caching strategies
- Bundle size

## Contributing

Contributions welcome! Please follow the existing skill structure and include:
- SKILL.md with frontmatter and core content
- References for detailed documentation
- Examples with working code patterns

## License

MIT
