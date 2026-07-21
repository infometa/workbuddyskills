# Accessibility Guidelines

WCAG 2.1 AA/AAA compliance guidelines for frontend designs.

---

## Color Contrast

### Text Contrast Requirements

| Text Type | Minimum Ratio | WCAG Level |
|-----------|---------------|------------|
| Normal text (<18px) | 4.5:1 | AA |
| Large text (18px+ or 14px bold) | 3:1 | AA |
| Normal text (enhanced) | 7:1 | AAA |
| UI components & graphics | 3:1 | AA |

### Checking Contrast

```html
<!-- ❌ BAD: Low contrast (2.5:1) -->
<p class="text-gray-400 bg-white">Hard to read text</p>

<!-- ✅ GOOD: Sufficient contrast (7:1) -->
<p class="text-gray-700 bg-white">Easy to read text</p>

<!-- ❌ BAD: Low contrast on dark -->
<p class="text-gray-600 bg-gray-900">Hard to read</p>

<!-- ✅ GOOD: High contrast on dark -->
<p class="text-gray-300 bg-gray-900">Easy to read</p>
```

### Common Safe Combinations

**Light backgrounds:**
- `bg-white` + `text-gray-900` (21:1)
- `bg-white` + `text-gray-700` (7.5:1)
- `bg-gray-50` + `text-gray-800` (10:1)

**Dark backgrounds:**
- `bg-gray-900` + `text-white` (16:1)
- `bg-black` + `text-gray-300` (10:1)
- `bg-gray-950` + `text-gray-100` (14:1)

### Don't Rely on Color Alone

```html
<!-- ❌ BAD: Color only indicates error -->
<input class="border-red-500" />
<p class="text-red-500">Invalid email</p>

<!-- ✅ GOOD: Color + icon + text -->
<input class="border-red-500" aria-invalid="true" aria-describedby="email-error" />
<p id="email-error" class="text-red-600 flex items-center gap-2">
  <svg aria-hidden="true"><!-- Error icon --></svg>
  Invalid email address
</p>
```

---

## Focus States

### Visible Focus Required

```html
<!-- ❌ BAD: Removing focus outline -->
<button class="focus:outline-none">Click</button>

<style>
  *:focus { outline: none; } /* NEVER DO THIS */
</style>

<!-- ✅ GOOD: Enhanced focus states -->
<button class="focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-600">
  Click
</button>

<!-- Alternative: Custom focus style -->
<button class="focus:outline-2 focus:outline-offset-2 focus:outline-black">
  Click
</button>
```

### Focus Ring Patterns

```css
/* Good focus ring for light mode */
.focus-ring-light:focus {
  outline: 2px solid #1a1a1a;
  outline-offset: 2px;
}

/* Good focus ring for dark mode */
.focus-ring-dark:focus {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}

/* Focus ring with brand color */
.focus-ring-brand:focus {
  outline: none;
  box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px #3b82f6;
}
```

### Focus Within for Containers

```html
<div class="border border-gray-200 rounded-lg p-4
            focus-within:ring-2 focus-within:ring-blue-500">
  <input type="text" class="focus:outline-none" />
</div>
```

---

## Semantic HTML

### Proper Document Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Descriptive Page Title | Site Name</title>
</head>
<body>
  <a href="#main-content" class="sr-only focus:not-sr-only">
    Skip to main content
  </a>

  <header role="banner">
    <nav aria-label="Main navigation">
      <!-- Navigation links -->
    </nav>
  </header>

  <main id="main-content" role="main">
    <h1>Page Title</h1>
    <!-- Main content -->
  </main>

  <footer role="contentinfo">
    <!-- Footer content -->
  </footer>
</body>
</html>
```

### Heading Hierarchy

```html
<!-- ❌ BAD: Skipping heading levels -->
<h1>Page Title</h1>
<h3>Section</h3>  <!-- Skipped h2! -->
<h5>Subsection</h5>  <!-- Skipped h4! -->

