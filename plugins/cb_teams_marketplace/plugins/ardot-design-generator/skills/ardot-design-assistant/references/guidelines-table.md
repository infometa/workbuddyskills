## Table

- Use the following rules **only when there is no predefined Table component or Table frame** in the design system or document.
- Table responsive multi screen design: Unless specifically defined, when converting a wide multi-column table to a mobile version, consider using cards instead of table

### Table Structure
- A table consists of:
  - A **header row** containing titles for each column.
  - One or more **data rows**.
  - If the user does not specify data, generate **dummy placeholder values** for each cell.

### Table Cells
- Each **cell** is represented as a **frame node**.
- When designing from scratch, a cell may contain:
  - A **text node** with `textGrowth: fixed-width`, or
  - Another **component or node** (e.g., label, button, etc.), if explicitly requested by the user.

### Table Layout Rules
- **Cell frame**
  - `width: fixed`
  - `height: fill_container`
- **Row frame**
  - Contains multiple cell frames.
  - `width: fill_container`
  - `height: fixed`
  - `children`: cell frames
