# Server Actions Mutation Patterns

## Basic CRUD Mutations

### Create

```tsx
// actions/posts.ts
'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { z } from 'zod'
import { auth } from '@/auth'

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(10),
  published: z.boolean().optional().default(false),
})

export async function createPost(formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const validated = createPostSchema.parse({
    title: formData.get('title'),
    content: formData.get('content'),
    published: formData.get('published') === 'true',
  })

  const post = await db.post.create({
    data: {
      ...validated,
      authorId: session.user.id,
    },
  })

  revalidatePath('/posts')
  redirect(`/posts/${post.id}`)
}
```

### Update

```tsx
// actions/posts.ts
'use server'

export async function updatePost(id: string, formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  // Verify ownership
  const post = await db.post.findUnique({
    where: { id },
    select: { authorId: true },
  })

  if (post?.authorId !== session.user.id) {
    throw new Error('Forbidden')
  }

  await db.post.update({
    where: { id },
    data: {
      title: formData.get('title') as string,
      content: formData.get('content') as string,
    },
  })

  revalidatePath('/posts')
  revalidatePath(`/posts/${id}`)
}
```

### Delete

```tsx
// actions/posts.ts
'use server'

export async function deletePost(id: string) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  // Verify ownership or admin
  const post = await db.post.findUnique({
    where: { id },
    select: { authorId: true },
  })

  if (post?.authorId !== session.user.id && session.user.role !== 'admin') {
    throw new Error('Forbidden')
  }

  await db.post.delete({ where: { id } })

  revalidatePath('/posts')
  redirect('/posts')
}
```

## Optimistic Updates

### Like Button with Optimistic UI

```tsx
// components/like-button.tsx
'use client'

import { useOptimistic, useTransition } from 'react'
import { toggleLike } from '@/actions/likes'

interface Props {
  postId: string
  initialLikes: number
  initialIsLiked: boolean
}

export function LikeButton({ postId, initialLikes, initialIsLiked }: Props) {
  const [isPending, startTransition] = useTransition()

  const [optimisticState, addOptimistic] = useOptimistic(
    { likes: initialLikes, isLiked: initialIsLiked },
    (state) => ({
      likes: state.isLiked ? state.likes - 1 : state.likes + 1,
      isLiked: !state.isLiked,
    })
  )

  async function handleClick() {
    startTransition(async () => {
      addOptimistic(null)
      await toggleLike(postId)
    })
  }

  return (
    <button
      onClick={handleClick}
      disabled={isPending}
      className="flex items-center gap-2"
    >
      <span className={optimisticState.isLiked ? 'text-red-500' : ''}>
        {optimisticState.isLiked ? '❤️' : '🤍'}
      </span>
      <span>{optimisticState.likes}</span>
    </button>
  )
}
```

```tsx
// actions/likes.ts
'use server'

import { revalidateTag } from 'next/cache'
import { auth } from '@/auth'

export async function toggleLike(postId: string) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const existing = await db.like.findUnique({
    where: {
      userId_postId: {
        userId: session.user.id,
        postId,
      },
    },
  })

  if (existing) {
    await db.like.delete({
      where: { id: existing.id },
    })
  } else {
    await db.like.create({
      data: {
        userId: session.user.id,
        postId,
      },
    })
  }

  revalidateTag(`post-${postId}`)
}
```

### Optimistic List Item

```tsx
// components/todo-list.tsx
'use client'

import { useOptimistic, useRef } from 'react'
import { addTodo } from '@/actions/todos'

interface Todo {
  id: string
  text: string
  completed: boolean
}

export function TodoList({ initialTodos }: { initialTodos: Todo[] }) {
  const formRef = useRef<HTMLFormElement>(null)

  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    initialTodos,
    (state, newTodo: Todo) => [...state, newTodo]
  )

  async function handleSubmit(formData: FormData) {
    const text = formData.get('text') as string

    // Add optimistic todo with temporary ID
    addOptimisticTodo({
      id: `temp-${Date.now()}`,
      text,
      completed: false,
    })

    formRef.current?.reset()

    // Server action will revalidate
    await addTodo(formData)
  }

  return (
    <div>
      <ul>
        {optimisticTodos.map((todo) => (
          <li
            key={todo.id}
            className={todo.id.startsWith('temp-') ? 'opacity-50' : ''}
          >
            {todo.text}
          </li>
        ))}
      </ul>

      <form ref={formRef} action={handleSubmit}>
        <input name="text" placeholder="Add todo..." required />
        <button type="submit">Add</button>
      </form>
    </div>
  )
}
```

## Error Handling

### Returning Errors to UI

```tsx
// actions/newsletter.ts
'use server'

import { z } from 'zod'

export type SubscribeResult = {
  success?: boolean
  error?: string
}

const schema = z.object({
  email: z.string().email('Please enter a valid email'),
})

export async function subscribe(
  _prevState: SubscribeResult,
  formData: FormData
): Promise<SubscribeResult> {
  const result = schema.safeParse({
    email: formData.get('email'),
  })

  if (!result.success) {
    return { error: result.error.errors[0].message }
  }

  try {
    // Check if already subscribed
    const existing = await db.subscriber.findUnique({
      where: { email: result.data.email },
    })

    if (existing) {
      return { error: 'This email is already subscribed' }
    }

    await db.subscriber.create({
      data: { email: result.data.email },
    })

    return { success: true }
  } catch (error) {
    console.error('Subscribe error:', error)
    return { error: 'Something went wrong. Please try again.' }
  }
}
```

