# Complete CRUD API Example

## File Structure

```
app/
├── api/
│   └── posts/
│       ├── route.ts           # GET all, POST new
│       └── [id]/
│           └── route.ts       # GET one, PUT, PATCH, DELETE
├── lib/
│   ├── db.ts                  # Database client
│   └── validations.ts         # Zod schemas
└── types/
    └── post.ts                # Type definitions
```

## Types

```tsx
// types/post.ts
export interface Post {
  id: string
  title: string
  content: string
  published: boolean
  authorId: string
  createdAt: Date
  updatedAt: Date
}

export interface CreatePostInput {
  title: string
  content: string
  authorId: string
  published?: boolean
}

export interface UpdatePostInput {
  title?: string
  content?: string
  published?: boolean
}
```

## Validations

```tsx
// lib/validations.ts
import { z } from 'zod'

export const createPostSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  content: z.string().min(1, 'Content is required'),
  authorId: z.string().uuid('Invalid author ID'),
  published: z.boolean().optional().default(false),
})

export const updatePostSchema = z.object({
  title: z.string().min(1).max(200).optional(),
  content: z.string().min(1).optional(),
  published: z.boolean().optional(),
})

export const paginationSchema = z.object({
  page: z.coerce.number().int().positive().optional().default(1),
  limit: z.coerce.number().int().positive().max(100).optional().default(10),
  sort: z.enum(['newest', 'oldest', 'title']).optional().default('newest'),
})

export type CreatePostInput = z.infer<typeof createPostSchema>
export type UpdatePostInput = z.infer<typeof updatePostSchema>
```

## Database Client

```tsx
// lib/db.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma
}
```

## Collection Route (GET all, POST)

```tsx
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import {
  createPostSchema,
  paginationSchema,
} from '@/lib/validations'

// GET /api/posts
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams

    // Parse and validate query parameters
    const params = paginationSchema.safeParse({
      page: searchParams.get('page'),
      limit: searchParams.get('limit'),
      sort: searchParams.get('sort'),
    })

    if (!params.success) {
      return NextResponse.json(
        { error: 'Invalid parameters', details: params.error.flatten() },
        { status: 400 }
      )
    }

    const { page, limit, sort } = params.data
    const skip = (page - 1) * limit

    // Determine sort order
    const orderBy = {
      newest: { createdAt: 'desc' as const },
      oldest: { createdAt: 'asc' as const },
      title: { title: 'asc' as const },
    }[sort]

    // Fetch posts and total count in parallel
    const [posts, total] = await Promise.all([
      prisma.post.findMany({
        skip,
        take: limit,
        orderBy,
        include: {
          author: {
            select: { id: true, name: true },
          },
        },
      }),
      prisma.post.count(),
    ])

    return NextResponse.json({
      data: posts,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
        hasMore: skip + posts.length < total,
      },
    })
  } catch (error) {
    console.error('GET /api/posts error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch posts' },
      { status: 500 }
    )
  }
}

// POST /api/posts
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate request body
    const validatedData = createPostSchema.safeParse(body)

    if (!validatedData.success) {
      return NextResponse.json(
        {
          error: 'Validation failed',
          details: validatedData.error.flatten(),
        },
        { status: 400 }
      )
    }

    // Verify author exists
    const author = await prisma.user.findUnique({
      where: { id: validatedData.data.authorId },
    })

    if (!author) {
      return NextResponse.json(
        { error: 'Author not found' },
        { status: 404 }
      )
    }

    // Create post
    const post = await prisma.post.create({
      data: validatedData.data,
      include: {
        author: {
          select: { id: true, name: true },
        },
      },
    })

    return NextResponse.json(post, { status: 201 })
  } catch (error) {
    console.error('POST /api/posts error:', error)
    return NextResponse.json(
      { error: 'Failed to create post' },
      { status: 500 }
    )
  }
}
```

## Single Resource Route (GET one, PUT, PATCH, DELETE)

