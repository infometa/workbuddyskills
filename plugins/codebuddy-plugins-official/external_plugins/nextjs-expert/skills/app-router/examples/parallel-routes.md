# Parallel Routes and Intercepting Routes

## Parallel Routes Basics

Parallel routes allow rendering multiple pages in the same layout simultaneously using named slots.

### Slot Convention

Slots are defined with `@folder` naming:

```
app/
├── @dashboard/
│   └── page.tsx
├── @analytics/
│   └── page.tsx
├── layout.tsx
└── page.tsx
```

### Layout with Slots

```tsx
// app/layout.tsx
export default function Layout({
  children,
  dashboard,
  analytics,
}: {
  children: React.ReactNode
  dashboard: React.ReactNode
  analytics: React.ReactNode
}) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <main className="col-span-2">{children}</main>
      <aside className="space-y-4">
        {dashboard}
        {analytics}
      </aside>
    </div>
  )
}
```

## Dashboard Layout Example

```
app/
├── @team/
│   ├── page.tsx
│   └── loading.tsx
├── @notifications/
│   ├── page.tsx
│   └── loading.tsx
├── @metrics/
│   └── page.tsx
├── layout.tsx
└── page.tsx
```

```tsx
// app/layout.tsx
export default function DashboardLayout({
  children,
  team,
  notifications,
  metrics,
}: {
  children: React.ReactNode
  team: React.ReactNode
  notifications: React.ReactNode
  metrics: React.ReactNode
}) {
  return (
    <div className="min-h-screen">
      <header className="h-16 border-b">
        <h1>Dashboard</h1>
      </header>

      <div className="grid grid-cols-4 gap-4 p-4">
        <main className="col-span-3">{children}</main>
        <aside className="space-y-4">
          {team}
          {notifications}
          {metrics}
        </aside>
      </div>
    </div>
  )
}

// app/@team/page.tsx
export default async function TeamSlot() {
  const team = await getTeamMembers()
  return (
    <div className="bg-white p-4 rounded shadow">
      <h2>Team</h2>
      <ul>
        {team.map(member => (
          <li key={member.id}>{member.name}</li>
        ))}
      </ul>
    </div>
  )
}
```

## Default Fallback

When navigating to a route without a matching slot, use `default.tsx`:

```tsx
// app/@notifications/default.tsx
export default function NotificationsDefault() {
  return null // or a placeholder
}
```

## Conditional Slots

```tsx
// app/layout.tsx
import { auth } from '@/auth'

export default async function Layout({
  children,
  admin,
  user,
}: {
  children: React.ReactNode
  admin: React.ReactNode
  user: React.ReactNode
}) {
  const session = await auth()

  return (
    <div>
      {session?.user?.role === 'admin' ? admin : user}
      {children}
    </div>
  )
}
```

## Intercepting Routes

Intercept a route to show it in the current layout (e.g., modals).

### Convention

| Pattern | Intercepts |
|---------|------------|
| `(.)folder` | Same level |
| `(..)folder` | One level up |
| `(..)(..)folder` | Two levels up |
| `(...)folder` | From root |

### Modal Example

```
app/
├── @modal/
│   ├── (.)photo/
│   │   └── [id]/
│   │       └── page.tsx    # Intercepted route (modal)
│   └── default.tsx
├── photo/
│   └── [id]/
│       └── page.tsx        # Full page route
├── layout.tsx
└── page.tsx
```

```tsx
// app/layout.tsx
export default function Layout({
  children,
  modal,
}: {
  children: React.ReactNode
  modal: React.ReactNode
}) {
  return (
    <>
      {children}
      {modal}
    </>
  )
}

// app/@modal/default.tsx
export default function Default() {
  return null
}

// app/@modal/(.)photo/[id]/page.tsx (Modal version)
import { Modal } from '@/components/modal'

export default async function PhotoModal({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const photo = await getPhoto(id)

  return (
    <Modal>
      <img src={photo.url} alt={photo.title} />
    </Modal>
  )
}

// app/photo/[id]/page.tsx (Full page version)
export default async function PhotoPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const photo = await getPhoto(id)

  return (
    <div className="container mx-auto">
      <img src={photo.url} alt={photo.title} />
      <h1>{photo.title}</h1>
    </div>
  )
}
```

### Modal Component

```tsx
// components/modal.tsx
'use client'

import { useRouter } from 'next/navigation'
import { useCallback, useEffect } from 'react'

export function Modal({ children }: { children: React.ReactNode }) {
  const router = useRouter()

  const onDismiss = useCallback(() => {
    router.back()
  }, [router])

  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss()
    },
    [onDismiss]
  )

  useEffect(() => {
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onKeyDown])

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center"
      onClick={onDismiss}
    >
      <div
        className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
        <button
          onClick={onDismiss}
          className="absolute top-4 right-4"
        >
          Close
        </button>
      </div>
    </div>
  )
}
```

### Gallery with Modal

```tsx
// app/page.tsx (Gallery)
import Link from 'next/link'

export default async function GalleryPage() {
  const photos = await getPhotos()

  return (
    <div className="grid grid-cols-4 gap-4">
      {photos.map((photo) => (
        <Link key={photo.id} href={`/photo/${photo.id}`}>
          <img
            src={photo.thumbnail}
            alt={photo.title}
            className="rounded cursor-pointer hover:opacity-80"
          />
        </Link>
      ))}
    </div>
  )
}
```

## Login Modal Pattern

```
app/
├── @auth/
│   ├── (.)login/
│   │   └── page.tsx        # Login modal
│   └── default.tsx
├── login/
│   └── page.tsx            # Full login page
└── layout.tsx
```

```tsx
// app/@auth/(.)login/page.tsx
import { Modal } from '@/components/modal'
import { LoginForm } from '@/components/login-form'

export default function LoginModal() {
  return (
    <Modal>
      <h1 className="text-2xl font-bold mb-4">Sign In</h1>
      <LoginForm />
    </Modal>
  )
}

// app/login/page.tsx
import { LoginForm } from '@/components/login-form'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">Sign In</h1>
        <LoginForm />
      </div>
    </div>
  )
}
```

## Tab Navigation with Parallel Routes

```
app/dashboard/
├── @tabs/
│   ├── overview/
│   │   └── page.tsx
│   ├── analytics/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
├── layout.tsx
└── page.tsx
```

```tsx
// app/dashboard/layout.tsx
import Link from 'next/link'

export default function DashboardLayout({
  children,
  tabs,
}: {
  children: React.ReactNode
  tabs: React.ReactNode
}) {
  return (
    <div>
      <nav className="flex gap-4 border-b pb-4">
        <Link href="/dashboard/overview">Overview</Link>
        <Link href="/dashboard/analytics">Analytics</Link>
        <Link href="/dashboard/settings">Settings</Link>
      </nav>
      <div className="mt-4">
        {tabs}
      </div>
    </div>
  )
}
```
