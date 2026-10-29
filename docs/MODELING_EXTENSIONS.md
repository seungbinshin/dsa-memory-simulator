# Audited modeling extensions

These are deterministic analytical budgets. They do not predict calibrated hardware
throughput, latency, thermal response, accuracy loss or optimal placement.

## Object and capacity basis

Catalog candidates retain `object_level` (die, stack or module). A result preserves
`units_per_object`, `component_object_level`, gross and explicitly supplied usable capacity.
`required_objects` is the precise count; `required_modules` remains its compatibility alias.
`required_components = required_objects * units_per_object`. Counts from different object
levels are not physical module interchangeability or a procurement recommendation.
`channels_per_module` retains its original API name and means declared channels per candidate
object. Bus pins and DDR5 subchannels never populate it automatically.

Legacy requests size against declared `capacity_bytes`. If `usable_capacity_bytes` is
present, that value is the sizing basis; explicit null remains unknown. No reserve fraction
is invented. The assembly helper reports usable capacity as null when unspecified and
labels its candidate's capacity as gross. It does not assume a usable percentage.

`compose_assembly('lpddr6', 8, id='example', pin_rate_gbit_s=12,
bus_width_bits=64, sustained_efficiency=.75)` combines the public 2e9 B/die with an
explicit eight-die scenario: 16e9 B gross capacity. Its wholly synthetic electrical
scenario is 12e9 bit/s * 64 bits / 8 = 96e9 B/s peak, then *0.75 = 72e9 B/s
conditional sustained bandwidth. The width is for the whole assembly and is not multiplied
by eight. The public “over 10.7 Gbit/s” statement is not treated as an exact rate.

Four HBM4 36e9 B stacks produce 144e9 B gross. Summing theoretical stack peaks assumes
independent full-width interfaces; sustained bandwidth and channel count stay null.
HBM5 composition propagates null specifications instead of assigning zero or low performance.

The DDR5 reference is the specific Kingston KSM64R52BD4-128MB datasheet: 16G addresses
times 64 payload bits / 8, using binary DRAM address count, gives 128 GiB =137438953472 B.
6400 MT/s *64/8 gives 51.2 decimal GB/s theoretical peak. The two 32-bit subchannels
are not host channels. Sustained bandwidth, module power and measured latency remain unknown.

## Placement coverage

`placement.bind_to_demand=true` compares non-excluded declared `assigned_bytes` with
the integrated phase capacity demand. It assumes allocations describe distinct demand
bytes; replicas must not be counted as new coverage. Missing allocations or demand propagate
unknown. Local pool/path checks keep their own verdict. A 160 GiB demand with 64 GiB
assigned leaves 96 GiB unassigned and the whole-demand verdict unevaluated even if all
declared local checks pass. This is a capacity coverage check, not an allocation optimizer
or proof that every required transfer has been routed.

## Conditional scenarios and breakpoints

`decision_study()` returns JSON-serializable `scenarios` with full requests/results,
`sensitivity`, `coverage`, `assembly_examples`, `breakpoints` and a labeled scenario
`envelope`. It performs no I/O and is deterministic. Units in JSON are bytes, bytes/s,
watts and counts; binary GiB is used only for readable example explanations.

The synthetic balanced profile has 256 GiB/object, 128 GiB/s and 50 W/object.
A capacity-rich profile has 512 GiB/object, 64 GiB/s and 20 W/object. They illustrate
count-versus-static-power tradeoffs and are not products. The named sensitivity series
references the balanced profile:

| Scenario | Capacity | Logical BW | Objects | Fabric |
|---|---:|---:|---:|---|
| Baseline | 64 GiB | 128 GiB/s | 1 | passes declared limit |
| Weight factor 3 | 160 GiB | 256 GiB/s | 2 | passes declared limit |
| Weight and KV factors 0.5 | 32 GiB | 64 GiB/s | 1 | passes declared limit |
| Weight factor 3, object BW factor 2 | 160 GiB | 256 GiB/s | 1 | fails 192 GiB/s limit |

The 32–160 GiB and 64–256 GiB/s envelope is a selected scenario range, not a
confidence interval or dated prediction. Quantization metadata, residual buffers and
accuracy effects are not inferred. Prefix reuse reduces declared prefill writes; it does
not automatically reduce decode KV capacity. Dense/MoE support means explicit separate
resident and active weight budgets, not architecture inference. MLA remains unsupported.

## Traceable gaps

`requirement_coverage()` maps memory families, four phases, rack/PSU, placement,
control/data, model budgets and future sensitivities to input/result/code paths and
limitations. Public unknowns are distinct from excluded HBF/NAND. `gap_schema()` supplies
an `input_path` only for fields that the API consumes. Context distributions and thermal
throttling ratios remain `not_implemented`; a placeholder is not claimed as a calculation.
Private measurements can improve supported inputs later under explicit provenance and
measurement conditions. No internal data is collected by this package.

Numeric and unknown/exclusion regression oracles live in `tests/test_exploration.py`;
all prior regression tests remain. Reviewers should check assertions against independent
arithmetic, not treat passing tests as evidence of hardware accuracy.