```tsx
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { updatePostSchema } from '@/lib/validations'

type Params = { params: Promise<{ id: string }> }

// GET /api/posts/[id]
export async function GET(request: NextRequest, { params }: Params) {
  try {
    const { id } = await params

    const post = await prisma.post.findUnique({
      where: { id },
      include: {
        author: {
          select: { id: true, name: true, email: true },
        },
      },
    })

    if (!post) {
      return NextResponse.json(
        { error: 'Post not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(post)
  } catch (error) {
    console.error('GET /api/posts/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch post' },
      { status: 500 }
    )
  }
}

// PUT /api/posts/[id] - Full replacement
export async function PUT(request: NextRequest, { params }: Params) {
  try {
    const { id } = await params
    const body = await request.json()

    // For PUT, all fields are required
    const fullUpdateSchema = updatePostSchema.required()
    const validatedData = fullUpdateSchema.safeParse(body)

    if (!validatedData.success) {
      return NextResponse.json(
        {
          error: 'Validation failed',
          details: validatedData.error.flatten(),
        },
        { status: 400 }
      )
    }

    // Check if post exists
    const existing = await prisma.post.findUnique({ where: { id } })

    if (!existing) {
      return NextResponse.json(
        { error: 'Post not found' },
        { status: 404 }
      )
    }

    const post = await prisma.post.update({
      where: { id },
      data: {
        ...validatedData.data,
        updatedAt: new Date(),
      },
      include: {
        author: {
          select: { id: true, name: true },
        },
      },
    })

    return NextResponse.json(post)
  } catch (error) {
    console.error('PUT /api/posts/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to update post' },
      { status: 500 }
    )
  }
}

// PATCH /api/posts/[id] - Partial update
export async function PATCH(request: NextRequest, { params }: Params) {
  try {
    const { id } = await params
    const body = await request.json()

    const validatedData = updatePostSchema.safeParse(body)

    if (!validatedData.success) {
      return NextResponse.json(
        {
          error: 'Validation failed',
          details: validatedData.error.flatten(),
        },
        { status: 400 }
      )
    }

    // Check if there's anything to update
    if (Object.keys(validatedData.data).length === 0) {
      return NextResponse.json(
        { error: 'No fields to update' },
        { status: 400 }
      )
    }

    // Check if post exists
    const existing = await prisma.post.findUnique({ where: { id } })

    if (!existing) {
      return NextResponse.json(
        { error: 'Post not found' },
        { status: 404 }
      )
    }

    const post = await prisma.post.update({
      where: { id },
      data: {
        ...validatedData.data,
        updatedAt: new Date(),
      },
      include: {
        author: {
          select: { id: true, name: true },
        },
      },
    })

    return NextResponse.json(post)
  } catch (error) {
    console.error('PATCH /api/posts/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to update post' },
      { status: 500 }
    )
  }
}

// DELETE /api/posts/[id]
export async function DELETE(request: NextRequest, { params }: Params) {
  try {
    const { id } = await params

    // Check if post exists
    const existing = await prisma.post.findUnique({ where: { id } })

    if (!existing) {
      return NextResponse.json(
        { error: 'Post not found' },
        { status: 404 }
      )
    }

    await prisma.post.delete({ where: { id } })

    // Return 204 No Content
    return new NextResponse(null, { status: 204 })
  } catch (error) {
    console.error('DELETE /api/posts/[id] error:', error)
    return NextResponse.json(
      { error: 'Failed to delete post' },
      { status: 500 }
    )
  }
}
```

## Error Handler Utility

```tsx
// lib/api-utils.ts
import { NextResponse } from 'next/server'
import { ZodError } from 'zod'
import { Prisma } from '@prisma/client'

export function handleApiError(error: unknown) {
  console.error('API Error:', error)

  if (error instanceof ZodError) {
    return NextResponse.json(
      {
        error: 'Validation failed',
        details: error.flatten(),
      },
      { status: 400 }
    )
  }

  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === 'P2025') {
      return NextResponse.json(
        { error: 'Record not found' },
        { status: 404 }
      )
    }

    if (error.code === 'P2002') {
      return NextResponse.json(
        { error: 'Duplicate entry' },
        { status: 409 }
      )
    }
  }

  return NextResponse.json(
    { error: 'Internal server error' },
    { status: 500 }
  )
}
```

## Usage Examples

### Fetch All Posts

```tsx
// Client-side fetch
const response = await fetch('/api/posts?page=1&limit=10&sort=newest')
const { data, pagination } = await response.json()
```

### Create a Post

```tsx
const response = await fetch('/api/posts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'My New Post',
    content: 'Post content here...',
    authorId: 'user-uuid',
  }),
})
const newPost = await response.json()
```

### Update a Post (Partial)

```tsx
const response = await fetch('/api/posts/post-id', {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    published: true,
  }),
})
const updatedPost = await response.json()
```

### Delete a Post

```tsx
const response = await fetch('/api/posts/post-id', {
  method: 'DELETE',
})

if (response.status === 204) {
  console.log('Post deleted successfully')
}
```

## Adding Authentication

```tsx
// app/api/posts/route.ts
import { auth } from '@/auth'

export async function POST(request: NextRequest) {
  // Check authentication
  const session = await auth()

  if (!session?.user) {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 401 }
    )
  }

  // Use authenticated user's ID
  const body = await request.json()
  body.authorId = session.user.id

  // ... rest of POST logic
}
```

## Rate Limiting

```tsx
// lib/rate-limit.ts
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'),
  analytics: true,
})

// app/api/posts/route.ts
export async function POST(request: NextRequest) {
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

  // ... rest of handler
}
```
