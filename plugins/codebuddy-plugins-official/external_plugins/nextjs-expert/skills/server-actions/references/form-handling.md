# Form Handling with Server Actions

## Basic Form Setup

### Server Action in Separate File

```tsx
// actions/contact.ts
'use server'

export async function submitContact(formData: FormData) {
  const name = formData.get('name') as string
  const email = formData.get('email') as string
  const message = formData.get('message') as string

  await db.contact.create({
    data: { name, email, message },
  })
}
```

### Form Component

```tsx
// app/contact/page.tsx
import { submitContact } from '@/actions/contact'

export default function ContactPage() {
  return (
    <form action={submitContact}>
      <input name="name" placeholder="Name" required />
      <input name="email" type="email" placeholder="Email" required />
      <textarea name="message" placeholder="Message" required />
      <button type="submit">Send</button>
    </form>
  )
}
```

## useFormState for Feedback

### Action with Return Value

```tsx
// actions/subscribe.ts
'use server'

import { z } from 'zod'

const schema = z.object({
  email: z.string().email('Invalid email address'),
})

export type SubscribeState = {
  success?: boolean
  error?: string
}

export async function subscribe(
  prevState: SubscribeState,
  formData: FormData
): Promise<SubscribeState> {
  const email = formData.get('email')

  const validated = schema.safeParse({ email })

  if (!validated.success) {
    return { error: validated.error.errors[0].message }
  }

  try {
    await db.subscriber.create({
      data: { email: validated.data.email },
    })
    return { success: true }
  } catch (error) {
    return { error: 'Failed to subscribe' }
  }
}
```

### Form with useFormState

```tsx
// components/subscribe-form.tsx
'use client'

import { useFormState } from 'react-dom'
import { subscribe, type SubscribeState } from '@/actions/subscribe'

const initialState: SubscribeState = {}

export function SubscribeForm() {
  const [state, formAction] = useFormState(subscribe, initialState)

  return (
    <form action={formAction}>
      <input
        name="email"
        type="email"
        placeholder="Enter your email"
        required
      />

      <SubmitButton />

      {state.error && (
        <p className="text-red-500">{state.error}</p>
      )}

      {state.success && (
        <p className="text-green-500">Successfully subscribed!</p>
      )}
    </form>
  )
}
```

## useFormStatus for Loading States

```tsx
// components/submit-button.tsx
'use client'

import { useFormStatus } from 'react-dom'

export function SubmitButton() {
  const { pending } = useFormStatus()

  return (
    <button
      type="submit"
      disabled={pending}
      className={pending ? 'opacity-50' : ''}
    >
      {pending ? 'Submitting...' : 'Submit'}
    </button>
  )
}
```

### With Additional Status Info

```tsx
// components/form-status.tsx
'use client'

import { useFormStatus } from 'react-dom'

export function FormStatus() {
  const { pending, data, method, action } = useFormStatus()

  if (!pending) return null

  return (
    <div className="text-gray-500">
      <p>Submitting form...</p>
      {data && <p>Fields: {Array.from(data.keys()).join(', ')}</p>}
    </div>
  )
}
```

## Complex Form with Multiple Fields

### Action

```tsx
// actions/create-post.ts
'use server'

import { z } from 'zod'
import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'

const createPostSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  content: z.string().min(10, 'Content must be at least 10 characters'),
  category: z.enum(['tech', 'lifestyle', 'business']),
  published: z.coerce.boolean().optional().default(false),
  tags: z.string().transform(str =>
    str.split(',').map(tag => tag.trim()).filter(Boolean)
  ),
})

export type CreatePostState = {
  success?: boolean
  errors?: {
    title?: string[]
    content?: string[]
    category?: string[]
    _form?: string[]
  }
}

export async function createPost(
  prevState: CreatePostState,
  formData: FormData
): Promise<CreatePostState> {
  const rawData = {
    title: formData.get('title'),
    content: formData.get('content'),
    category: formData.get('category'),
    published: formData.get('published'),
    tags: formData.get('tags'),
  }

  const validated = createPostSchema.safeParse(rawData)

  if (!validated.success) {
    return {
      errors: validated.error.flatten().fieldErrors,
    }
  }

  try {
    const post = await db.post.create({
      data: {
        ...validated.data,
        authorId: getCurrentUserId(),
      },
    })

    revalidatePath('/posts')
    redirect(`/posts/${post.id}`)
  } catch (error) {
    return {
      errors: {
        _form: ['Failed to create post. Please try again.'],
      },
    }
  }
}
```

### Form Component

