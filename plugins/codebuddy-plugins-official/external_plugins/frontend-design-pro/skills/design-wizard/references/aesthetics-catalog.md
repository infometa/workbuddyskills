# Aesthetics Catalog

Comprehensive catalog of design aesthetics with characteristics and code examples.

---

## Modern Aesthetics

### Dark & Premium

**Characteristics:**
- Black/dark gray backgrounds (#0a0a0a, #121212)
- High-contrast white or cream text
- Accent color sparingly used
- Large typography
- Generous white space
- Subtle gradients or noise textures

**Best for:** SaaS, fintech, luxury brands, developer tools

```html
<!-- Dark & Premium Example -->
<section class="bg-[#0a0a0a] min-h-screen px-8 py-24">
  <div class="max-w-6xl mx-auto">
    <h1 class="text-white text-6xl md:text-8xl font-bold tracking-tight">
      Build something
      <span class="text-[#ff6b35]">worth building</span>
    </h1>
    <p class="text-gray-400 text-xl mt-8 max-w-2xl">
      Enterprise-grade infrastructure for teams that ship fast.
    </p>
    <div class="flex gap-4 mt-12">
      <button class="bg-white text-black px-8 py-4 font-medium">
        Start free
      </button>
      <button class="border border-gray-700 text-white px-8 py-4">
        View demos
      </button>
    </div>
  </div>
</section>
```

---

### Glassmorphism

**Characteristics:**
- Frosted glass effect (backdrop-blur)
- Semi-transparent backgrounds
- Subtle borders
- Gradient backgrounds behind glass
- Light and airy feel

**Best for:** Dashboards, mobile apps, creative portfolios

```html
<!-- Glassmorphism Example -->
<section class="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 p-8">
  <div class="max-w-lg mx-auto">
    <div class="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl p-8">
      <h2 class="text-white text-3xl font-semibold">Welcome back</h2>
      <p class="text-white/70 mt-2">Sign in to continue</p>
      <div class="mt-8 space-y-4">
        <input
          type="email"
          placeholder="Email"
          class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/50"
        >
        <button class="w-full bg-white text-gray-900 rounded-xl py-3 font-medium">
          Continue
        </button>
      </div>
    </div>
  </div>
</section>
```

---

### Neobrutalism

**Characteristics:**
- Bold black borders (2-4px)
- Flat colors (no gradients)
- Hard drop shadows (offset, no blur)
- Raw, unpolished aesthetic
- Strong typography
- High contrast

**Best for:** Creative agencies, portfolios, startups wanting to stand out

```html
<!-- Neobrutalism Example -->
<section class="bg-[#ffe951] min-h-screen p-8">
  <div class="max-w-4xl mx-auto">
    <div class="bg-white border-4 border-black shadow-[8px_8px_0_0_#000] p-8">
      <h1 class="text-6xl font-black uppercase tracking-tight">
        No fluff.<br>Just work.
      </h1>
      <p class="text-xl mt-6 font-medium">
        We build products that people actually use.
      </p>
      <button class="mt-8 bg-black text-white px-8 py-4 font-bold uppercase
                     border-4 border-black hover:bg-white hover:text-black
                     transition-colors">
        See Projects
      </button>
    </div>
  </div>
</section>
```

---

### Bento Grid

**Characteristics:**
- Grid-based layout
- Cards of varying sizes
- Consistent gaps
- Feature highlights in larger cells
- Often paired with dark mode

**Best for:** Feature showcases, dashboards, product pages

```html
<!-- Bento Grid Example -->
<section class="bg-gray-950 p-8">
  <div class="max-w-6xl mx-auto grid grid-cols-4 gap-4 auto-rows-[200px]">
    <!-- Large feature card -->
    <div class="col-span-2 row-span-2 bg-gradient-to-br from-violet-600 to-purple-700 rounded-3xl p-8 flex flex-col justify-end">
      <h3 class="text-white text-3xl font-bold">AI-Powered Analysis</h3>
      <p class="text-white/70 mt-2">Understand your data in seconds</p>
    </div>

    <!-- Small cards -->
    <div class="bg-gray-900 rounded-3xl p-6 border border-gray-800">
      <div class="text-4xl">99.9%</div>
      <div class="text-gray-400 mt-2">Uptime</div>
    </div>

    <div class="bg-gray-900 rounded-3xl p-6 border border-gray-800">
      <div class="text-4xl">50ms</div>
      <div class="text-gray-400 mt-2">Latency</div>
    </div>

    <!-- Wide card -->
    <div class="col-span-2 bg-gray-900 rounded-3xl p-6 border border-gray-800">
      <h4 class="text-xl font-semibold text-white">Integrations</h4>
      <div class="flex gap-4 mt-4">
        <!-- Integration icons -->
      </div>
    </div>
  </div>
</section>
```

---

## Retro Aesthetics

### Brutalist/Editorial

**Characteristics:**
- Strong typographic hierarchy
- Serif fonts for headlines
- Asymmetric layouts
- High contrast black/white
- Magazine-inspired
- Dense content layouts

**Best for:** Editorial, blogs, news, agencies

```html
<!-- Brutalist/Editorial Example -->
<section class="bg-white min-h-screen">
  <div class="grid grid-cols-12 min-h-screen">
    <!-- Left column -->
    <div class="col-span-4 border-r border-black p-8">
      <div class="text-sm uppercase tracking-widest">Issue 47</div>
      <div class="text-sm mt-4">Winter 2024</div>
    </div>

    <!-- Main content -->
    <div class="col-span-8 p-8">
      <h1 class="font-serif text-[120px] leading-none tracking-tight">
        The Future
      </h1>
      <h2 class="font-serif text-[80px] leading-none text-gray-400">
        is Unwritten
      </h2>
      <div class="mt-16 max-w-2xl">
        <p class="text-xl leading-relaxed font-serif">
          An exploration of what comes next in design, technology, and culture.
        </p>
      </div>
    </div>
  </div>
</section>
```

---

### Y2K/Cyber

**Characteristics:**
- Neon colors (cyan, magenta, lime)
- Dark backgrounds
- Glitch effects
- Tech/matrix aesthetics
- Metallic gradients
- Futuristic typography

**Best for:** Gaming, music, tech startups, events

```html
<!-- Y2K/Cyber Example -->
<section class="bg-black min-h-screen p-8 overflow-hidden">
  <div class="max-w-6xl mx-auto relative">
    <!-- Glow effects -->
    <div class="absolute top-20 left-20 w-96 h-96 bg-cyan-500/20 rounded-full blur-[100px]"></div>
    <div class="absolute bottom-20 right-20 w-96 h-96 bg-fuchsia-500/20 rounded-full blur-[100px]"></div>

    <h1 class="font-mono text-7xl font-bold text-transparent bg-clip-text
               bg-gradient-to-r from-cyan-400 via-fuchsia-500 to-cyan-400
               relative z-10">
      ENTER_THE_VOID
    </h1>
    <p class="font-mono text-cyan-400/70 text-xl mt-6">
      // Initialize sequence 2024.12.01
    </p>
    <button class="mt-12 border-2 border-cyan-400 text-cyan-400 px-8 py-4
                   font-mono uppercase hover:bg-cyan-400 hover:text-black
                   transition-all relative z-10">
      [CONNECT]
    </button>
  </div>
</section>
```

---

## Cultural Aesthetics

### Swiss Typography

**Characteristics:**
- Grid-based layouts
- Sans-serif typography (Helvetica, Neue Haas)
- Strong alignment
- Minimal color (often black, white, red)
- Mathematical precision
- Lots of white space

**Best for:** Corporate, design agencies, minimal brands

```html
<!-- Swiss Typography Example -->
<section class="bg-white min-h-screen p-16">
  <div class="grid grid-cols-12 gap-8">
    <div class="col-span-4">
      <div class="text-red-600 text-sm font-medium uppercase tracking-wider">
        Principles
      </div>
    </div>
    <div class="col-span-8">
      <h1 class="text-7xl font-light leading-tight tracking-tight">
        Form follows
        <span class="font-bold">function</span>
      </h1>
      <div class="mt-16 grid grid-cols-2 gap-16">
        <div>
          <div class="w-12 h-0.5 bg-black mb-6"></div>
          <p class="text-lg leading-relaxed">
            Good design is as little design as possible. Less, but better.
          </p>
        </div>
        <div>
          <div class="w-12 h-0.5 bg-black mb-6"></div>
          <p class="text-lg leading-relaxed">
            Making a design simple is about subtracting the obvious.
          </p>
        </div>
      </div>
    </div>
  </div>
</section>
```

---

### Scandinavian Minimal

**Characteristics:**
- Warm off-white backgrounds (#faf8f5)
- Natural, muted colors
- Clean sans-serif fonts
- Rounded elements
- Cozy, inviting feel
- Nature-inspired accents

**Best for:** Lifestyle, wellness, home goods, sustainable brands

```html
<!-- Scandinavian Minimal Example -->
<section class="bg-[#faf8f5] min-h-screen p-8">
  <div class="max-w-5xl mx-auto py-24">
    <h1 class="text-5xl font-light text-gray-800 leading-tight">
      Simple things,<br>
      <span class="text-gray-400">done well</span>
    </h1>
    <p class="text-xl text-gray-500 mt-8 max-w-xl">
      Thoughtfully designed objects for everyday living.
    </p>
    <div class="mt-16 grid grid-cols-3 gap-8">
      <div class="aspect-square bg-[#e8e4de] rounded-2xl"></div>
      <div class="aspect-square bg-[#d4cec4] rounded-2xl"></div>
      <div class="aspect-square bg-[#c0b8ac] rounded-2xl"></div>
    </div>
  </div>
</section>
```

---

### Japanese Zen

**Characteristics:**
- Extreme minimalism
- Asymmetric balance
- Nature elements
- Subtle textures
- Muted, earthy colors
- Meditative white space

**Best for:** Wellness, luxury, hospitality, art

```html
<!-- Japanese Zen Example -->
<section class="bg-stone-50 min-h-screen flex items-center justify-center">
  <div class="text-center px-8">
    <div class="w-px h-24 bg-stone-300 mx-auto"></div>
    <h1 class="text-4xl font-light tracking-[0.2em] text-stone-700 mt-12">
      STILLNESS
    </h1>
    <p class="text-stone-400 mt-6 tracking-wide">
      Find peace in simplicity
    </p>
    <div class="w-px h-24 bg-stone-300 mx-auto mt-12"></div>
  </div>
</section>
```

---

## Stripped-Down Aesthetics

### Statement Hero

**Characteristics:**
- One bold statement
- Massive typography
- Minimal supporting elements
- Clear single CTA
- Maximum impact

**Best for:** Launch pages, artist sites, bold brands

```html
<!-- Statement Hero Example -->
<section class="bg-black min-h-screen flex flex-col justify-center px-8">
  <div class="max-w-7xl">
    <h1 class="text-[15vw] font-black text-white leading-[0.85] tracking-tighter">
      MAKE
      <br>
      <span class="text-[#ff0000]">NOISE</span>
    </h1>
    <button class="mt-16 text-white border-b-2 border-white pb-1 text-xl
                   hover:text-[#ff0000] hover:border-[#ff0000] transition-colors">
      Enter
    </button>
  </div>
</section>
```

---

### Type-Only

**Characteristics:**
- No images
- Typography is the design
- Creative type treatments
- High readability
- Content-focused

**Best for:** Writers, agencies, minimal portfolios

```html
<!-- Type-Only Example -->
<section class="bg-white min-h-screen p-8">
  <div class="max-w-4xl mx-auto py-24">
    <h1 class="text-8xl font-serif font-bold leading-tight">
      Words
      <em class="font-light">matter</em>
    </h1>
    <div class="mt-24 space-y-8 text-2xl font-serif leading-relaxed">
      <p>
        Every word carries weight. Every sentence has purpose.
      </p>
      <p class="text-gray-400">
        We craft language that moves people to action.
      </p>
    </div>
  </div>
</section>
```

---

## Choosing an Aesthetic

| Aesthetic | Energy | Audience | Best For |
|-----------|--------|----------|----------|
| Dark & Premium | Professional, sophisticated | Enterprise, developers | SaaS, fintech |
| Glassmorphism | Modern, fresh | Tech-savvy | Dashboards, apps |
| Neobrutalism | Bold, rebellious | Young, creative | Startups, portfolios |
| Bento Grid | Organized, feature-rich | Product users | Feature pages |
| Editorial | Intellectual, curated | Readers | Blogs, magazines |
| Y2K/Cyber | Energetic, futuristic | Gamers, youth | Gaming, events |
| Swiss | Clean, trustworthy | Professionals | Corporate, agencies |
| Scandinavian | Warm, inviting | Lifestyle | Wellness, home |
| Japanese Zen | Calm, refined | Art lovers | Luxury, hospitality |
| Statement Hero | Bold, memorable | General | Launch pages |
| Type-Only | Intellectual | Writers | Portfolios, agencies |
