---
description: Create a Jobs to be Done (JTBD) document for a product feature focusing on user needs
category: project-task-management
argument-hint: "<feature description> [output-path]"
allowed-tools: Write, TodoWrite
---

Create a comprehensive Jobs to be Done (JTBD) document based on the feature description provided.

## Instructions:
1. Parse the arguments:
   - First argument: Feature/product description (required)
   - Second argument: Output path (optional, defaults to `JTBD.md` in current directory)

2. Create a well-structured JTBD document that includes:

   **Core Job Statement**:
   - When [situation]
   - I want to [motivation]
   - So I can [expected outcome]

   **Job Map**:
   - Define: What users need to understand first
   - Locate: What inputs/resources users need
   - Prepare: How users get ready
   - Confirm: How users verify readiness
   - Execute: The core action
   - Monitor: How users track progress
   - Modify: How users make adjustments
   - Conclude: How users finish the job

   **Context & Circumstances**:
   - Functional job aspects
   - Emotional job aspects
   - Social job aspects

   **Success Criteria**:
   - How users measure success
   - What outcomes they expect
   - Time/effort constraints

   **Pain Points**:
   - Current frustrations
   - Workarounds users employ
   - Unmet needs

   **Competing Solutions**:
   - How users currently solve this
   - Alternative approaches
   - Why current solutions fall short

3. Focus on:
   - User motivations (not features)
   - Jobs that remain stable over time
   - Outcomes users want to achieve
   - Context that triggers the job

4. Use the TodoWrite tool to track JTBD sections as you complete them

## Example usage:
- `/create-jtbd "Help developers find and fix bugs faster"`
- `/create-jtbd "Enable teams to collaborate on documents in real-time" collab-JTBD.md`

Feature description: $ARGUMENTS