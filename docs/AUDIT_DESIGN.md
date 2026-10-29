# Independent audit remediation design

Goal: turn an offline memory demand model into a reproducible decision aid that shows
coverage, missing evidence, bottlenecks and scenario trade-offs. The prior calculation
baseline is preserved in a separate workspace; this revision is independently audited.

The user delegated chart choice and requested correction of the original requirements,
not an optimizer, cycle simulator or an assertion of measured hardware performance.
Use existing Python standard library and an offline HTML/SVG/CSS/JavaScript report.
All design choices below are implementation choices, not newly claimed user specifications.

## Initial findings

- Real HexaHarness project integration is verified. Strict audit warnings concern
  unproven unattended operational readiness, which is not claimed.
- Quantitative phase and declared topology budgets exist; audit must trace every initial
  axis and distinguish implemented arithmetic from labels or data placeholders.
- The prior visual is partial: one KV bar plot plus long raw tables does not communicate
  coverage, normalized bottlenecks or system trade-offs, and the mobile page overflows.

## Bounded corrections

Preserve core API compatibility and all arithmetic regressions. Repair only evidence-backed
computational gaps found in the requirement traceability audit. Add public baseline sources
and explicit composition/coverage/sensitivity inputs where needed; never convert vendor peak
to sustained bandwidth without a separately labeled scenario assumption.

Replace the default report with a compact, responsive 2D decision dashboard:

1. Baseline versus scenario capacity and logical bandwidth in separate labeled charts,
   with units, zero/ticks, exact values, ratios and changed assumptions visible.
2. Phase/scenario selector with capacity/traffic composition and module counts.
3. Candidate-by-field coverage matrix separating observed/public, derived, scenario and
   unknown evidence. Exact missing fields explain withheld recommendations.
4. Demand/limit utilization bars with textual pass/fail/unknown labels; unknown limits
   never produce invented percentages. Raw data stays in local collapsible details.
5. Hot/warm/migration and direct/relay comparisons show independent declared budgets.
6. Configuration trade-offs and bounded sensitivity scenarios distinguish demand growth,
   efficiency reduction and technology offsets. Conditional ranges are not confidence intervals.

Use legible system fonts, restrained blue/teal for values, amber for unknown and red plus text
for violated limits. No external assets or animation dependency. Keep labels at readable CSS
sizes rather than scaling a whole desktop plot down. Primary content fits390px; detailed tables
may scroll within their container. Controls require visible labels, focus indicators and
keyboard operation. Local UI guidance search returned an unrelated sales-page pattern, so
the design uses the skill's accessibility/contrast/responsive principles, not that pattern.

## Acceptance and distribution

Independent numerical probes and 29 existing tests remain. Add targeted tests for new
calculation paths and report data agreement. Verify actual desktop/mobile rendering and
selector behavior in Ego Lite, with screenshots tied to output hashes. Complete real
HexaHarness build/lint/test and a bounded independent PsOs review/verification task.

Only after all three scoped gates pass, publish a new private repository through existing
authorized GitHub authentication. Ship source, factual public source notes, assumptions,
safe synthetic examples, reproducibility commands and sanitized audit evidence. Exclude
original private handoff/report text, personal paths/session IDs, credentials, PsOs ledger
and raw local runtime logs. No deployment or Pages. No package or third-party code is bundled.
