---
description: Update or generate YAML documentation for SQL models with proper descriptions and tests
category: documentation-changelogs
argument-hint: <model_name_or_path>
allowed-tools: Read, Write, Edit
---

$ARGUMENTS

Update or generate the YAML docs for this SQL model or folder of models. Look for a matching YAML file or documentation for this model inside a combined YAML file in the same directory. If the YAML for the given SQL model is not included, generate it from scratch based on the SQL code and anything that can be inferred from the upstream files and their YAML. Put the resulting YAML in a separate file matching the name of the model, and if necessary remove this model from any combined YAML files.

Use the `generate_model_yaml` operation to determine the canonical list of columns and data types. Add/update all data types in any existing YAML. If no there is no existing YAML file, add descriptions (and tests, if necessary) to the output of this operation. In this case (and only this case), remove columns that have been commented out or excluded from the SQL.

- Make sure to add a brief description for the model. Infer the model type (staging, intermediate, or mart) and include information about its sources if important. (This doesn't mean adding a `source` property.)
- Carry over descriptions and tests from any matching upstream columns, or update as necessary for derived columns. Ignore relationship tests to a different modeling layer. Ignore any included models or sources that are not directly referenced in this model.
- If a uniqueness test for more than one column is required, use `unique_combination_of_columns` from the dbt_utils package and put it after the model description and before `columns:`, under `data_tests:`. Only add such a test if explicitly requested or if there is such a test upstream, all columns are present in this model, and the cardinality of this model appears to match. Do not change this test if it already exists.
- A uniqueness/primary key test for a single column should be the standard `unique` and `not_null` tests on that column only.
- Use the `data_tests:` syntax
- Add tests for individual columns under `models.columns`; do not use the model-wide `models.data_tests` unless directed to do so.
- Don't include `version: 2` at the top; just start with `models:`
- Do not make guesses about accepted values. Include accepted values tests when (and only when) the column's values are explicitly