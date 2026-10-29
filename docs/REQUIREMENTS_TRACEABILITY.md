# 원요구 19축 — 제품전략 의미 검토 갱신

검토일: 2026-10-29 UTC. 아래 갱신은 공개 근거 → 명시적 workload/운영 가정 → 계산 또는 필요한 정보 → 현재 대안 → 조건부 제품 검토 방향 → 반증/측정의 연결을 독립적으로 검토한 기록이다. 소스 확인 시각은 06:39 UTC이며, 이전 분석표와 검토 바인딩은 이 문서 아래에 원문 그대로 보존한다.

## 현재 판정과 승인 경계

**19축의 공개자료 기반 조건부 전략 연결은 완료 — 제한 있음.** 이름이나 상태값의 존재만으로 통과시킨 것이 아니다. 세 제품 방향(`hbm-throughput-energy`, `capacity-tier-kv`, `edge-qos`)에 실제 phase 예산, component/channel/path/rack 제약, 공개 제품 상태, 기존 대안과 판단 전환 조건이 연결됐다. 미공개 사양 때문에 보류하는 행도 요구 목표와 필요한 정보가 명시돼 있다.

이 판정은 실제 시장 미충족, 제품 우월성, 고객 채택량, 수익성, 출시 시점 또는 하드웨어 qualification을 입증하지 않는다. 우선순위는 선언한 제약에 따른 **엔지니어링 검토 순서**다. 전체 수요가 미확인인 phase의 부분 traffic 하한은 제품의 완전한 BW 요구가 아니다. `eligible`, 할당 합계 일치 또는 nominal/peak 이하는 전체 시스템 적합 판정이 아니다.

**전체 lifecycle 인수와 새 생성물의 시각화 인수는 이 기록에서 대기 상태다.** 최종 build/test/lint, 재현 산출물, 실제 화면과 상호작용 및 해당 판본의 승인 기록은 별도로 확정해야 한다. 이 갱신은 그 실행을 대신하지 않는다.

## 분류와 추적 방법

19개 ID는 `strategy._requirement_trace()`와 `portfolio.axis_trace`가 공유하는 원요구의 범위 축이다. 아래 보존된 **24개 역사적 행**은 이전 계산기 검증의 세부 분류이며 1:1 대응표가 아니다. 24개 산술 항목이나 19개 ID의 개수만으로 전략 완료를 판단하지 않는다.

- **A — 분석 연결 완료:** 명시적 조건의 계산과 현재 대안이 제품 방향 또는 검증 우선순위를 바꾼다. 실측 완료라는 뜻이 아니다.
- **W — 근거 있는 판단 보류:** 분석할 수 있는 부분은 계산했고, 세대/qualification 결정에 필요한 외부 정보와 반증 조건을 특정했다. 미확인값을 성능 부족으로 바꾸지 않는다.
- **X — 범위에 따른 제외:** 사용자 요구대로 포지셔닝만 유지한다.

공통 코드: [portfolio.py](../memory_dsa/portfolio.py)의 순수 예산 함수, `portfolio_study`, `_profile_placement`; [portfolio_evidence.py](../memory_dsa/portfolio_evidence.py)의 `product_families`/출처; [strategy.py](../memory_dsa/strategy.py)의 통합과 원요구 ID 보존. 공개 출처의 `published`, `checked_at`, 제품 기록의 `commercial_status`/`status_as_of`는 서로 다른 값이다. 표준·roadmap·sample·component 출하·system 출하는 구분한다.

화면 경로는 [strategy.html](../outputs/strategy.html)의 `#portfolio-board`(검토 순서), `#portfolio-analyses`(계산), `#portfolio-family-comparisons`(수치 대조), `#portfolio-trace`(19축), `#portfolio-internal-inputs`(측정 조건)다. 이는 renderer의 연결 목표이며 최종 실제 화면 인수의 대체 증거가 아니다. JSON의 `portfolio.axis_trace[].family_assessment_refs`는 해당 수치 대조를, `evidence_refs`는 workload와 PF 공급 근거를 함께 연결한다.

## 19축 최종 의미 추적

아래 분석 ID는 `portfolio.analyses[]`, 비교는 `portfolio.family_assessments[]`, 배치는 `portfolio.profiles[].placement`에서 찾는다. 시험 열은 [tests/test_portfolio.py](../tests/test_portfolio.py)의 실제 회귀 명세를 가리키며, 이 표 자체가 시험 실행 기록은 아니다.

