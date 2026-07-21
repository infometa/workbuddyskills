# Server and Client Component Composition Patterns

## The Children Pattern

Pass Server Components to Client Components via children:

```tsx
// components/modal.tsx (Client)
'use client'

import { useState } from 'react'

export function Modal({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Open</button>
      {isOpen && (
        <div className="modal">
          {children} {/* Server-rendered! */}
          <button onClick={() => setIsOpen(false)}>Close</button>
        </div>
      )}
    </>
  )
}

// app/page.tsx (Server)
import { Modal } from '@/components/modal'
import { ServerContent } from '@/components/server-content'

export default async function Page() {
  const data = await getData() // Fetched on server

  return (
    <Modal>
      <ServerContent data={data} /> {/* Rendered on server */}
    </Modal>
  )
}
```

## The Slots Pattern

Multiple render props for complex layouts:

```tsx
// components/dashboard-shell.tsx (Client)
'use client'

import { useState } from 'react'

interface DashboardShellProps {
  header: React.ReactNode
  sidebar: React.ReactNode
  main: React.ReactNode
}

export function DashboardShell({ header, sidebar, main }: DashboardShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex flex-col h-screen">
      <header className="h-16 border-b">{header}</header>
      <div className="flex flex-1">
        {sidebarOpen && <aside className="w-64">{sidebar}</aside>}
        <main className="flex-1">{main}</main>
      </div>
    </div>
  )
}

// app/dashboard/page.tsx (Server)
export default async function DashboardPage() {
  const user = await getUser()
  const stats = await getStats()
  const navigation = await getNavigation()

  return (
    <DashboardShell
      header={<UserHeader user={user} />}
      sidebar={<Navigation items={navigation} />}
      main={<DashboardContent stats={stats} />}
    />
  )
}
```

## Provider Pattern

Wrap providers at the boundary:

```tsx
// app/providers.tsx (Client)
'use client'

import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system">
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  )
}

// app/layout.tsx (Server)
import { Providers } from './providers'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

## Data Down, Actions Up

Pass server data down, use Server Actions for mutations:

```tsx
// app/posts/page.tsx (Server)
import { PostList } from '@/components/post-list'
import { deletePost } from '@/actions/posts'

export default async function PostsPage() {
  const posts = await db.post.findMany()

  return <PostList posts={posts} onDelete={deletePost} />
}

// components/post-list.tsx (Client)
'use client'

import { useTransition } from 'react'

interface Post {
  id: string
  title: string
}

interface PostListProps {
  posts: Post[]
  onDelete: (id: string) => Promise<void>
}

export function PostList({ posts, onDelete }: PostListProps) {
  const [isPending, startTransition] = useTransition()

  const handleDelete = (id: string) => {
    startTransition(async () => {
      await onDelete(id)
    })
  }

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>
          {post.title}
          <button
            onClick={() => handleDelete(post.id)}
            disabled={isPending}
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  )
}

// actions/posts.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function deletePost(id: string) {
  await db.post.delete({ where: { id } })
  revalidatePath('/posts')
}
```

## Lifting State Up

Move state to closest Client Component ancestor:

```tsx
// Before: Too much client code
'use client'
export function ProductPage() {
  const [selectedSize, setSelectedSize] = useState('M')
  const product = useProduct() // Client fetch

  return (
    <div>
      <h1>{product.title}</h1>  {/* Could be server */}
      <p>{product.description}</p>  {/* Could be server */}
      <SizeSelector value={selectedSize} onChange={setSelectedSize} />
      <AddToCart productId={product.id} size={selectedSize} />
    </div>
  )
}

// After: Minimal client code
// app/products/[id]/page.tsx (Server)
export default async function ProductPage({ params }) {
  const { id } = await params
  const product = await getProduct(id)

  return (
    <div>
      <h1>{product.title}</h1>
      <p>{product.description}</p>
      <ProductActions productId={product.id} />
    </div>
  )
}

// components/product-actions.tsx (Client)
'use client'

export function ProductActions({ productId }: { productId: string }) {
  const [selectedSize, setSelectedSize] = useState('M')

  return (
    <>
      <SizeSelector value={selectedSize} onChange={setSelectedSize} />
      <AddToCart productId={productId} size={selectedSize} />
    </>
  )
}
```

## Shared Data Pattern

Use React's cache() for shared data:

```tsx
// lib/get-user.ts
import { cache } from 'react'

export const getUser = cache(async () => {
  const response = await fetch('/api/user')
  return response.json()
})

// app/layout.tsx (Server)
import { getUser } from '@/lib/get-user'

export default async function Layout({ children }) {
  const user = await getUser() // Cached

  return (
    <div>
      <header>Welcome, {user.name}</header>
      {children}
    </div>
  )
}

// app/page.tsx (Server)
import { getUser } from '@/lib/get-user'

export default async function Page() {
  const user = await getUser() // Returns cached result

  return <h1>Hello, {user.name}!</h1>
}
```

## Context for Client Tree

Context only works in Client Components:

```tsx
// context/cart-context.tsx (Client)
'use client'

import { createContext, useContext, useState } from 'react'

interface CartContextType {
  items: string[]
  addItem: (id: string) => void
}

const CartContext = createContext<CartContextType | null>(null)

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<string[]>([])

  const addItem = (id: string) => {
    setItems(prev => [...prev, id])
  }

  return (
    <CartContext.Provider value={{ items, addItem }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart() {
  const context = useContext(CartContext)
  if (!context) throw new Error('useCart must be used within CartProvider')
  return context
}

// components/add-to-cart.tsx (Client)
'use client'

import { useCart } from '@/context/cart-context'

export function AddToCart({ productId }: { productId: string }) {
  const { addItem } = useCart()

  return (
    <button onClick={() => addItem(productId)}>
      Add to Cart
    </button>
  )
}
```

## Render Props for Server Components

```tsx
// components/data-fetcher.tsx (Server)
interface DataFetcherProps<T> {
  fetch: () => Promise<T>
  render: (data: T) => React.ReactNode
}

export async function DataFetcher<T>({ fetch, render }: DataFetcherProps<T>) {
  const data = await fetch()
  return <>{render(data)}</>
}

// Usage in Server Component
export default function Page() {
  return (
    <DataFetcher
      fetch={getUsers}
      render={(users) => (
        <ul>
          {users.map(u => <li key={u.id}>{u.name}</li>)}
        </ul>
      )}
    />
  )
}
```

## Higher-Order Component Pattern

```tsx
// lib/with-auth.tsx
import { auth } from '@/auth'
import { redirect } from 'next/navigation'

export function withAuth<P extends object>(
  Component: React.ComponentType<P & { user: User }>
) {
  return async function AuthenticatedComponent(props: P) {
    const session = await auth()

    if (!session?.user) {
      redirect('/login')
    }

    return <Component {...props} user={session.user} />
  }
}

// app/dashboard/page.tsx
import { withAuth } from '@/lib/with-auth'

function DashboardPage({ user }: { user: User }) {
  return <h1>Welcome, {user.name}</h1>
}

export default withAuth(DashboardPage)
```
