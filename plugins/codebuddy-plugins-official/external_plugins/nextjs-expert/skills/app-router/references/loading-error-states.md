# Loading and Error States in Next.js

## Loading UI with loading.tsx

### Basic Loading State

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return <div>Loading...</div>
}
```

### Skeleton Loading

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-1/4 mb-4" />
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded w-full" />
        <div className="h-4 bg-gray-200 rounded w-5/6" />
        <div className="h-4 bg-gray-200 rounded w-4/6" />
      </div>
    </div>
  )
}
```

### How loading.tsx Works

Next.js automatically wraps `page.tsx` in a Suspense boundary:

```tsx
// What Next.js creates internally
<Suspense fallback={<Loading />}>
  <Page />
</Suspense>
```

## Manual Suspense Boundaries

### Streaming Components

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react'
import { SlowComponent } from './slow-component'
import { FastComponent } from './fast-component'

export default function DashboardPage() {
  return (
    <div>
      <FastComponent /> {/* Renders immediately */}

      <Suspense fallback={<p>Loading analytics...</p>}>
        <SlowAnalytics /> {/* Streams when ready */}
      </Suspense>

      <Suspense fallback={<p>Loading feed...</p>}>
        <SlowFeed /> {/* Streams when ready */}
      </Suspense>
    </div>
  )
}
```

### Nested Suspense

```tsx
export default function Page() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Header />
      <main>
        <Suspense fallback={<SidebarSkeleton />}>
          <Sidebar />
        </Suspense>
        <Suspense fallback={<ContentSkeleton />}>
          <Content />
        </Suspense>
      </main>
    </Suspense>
  )
}
```

## Error Handling with error.tsx

### Basic Error Boundary

```tsx
// app/dashboard/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded">
      <h2 className="text-red-800 font-bold">Something went wrong!</h2>
      <p className="text-red-600">{error.message}</p>
      <button
        onClick={() => reset()}
        className="mt-2 px-4 py-2 bg-red-600 text-white rounded"
      >
        Try again
      </button>
    </div>
  )
}
```

### Error Boundary Scope

Error boundaries catch errors in:
- Child components
- The `page.tsx` in the same segment
- Nested routes

```
app/
├── layout.tsx          # ❌ Errors here not caught
├── error.tsx           # ✅ Catches errors below
├── page.tsx            # ✅ Errors caught by error.tsx
└── dashboard/
    ├── layout.tsx      # ✅ Errors caught by parent error.tsx
    ├── error.tsx       # ✅ Catches dashboard errors
    └── page.tsx        # ✅ Errors caught by dashboard/error.tsx
```

### Global Error Handler

For errors in root layout:

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

### Error Logging

```tsx
// app/error.tsx
'use client'

import { useEffect } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log to error reporting service
    console.error(error)
    reportError(error)
  }, [error])

  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

## Not Found Handling

### not-found.tsx

```tsx
// app/not-found.tsx
import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2 className="text-2xl font-bold">404 - Page Not Found</h2>
      <p className="text-gray-600 mt-2">
        The page you're looking for doesn't exist.
      </p>
      <Link
        href="/"
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Return Home
      </Link>
    </div>
  )
}
```

### Triggering Not Found

```tsx
// app/posts/[slug]/page.tsx
import { notFound } from 'next/navigation'

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const post = await getPost(slug)

  if (!post) {
    notFound() // Renders not-found.tsx
  }

  return <article>{post.content}</article>
}
```

### Nested Not Found

```tsx
// app/dashboard/not-found.tsx
export default function DashboardNotFound() {
  return (
    <div>
      <h2>Dashboard resource not found</h2>
      <p>The requested dashboard item doesn't exist.</p>
    </div>
  )
}
```

## Combined Patterns

### Loading + Error + Not Found

```
app/dashboard/
├── layout.tsx
├── loading.tsx       # Shows while page loads
├── error.tsx         # Shows on errors
├── not-found.tsx     # Shows for 404s
└── page.tsx
```

### Progressive Loading

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react'

export default function DashboardPage() {
  return (
    <div>
      {/* Critical content loads first */}
      <h1>Dashboard</h1>

      {/* Stats stream in */}
      <Suspense fallback={<StatsSkeleton />}>
        <Stats />
      </Suspense>

      {/* Chart streams separately */}
      <Suspense fallback={<ChartSkeleton />}>
        <Chart />
      </Suspense>

      {/* Recent activity last */}
      <Suspense fallback={<ActivitySkeleton />}>
        <RecentActivity />
      </Suspense>
    </div>
  )
}
```

### Error Recovery with State

```tsx
// app/error.tsx
'use client'

import { useState } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  const [isRetrying, setIsRetrying] = useState(false)

  const handleRetry = async () => {
    setIsRetrying(true)
    // Optional: wait before retry
    await new Promise(resolve => setTimeout(resolve, 1000))
    reset()
  }

  return (
    <div>
      <h2>Error: {error.message}</h2>
      <button onClick={handleRetry} disabled={isRetrying}>
        {isRetrying ? 'Retrying...' : 'Try again'}
      </button>
    </div>
  )
}
```
