# Prompt register

Every prompt the system runs, with its version. The full specification of
each (purpose, inputs, output format, how it is checked, known weaknesses)
is in the Stage 3 Prompt Library workbook. Code loads prompts from these
files; none is written inline. Responses are cached by a hash of prompt id,
version and inputs, so changing a prompt means changing its version.

| ID | Name | Category | Version | Model | File | Serves |
|---|---|---|---|---|---|---|
| PR-01 | Grounded reply draft | Build | 1.0 | gpt-oss-20b, temperature 0 | `build/PR-01.md` | FR-06, FR-03, FR-12 |
| PR-02 | Grounding check (guardrail) | Build | 1.0 | gpt-oss-20b, temperature 0 | `build/PR-02.md` | FR-07, FR-06 |

## Change history

| Date | ID | Version | Change |
|---|---|---|---|
| 2026-11-18 | PR-01, PR-02 | 1.0 | First version, as specified in the Stage 3 Prompt Library |
