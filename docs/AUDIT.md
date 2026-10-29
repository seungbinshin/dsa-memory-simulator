# Independent three-gate audit

Review date: 2026-10-27 UTC. This is an explicit-input analytical decision aid,
not a calibrated hardware simulator or confirmed product recommendation.

| Gate | Initial verdict | Final reviewed scope |
|---|---|---|
| Real HexaHarness integration | PASS for project integration; PARTIAL unattended readiness | PASS: actual installed 1.0.0 CLI, task-bound commands and required build, syntax-compilation and test sensors; no mock adapter |
| Original requirements and useful perspectives | PARTIAL | PASS for the documented analytical scope after object-unit, assembly, usable-capacity, placement-coverage and sensitivity repairs |
| Expected visual result | PARTIAL | PASS: actual responsive dashboard, numeric/visual review, units, evidence gaps, bottlenecks, conditional changes and configuration/routing tradeoffs |

## What failed initially, and why

The first accepted version emphasized phase arithmetic and raw export tables. It
omitted a complete object-unit path for LPDDR6 assembly, a usable-capacity distinction,
whole-demand coverage for declared placement, and compact decision coverage/sensitivity
records. Its one chart and wide tables did not communicate the expected decision
flow on a phone. Those were scope and presentation gaps missed by the earlier checks.

The repaired version preserves die/stack/module/assembly units, adds explicit assembly
assumptions, binds optional placement to total capacity demand, distinguishes supported
internal-input paths from unimplemented ones, and computes named growth, efficiency
and fabric-bound scenarios. No optimizer or unverified private specification was added.
The report now separates capacity/BW axes, shows required-versus-limit bars, exact
unknown fields, direct/relay paths, and scenario/configuration controls.

A post-integration regression failed because it expected the old raw-table token
`control_data` inside HTML. Its CSV section assertion was retained; the HTML assertion
now checks the actual control comparison mount and embedded `kv_system` data. The
substantive output checks were not removed. All 44 tests then passed.

## Executed evidence and independence

- Full Python3.13 unit/integration/regression suite: 44 passed, including numerical
  boundary, null, scope-exclusion, CLI/API, deterministic-export and renderer tests.
- The same 44 tests passed from a read-only temporary source copy; copied files were
  unchanged. This establishes reproducibility under that environment, not all platforms.
- A separate reviewer ran independent numerical probes against the core without edits.
  See [requirements traceability](REQUIREMENTS_TRACEABILITY.md) for equations and hashes.
- Seven supplemental oracle groups passed, including all four phases, assembly units,
  null/placement rules, sensitivity boundaries, public units and JSON/CSV/HTML parity.
  This supplement was written by an implementer and is not labeled independent review.
- Actual Ego Lite desktop/mobile execution confirmed viewport/document widths of
  1440/1440, 768/768 and 390/390. Native phase/scenario/candidate controls updated results;
  keyboard Tab moved from phase to scenario. A separate visual reviewer opened six
  screenshots and checked the displayed arithmetic. See [visual audit](VISUAL_AUDIT.md).
- [Validation metadata](VALIDATION.json) binds generated outputs and screenshots by SHA256.

## What the harness evidence means

The installed HexaHarness 1.0.0 launcher and official task/checkpoint validation were
used, following its required command protocol. The previous implementation's completed
checkpoints and retained build/lint/test evidence were independently inspected. This
repair uses its own real change checkpoint; final completion and runtime capture are
required by the owner's publication gate. Runtime records are retained privately,
not bundled into this repository. The configured checks are reproducible in AGENTS.md
and .hexaharness/harness.yaml. Syntax compilation is not a style or type checker.

The official operational audit had 7 PASS, 5 WARN and 0 FAIL. Warnings concerned absence
of failure-derived rules and unattended/escalation/STOP/tripwire drills. No fictional
failures or nominal runs were added. Project integration PASS does not establish
unattended operational readiness. One public input-manifest packaging write occurred
without a successful pre-write observation after a transient metadata-capture error;
it was separately hashed and checked. This exception is disclosed, and no claim is
made that every host edit was perfectly mediated. Production repairs and final review
artifacts have successful pre-write observations. A harness is execution evidence,
not a proof that every domain assumption is correct.

## Interpretation and publication boundary

HBM5 and unverified DDR7 remain null; HBF/NAND is positioning-only. Public peak BW never
becomes sustained BW without an explicit scenario assumption. Selected ranges are not
confidence intervals or forecasts. Training and Physical AI consume declared budgets;
MLA, automatic architecture inference, placement optimization, physical compatibility,
thermal dynamics and calibrated p99/energy are not claimed. Missing private measurements
remain future local inputs. No private data was collected.

Only public factual notes/links, source, tests, synthetic outputs, sanitized review
records and screenshots belong in the private release. The original reference report,
personal sessions, handoff/accounting logs, keys and raw runtime state are excluded.
Publication is conditional on these three reviews and final execution/privacy checks.
