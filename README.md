# DRAM Decision Explorer

An offline, reproducible analytical simulator for comparing AI memory demand,
DRAM configurations and rack constraints. It distinguishes evidence gaps from
known resource deficits and shows how conditional model/technology scenarios
change capacity, logical traffic and configuration requirements.

## Run locally

Python 3.11+ and its standard library are sufficient; verification uses Python3.13.
No installation, service, login or network connection is required to use the model.

```sh
python3.13 -B -m memory_dsa demo --output outputs
python3.13 -B -m memory_dsa evaluate --input outputs/baseline-request.json --output /tmp/kv.json
python3.13 -B -m memory_dsa integrated --input outputs/integrated-request.json --output /tmp/integrated.json
python3.13 -B -m unittest discover -s tests -v
python3.13 -B verify_reproducibility.py
```

Open **outputs/index.html** for the decision dashboard. Machine-readable outputs
include results.json, results.csv and integrated-results.csv. Exact example requests
and canonical input hashes accompany the generated results. Re-running the same
inputs produces byte-identical outputs. Tests use temporary output directories.

## What is calculated

- KV payload for explicit GQA/MHA dimensions; capacity and logical decode scans.
- Integrated decode, prefill, training and Physical AI byte budgets, with independent
  resident weights/state and active weight traffic. Dense/MoE use explicit resident
  and active budgets; an architecture label alone never invents numerical demand.
- Module/construction-unit counts and explicit channel, fabric, scale-up/scale-out,
  rack power, PSU, cooling and supplied latency constraints.
- Declared heterogeneous pools, migration paths, and KV control/data direct versus
  relay budgets. Placement is evaluated from declared allocations, not optimized.
- Explicit assembly composition and demand coverage, plus named sensitivity and
  breakpoint examples; see [modeling extensions](docs/MODELING_EXTENSIONS.md).

The stable APIs are `memory_dsa.api.analyze(request)` and
`memory_dsa.integrated.analyze_integrated(request)`. The latter also exposes
`evaluate_placement`, `evaluate_kv_system` and `compare_scenarios`.
`memory_dsa.exploration.decision_study()` provides the audited examples and
machine-readable decision coverage. See generated requests and the modeling guide
for schemas and equations.

## Evidence and interpretation

[Public memory sources](inputs/PUBLIC_SOURCE_NOTES.md) and
[model-trend evidence](inputs/MODEL_TRENDS.md) contain primary links and dates.
Catalog values retain source IDs, units, object levels and evidence kinds. Peak
bandwidth is never silently promoted to sustained bandwidth. Explicit efficiency
assumptions remain scenarios. Die, stack, module, channel and rack quantities must
not be compared as interchangeable hardware. PSU capacity is input-side watts;
rack/cooling limits are IT-side watts.

HBM5 and unverified DDR7 values remain **null**, and missing essential fields withhold
recommendations. HBF/NAND is shown only as adjacent positioning and excluded from
main analysis. Null is not zero and does not prove that a technology is insufficient.
The separate local-input gap schema identifies measurement conditions and whether
an input is computationally supported. No private specifications or company traces
are included or automatically acquired.

All example growth/efficiency factors and years are configurable **conditional
scenarios**, not actual forecasts, confidence intervals or product specifications.
Logical traffic is not measured bus traffic. Quantization multipliers omit layout,
metadata and residual-cache overhead unless supplied explicitly. Prefix reuse changes
prefill work; it does not automatically shrink resident decode KV state. Unsupported
MLA layouts are rejected rather than represented by a false GQA conversion.

Training/Physical AI expert communication uses explicit path budgets; no decoder
token rate is inferred. No calibrated TTFT/ITL/p99/tokens-per-joule, cycle simulation,
allocation optimizer, physical feasibility certification or purchase recommendation
is claimed. A conditional eligible configuration passes its declared checks; missing
constraints remain visible and prevent a conclusive ranking.

## Audit and development

The independent [three-gate audit](docs/AUDIT.md) maps original requirements to code,
numeric evidence and limitations. [Visual guide](docs/VISUAL_GUIDE.md) explains the
dashboard. Sanitized execution evidence and screenshots accompany the audited release.
HexaHarness is an external development tool: its real project checkpoints and required
build/test/lint gates were used; it is not an adapter or a runtime simulator dependency.
Its operational readiness warnings are distinguished from project integration evidence.

This repository contains source, factual public notes and synthetic examples only.
The original reference report, private handoff, personal session records, credentials,
internal task ledger and raw local execution logs are intentionally not distributed.
See [third-party notices](docs/THIRD_PARTY_NOTICES.md). No third-party assets are bundled.
