---
description: Explore decision branches with probability weighting, expected value analysis, and scenario-based optimization.
category: simulation-modeling
argument-hint: "Specify decision tree parameters"
---

# Decision Tree Explorer

Explore decision branches with probability weighting, expected value analysis, and scenario-based optimization.

## Instructions

You are tasked with creating a comprehensive decision tree analysis to explore complex decision scenarios and optimize choice outcomes. Follow this systematic approach: **$ARGUMENTS**

### 1. Prerequisites Assessment

**Critical Decision Context Validation:**

- **Decision Scope**: What specific decision(s) need to be made?
- **Stakeholders**: Who will be affected by and involved in this decision?
- **Time Constraints**: What are the decision deadlines and implementation timelines?
- **Success Criteria**: How will you measure decision success or failure?
- **Resource Constraints**: What limitations affect available options?

**If any context is unclear, guide systematically:**

```
Missing Decision Scope:
"I need clarity on the decision you're analyzing. Please specify:
- Primary Decision: The main choice you need to make
- Decision Level: Strategic, tactical, or operational
- Decision Type: Go/no-go, resource allocation, priority ranking, or option selection
- Alternative Options: What choices are you considering?

Examples:
- Strategic: 'Should we enter the European market next year?'
- Investment: 'Which of 3 product features should we build first?'
- Operational: 'Should we migrate to microservices or improve the monolith?'
- Crisis: 'How should we respond to the new competitor launch?'"

Missing Success Criteria:
"How will you evaluate if this decision was successful?
- Financial Metrics: Revenue impact, cost savings, ROI targets
- Strategic Metrics: Market share, competitive position, capability building
- Operational Metrics: Efficiency gains, quality improvements, risk reduction
- Timeline Metrics: Speed to market, implementation time, payback period"

Missing Resource Context:
"What constraints limit your decision options?
- Budget: Available investment capital and operating funds
- Time: Implementation deadlines and resource availability windows
- Capabilities: Team skills, technology infrastructure, operational capacity
- Regulatory: Compliance requirements and approval processes"
```

### 2. Decision Architecture Mapping

**Structure the decision systematically:**

#### Decision Hierarchy
- Primary decision point and core question
- Secondary decisions that follow from primary choice
- Tertiary decisions and implementation details
- Decision dependencies and sequencing requirements
- Option combinations and interaction effects

#### Stakeholder Impact Analysis
- Decision makers and approval authorities
- Implementation teams and resource owners
- Customers and end users affected
- External partners and dependencies
- Competitive landscape implications

#### Constraint Identification
- Hard constraints (cannot be violated)
- Soft constraints (preferences and trade-offs)
- Temporal constraints (timing and sequencing)
- Resource constraints (budget, capacity, capabilities)
- Regulatory and compliance constraints

### 3. Option Generation and Structuring

**Systematically identify and organize decision alternatives:**

#### Comprehensive Option Development
- Direct approaches to achieving the goal
- Hybrid solutions combining multiple approaches
- Phased approaches with incremental implementation
- Alternative goals that might better serve needs
- "Do nothing" baseline for comparison

#### Option Categorization
- Quick wins vs. long-term strategic moves
- High-risk/high-reward vs. safe/incremental options
- Resource-intensive vs. lean approaches
- Internal development vs. external partnerships
- Proven approaches vs. innovative experiments

#### Option Feasibility Assessment
```
For each option, evaluate:
- Technical Feasibility: Can this actually be implemented?
- Economic Feasibility: Do benefits justify costs?
- Operational Feasibility: Do we have capability to execute?
- Timeline Feasibility: Can this be done in available time?
- Political Feasibility: Will stakeholders support this?

Feasibility Scoring (1-10 scale):
Option: [name]
- Technical: [score] - [reasoning]
- Economic: [score] - [reasoning]
- Operational: [score] - [reasoning]
- Timeline: [score] - [reasoning]
- Political: [score] - [reasoning]
Overall Feasibility: [average score]
```

### 4. Probability Assessment Framework

**Apply systematic probability estimation:**

#### Base Rate Analysis
- Historical success rates for similar decisions
- Industry benchmarks and comparative data
- Expert judgment and domain knowledge
- Market research and customer validation data
- Internal capability assessment and track record

#### Scenario Probability Weighting
- Best case scenario probabilities (optimistic outcomes)
- Most likely scenario probabilities (base case expectations)
- Worst case scenario probabilities (pessimistic outcomes)
- Black swan event probabilities (extreme scenarios)
- Competitive response probabilities