```tsx
// components/newsletter-form.tsx
'use client'

import { useFormState } from 'react-dom'
import { subscribe } from '@/actions/newsletter'
import { SubmitButton } from './submit-button'

export function NewsletterForm() {
  const [state, formAction] = useFormState(subscribe, {})

  if (state.success) {
    return (
      <div className="bg-green-100 text-green-800 p-4 rounded">
        Thanks for subscribing!
      </div>
    )
  }

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <input
          name="email"
          type="email"
          placeholder="Enter your email"
          className={state.error ? 'border-red-500' : ''}
        />
        {state.error && (
          <p className="text-red-500 text-sm mt-1">{state.error}</p>
        )}
      </div>
      <SubmitButton>Subscribe</SubmitButton>
    </form>
  )
}
```

### Global Error Boundary

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
    console.error('Application error:', error)
  }, [error])

  return (
    <div className="p-8 text-center">
      <h2 className="text-2xl font-bold text-red-600">Something went wrong!</h2>
      <p className="mt-2 text-gray-600">{error.message}</p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Try again
      </button>
    </div>
  )
}
```

## Transaction Patterns

### Multi-Step Transaction

```tsx
// actions/checkout.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function processCheckout(formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    throw new Error('Unauthorized')
  }

  const cartItems = await db.cartItem.findMany({
    where: { userId: session.user.id },
    include: { product: true },
  })

  if (cartItems.length === 0) {
    return { error: 'Cart is empty' }
  }

  // Use transaction to ensure atomicity
  const order = await db.$transaction(async (tx) => {
    // 1. Create order
    const order = await tx.order.create({
      data: {
        userId: session.user.id,
        status: 'pending',
        total: cartItems.reduce(
          (sum, item) => sum + item.quantity * item.product.price,
          0
        ),
      },
    })

    // 2. Create order items
    await tx.orderItem.createMany({
      data: cartItems.map((item) => ({
        orderId: order.id,
        productId: item.productId,
        quantity: item.quantity,
        price: item.product.price,
      })),
    })

    // 3. Update inventory
    for (const item of cartItems) {
      await tx.product.update({
        where: { id: item.productId },
        data: {
          inventory: {
            decrement: item.quantity,
          },
        },
      })
    }

    // 4. Clear cart
    await tx.cartItem.deleteMany({
      where: { userId: session.user.id },
    })

    return order
  })

  revalidatePath('/cart')
  revalidatePath('/orders')

  return { success: true, orderId: order.id }
}
```

## Real-time Updates with Server Actions

### Polling Pattern

```tsx
// components/live-data.tsx
'use client'

import { useEffect, useState, useTransition } from 'react'
import { getData } from '@/actions/data'

export function LiveData() {
  const [data, setData] = useState(null)
  const [isPending, startTransition] = useTransition()

  useEffect(() => {
    // Initial fetch
    startTransition(async () => {
      const result = await getData()
      setData(result)
    })

    // Poll every 5 seconds
    const interval = setInterval(() => {
      startTransition(async () => {
        const result = await getData()
        setData(result)
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      {isPending && <span className="text-gray-400">Updating...</span>}
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}
```

## Bound Actions with Arguments

```tsx
// components/post-actions.tsx
import { deletePost, publishPost } from '@/actions/posts'

export function PostActions({ postId }: { postId: string }) {
  // Bind the postId to the action
  const deleteWithId = deletePost.bind(null, postId)
  const publishWithId = publishPost.bind(null, postId)

  return (
    <div className="flex gap-2">
      <form action={publishWithId}>
        <button type="submit">Publish</button>
      </form>

      <form action={deleteWithId}>
        <button type="submit" className="text-red-600">
          Delete
        </button>
      </form>
    </div>
  )
}
```

```tsx
// actions/posts.ts
'use server'

export async function deletePost(postId: string) {
  await db.post.delete({ where: { id: postId } })
  revalidatePath('/posts')
}

export async function publishPost(postId: string) {
  await db.post.update({
    where: { id: postId },
    data: { published: true },
  })
  revalidatePath('/posts')
  revalidatePath(`/posts/${postId}`)
}
```

## Debounced Auto-Save

```tsx
// components/auto-save-form.tsx
'use client'

import { useEffect, useRef, useState, useTransition } from 'react'
import { saveDraft } from '@/actions/drafts'

export function AutoSaveForm({ draftId, initialContent }: {
  draftId: string
  initialContent: string
}) {
  const [content, setContent] = useState(initialContent)
  const [saved, setSaved] = useState(true)
  const [isPending, startTransition] = useTransition()
  const timeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    if (content === initialContent) return

    setSaved(false)

    // Debounce save
    clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      startTransition(async () => {
        await saveDraft(draftId, content)
        setSaved(true)
      })
    }, 1000)

    return () => clearTimeout(timeoutRef.current)
  }, [content, draftId, initialContent])

  return (
    <div>
      <div className="flex justify-between mb-2">
        <span>Draft</span>
        <span className="text-sm text-gray-500">
          {isPending ? 'Saving...' : saved ? 'Saved' : 'Unsaved changes'}
        </span>
      </div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="w-full h-64 p-4 border rounded"
      />
    </div>
  )
}
```

```tsx
// actions/drafts.ts
'use server'

export async function saveDraft(id: string, content: string) {
  await db.draft.update({
    where: { id },
    data: {
      content,
      updatedAt: new Date(),
    },
  })
}
```
