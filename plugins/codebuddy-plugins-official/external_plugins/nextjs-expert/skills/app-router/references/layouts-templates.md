# Next.js Layouts and Templates

## Root Layout

Every Next.js app requires a root layout at `app/layout.tsx`:

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'My App',
  description: 'Description of my app',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}
```

**Requirements:**
- Must define `<html>` and `<body>` tags
- Must accept and render `children`
- Server Component (cannot use `'use client'`)

## Nested Layouts

Create layouts for route segments:

```
app/
├── layout.tsx              # Root layout
├── page.tsx                # Home page
└── dashboard/
    ├── layout.tsx          # Dashboard layout
    ├── page.tsx            # /dashboard
    └── settings/
        ├── layout.tsx      # Settings layout
        └── page.tsx        # /dashboard/settings
```

```tsx
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex">
      <aside className="w-64 bg-gray-100 p-4">
        <DashboardNav />
      </aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
```

## Layout Composition

Layouts nest automatically:

```
Root Layout
└── Dashboard Layout
    └── Settings Layout
        └── Page
```

The final output:
```tsx
<RootLayout>
  <DashboardLayout>
    <SettingsLayout>
      <SettingsPage />
    </SettingsLayout>
  </DashboardLayout>
</RootLayout>
```

## Sharing UI Across Routes

### Common Header/Footer

```tsx
// app/layout.tsx
import { Header } from '@/components/header'
import { Footer } from '@/components/footer'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  )
}
```

### Conditional Layouts with Route Groups

```
app/
├── (with-header)/
│   ├── layout.tsx          # Layout with header
│   ├── about/page.tsx
│   └── contact/page.tsx
└── (no-header)/
    ├── layout.tsx          # Layout without header
    └── login/page.tsx
```

## Templates vs Layouts

### Layout Behavior

- Persists across navigations
- Maintains state
- Does not re-render

### Template Behavior

- Creates new instance on navigation
- Re-renders on every navigation
- State is reset

```tsx
// app/dashboard/template.tsx
'use client'

import { useEffect } from 'react'

export default function Template({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Runs on every navigation
    console.log('Template mounted')
    return () => console.log('Template unmounted')
  }, [])

  return <div>{children}</div>
}
```

### When to Use Templates

1. **Page transitions/animations:**
```tsx
// app/template.tsx
'use client'

import { motion } from 'framer-motion'

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      {children}
    </motion.div>
  )
}
```

2. **Analytics on route change:**
```tsx
'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'

export default function Template({ children }) {
  const pathname = usePathname()

  useEffect(() => {
    trackPageView(pathname)
  }, [pathname])

  return <>{children}</>
}
```

## Layout Data Fetching

Layouts can fetch data:

```tsx
// app/dashboard/layout.tsx
import { getUser } from '@/lib/auth'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await getUser()

  return (
    <div>
      <header>
        <span>Welcome, {user.name}</span>
      </header>
      {children}
    </div>
  )
}
```

**Note:** You cannot pass data from layout to page via props. Use:
- Shared fetch with `cache()`
- React Context
- Parallel data fetching

## Shared Fetching Pattern

```tsx
// lib/get-user.ts
import { cache } from 'react'

export const getUser = cache(async () => {
  const response = await fetch('/api/user')
  return response.json()
})

// app/dashboard/layout.tsx
import { getUser } from '@/lib/get-user'

export default async function Layout({ children }) {
  const user = await getUser() // Cached
  return <div><UserNav user={user} />{children}</div>
}

// app/dashboard/page.tsx
import { getUser } from '@/lib/get-user'

export default async function Page() {
  const user = await getUser() // Returns cached result
  return <h1>Hello {user.name}</h1>
}
```

## Multiple Root Layouts

Use route groups for different root layouts:

```
app/
├── (marketing)/
│   ├── layout.tsx          # Marketing root layout
│   ├── page.tsx            # / (home)
│   └── about/page.tsx      # /about
└── (app)/
    ├── layout.tsx          # App root layout
    └── dashboard/page.tsx  # /dashboard
```

```tsx
// app/(marketing)/layout.tsx
export default function MarketingLayout({ children }) {
  return (
    <html lang="en">
      <body className="marketing-theme">{children}</body>
    </html>
  )
}

// app/(app)/layout.tsx
export default function AppLayout({ children }) {
  return (
    <html lang="en">
      <body className="app-theme">{children}</body>
    </html>
  )
}
```

## Layout Metadata

```tsx
// app/dashboard/layout.tsx
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: {
    template: '%s | Dashboard',
    default: 'Dashboard',
  },
}

// app/dashboard/settings/page.tsx
export const metadata = {
  title: 'Settings', // Results in: "Settings | Dashboard"
}
```
