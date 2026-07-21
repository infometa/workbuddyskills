# Mobile App Scene Injection Prompt

This file is the Agent injection prompt for the **Mobile App** scene. When the Agent receives requests involving iOS / Android / Mini Program UI, App pages, or mobile interface design, it MUST strictly follow the instructions in this file.

---

## 1. Scene Definition

**Scene Name**: Mobile App
**`fetch_guidelines` topic**: `mobile-app`
**Target Device**: iPhone 17 Pro (6.3" Super Retina XDR, ProMotion, Dynamic Island)
**Default Canvas Size (logical points, pt)**: **402 × 874 pt** (native resolution 1206 × 2622 px)
**Design Density**: Designed @1x, exported @3x (scale factor = 3)
**Safe Area (portrait)**:
- Status Bar: **54 pt**
- Safe Area Top (includes Dynamic Island reserve): **62 pt**
- Safe Area Bottom (Home Indicator): **34 pt**
- Left / Right: 0 pt
**Key Control Reference Heights**: NavBar 44 pt, TabBar 49 pt (excluding 34 pt bottom safe area, 83 pt total)
**Compatibility with Other Devices**: If the user explicitly requests iPhone 17 / iPhone 17 Pro Max / Android, create an additional canvas based on the actual logical dimensions, but default to iPhone 17 Pro. In landscape mode, pay extra attention to the 62 pt safe-area inset on the left and right.

**Trigger Keywords** (entering this scene if any is matched):
- English: mobile app, iOS screen, Android screen, app design, onboarding screen, splash screen, sign-in page (mobile), tab bar, bottom sheet, mini program, in-app screen
- Chinese: 移动端、手机端、App 页面、App 界面、iOS 页面、安卓页面、小程序页面、启动页、引导页、登录页（移动端）、个人中心、底部导航、Tab 栏、移动端原型

---

## 2. Required Skill to Load

```
use_skill("ardot-design-assistant")
```
> This scene strictly follows the Skill's standard workflow (Steps 1–7).
---

## 3. Required Rules / References to Load

| Reference File                          | When to Load                                         |
|-----------------------------------------|------------------------------------------------------|
| `rules/style-guide.md`                  | **Always load** — mobile visual style, hierarchy, card-based layouts. |
| `rules/design-rules.md`                 | Required reading before executing `batch_edit`; pay attention to flexbox vertical layout. |
| `references/ardot-workflow.md`          | Reference for multi-screen workflows.                |
| `references/design-to-code-workflow.md` | Enable only for "App UI to H5 / Mini Program frontend code" tasks. |

**Required guidelines fetch**:
```
fetch_guidelines(topic: "mobile-app")
```

---

## 4. MCP Tool Whitelist (Strictly Limited)

**Core Tools**:
- `fetch_editor_state`
- `fetch_guidelines` (topic fixed to `mobile-app`)
- `fetch_style_guide_tags` (optional — prefer reading `../../rules/style-guide-tags.md` directly; the tag list is static)
- `fetch_style_guide` (tags MUST include `mobile` or `mobile-app`)
- `fetch_variables`
- `apply_variables`
- `locate_available_space`
- `batch_read`
- `batch_edit` (≤ 25 ops / call)
- `capture_screenshot`
- `capture_layout`
- `upload_images`

---

## 5. Scene-Specific Constraints

1. **Frame**: Each screen MUST be an independent **402×874 pt** Frame, laid out according to the safe areas below (top to bottom):
   - 0–54 pt: Status Bar area (system status bar, no content)
   - 54–62 pt: Dynamic Island reserve (avoid capsule occlusion; if NavBar overlaps here, test it)
   - From 62 pt: Content safe area starts (NavBar / Page Title start here)
   - Bottom 34 pt: Home Indicator reserve (no tappable elements allowed)
   - If the page includes a TabBar: the entire 0–83 pt region at the bottom is the TabBar area (49 pt for the bar itself, 34 pt for the safe area)
2. **Multi-Screen Principle**: When the task involves multiple pages (e.g., login + home + details), screens MUST be arranged horizontally, with ≥ 40 pt spacing between screens, all attached under the same Design Board.
3. **Touch Targets**: All tappable elements are ≥ 44×44 pt; bottom Tab icons 24–28 pt, labels 10–12 pt.
4. **Type Scale** (iOS Human Interface Guidelines standard):
   - Large Title 34 / Title 1 28 / Title 2 22 / Title 3 20
   - Headline 17 Bold / Body 17 / Callout 16 / Subhead 15 / Footnote 13 / Caption 1 12 / Caption 2 11
   - Body text **≥ 13 pt**; smaller sizes are forbidden.
5. **Components**: StatusBar, NavBar, TabBar, ListItem, Card, Sheet, Toast, Input, Button (primary/secondary/destructive/text), Switch, Avatar, Badge. Prefer reusing existing components.
6. **Hierarchy and States**: Provide at least `default / pressed / disabled` states for key components; if list items are swipeable, include a sample for the swipe state.
7. **Images and Icons**: Icons use a unified 24pt grid; placeholder images are retrieved via `G(nodeId, "stock", prompt)` for random images, or `G(nodeId, "ai", prompt)` when semantic images are explicitly required; avatars use circles or extra-large rounded corners.
8. **Dark Mode**: If the user requests dark mode or `DESIGN.md` declares a Dark mode, reuse the same components and variables and switch via variable modes; hard-coding two sets of components is forbidden.

---

## 7. Acceptance Checklist (Agent Self-Check)

- [ ] Each screen is strictly **402×874 pt** (iPhone 17 Pro; or another device size explicitly specified by the user)
- [ ] Top Status Bar 54 pt + Dynamic Island up to 62 pt safe area is reserved, NavBar starts at 62 pt
- [ ] Bottom Home Indicator 34 pt safe area is reserved; if a TabBar exists, the bottom totals 83 pt
- [ ] Touch targets are ≥ 44×44 pt
- [ ] Body text size ≥ 13 pt
- [ ] `capture_screenshot` is performed after each screen is completed
- [ ] Base components come from `DESIGN.md` and are reused rather than duplicated
- [ ] `capture_layout` shows no overlap / clipping
- [ ] For dark mode: variable modes fully cover all usages, with no hard-coded colors