#### Probability Calibration Methods
```
Use multiple estimation approaches:

1. Historical Data Analysis:
   - Similar past decisions and outcomes
   - Success/failure rates in comparable situations
   - Market adoption patterns for similar offerings

2. Expert Consultation:
   - Domain expert probability estimates
   - Cross-functional team input and perspectives
   - External advisor and consultant insights

3. Market Validation:
   - Customer research and feedback
   - Competitive analysis and market dynamics
   - Regulatory and environmental factor assessment

4. Monte Carlo Simulation:
   - Run multiple probability scenarios
   - Test sensitivity to assumption changes
   - Generate confidence intervals for estimates
```

### 5. Expected Value Calculation

**Quantify decision outcomes systematically:**

#### Outcome Quantification
- Financial returns and cost implications
- Strategic value and competitive advantages
- Risk reduction and option value creation
- Time savings and efficiency improvements
- Learning value and capability building

#### Multi-Dimensional Value Assessment
```
Value Calculation Framework:

Financial Value:
- Direct Revenue Impact: $[amount] ± [uncertainty range]
- Cost Savings: $[amount] ± [uncertainty range]
- Investment Required: $[amount] and timeline
- NPV Calculation: $[net present value] over [timeframe]

Strategic Value:
- Market Position Improvement: [qualitative + quantitative]
- Competitive Advantage Creation: [sustainable differentiation]
- Capability Building: [new skills and infrastructure]
- Option Value: [future opportunities enabled]

Risk Value:
- Risk Reduction: [quantified risk mitigation]
- Downside Protection: [worst-case scenario costs]
- Opportunity Cost: [alternative options foregone]
- Reversibility: [cost and difficulty of changing course]
```

#### Expected Value Integration
```
Expected Value Formula Application:
EV = Σ(Probability × Outcome Value) for all scenarios

Example Calculation:
Option A: New Product Launch
- Best Case (20% probability): $10M revenue, 80% margin = $8M profit
- Base Case (60% probability): $5M revenue, 70% margin = $3.5M profit  
- Worst Case (20% probability): $1M revenue, 50% margin = $0.5M profit

Expected Value = (0.20 × $8M) + (0.60 × $3.5M) + (0.20 × $0.5M)
= $1.6M + $2.1M + $0.1M = $3.8M

Investment Required: $2M
Net Expected Value: $1.8M
```

### 6. Risk Analysis and Sensitivity Testing

**Comprehensively assess decision risks:**

#### Risk Identification Matrix
- Implementation risks (execution challenges)
- Market risks (demand, competition, economic changes)
- Technology risks (technical feasibility, obsolescence)
- Regulatory risks (compliance, approval, policy changes)
- Resource risks (availability, capability, cost overruns)

#### Sensitivity Analysis
- Key assumption stress testing
- Break-even analysis for critical variables
- Scenario analysis with parameter variations
- Confidence interval calculation for outcomes
- Robustness testing across different conditions

#### Risk Mitigation Strategy Development
```
Risk Mitigation Framework:

For each significant risk:
1. Risk Description: [specific risk scenario]
2. Probability Assessment: [likelihood of occurrence]
3. Impact Assessment: [severity if it occurs]
4. Early Warning Indicators: [signals to watch for]
5. Prevention Strategies: [actions to reduce probability]
6. Mitigation Strategies: [actions to reduce impact]
7. Contingency Plans: [responses if risk materializes]
8. Risk Ownership: [who monitors and responds]
```

### 7. Decision Tree Visualization and Analysis

**Create clear decision tree representations:**

#### Tree Structure Design
```
Decision Tree Format:

[Decision Point] 
├── Option A [probability: X%]
│   ├── Scenario A1 [probability: Y%] → Outcome: $Z
│   ├── Scenario A2 [probability: Y%] → Outcome: $Z
│   └── Scenario A3 [probability: Y%] → Outcome: $Z
├── Option B [probability: X%]
│   ├── Scenario B1 [probability: Y%] → Outcome: $Z
│   └── Scenario B2 [probability: Y%] → Outcome: $Z
└── Option C [probability: X%]
    └── Scenario C1 [probability: Y%] → Outcome: $Z

Expected Values:
- Option A: $[calculated EV]
- Option B: $[calculated EV]  
- Option C: $[calculated EV]
```

#### Decision Path Analysis
- Optimal path identification based on expected value
- Alternative paths with acceptable risk/return profiles
- Contingency routing based on early decision outcomes
- Information value analysis (worth of additional research)
- Real option valuation (value of delaying decisions)

