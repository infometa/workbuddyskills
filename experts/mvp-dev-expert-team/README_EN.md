# MVP Dev Expert Team

From idea to product in one sentence. A 7-member full-stack AI expert team — describe your idea, confirm three documents once, and the rest is fully automated.

## ⛔ P0 Absolute Rules

This expert team enforces three absolute rules. All outputs must pass:

1. **NO emoji as functional icons** → Only **Lucide** icon library allowed (lucide-react / lucide-vue-next / inline SVG)
2. **NO purple-to-pink gradient hero visuals** → Solid colors + brand glow instead
3. **NO AI template slop** → Real copy + Design Tokens + hand-crafted details

Every phase gate checks these rules. Violation = sent back for redo.

## 🎨 Design System

Aligned with industry design systems standard:
- **4-Layer Token Architecture**: A1-identity → A2 → B-slot → C-extension
- **9-Section DESIGN.md output format**: Visual Theme → Color → Typography → Components → Layout → Depth → Do's & Don'ts → Responsive → Agent Guide
- **Craft specifications**: Typography precision, color palette rules, animation discipline, anti-AI slop checks
- **Max 2 accent uses per screen**, **ALL CAPS ≥0.06em letter-spacing**, **150ms motion convergence value**

## Type

Team-based (multi-role collaborative team), orchestrated by the Project Director with 7 domain experts.

## Team Members

- DaWanQu JingZai (Project Director) — Coordination & orchestration
- Xu Qingchu (Product Manager) — Requirements analysis, competitive research
- Yan Haokan (UI/UX Designer) — UI/UX design, anti-AI-template quality control
- Gao Jianyuan (Chief Architect) — Tech stack selection, system architecture
- Jia Simin (Frontend Engineer) — Frontend development + self-check & fix
- Bei Luoqi (Backend Engineer) — Backend API + database
- Yan Guoguan (QA Engineer) — Layered testing, quality gates
- Bu Dangji (DevOps Engineer) — Automated deployment, delivery integration

## Workflow

Requirements clarification → Parallel research (three documents) → User confirms three documents → Spec auto-locked → Design → Parallel development + self-check → Testing → Deployment & delivery. Auto-proceeds after confirmation; only notifies user for technical infeasibility or critical defects.

## Usage Examples

- "I want to build a team collaboration tool from scratch"
- "Help me develop an e-commerce mini program"
- "I have a product idea, help me make it an MVP"

## Environment Variables

Configure the following environment variables before deployment:

- `JWT_SECRET` — JWT signing key (run `openssl rand -hex 32` to generate)
- `DATABASE_URL` — Database connection string

## Installation

1. Download the expert package
2. Extract to ~/.workbuddy/plugins/marketplaces/my-experts/plugins/mvp-dev-expert-team/
3. Restart WorkBuddy, find "MVP Dev Expert Team" in the expert list
4. Click to start a conversation, enter your product idea to launch
