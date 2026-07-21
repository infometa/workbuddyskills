# Anti-Patterns

Design patterns to avoid. These make designs look generic, dated, or like "AI slop."

---

## 1. Hero Badges/Pills

**The Problem:** Small tags above headlines like "New", "AI-Powered", "Introducing" scream generic template.

```html
<!-- ❌ BAD: Hero badge -->
<div class="text-center py-24">
  <span class="bg-purple-100 text-purple-800 px-4 py-1 rounded-full text-sm font-medium">
    ✨ AI-Powered
  </span>
  <h1 class="text-5xl font-bold mt-6">
    Welcome to Our Platform
  </h1>
</div>

<!-- ✅ GOOD: Direct statement -->
<div class="py-24">
  <h1 class="text-7xl font-bold tracking-tight">
    Ship faster with AI
  </h1>
  <p class="text-xl text-gray-600 mt-6 max-w-2xl">
    Code review, documentation, and deployment—automated.
  </p>
</div>
```

**Why it's bad:**
- Every AI startup uses this pattern
- Adds visual noise before the actual message
- Often contains buzzwords
- Makes the design instantly forgettable

**Alternatives:**
- Lead with the headline
- Use subheadings for context
- Show, don't tell (demo the feature)

---

## 2. Generic Fonts

**The Problem:** Inter, Roboto, Arial, Open Sans, and system-ui make designs blend together.

```html
<!-- ❌ BAD: Generic fonts -->
<h1 class="font-sans text-4xl">
  Welcome to Our App
</h1>
<p class="font-sans text-gray-600">
  The best way to manage your workflow.
</p>

<!-- ✅ GOOD: Distinctive typography -->
<h1 class="font-['Instrument_Serif'] text-5xl tracking-tight">
  Welcome to Our App
</h1>
<p class="font-['Outfit'] text-gray-600">
  The best way to manage your workflow.
</p>
```

**Overused fonts to avoid:**
- Inter (the default AI font)
- Roboto
- Open Sans
- Arial/Helvetica (unless doing Swiss)
- system-ui/sans-serif
- Lato, Poppins (overexposed)

**Better alternatives:**
- **Display:** Instrument Serif, Fraunces, Clash Display, Cabinet Grotesk
- **Body:** Outfit, Satoshi, General Sans, Plus Jakarta Sans
- **Mono:** JetBrains Mono, Fira Code, IBM Plex Mono

---

## 3. Purple/Blue Gradients on White

**The Problem:** The default "tech startup" look.

```html
<!-- ❌ BAD: Generic gradient -->
<section class="bg-white py-24">
  <h1 class="text-5xl font-bold text-transparent bg-clip-text
             bg-gradient-to-r from-purple-600 to-blue-500">
    Build the Future
  </h1>
  <button class="bg-gradient-to-r from-purple-600 to-blue-500 text-white px-8 py-4 rounded-full">
    Get Started
  </button>
</section>

<!-- ✅ GOOD: Distinctive color choice -->
<section class="bg-[#0a0a0a] py-24">
  <h1 class="text-5xl font-bold text-white">
    Build the <span class="text-[#ff6b35]">Future</span>
  </h1>
  <button class="bg-[#ff6b35] text-black px-8 py-4 font-medium">
    Get Started
  </button>
</section>
```

**Why it's bad:**
- Every SaaS landing page uses purple-blue
- Creates instant "template" recognition
- Shows no brand thinking

**Alternatives:**
- Single bold accent color
- Dark mode with contrast
- Warm neutrals with one pop color
- Monochromatic schemes

---

## 4. Generic Geometric Shapes

**The Problem:** Abstract blobs, circles, and geometric decorations.

```html
<!-- ❌ BAD: Generic decorative shapes -->
<section class="relative bg-white py-24">
  <!-- Decorative blobs -->
  <div class="absolute top-0 right-0 w-96 h-96 bg-purple-200 rounded-full blur-3xl opacity-50"></div>
  <div class="absolute bottom-0 left-0 w-72 h-72 bg-blue-200 rounded-full blur-3xl opacity-50"></div>

  <h1 class="relative z-10">Welcome</h1>
</section>

<!-- ✅ GOOD: Intentional visual treatment -->
<section class="bg-[#f5f5f0] py-24">
  <div class="border-l-4 border-black pl-8">
    <h1>Welcome</h1>
  </div>
</section>
```

**Patterns to avoid:**
- Background gradient blobs
- Floating circles/squares
- Abstract line decorations
- Generic mesh gradients
- Scattered geometric shapes

**Alternatives:**
- No decoration (let typography work)
- Intentional borders/lines
- Grid patterns with purpose
- Photography (if relevant)
- Custom illustrations (if budget allows)

---

## 5. Excessive Rounded Corners

**The Problem:** Everything is a pill or has rounded-3xl.

```html
<!-- ❌ BAD: Over-rounded everything -->
<div class="rounded-3xl bg-gray-100 p-8">
  <button class="rounded-full bg-gray-200 px-6 py-3">
    Click
  </button>
  <div class="rounded-2xl bg-white mt-4 p-4">
    <span class="rounded-full bg-gray-100 px-3 py-1">Tag</span>
  </div>
</div>

<!-- ✅ GOOD: Intentional border radius -->
<div class="bg-gray-100 p-8">
  <button class="rounded bg-black text-white px-6 py-3">
    Click
  </button>
  <div class="bg-white mt-4 p-4 rounded-lg">
    <span class="bg-gray-100 px-3 py-1 rounded">Tag</span>
  </div>
</div>
```

**The problem:**
- Looks like iOS/Apple copy
- Removes visual interest
- Everything looks the same
- Feels soft/uncommitted

