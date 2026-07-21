# Session Management in Next.js

## Session Strategies

### 1. Stateless JWT Sessions

Store session data in the token itself:

```tsx
// lib/jwt.ts
import { SignJWT, jwtVerify } from 'jose'

const secret = new TextEncoder().encode(process.env.JWT_SECRET)

export interface SessionPayload {
  userId: string
  email: string
  role: string
  expiresAt: Date
}

export async function createSession(payload: Omit<SessionPayload, 'expiresAt'>) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days

  const token = await new SignJWT({ ...payload, expiresAt })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(secret)

  return { token, expiresAt }
}

export async function verifySession(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, secret, {
      algorithms: ['HS256'],
    })
    return payload as SessionPayload
  } catch {
    return null
  }
}
```

### 2. Database Sessions

Store session in database, only ID in cookie:

```tsx
// lib/session.ts
import { cookies } from 'next/headers'
import { nanoid } from 'nanoid'

export async function createSession(userId: string) {
  const sessionId = nanoid(32)
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)

  await db.session.create({
    data: {
      id: sessionId,
      userId,
      expiresAt,
    },
  })

  const cookieStore = await cookies()
  cookieStore.set('session', sessionId, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    expires: expiresAt,
    path: '/',
  })

  return sessionId
}

export async function getSession() {
  const cookieStore = await cookies()
  const sessionId = cookieStore.get('session')?.value

  if (!sessionId) return null

  const session = await db.session.findUnique({
    where: { id: sessionId },
    include: { user: true },
  })

  if (!session || session.expiresAt < new Date()) {
    return null
  }

  return session
}

export async function deleteSession() {
  const cookieStore = await cookies()
  const sessionId = cookieStore.get('session')?.value

  if (sessionId) {
    await db.session.delete({ where: { id: sessionId } })
    cookieStore.delete('session')
  }
}
```

## Cookie Configuration

### Secure Cookie Settings

```tsx
// lib/cookies.ts
import { cookies } from 'next/headers'

export async function setSessionCookie(sessionId: string, maxAge: number) {
  const cookieStore = await cookies()

  cookieStore.set('session', sessionId, {
    httpOnly: true,          // Not accessible via JavaScript
    secure: process.env.NODE_ENV === 'production',  // HTTPS only in prod
    sameSite: 'lax',         // CSRF protection
    maxAge,                   // Expiration in seconds
    path: '/',               // Available on all paths
  })
}

export async function getSessionCookie() {
  const cookieStore = await cookies()
  return cookieStore.get('session')?.value
}

export async function clearSessionCookie() {
  const cookieStore = await cookies()
  cookieStore.delete('session')
}
```

### SameSite Options

```tsx
// 'strict' - Cookie only sent on same-site requests
// 'lax' - Cookie sent on same-site + top-level navigation
// 'none' - Cookie sent on all requests (requires secure: true)

// For OAuth callbacks from external providers:
cookieStore.set('oauth-state', state, {
  httpOnly: true,
  secure: true,
  sameSite: 'none', // Required for cross-site OAuth
  maxAge: 600, // 10 minutes
})
```

## Session Refresh

### Sliding Window Sessions

```tsx
// lib/session.ts
const SESSION_DURATION = 7 * 24 * 60 * 60 * 1000 // 7 days
const REFRESH_THRESHOLD = 24 * 60 * 60 * 1000     // 1 day

export async function getSessionWithRefresh() {
  const cookieStore = await cookies()
  const sessionId = cookieStore.get('session')?.value

  if (!sessionId) return null

  const session = await db.session.findUnique({
    where: { id: sessionId },
    include: { user: true },
  })

  if (!session || session.expiresAt < new Date()) {
    await deleteSession()
    return null
  }

  // Refresh if session expires within threshold
  const timeUntilExpiry = session.expiresAt.getTime() - Date.now()

  if (timeUntilExpiry < REFRESH_THRESHOLD) {
    const newExpiresAt = new Date(Date.now() + SESSION_DURATION)

    await db.session.update({
      where: { id: sessionId },
      data: { expiresAt: newExpiresAt },
    })

    cookieStore.set('session', sessionId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      expires: newExpiresAt,
      path: '/',
    })
  }

  return session
}
```

### Token Rotation

