# Dynamic Routes Examples

## Single Dynamic Segment

### Basic Dynamic Route

```
app/
└── blog/
    └── [slug]/
        └── page.tsx
```

```tsx
// app/blog/[slug]/page.tsx
interface PageProps {
  params: Promise<{ slug: string }>
}

export default async function BlogPost({ params }: PageProps) {
  const { slug } = await params

  const post = await fetch(`https://api.example.com/posts/${slug}`)
    .then(res => res.json())

  return (
    <article>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
    </article>
  )
}

// Generate static pages at build time
export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts')
    .then(res => res.json())

  return posts.map((post) => ({
    slug: post.slug,
  }))
}
```

### Multiple Dynamic Segments

```
app/
└── shop/
    └── [category]/
        └── [productId]/
            └── page.tsx
```

```tsx
// app/shop/[category]/[productId]/page.tsx
interface PageProps {
  params: Promise<{
    category: string
    productId: string
  }>
}

export default async function ProductPage({ params }: PageProps) {
  const { category, productId } = await params

  return (
    <div>
      <nav>Category: {category}</nav>
      <h1>Product: {productId}</h1>
    </div>
  )
}

export async function generateStaticParams() {
  const products = await getProducts()

  return products.map((product) => ({
    category: product.category,
    productId: product.id,
  }))
}
```

## Catch-All Segments

### Basic Catch-All

```
app/
└── docs/
    └── [...slug]/
        └── page.tsx
```

Matches: `/docs/a`, `/docs/a/b`, `/docs/a/b/c`

```tsx
// app/docs/[...slug]/page.tsx
interface PageProps {
  params: Promise<{ slug: string[] }>
}

export default async function DocsPage({ params }: PageProps) {
  const { slug } = await params
  // slug = ['a', 'b', 'c'] for /docs/a/b/c

  const path = slug.join('/')
  const doc = await getDoc(path)

  return (
    <div>
      <nav>
        {slug.map((segment, index) => (
          <span key={index}>
            {index > 0 && ' / '}
            {segment}
          </span>
        ))}
      </nav>
      <article>{doc.content}</article>
    </div>
  )
}
```

### Optional Catch-All

```
app/
└── shop/
    └── [[...slug]]/
        └── page.tsx
```

Matches: `/shop`, `/shop/category`, `/shop/category/product`

```tsx
// app/shop/[[...slug]]/page.tsx
interface PageProps {
  params: Promise<{ slug?: string[] }>
}

export default async function ShopPage({ params }: PageProps) {
  const { slug } = await params

  // /shop -> slug is undefined
  // /shop/electronics -> slug = ['electronics']
  // /shop/electronics/phones -> slug = ['electronics', 'phones']

  if (!slug) {
    return <AllProducts />
  }

  if (slug.length === 1) {
    return <CategoryPage category={slug[0]} />
  }

  return <ProductPage category={slug[0]} product={slug[1]} />
}
```

## Dynamic Metadata

### Based on Route Params

```tsx
// app/blog/[slug]/page.tsx
import { Metadata } from 'next'

interface PageProps {
  params: Promise<{ slug: string }>
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { slug } = await params
  const post = await getPost(slug)

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [post.coverImage],
    },
  }
}

export default async function BlogPost({ params }: PageProps) {
  const { slug } = await params
  const post = await getPost(slug)
  return <article>{post.content}</article>
}
```

## Search Params

### Accessing Query Params

```tsx
// app/search/page.tsx
interface PageProps {
  searchParams: Promise<{ q?: string; page?: string }>
}

export default async function SearchPage({ searchParams }: PageProps) {
  const { q, page } = await searchParams
  const currentPage = parseInt(page || '1')

  const results = await search(q, currentPage)

  return (
    <div>
      <h1>Search results for: {q}</h1>
      <ul>
        {results.map(result => (
          <li key={result.id}>{result.title}</li>
        ))}
      </ul>
      <Pagination current={currentPage} />
    </div>
  )
}
```

### Combined with Dynamic Segments

```tsx
// app/products/[category]/page.tsx
interface PageProps {
  params: Promise<{ category: string }>
  searchParams: Promise<{ sort?: string; filter?: string }>
}

export default async function CategoryPage({
  params,
  searchParams,
}: PageProps) {
  const { category } = await params
  const { sort, filter } = await searchParams

  const products = await getProducts({
    category,
    sort: sort || 'newest',
    filter,
  })

  return (
    <div>
      <h1>{category}</h1>
      <ProductGrid products={products} />
    </div>
  )
}
```

## Static Generation Patterns

### Generate All Pages

```tsx
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await getAllPosts()

  return posts.map((post) => ({
    slug: post.slug,
  }))
}
```

### Generate on Demand (ISR)

```tsx
// app/blog/[slug]/page.tsx
export const dynamicParams = true // Allow dynamic params not in generateStaticParams

export async function generateStaticParams() {
  // Only pre-render popular posts
  const popularPosts = await getPopularPosts(10)

  return popularPosts.map((post) => ({
    slug: post.slug,
  }))
}
```

### Block Unknown Params

```tsx
// app/blog/[slug]/page.tsx
export const dynamicParams = false // Return 404 for unknown slugs

export async function generateStaticParams() {
  const posts = await getAllPosts()
  return posts.map((post) => ({ slug: post.slug }))
}
```

## Real-World Example: E-commerce

```
app/
└── shop/
    ├── page.tsx                           # /shop
    ├── [category]/
    │   ├── page.tsx                       # /shop/electronics
    │   └── [productId]/
    │       ├── page.tsx                   # /shop/electronics/123
    │       └── reviews/
    │           └── page.tsx               # /shop/electronics/123/reviews
    └── cart/
        └── page.tsx                       # /shop/cart
```

```tsx
// app/shop/[category]/[productId]/page.tsx
interface PageProps {
  params: Promise<{
    category: string
    productId: string
  }>
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { category, productId } = await params
  const product = await getProduct(productId)

  return {
    title: `${product.name} | ${category}`,
    description: product.description,
  }
}

export default async function ProductPage({ params }: PageProps) {
  const { category, productId } = await params
  const product = await getProduct(productId)

  return (
    <div>
      <Breadcrumbs category={category} product={product.name} />
      <ProductDetails product={product} />
      <RelatedProducts category={category} />
    </div>
  )
}

export async function generateStaticParams() {
  const products = await getAllProducts()

  return products.map((product) => ({
    category: product.category,
    productId: product.id,
  }))
}
```