| 원요구 ID | 근거 → 실제 분석/코드 → 제품 판단 | 상태와 남는 한계 | 관련 회귀 명세 |
|---|---|---|---|
| `HBM4` | PF01–PF04; `training-state`, `decode-capacity`, `rack-power`. 설정한 8-stack 용량 목표와 36 GB 출하 기록, 현재 HBM4 system 대안을 비교한다. | A. 지정 구성의 부족만 판정한다. sample·system 합계를 단일 stack의 qualified 수치로 바꾸지 않는다. | `test_family_matrix_is_computed_and_samples_never_become_deployment_pass` |
| `HBM4E` | PF05 및 HBM4 대안; `training-state`의 목표를 48 GB sample과 대조하고 전력의 공동 qualification으로 연결한다. | A. sample의 capacity/BW 최대치를 한 보장 동작점이나 양산 제품으로 합치지 않는다. | `test_family_matrix_is_computed_and_samples_never_become_deployment_pass` |
| `HBM5` | PF06; `training-state`, `decode-capacity`의 요구 목표와 현재 HBM4/4E·샤딩 대안을 먼저 확인한다. | W. 실제 사양은 null. 사양 소유자의 승인된 입력과 동일 동작점 qualification 전에는 세대 선택을 보류한다. | `test_undisclosed_families_remain_null_and_not_bad_products` |
| `DDR6` | PF07, PF12–PF13; `ddr-tier`, `kv-transfer`, `kv-control`. warm retention으로 module 목표를 역산하고 DDR5/MRDIMM·channel·path 대안을 비교한다. | W. 역사적 9600/2028 전망은 현재 제품 입력이 아니다. controller/모듈 구성·실효 성능은 미확인이다. | `test_undisclosed_families_remain_null_and_not_bad_products`; channel 회귀 |
| `DDR7` | PF08의 GDDR7 구분과 DDR5 대안; 동일 `ddr-tier`/`kv-transfer` 요구에 연결한다. | W. 미래 module 목표와 미검증 DDR7 사양을 분리한다. 조사에서 확인하지 못한 것을 비존재로 주장하지 않는다. | `test_undisclosed_families_remain_null_and_not_bad_products` |
| `LPDDR6` | PF09–PF11, PF14 및 P06–P07; `physical-qos`. 표준·die·package/platform 검증과 기존 LPDDR5X/Thor를 구분한다. | W. sensor copy 하한은 계산하지만 전체 concurrent VLA/VLM의 용량/BW/rail W는 미확인이다. SOM과 die/package를 직접 비교하지 않는다. | `test_edge_sensor_copy_is_not_total_inference_traffic`; family 비교 회귀 |
| `decode` | P01–P02/P05/P08; `decode-capacity`, `make_llm_case`, `reverse_object_targets`. 현재 GPU와 정밀도·동시성·계층화 대안을 연결한다. | A. full-scan traffic은 논리 모델이고 runtime 여유·품질·실제 ITL/p99는 별도다. | family 비교 회귀; 기존 `tests/test_strategy.py`의 공개 구조/현재 B300 대안 회귀 |
| `training` | P01, PX01/PX07; `training_budget` → `training-state` → HBM 목표와 rack 전력. 상태·샤딩·BF16 staging·activation 가정을 분리한다. | A. configured capacity와 optimizer-window 하한만 계산한다. forward/backward/collective 전체 traffic는 null이며 전체 BW 확정은 보류한다. | `test_training_sharding_keeps_unsharded_staging_and_activations` |
| `prefill` | P01–P02/PX02–PX03; `prefill_budget` → `prefill-reuse` → cache/compute/전체 traffic 검증 우선. | A. reuse의 KV write 절감만 계산한다. resident 절감·전체 prefill BW·실제 TTFT를 만들어 넣지 않는다. | `test_unknown_total_traffic_is_not_zero_or_lower_bound`; `test_prefix_reuse_does_not_invent_resident_capacity_reduction` |
| `physical_ai` | P06–P07; `edge_sensor_budget` → `physical-qos` → 기존 SOM에서 tail/품질/열 검증 우선. | A. vendor median과 새 p99≤40 ms 목표가 다르다. 전체 allocation/traffic와 실제 memory power는 미확인이다. | `test_edge_sensor_copy_is_not_total_inference_traffic`; `test_edge_p99_target_is_assumption_and_not_vendor_median` |
| `module-capacity-BW-channels` | PF12–PF13; `reverse_object_targets`, `channel_budget`, `ddr-tier`. module 밀도·slot 대안과 독립 channel BW를 분리한다. | A. DIMM 수 증가만으로 channel BW가 증가하지 않는다. usable/효율 가정과 CPU/2DPC/전기적 qualification은 별도다. | `test_modules_on_same_channel_do_not_multiply_bandwidth`; `test_reverse_sizing_honors_reserve_and_efficiency` |
| `rack-power-PSU` | PX04; `rack_residual` → `rack-power`. N+1 DC·AC 효율·냉각·non-DRAM 예산으로 stack별 잔여 상한을 역산한다. | A. 같은 capacity/BW 동작점에서 DRAM W를 검증해야 한다. transient·배선·실측 non-DRAM·thermal dynamics는 미모델링이다. | `test_nplus1_rating_is_dc_and_efficiency_applies_only_to_ac`; `test_negative_rack_residual_is_preserved_and_unknown_limit_blocks_pass` |
| `heterogeneous-disaggregation` | PX03/PX06/PF12; `transfer_budget`, `_profile_placement` → profile별 동일 warm/hot 수요와 path. growth의64-prefix와 efficient의16-prefix를 따로 묶는다. | A. disjoint KV slice만 평가한다. growth의 warm/path 부족을 드러내고 efficient도 hot 용량 미확인 때문에 전체 판단을 보류한다. 임시 복제·weights·전체 active deployment는 포함하지 않는다. | `test_profile_placement_uses_same_demand_and_preserves_growth_shortfall`; `test_known_transfer_bottleneck_is_not_hidden_by_an_unknown_link` |
| `kv-control-data` | PX03/PX06; `evaluate_kv_system` → `kv-control`/`kv-transfer`. direct control과 남는 data 병목, relay 비용을 분리한다. | A. control CPU 처리량·tail·장애 복구·운영비는 미측정이다. link 실패를 DRAM density 시장 공백으로 바꾸지 않는다. | `test_existing_path_results_never_imply_whole_system_fit` |
| `model-trends-demand-growth` | PX05/PX02/P01; `model-trends`와 training/decode/sensor 예산. total/active, 동시성, retention을 구분한다. | A. MoE 활성량은 상주량/BW가 아니다. MLA KV는 미입력이며 미래 연도별 확률·시장 규모를 예측하지 않는다. | `test_moe_active_parameters_not_reused_as_residency_or_kv` |
| `model-tech-demand-reduction` | PX02/P07 및 정밀도·샤딩 가정; `prefill-reuse`, `model-trends`, `training-state`와 profile 검토 순서 전환. | A. 품질·metadata·실제 hit rate·샤딩 통신비는 추가 조건이다. 감소 요인이 기존 제품을 유효한 대안으로 되돌릴 수 있다. | `test_rule_based_priority_changes_when_capacity_pressure_relaxes`; prefix reuse 회귀 |
| `internal-collaboration-inputs` | `internal_inputs`의5개 결정 입력과 [내부 검증 플레이북](INTERNAL_VALIDATION_PLAYBOOK.md)의19축 절차. 단위·측정 조건·수신 필드·임계값·반증 기준 연결. | A. 자동 내부자료 loader는 없다. edge-tail과 thermal/context 분포 등 미지원 모델은 명시적 확장이 필요하다. 비공개 데이터는 취득하지 않았다. | `test_internal_tail_gap_is_an_extension_not_fake_ingestion` |
| `coverage-insufficiency-blank` | `family_assessments`, `axis_trace`, profile별 placement와 세 방향. PF 공급 근거·분석·대조 ID가 연결된다. | A. 조건부 부족, envelope 내 후보, unknown, scope 불일치, 미입증 시장을 분리한다. 18행을18개 제품 적합성 통과로 세지 않는다. | `test_json_determinism_and_no_unserved_market_assertion`; family 비교/placement 회귀 |
| `HBF/NAND` | 범위 제외 → `axis_trace`/`boundaries`; DRAM 외부 저장 위치 설명만 유지. | X. 분석 후보·용량/BW 합계·추천·랭킹·필수 사내 수집 대상으로 추가하지 않는다. | `test_complete_trace_is_connected_to_results_but_preserves_withheld_judgment`; 기존 family 제외 회귀 |

