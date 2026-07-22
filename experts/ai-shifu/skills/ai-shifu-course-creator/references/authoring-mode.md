# Authoring Mode

Select one execution mode for each Segmentation, Orchestration, Generation, or Optimization run.

## Required References

- `data-contracts.md#fallback-output-extensions`

## Mode Selection

- **Standard mode** (default): Use when the input quality is sufficient. Run the selected phases with their standard schemas.
- **Fallback mode:** Use when the input is incomplete, conflicting, or low-quality. Produce coarse outputs, mark uncertainty explicitly, and give focused rerun hints. Add the phase-specific fallback fields defined by the data contract to the standard output.
