---
description: Migrate JavaScript project to TypeScript
category: typescript-migration
---

# Migrate to TypeScript

Migrate JavaScript project to TypeScript

## Instructions

1. **Project Analysis and Migration Planning**
   - Analyze current JavaScript codebase structure and complexity
   - Identify external dependencies and their TypeScript support
   - Assess project size and determine migration approach (gradual vs. complete)
   - Review existing build system and bundling configuration
   - Create migration timeline and phased approach plan

2. **TypeScript Installation and Configuration**
   - Install TypeScript and related dependencies (@types packages)
   - Create comprehensive tsconfig.json with strict configuration
   - Configure path mapping and module resolution
   - Set up incremental compilation and build optimization
   - Configure TypeScript for different environments (development, production, testing)

3. **Build System Integration**
   - Update build tools to support TypeScript compilation
   - Configure webpack, Vite, or other bundlers for TypeScript
   - Set up development server with TypeScript support
   - Configure hot module replacement for TypeScript files
   - Update build scripts and package.json configurations

4. **File Migration Strategy**
   - Start with configuration files and utility modules
   - Migrate from least to most complex modules
   - Rename .js files to .ts/.tsx incrementally
   - Update import/export statements to use TypeScript syntax
   - Handle mixed JavaScript/TypeScript codebase during transition

5. **Type Definitions and Interfaces**
   - Create comprehensive type definitions for project-specific types
   - Install @types packages for external dependencies
   - Define interfaces for API responses and data structures
   - Create custom type declarations for untyped libraries
   - Set up shared types and interfaces across modules

6. **Code Transformation and Type Annotation**
   - Add explicit type annotations to function parameters and return types
   - Convert JavaScript classes to TypeScript with proper typing
   - Transform object literals to typed interfaces
   - Add generic types for reusable components and functions
   - Handle complex types like union types, mapped types, and conditional types

7. **Error Resolution and Type Safety**
   - Resolve TypeScript compiler errors systematically
   - Fix type mismatches and undefined behavior
   - Handle null and undefined values with strict null checks
   - Configure ESLint rules for TypeScript best practices
   - Set up type checking in CI/CD pipeline

8. **Testing and Validation**
   - Update test files to TypeScript
   - Configure testing framework for TypeScript support
   - Add type testing with tools like tsd or @typescript-eslint
   - Validate type safety in test suites
   - Set up type coverage reporting

9. **Developer Experience Enhancement**
   - Configure IDE/editor for optimal TypeScript support
   - Set up IntelliSense and auto-completion
   - Configure debugging for TypeScript source maps
   - Set up type-aware linting and formatting
   - Create TypeScript-specific code snippets and templates

10. **Documentation and Team Onboarding**
    - Update project documentation for TypeScript setup
    - Create TypeScript coding standards and best practices guide
    - Document migration decisions and type system architecture
    - Set up type documentation generation
    - Train team members on TypeScript development workflows
    - Create troubleshooting guide for common TypeScript issues