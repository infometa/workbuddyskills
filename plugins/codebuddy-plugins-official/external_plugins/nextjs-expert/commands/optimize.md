---
description: Analyze and optimize Next.js application performance
allowed-tools:
  - Read
  - Glob
  - Grep
  - Skill
  - AskUserQuestion
---

# Optimize Next.js Application

You are analyzing a Next.js application to identify and recommend performance optimizations.

## Workflow

### Step 1: Analyze Current State

Examine the codebase for common performance issues:

1. **Component Boundaries**
   - Find `'use client'` directives
   - Check if client boundaries are too high
   - Look for unnecessary client components

2. **Data Fetching**
   - Check for waterfalls (sequential fetches)
   - Look for missing parallel fetching
   - Identify uncached requests

3. **Bundle Size**
   - Check for large client-side imports
   - Look for unused dependencies
   - Find components that could be server-rendered

4. **Image Optimization**
   - Look for `<img>` tags (should use `next/image`)
   - Check for missing width/height
   - Identify unoptimized images

5. **Caching**
   - Check fetch() cache options
   - Look for missing revalidation strategies
   - Identify static vs dynamic content

### Step 2: Apply Skills

Use relevant skills to understand best practices:
- `server-components` - For component boundary optimization
- `app-router` - For routing and layout optimization
- `route-handlers` - For API optimization
- `server-actions` - For mutation optimization

### Step 3: Generate Report

Create an optimization report covering:

## Optimization Categories

### 1. Server/Client Component Boundaries

**Check for:**
- Client components that don't use hooks or browser APIs
- Large component trees under 'use client'
- Data fetching in client components

**Recommendations:**
- Move data fetching to server components
- Push 'use client' boundaries down
- Pass server data as props to client components

### 2. Data Fetching Patterns

**Check for:**
- Sequential await statements
- fetch() without cache options
- Missing generateStaticParams

**Recommendations:**
```tsx
// Before: Sequential
const user = await getUser()
const posts = await getPosts()

// After: Parallel
const [user, posts] = await Promise.all([
  getUser(),
  getPosts(),
])
```

### 3. Bundle Optimization

**Check for:**
- Large npm packages in client components
- Missing dynamic imports
- Unused exports

**Recommendations:**
```tsx
// Dynamic import for client-only libraries
const Chart = dynamic(() => import('./Chart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
})
```

### 4. Image Optimization

**Check for:**
- `<img>` instead of `<Image>`
- Missing blur placeholders
- Unoptimized formats

**Recommendations:**
```tsx
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority // For above-the-fold images
  placeholder="blur"
/>
```

### 5. Caching Strategy

**Check for:**
- Missing cache directives
- No revalidation configuration
- Overly dynamic pages

**Recommendations:**
```tsx
// Cache with revalidation
const data = await fetch(url, {
  next: { revalidate: 3600 }, // 1 hour
})

// Tag-based revalidation
const data = await fetch(url, {
  next: { tags: ['products'] },
})
```

### 6. Loading States

**Check for:**
- Missing loading.tsx files
- No Suspense boundaries
- Blocking renders

**Recommendations:**
- Add loading.tsx for route segments
- Wrap slow components in Suspense
- Use streaming for large pages

## Output Format

After analysis, provide:

1. **Summary**: Overall performance assessment
2. **High Priority**: Issues with biggest impact
3. **Quick Wins**: Easy fixes with good returns
4. **Code Changes**: Specific file changes needed
5. **Metrics**: Expected improvements

## Example Report

```
## Performance Analysis Report

### Summary
Found 5 high-priority and 8 medium-priority optimization opportunities.

### High Priority Issues

1. **Large Client Boundary** (app/dashboard/page.tsx)
   - Impact: High
   - Issue: Entire dashboard is client-rendered
   - Fix: Split into server/client components

2. **Sequential Data Fetching** (app/products/page.tsx)
   - Impact: High
   - Issue: 3 sequential await calls
   - Fix: Use Promise.all()

### Quick Wins

1. Add loading.tsx to /dashboard
2. Convert 12 <img> tags to <Image>
3. Add cache options to 8 fetch() calls

### Estimated Impact
- Bundle size: -15%
- TTFB: -200ms
- LCP: -500ms
```
