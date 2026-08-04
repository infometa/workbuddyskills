---
name: marketing-growth
description: "Full-stack marketing growth skill providing frameworks, templates, tools, and references for SaaS and digital product marketing. Covers CRO, copywriting, SEO, email, ads, analytics, referrals, and strategic planning. Trigger: marketing plan, CRO, conversion optimization, SEO audit, email sequence, growth strategy, copywriting, analytics tracking, referral program, content strategy, pricing, launch plan, churn prevention, A/B testing."
---

# Marketing Growth Skill

This skill provides the knowledge base and reference library for the Marketing Growth Team. It contains frameworks, templates, implementation guides, and tool integrations covering all aspects of SaaS and digital product marketing.

## Reference Library Structure

```
references/
├── cro/                    # Conversion Rate Optimization
│   ├── copy-frameworks.md          # Headline formulas, page templates
│   ├── natural-transitions.md      # Section transition phrases
│   ├── experiments.md              # A/B test ideas by page type
│   └── form-optimization.md        # Form CRO guidance
├── seo/                    # Search Engine Optimization
│   ├── technical-seo-checklist.md  # Complete technical audit checklist
│   ├── ai-seo-guide.md            # AEO/GEO/LLMO strategies
│   ├── programmatic-seo.md         # Programmatic SEO implementation
│   ├── international-seo.md        # Hreflang, i18n best practices
│   ├── schema-implementation.md    # Structured data guide
│   └── content-strategy.md         # Editorial planning templates
├── email/                  # Email Marketing
│   ├── sequence-templates.md       # Complete sequence templates
│   ├── email-types.md             # Full email type reference
│   ├── copy-guidelines.md         # Email copy best practices
│   └── cold-email-frameworks.md   # Outbound strategies
├── ads/                    # Paid Advertising
│   ├── ad-creative-guide.md       # Creative best practices
│   └── campaign-frameworks.md     # Campaign structure guides
├── analytics/              # Analytics & Attribution
│   ├── ga4-implementation.md      # GA4 setup guide
│   ├── gtm-implementation.md      # GTM container setup
│   ├── event-library.md           # Event naming library
│   └── attribution-models.md     # Attribution modeling guide
├── strategy/               # Marketing Strategy
│   ├── ideas-by-category.md       # 139 marketing ideas library
│   ├── current-state-rubric.md    # 17-section audit rubric
│   ├── marketing-psychology.md    # Persuasion frameworks
│   └── pricing-strategy.md        # Pricing and offers
├── growth/                 # Growth Engineering
│   ├── referral-programs.md       # Referral mechanics
│   ├── community-marketing.md    # Community-led growth
│   ├── launch-playbook.md        # Product launch guides
│   └── churn-prevention.md       # Churn analysis and prevention
└── tools/                  # Tool Integrations
    ├── registry.md                # Full 88-tool index
    ├── china-alternatives.md      # China market tool alternatives
    └── integrations/              # Per-tool integration guides
```

## How to Use

1. The team lead routes user requests to the appropriate team member
2. Team members reference the relevant files in this skill for detailed frameworks and templates
3. Load references on-demand — only pull what's needed for the current task
4. Tool integration guides provide API endpoints, auth patterns, and common operations

## China Market Adaptations

This skill includes China-specific marketing tool alternatives and considerations:
- See `references/tools/china-alternatives.md` for mapping
- WeChat ecosystem (公众号, 小程序, 视频号) strategies
- Baidu SEO differences from Google
- China-specific ad platforms (巨量引擎, 腾讯广告, 百度推广)
- Local analytics tools (神策数据, GrowingIO)
