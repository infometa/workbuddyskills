---
name: idea-validator
description: Validate startup ideas using Hexa's Opportunity Memo framework and Perceived Created Value (PCV) methodology. Assess problem-solution fit, market opportunity, and determine if an idea is worth
  pursuing.
description_zh: 创业想法验证，评估问题-方案匹配度与市场机会
description_en: Validate startup ideas with problem-solution fit and market assessment
version: 1.0.1
metadata:
  version: 1.0.0
  tags: business, hexa, validation, startup, idea, problem-solution-fit
---

# Idea Validator - Startup Idea Assessment Framework

Rigorously assess startup ideas BEFORE building using structured validation—saving months of wasted effort on ideas that won't work.

**Hexa's Principle:** "You want to make something people want. But people don't always know what they want—so you need to understand what they actually need."

## When This Activates

- User asks "is this a good idea"
- User says "I want to build X" without validation
- User asks "should I pursue this"
- User mentions a startup idea they're considering
- User wants to know if their idea is worth building

## The Framework

**Validation = Opportunity Memo Assessment + Perceived Created Value (PCV) Score**

### Problem Assessment Matrix

| Dimension | Rating | Impact |
|-----------|--------|--------|
| Frequency | [Daily/Weekly/Monthly] | High/Med/Low |
| Severity | [Critical/Important/Nice-to-have] | High/Med/Low |
| Awareness | [Actively seeking/Aware/Unaware] | High/Med/Low |
| Budget | [Has budget/Would find/No budget] | High/Med/Low |

**Problem Score:** 3-4 High = Strong. 1-2 = Weak. 0 = Not a real problem.

### PCV Scoring (4 Dimensions)

Rate current solution problems + your improvement:

| Dimension | Current Problem | Your Improvement |
|-----------|-----------------|------------------|
| **Price** | Not a problem / A problem / Serious | No diff / Some / Serious |
| **Quality** | Not a problem / A problem / Serious | No diff / Some / Serious |
| **Performance** | Not a problem / A problem / Serious | No diff / Some / Serious |
| **Convenience** | Not a problem / A problem / Serious | No diff / Some / Serious |

**Scoring:** a=0, b=1, c=3 points. Sum all 8 ratings.

| Score | Interpretation | Recommendation |
|-------|---------------|----------------|
| 0-6 | Weak | Don't pursue |
| 7-12 | Moderate | Needs refinement |
| 13-18 | Strong | Worth pursuing |
| 19-24 | Exceptional | Build NOW |

## Quick Discovery Questions

**Problem Space:**

1. What specific pain point does your ICP feel?
2. How do they currently solve this?
3. What's wrong with current solutions?
4. How often do they experience this pain?
5. What does this problem cost them?

**Timing:**

1. Why is NOW the right time?
2. What has changed recently?
3. What barriers existed before that are now gone?

**ICP:**

1. Company type, size, industry
2. Buyer vs. user role
3. What triggers them to seek a solution?

## Integration

| Skill | When to Use |
|-------|-------------|
| `market-sizer` | After validation passes |
| `startup-icp-definer` | Deep dive on customer |
| `mvp-architect` | Scope the build |
| `leads-researcher` | Find design partners |

---

**For detailed execution workflow, output templates, and PCV calculations:** `references/full-guide.md`
