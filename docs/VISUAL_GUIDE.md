# Reading the offline decision explorer

`memory_dsa.report.render_report(data)` returns a complete HTML document containing
the supplied results as JSON, system-font styling and local JavaScript. It requires
no web service, chart package, downloaded font or network connection. Calculations
remain in the model; display formatting does not replace or mutate model values.

Open the generated `outputs/index.html`. The dashboard separates:

- KV capacity from logical bandwidth, using independent linear scales, zero ticks,
  explicit TiB or TiB/s units, baseline ratios and changed scenario assumptions.
- Phase demand from the selected configuration's limits. Phase, scenario and
  candidate controls update the demand composition, constraints and system budgets.
- Published memory profile fields from synthetic sizing profiles. Each published
  profile retains its object level, evidence kind, source links and missing fields.
- Declared hot/warm pool capacity and migration bandwidth from whole-demand
  coverage. Local pool feasibility alone does not establish system feasibility.
- Direct payload routing from payload relayed through the control server. Metadata,
  control traffic and payload traffic are separate budgets.
- Model growth, efficiency reduction and technology supply changes. Synthetic
  configuration counts and modeled watts are not product recommendations.

## Interpretation

Green or teal with **Within bound** means the specific supplied constraint passes.
Red with **Limit exceeded** means it fails. Amber with **Unknown** or
**Evidence missing** means evidence is absent. Unknown utilization never receives
a percentage. A bar above its bound is visually capped at the track width; its
numeric utilization remains visible. Known zero is retained as zero.

Catalog values use decimal GB/TB for public specification context; computed demand
uses binary GiB/TiB. A capacity amount and bandwidth per second are never combined
on one scale. Peak bandwidth is not silently substituted for sustained bandwidth.
Scenario ranges are ranges across assumptions, not statistical confidence intervals.
HBM5 unknowns are missing evidence, not evidence of insufficient performance.
HBF/NAND remains positioning-only and is excluded from the analyzed configurations.

The capacity and traffic panels are analytical budgets. They do not demonstrate
hardware accuracy, tail-latency calibration, scheduling behavior or a measured
forecast. The source registry, missing-input register and collapsed exact JSON
provide the boundary of the model's evidence.

## Interaction and inspection

Use native keyboard-accessible selects with visible focus:

- `#phase-select`: filters the scenario list by workload phase.
- `#scenario-select`: updates demand, configuration choices and topology budgets.
- `#candidate-select`: updates candidate sizing, limits and the status readout.
- `#status-live`: announces the selected scenario and feasibility boundary.
- `#constraint-bars`: explicit required/limit numbers and utilization statuses.
- `#coverage-cards`: published profiles, object levels and missing evidence.
- `#placement-view`: declared pools, paths and whole-demand coverage.
- `#control-modes`: direct and relay comparison.
- `#sensitivity-view`: conditional growth/efficiency/technology comparisons.
- `html[data-report-ready="true"]`: initial rendering finished without a JavaScript
  exception. This is a readiness hook, not proof that the visual audit passed.

The primary layout uses responsive CSS and fixed readable text sizes rather than
shrinking an SVG designed for a desktop. At 390 CSS pixels, cards and controls stack.
Detailed JSON scrolls inside its container. Browser acceptance checks should verify
document width does not exceed viewport width, visible labels and units, selector
changes, keyboard focus, and the direct/relay failure example. Save actual desktop
and mobile screenshots separately with the generated artifact hash; unit checks do
not establish visual acceptance.

## Data and checks

The renderer consumes the existing `scenarios`, `integrated_scenarios`, `catalog`,
`sources` and `internal_gaps` keys. Optional `decision_study` supplies extra scenario
choices, sensitivity rows, coverage notes, assembly examples and breakpoints. Model
input and output JSON stays available in collapsed details and the neighboring JSON
file. HTML-sensitive JSON characters and displayed strings are escaped. Source links
accept only HTTP(S), and are never loaded as runtime assets.

Targeted tests check exact JSON round-trip and determinism, preservation of null and
zero, rejection of non-finite JSON numbers, script-breakout safety and absence of
external runtime assets. If Node is available, two additional checks validate script
syntax and exercise display sinks for missing versus zero values. They do not replace
the separate real-browser layout and interaction audit.
