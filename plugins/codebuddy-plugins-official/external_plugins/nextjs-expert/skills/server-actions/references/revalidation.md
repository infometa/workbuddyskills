# Revalidation with Server Actions

## Overview

After mutations, revalidate cached data to reflect changes:
- `revalidatePath()` - Invalidate specific routes
- `revalidateTag()` - Invalidate by cache tag

## revalidatePath

### Basic Usage

```tsx
// actions/posts.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function createPost(formData: FormData) {
  const post = await db.post.create({
    data: {
      title: formData.get('title') as string,
      content: formData.get('content') as string,
    },
  })

  // Revalidate the posts list page
  revalidatePath('/posts')
}
```

### Path Types

```tsx
// Revalidate a specific page
revalidatePath('/posts')

// Revalidate a dynamic route
revalidatePath('/posts/[slug]', 'page')

// Revalidate a layout (and all pages using it)
revalidatePath('/posts', 'layout')

// Revalidate everything
revalidatePath('/', 'layout')
```

### Revalidate Multiple Paths

```tsx
// actions/update-post.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function updatePost(id: string, formData: FormData) {
  const post = await db.post.update({
    where: { id },
    data: {
      title: formData.get('title') as string,
      content: formData.get('content') as string,
    },
  })

  // Revalidate both the list and detail pages
  revalidatePath('/posts')
  revalidatePath(`/posts/${post.slug}`)
}
```

### With Dynamic Segments

```tsx
// actions/category.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function updateCategory(categorySlug: string, formData: FormData) {
  await db.category.update({
    where: { slug: categorySlug },
    data: { name: formData.get('name') as string },
  })

  // Revalidate the specific category page
  revalidatePath(`/categories/${categorySlug}`)

  // Also revalidate all product pages in this category
  revalidatePath('/products/[...slug]', 'page')
}
```

## revalidateTag

### Setup Tags in Data Fetching

```tsx
// lib/data.ts
export async function getPosts() {
  const res = await fetch('https://api.example.com/posts', {
    next: { tags: ['posts'] },
  })
  return res.json()
}

export async function getPost(id: string) {
  const res = await fetch(`https://api.example.com/posts/${id}`, {
    next: { tags: ['posts', `post-${id}`] },
  })
  return res.json()
}

export async function getUser(id: string) {
  const res = await fetch(`https://api.example.com/users/${id}`, {
    next: { tags: ['users', `user-${id}`] },
  })
  return res.json()
}
```

### Revalidate by Tag

```tsx
// actions/posts.ts
'use server'

import { revalidateTag } from 'next/cache'

export async function createPost(formData: FormData) {
  await db.post.create({
    data: {
      title: formData.get('title') as string,
    },
  })

  // Invalidate all data tagged with 'posts'
  revalidateTag('posts')
}

export async function updatePost(id: string, formData: FormData) {
  await db.post.update({
    where: { id },
    data: { title: formData.get('title') as string },
  })

  // Invalidate just this specific post
  revalidateTag(`post-${id}`)
}

export async function deletePost(id: string) {
  await db.post.delete({ where: { id } })

  // Invalidate both the specific post and the list
  revalidateTag(`post-${id}`)
  revalidateTag('posts')
}
```

### Multiple Tags

```tsx
// actions/user.ts
'use server'

import { revalidateTag } from 'next/cache'

export async function updateUserProfile(userId: string, formData: FormData) {
  await db.user.update({
    where: { id: userId },
    data: {
      name: formData.get('name') as string,
      bio: formData.get('bio') as string,
    },
  })

  // Revalidate user data
  revalidateTag(`user-${userId}`)

  // Also revalidate their posts (which show author info)
  revalidateTag(`posts-by-${userId}`)
}
```

## Combining revalidatePath and revalidateTag

```tsx
// actions/blog.ts
'use server'

import { revalidatePath, revalidateTag } from 'next/cache'

export async function publishPost(id: string) {
  const post = await db.post.update({
    where: { id },
    data: { published: true },
  })

  // Revalidate cached API data by tag
  revalidateTag('posts')
  revalidateTag(`post-${id}`)

  // Revalidate rendered pages by path
  revalidatePath('/posts')
  revalidatePath(`/posts/${post.slug}`)
  revalidatePath('/') // Home page might show latest posts
}
```

## Revalidation Patterns

### Optimistic Update + Revalidation

```tsx
// components/like-button.tsx
'use client'

import { useOptimistic, useTransition } from 'react'
import { likePost } from '@/actions/posts'

