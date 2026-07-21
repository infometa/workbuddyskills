# Design Principles

Core visual design principles with code examples demonstrating proper implementation.

## 1. Visual Hierarchy

Guide the eye through content in order of importance.

```html
<!-- ❌ BAD: Everything same weight -->
<div class="p-8">
  <p class="text-lg">Welcome</p>
  <p class="text-lg">Build amazing products with our platform</p>
  <p class="text-lg">Get Started</p>
</div>

<!-- ✅ GOOD: Clear hierarchy -->
<div class="p-8">
  <p class="text-sm uppercase tracking-widest text-gray-500">Welcome</p>
  <h1 class="text-5xl font-bold mt-2">Build amazing products</h1>
  <p class="text-xl text-gray-600 mt-4">with our platform</p>
  <button class="mt-8 bg-black text-white px-8 py-3">Get Started</button>
</div>
```

**Key techniques:**
- Size difference between levels (1.5x+ ratio)
- Weight contrast (bold headers, regular body)
- Color contrast (primary vs muted)
- Spatial grouping

## 2. Alignment

Create visual connections through consistent alignment.

```html
<!-- ❌ BAD: Inconsistent alignment -->
<div class="p-8">
  <h2 class="text-center">Features</h2>
  <p class="text-left">Feature description here</p>
  <button class="mx-auto block">Learn More</button>
</div>

<!-- ✅ GOOD: Consistent left alignment -->
<div class="p-8">
  <h2 class="text-left">Features</h2>
  <p class="text-left">Feature description here</p>
  <button class="text-left">Learn More</button>
</div>
```

**Key techniques:**
- Pick one alignment per section
- Use grid/flexbox for consistent alignment
- Align elements to invisible lines
- Headers and their content share alignment

## 3. Contrast

Make important elements stand out.

```html
<!-- ❌ BAD: Low contrast, hard to read -->
<div class="bg-gray-100 p-8">
  <h2 class="text-gray-400">Features</h2>
  <button class="bg-gray-200 text-gray-500 px-6 py-2">Click</button>
</div>

<!-- ✅ GOOD: High contrast, clear focus -->
<div class="bg-white p-8">
  <h2 class="text-gray-900">Features</h2>
  <button class="bg-black text-white px-6 py-2">Click</button>
</div>
```

**Key techniques:**
- Dark on light or light on dark
- One high-contrast CTA per section
- Use color for emphasis, not decoration
- Minimum 4.5:1 ratio for text

## 4. White Space

Give elements room to breathe.

```html
<!-- ❌ BAD: Cramped, claustrophobic -->
<div class="p-2">
  <h2 class="mb-1">Title</h2>
  <p class="mb-1">Description text here</p>
  <button class="mb-1">Action</button>
</div>

<!-- ✅ GOOD: Generous spacing -->
<div class="p-12 md:p-24">
  <h2 class="mb-6">Title</h2>
  <p class="mb-8 max-w-2xl">Description text here</p>
  <button class="mt-4">Action</button>
</div>
```

**Key techniques:**
- Generous padding (p-8 minimum for sections)
- Max-width for readability (max-w-prose)
- Vertical rhythm with consistent spacing scale
- Let elements breathe

## 5. Proximity

Group related elements together.

```html
<!-- ❌ BAD: Equal spacing everywhere -->
<div class="space-y-4">
  <h3>Feature Title</h3>
  <p>Feature description</p>
  <a href="#">Learn more</a>
  <h3>Another Feature</h3>
  <p>Another description</p>
  <a href="#">Learn more</a>
</div>

<!-- ✅ GOOD: Grouped by relationship -->
<div class="space-y-12">
  <div class="space-y-3">
    <h3>Feature Title</h3>
    <p>Feature description</p>
    <a href="#">Learn more</a>
  </div>
  <div class="space-y-3">
    <h3>Another Feature</h3>
    <p>Another description</p>
    <a href="#">Learn more</a>
  </div>
</div>
```

**Key techniques:**
- Related items closer together
- Unrelated items further apart
- Use cards/containers to reinforce grouping
- Visual separation between sections

## 6. Repetition

Create consistency through repeated patterns.

```html
<!-- ❌ BAD: Inconsistent card styles -->
<div class="grid grid-cols-3 gap-4">
  <div class="bg-white p-4 rounded shadow">Card 1</div>
  <div class="bg-gray-100 p-8 border">Card 2</div>
  <div class="bg-white p-6 rounded-2xl">Card 3</div>
</div>

<!-- ✅ GOOD: Consistent pattern -->
<div class="grid grid-cols-3 gap-6">
  <div class="bg-white p-6 rounded-lg border border-gray-200">Card 1</div>
  <div class="bg-white p-6 rounded-lg border border-gray-200">Card 2</div>
  <div class="bg-white p-6 rounded-lg border border-gray-200">Card 3</div>
</div>
```

**Key techniques:**
- Same styling for same element types
- Consistent spacing scale (4, 8, 12, 16, 24)
- Repeated visual motifs
- Design system thinking

## 7. Unity

Create cohesive designs where all elements belong.

