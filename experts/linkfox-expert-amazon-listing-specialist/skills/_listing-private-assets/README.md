# Bundled Listing Compliance Rules

This non-Skill directory contains local rule data consumed by `listing-compliance-scan`:

- hashed brand-conflict indexes;
- English and Chinese superlative / unsupported-claim rules (the Chinese set currently has 115 条 / 11 类);
- metadata describing versions and matching behavior.

It is bundled with the portable expert so compliance checks work without a LinkFox service, API key,
store authorization or network request. Keep this directory beside the `listing-*` skill directories
when copying the expert to another harness.

The hashed brand index is a screening aid, not a complete trademark database. A local pass is not legal
clearance. The JSON claim rules may be inspected and adapted by the receiving harness.