<!-- ✅ GOOD: Sequential heading levels -->
<h1>Page Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>
<h2>Another Section</h2>
```

### Landmark Regions

```html
<header><!-- Site header, appears once --></header>
<nav aria-label="Main"><!-- Primary navigation --></nav>
<nav aria-label="Breadcrumb"><!-- Secondary navigation --></nav>
<main><!-- Main content, appears once --></main>
<aside><!-- Sidebar content --></aside>
<footer><!-- Site footer --></footer>
<section aria-labelledby="section-heading">
  <h2 id="section-heading">Section Title</h2>
</section>
```

---

## Keyboard Navigation

### Tab Order

```html
<!-- ❌ BAD: Positive tabindex disrupts order -->
<button tabindex="3">Third</button>
<button tabindex="1">First</button>
<button tabindex="2">Second</button>

<!-- ✅ GOOD: Natural DOM order -->
<button>First</button>
<button>Second</button>
<button>Third</button>

<!-- Use tabindex="0" to make non-interactive elements focusable -->
<div tabindex="0" role="button">Custom button</div>

<!-- Use tabindex="-1" for programmatic focus only -->
<div id="modal" tabindex="-1">Modal content</div>
```

### Keyboard-Accessible Components

```html
<!-- Interactive button that works with keyboard -->
<button
  type="button"
  onclick="handleClick()"
  onkeydown="handleKeydown(event)"
>
  Click or press Enter/Space
</button>

<script>
  function handleKeydown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  }
</script>
```

### Skip Links

```html
<body>
  <!-- First focusable element -->
  <a href="#main-content"
     class="absolute left-0 top-0 -translate-y-full
            focus:translate-y-0 bg-black text-white
            px-4 py-2 z-50 transition-transform">
    Skip to main content
  </a>

  <header><!-- Long header/nav --></header>

  <main id="main-content" tabindex="-1">
    <!-- Main content -->
  </main>
</body>
```

---

## ARIA Attributes

### Common ARIA Patterns

```html
<!-- Button with expanded state -->
<button
  aria-expanded="false"
  aria-controls="dropdown-menu"
>
  Menu
</button>
<ul id="dropdown-menu" hidden>
  <!-- Menu items -->
</ul>

<!-- Loading state -->
<button aria-busy="true" disabled>
  <span class="animate-spin">⏳</span>
  Loading...
</button>

<!-- Current page in navigation -->
<nav>
  <a href="/" aria-current="page">Home</a>
  <a href="/about">About</a>
</nav>

<!-- Required form field -->
<label for="email">Email *</label>
<input
  id="email"
  type="email"
  required
  aria-required="true"
/>

<!-- Error state -->
<input
  aria-invalid="true"
  aria-describedby="error-message"
/>
<p id="error-message" role="alert">
  Please enter a valid email
</p>
```

### ARIA Labels

```html
<!-- Icon-only button needs label -->
<button aria-label="Close menu">
  <svg aria-hidden="true"><!-- X icon --></svg>
</button>

<!-- Link with more context -->
<a href="/article-1" aria-label="Read more about Article Title">
  Read more
</a>

<!-- Labeling a region -->
<section aria-labelledby="features-heading">
  <h2 id="features-heading">Features</h2>
</section>
```

---

## Images and Media

### Alt Text

```html
<!-- ❌ BAD: Missing or unhelpful alt -->
<img src="hero.jpg" />
<img src="hero.jpg" alt="image" />
<img src="hero.jpg" alt="hero-image-1.jpg" />

<!-- ✅ GOOD: Descriptive alt text -->
<img src="hero.jpg" alt="Team collaborating around a whiteboard" />

<!-- Decorative images: empty alt -->
<img src="decorative-pattern.svg" alt="" role="presentation" />

<!-- Complex images: longer description -->
<figure>
  <img src="chart.png" alt="Bar chart showing revenue growth" aria-describedby="chart-desc" />
  <figcaption id="chart-desc">
    Revenue increased 45% year-over-year, from $2M to $2.9M.
  </figcaption>
</figure>
```

### SVG Accessibility

```html
<!-- Decorative SVG -->
<svg aria-hidden="true" focusable="false">
  <!-- paths -->
</svg>

<!-- Meaningful SVG -->
<svg role="img" aria-labelledby="svg-title">
  <title id="svg-title">Company Logo</title>
  <!-- paths -->
