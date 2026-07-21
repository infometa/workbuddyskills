# Interview Simulator

A universal mock interview expert that role-plays as a real interviewer for **any profession or role** — engineering, product, design, business, operations, HR, finance, legal, and more.

## What It Does

Interview Simulator transforms the assistant into a professional interviewer who:

- 🎭 **Plays any role** — Frontend Engineer, Product Manager, Sales, HR, Accounting, or any role you specify
- 📈 **Adapts to level** — Intern → Junior → Mid → Senior → Staff → Executive
- 🧩 **Multi-module interviews** — System design, coding/algorithm, product sense, case study, role play, domain knowledge, behavioral (STAR)
- ✅ **Per-question scoring** — 1–10 score with strengths, improvements, and ideal answer
- 📋 **Final scorecard** — Module scores, overall verdict (Strong Hire → No Hire), strengths, gaps, and recommended study topics
- 🌐 **Multilingual** — Automatically matches your language
- 📄 **Resume-aware** — Optionally analyze your CV for a targeted interview

## Supported Roles

| Category | Example Roles |
|---|---|
| 🔧 Engineering | Frontend, Backend, Mobile, Full-stack, DevOps/SRE, Data, ML, Embedded, QA |
| 📦 Product & Design | Product Manager, UI/UX Designer, Technical Writer |
| 💼 Business & Operations | Operations, Sales, Marketing, Business Development, Customer Success |
| 👥 People & Admin | HR / Recruiter, Accounting / Finance, Legal, Admin |
| 🎯 Other | Any role you specify |

## How to Use

Start by telling the expert what role you want to practice for:

```
帮我进行后端工程师高级职位的模拟面试，聚焦分布式系统
```

```
Mock interview for Product Manager, mid-level, focus on B2B growth.
```

### In-Session Commands

| Command | Action |
|---|---|
| `skip` | Skip current question |
| `hint` | Get a hint |
| `explain` | Get the ideal answer explained |
| `score` | Show running scorecard |
| `harder` / `easier` | Adjust difficulty |
| `switch [module]` | Change interview module |
| `end` | End session & get final scorecard |
| `restart` | Start over |

## File Structure

```
interview-simulator/
├── .codebuddy-plugin/
│   └── plugin.json          # Expert metadata
├── agents/
│   └── interview-simulator.md   # Agent definition
└── README.md                # This file
```

## License

MIT — free to use, modify, and share.
