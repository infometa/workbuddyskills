# Next.js App Router File Conventions

## Route Segment Files

### page.tsx

The `page.tsx` file makes a route segment publicly accessible:

```tsx
// app/dashboard/page.tsx
export default function DashboardPage() {
  return <h1>Dashboard</h1>
}
```

**Rules:**
- Required to make a route accessible
- Must export a default React component
- Server Component by default
- Can be async for data fetching

### layout.tsx

Shared UI that wraps page and nested layouts:

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div>
      <nav>Dashboard Nav</nav>
      <main>{children}</main>
    </div>
  )
}
```

**Rules:**
- Must accept a `children` prop
- Preserves state across navigations
- Does not re-render when navigating between child routes
- Root layout is required and must include `<html>` and `<body>`

### loading.tsx

Instant loading UI using React Suspense:

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
    </div>
  )
}
```

**Rules:**
- Automatically wraps page in Suspense boundary
- Shows while page content is loading
- Nested loading states are supported

### error.tsx

Error boundary for route segment:

```tsx
// app/dashboard/error.tsx
'use client' // Must be a Client Component

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2>Something went wrong!</h2>
      <p>{error.message}</p>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

**Rules:**
- Must be a Client Component (`'use client'`)
- Receives `error` and `reset` props
- Does not catch errors in root layout (use `global-error.tsx`)

### global-error.tsx

Error boundary for root layout:

```tsx
// app/global-error.tsx
'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  )
}
```

### not-found.tsx

UI for 404 responses:

```tsx
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div>
      <h2>Not Found</h2>
      <p>Could not find requested resource</p>
      <Link href="/">Return Home</Link>
    </div>
  )
}
```

**Triggering:**
```tsx
import { notFound } from 'next/navigation'

export default async function Page({ params }) {
  const { id } = await params
  const post = await getPost(id)

  if (!post) {
    notFound() // Triggers not-found.tsx
  }

  return <Post post={post} />
}
```

### template.tsx

Like layout but re-renders on navigation:

```tsx
// app/dashboard/template.tsx
export default function Template({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>
}
```

**Use cases:**
- Enter/exit animations
- Features that rely on useEffect on each navigation
- Resetting state on navigation

### default.tsx

Fallback for parallel routes:

```tsx
// app/@modal/default.tsx
export default function Default() {
  return null
}
```

## Route Segment Options

### Route Segment Config

```tsx
// app/dashboard/page.tsx

// Force dynamic rendering
export const dynamic = 'force-dynamic'
// Options: 'auto' | 'force-dynamic' | 'error' | 'force-static'

// Set revalidation time
export const revalidate = 3600 // seconds

// Set runtime
export const runtime = 'nodejs' // or 'edge'

// Maximum execution duration
export const maxDuration = 30 // seconds

// Prefer fetching certain data
export const fetchCache = 'auto'
// Options: 'auto' | 'default-cache' | 'only-cache' | 'force-cache' | 'force-no-store' | 'default-no-store' | 'only-no-store'
```

## Folder Naming Conventions

### Dynamic Segments

| Pattern | Example | Matches |
|---------|---------|---------|
| `[folder]` | `[id]` | `/123` |
| `[...folder]` | `[...slug]` | `/a/b/c` |
| `[[...folder]]` | `[[...slug]]` | `/` or `/a/b/c` |

### Route Groups

Organize without affecting URL:

```
app/
├── (marketing)/
│   ├── about/page.tsx     # /about
│   └── contact/page.tsx   # /contact
└── (shop)/
    └── products/page.tsx  # /products
```

### Private Folders

Exclude from routing:

```
app/
├── _components/
│   └── button.tsx         # Not a route
└── dashboard/
    └── page.tsx           # /dashboard
```

### Parallel Routes

Named slots with `@folder`:

```
app/
├── @modal/
│   └── login/page.tsx
├── @sidebar/
│   └── page.tsx
├── layout.tsx
└── page.tsx
```

### Intercepting Routes

| Pattern | Intercepts |
|---------|------------|
| `(.)folder` | Same level |
| `(..)folder` | One level up |
| `(..)(..)folder` | Two levels up |
| `(...)folder` | From root |

## File Hierarchy

Rendering order in a route segment:

1. `layout.tsx`
2. `template.tsx`
3. `error.tsx` (boundary)
4. `loading.tsx` (boundary)
5. `not-found.tsx` (boundary)
6. `page.tsx` or nested `layout.tsx`