## 독립 검토에서 확인한 수치와 수정 폐쇄

문서 작성자는 소스·계산식·추적 연결을 읽기 검토했다. **별도의 독립 수치 검토자가 같은 최종 core hash에서 Python `-B`로21개 assertion을 실행해21/21 PASS, exit0, 소스 before/after hash 불변을 확인했다.** 문서 작성자가 그 probe나 전체 suite를 실행한 것은 아니다. 검사 범위는 zero-transfer/unknown 경계, 세 profile의 동일 수요·배치 상태, source/test/PF 참조,9개 분석·18개 대조·19축 및 NAND 제외다. 전체 lifecycle/시각화 검증은 위 대기 상태를 유지한다.

- **분석과 대조:**9개 분석,18개 family-assessment,19축이다. 대조18행 중10개는 수치 대조,4개는 unknown,4개는 scope 불일치다. 숫자와 보류 이유를 함께 읽어야 한다.
- **Training:** 선택한4/8-shard 모델은 약317.86/177.86 GB/rank이며,8 stack·90% usable 가정의 nominal 목표는 약44.15/24.70 GB/stack이다. 전체 training traffic를 이 optimizer 하한으로 대체하지 않는다.
- **Prefill:** 선언한 KV write는 reuse0/75%에서 약21.47/5.37 GB/s다. resident 절감이나 전체 prefill throughput을 입증하지 않는다.
- **Path:**40 GiB,4 arrivals/s, miss50%,0.5 s allowance에서85.899 GB/s가 필요해80 GB/s 경로를 넘는다. zero arrivals 또는 zero misses는 요구0이며, 드물지만 양수인 miss는 per-copy deadline을 유지한다. 알려진 부족은 다른 링크가 unknown이어도 숨기지 않는다.
- **Growth 배치:** warm2,748,779,069,440 B 대 usable 예산921,600,000,000 B. 별도 hot40 GiB를 합친 선언 수요2,791,728,742,400 B에 할당을 묶는다. 미배정0은 할당 회계가 맞다는 뜻이며 whole-demand 결과는 `insufficient`다.
- **Efficient 배치:** 선언 수요730,144,440,320 B에서 warm/path 조건은 통과하지만 hot usable capacity가 null이므로 whole-demand는 `unevaluated`다. 이 slice를 별도1-byte decode 대안과 동일 실행 구성으로 합치지 않는다.
- **Rack:** 선언한 냉각28/25 kW 조건에서 DRAM 잔여 상한은50/12.5 W/stack이다. 이는 두 조건의 상한이며 실측 W나 하나의 허용 최소–최대 범위가 아니다.
- **폐쇄한 결함:** zero-transfer의 가짜 deadline 요구, 중복 `#` 화면 경로, 축별 PF 공급 근거/대조 ID 누락, growth64-prefix에16-prefix placement를 적용하던 불일치를 수정 후 확인했다.

