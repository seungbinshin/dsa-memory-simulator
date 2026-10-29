# Product-strategy correction — authorized local scope

The public release's analytical/visual PASS did not answer the original question: what memory product capabilities should be developed, for which workload, with what evidence and uncertainty? Gate 2/3 are PARTIAL until independent review answers that question. Public main remains e394dcd830915e6a51ee57e23a080ad95054b07d; no push is authorized for this correction before review.

## Chosen implementation

Preserve the existing simulator and add an offline strategy report linked prominently from outputs/index.html. Add a deterministic Python analysis/data module and a self-contained HTML renderer. No new runtime dependency, server, private input, deployment or remote mutation. Use the isolated dsa-memory-simulator-strategy clone, local/product-strategy branch.

The two verified cases are retained as deep dives, not a sufficient completion boundary. The current goal covers all original 19 axes through a shared product-decision map. Reuse a small set of server, memory-tier and edge configurations so training/prefill/decode, assembly, rack and paths constrain the same decisions. Workload/platform cases and reverse-derived design targets do not establish an unserved market.

## Required report flow

1. A visible product-decision summary: which capability to explore conditionally, what not to infer, and which measurement would change the decision.
2. Workload × product matrix with separate capacity upper-bound exclusion, bandwidth-model/peak exclusion, unknown realized performance, and vendor-demonstrated baseline. A nominal/peak envelope never establishes feasibility.
3. Common-unit demand/capability visual: each facet uses one deployment unit and one memory path. Decimal GB/GB/s; gross/nominal and usable remain distinct. Unknowns stay outside numeric coordinates. Logical traffic is explicitly conditional and not a hardware measurement. Capacity lower bound exceeding nominal maximum can rule out that stated single-device configuration; fitting cannot establish deployment feasibility.
4. A small number of linked product directions with target capacity/BW/power/latency ranges or null, source or assumption for each, workload ID and assessment links, current alternatives, disconfirming conditions and specific internal measurements. Profiles change engineering validation priority only through explicit analysis rules and declared objectives. No arbitrary market-attractiveness score, confirmed market-size or all-market-unserved claim.
5. A dated family-state table separates standard, roadmap, sample, component commercial shipment, platform validation and system shipment claims. HBM4/4E/5, DDR6/7 and LPDDR6 each connect to workload-derived targets and a decision, including explicit judgment withheld when product data are absent. Existing DDR5, LPDDR5X and qualified systems are counterexamples, not omitted competitors. A stack, die, module, GPU and whole system are never directly interchanged.
6. Exactly the original 19 axes have evidence, inputs, actual analysis/results, product direction, screen and verification links. No row passes solely because its name or a null appears. Missing physical/product data may justify a decision-withheld result only after the workload target, current alternatives and decision-changing input are analyzed. Available training, prefill, rack, channel and path arithmetic must be applied rather than left as an unconnected function.

## Shared analyses

- Training: declare stored weights, gradients, optimizer states, sharding/replication, prefetch buffers and activations separately. Report per-device memory for that configuration, not a universal bytes-per-parameter rule. An optimizer update traffic model is a partial logical budget; full-step traffic/communication and achieved throughput remain unknown without matching evidence.
- Prefill: compute KV write volume from the public model structure, arrival/input conditions and prefix reuse. Label this as a lower bound, separate from attention/GEMM traffic and compute. A selected TTFT budget derives a required rate but does not predict TTFT.
- Decode and model evolution: preserve the verified Llama capacity/traffic alternatives and current-product counterexamples. Separate MoE total resident parameters from activated parameters; do not apply GQA KV equations to MLA. Quantization, reuse, sharding and recomputation can reduce a product direction's priority.
- Modules/channels: derive capacity units and independent memory-channel requirements separately. Additional DIMMs on one channel do not multiply channel bandwidth. DPC/rate/platform qualification remains explicit.
- Rack/PSU: use compatible DC/AC boundaries, surviving PSU capacity, cooling/busbar limits, other IT and reserve. A total GPU/server power number cannot supply a DRAM-only residual. Numeric examples use explicitly declared non-DRAM budgets; negative headroom is a failed configuration, not zero demand. Peak efficiency and transient overload are not continuous operating specifications.
- Heterogeneous/KV paths: compare the same payload in local and tiered placements. Capacity coverage does not imply usable offload: transfer-rate and transfer-time lower bounds can reject the path. Metadata/control, direct payload, relay ingress and relay egress remain distinct. A central metadata server does not imply a data relay.
- Physical AI: retain the vendor-supported single VLA baseline and identify what concurrent workloads must measure. A memory product loses priority if compute/scheduler or software explains the latency deficit. Vendor median is not p99; SOM power is not DRAM power.
- Internal inputs: name each field, unit, measurement condition, receiving calculation and threshold that changes a decision. Do not collect private corporate or partner data.

## Acceptance

Independent review must inspect all 19 rows against the shared analyses and trace each main direction through evidence → explicit operating assumption → demand/constraint calculation → current product or path bound → target/alternative → falsification/measurement. It must find a real baseline already served, a conditional numeric shortfall, a software/system alternative that changes priority, and a justified withheld judgment. HBM5 and unverified DDR6/DDR7 product specifications remain null; HBF/NAND remains positioning-only and absent from analysis candidates and measurement requirements.

Regression checks must validate equations, units/scopes, component-versus-system status, channel invariance, PSU boundary accounting, directional path checks, quantitative reductions, decision-rule changes and evidence/target distinction. Checking 19 row names alone is insufficient. Actual Ego Lite captures and interaction checks must show the decision meaning, priority changes, family status and trace links on desktop and mobile. A complete analytical decision chain can pass with explicit external-data limitations; unconnected work or absent analysis remains PARTIAL. Market validation, hardware calibration and confidential specifications are not silently included in an analytical pass.

## Local review boundary

This correction remains isolated and unpushed. Existing execution history is preserved separately; publication requires review of the corrected product-strategy purpose.
