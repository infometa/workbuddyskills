# Data Fetching Patterns in Server Components

## Basic Async Component

```tsx
// app/posts/page.tsx
export default async function PostsPage() {
  const posts = await fetch('https://api.example.com/posts')
    .then(res => res.json())

  return (
    <ul>
      {posts.map(post => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

## Direct Database Access

```tsx
// app/users/page.tsx
import { prisma } from '@/lib/prisma'

export default async function UsersPage() {
  const users = await prisma.user.findMany({
    select: {
      id: true,
      name: true,
      email: true,
      _count: {
        select: { posts: true }
      }
    },
    orderBy: { createdAt: 'desc' },
    take: 10
  })

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>
            {user.name} ({user._count.posts} posts)
          </li>
        ))}
      </ul>
    </div>
  )
}
```

## Parallel Data Fetching

Fetch multiple resources simultaneously:

```tsx
// app/dashboard/page.tsx
async function getUser() {
  const res = await fetch('https://api.example.com/user')
  return res.json()
}

async function getPosts() {
  const res = await fetch('https://api.example.com/posts')
  return res.json()
}

async function getAnalytics() {
  const res = await fetch('https://api.example.com/analytics')
  return res.json()
}

export default async function DashboardPage() {
  // Fetch all data in parallel
  const [user, posts, analytics] = await Promise.all([
    getUser(),
    getPosts(),
    getAnalytics()
  ])

  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <PostsList posts={posts} />
      <AnalyticsChart data={analytics} />
    </div>
  )
}
```

## Sequential Data Fetching

When one request depends on another:

```tsx
// app/user/[id]/posts/page.tsx
interface PageProps {
  params: Promise<{ id: string }>
}

export default async function UserPostsPage({ params }: PageProps) {
  const { id } = await params

  // First, get user to verify they exist
  const user = await prisma.user.findUnique({
    where: { id }
  })

  if (!user) {
    notFound()
  }

  // Then, get their posts
  const posts = await prisma.post.findMany({
    where: { authorId: id },
    orderBy: { createdAt: 'desc' }
  })

  return (
    <div>
      <h1>{user.name}'s Posts</h1>
      <PostsList posts={posts} />
    </div>
  )
}
```

## Streaming with Suspense

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react'

// Fast component
function DashboardHeader() {
  return <h1>Dashboard</h1>
}

// Slow components
async function SlowStats() {
  const stats = await fetch('/api/stats', { cache: 'no-store' })
    .then(r => r.json())

  return <StatsDisplay stats={stats} />
}

async function SlowChart() {
  const data = await fetch('/api/chart-data', { cache: 'no-store' })
    .then(r => r.json())

  return <Chart data={data} />
}

export default function DashboardPage() {
  return (
    <div>
      <DashboardHeader /> {/* Renders immediately */}

      <Suspense fallback={<StatsSkeleton />}>
        <SlowStats /> {/* Streams when ready */}
      </Suspense>

      <Suspense fallback={<ChartSkeleton />}>
        <SlowChart /> {/* Streams independently */}
      </Suspense>
    </div>
  )
}
```

## Cached Data Fetching

### Using React cache()

```tsx
// lib/data.ts
import { cache } from 'react'
import { prisma } from '@/lib/prisma'

// Deduplicate within single render
export const getUser = cache(async (id: string) => {
  return prisma.user.findUnique({ where: { id } })
})

// Multiple components can call this
// Only one database query is made

// components/user-header.tsx
export async function UserHeader({ userId }: { userId: string }) {
  const user = await getUser(userId) // Cached
  return <header>Welcome, {user?.name}</header>
}

// components/user-sidebar.tsx
export async function UserSidebar({ userId }: { userId: string }) {
  const user = await getUser(userId) // Returns same cached value
  return <aside>{user?.bio}</aside>
}
```

### Using fetch() with caching