</svg>
```

---

## Form Accessibility

### Labels and Inputs

```html
<!-- ❌ BAD: No label association -->
<label>Email</label>
<input type="email" />

<!-- ✅ GOOD: Explicit label association -->
<label for="email">Email</label>
<input type="email" id="email" />

<!-- Or implicit association -->
<label>
  Email
  <input type="email" />
</label>

<!-- Required fields -->
<label for="name">
  Name <span aria-hidden="true">*</span>
  <span class="sr-only">(required)</span>
</label>
<input id="name" type="text" required aria-required="true" />
```

### Error Messages

```html
<div>
  <label for="password">Password</label>
  <input
    type="password"
    id="password"
    aria-invalid="true"
    aria-describedby="password-error password-hint"
  />
  <p id="password-hint" class="text-gray-500">
    Must be at least 8 characters
  </p>
  <p id="password-error" class="text-red-600" role="alert">
    Password is too short
  </p>
</div>
```

### Button States

```html
<!-- Disabled button -->
<button disabled aria-disabled="true">
  Submit
</button>

<!-- Loading button -->
<button aria-busy="true">
  <span class="sr-only">Loading</span>
  <span aria-hidden="true" class="animate-spin">⏳</span>
  Submitting...
</button>
```

---

## Motion and Animation

### Respecting User Preferences

```html
<style>
  /* Default: animations enabled */
  .animate-fade-in {
    animation: fadeIn 0.3s ease-out;
  }

  /* Respect user preference */
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
</style>

<!-- Tailwind approach -->
<div class="motion-safe:animate-bounce motion-reduce:animate-none">
  Content
</div>
```

### Safe Animation Patterns

```html
<!-- Subtle, non-essential animations -->
<button class="transition-colors duration-200 hover:bg-gray-100">
  Hover me
</button>

<!-- Focus animations are important for accessibility -->
<button class="transition-shadow duration-200 focus:ring-2 focus:ring-blue-500">
  Focus me
</button>
```

---

## Screen Reader Utilities

### Visually Hidden Content

```html
<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }

  .sr-only-focusable:focus {
    position: static;
    width: auto;
    height: auto;
    padding: inherit;
    margin: inherit;
    overflow: visible;
    clip: auto;
    white-space: normal;
  }
</style>

<!-- Usage -->
<button>
  <svg aria-hidden="true"><!-- icon --></svg>
  <span class="sr-only">Delete item</span>
</button>
```

### Announcements

```html
<!-- Live region for dynamic content -->
<div aria-live="polite" aria-atomic="true" class="sr-only">
  <!-- Updated content will be announced -->
</div>

<!-- Alert for important messages -->
<div role="alert">
  Form submitted successfully!
</div>

<!-- Status for less urgent updates -->
<div role="status">
  3 items in cart
</div>
```

---

## Testing Checklist

### Automated Testing
- [ ] Run axe-core or Lighthouse accessibility audit
- [ ] Check color contrast with browser DevTools
- [ ] Validate HTML with W3C validator

### Manual Testing
- [ ] Navigate with keyboard only (Tab, Enter, Space, Arrow keys)
- [ ] Test with screen reader (VoiceOver, NVDA, JAWS)
- [ ] Zoom to 200% and verify layout works
- [ ] Test with Windows High Contrast Mode
- [ ] Verify prefers-reduced-motion is respected

### Content Review
- [ ] All images have appropriate alt text
- [ ] Headings follow logical order (h1 → h2 → h3)
- [ ] Links have descriptive text (not "click here")
- [ ] Form fields have visible labels
- [ ] Error messages are clear and helpful

---

## Quick Reference

| Element | Requirement |
|---------|-------------|
| Text | 4.5:1 contrast ratio |
| Large text | 3:1 contrast ratio |
| Focus indicator | Visible on all interactive elements |
| Images | Alt text (empty for decorative) |
| Forms | Associated labels |
| Buttons | Accessible name |
| Skip link | First focusable element |
| Animations | Respect prefers-reduced-motion |
| Headings | Sequential order |
| Language | `lang` attribute on html |