```html
<!-- ❌ BAD: Mixed styles, no cohesion -->
<div>
  <h1 class="font-serif text-4xl">Welcome</h1>
  <button class="font-mono bg-gradient-to-r from-pink-500 to-yellow-500 rounded-full">
    Click
  </button>
  <p class="font-sans text-gray-600">Some text</p>
</div>

<!-- ✅ GOOD: Unified design language -->
<div>
  <h1 class="font-display text-4xl text-gray-900">Welcome</h1>
  <button class="font-display bg-gray-900 text-white rounded">
    Click
  </button>
  <p class="font-body text-gray-600">Some text</p>
</div>
```

**Key techniques:**
- Limited font families (2 max)
- Consistent color palette
- Unified border radius
- Cohesive icon style

## 8. Balance

Distribute visual weight evenly.

```html
<!-- ❌ BAD: All weight on left -->
<div class="flex justify-between items-center">
  <div>
    <img src="logo.svg" class="h-12">
    <h1 class="text-4xl font-bold">Company</h1>
    <p class="text-xl">Tagline here</p>
  </div>
  <a href="#" class="text-sm">Link</a>
</div>

<!-- ✅ GOOD: Balanced weight -->
<div class="flex justify-between items-center">
  <div class="flex items-center gap-4">
    <img src="logo.svg" class="h-8">
    <span class="text-xl font-medium">Company</span>
  </div>
  <nav class="flex gap-8 items-center">
    <a href="#">Products</a>
    <a href="#">About</a>
    <button class="bg-black text-white px-4 py-2">Contact</button>
  </nav>
</div>
```

**Key techniques:**
- Distribute heavy elements
- Use asymmetrical balance for interest
- Consider visual weight of colors
- Balance positive and negative space

## 9. Scale

Use size to show importance and create rhythm.

```html
<!-- ❌ BAD: Monotonous sizing -->
<div>
  <h1 class="text-2xl">Title</h1>
  <h2 class="text-xl">Subtitle</h2>
  <p class="text-lg">Body text</p>
</div>

<!-- ✅ GOOD: Dramatic scale differences -->
<div>
  <h1 class="text-6xl md:text-8xl font-bold tracking-tight">Title</h1>
  <h2 class="text-xl text-gray-500 mt-4">Subtitle</h2>
  <p class="text-base mt-8">Body text</p>
</div>
```

**Key techniques:**
- Large scale differences (not incremental)
- Use scale for emphasis
- Responsive scaling with breakpoints
- Consider viewing context

## 10. Color Theory

Use color intentionally.

```html
<!-- ❌ BAD: Too many colors -->
<div class="bg-purple-100">
  <h1 class="text-pink-600">Title</h1>
  <p class="text-green-500">Description</p>
  <button class="bg-orange-500 text-yellow-300">Click</button>
</div>

<!-- ✅ GOOD: Intentional palette -->
<div class="bg-gray-50">
  <h1 class="text-gray-900">Title</h1>
  <p class="text-gray-600">Description</p>
  <button class="bg-indigo-600 text-white">Click</button>
</div>
```

**Key techniques:**
- 60-30-10 rule (dominant, secondary, accent)
- One accent color for CTAs
- Use grays for most text
- Color has meaning (red=error, green=success)

## 11. Typography

Type is the foundation of design.

```html
<!-- ❌ BAD: Poor typography -->
<p class="text-sm leading-none tracking-normal">
  This is a long paragraph of text that's hard to read because the
  line height is too tight and the font size is too small.
</p>

<!-- ✅ GOOD: Readable typography -->
<p class="text-lg leading-relaxed tracking-normal max-w-prose">
  This is a long paragraph of text that's easy to read because the
  line height is comfortable and the font size is appropriate.
</p>
```

**Key techniques:**
- 16px minimum for body text
- 1.5-1.75 line height for body
- Max 75 characters per line
- Letter-spacing for all-caps

## 12. Depth

Create visual layers.

```html
<!-- ❌ BAD: Flat, no depth -->
<div class="bg-white">
  <div class="bg-white border">Card</div>
</div>

<!-- ✅ GOOD: Layered depth -->
<div class="bg-gray-100">
  <div class="bg-white shadow-lg rounded-xl p-8">
    <div class="bg-gray-50 p-4 rounded-lg">Nested</div>
  </div>
</div>
```

**Key techniques:**
- Background color differentiation
- Strategic shadow usage
- Z-index layering
- Blur effects for depth

## 13. Motion

Animation should enhance, not distract.

```html
<!-- ❌ BAD: Gratuitous animation -->
<button class="animate-bounce animate-pulse bg-gradient-to-r animate-spin">
  Click Me!
</button>

<!-- ✅ GOOD: Purposeful motion -->
<button class="transition-all duration-200 hover:scale-105 hover:shadow-lg
               focus:ring-2 focus:ring-offset-2 focus:ring-black">
  Click Me
</button>

<style>
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
```

**Key techniques:**
- Animate interactions (hover, focus)
- Keep animations under 300ms
- Respect prefers-reduced-motion
- Motion should have purpose
