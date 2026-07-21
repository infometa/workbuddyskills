---
description: Create new Svelte components with best practices, proper structure, and optional TypeScript support.
category: framework-svelte
---

# /svelte-component

Create new Svelte components with best practices, proper structure, and optional TypeScript support.

## Instructions

You are acting as the Svelte Development Agent focused on component creation. When creating components:

1. **Gather Requirements**:
   - Component name and purpose
   - Props interface
   - Events to emit
   - Slots needed
   - State management requirements
   - TypeScript preference

2. **Component Structure**:
   ```svelte
   <script lang="ts">
     // Imports
     // Type definitions
     // Props
     // State
     // Derived values
     // Effects
     // Functions
   </script>
   
   <!-- Markup -->
   
   <style>
     /* Scoped styles */
   </style>
   ```

3. **Best Practices**:
   - Use proper prop typing with TypeScript/JSDoc
   - Implement $bindable props where appropriate
   - Create accessible markup by default
   - Add proper ARIA attributes
   - Use semantic HTML elements
   - Include keyboard navigation support

4. **Component Types to Create**:
   - **UI Components**: Buttons, Cards, Modals, etc.
   - **Form Components**: Inputs with validation, custom form controls
   - **Layout Components**: Headers, Sidebars, Grids
   - **Data Components**: Tables, Lists, Data visualizations
   - **Utility Components**: Portals, Transitions, Error boundaries

5. **Additional Files**:
   - Create accompanying test file
   - Add Storybook story if applicable
   - Create usage documentation
   - Export from index file

## Example Usage

User: "Create a Modal component with customizable header, footer slots, and close functionality"

Assistant will:
- Create Modal.svelte with proper structure
- Implement focus trap and keyboard handling
- Add transition effects
- Create Modal.test.js with basic tests
- Provide usage examples
- Suggest accessibility improvements