### 8. Optimization and Recommendation Engine

**Generate data-driven decision recommendations:**

#### Multi-Criteria Decision Analysis
- Weighted scoring across multiple decision criteria
- Trade-off analysis between competing objectives
- Pareto frontier identification for efficient solutions
- Stakeholder preference integration
- Scenario robustness across different weighting schemes

#### Recommendation Generation
```
Decision Recommendation Format:

## Primary Recommendation: [Selected Option]

### Executive Summary
- Recommended Decision: [specific choice and rationale]
- Expected Value: $[amount] with [confidence level]%
- Key Success Factors: [critical requirements for success]
- Major Risks: [primary concerns and mitigation approaches]
- Implementation Timeline: [key milestones and dependencies]

### Supporting Analysis
- Expected Value Calculation: [detailed breakdown]
- Probability Assessments: [key assumptions and sources]
- Risk Assessment: [major risks and mitigation strategies]
- Sensitivity Analysis: [critical variables and break-even points]
- Alternative Options: [other viable choices and trade-offs]

### Implementation Guidance
- Immediate Next Steps: [specific actions required]
- Success Metrics: [measurable indicators of progress]
- Decision Points: [future choice points and triggers]
- Resource Requirements: [budget, team, timeline needs]
- Stakeholder Communication: [alignment and buy-in strategies]

### Contingency Planning
- Plan B Options: [alternative approaches if primary fails]
- Early Warning Systems: [risk monitoring and triggers]
- Decision Reversal: [exit strategies and switching costs]
- Adaptive Strategies: [adjustment mechanisms for changing conditions]
```

### 9. Decision Quality Validation

**Ensure robust decision-making process:**

#### Process Quality Checklist
- [ ] All relevant stakeholders consulted
- [ ] Comprehensive option generation completed
- [ ] Probability assessments calibrated with data
- [ ] Value calculations include all material factors
- [ ] Risks identified and mitigation planned
- [ ] Assumptions explicitly documented and tested
- [ ] Decision criteria clearly defined and weighted
- [ ] Implementation feasibility validated

#### Bias Detection and Mitigation
- Confirmation bias: Seeking information that supports preferences
- Anchoring bias: Over-relying on first information received
- Availability bias: Overweighting easily recalled examples
- Optimism bias: Overestimating positive outcomes
- Sunk cost fallacy: Continuing failed approaches
- Analysis paralysis: Over-analyzing instead of deciding

#### Decision Documentation
- Decision rationale and supporting analysis
- Key assumptions and probability assessments
- Alternative options considered and rejected
- Stakeholder input and consultation process
- Risk assessment and mitigation strategies
- Implementation plan and success metrics

### 10. Learning and Feedback Integration

**Establish decision quality improvement:**

#### Decision Outcome Tracking
- Actual vs. predicted outcomes measurement
- Assumption validation against real results
- Decision timing and implementation effectiveness
- Stakeholder satisfaction and support levels
- Unintended consequences and side effects

#### Continuous Improvement
- Decision-making process refinement
- Probability calibration improvement over time
- Risk assessment accuracy enhancement
- Stakeholder engagement optimization
- Tool and framework evolution

## Usage Examples

```bash
# Strategic business decision
/simulation:decision-tree-explorer Should we acquire competitor X for $50M or build competing product internally?

# Product development prioritization
/simulation:decision-tree-explorer Which of 5 product features should we build first given limited engineering resources?

# Technology architecture choice
/simulation:decision-tree-explorer Microservices vs monolith architecture for our new platform?

# Market expansion decision
/simulation:decision-tree-explorer European market entry strategy: direct expansion vs partnership vs acquisition?
```

## Quality Indicators

- **Green**: Comprehensive options, calibrated probabilities, quantified outcomes, documented assumptions
- **Yellow**: Good option coverage, reasonable probability estimates, partially quantified outcomes
- **Red**: Limited options, uncalibrated probabilities, qualitative-only outcomes

## Common Pitfalls to Avoid

- Analysis paralysis: Over-analyzing instead of making timely decisions
- False precision: Using precise numbers for uncertain estimates  
- Option tunnel vision: Not considering creative alternatives
- Probability miscalibration: Overconfidence in likelihood estimates
- Value tunnel vision: Focusing only on financial outcomes
- Implementation blindness: Not considering execution challenges

Transform complex decisions into systematic analysis for exponentially better choice outcomes.