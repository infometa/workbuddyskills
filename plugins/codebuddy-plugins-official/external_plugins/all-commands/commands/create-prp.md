---
description: Create a comprehensive Product Requirement Prompt (PRP) with research and context gathering
category: project-task-management
argument-hint: <feature_description>
allowed-tools: Read, Write, WebSearch
---

# Product Requirement Prompt (PRP) Creation

You will help the user create a comprehensive Product Requirement Prompt (PRP) for: $ARGUMENTS

## What is a PRP?

A Product Requirement Prompt (PRP) is a detailed document that defines the requirements, context, and specifications for a feature or product. It serves as a comprehensive guide for implementation, ensuring all stakeholders have a clear understanding of what needs to be built, why it's needed, and how success will be measured.

## Research Process

Before creating the PRP, conduct thorough research to gather all necessary context:

### 1. **Web Research**
   - Search for best practices related to the feature/product
   - Research similar implementations and solutions
   - Look for relevant library documentation
   - Find example implementations on platforms like GitHub, StackOverflow
   - Identify industry standards and patterns
   - Gather competitive analysis if applicable

### 2. **Documentation Review**
   - Check for any existing project documentation
   - Identify documentation gaps that need to be addressed
   - Review any related technical specifications
   - Look for architectural decision records (ADRs) if present

### 3. **Codebase Exploration** (if applicable)
   - Identify relevant files and directories that provide implementation context
   - Look for existing patterns that should be followed
   - Find similar features that could serve as references
   - Check for any technical constraints or dependencies

### 4. **Requirements Gathering**
   - Clarify any ambiguous requirements with the user
   - Identify both functional and non-functional requirements
   - Determine performance, security, and scalability needs
   - Establish clear acceptance criteria

## PRP Template Structure

Create a comprehensive PRP following this structure:

### 1. Executive Summary
- **Feature Name**: [Clear, descriptive name]
- **Version**: [Document version]
- **Date**: [Creation date]
- **Author**: [Author/Team]
- **Status**: [Draft/Review/Approved]
- **Brief Description**: [1-2 paragraph overview of the feature]

### 2. Problem Statement
- **Current Situation**: What problem exists today?
- **Impact**: Who is affected and how?
- **Opportunity**: What opportunity does solving this create?
- **Constraints**: What limitations exist?

### 3. Goals & Objectives
- **Primary Goal**: The main objective to achieve
- **Secondary Goals**: Additional benefits or objectives
- **Success Metrics**: How success will be measured
- **Key Performance Indicators (KPIs)**: Specific, measurable outcomes

### 4. User Stories & Use Cases
- **Target Users**: Who will use this feature?
- **User Stories**: As a [user type], I want [goal] so that [benefit]
- **Use Case Scenarios**: Detailed walkthrough of user interactions
- **Edge Cases**: Unusual or boundary scenarios to consider

### 5. Functional Requirements
- **Core Features**: Must-have functionality
- **Optional Features**: Nice-to-have functionality
- **Feature Priority**: P0 (Critical), P1 (Important), P2 (Nice to have)
- **Dependencies**: Other features or systems this depends on

### 6. Non-Functional Requirements
- **Performance**: Response time, throughput, resource usage
- **Security**: Authentication, authorization, data protection
- **Scalability**: Expected load and growth projections
- **Reliability**: Uptime requirements, error handling
- **Usability**: User experience requirements
- **Compatibility**: Browser, device, system requirements

### 7. Technical Specifications
- **Architecture Overview**: High-level design approach
- **Technology Stack**: Languages, frameworks, libraries to use
- **Data Models**: Database schemas, API contracts
- **Integration Points**: External systems or APIs
- **Technical Constraints**: Known limitations or requirements

### 8. Implementation Plan
- **Phases**: Break down into manageable phases
- **Milestones**: Key deliverables and checkpoints
- **Timeline**: Estimated duration for each phase
- **Resources**: Team members, tools, infrastructure needed
- **Dependencies**: External dependencies and blockers

### 9. Risk Assessment
- **Technical Risks**: Potential technical challenges
- **Business Risks**: Market, competition, or strategic risks
- **Mitigation Strategies**: How to address each risk
- **Contingency Plans**: Backup approaches if primary plan fails

### 10. Success Criteria & Acceptance Tests
- **Acceptance Criteria**: Specific conditions that must be met
- **Test Scenarios**: Key test cases to validate functionality
- **Performance Benchmarks**: Measurable performance targets
- **Quality Gates**: Checkpoints before moving to next phase

### 11. Documentation & Training
- **Documentation Needs**: User guides, API docs, technical docs
- **Training Requirements**: Who needs training and what type
- **Knowledge Transfer**: How knowledge will be shared

### 12. Post-Launch Considerations
- **Monitoring**: What metrics to track after launch
- **Maintenance**: Ongoing maintenance requirements
- **Future Enhancements**: Potential future improvements
- **Deprecation Plan**: If replacing existing functionality

## Context Prioritization

When creating the PRP, prioritize including:
1. **Specific, actionable requirements** over vague descriptions
2. **Measurable success criteria** that can be objectively evaluated
3. **Clear scope boundaries** to prevent scope creep
4. **Realistic timelines** based on complexity and resources
5. **Risk mitigation strategies** for identified challenges

## Interaction with User

Throughout the PRP creation process:
1. Ask clarifying questions when requirements are ambiguous
2. Confirm assumptions before including them in the PRP
3. Request additional context when needed
4. Validate technical approaches with the user
5. Ensure alignment on priorities and constraints

## Final Output

The completed PRP should be:
- **Comprehensive**: Cover all aspects of the feature/product
- **Clear**: Use precise language, avoid ambiguity
- **Actionable**: Provide enough detail for implementation
- **Measurable**: Include specific success criteria
- **Realistic**: Consider constraints and limitations
- **Maintainable**: Easy to update as requirements evolve

Begin by asking the user for any specific context or requirements they want to emphasize, then proceed with research and PRP creation based on the feature description provided.