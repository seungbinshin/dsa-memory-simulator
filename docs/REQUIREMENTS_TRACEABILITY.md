# Requirements traceability — audited analytical scope

Review date: 2026-10-27 UTC. The independent core reviewer prepared this traceability and numerical review. The owner imported it after the project write-policy check. See AUDIT.md for the separate final project and visual checks.

## Verdict

**PASS for the bounded, explicit-input analytical core reviewed here.** The four material gaps from the initial full-requirements audit now have executable paths: object-level/LPDDR6 assembly, usable capacity, demand-bound placement coverage, and named increase/decrease sensitivity with coverage records. No additional blocking computational defect was found in the reviewed additions.

This is not a hardware-validation verdict. The owner must still bind the final source/output version to the full regression suite, real project checkpoint, generated JSON/CSV/HTML and UI checks. This reviewer ran separate direct numerical probes, not the full suite or checkpoint. A previous test-count claim alone is not substituted for these final checks.

## Original requirements and latest amendments

The initial request was to prepare reproducible materials and a simulator linking memory product facts, rack constraints, AI model/workload development, module capacity/bandwidth/channel configuration, heterogeneous/disaggregated systems, KV control/data architecture and Physical AI; show coverage, insufficiency and missing evidence, including future internal measurements.

Latest amendments override the historical report: HBF/NAND is positioning-only; unpublished HBM5 values stay null; future changes must consider demand growth and efficiency reductions. The implementation is new document-based work, not recovered original source. Unverified historical report numbers are not authoritative inputs.

| Requirement | Actual implementation and quantitative evidence | Verdict / deliberate boundary |
|---|---|---|
| HBM4 12H/16H | catalog.py preserves stack-level facts; 36e9 B/12H stack and derived 11.7e9×2048/8=2.9952e12 B/s theoretical peak. 16H retains known capacity only. api.py preserves stack counts. | PASS for supplied public evidence. Sustained bandwidth, power and channels remain unknown. |
| HBM4E | Known 48e9 B/stack and maximum pin rate remain distinct; unverified bus width and peak stay null. | PASS for evidence/unknown treatment; no fabricated performance. |
| HBM5, DDR7 | Catalog numerical fields remain null; composition and scenarios propagate missing values. | PASS for user-authorized blanks. This is not an implemented product performance prediction. |
| DDR6 | Historical roadmap remains separate from normative candidate values. | PASS for honest boundary. Historical projection is not a current specification. |
| LPDDR6 | Catalog candidates now retain the die. compose_assembly accepts an explicit unit count and independent electrical assumptions. Eight 2e9 B dies produce16e9 B; synthetic12 Gbit/s×64/8 produces96e9 B/s peak. | PASS for conditional assembly arithmetic. No claim of a qualified package, board or public module specification. |
| DDR5 reference | Specific public datasheet reference: binary 16G addresses×64 payload bits/8=137438953472 B;6400 MT/s×64/8=51.2e9 B/s theoretical peak. ECC width and rank count are not multiplied into payload bandwidth. | PASS against the supplied new source notes; public sustained/power/latency remain null. |
| die/stack/module/assembly distinction | Candidates/results retain object_level, component_object_level, units_per_object, required_objects and required_components. required_modules remains a documented compatibility alias. | PASS. Different object counts are not physically interchangeable modules or purchasing recommendations. |
| Gross versus usable capacity | Explicit usable_capacity_bytes becomes the sizing basis; explicit null stays unknown; usable greater than gross is rejected. | PASS. No hidden reserve percentage. Legacy gross-capacity assumptions remain explicit. |
| Module/channel configuration | Capacity/BW determine object count; declared channels per object determine channel count and limit checks. Pin width is not interpreted as host channels. | PASS for explicit configuration budgets, not automatic electrical topology inference. |
| Rack power, PSU and cooling | Object watts plus rack base, wall watts through explicit efficiency, and independent rack/PSU/cooling ceilings. | PASS for static budget arithmetic; transient thermal behavior and redundancy modeling are not claimed. |
| Fabric and scale-up/out | Declared bandwidth ceilings remain independent of memory-object scaling. Prefill expert traffic uses aggregate input TPS; unsupported non-token routing stays unknown. | PASS. No inferred complete network topology. |
| Heterogeneous/disaggregated pools | Per-pool capacity/BW and declared path traffic checks retain local failures. Optional bind_to_demand compares assigned capacity with integrated demand. | PASS for declared allocations and total capacity coverage. No allocation optimizer or automatic traffic coverage. |
| KV control/data and relay | Metadata capacity, control traffic and payload traffic are separate; relay sends payload+control over the control link. | PASS for explicit budgets. Service implementation and tail latency are not inferred. |
| Decode | GQA/MHA-like logical payload and scan model remain intact. | PASS within its documented formula; logical traffic is not measured bus traffic. |
| Prefill | Aggregate arrival rate, new-KV writes and explicit reuse/other traffic affect demand. | PASS. Prefix reuse does not automatically lower decode capacity or decode attention traffic. |
| Training | Explicit weights/activation/optimizer capacity and bytes-per-step×steps-per-second drive configuration. | PASS as an explicit byte-budget model; no automatic optimizer/parallelism/collective derivation. |
| Physical AI/multimodal | Explicit resident/intermediate state and frame bytes×frame rate plus other traffic are calculated; LPDDR6 assembly is now available as a separate candidate path. | PASS for declared state/frame budgets. Sensor scheduling and arbitrary multimodal architecture inference are not claimed. |
| Dense/MoE and other model trends | Resident and active weight budgets and expert traffic are distinct. Public model-trend notes explain input meanings. Coverage labels the supported mode explicitly. | PASS for explicit-budget analysis. Model-name lookup and structure inference are absent. MLA is explicitly unsupported, not disguised as GQA. |
| Future demand increase and decrease | decision_study computes named baseline, weight-growth, precision-efficiency and technology/fabric scenarios. Full requests, assumptions and ratios are returned. | PASS for conditional sensitivity; not empirical forecast probabilities or shipment predictions. |
| Uncertainty and breakpoints | Unknowns remain null; scenario envelope is labeled a selected range, not confidence interval. Exact bandwidth/module and fabric boundaries are exposed. | PASS for bounded uncertainty communication. No probabilistic model is claimed. |
| Coverage/insufficiency/blank | requirement_coverage records family, four phases, infrastructure, placement, control/data, model assumptions and unimplemented/excluded axes with input/output/code paths and limitations. | PASS in core data. Final rendered/exported parity remains an owner release check. |
| Internal measurement inputs | gap_schema gives supported input paths; thermal_throttle_ratio and context_distribution are explicitly not_implemented. Conditions and provenance slots remain empty. | PASS for an honest future-input map. No private data ingestion or automatic effect for unsupported fields. |
| HBF/NAND exclusion | Excluded families cannot size, rank, support placements or supply coverage capacity. | PASS. Historical positioning text does not make them analysis candidates. |
| Reproducible outputs and real verification | Prior CLI/tests remain; new functions are deterministic and side-effect free. New source tests describe the numerical cases below. | Final full-suite, output/UI and checkpoint evidence belongs to the owner. This review does not assert their completion. |