```tsx
// Default: Cache indefinitely (static)
const data = await fetch('https://api.example.com/data')

// Revalidate every hour
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 3600 }
})

// No caching (always fresh)
const data = await fetch('https://api.example.com/data', {
  cache: 'no-store'
})

// Cache with tags for targeted revalidation
const data = await fetch('https://api.example.com/posts', {
  next: { tags: ['posts'] }
})

// Later, revalidate by tag
import { revalidateTag } from 'next/cache'
revalidateTag('posts')
```

## Error Handling

```tsx
// app/posts/page.tsx
import { notFound } from 'next/navigation'

async function getPost(slug: string) {
  const res = await fetch(`https://api.example.com/posts/${slug}`)

  if (!res.ok) {
    if (res.status === 404) {
      return null
    }
    throw new Error('Failed to fetch post')
  }

  return res.json()
}

export default async function PostPage({
  params
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const post = await getPost(slug)

  if (!post) {
    notFound() // Renders not-found.tsx
  }

  return <article>{post.content}</article>
}
```

## With Loading States

```tsx
// app/products/page.tsx
import { Suspense } from 'react'

async function ProductGrid() {
  const products = await prisma.product.findMany()

  return (
    <div className="grid grid-cols-4 gap-4">
      {products.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}

async function FeaturedProducts() {
  const featured = await prisma.product.findMany({
    where: { featured: true },
    take: 4
  })

  return (
    <div className="flex gap-4">
      {featured.map(product => (
        <FeaturedCard key={product.id} product={product} />
      ))}
    </div>
  )
}

export default function ProductsPage() {
  return (
    <div>
      <h1>Products</h1>

      <section>
        <h2>Featured</h2>
        <Suspense fallback={<FeaturedSkeleton />}>
          <FeaturedProducts />
        </Suspense>
      </section>

      <section>
        <h2>All Products</h2>
        <Suspense fallback={<GridSkeleton />}>
          <ProductGrid />
        </Suspense>
      </section>
    </div>
  )
}
```

## Preloading Data

```tsx
// lib/data.ts
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  return prisma.user.findUnique({ where: { id } })
})

// Preload function (doesn't await)
export const preloadUser = (id: string) => {
  void getUser(id)
}

// app/user/[id]/page.tsx
import { getUser, preloadUser } from '@/lib/data'

export default async function UserPage({
  params
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params

  // Start fetching user data immediately
  preloadUser(id)

  // Do other work...

  // Now use the (likely cached) result
  const user = await getUser(id)

  return <UserProfile user={user} />
}
```

## Combining with Client Components

```tsx
// app/products/page.tsx (Server)
export default async function ProductsPage() {
  const products = await prisma.product.findMany()

  return (
    <div>
      <h1>Products</h1>
      {/* Client component receives server-fetched data */}
      <ProductFilter initialProducts={products} />
    </div>
  )
}

// components/product-filter.tsx (Client)
'use client'

import { useState, useMemo } from 'react'

interface Product {
  id: string
  name: string
  category: string
  price: number
}

export function ProductFilter({
  initialProducts
}: {
  initialProducts: Product[]
}) {
  const [category, setCategory] = useState('all')
  const [sort, setSort] = useState('name')

  const filtered = useMemo(() => {
    let result = initialProducts

    if (category !== 'all') {
      result = result.filter(p => p.category === category)
    }

    return result.sort((a, b) => {
      if (sort === 'price') return a.price - b.price
      return a.name.localeCompare(b.name)
    })
  }, [initialProducts, category, sort])

  return (
    <div>
      <div className="filters">
        <select value={category} onChange={e => setCategory(e.target.value)}>
          <option value="all">All Categories</option>
          <option value="electronics">Electronics</option>
          <option value="clothing">Clothing</option>
        </select>

        <select value={sort} onChange={e => setSort(e.target.value)}>
          <option value="name">Name</option>
          <option value="price">Price</option>
        </select>
      </div>

      <ul>
        {filtered.map(product => (
          <li key={product.id}>
            {product.name} - ${product.price}
          </li>
        ))}
      </ul>
    </div>
  )
}
```
