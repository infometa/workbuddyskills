---
description: Create a Product Requirements Document (PRD) for a product feature
category: project-task-management
argument-hint: "<feature description> [output-path]"
allowed-tools: Write, TodoWrite
---

Create a comprehensive Product Requirements Document (PRD) based on the feature description provided.

## Instructions:
1. Parse the arguments:
   - First argument: Feature description (required)
   - Second argument: Output path (optional, defaults to `PRD.md` in current directory)

2. Create a well-structured PRD that includes:
   - **Executive Summary**: Brief overview of the feature
   - **Problem Statement**: What problem does this solve?
   - **Objectives**: Clear, measurable goals
   - **User Stories**: Who are the users and what are their needs?
   - **Functional Requirements**: What the feature must do
   - **Non-Functional Requirements**: Performance, security, usability standards
   - **Success Metrics**: How will we measure success?
   - **Assumptions & Constraints**: Any limitations or dependencies
   - **Out of Scope**: What this PRD does NOT cover

3. Focus on:
   - User needs and business value (not technical implementation)
   - Clear, measurable objectives
   - Specific acceptance criteria
   - User personas and their journey

4. Use the TodoWrite tool to track PRD sections as you complete them

## Example usage:
- `/create-prd "Add dark mode toggle to settings"`
- `/create-prd "Implement user authentication with SSO" auth-PRD.md`

Feature description: $ARGUMENTS