# Middleware-Based Authentication

## Basic Middleware Setup

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*', '/api/protected/:path*'],
}
```

## Route Protection Patterns

### Public vs Protected Routes

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const publicRoutes = ['/', '/login', '/register', '/about', '/pricing']
const authRoutes = ['/login', '/register']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('session')?.value

  // Check if route is public
  const isPublicRoute = publicRoutes.some(
    route => pathname === route || pathname.startsWith(`${route}/`)
  )

  // Check if route is auth (login/register)
  const isAuthRoute = authRoutes.includes(pathname)

  // Redirect authenticated users away from auth routes
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // Redirect unauthenticated users to login
  if (!isPublicRoute && !token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('callbackUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|public).*)'],
}
```

### Role-Based Access Control

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify } from 'jose'

const roleRoutes = {
  admin: ['/admin/:path*'],
  editor: ['/editor/:path*', '/posts/edit/:path*'],
  user: ['/dashboard/:path*', '/settings/:path*'],
}

async function getTokenData(token: string) {
  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET)
    const { payload } = await jwtVerify(token, secret)
    return payload as { userId: string; role: string }
  } catch {
    return null
  }
}

function matchesRoute(pathname: string, patterns: string[]) {
  return patterns.some(pattern => {
    const regex = new RegExp(
      '^' + pattern.replace(':path*', '.*') + '$'
    )
    return regex.test(pathname)
  })
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const userData = await getTokenData(token)

  if (!userData) {
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('token')
    return response
  }

  // Check admin routes
  if (matchesRoute(pathname, roleRoutes.admin)) {
    if (userData.role !== 'admin') {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }
  }

  // Check editor routes
  if (matchesRoute(pathname, roleRoutes.editor)) {
    if (!['admin', 'editor'].includes(userData.role)) {
      return NextResponse.redirect(new URL('/unauthorized', request.url))
    }
  }

  return NextResponse.next()
}
```

## JWT Token Verification

### With jose Library

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify, JWTPayload } from 'jose'

interface TokenPayload extends JWTPayload {
  userId: string
  email: string
  role: string
}

async function verifyToken(token: string): Promise<TokenPayload | null> {
  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET)
    const { payload } = await jwtVerify(token, secret, {
      algorithms: ['HS256'],
    })
    return payload as TokenPayload
  } catch (error) {
    console.error('Token verification failed:', error)
    return null
  }
}

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const payload = await verifyToken(token)

  if (!payload) {
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('auth-token')
    return response
  }

  // Add user info to headers for downstream use
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-user-id', payload.userId)
  requestHeaders.set('x-user-role', payload.role)

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  })
}
```

## Session Refresh

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const sessionToken = request.cookies.get('session')?.value

  if (!sessionToken) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Verify and potentially refresh session
  try {
    const response = await fetch(
      `${request.nextUrl.origin}/api/auth/verify`,
      {
        headers: {
          cookie: `session=${sessionToken}`,
        },
      }
    )

    if (!response.ok) {
      const loginResponse = NextResponse.redirect(
        new URL('/login', request.url)
      )
      loginResponse.cookies.delete('session')
      return loginResponse
    }

    const data = await response.json()

    // If session was refreshed, update the cookie
    if (data.newToken) {
      const nextResponse = NextResponse.next()
      nextResponse.cookies.set('session', data.newToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7, // 7 days
      })
      return nextResponse
    }

    return NextResponse.next()
  } catch (error) {
    console.error('Session verification error:', error)
    return NextResponse.redirect(new URL('/login', request.url))
  }
}
```

## API Route Protection

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // API route protection
  if (pathname.startsWith('/api/')) {
    // Skip public API routes
    if (
      pathname.startsWith('/api/auth/') ||
      pathname.startsWith('/api/public/')
    ) {
      return NextResponse.next()
    }

    // Check for API key or Bearer token
    const authHeader = request.headers.get('authorization')

    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Missing authentication' },
        { status: 401 }
      )
    }

    const token = authHeader.split(' ')[1]

    try {
      const isValid = await verifyApiToken(token)

      if (!isValid) {
        return NextResponse.json(
          { error: 'Invalid token' },
          { status: 401 }
        )
      }
    } catch (error) {
      return NextResponse.json(
        { error: 'Authentication failed' },
        { status: 401 }
      )
    }
  }

  return NextResponse.next()
}
```

## Rate Limiting in Middleware

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '1 m'),
  analytics: true,
})

export async function middleware(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const ip = request.headers.get('x-forwarded-for') ?? '127.0.0.1'
    const { success, limit, reset, remaining } = await ratelimit.limit(ip)

    if (!success) {
      return NextResponse.json(
        { error: 'Too many requests' },
        {
          status: 429,
          headers: {
            'X-RateLimit-Limit': limit.toString(),
            'X-RateLimit-Remaining': remaining.toString(),
            'X-RateLimit-Reset': reset.toString(),
          },
        }
      )
    }
  }

  return NextResponse.next()
}
```

## Matcher Configuration

### Precise Matching

```tsx
export const config = {
  matcher: [
    // Match all paths except static files
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}
```

### Multiple Matchers

```tsx
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/api/:path*',
    '/settings/:path*',
  ],
}
```

### Regex Patterns

```tsx
export const config = {
  matcher: [
    // Match paths starting with /api but not /api/public
    '/api/((?!public).*)',
    // Match all dashboard routes
    '/dashboard/(.*)',
  ],
}
```

## Conditional Middleware

```tsx
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Different logic for different paths
  if (pathname.startsWith('/api/')) {
    return handleApiAuth(request)
  }

  if (pathname.startsWith('/admin')) {
    return handleAdminAuth(request)
  }

  if (pathname.startsWith('/dashboard')) {
    return handleUserAuth(request)
  }

  return NextResponse.next()
}

function handleApiAuth(request: NextRequest) {
  const apiKey = request.headers.get('x-api-key')
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return NextResponse.json({ error: 'Invalid API key' }, { status: 401 })
  }
  return NextResponse.next()
}

function handleAdminAuth(request: NextRequest) {
  const token = request.cookies.get('admin-token')?.value
  if (!token) {
    return NextResponse.redirect(new URL('/admin/login', request.url))
  }
  return NextResponse.next()
}

function handleUserAuth(request: NextRequest) {
  const session = request.cookies.get('session')?.value
  if (!session) {
    return NextResponse.redirect(new URL('/login', request.url))
  }
  return NextResponse.next()
}
```

## Headers and Cookies

```tsx
// middleware.ts
export function middleware(request: NextRequest) {
  const response = NextResponse.next()

  // Add security headers
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')

  // Set CORS headers for API routes
  if (request.nextUrl.pathname.startsWith('/api/')) {
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set(
      'Access-Control-Allow-Methods',
      'GET, POST, PUT, DELETE, OPTIONS'
    )
  }

  return response
}
```