interface Props {
  postId: string
  initialLikes: number
  isLiked: boolean
}

export function LikeButton({ postId, initialLikes, isLiked }: Props) {
  const [isPending, startTransition] = useTransition()
  const [optimisticState, addOptimistic] = useOptimistic(
    { likes: initialLikes, isLiked },
    (state, _action) => ({
      likes: state.isLiked ? state.likes - 1 : state.likes + 1,
      isLiked: !state.isLiked,
    })
  )

  const handleLike = () => {
    startTransition(async () => {
      addOptimistic(null)
      await likePost(postId) // This will revalidate
    })
  }

  return (
    <button onClick={handleLike} disabled={isPending}>
      {optimisticState.isLiked ? '❤️' : '🤍'} {optimisticState.likes}
    </button>
  )
}
```

```tsx
// actions/posts.ts
'use server'

import { revalidateTag } from 'next/cache'

export async function likePost(postId: string) {
  const userId = await getCurrentUserId()

  await db.like.upsert({
    where: {
      userId_postId: { userId, postId },
    },
    create: { userId, postId },
    update: {},
  })

  revalidateTag(`post-${postId}`)
}
```

### Cascade Revalidation

```tsx
// actions/comments.ts
'use server'

import { revalidateTag, revalidatePath } from 'next/cache'

export async function addComment(postId: string, formData: FormData) {
  const comment = await db.comment.create({
    data: {
      postId,
      content: formData.get('content') as string,
      authorId: await getCurrentUserId(),
    },
    include: { post: true },
  })

  // Revalidate the specific post (comment count changed)
  revalidateTag(`post-${postId}`)

  // Revalidate comments for this post
  revalidateTag(`comments-${postId}`)

  // Revalidate the post page
  revalidatePath(`/posts/${comment.post.slug}`)

  // Revalidate "recent comments" widgets
  revalidateTag('recent-comments')
}
```

### Conditional Revalidation

```tsx
// actions/posts.ts
'use server'

import { revalidatePath, revalidateTag } from 'next/cache'

export async function updatePost(id: string, formData: FormData) {
  const wasPublished = await db.post.findUnique({
    where: { id },
    select: { published: true },
  })

  const post = await db.post.update({
    where: { id },
    data: {
      title: formData.get('title') as string,
      published: formData.get('published') === 'true',
    },
  })

  // Always revalidate the specific post
  revalidateTag(`post-${id}`)
  revalidatePath(`/posts/${post.slug}`)

  // Only revalidate the list if publish status changed
  if (wasPublished?.published !== post.published) {
    revalidateTag('posts')
    revalidatePath('/posts')
    revalidatePath('/') // Feed page
  }
}
```

## Route Handler Revalidation

```tsx
// app/api/revalidate/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { revalidateTag, revalidatePath } from 'next/cache'

export async function POST(request: NextRequest) {
  const secret = request.headers.get('x-revalidate-secret')

  if (secret !== process.env.REVALIDATE_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 })
  }

  const body = await request.json()

  if (body.tag) {
    revalidateTag(body.tag)
  }

  if (body.path) {
    revalidatePath(body.path)
  }

  return NextResponse.json({ revalidated: true, now: Date.now() })
}
```

## On-Demand Revalidation from External Webhook

```tsx
// app/api/webhook/cms/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { revalidateTag } from 'next/cache'

export async function POST(request: NextRequest) {
  const signature = request.headers.get('x-webhook-signature')
  const body = await request.json()

  // Verify webhook signature
  if (!verifyWebhookSignature(signature, body)) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 })
  }

  const { event, data } = body

  switch (event) {
    case 'post.created':
    case 'post.updated':
    case 'post.deleted':
      revalidateTag('posts')
      revalidateTag(`post-${data.id}`)
      break

    case 'user.updated':
      revalidateTag(`user-${data.id}`)
      break

    case 'cache.purge':
      // Full cache purge
      revalidateTag('all')
      break
  }

  return NextResponse.json({ success: true })
}
```

## Debugging Revalidation

```tsx
// actions/debug.ts
'use server'

import { revalidatePath, revalidateTag } from 'next/cache'

export async function debugRevalidate(target: string, type: 'path' | 'tag') {
  console.log(`Revalidating ${type}: ${target}`)

  if (type === 'tag') {
    revalidateTag(target)
  } else {
    revalidatePath(target)
  }

  console.log(`Revalidation complete at: ${new Date().toISOString()}`)
}
```