**Alternatives:**
- Mix rounded and sharp
- Use sharp corners for contrast
- Reserve rounded for interactive elements
- Match brand personality

---

## 6. Template Layouts

**The Problem:** Hero → Features Grid → Testimonials → CTA → Footer

```html
<!-- ❌ BAD: Predictable template structure -->
<section class="text-center py-24">
  <span class="badge">New</span>
  <h1>Welcome to Our Platform</h1>
  <p>The best solution for your needs</p>
  <button>Get Started</button>
</section>

<section class="grid grid-cols-3 gap-8 py-24">
  <div class="card">Feature 1</div>
  <div class="card">Feature 2</div>
  <div class="card">Feature 3</div>
</section>

<section class="py-24">
  <h2>What People Say</h2>
  <!-- Testimonial cards -->
</section>

<section class="text-center py-24 bg-purple-600">
  <h2>Ready to Start?</h2>
  <button>Sign Up Now</button>
</section>

<!-- ✅ GOOD: Unexpected structure -->
<section class="min-h-screen grid grid-cols-2">
  <div class="bg-black p-16 flex items-end">
    <h1 class="text-white text-6xl">We build things</h1>
  </div>
  <div class="bg-[#ff6b35] p-16 flex items-center">
    <p class="text-2xl">that actually work.</p>
  </div>
</section>

<section class="py-32">
  <div class="max-w-xl mx-auto space-y-24">
    <!-- Scrolling case studies, not feature cards -->
  </div>
</section>
```

**Predictable patterns to break:**
- Centered hero with badge
- 3-column feature grid
- Testimonial carousel
- Purple CTA section
- Standard footer layout

**Alternatives:**
- Asymmetric layouts
- Single-column narrative
- Case study focus
- Interactive elements
- Unexpected section breaks

---

## 7. Generic Copy Patterns

**The Problem:** Template language that could apply to anything.

```html
<!-- ❌ BAD: Generic copy -->
<section>
  <h1>The All-in-One Platform for Your Business</h1>
  <p>Streamline your workflow and boost productivity with our cutting-edge solution.</p>
  <button>Start Your Free Trial</button>
</section>

<!-- ✅ GOOD: Specific, opinionated copy -->
<section>
  <h1>Stop drowning in spreadsheets</h1>
  <p>One dashboard. Every metric. Updated in real-time.</p>
  <button>See your data</button>
</section>
```

**Phrases to avoid:**
- "All-in-one platform"
- "Boost productivity"
- "Streamline workflow"
- "Cutting-edge solution"
- "Transform your business"
- "Next-generation"
- "Seamless integration"
- "Start your free trial"

**Better approaches:**
- State the specific problem
- Show the transformation
- Use concrete language
- Be opinionated

---

## 8. Overused Stock Imagery

**The Problem:** Happy people pointing at screens, diverse teams laughing.

**Patterns to avoid:**
- People pointing at laptops
- Diverse team in modern office
- Hands typing on keyboard
- Abstract 3D shapes
- Generic dashboard screenshots
- Handshakes

**Alternatives:**
- No images (type-only)
- Custom photography
- Actual product screenshots
- Abstract but branded graphics
- Illustrations (if distinctive)

---

## 9. Dark Mode Clichés

**The Problem:** Dark mode done wrong.

```html
<!-- ❌ BAD: Poor dark mode -->
<section class="bg-gray-900">
  <h1 class="text-gray-300">Title</h1> <!-- Too low contrast -->
  <p class="text-gray-500">Description</p> <!-- Unreadable -->
  <div class="bg-gray-800 border border-gray-700"> <!-- Boring stacking -->
    Content
  </div>
</section>

<!-- ✅ GOOD: Intentional dark design -->
<section class="bg-[#0a0a0a]">
  <h1 class="text-white">Title</h1>
  <p class="text-gray-400">Description</p>
  <div class="bg-gradient-to-b from-white/5 to-transparent border border-white/10 rounded-2xl">
    Content
  </div>
</section>
```

**Dark mode anti-patterns:**
- Pure #000000 black
- Gray-on-gray stacking
- Low contrast text
- No accent colors
- Boring, flat appearance

**Better dark mode:**
- Use #0a0a0a or #121212
- High contrast white text
- Subtle gradients and borders
- One strong accent color
- Depth through transparency

---

## 10. Animation Abuse

**The Problem:** Animations that distract rather than enhance.

```html
<!-- ❌ BAD: Gratuitous animation -->
<button class="animate-bounce animate-pulse bg-gradient-to-r from-purple-500 to-pink-500">
  Click Me!!!
</button>

<div class="animate-spin">
  <svg>...</svg> <!-- Spinning icon for no reason -->
</div>

<!-- ✅ GOOD: Purposeful motion -->
<button class="transition-transform duration-200 hover:scale-105 focus:ring-2">
  Click Me
</button>

<style>
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
```

**Animation anti-patterns:**
- Bouncing CTAs
- Spinning logos
- Pulsing elements
- Fade-in-up on scroll (overused)
- Parallax everything

**Better animation:**
- Subtle hover states
- Focus indicators
- Page transitions
- Loading states
- Micro-interactions

---

## Quick Checklist

Before finalizing any design, check:

- [ ] No hero badges/pills above headlines
- [ ] No Inter, Roboto, Arial fonts
- [ ] No purple-blue gradients on white
- [ ] No decorative blob shapes
- [ ] No uniform rounded-3xl everywhere
- [ ] No predictable Hero→Features→Testimonials layout
- [ ] No generic "boost productivity" copy
- [ ] No stock photo clichés
- [ ] No low-contrast dark mode
- [ ] No gratuitous animations
