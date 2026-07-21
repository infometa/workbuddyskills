---
description: Configure monorepo project structure
category: project-setup
argument-hint: "Specify monorepo configuration options"
---

# Setup Monorepo

Configure monorepo project structure

## Instructions

1. **Monorepo Tool Analysis**
   - Parse monorepo tool from arguments: `$ARGUMENTS` (nx, lerna, rush, yarn-workspaces, pnpm-workspaces, turborepo)
   - If no tool specified, analyze project structure and recommend best tool based on:
     - Project size and complexity
     - Existing package manager
     - Team preferences and CI/CD requirements
   - Validate tool compatibility with existing codebase

2. **Workspace Structure Setup**
   - Create standard monorepo directory structure:
     - `packages/` or `apps/` for applications
     - `libs/` or `shared/` for shared libraries
     - `tools/` for build tools and scripts
     - `docs/` for documentation
   - Configure workspace root package.json with workspace definitions
   - Set up proper .gitignore for monorepo patterns

3. **Tool-Specific Configuration**
   - **Nx**: Initialize Nx workspace, configure nx.json, add essential plugins
   - **Lerna**: Set up lerna.json, configure version management and publishing
   - **Rush**: Initialize rush.json, configure build orchestration and policies
   - **Yarn Workspaces**: Configure workspaces in package.json, set up workspace protocols
   - **pnpm Workspaces**: Set up pnpm-workspace.yaml, configure filtering and dependencies
   - **Turborepo**: Initialize turbo.json, configure pipeline and caching

4. **Package Management Configuration**
   - Configure package manager settings for workspace support
   - Set up dependency hoisting and deduplication rules
   - Configure workspace-specific package.json templates
   - Set up cross-package dependency management
   - Configure private package registry if needed

5. **Build System Integration**
   - Configure build orchestration and task running
   - Set up dependency graph analysis and affected package detection
   - Configure parallel builds and task caching
   - Set up incremental builds for changed packages
   - Configure build artifacts and output management

6. **Development Workflow**
   - Set up workspace-wide development scripts
   - Configure hot reloading and watch mode for development
   - Set up workspace-wide linting and formatting
   - Configure debugging across multiple packages
   - Set up workspace-wide testing and coverage

7. **Version Management**
   - Configure versioning strategy (independent vs. fixed versions)
   - Set up changelog generation for workspace packages
   - Configure release workflow and package publishing
   - Set up semantic versioning and conventional commits
   - Configure workspace-wide dependency updates

8. **CI/CD Pipeline Integration**
   - Configure CI to detect affected packages and run targeted tests
   - Set up build matrix for different package combinations
   - Configure deployment pipeline for multiple packages
   - Set up workspace-wide quality gates
   - Configure artifact publishing and registry management

9. **Documentation and Standards**
   - Create workspace-wide development guidelines
   - Document package creation and management procedures
   - Set up workspace-wide code standards and conventions
   - Create architectural decision records for monorepo patterns
   - Document deployment and release procedures

10. **Validation and Testing**
    - Verify workspace configuration is correct
    - Test package creation and cross-package dependencies
    - Validate build pipeline and task execution
    - Test development workflow and hot reloading
    - Verify CI/CD integration and affected package detection
    - Create example packages to demonstrate workspace functionality