```tsx
// lib/session.ts
export async function rotateSession(oldSessionId: string) {
  const oldSession = await db.session.findUnique({
    where: { id: oldSessionId },
  })

  if (!oldSession) return null

  // Create new session
  const newSessionId = nanoid(32)
  const expiresAt = new Date(Date.now() + SESSION_DURATION)

  await db.$transaction([
    // Create new session
    db.session.create({
      data: {
        id: newSessionId,
        userId: oldSession.userId,
        expiresAt,
      },
    }),
    // Delete old session
    db.session.delete({
      where: { id: oldSessionId },
    }),
  ])

  const cookieStore = await cookies()
  cookieStore.set('session', newSessionId, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    expires: expiresAt,
    path: '/',
  })

  return newSessionId
}
```

## Server-Side Session Access

### In Server Components

```tsx
// app/dashboard/page.tsx
import { getSession } from '@/lib/session'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const session = await getSession()

  if (!session) {
    redirect('/login')
  }

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
      <p>Email: {session.user.email}</p>
    </div>
  )
}
```

### In Server Actions

```tsx
// actions/profile.ts
'use server'

import { getSession } from '@/lib/session'
import { revalidatePath } from 'next/cache'

export async function updateProfile(formData: FormData) {
  const session = await getSession()

  if (!session) {
    throw new Error('Unauthorized')
  }

  await db.user.update({
    where: { id: session.user.id },
    data: {
      name: formData.get('name') as string,
      bio: formData.get('bio') as string,
    },
  })

  revalidatePath('/profile')
}
```

### In Route Handlers

```tsx
// app/api/user/route.ts
import { NextResponse } from 'next/server'
import { getSession } from '@/lib/session'

export async function GET() {
  const session = await getSession()

  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  return NextResponse.json({
    user: {
      id: session.user.id,
      name: session.user.name,
      email: session.user.email,
    },
  })
}
```

## Session Context for Client

```tsx
// lib/auth.tsx
'use client'

import { createContext, useContext, useEffect, useState } from 'react'

interface User {
  id: string
  name: string
  email: string
}

interface SessionContextType {
  user: User | null
  loading: boolean
  refresh: () => Promise<void>
}

const SessionContext = createContext<SessionContextType | null>(null)

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchSession = async () => {
    try {
      const res = await fetch('/api/auth/session')
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSession()
  }, [])

  return (
    <SessionContext.Provider value={{ user, loading, refresh: fetchSession }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used within SessionProvider')
  }
  return context
}
```

## Session Cleanup

### Cleanup Expired Sessions

```tsx
// lib/session.ts
export async function cleanupExpiredSessions() {
  const result = await db.session.deleteMany({
    where: {
      expiresAt: {
        lt: new Date(),
      },
    },
  })

  console.log(`Cleaned up ${result.count} expired sessions`)
  return result.count
}

// Run via cron job or scheduled function
// app/api/cron/cleanup/route.ts
import { NextResponse } from 'next/server'
import { cleanupExpiredSessions } from '@/lib/session'

export async function GET(request: Request) {
  // Verify cron secret
  const authHeader = request.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const count = await cleanupExpiredSessions()
  return NextResponse.json({ cleaned: count })
}
```

### Revoke All Sessions

```tsx
// lib/session.ts
export async function revokeAllSessions(userId: string, exceptCurrent?: string) {
  await db.session.deleteMany({
    where: {
      userId,
      ...(exceptCurrent && { id: { not: exceptCurrent } }),
    },
  })
}

// actions/security.ts
'use server'

import { getSession, revokeAllSessions } from '@/lib/session'

export async function logoutAllDevices() {
  const session = await getSession()

  if (!session) {
    throw new Error('Unauthorized')
  }

  // Keep current session, revoke all others
  await revokeAllSessions(session.user.id, session.id)

  return { success: true }
}
```

## Multi-Device Session Management

```tsx
// app/settings/sessions/page.tsx
import { getSession } from '@/lib/session'

export default async function SessionsPage() {
  const currentSession = await getSession()

  const allSessions = await db.session.findMany({
    where: { userId: currentSession?.user.id },
    orderBy: { createdAt: 'desc' },
  })

  return (
    <div>
      <h1>Active Sessions</h1>
      <ul>
        {allSessions.map((session) => (
          <li key={session.id}>
            <p>Created: {session.createdAt.toLocaleDateString()}</p>
            <p>Expires: {session.expiresAt.toLocaleDateString()}</p>
            {session.id === currentSession?.id ? (
              <span className="text-green-600">Current session</span>
            ) : (
              <form action={revokeSession.bind(null, session.id)}>
                <button type="submit">Revoke</button>
              </form>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
```
