# HTTP Methods in Route Handlers

## Supported Methods

Export async functions with HTTP method names:

```tsx
// app/api/posts/route.ts
export async function GET(request: Request) {}
export async function POST(request: Request) {}
export async function PUT(request: Request) {}
export async function PATCH(request: Request) {}
export async function DELETE(request: Request) {}
export async function HEAD(request: Request) {}
export async function OPTIONS(request: Request) {}
```

## GET Requests

### Basic GET

```tsx
// app/api/posts/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  const posts = await db.post.findMany()
  return NextResponse.json(posts)
}
```

### GET with Query Parameters

```tsx
// app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const query = searchParams.get('q')
  const page = parseInt(searchParams.get('page') || '1')
  const limit = parseInt(searchParams.get('limit') || '10')

  const results = await db.post.findMany({
    where: {
      OR: [
        { title: { contains: query || '' } },
        { content: { contains: query || '' } },
      ],
    },
    skip: (page - 1) * limit,
    take: limit,
  })

  return NextResponse.json({
    results,
    page,
    limit,
    query,
  })
}
```

### GET with Dynamic Segment

```tsx
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  const post = await db.post.findUnique({
    where: { id },
  })

  if (!post) {
    return NextResponse.json(
      { error: 'Post not found' },
      { status: 404 }
    )
  }

  return NextResponse.json(post)
}
```

## POST Requests

### JSON Body

```tsx
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const body = await request.json()

  const post = await db.post.create({
    data: {
      title: body.title,
      content: body.content,
      authorId: body.authorId,
    },
  })

  return NextResponse.json(post, { status: 201 })
}
```

### Form Data

```tsx
// app/api/upload/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const formData = await request.formData()
  const name = formData.get('name') as string
  const email = formData.get('email') as string

  // Process form data
  const user = await db.user.create({
    data: { name, email },
  })

  return NextResponse.json(user, { status: 201 })
}
```

### File Upload

```tsx
// app/api/upload/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { writeFile } from 'fs/promises'
import path from 'path'

export async function POST(request: NextRequest) {
  const formData = await request.formData()
  const file = formData.get('file') as File

  if (!file) {
    return NextResponse.json(
      { error: 'No file provided' },
      { status: 400 }
    )
  }

  const bytes = await file.arrayBuffer()
  const buffer = Buffer.from(bytes)

  const filename = `${Date.now()}-${file.name}`
  const filepath = path.join(process.cwd(), 'public/uploads', filename)

  await writeFile(filepath, buffer)

  return NextResponse.json({
    url: `/uploads/${filename}`,
  })
}
```

## PUT Requests

Full resource replacement:

```tsx
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const body = await request.json()

  const post = await db.post.update({
    where: { id },
    data: {
      title: body.title,
      content: body.content,
      published: body.published,
    },
  })

  return NextResponse.json(post)
}
```

## PATCH Requests

Partial update:

```tsx
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const body = await request.json()

  // Only update provided fields
  const post = await db.post.update({
    where: { id },
    data: body,
  })

  return NextResponse.json(post)
}
```

## DELETE Requests

```tsx
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  await db.post.delete({
    where: { id },
  })

  return new NextResponse(null, { status: 204 })
}
```

## Request Headers

```tsx
// app/api/protected/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  // Get specific header
  const authHeader = request.headers.get('authorization')

  // Get all headers
  const contentType = request.headers.get('content-type')
  const userAgent = request.headers.get('user-agent')

  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    )
  }

  const token = authHeader.split(' ')[1]
  // Validate token...

  return NextResponse.json({ message: 'Authenticated' })
}
```

## Response Headers

```tsx
// app/api/data/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  const data = { message: 'Hello' }

  return NextResponse.json(data, {
    status: 200,
    headers: {
      'Cache-Control': 'max-age=3600, s-maxage=3600',
      'X-Custom-Header': 'custom-value',
    },
  })
}
```

## Cookies

### Reading Cookies

```tsx
// app/api/user/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function GET(request: NextRequest) {
  // Method 1: From request
  const token = request.cookies.get('token')?.value

  // Method 2: Using cookies() function
  const cookieStore = await cookies()
  const sessionId = cookieStore.get('sessionId')?.value

  return NextResponse.json({ token, sessionId })
}
```

### Setting Cookies

```tsx
// app/api/login/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const token = await authenticate(body.email, body.password)

  const response = NextResponse.json({ success: true })

  response.cookies.set('token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 60 * 60 * 24 * 7, // 1 week
    path: '/',
  })

  return response
}
```

### Deleting Cookies

```tsx
// app/api/logout/route.ts
import { NextResponse } from 'next/server'

export async function POST() {
  const response = NextResponse.json({ success: true })

  response.cookies.delete('token')

  // Or set with expired date
  response.cookies.set('token', '', {
    expires: new Date(0),
  })

  return response
}
```

## URL Handling

```tsx
// app/api/info/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { pathname, searchParams, origin } = request.nextUrl

  return NextResponse.json({
    pathname,      // /api/info
    origin,        // http://localhost:3000
    query: Object.fromEntries(searchParams),
  })
}
```

## Redirects

```tsx
// app/api/old-endpoint/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { redirect } from 'next/navigation'

export async function GET(request: NextRequest) {
  // Method 1: Using redirect()
  redirect('/api/new-endpoint')

  // Method 2: Using NextResponse.redirect()
  return NextResponse.redirect(new URL('/api/new-endpoint', request.url))

  // Method 3: Redirect with status
  return NextResponse.redirect(
    new URL('/api/new-endpoint', request.url),
    { status: 301 } // Permanent redirect
  )
}
```