```tsx
// components/create-post-form.tsx
'use client'

import { useFormState } from 'react-dom'
import { createPost, type CreatePostState } from '@/actions/create-post'

const initialState: CreatePostState = {}

export function CreatePostForm() {
  const [state, formAction] = useFormState(createPost, initialState)

  return (
    <form action={formAction} className="space-y-4">
      {/* Form-level errors */}
      {state.errors?._form && (
        <div className="bg-red-100 text-red-700 p-4 rounded">
          {state.errors._form.map((error, i) => (
            <p key={i}>{error}</p>
          ))}
        </div>
      )}

      {/* Title field */}
      <div>
        <label htmlFor="title">Title</label>
        <input
          id="title"
          name="title"
          className={state.errors?.title ? 'border-red-500' : ''}
        />
        {state.errors?.title && (
          <p className="text-red-500 text-sm">{state.errors.title[0]}</p>
        )}
      </div>

      {/* Content field */}
      <div>
        <label htmlFor="content">Content</label>
        <textarea
          id="content"
          name="content"
          rows={10}
          className={state.errors?.content ? 'border-red-500' : ''}
        />
        {state.errors?.content && (
          <p className="text-red-500 text-sm">{state.errors.content[0]}</p>
        )}
      </div>

      {/* Category select */}
      <div>
        <label htmlFor="category">Category</label>
        <select id="category" name="category">
          <option value="">Select category</option>
          <option value="tech">Technology</option>
          <option value="lifestyle">Lifestyle</option>
          <option value="business">Business</option>
        </select>
        {state.errors?.category && (
          <p className="text-red-500 text-sm">{state.errors.category[0]}</p>
        )}
      </div>

      {/* Published checkbox */}
      <div className="flex items-center gap-2">
        <input type="checkbox" id="published" name="published" value="true" />
        <label htmlFor="published">Publish immediately</label>
      </div>

      {/* Tags input */}
      <div>
        <label htmlFor="tags">Tags (comma-separated)</label>
        <input id="tags" name="tags" placeholder="react, nextjs, typescript" />
      </div>

      <SubmitButton />
    </form>
  )
}
```

## File Upload Form

```tsx
// actions/upload.ts
'use server'

import { writeFile } from 'fs/promises'
import path from 'path'

export type UploadState = {
  success?: boolean
  error?: string
  url?: string
}

export async function uploadFile(
  prevState: UploadState,
  formData: FormData
): Promise<UploadState> {
  const file = formData.get('file') as File

  if (!file || file.size === 0) {
    return { error: 'No file selected' }
  }

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    return { error: 'Invalid file type. Only JPEG, PNG, and WebP allowed.' }
  }

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    return { error: 'File too large. Maximum 5MB allowed.' }
  }

  try {
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    const filename = `${Date.now()}-${file.name}`
    const filepath = path.join(process.cwd(), 'public/uploads', filename)

    await writeFile(filepath, buffer)

    return {
      success: true,
      url: `/uploads/${filename}`,
    }
  } catch (error) {
    return { error: 'Failed to upload file' }
  }
}
```

### Upload Form Component

```tsx
// components/upload-form.tsx
'use client'

import { useFormState } from 'react-dom'
import { useState } from 'react'
import { uploadFile, type UploadState } from '@/actions/upload'

const initialState: UploadState = {}

export function UploadForm() {
  const [state, formAction] = useFormState(uploadFile, initialState)
  const [preview, setPreview] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setPreview(URL.createObjectURL(file))
    }
  }

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="file" className="block">
          Choose an image
        </label>
        <input
          type="file"
          id="file"
          name="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileChange}
        />
      </div>

      {preview && (
        <div>
          <img src={preview} alt="Preview" className="max-w-xs rounded" />
        </div>
      )}

      <SubmitButton />

      {state.error && (
        <p className="text-red-500">{state.error}</p>
      )}

      {state.success && state.url && (
        <div className="text-green-500">
          <p>Upload successful!</p>
          <img src={state.url} alt="Uploaded" className="max-w-xs mt-2" />
        </div>
      )}
    </form>
  )
}
```

## Form with Dynamic Fields

```tsx
// components/dynamic-form.tsx
'use client'

import { useFormState } from 'react-dom'
import { useState } from 'react'
import { submitItems } from '@/actions/items'

export function DynamicForm() {
  const [state, formAction] = useFormState(submitItems, {})
  const [items, setItems] = useState([{ id: 1, value: '' }])

  const addItem = () => {
    setItems(prev => [...prev, { id: Date.now(), value: '' }])
  }

  const removeItem = (id: number) => {
    setItems(prev => prev.filter(item => item.id !== id))
  }

  return (
    <form action={formAction}>
      {items.map((item, index) => (
        <div key={item.id} className="flex gap-2">
          <input
            name={`items[${index}]`}
            placeholder={`Item ${index + 1}`}
          />
          <button
            type="button"
            onClick={() => removeItem(item.id)}
          >
            Remove
          </button>
        </div>
      ))}

      <button type="button" onClick={addItem}>
        Add Item
      </button>

      <SubmitButton />
    </form>
  )
}
```

### Process Dynamic Fields

```tsx
// actions/items.ts
'use server'

export async function submitItems(
  prevState: unknown,
  formData: FormData
) {
  // Get all items from form
  const items: string[] = []
  let index = 0

  while (formData.has(`items[${index}]`)) {
    const value = formData.get(`items[${index}]`) as string
    if (value.trim()) {
      items.push(value.trim())
    }
    index++
  }

  // Process items...
  await db.item.createMany({
    data: items.map(name => ({ name })),
  })

  return { success: true, count: items.length }
}
```

## Progressive Enhancement

Forms work without JavaScript enabled:

```tsx
// components/search-form.tsx
import { searchPosts } from '@/actions/search'

export function SearchForm() {
  return (
    <form action={searchPosts}>
      <input name="q" placeholder="Search..." />
      <button type="submit">Search</button>
    </form>
  )
}
```

```tsx
// actions/search.ts
'use server'

import { redirect } from 'next/navigation'

export async function searchPosts(formData: FormData) {
  const query = formData.get('q') as string
  redirect(`/search?q=${encodeURIComponent(query)}`)
}
```
