# Server vs Client Components

## Overview

In Next.js App Router, components are Server Components by default. Understanding when to use each type is crucial for optimal performance.

## Quick Decision Guide

| Need | Component Type |
|------|----------------|
| Fetch data | Server |
| Access backend resources | Server |
| Keep sensitive info on server | Server |
| Reduce client JavaScript | Server |
| Use useState/useReducer | Client |
| Use useEffect/lifecycle | Client |
| Use event listeners (onClick) | Client |
| Use browser APIs | Client |
| Use custom hooks with state | Client |

## Server Components

### Characteristics

- Render on the server only
- Never shipped to the client
- Can directly access databases, file systems
- No JavaScript bundle cost

### Example

```tsx
// app/users/page.tsx - Server Component (default)
import { db } from '@/lib/db'

export default async function UsersPage() {
  // Direct database access - only runs on server
  const users = await db.user.findMany({
    select: { id: true, name: true, email: true }
  })

  // Sensitive operations are safe
  const secret = process.env.API_SECRET

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  )
}
```

### What You Can Do

```tsx
// ✅ Server Component capabilities
async function ServerComponent() {
  // Database queries
  const data = await prisma.post.findMany()

  // File system access
  const file = await fs.readFile('./data.json')

  // Environment variables (secret)
  const apiKey = process.env.SECRET_API_KEY

  // Async operations
  const response = await fetch('https://api.example.com')

  // Heavy computations (not in client bundle)
  const processed = heavyComputation(data)

  return <div>{/* ... */}</div>
}
```

### What You Cannot Do

```tsx
// ❌ These will NOT work in Server Components
function ServerComponent() {
  // No hooks
  const [state, setState] = useState() // Error!
  useEffect(() => {}) // Error!

  // No event handlers
  <button onClick={() => {}} /> // Error!

  // No browser APIs
  window.localStorage // Error!
  document.querySelector // Error!
}
```

## Client Components

### Marking as Client

Add `'use client'` directive at the top:

```tsx
// components/counter.tsx
'use client'

import { useState } from 'react'

export function Counter() {
  const [count, setCount] = useState(0)

  return (
    <button onClick={() => setCount(c => c + 1)}>
      Count: {count}
    </button>
  )
}
```

### What You Can Do

```tsx
'use client'

function ClientComponent() {
  // Hooks
  const [state, setState] = useState()
  useEffect(() => {}, [])

  // Event handlers
  const handleClick = () => console.log('clicked')

  // Browser APIs
  const width = window.innerWidth

  return (
    <button onClick={handleClick}>
      Click me
    </button>
  )
}
```

### What You Cannot Do

```tsx
'use client'

// ❌ These will NOT work in Client Components
async function ClientComponent() {
  // No async component
  const data = await fetch() // Error!

  // No direct database access
  const users = await prisma.user.findMany() // Error!

  // No server-only imports
  import { readFile } from 'fs' // Error!
}
```

## The Client Boundary

### How It Works

When you add `'use client'`, you create a boundary:

```
Server Component (layout.tsx)
├── Server Component (header.tsx)
├── Server Component (sidebar.tsx)
└── Client Component ('use client') ← BOUNDARY
    ├── Client Component (automatically)
    ├── Client Component (automatically)
    └── Server Component via children ← Can still be Server!
```

### Key Rules

1. **Below the boundary is client by default**
   ```tsx
   'use client'

   // This component and all its imports become client
   import { Button } from './button' // Button is now client
   ```

2. **Props must be serializable**
   ```tsx
   // ✅ Can pass
   <ClientComponent
     data={{ name: 'John' }}    // Plain objects
     items={['a', 'b']}          // Arrays
     count={42}                  // Numbers
     isActive={true}             // Booleans
   />

   // ❌ Cannot pass
   <ClientComponent
     onClick={() => {}}          // Functions
     user={userInstance}         // Class instances
     date={new Date()}           // Date objects
   />
   ```

3. **Server Components can be children**
   ```tsx
   // components/client-wrapper.tsx
   'use client'

   export function ClientWrapper({ children }) {
     const [open, setOpen] = useState(false)
     return <div>{open && children}</div>
   }

   // app/page.tsx (Server)
   export default function Page() {
     return (
       <ClientWrapper>
         <ServerComponent /> {/* Still renders on server! */}
       </ClientWrapper>
     )
   }
   ```

## When to Use Client Directive

### Definitely Need 'use client'

```tsx
'use client'

// 1. Using React hooks
import { useState, useEffect, useContext } from 'react'

// 2. Using event handlers
<button onClick={handleClick}>

// 3. Using browser APIs
useEffect(() => {
  const width = window.innerWidth
}, [])

// 4. Using libraries that need browser
import { motion } from 'framer-motion'

// 5. Using Context
const theme = useContext(ThemeContext)
```

### Don't Need 'use client'

```tsx
// These work in Server Components

// Static rendering
<div className="container">
  <h1>Hello</h1>
</div>

// Data fetching
const data = await fetch('/api/data')

// Conditional rendering (based on data, not state)
{user.isAdmin && <AdminPanel />}

// Mapping over data
{items.map(item => <Item key={item.id} />)}
```

## Common Patterns

### Minimal Client Components

Keep client boundaries as small as possible:

```tsx
// ❌ Don't make entire page client
'use client'
export default function Page() {
  const [filter, setFilter] = useState('')
  const data = fetchedData // This won't work!
  // ...
}

// ✅ Make only interactive part client
// app/page.tsx (Server)
export default async function Page() {
  const data = await getData()
  return (
    <div>
      <h1>Products</h1>
      <ProductFilter /> {/* Client */}
      <ProductList products={data} />
    </div>
  )
}

// components/product-filter.tsx
'use client'
export function ProductFilter() {
  const [filter, setFilter] = useState('')
  // ...
}
```

### Interleaving Pattern

```tsx
// Server → Client → Server

// app/page.tsx (Server)
export default function Page() {
  return (
    <ClientTabs>
      <ServerContent /> {/* Passed as children */}
    </ClientTabs>
  )
}

// components/client-tabs.tsx
'use client'
export function ClientTabs({ children }) {
  const [tab, setTab] = useState(0)
  return (
    <div>
      <button onClick={() => setTab(0)}>Tab 1</button>
      <button onClick={() => setTab(1)}>Tab 2</button>
      {children} {/* Server-rendered content */}
    </div>
  )
}
```

## Debugging

### Check Component Type

```tsx
// Add this to see where component runs
export default function MyComponent() {
  console.log('Running on:', typeof window === 'undefined' ? 'server' : 'client')
  return <div>...</div>
}
```

### Common Errors

```
Error: useState only works in Client Components
→ Add 'use client' directive

Error: Event handlers cannot be passed to Client Component props
→ Move the handler into a Client Component

Error: Functions cannot be passed directly to Client Components
→ Create a Client wrapper or use Server Actions
```
