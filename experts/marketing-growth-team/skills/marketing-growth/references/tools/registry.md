# Marketing Tools Registry

> Source: github.com/coreyhaines31/marketingskills (MIT License)

## Overview

88 marketing tools organized by category, with API, MCP, CLI, and SDK availability indicators.

## MCP-Enabled Tools (14+ native)

These tools support Model Context Protocol for direct AI agent interaction:

- **ga4** — Google Analytics 4 data access
- **stripe** — Payment and subscription management
- **mailchimp** — Email marketing management
- **google-ads** — Ad campaign management
- **resend** — Transactional email sending
- **zapier** — Workflow automation + 8,000+ app SDK
- **zoominfo** — B2B contact and intent data
- **clay** — Data enrichment and outbound automation
- **supermetrics** — Cross-platform marketing data
- **coupler** — Marketing data pipelines
- **outreach** — Sales engagement sequences
- **crossbeam** — Partner ecosystem data
- **introw** — Partner relationship management
- **exa** — AI-powered web search
- **composio** — Integration layer for 500+ tools (HubSpot, Salesforce, Meta Ads, etc.)

## Tools by Category

### Analytics (7)
| Tool | MCP | Best For |
|------|:---:|---------|
| ga4 | ✓ | Web analytics, Google ecosystem |
| mixpanel | - | Product analytics, event tracking |
| amplitude | - | Product analytics, cohort analysis |
| posthog | - | Open-source analytics, session replay |
| segment | - | Customer data platform, routing |
| adobe-analytics | - | Enterprise analytics |
| plausible | - | Privacy-focused analytics |

### SEO (6)
| Tool | MCP | Best For |
|------|:---:|---------|
| google-search-console | - | Organic search performance |
| semrush | - | Keyword research, competitive analysis |
| ahrefs | - | Backlink analysis, content explorer |
| dataforseo | - | SERP data API |
| keywords-everywhere | - | Keyword metrics |
| rankparse | ✓ | Rank tracking |

### Email Marketing (11)
| Tool | MCP | Best For |
|------|:---:|---------|
| mailchimp | ✓ | SMB email marketing |
| customer-io | - | Behavior-based automation |
| sendgrid | - | Transactional email at scale |
| resend | ✓ | Developer-friendly transactional |
| sequenzy | ✓ | Email sequences |
| nitrosend | ✓ | AI-native email |
| kit | - | Creator/newsletter focused |
| beehiiv | - | Newsletter platform |
| klaviyo | - | E-commerce email/SMS |
| postmark | - | Reliable transactional |
| brevo | - | Email/SMS combo |

### CRM (3)
| Tool | MCP | Best For |
|------|:---:|---------|
| hubspot | - | Full marketing + sales CRM |
| salesforce | - | Enterprise CRM |
| close | - | SMB sales CRM |

### Advertising (4)
| Tool | MCP | Best For |
|------|:---:|---------|
| google-ads | ✓ | Search and display advertising |
| meta-ads | - | Social advertising (FB/IG) |
| linkedin-ads | - | B2B professional targeting |
| tiktok-ads | - | Short-form video ads |

### Data Enrichment (4)
| Tool | MCP | Best For |
|------|:---:|---------|
| clearbit | - | Company/contact enrichment |
| apollo | - | B2B prospecting database |
| zoominfo | ✓ | Enterprise intent data |
| clay | ✓ | Multi-source enrichment |

### Referral/Affiliate (5)
| Tool | MCP | Best For |
|------|:---:|---------|
| rewardful | - | SaaS affiliate tracking |
| tolt | - | Simple referral programs |
| dub-co | - | Link management |
| mention-me | - | Enterprise referral |
| partnerstack | - | Partner ecosystem |

### Video (3)
| Tool | MCP | Best For |
|------|:---:|---------|
| wistia | - | Business video hosting |
| heygen | ✓ | AI video generation |
| hyperframes | - | Video creation toolkit |

### Commerce & CMS (6)
| Tool | MCP | Best For |
|------|:---:|---------|
| shopify | - | E-commerce platform |
| wordpress | - | CMS, blogging |
| webflow | - | Visual website builder |
| sanity | - | Headless CMS |
| contentful | - | Headless CMS |
| strapi | - | Open-source headless CMS |

## CLI Tool Pattern

All CLI tools in the original repository follow a consistent pattern:
- **Zero dependency** — Only requires Node 18+, uses native `fetch`
- **JSON output** — Pipeable to `jq`, saveable to files
- **Environment variable auth** — Set `{TOOL}_API_KEY`
- **Consistent command format** — `{tool} <resource> <action> [options]`

## Quick Start by Use Case

| Use Case | Tools |
|----------|-------|
| Set up analytics | ga4 + segment |
| Launch referral program | rewardful/tolt + dub-co |
| Email automation | customer-io + resend |
| Cold email outreach | hunter + lemlist/instantly |
| Run paid ads | google-ads + meta-ads |
| Track attribution | ga4 + segment + attribution modeling |