## Independent numerical probes actually run

Execution used Python3.13 with -B and PYTHONDONTWRITEBYTECODE=1. Inputs were created/copied in memory. No source, generated output, cache, test file or project-state write was performed. Selected source hashes were unchanged after the probes.

1. LPDDR6 assembly:8×2,000,000,000=16,000,000,000 B gross; synthetic12e9×64/8=96,000,000,000 B/s peak; explicit0.75 efficiency=72,000,000,000 B/s conditional sustained. Without an efficiency, sustained remained null.
2. HBM unit semantics: a144,000,000,000 B synthetic demand with36,000,000,000 B/stack produced4 required_objects,4 required_components, object_level=stack, channels=null. Four-stack composition preserved144e9 B; HBM5 gross remained null.
3. Usable capacity:64 GiB demand,64 GiB gross and48 GiB explicit usable capacity required2 objects. Changing usable capacity to explicit null made object count null.
4. Demand/placement binding: model growth produced160 GiB demand while64 GiB stayed assigned. The result exposed96 GiB unassigned, coverage status=fail and whole_demand_status=unevaluated. Missing demand propagated null unassigned capacity.
5. Sensitivity: baseline64 GiB/128 GiB/s→1 object; weight×3 gave160 GiB/256 GiB/s→2; weight/KV×0.5 gave32 GiB/64 GiB/s→1. Technology BW×2 restored1 object for growth but still failed the independent192 GiB/s fabric ceiling.
6. Boundary: baseline BW128 GiB/s uses1 object; increasing weight factor enough to add exactly1 B/s required2. A256 GiB/s fabric ceiling passed growth demand at equality; one B/s below failed.
7. Coverage: requested families and four phases were present. MLA was not_implemented, HBF/NAND excluded, thermal/context-distribution gaps had no consumer path rather than a false computed status.

All independent assertions passed. These probes complement rather than replace the project tests.

## Remaining limits that are acceptable for this deliverable

- Placement capacity binding assumes non-overlapping declared allocations. Replicas are not automatically deduplicated, and bandwidth routes are not inferred from total capacity.
- Assembly pin width is for the whole assembly and is not multiplied by die count. Sum-of-component peak requires the documented independent-interface assumption. Controller, packaging and thermal qualification remain external inputs.
- Module rank ordering is a conditional comparison of declared objects and watts; it is not a cross-package compatibility or procurement recommendation.
- Quantization sensitivity omits metadata/residual/accuracy overhead unless the caller budgets it. Prefix reuse scope is limited and explicit. No unsupported MLA or full model architecture is invented to broaden coverage.
- Public unknowns remain unresolved. Quantitative output is a conditional analytical result, not measured hardware performance. TTL/hotness controllers, optimized placement, calibrated latency/energy and private measurement acquisition are outside the claimed implementation.

## Review binding

Source read and independent probes:2026-10-27 approximately08:47–08:50 UTC. The reviewed source hashes were:

| File | SHA256 |
|---|---|
| memory_dsa/api.py | cae3a5f7cbda3e0313568ef44f3db99af6f7c21289f1dce824df3e368e5c881b |
| memory_dsa/integrated.py | aa3fd4cf6ea121eeafe2edbf53ede1827f468f270150c6e97f52f227d8f345a3 |
| memory_dsa/catalog.py | b68c9a069a915740756842b2d1ba594cb1f257ce60f8c6c4e1807ebe45d96000 |
| memory_dsa/exploration.py | 148ca219a089971635f6ed516ff188f16c8d38df9a702bc5cda314a9812a7ba9 |
| tests/test_exploration.py | eb2b0fcd6095af098a60dcd3a19f9e9d1a06a3f27763dbd751ddeb51b4dfa4cd |
| docs/MODELING_EXTENSIONS.md | e2a432765e7d0ac7d656ff37dbe82a59ba1e9a248417094de7089eacd5e4d29a |

This review did not perform fresh web source verification, full-suite execution, UI inspection, final project acceptance or publication. The supplied public notes were compared with the code's statements and formulas. No blocking numerical or semantic mismatch was found within this review scope.