## 최종 core 바인딩과 남은 제한

2026-10-29 06:39 UTC에 읽은 core와 별도 독립 probe가 일치하는 바인딩이다. 소스가 변경되면 관련 의미 검토와 실행 근거를 갱신해야 한다. renderer/생성 HTML/화면 캡처는 별도 최종 인수에서 묶는다.

| 파일 | SHA256 |
|---|---|
| `memory_dsa/portfolio.py` | `dc81a26e33ee14b1c6300d2bf68714ea94f5c0e13f5f6145cc6282d488b9a112` |
| `memory_dsa/portfolio_evidence.py` | `83883ee51dabf2c91455b23a53cb1abcccdf6b11419bb6f52fd1e57454980ab3` |
| `memory_dsa/strategy.py` | `bbad0d030d44122f3010d6f17e82c53d780abc8a554b9c9a8cb1eb72571b3870` |
| `tests/test_portfolio.py` | `77bb2598f0b16678da57ac19b276c124d0a38739a2835442bee593f922772c47` |

미측정 sustained BW·usable capacity·DRAM rail·phase 전체 traffic·tail/열/품질은 그대로 남는다. 사양이 없는 세대를 낮은 성능으로 평가하지 않고, 공급 peak와 논리 traffic 하한을 실측 충족으로 표시하지 않는다. 고정 profile은 선택한 설계 시나리오이며 확률 예측이나 실제 서비스 분포가 아니다. 이 의미 검토는 새 웹 출처 검증, 고객 조사, 하드웨어 실험, 전체 시스템 qualification 또는 공개 배포 승인을 수행하지 않았다.

---

아래는 이전 판정의 범위와 오류 수정 이력을 보존한 역사적 원문이다. 과거의 PARTIAL/PASS를 위 최신 판정이나 별도 최종 lifecycle/시각화 인수와 혼동하지 않는다.

<!-- preserved-historical-traceability -->

# Requirements traceability — audited analytical scope

Review date: 2026-10-27 UTC. The independent core reviewer prepared this traceability and numerical review. The owner imported it after the project write-policy check. See AUDIT.md for the separate final project and visual checks.

## Verdict

**2026-10-29 correction: PARTIAL against the original requirements.** The earlier bounded-core PASS below does not cover product development recommendations, evidence-to-target reasoning, or current products versus unmet workload demand. Future sensitivity and input-field coverage were accepted as substitutes for this missing strategy layer. It is being repaired in the isolated local copy; no full-scope acceptance is claimed until independent semantic review.

New acceptance requires workload/product assessments with explicit bound semantics; a demand/capability map using the same deployment unit and memory path; and conditional directions with capacity/BW/power/latency target provenance or null, alternatives, disconfirming conditions and measurements. Unknown specifications must not become market gaps. Existing implementations and historical evidence below remain intact.

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
