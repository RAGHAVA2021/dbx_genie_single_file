# Text Instruction Justification

- Exact instruction text: maintained in `general_instructions.md` and injected as the single `text_instructions` item.
- Why structured surfaces were insufficient: ambiguity handling, unavailable-data disclosure, response transparency, and summary caveats are global behaviours rather than table, column, join, or SQL-example metadata.
- Intended global behavior: require clarification for ambiguous requests, disclose unavailable data and assumptions, respect governed access, and state the date range and sources used.
- Possible overreach or regression risk: broad instructions could cause unnecessary clarification or refusal. Metric formulas, joins, filters, and table-selection rules must remain in structured configuration rather than migrating into this file.
- How the instruction will be reviewed or validated: business and security owners review the wording; workspace smoke tests cover ambiguous, unsupported, and security-sensitive questions; evaluation results are checked before promotion.

