# 내부 검증 실행 매뉴얼 — 19개 요구축에서 제품 판단까지

이 문서는 **앞으로 수행할 조사·측정·모델 보완·전략 판단의 실행 계획**이다. 여기 적힌 실험, 사내 사양 조회, 고객 데이터 수집, 하드웨어 계측은 이 문서를 작성하면서 수행하지 않았다. 수치가 있는 절차는 명시적으로 제안한 실험 설계 또는 현재 코드의 조건부 사례이며, 표준이 정한 필수 표본 수나 실제 고객 요구로 간주하지 않는다.

프로젝트 목적, 구조, 화면과 재현 명령은 [PROJECT_GUIDE.md](PROJECT_GUIDE.md), 공개 제품 상태는 [PORTFOLIO_PUBLIC_EVIDENCE.md](../inputs/PORTFOLIO_PUBLIC_EVIDENCE.md), 기존 산술 모델은 [MODELING_EXTENSIONS.md](MODELING_EXTENSIONS.md)를 함께 읽는다. 이 매뉴얼은 제품 구매·개발 확정 전에 어떤 증거를 어떤 조건에서 확보하고, 어디에 넣고, 어떤 가설을 기각할지를 다룬다.

## 1. 검증 단위와 책임

### 1.1 요구축 19개와 측정 공백 5개는 다른 분류다

19개 ID는 `memory_dsa.strategy._requirement_trace()`의 원요구 분류이며, 새 `memory_dsa.portfolio.portfolio_study().axis_trace[].requirement_id`와 연결한다. 과거 `REQUIREMENTS_TRACEABILITY.md`의 24개 세부 행은 구현 검사항목 분류다. 두 목록을 같은 목록 또는 같은 개수의 시험으로 부르지 않는다. 하나의 요구축이 여러 산술 시험을 필요로 하고, 한 측정이 여러 요구축에 근거를 제공할 수 있다.

아래 공백 ID는 `portfolio_study().internal_inputs[].id`에 실제 존재하는 안정 ID다. 문서에서 새로운 19개 측정 ID를 만들어 중복 수집하지 않는다.

| 공백 ID | 확보할 핵심 근거 | 주된 판단 | 책임 역할 |
|---|---|---|---|
| `usable-stack` | 동작점·구성별 할당 가능 용량, peak allocation, reserve | HBM density 증가 전에 기존 구성으로 필요한 용량이 확보되는가 | 메모리·플랫폼 qualification 담당 |
| `memory-rail` | DRAM rail 전력, 비DRAM 부하, 열·PSU 경계 | 용량·BW와 전력 목표를 같은 동작점에서 만족하는가 | 전력·열 계측 담당 및 플랫폼 통합 담당 |
| `migration` | source/destination/fabric의 방향별 지속 BW, copy·queue·tail | warm tier나 분리형 구성이 서비스 여유 시간을 지키는가 | 메모리 계층·전송 경로 담당 |
| `edge-tail` | 동시 센서/VLA/VLM의 종단 p99, 품질, 열 | 기존 LPDDR5X 최적화로 해결되는가, LPDDR6/QoS 변경이 필요한가 | Physical AI 실험 담당 및 응용 품질 책임자 |
| `phase-traffic` | training/prefill 및 관련 decode의 전체 물리 트래픽·compute·stall | 부분 논리 트래픽 하한을 실제 BW 요구로 오인하지 않는가 | 학습·서빙 런타임/컴파일러 계측 담당 |

이 역할은 수행에 필요한 책임이며 실제 조직명·부서 배정을 추정한 것이 아니다. 각 실행 전 한 사람의 **시험 책임자**, 한 사람의 **독립 검토자**, 내부 자료의 **접근 승인자**, 해당 SLO·품질의 **요구사항 책임자**를 기록한다. 측정 작성자가 혼자 제품 개발 결론까지 승인하지 않는다.

| 원요구 ID | 관련 안정 공백 ID | 시작 우선순위 |
|---|---|---|
| `HBM4` | usable-stack, phase-traffic, memory-rail | P0: 사용 가능한 기존 대안 |
| `HBM4E` | usable-stack, phase-traffic, memory-rail | P1: 승인된 샘플·플랫폼이 있을 때 |
| `HBM5` | usable-stack, phase-traffic, memory-rail | P2: 공개 공란 유지, 승인된 내부 입력만 |
| `DDR6` | migration, phase-traffic, memory-rail | P2: DDR5 대안 검증 후 |
| `DDR7` | migration, phase-traffic, memory-rail | P2: 규격·제품의 실재 근거부터 |
| `LPDDR6` | edge-tail, memory-rail, phase-traffic | P1: LPDDR5X 비교 기준점 후 |
| `decode` | usable-stack, phase-traffic, migration | P0 |
| `training` | usable-stack, phase-traffic, memory-rail | P0 |
| `prefill` | phase-traffic, migration | P0 |
| `physical_ai` | edge-tail, memory-rail, phase-traffic | P0 |
| `module-capacity-BW-channels` | usable-stack, migration, memory-rail | P0 |
| `rack-power-PSU` | memory-rail | P0 |
| `heterogeneous-disaggregation` | migration, phase-traffic, memory-rail | P0 |
| `kv-control-data` | migration, phase-traffic | P0 |
| `model-trends-demand-growth` | 5개 모두, 선택한 workload에 한정 | P1: 운영 분포 확인 후 |
| `model-tech-demand-reduction` | 5개 모두, 해당 최적화에 한정 | P0: 신제품 필요성 반증 |
| `internal-collaboration-inputs` | 5개 모두 | P0: 자료 계약·측정 설계 |
| `coverage-insufficiency-blank` | 5개 모두 | P0: 최종 분류·독립 검토 |
| `HBF/NAND` | 없음 | 제외: 필수 조사·측정 없음 |

P0/P1/P2는 **이번 판단을 풀기 위한 제안된 작업 순서**다. 투자 우선순위·시장규모 점수·고객 채택 전망이 아니다. 현재 구성과 소프트웨어 대안이 SLO를 만족하면 미래 세대 실험을 뒤로 미룬다. 미보유 장비·내부 권한을 자동 확보하는 승인으로 이 표를 사용하지 않는다.

### 1.2 네 종류의 작업을 분리한다

- **조사:** 규격 판본, 제품 상태, 호환 플랫폼, 실제 사용 조건과 책임자를 확인한다. 발표·샘플·검증·양산·시스템 출하·고객 workload qualification을 구별한다.
- **측정:** 정해진 구성에서 원시 시계열·카운터·품질을 수집한다. 이 매뉴얼의 실험 설계는 담당자가 사전 승인한 실험 환경에서만 실행한다.
- **모델 보완:** 코드가 받는 입력에 근거를 명시해 연결한다. 아직 소비하지 않는 입력은 별도 구현·회귀 검증을 거쳐야 한다.
- **전략 판단:** 동일 품질/SLO에서 기존 제품·배치·정밀도·소프트웨어 대안이 남는지 확인한 뒤 제품 목표를 유지·완화·보류한다. 데이터 공란만으로 시장 공백을 선언하지 않는다.

## 2. 공통 실행 프로토콜

### 2.1 시험 전 고정할 기록과 계측 경계

모든 시험 계획서에 `requirement_id`, `gap_id`, 가설, 비교 대안, 측정 책임자, 독립 검토자, 성공/반증 기준, 중단 조건을 먼저 쓴다. 결과를 본 뒤 유리한 SLO·대상 workload·제외 규칙으로 변경하면 새 시험 판본으로 분리한다.

공통 환경 기록: 장비 SKU·보드 판본·실험용 익명 ID, DRAM 구성/채널/속도, BIOS·firmware·driver·OS·런타임·커널·모델 revision, 정밀도와 layout, NUMA/CPU affinity, page/cache 정책, 전력·클록 모드, 입력 전압, 냉각 조건, 센서 교정일/오차, 계측 도구·카운터 정의, seed, 데이터셋 버전과 공개 가능 범위. 원시 고객 prompt·개인정보·파트너 고유 식별자는 결과 공유에 필요하지 않으면 수집하지 않는다.

용량은 B, 전송률은 B/s, 전력은 W, 시간은 코드 필드에 맞춰 s/ms/ns로 기록한다. GB=`10^9 B`, GiB=`2^30 B`를 명시한다. DQ 핀 수·pseudo-channel·DDR subchannel·독립 host channel을 각각 기록한다. 단일 die/stack/package/module/GPU/SOM/system/rack의 scope가 다르면 합계나 평균으로 직접 비교하지 않는다. 순수 양방향 합계 BW와 단방향 정격도 분리한다.

**실제 코드의 근거 수량 형식**은 `strategy.quantity()`가 반환하는 `{value, min, max, unit, scope, kind, sources, note}`다. `value=null`이어도 공개 하한/상한인 `min/max`가 알려질 수 있다. 이것을 자동으로 중간값으로 바꾸지 않는다. 범위가 SKU 집합인지, 엄격한 하한인지, 실험 CI인지 `kind/note`로 구분한다. 서로 다른 SKU의 최대 용량·최대 BW·최소 W를 하나의 가상 동작점으로 합치지 않는다.

### 2.2 제안하는 파일럿과 반복 설계

아래 숫자는 비용과 변동성을 알아보기 위한 **파일럿 출발점**이다. 모든 장비·tail 수준에 충분한 표본 수라는 보장은 없다.

1. 단일 구성의 기능·계측 검증 후, 예를 들어 입력 순서 seed 3개 × 독립 실행 5회를 계획한다. 장비별 변동을 주장하려면 보드/모듈 개체를 별도 층으로 표집하고, 한 보드의 반복을 여러 독립 제품 표본으로 세지 않는다.
2. 예를 들어 60초 warmup 후 10초 창 3개에서 처리량·전력·온도 추세를 확인한다. 안정화가 안 되면 정해진 허용 시간까지 연장하고, 끝내 불안정하면 원인을 기록한다. 긴 초기화나 열 soak가 필요한 장비에서는 시간을 늘린다. cold start는 별도 시험으로 남긴다.
3. 구성 A/B 순서를 seed별로 교차 또는 무작위화하고 동일 입력을 재생한다. warm-cache/cold-cache 조건을 섞어 평균내지 않는다. 경쟁 부하가 있는 경우 그 종류·세기·시작점을 기록한다.
4. 평균·중앙값뿐 아니라 각 실행의 분포, 최대 resident allocation, p95/p99, 오류/timeout, drop·재시도, throttling 구간을 보존한다. 실패 요청을 latency 표본에서 제외하면 실패율을 별도 보고하고 제외 규칙을 고정한다.
5. 본 시험 표본 수는 파일럿의 분산·자기상관, 구별하려는 최소 효과, SLO 위반률 목표로 정한다. 반복 횟수만 늘려 계측 편향·하드웨어 개체 부족을 해결했다고 보지 않는다.

### 2.3 tail·불확실성·판정 규칙

요청별 도착·시작·완료 시각과 timeout을 수집한다. TTFT, 토큰 간 ITL/TPOT, copy 시간, 제어 주기 p99는 서로 다른 지표다. 한 지표의 median을 다른 지표의 p99로 사용하지 않는다. 클라이언트와 서버 시계를 섞으면 동기화 오차도 기록한다.

독립 요청이라고 입증할 수 있는 표본에는 순서통계 기반 분위수 구간이나 적합한 재표집을 사용한다. burst·세션 상관이 있으면 session/run/time-block 단위 재표집 또는 run 간 분포를 사용하고 block 길이 선택을 보고한다. 예를 들어 95% 구간을 택할 수 있지만 신뢰수준은 요구사항 책임자가 사전에 정한다. p99에서 꼬리 표본이 부족하면 `insufficient_tail_evidence`로 남긴다. p999를 p99 표본으로 외삽하지 않는다.

제안된 판정: p99 신뢰구간 **상단**이 목표 이하이고 품질·전력·오류율 조건도 충족하면 해당 구성의 조건부 통과, 구간 **하단**이 목표를 넘으면 실패, 그 사이면 미확정이다. 모든 출력 수치에 측정 오차와 실행 변동을 분리한다. 무실패 N회에서 약 `3/N`은 독립 Bernoulli 시행과 95% 단측 구간의 근사적 실패율 상한일 뿐이다. 상관된 프레임이나 모든 상황에 보편 적용하지 않는다.

물리 BW가 논리 식보다 작거나 커도 즉시 버그로 판단하지 않는다. cache reuse, write amplification, metadata, padding, 복제, 재전송, 카운터 영역이 무엇을 포함하는지 대조한다. 불일치 허용폭은 센서 오차·모델 범위를 근거로 사전에 정한다. 필요한 물리량의 일부가 없으면 전체 합계는 `null`; 확인된 하한은 별도 보존한다.

### 2.4 승인·자료 보존·내부 overlay

원시 계측, HBM5 등 비공개 사양, 고객 workload 요약의 민감한 값은 **이 저장소 밖의 승인된 INTERNAL 저장 위치**에 둔다. Git 저장소가 private여도 내부 원문 저장소로 사용하지 않는다. `.gitignore`만으로 비밀 보호를 보장하지 않는다. 자료 소유자가 재사용·가공·보관·공유 범위를 승인하고, 공개 배포본에는 값이 비어 있는 스키마와 합성 회귀 입력만 남긴다.

제안된 INTERNAL 구조(자동 생성·로더 아님):

```text
<INTERNAL_ROOT>/<study_id>/
  protocol.json             # 승인된 가설·SLO·설계·실험 판본
  evidence/<run_id>.json    # 측정 조건, 요약, 원시 파일 hash, 접근 등급
  overlays/<candidate>.json # 내부 관측치; 공개 카탈로그와 분리
  requests/<case>.json      # 실제 CLI가 허용하는 필드만 복사한 실행 입력
  results/<case>.json       # 민감 값이 포함되므로 내부에만 보관
  decision.md              # 반증 포함 판단과 독립 검토 서명
```

HBM5 등 비공개 사양용 **빈 내부 기록 예시**다. 실제 값·소스 경로·인물 이름을 공개 저장소의 이 템플릿에 채우지 않는다. `measurement`와 `candidate_values`는 제안된 작업 기록이며 CLI 입력 스키마가 아니다.

```json
{
  "requirement_id": "HBM5",
  "gap_ids": ["usable-stack", "memory-rail", "phase-traffic"],
  "classification": "INTERNAL",
  "approval_reference": null,
  "source_reference": null,
  "measurement": {
    "scope": "one qualified HBM stack operating point",
    "hardware_revision": null,
    "temperature_c": null,
    "voltage_v": null,
    "workload_revision": null,
    "sample_count": null,
    "independent_run_count": null,
    "uncertainty_method": null,
    "raw_evidence_sha256": null
  },
  "candidate_values": {
    "capacity_bytes": null,
    "usable_capacity_bytes": null,
    "sustained_bw_bytes_s": null,
    "power_w": null,
    "channels_per_module": null,
    "p99_latency_ns": null
  },
  "qualification_status": "not_measured"
}
```

**현재 자동 overlay loader는 없다.** 담당자가 공개 baseline request의 복사본을 내부에서 만들고, 단위·scope·측정 조건을 독립 검토한 뒤 허용 필드에 명시적으로 옮긴다. `api.obj()`는 모르는 키를 거절하므로 측정 메타데이터·source reference를 실행 입력의 임의 키로 추가하지 않는다. 후보의 `provenance="local_override"`와 내부 evidence 기록을 case ID로 연결한다. 이것은 공개 `catalog.py`/`portfolio_evidence.py`를 내부 값으로 덮어쓰는 절차가 아니다.

HBM4/4E/5 후보는 실행 API에서 `family="HBM"`을 쓰고 세대는 `id`와 내부 evidence에 보존한다. 현재 `family="HBM5"` 같은 미지원 문자열을 넣지 않는다. 또한 API 후보 object level은 die/stack/package/module/assembly이며 GPU/SOM 전체를 임의로 module로 재명명하지 않는다. 전체 GPU/SOM 비교는 `strategy.py`의 동일 scope 비교에 맡기거나 검토된 확장으로 처리한다.

허용된 내부 파일이 이미 준비된 뒤 사용할 수 있는 **현재 CLI**는 다음과 같다. 아래는 실행 예시이며 이 문서 작성 시 실행하지 않았다. `INTERNAL_ROOT`는 담당자가 승인된 저장 위치로 지정한다.

```sh
python3.13 -B -m memory_dsa evaluate --input "$INTERNAL_ROOT/requests/kv.json" --output "$INTERNAL_ROOT/results/kv.json"
python3.13 -B -m memory_dsa integrated --input "$INTERNAL_ROOT/requests/phase.json" --output "$INTERNAL_ROOT/results/phase.json"
python3.13 -B -m memory_dsa compare --input "$INTERNAL_ROOT/requests/comparison.json" --output "$INTERNAL_ROOT/results/comparison.json"
```

`compare`의 최상위는 `{request, scenarios}`이고 각 scenario는 `{id, year, scenario}`다. 각 행의 factor는 같은 baseline request의 `scenario`에 얕게 합쳐지며 행 사이에 누적되지 않는다. `year`는 조건부 시나리오 라벨이지 예측 검증이 아니다. `portfolio.py`의 순수 함수들은 Python API이며 현재 독립 portfolio CLI나 내부 파일 자동 수집기를 가정하지 않는다. 기본 `demo`는 코드의 공개·합성 사례를 다시 생성하므로 내부 overlay를 자동 적용하지 않는다. `evaluate/integrated/compare` 출력의 상위 내부 디렉터리는 실행 전에 존재해야 한다.

### 2.5 코드 결과를 읽을 때의 차단 조건

`api._analyze()`는 실패한 알려진 제약이 없으면 후보 `status="eligible"`을 반환하면서, 미평가 제약 때문에 `ranking_eligible=False`일 수 있다. 따라서 다음을 함께 확인한다.

1. 각 `candidates[].constraints`의 `pass/fail/unevaluated`와 `reasons`를 읽는다. `eligible` 하나만으로 전체 시스템 적합을 선언하지 않는다.
2. `ranking_eligible`과 최상위 `comparison_conclusive`가 참이어도 입력된 정적 제약 범위의 순위다. `whole_system_validated=False`, `predictions.ttft_ms/itl_ms/p99_ms/tokens_per_joule=null`은 실제 한계다.
3. `placement.coverage`는 non-overlapping capacity 할당 검사다. 새 포트폴리오에서는 `profiles[].placement.evaluation.coverage.status`의 pass가 선언된 KV slice의 배분 누락이 없다는 뜻이다. 같은 `evaluation.status`와 `coverage.whole_demand_status`를 함께 읽는다. `whole_system_validated=False`이며 실제 pool 용량·모든 트래픽 경로·이동 중 복제·tail을 보증하지 않는다.
4. `portfolio`의 `conditional_headroom` 역시 입력한 조건의 여유다. `unknown`·`not_comparable`·부분 하한을 통과로 바꾸지 않는다. `rack_residual()`은 `residual_memory_dc_w`와 `memory_w_per_object_ceiling`의 음수를 보존한다. 할당 가능량 표시인 `allocatable_memory_dc_w`만 0 이상으로 자른다. `baseline_already_exceeds_ceiling=True`이면 이미 비DRAM 기준 부하가 상한을 넘은 상태이며, 할당량 0을 안전한 통과로 읽지 않는다.
5. `catalog.gap_schema()`의 `thermal_throttle_ratio`, `context_distribution`은 `input_path=null`, `implementation_status="not_implemented"`다. 측정 기록은 유용하지만 이를 request에 넣어 자동 반영됐다고 주장하지 않는다. 열 시계열/분포/tail 모델은 별도의 코드 확장·회귀 대상이다.

### 2.6 현재 portfolio 수신 계약의 정확한 의미

`portfolio_study().internal_inputs[]`의 `measurement_condition`은 `verification_method`의 별칭이고, `decision_threshold`는 `threshold` 수량의 별칭이다. `receiver_field`는 함수 인수로 **수동 전달할 경로를 설명하는 문자열**이며 자동 바인딩 코드가 아니다. `status`는 현재 `missing_internal_measurement`다.

| gap ID | 실제 `receiver_field`와 실행 가능 범위 | 입력 전 검토 |
|---|---|---|
| `usable-stack` | `compare_quantity(available)`의 usable-capacity quantity를 수동 구성 | required와 available의 unit/scope를 정확히 맞춘다. 현재 요구 threshold의 scope는 `one HBM stack usable allocation`이다. 명목 stack 용량과 직접 비교하지 않으며 GPU 전체 allocator 결과를 근거 없이 나누지 않는다. |
| `memory-rail` | `rack_residual.proposed_memory_w`; `non_dram_dc_w`는 별도 갱신 | 동일 rack·동작점의 W 경계와 object count를 맞춘다. 현재 12.5 W/stack threshold는 25 kW cooling 등 설정의 산술이며 모든 시스템의 요구가 아니다. |
| `migration` | `transfer_budget.source_bytes_s / destination_bytes_s / fabric_bytes_s` | 같은 방향·payload·접근 패턴의 지속값을 각각 넣는다. 현재 약85.90 GB/s는 40GiB·miss·arrival·deadline 시나리오에서 도출된 값이다. 일부 값이 null이어도 `known_path_ceiling_bytes_s`보다 요구가 크면 `conditional_shortfall`이며, 전체 `path_limit_bytes_s`는 여전히 null이다. 알려진 한도를 넘지 않았어도 나머지 값이 없으면 `unknown`이다. |
| `edge-tail` | `receiver_field=null`, `ingestion_status="required_model_extension"` | p99 원시 분포·CI를 내부 evidence로 보존한다. `edge_sensor_budget()`가 센서 하한을 계산해도 measured p99 ingestion이 구현됐다는 뜻은 아니다. |
| `phase-traffic` | `training_budget.other_traffic_bytes_s / prefill_budget.other_traffic_bytes_s` | 모델 하한 항목과 중복되지 않는 동일 시간창의 나머지량만 넣는다. 논리 하한+물리 잔여의 합은 여전히 조건부 모델이며 원시 물리 총량과 별도 검증한다. |

실측값으로 순수 함수를 호출한 결과가 기본 `portfolio_study()` 사례에 자동 반영되는 것은 아니다. 내부 driver에서 명시적으로 호출하고 결과를 보존하거나, 입력 계약을 확장하는 별도 소스 변경·검토가 필요하다. threshold를 넘나드는 제품 결론에는 환경·품질·SLO의 추가 조건이 붙는다.

또한 새 포트폴리오의 DDR5 기준점은 PF12의 **Micron 128 decimal GB / 최대5600 MT/s**이며, 레거시 explorer의 S12 **Kingston 128 GiB / 6400 MT/s**와 다르다. source ID, capacity B와 transfer/s를 함께 선택한다. 한쪽 용량과 다른 쪽 속도를 합친 가상 부품을 만들어 비교하지 않는다.

## 3. 원요구별 실행 카드

각 카드는 공통 프로토콜을 전제로 하되, 실제로 바꿀 입력·시험 순서·반증 기준을 구체화한다. 아래 회귀 시험은 **현재 존재하는 시험**과 **추가 제안**을 구별한다. 이 문서는 시험을 추가하거나 실행했다는 기록이 아니다.

### 3.1 `HBM4` — 현재 제품으로 해결되는 범위를 먼저 확정

- **공백·목적·책임·우선:** `usable-stack`, `phase-traffic`, `memory-rail`; 기존 qualified HBM4 구성이 용량/BW/전력을 동시에 충족하는지 확인한다. 메모리·플랫폼 qualification 담당이 P0으로 수행하고 workload 책임자가 SLO를 정한다. 조사→측정→전략 판단 순서다.
- **필드·단위:** 정확한 SKU/stack 수/용량 B, usable B, phase별 read/write B/s, DRAM W, 온도 °C, 실제 동작 속도, 오류율, allocation peak B, TTFT/ITL ms. 공개 PF01–PF04의 표준·component 출하·system shipping과 실제 보유 플랫폼 상태를 분리한다.
- **환경·획득:** 승인된 HBM4 탑재 플랫폼의 제조사 문서와 allocator/메모리 카운터/rail telemetry를 결합한다. rail 계측이 없으면 GPU board W만 기록하고 stack W는 null로 남긴다. GPU 전체 usable을 stack 수로 나누려면 접근·striping·reserve 배분 근거가 필요하다.
- **절차:** 동일 모델에서 작은 용량 기준점→목표 batch/context→메모리 압박점 순서로 시험한다. training과 decode를 분리하고, allocation trace와 물리 traffic 및 W를 같은 시간창에 맞춘다. 그 뒤 샤딩/정밀도 대안을 같은 SLO로 비교한다.
- **통제·표본:** 모델·커널·동작 속도·온도·전력모드·입력 seed를 고정하고 구성 순서를 교차한다. 공통 파일럿을 쓰되 SKU/보드별 표본을 별도 계층으로 보고한다. peak allocation의 run 간 범위와 BW/W 계측 오차를 함께 제시한다.
- **수락·반증:** 요구 용량의 상측 불확실성을 usable 용량의 하측 근거가 덮고 동일 동작점의 SLO·W·열·오류 조건이 통과하면 기존 제품 대안 유지. 기존 HBM4가 통과하면 HBM5 density 필수 가설은 반증된다. 병목이 compute/fabric이면 HBM BW 증설 결론을 보류한다.
- **삽입 경로:** 내부 request `candidates[].capacity_bytes/usable_capacity_bytes/sustained_bw_bytes_s/power_w`, `object_level="stack"`, `provenance="local_override"`; `portfolio.reverse_object_targets(capacity_bytes, logical_bw_bytes_s, objects, usable_fraction, bandwidth_efficiency)`에는 근거 있는 집계값과 효율만 넣는다. `usable-stack` receiver와 public `product_families()[id="HBM4"]`의 사실은 별도로 유지한다.
- **회귀·결정:** 기존 `test_hbm_stacks_unknown_channels_and_no_implicit_sustained`, `test_assembly_usable_capacity_drives_sizing`를 유지한다. 추가 제안: 같은 capacity/BW/W 동작점 ID가 다르면 묶음 qualification을 거절하는 시험. 통과 시 새 세대 대신 기존 구성·SW 최적화를 우선하며, 실패 시 부족한 물리량만 제품 목표로 남긴다.

### 3.2 `HBM4E` — sample envelope를 동시 보장점으로 검증

- **공백·목적·책임·우선:** `usable-stack`, `phase-traffic`, `memory-rail`; PF05 및 기존 공개 sample 정보의 용량·속도·BW를 실제 조합에서 확인한다. 샘플 qualification 담당이 P1으로 수행한다. 승인된 샘플이 없으면 조사 단계에서 멈추며 장비 확보를 필수 승인으로 간주하지 않는다.
- **필드·단위:** sample revision/stack height/용량 B, pin rate bit/s/pin, 검증된 interface 폭 bit, 지속 B/s, W, usable B, 온도·전압 범위, 수정 이력, qualification 조건. 서로 별개인 최대16 Gb/s와 최대3.6 TB/s를 한 점으로 합치지 않는다.
- **환경·획득:** 동일 controller·package·보드와 sample 지원 SW에서 공급자 시험 조건을 확인하고 승인된 계측으로 재현한다. 공개 출하/양산 상태는 source date와 scope를 기록하며 시간 경과로 자동 갱신하지 않는다.
- **절차:** 먼저 검증된 보수 동작점에서 기능·오류·할당 가능 용량을 측정한다. 허용된 범위 안에서 속도·온도별 BW/W를 쌍으로 수집하고 동일 workload를 반복한다. sample 한계와 SW 미지원 실패를 DRAM density 실패로 섞지 않는다.
- **통제·표본:** sample lot/revision별로 분리한다. 공통 반복 설계에 동작점별 열 안정화와 test order를 추가한다. 적은 sample 개체는 생산 모집단 대표성이 없다고 명시하고 평균 하나로 양산 qualification을 선언하지 않는다.
- **수락·반증:** 목표 용량·지속 BW·rail W가 같은 승인 동작점에서 함께 성립해야 후보 유지. 요구가 기존 HBM4/샤딩 대안으로 충족되면 HBM4E 전환의 필수성은 반증된다. 속도 최대점만 충족하거나 sample 상태만 확인되면 출시/채택 판단은 보류한다.
- **삽입 경로:** 공개 record는 `portfolio_evidence.product_families()[id="HBM4E"].records[]`의 상태·근거만 유지한다. 내부 측정은 HBM 후보의 usable/BW/W 및 `reverse_object_targets()` 인수로 명시적 연결한다. shipping certainty·sample 수율·동작점별 surface는 현재 API 자동 모델이 아니므로 별도 evidence로 둔다.
- **회귀·결정:** 기존 `test_public_object_levels_and_lpddr_are_preserved`, `test_unknown_not_zero_or_insufficient`, 새 `tests/test_portfolio.py`의 `test_vendor_ranges_are_envelopes_not_continuous_qualified_products`, `test_family_matrix_is_computed_and_samples_never_become_deployment_pass`를 유지한다. 추가 제안: 실제 qualification 기록에서 operating-point ID가 다른 극값을 결합하면 거절하는 시험. 결과로 sample 평가 지속·기존 제품 유지·조건부 target 조정 중 하나를 선택한다.

### 3.3 `HBM5` — 비공개 사양은 공란, 목표와 사실을 분리

- **공백·목적·책임·우선:** `usable-stack`, `phase-traffic`, `memory-rail`; 제품 사양을 추정하지 않고 workload에서 도출한 목표가 현재 대안으로 해결되는지 검토한다. 제품 사양 소유자와 qualification 역할이 P2로 담당한다. 내부 접근이 승인되지 않으면 공개 공란 유지가 정상 결과다.
- **필드·단위:** 위 빈 INTERNAL 템플릿의 capacity/usable B, sustained B/s, DRAM W, channel count, p99 ns, 동일 operating-point 식별자와 자료 판본. 공개 PF06의 공정·architecture 방향으로 이 값들을 채우지 않는다.
- **환경·획득:** 승인된 내부 사양 소유자가 허용된 요약 필드만 제공한다. 원문 위치·숫자·식별자는 내부 기록에만 둔다. 실제 sample이 없으면 문서 조사만 수행하며 측정·qualification 완료로 표시하지 않는다.
- **절차:** (1) 조사에서 필드별 승인/공개 가능 범위 확인 (2) 현재 HBM4/4E/stack 수/샤딩 대안으로 같은 요구 재평가 (3) 남는 목표만 내부 사양과 같은 scope로 대조 (4) sample이 합법적으로 준비된 이후 3.1/3.2 절차로 측정한다.
- **통제·표본:** 사양서 판본과 목표 시나리오 판본을 고정한다. 문서상의 min/max는 실험 CI가 아니다. sample 수 0이면 `not_measured`; 향후 lot/동작점별 반복과 계측 오차 계획을 별도 승인한다.
- **수락·반증:** null은 unknown이며 낮은 성능이 아니다. 현재 대안이 요구를 만족하면 HBM5 필수 가설을 기각한다. 내부 값이 목표를 덮어도 실제 joint qualification 전에는 개발/출시 성공으로 판단하지 않는다.
- **삽입 경로:** `portfolio_evidence.product_families()[id="HBM5"]`와 공개 `catalog.public_catalog()[id="hbm5"]`는 공란을 유지한다. 내부에서만 `candidates[].family="HBM"`, `id`에 세대 구분, `provenance="local_override"`로 명시적 request를 만든다. 자동 내부자료 loader는 없다.
- **회귀·결정:** 기존 `test_hbm_stacks_unknown_channels_and_no_implicit_sustained`, `test_unknown_and_zero_are_not_the_same`를 유지한다. 추가 제안: 내부 evidence가 공개 demo/HTML/CSV에 유입되지 않는 합성 canary 시험. 목표는 유지할 수 있어도 공개 근거만으로 HBM5 사양·출시·우월성을 확정하지 않는다.

### 3.4 `DDR6` — DDR5 대안을 넘어서는 요구를 먼저 역산

- **공백·목적·책임·우선:** `migration`, `phase-traffic`, `memory-rail`; warm KV 목표가 메모리 세대 문제인지 채널/슬롯/path 문제인지 구별한다. 메모리 controller·서버 qualification 담당이 P2 조사, 기존 DDR5 측정 담당이 P0 기준점을 맡는다.
- **필드·단위:** 규격 판본/날짜, 호환 controller, qualified 모듈 용량 B·데이터율 transfer/s·payload 폭 bit·독립 채널 수, 1DPC/2DPC, usable B, 지속 B/s, 모듈 W, 방향별 path B/s와 copy s. PF07의 역사적9600 Mbps/2028은 현재 제품 값이 아니다.
- **환경·획득:** 우선 보유 DDR5 구성의 CPU/NUMA·DIMM population·협상 속도를 공식 자료와 계측으로 확인한다. DDR6 실제 사양·플랫폼은 승인된 자료가 있을 때만 추가한다. sample이 없으면 DDR6 실험을 실행한 것으로 기록하지 않는다.
- **절차:** 16/64 warm-prefix 등 현재 조건부 사례를 실제 retention 분포로 교체해 용량을 산정한다. 1DPC/2DPC·독립 채널 수를 분리해 read/write mix를 재생하고, 같은 KV copy가 fabric 상한에 걸리는지 함께 측정한다.
- **통제·표본:** payload 크기·NUMA affinity·cache 상태·DIMM rank·온도를 고정한다. 채널별/소켓별 공통 반복과 여러 접근 패턴을 층화하고, 속도 하향 협상은 실패를 숨기지 않고 별도 조건으로 기록한다.
- **수락·반증:** 기존 DDR5의 슬롯/채널 확대·retention 정책으로 품질/SLO/전력이 맞으면 DDR6 필수 가설 기각. 메모리 BW를 높여도 path 또는 queue가 제한하면 DDR6 속도 목표를 전략적 해법으로 확정하지 않는다.
- **삽입 경로:** `portfolio.channel_budget(modules, independent_channels, transfers_per_s, data_width_bits, efficiency, demand_bytes_s)`와 `transfer_budget(source_bytes_s, destination_bytes_s, fabric_bytes_s, ...)`; 기본 API 후보 `capacity_bytes`, `usable_capacity_bytes`, `sustained_bw_bytes_s`, `channels_per_module`. DDR6 미확인 public record는 null을 유지한다.
- **회귀·결정:** 기존 `test_ddr5_public_peak_does_not_become_sustained`, `test_constraints_boundaries`와 새 `test_modules_on_same_channel_do_not_multiply_bandwidth` 유지. 추가 제안: 2DPC 협상 속도 fixture. 결과는 새 규격 필요성, 기존 구성 변경, 또는 전송 경로 개선으로 나눈다.

### 3.5 `DDR7` — 존재·규격·적용 시점부터 조사

- **공백·목적·책임·우선:** `migration`, `phase-traffic`, `memory-rail`; 미검증 DDR7을 기존 수요의 확정 해결책으로 이름 붙이지 않는다. 규격 근거 검토 역할과 제품 아키텍처 책임자가 P2로 조사한다.
- **필드·단위:** 실제 DDR7 규격 식별자·판본·공표 상태, general-purpose DRAM scope, controller/모듈 qualification 조건, 확보된 경우에만 용량 B·지속 B/s·W·채널. PF08의 GDDR7 자료는 DDR7 사양 입력이 아니다.
- **환경·획득:** 공개 원문 또는 승인된 내부 사양 소유자로부터 확인한다. 규격 접근 제한은 우회하지 않는다. 자료가 없으면 “이번 조사에서 미확인”으로 남기며 실재 부정이나 값 추정을 하지 않는다.
- **절차:** DDR5/현재 대안의 동일 SLO 결과를 먼저 정리하고, 미충족 요구를 세대 중립적인 B/B/s/W와 호환성 제약으로 적는다. 새 규격이 확인되면 scope/전기적 호환성 검토 후에만 별도 승인된 sample 시험을 설계한다.
- **통제·표본:** 문서 판본·확인일·대상 scope를 고정하고 독립 검토자가 DDR7/GDDR7 혼동을 확인한다. 조사 단계는 hardware 표본수 0이다. 나중의 측정 계획은 3.4를 따른다는 계획만 기록하고 CI를 만들지 않는다.
- **수락·반증:** 신뢰할 수 있는 규격/제품 근거가 없으면 평가 보류. 현재 DDR5/DDR6로 확인된 대안이 같은 요구를 충족하면 특정 DDR7 세대를 필수로 제안하는 가설이 기각된다.
- **삽입 경로:** `product_families()[id="DDR7"].records[]`의 public 수량은 미확인 동안 null. workload 목표는 `reverse_object_targets()`와 `channel_budget()`의 조건부 입력으로 표현하며 목표를 public spec에 복사하지 않는다. 신규 topology 지원은 별도 모델 개선이다.
- **회귀·결정:** 기존 `test_catalog_corrections`, `test_unknown_not_zero_or_insufficient` 유지. 추가 제안: GDDR7 출처가 DDR7 수량을 채우면 검토 실패하는 provenance fixture. “DDR7 개발 확정” 대신 세대 중립 성능 요구 또는 조사 보류로 인계한다.

### 3.6 `LPDDR6` — die/package/SOM와 응용 qualification 분리

- **공백·목적·책임·우선:** `edge-tail`, `memory-rail`, `phase-traffic`; LPDDR5X SOM 대안 대비 LPDDR6의 실제 의미를 확인한다. 저전력 메모리·플랫폼 qualification 역할이 P1로 수행한다.
- **필드·단위:** die/package 용량 B, package 구성, DQ/subchannel/host payload 폭 bit, 데이터율 bit/s/pin, usable SOM B, sustained B/s, DRAM rail W, 전체 SOM W, tail ms, 열 조건. PF09–PF11의 표준·16Gb die·16GB package·플랫폼 검증 scope를 보존한다.
- **환경·획득:** 실제 호환 controller/보드에서 공개 또는 승인된 datasheet와 계측을 연결한다. 24 DQ 구조를 유효 payload BW로 자동 환산하거나 LPDDR5X Thor 결과를 LPDDR6 실측으로 복사하지 않는다.
- **절차:** 구성/호환성 확인→메모리 접근 pattern별 지속 BW/W→단일 VLA 기준점→동시 camera/VLM→열 soak 순서로 진행한다. 가능하면 같은 응용 품질에서 copy 제거·스케줄링 대안도 비교한다.
- **통제·표본:** precision·camera 해상도/fps·controller clock/DVFS 상태·전력모드·냉각을 고정한다. 공통 반복에 DVFS 전환 구간과 장시간 tail을 별도 층화한다. platform 차이가 있으면 메모리 세대만의 효과라고 인과 해석하지 않는다.
- **수락·반증:** 기존 LPDDR5X에서 SLO·품질·열이 통과하면 density/BW 전환 필수성을 기각한다. LPDDR6가 평균 BW만 높고 p99·W가 나빠지면 해당 동작점은 통과가 아니다.
- **삽입 경로:** `compose_assembly(component_id="lpddr6", unit_count, id=..., pin_rate_gbit_s=..., bus_width_bits=..., sustained_efficiency=..., usable_capacity_bytes=..., channels=...)`는 명시한 조건부 조합 계산일 뿐 실측 loader가 아니다. 실제 측정은 해당 scope의 내부 후보로 넣고, `portfolio.edge_sensor_budget()`와 별도 edge-tail evidence에 연결한다.
- **회귀·결정:** 기존 `test_explicit_lpddr_assembly_uses_decimal_peak_and_efficiency`, `test_metric_units_and_memory_path_cannot_be_relabeled` 유지. 추가 제안: 16Gb→2GB와 16GB package 혼동, whole-SOM W→DRAM W 혼동을 차단하는 fixture. density/BW보다 QoS/controller/전력 개선이 필요한지 결정한다.

### 3.7 `decode` — 논리 scan과 실제 서비스 traffic 분리

- **공백·목적·책임·우선:** `usable-stack`, `phase-traffic`, `migration`; 장문·동시성 증가가 실제 어떤 자원을 제한하는지 확인한다. 서빙 런타임 계측 담당과 서비스 SLO 책임자가 P0으로 수행한다.
- **필드·단위:** model revision·layers/KV heads/head dim, context tokens, 동시 세션 수, weight/KV dtype, tokens/s/session, resident/peak B, physical read/write B/s, TTFT·ITL·queue ms, 오류·timeout·품질. aggregate tokens/s와 세션당 속도를 구분한다.
- **환경·획득:** 공개·합성 또는 승인된 익명 workload trace를 같은 런타임에 재생한다. allocator와 hardware counter 및 요청 로그를 동기화한다. 품질 평가는 허용된 데이터셋에서 동일 조건으로 수행한다.
- **절차:** 1→2→4 세션을 제안된 탐색 격자로 삼되 실제 운영 분포를 우선한다. context 길이를 분리하고 admission/batching/cache 정책을 고정해 decode steady state를 측정한다. 다음으로 저정밀도·offload 대안을 동일 품질/SLO에서 비교한다.
- **통제·표본:** seed·요청 순서·output length·batch scheduler·KV layout을 기록한다. 공통 반복과 burst 별 tail 구간을 사용하며 여러 세션의 토큰을 독립 요청처럼 합산하지 않는다. allocation peak는 steady average와 따로 보고한다.
- **수락·반증:** 현재 GPU/HBM4 대안이 목표 동시성에서 품질/SLO를 만족하면 새 capacity 필수 주장 기각. 물리 traffic가 full-scan 모델보다 작으면 측정된 재사용 범위를 설명하고 목표 BW를 재검토한다. OOM·latency 실패·queue 제한은 별도 원인이다.
- **삽입 경로:** `workload.layers/kv_heads/head_dim/bytes_per_element/context_tokens/concurrency/output_tokens_per_s_per_request`, `resident_weight_bytes`, `active_weight_bytes_per_token`; integrated의 `phase_budget.resident_state_bytes`. 간단한 공개 구조 비교는 `strategy.make_llm_case(sessions, context_tokens, weight_bytes, kv_bytes, tokens_per_s)`에 연결한다. 요청 latency 원시 분포는 현재 API에 직접 넣지 않는다.
- **회귀·결정:** 기존 `test_public_architecture_kv_and_payload_are_distinct`, `test_resident_weights_change_sizing`, `test_current_b300_refutes_blanket_new_capacity_claim` 유지. 추가 제안: 같은 논리 토큰량에서 physical traffic가 달라도 논리 출력과 측정 evidence가 구분되는 시험. 용량 확대·BW 개선·batch/precision·offload 중 원인에 맞는 대안을 선택한다.

### 3.8 `training` — state/optimizer 하한에서 전체 step으로 확장

- **공백·목적·책임·우선:** `usable-stack`, `phase-traffic`, `memory-rail`; state·prefetch·activation·collective의 시간적 겹침과 전체 traffic을 확인한다. 학습 런타임/분산 통신 계측 역할이 P0으로 담당한다.
- **필드·단위:** parameters, shards, layers/prefetch layers, dtype별 state B, activation peak B, collective/workspace B, bytes/step, steps/s, optimizer window s, forward/backward/update 시간 s, compute utilization·BW stall·rail W, 수렴/품질 지표.
- **환경·획득:** 선택한 FSDP/optimizer 구현과 모델 revision을 고정한 실험 cluster에서 profiler·allocator·통신 trace를 함께 수집한다. 현재 `training_budget()`의 FP32 state16B/parameter와 update28B/parameter는 설계 가정이며 모든 optimizer 기본값이 아니다.
- **절차:** state별 tensor accounting→한 step timeline→여러 step peak·평균→4/8 shard 비교→activation recomputation 비교 순서로 수행한다. optimizer window traffic만으로 전체 training BW를 선언하지 않는다. shard 증가의 collective/동기화 비용을 함께 기록한다.
- **통제·표본:** global batch와 품질 목표, sequence length, optimizer, accumulation, checkpoint/recompute를 고정한다. 공통 seed/run 반복에 optimizer 초기 상태·steady training 구간을 구분한다. step 간 상관과 rank 간 최대값을 보고하고 평균 rank만 보지 않는다.
- **수락·반증:** measured peak 및 전체 SLO가 현재 qualified HBM 구성이나 샤딩으로 충족되면 density 증설 필수 가설 기각. compute/collective가 지배하면 optimizer 하한에서 역산한 BW target을 보류한다. 모델·실측 차이는 allocator/복제/통신 buffer를 포함해 설명해야 한다.
- **삽입 경로:** `portfolio.training_budget(parameters, shards, layers, prefetch_layers, activation_bytes, update_window_s, other_traffic_bytes_s)`. `other_traffic_bytes_s`는 같은 window에서 optimizer 하한과 중복되지 않는 나머지량이어야 한다. `parameters/layers`는 균일 layer 근사이며 실제 큰 embedding/FSDP group·max prefetch·collective buffer를 자동 반영하지 않는다. 이 차이는 명시적인 측정 대체/모델 보완 대상이다. 일반 API는 `workload.resident_weight_bytes/activation_bytes/optimizer_bytes`, `phase_budget.training_bytes_per_step/training_steps_per_s`를 받는다. temporal peak scheduling은 별도 모델 보완이다.
- **회귀·결정:** 기존 `test_training_explicit_step_budget`, `test_non_token_phases_do_not_infer_expert_fabric`와 새 `test_unknown_total_traffic_is_not_zero_or_lower_bound`, `test_training_sharding_keeps_unsharded_staging_and_activations` 유지. 추가 제안: 계측 trace에서 optimizer+other 중복을 검출하는 fixture. 제품 목표를 state 용량·지속 traffic·열 여유 중 확인된 항목으로 좁힌다.

### 3.9 `prefill` — cache write 절감과 TTFT를 따로 검증

- **공백·목적·책임·우선:** `phase-traffic`, `migration`; prefix reuse와 분리형 배치의 효과가 실제 TTFT 개선으로 이어지는지 확인한다. prefill 런타임 및 cache 담당이 P0으로 수행한다.
- **필드·단위:** requests, input tokens/request, input tokens/s, reuse fraction, KV B/token, window s, KV write B/s, GEMM/attention/weight traffic B/s, compute time·TTFT ms, resident cache B, eviction·miss·hit count, copy payload B.
- **환경·획득:** 동일 모델·paged-cache·attention kernel에서 명시한 동일 prefix와 비재사용 입력을 만든다. hit 판정을 runtime trace로 확인하며 목표 reuse 비율을 실측 hit 비율로 오인하지 않는다.
- **절차:** cold baseline→동일 prefix warm reuse→부분 reuse→burst/eviction 조건을 분리한다. KV write·전체 physical traffic·compute/queue·TTFT를 함께 측정하고 재사용 때문에 오래 보존되는 resident bytes를 별도 계측한다. disaggregation이면 copy 시간을 덧붙인다.
- **통제·표본:** prefix identity·입력 길이·cache 크기·eviction policy·arrival pattern을 고정한다. 공통 반복을 cold/warm별로 수행하고 동일 prefix 반복에 따른 상관을 block 단위로 반영한다. timeout 요청을 제거하지 않는다.
- **수락·반증:** 동일 품질에서 TTFT 상측 CI와 retention/power 조건을 충족해야 개선 인정. KV write만 감소하고 queue/copy 때문에 TTFT가 실패하면 신제품 BW 절감 근거로 승격하지 않는다. 기존 cache 최적화가 해결하면 새 메모리 필수성은 반증된다.
- **삽입 경로:** `portfolio.prefill_budget(requests, input_tokens, reuse_fraction, window_s, kv_bytes_per_token, other_traffic_bytes_s)`; 일반 API `workload.input_tokens_per_s/prefix_reuse_ratio/active_weight_bytes_per_token`, `phase_budget.prefill_other_bw_bytes_s`. `resident_capacity_savings_bytes`, `achieved_ttft_s`는 현재 null 출력이며 자동 추정하지 않는다.
- **회귀·결정:** 기존 `test_prefill_rate_reuse`, `test_prefill_expert_fabric_uses_input_token_rate`와 새 `test_prefix_reuse_does_not_invent_resident_capacity_reduction`, `test_unknown_total_traffic_is_not_zero_or_lower_bound` 유지. 추가 제안: 계측 cache block의 공유/retention과 실제 resident capacity savings를 검증하는 fixture. 방향은 메모리 BW·cache 정책·분리/통합 배치 중 실제 지배 원인에 따라 바뀐다.

### 3.10 `physical_ai` — median 기준점에서 동시 부하 tail로

- **공백·목적·책임·우선:** `edge-tail`, `memory-rail`, `phase-traffic`; 공개 단일 VLA median을 넘어선 workload의 p99·품질·열을 확인한다. Physical AI 실험 역할과 제어 품질 책임자가 P0으로 수행한다.
- **필드·단위:** camera 수/width/height/pixel bytes/fps, VLA/VLM model revision, batch/denoising steps, copy count, sensor ingress·physical DRAM B/s, resident peak B, end-to-end p50/p95/p99 ms, deadline miss율, task success, DRAM W와 SOM W, 온도/throttle.
- **환경·획득:** 공개 baseline의 software·MAXN 등 조건을 먼저 재현 가능한 범위에서 명시한다. 초기 실험은 기록된 센서 입력·안전한 오프라인 재생 환경에서 시행하며 실제 로봇 동작 시험은 별도 승인/안전 절차가 필요하다.
- **절차:** 단일 camera/VLA→목표 camera 수→VLM 동시 부하→copy 제거/비동기 scheduling→지속 열 부하 순서로 진행한다. 센서 timestamp에서 응용 결과까지 재고, copy-only5ms와 종단40ms 목표를 분리한다. 4camera/40ms는 현재 설계 사례이지 확정된 고객 요구가 아니다.
- **통제·표본:** 해상도/fps·입력 장면·model seed·precision·클록·열을 고정한다. 공통 반복에 장면 난도·burst·긴 실행을 층화하고 프레임 자기상관을 반영한 tail CI를 산출한다. 품질 저하를 latency 개선으로 교환하려면 요구 책임자가 허용폭을 먼저 정한다.
- **수락·반증:** 목표 품질·열·전력에서 p99 상측 CI가 사전 SLO 이하면 기존 SOM 대안 유지. 기존 LPDDR5X가 통과하면 LPDDR6 density/BW 증설 필수 주장 기각. compute/queue/sensor I/O가 원인이면 메모리 세대 변경을 직접 처방하지 않는다.
- **삽입 경로:** `portfolio.edge_sensor_budget(cameras, width, height, bytes_per_pixel, fps, memory_copies, transfer_window_s, other_traffic_bytes_s)`는 sensor-copy 하한만 계산한다. 현재 `memory_copies`는 양의 정수이며 zero-copy 대안을 시험했다고 임의로 0을 넣을 수 없다. zero-copy/공유 버퍼를 모델링하려면 실제 남는 DRAM traffic을 정의하는 별도 확장이 필요하다. 통합 API는 `phase_budget.frame_bytes/frames_per_s/physical_other_bw_bytes_s/resident_state_bytes/intermediate_state_bytes`와 `workload.resident_weight_bytes`를 받는다. total peak와 p99 분포는 내부 evidence 및 향후 모델 개선 항목이다.
- **회귀·결정:** 기존 `test_physical_ai_frame_traffic`, `test_vendor_baseline_does_not_establish_future_tail_slo`와 새 `test_edge_sensor_copy_is_not_total_inference_traffic`, `test_internal_tail_gap_is_an_extension_not_fake_ingestion`, `test_edge_p99_target_is_assumption_and_not_vendor_median` 유지. 추가 제안: 승인된 합성 trace로 tail-CI 판정을 검증하는 확장 시험. 결과에 따라 LPDDR capacity/BW보다 controller QoS·copy·scheduling·전력 설계를 우선할 수 있다.

### 3.11 `module-capacity-BW-channels` — 물리 객체와 독립 채널을 검증

- **공백·목적·책임·우선:** `usable-stack`, `migration`, `memory-rail`; 계산상 object count가 실제 구현 가능한 모듈/채널 구성인지 확인한다. 메모리 구성·controller qualification 역할이 P0으로 수행한다.
- **필드·단위:** object_level/component_object_level, units/object, gross/usable B, payload bus bit, transfer/s, 독립 channels, rank/DPC, slot count, 협상 속도, sustained B/s, object W. ECC 폭·rank·DQ 수를 payload BW에 중복 곱하지 않는다.
- **환경·획득:** topology 문서·실제 장착 상태·controller 설정을 교차 확인하고 채널별 counter로 공유 여부를 검증한다. LPDDR 조합은 부품 수와 aggregate bus width를 구별한다.
- **절차:** 단일 채널 기준점→독립 채널 추가→같은 채널 DIMM 추가를 각각 측정한다. capacity와 BW 증가를 따로 그린다. 큰 assembly의 usable reserve와 동작 속도 하향·열 제약을 검토한 뒤 workload를 재생한다.
- **통제·표본:** access stride/read-write mix, NUMA, DPC/rank, controller mode를 고정한다. 같은 슬롯 구성 반복과 서로 다른 모듈 개체를 구별하고 channel counter 합과 aggregate tool 값의 차이를 오차로 남긴다.
- **수락·반증:** 독립 인터페이스가 확인되고 동일 구성에서 요구 capacity/BW/W가 함께 성립해야 구성 후보 유지. 모듈 수만 늘려도 채널 BW가 늘지 않으면 선형 module BW 가정을 적용한 추천을 반증한다.
- **삽입 경로:** `exploration.compose_assembly()`의 `unit_count`, aggregate `bus_width_bits`, `channels`; `portfolio.channel_budget()`의 `modules`와 `independent_channels`는 별개다. 후보 `channels_per_module`은 이름과 달리 candidate object당 선언 채널 수이며 `units_per_object`와 함께 해석한다.
- **회귀·결정:** 기존 `test_explicit_lpddr_assembly_uses_decimal_peak_and_efficiency`, `test_invalid_assembly_inputs`, `test_assembly_usable_capacity_drives_sizing`와 새 `test_modules_on_same_channel_do_not_multiply_bandwidth` 유지. 추가 제안: measured negotiated rate와 populated-channel fixture. density 확대와 채널/컨트롤러 확대 중 필요한 쪽을 고른다.

### 3.12 `rack-power-PSU` — AC/DC·장애 생존·열을 같은 경계로

- **공백·목적·책임·우선:** `memory-rail`; DRAM에 실제 남는 전력과 rack 한계를 역산한다. 전력·열 계측 역할 및 rack 통합 책임자가 P0으로 수행한다.
- **필드·단위:** AC input W, shelf survivable DC W, PSU 효율(무차원, 부하별), 냉각 DC W, non-DRAM DC W, DRAM object count/W, 전압 V·transient ms·온도 °C, 장애 domain과 reserve. GPU TDP에 HBM이 포함되면 이를 non-DRAM으로 넣어 다시 HBM W를 더하지 않는다.
- **환경·획득:** 승인된 lab rack의 교정된 입력·출력 계측과 부하 telemetry를 사용한다. N+1 DC 정격은 이미 출력이므로 효율을 다시 곱하지 않는다. N+N feed 장애는 단순 PSU 하나 제거와 다르며 공식 장애 domain 자료를 조사한다.
- **절차:** idle·메모리 workload·compute workload·혼합 부하를 분리하고 같은 시간창의 AC/DC/rail/온도를 수집한다. 허용된 정상 부하에서만 파일럿을 수행한다. 장애 주입·전원 차단·한계 과도 부하는 별도 장비 소유자 승인과 lab 절차가 확보된 경우에만 수행하며 운영 서비스에서 실행하지 않는다.
- **통제·표본:** 입력전압·냉각·PSU population·클록·workload를 고정한다. 부하 곡선과 thermal steady state를 여러 run에서 측정하고 센서 오차·샘플 주기 때문에 놓치는 transient를 명시한다. peak efficiency를 모든 부하에 상수로 적용하지 않는다.
- **수락·반증:** joint capacity/BW/SLO 동작점에서 요구 DRAM W가 보수적 residual 이하이고 알려진 rack 한계가 통과해야 후보 유지. 계측 경계를 분리할 수 없으면 memory rail은 unknown. 현재 전력 제한·샤딩·소프트웨어로 해결되면 새 DRAM 효율 목표의 필수성을 재검토한다.
- **삽입 경로:** `portfolio.rack_residual(shelf_count, shelf_nplus1_dc_w, available_ac_w, psu_efficiency, cooling_dc_w, non_dram_dc_w, memory_objects, proposed_memory_w)`; 기존 API의 `rack.base_power_w/power_limit_w/psu_efficiency/psu_capacity_w/cooling_limit_w`, 후보 `power_w`. 기존 API `psu_capacity_w`는 wall AC 비교이고 portfolio의 shelf DC와 단위 경계가 다르다. transient·busbar·thermal dynamics는 현재 별도 측정/모델 확장이다.
- **회귀·결정:** 기존 `test_integrated_rack_constraints`, `test_constraints_boundaries`와 새 `test_nplus1_rating_is_dc_and_efficiency_applies_only_to_ac`, `test_negative_rack_residual_is_preserved_and_unknown_limit_blocks_pass` 유지. 추가 제안: 부하별 효율 곡선·transient 계측을 반영할 때 새 모델의 경계 시험. 제품 목표는 단순 W/stack이 아니라 같은 성능점에서의 W와 열 조건으로 제시한다.

### 3.13 `heterogeneous-disaggregation` — 용량 확보와 전송 가능성을 함께

- **공백·목적·책임·우선:** `migration`, `phase-traffic`, `memory-rail`; warm/cold DRAM 배치·prefill/decode 분리가 실제 이득인지 확인한다. 계층 메모리/전송 담당과 서빙 SLO 책임자가 P0으로 수행한다.
- **필드·단위:** pool gross/usable/assigned B, hot fraction·miss fraction, copy payload B, arrival/s, source/destination/fabric 지속 B/s, 방향, queue/handshake/serialization/copy s, TTFT/ITL ms, replication·eviction·재전송, CPU·NIC·DRAM W.
- **환경·획득:** 승인된 단일·다중 host testbed에서 NUMA/CXL/PCIe/NIC topology와 접근 가능성을 확인한다. CXL 용량 제공이 GPU 직접 접근 또는 HBM 동등 BW를 뜻하지 않는다. CPU/GPU memory-sharing 공개 사례의 수치를 다른 플랫폼에 기본값으로 복사하지 않는다.
- **절차:** local 재계산/보존 기준점→direct copy 단일 요청→동시 miss/arrival burst→shared-link 경쟁→실제 cache 정책을 비교한다. 전송 전후 pool read/write와 link traffic을 중복 없이 합산한다. overlap은 구현 trace로 입증된 구간만 인정한다.
- **통제·표본:** payload/layout·정렬·경로·miss·arrival trace·cache 상태·network contention을 고정한다. 공통 반복에 burst와 큰 payload를 층화하고 per-copy latency와 steady throughput CI를 따로 구한다.
- **수락·반증:** arrival과 miss가 모두 양수일 때 `max(arrival×miss×payload, payload/deadline)`가 방향별 path에 들어가는 것은 필요조건이다. 둘 중 하나가 0이면 현재 함수는 `transfer_required=False`, 필요한 BW=0, copy 시간 하한=null로 반환하며 존재하지 않는 전송 요구를 만들지 않는다. 드문 양의 miss에는 여전히 per-copy deadline이 적용된다. queue 등을 포함한 E2E tail·품질·W까지 통과해야 대안 유지. copy보다 재계산이 빠르거나 hit가 낮으면 tier 이득 가설을 기각한다. fabric 부족을 DRAM density 부족으로 분류하지 않는다.
- **삽입 경로:** `portfolio.transfer_budget(payload_bytes, arrival_rate_s, miss_fraction, deadline_s, source_bytes_s, destination_bytes_s, fabric_bytes_s)`; 통합 API `placement.pools[].capacity_bytes/sustained_bw_bytes_s/assigned_bytes/access_bw_bytes_s`, `placement.paths[].traffic_bytes_s/bandwidth_bytes_s`, `bind_to_demand`. queue·latency overlap 모델은 아직 별도 확장이다.
- **회귀·결정:** 기존 `test_local_pool_and_link_deficits`, `test_placement_binding_catches_unassigned_future_capacity`, `test_unknown_usable_capacity_and_excluded_placement_do_not_fill_gaps`와 새 `test_transfer_deadline_can_fail_even_when_average_rate_fits`, `test_unknown_link_cannot_be_declared_feasible` 유지. 추가 제안: replica 중복 coverage 방지. 결과로 tier capacity·channel·fabric·locality 중 필요한 조치가 바뀐다.

현재 `profiles[].placement`의 측정 대상은 다음과 같은 **BF16 warm cache와 별개의 hot destination으로 구성한 KV slice**다. 별도 1-byte decode 대안의 active workload 전체와 합치지 않는다.

| profile ID | warm 할당 | 서로 겹치지 않는 hot 할당 | 배분과 적합성 해석 |
|---|---:|---:|---|
| `growth`, `power-constrained` | 64 × 40 GiB | 40 GiB | 총 slice 수요를 모두 배분해 `coverage.status=pass`여도 지정 warm 용량·경로 한도를 넘는다. |
| `efficient` | 16 × 40 GiB | 40 GiB | 지정 warm 용량·경로 예산은 충족하지만 hot usable capacity가 null이므로 전체 적합 판정은 보류한다. |

현재 모든 profile의 `transient_replication_bytes`와 hot pool `capacity_bytes`는 null이다. 측정에서는 이동 중 source/destination 동시 점유, 복제 수명, allocator 및 전체 active sessions/weights의 추가 peak를 별도로 확보한다. `transient_replication_bytes`는 현재 설명용 미확보 출력이며 새로운 자동 ingestion 필드가 아니다. 내부 evidence로 보존하고 전체 구성 모델에 넣으려면 명시적 확장·검토가 필요하다. 경로의 `known_bound_transfer_time_lower_bound_s`는 알려진 상한만으로 얻은 하한이며, 미확인 전체 경로의 `transfer_time_lower_bound_s`와 구별한다.

### 3.14 `kv-control-data` — metadata controller와 payload relay를 구분

- **공백·목적·책임·우선:** `migration`, `phase-traffic`; controller-only 구성으로 충분한지, relay가 필요한지 검증한다. KV 서비스/전송 프로토콜 담당이 P0으로 수행한다.
- **필드·단위:** sessions, metadata B/session·등록영역/peer/block entry 수, control ops/s·B/op, event/heartbeat B/s, payload ingress/egress B/s, link 지속 B/s, server metadata B, CPU cycles/op·ops/s, E2E p99 ms, 복구 시간·오류율.
- **환경·획득:** 동일 metadata 정책·payload 경로의 direct/relay testbed에서 control/data counter와 CPU profile을 수집한다. 중앙 metadata 서버의 존재만으로 payload가 그 서버를 통과한다고 가정하지 않는다.
- **절차:** metadata-only 기준점→direct payload→같은 workload의 relay→동시 session/등록 churn을 순차 비교한다. heartbeat와 cache hit에 따른 control 비용을 포함한다. 장애 복구는 별도 승인된 테스트 계획에서만 수행한다.
- **통제·표본:** payload/operation mix·등록 캐시·peer 수·암호화/복제 정책·동시성을 고정한다. warm 등록과 cold 등록을 나누고 burst별 tail을 수집한다. 양방향 합계를 단방향 link 정격과 비교하지 않는다.
- **수락·반증:** metadata 용량·link·CPU·tail·필요 신뢰성이 함께 충족돼야 controller 안을 선택한다. direct가 요구를 만족하면 relay를 필수 경로로 주장하지 않는다. relay 실패가 CPU/copy 때문이면 신규 DRAM 시장 공백 주장도 기각한다.
- **삽입 경로:** `integrated.evaluate_kv_system()`/`kv_system`의 `sessions`, `metadata_bytes_per_session`, `control_operations_per_s`, `control_bytes_per_operation`, `payload_bw_bytes_s`, `control_link_bw_bytes_s`, `data_link_bw_bytes_s`, `server_metadata_capacity_bytes`. event·등록 구조·CPU·replication·장애/tail은 현재 자동 모델이 아니며 집계 근거를 내부 기록으로 보존하고 필요 시 코드 확장한다.
- **회귀·결정:** 기존 `test_control_data_separation`, `test_zero_and_missing_are_distinct` 유지. 추가 제안: metadata 불명은 전체 mode 미평가, relay의 별도 ingress/egress 요구를 검증하는 확장 시험. controller-only·relay·분산 metadata 중 실제 요구가 뒷받침하는 최소 구성을 선택한다.

### 3.15 `model-trends-demand-growth` — 미래 증가를 분포와 시나리오로

- **공백·목적·책임·우선:** 선택 workload에 관련된 5개 공백; 모델·서비스 발전이 어떤 메모리 수요를 만드는지 분리한다. workload 분석 역할과 제품 전략 책임자가 P1으로 조사/모델 보완을 담당한다.
- **필드·단위:** model revision·총/활성 parameter 수, context tokens 분포, live sessions, calls/task, output tokens/call, task arrivals/s, branch 수, sensor 수/fps, resident B, phase traffic B/s, 추정 구간과 가정 근거. 순차 agent 호출 수와 순간 동시성을 동일 배수로 쓰지 않는다.
- **환경·획득:** 공개 모델 구조와 승인된 익명 운영 집계/파트너 조건을 분리한다. 원시 prompt 대신 충분한 histogram·구간 요약을 우선하며 모집단·기간·누락률·sampling 규칙을 기록한다.
- **절차:** 기준 workload를 확정한 뒤 context, 동시성, 모델 상주량, output rate를 하나씩 바꾸고 주요 상호작용을 추가한다. 증가만이 아니라 3.16의 효율 개선 시나리오를 같은 표에 둔다. 실제 분포가 없으면 selected range로만 발표한다.
- **통제·표본:** 분석 기간/서비스 집단·SLO·품질·하드웨어를 고정하고 시간대/고객 유형을 층화한다. 시계열 자기상관을 고려하며 다른 기간을 holdout으로 두는 설계를 제안한다. 연도 라벨·1→2→4 동시성은 확률이나 채택량이 아니다.
- **수락·반증:** 관측 분포가 가정 범위를 덮는지와 결과가 한 가정에 과민한지 검토한다. 실제 성장축이 없거나 효율 개선이 수요 증가를 상쇄하면 관련 신제품 우선순위를 낮춘다. 표본 부족을 시장 수요 없음으로 결론내리지 않는다.
- **삽입 경로:** `strategy.make_llm_case()`의 명시 인수와 일반 API `scenario.context_multiplier/concurrency_multiplier/layers_multiplier/weight_multiplier/kv_bytes_multiplier`; `compare_scenarios(request, scenarios)`. `context_distribution`은 현재 gap schema에서 미구현이므로 외부에서 대표 조건을 명시해 여러 request를 만들거나 분포 모델을 별도 구현한다.
- **회귀·결정:** 기존 `test_scenario_and_zero_rate`, `test_named_sensitivity_and_fabric_breakpoint`, `test_custom_assumptions_describe_actual_inputs` 유지. 추가 제안: 동일 task의 순차 calls가 concurrency에 중복 반영되지 않는 산술 fixture와 holdout 오차 점검. 전략은 조건부 목표 범위와 다음 관측 시점으로 제시하며 확정 수요예측으로 표현하지 않는다.

### 3.16 `model-tech-demand-reduction` — 새 메모리 필요성의 반증 실험

- **공백·목적·책임·우선:** 해당 workload의 5개 공백; quantization·GQA·reuse·샤딩·recompute·copy 제거로 기존 제품이 충분해지는지 확인한다. 모델 품질 책임자와 런타임 최적화 역할이 P0으로 수행한다.
- **필드·단위:** weight/KV bit, group size·metadata/residual/padding B, resident/physical traffic B, quality score, TTFT/ITL/p99 ms, energy J/request, cache hit/eviction, shard 통신 B/s, copy count. 낮은 bit 수를 모든 tensor·optimizer에 자동 전파하지 않는다.
- **환경·획득:** 동일 모델·데이터·품질 평가셋에서 지원되는 kernel을 사용한다. 공개 AWQ/KIVI/GQA/MLA 기제는 해석 근거이며 논문의 절감률을 새 모델의 실측값으로 복사하지 않는다.
- **절차:** precision 또는 한 최적화만 바꾸는 A/B→조합 최적화→대표 난도/긴 context/열 조건으로 확장한다. 저장량과 metadata를 실측하고 cache hit가 prefill work·decode residency·전송량 중 어디에 영향을 주는지 분해한다.
- **통제·표본:** seed·입력·품질 기준·SLO·하드웨어를 고정하고 matched-run 비교를 한다. 공통 반복과 품질 표본의 신뢰구간을 함께 제시한다. latency만 좋아지고 task quality가 사전 허용폭을 벗어나면 통과가 아니다.
- **수락·반증:** 기존 메모리에서 품질/SLO/W가 유지되면 해당 신규 density/BW 필수 가설을 기각한다. 작은 payload와 실제 allocation이 다르면 metadata/복제/커널 제약을 포함해 효과를 다시 계산한다. MLA는 미지원 모델 구조로 남기며 임의 multiplier로 구현했다고 주장하지 않는다.
- **삽입 경로:** `make_llm_case(weight_bytes, kv_bytes, sessions, ...)`, `workload.bytes_per_element/resident_weight_bytes/active_weight_bytes_per_token/prefix_reuse_ratio`, `scenario.kv_bytes_multiplier/weight_multiplier`; `training_budget(shards, activation_bytes, ...)`. packed metadata/residual·MLA 구조·품질 함수는 현재 별도 모델 개선 대상이다.
- **회귀·결정:** 기존 `test_precision_alternative_can_remove_capacity_exclusion`, `test_prefill_rate_reuse`, `test_model_and_technology_change_modules` 유지. 추가 제안: weight precision 변경이 KV precision을 자동 변경하지 않음, prefix reuse가 decode capacity를 자동 줄이지 않음, metadata overhead 포함 fixture. 신제품 요구를 완화하거나 SW·controller 개선을 우선한다.

### 3.17 `internal-collaboration-inputs` — 실제 사용 가능한 자료 계약

- **공백·목적·책임·우선:** 5개 모두; 공개 공란을 무엇으로 보완할지 자료 소유자와 실행 가능한 계약을 만든다. 내부 자료 소유자·계측 책임자·접근 승인자·독립 검토자가 P0으로 역할을 나눈다. 특정 회사·부서의 협력 또는 데이터 제공을 이미 확보했다고 가정하지 않는다.
- **필드·단위:** 각 공백의 value/unit/scope/조건/기간/표본/CI/장비·SW 판본/접근 등급/원시 hash/수집 목적/허용 보관·공유 범위. sustained B/s·DRAM W·p99 ns 또는 ms·fabric B/s의 조건을 함께 받아 숫자만 인계하지 않는다.
- **환경·획득:** 승인된 내부 저장소에서 담당자가 필요한 최소 요약을 제공한다. 공개 저장소·대화 로그·원본 사내 보고서를 자동 검색하거나 외부로 복사하는 절차는 없다. 제공 권한이 없으면 공란과 필요한 승인 역할을 기록한다.
- **절차:** 공백별 요청서→자료 소유자의 scope/사용 승인→측정 프로토콜 합의→schema/단위 검토→원시 hash와 요약 보존→독립 재계산→내부 request 생성 순서다. 파트너 수치와 사내 재현 수치는 별도 evidence ID로 둔다.
- **통제·표본:** 동일 필드명이더라도 access pattern·온도·population·workload가 다르면 병합하지 않는다. 원 제공자의 N·반복·검열/누락·CI 방법을 받아 검토하고 없는 경우 unknown으로 보존한다. 숫자 신뢰도를 임의 점수로 채우지 않는다.
- **수락·반증:** 권한·단위·scope·조건·오차·재현 근거가 확인된 필드만 내부 계산에 사용한다. 자료가 없거나 서로 충돌하면 recommendation을 보류하고 충돌 이유를 남긴다. 현업 workload 자체가 가정한 요구를 갖지 않으면 해당 제품 방향을 반증한다.
- **삽입 경로:** 실행에 지원되는 항목만 `catalog.gap_schema().fields[].input_path`를 확인해 복사한다. 주요 경로는 후보 sustained BW/power/p99, `rack.fabric_bw_bytes_s/psu_efficiency`, `workload.prefix_reuse_ratio/metadata_bytes_per_request`. `thermal_throttle_ratio/context_distribution` 등 미지원 값은 내부 evidence에만 두고 별도 모델 변경 요청을 낸다.
- **회귀·결정:** 기존 `test_coverage_does_not_claim_unimplemented_gap_fields`, `test_immutable_inputs`, `test_input_validation_determinism_and_no_mutation` 유지. 추가 제안: 합성 내부 canary가 public demo/export에 섞이지 않는 시험과 unsupported metadata key 거절 시험. 어떤 사내/협력사 측정이 제품 결정을 바꿨는지 case ID와 함께 추적한다.

### 3.18 `coverage-insufficiency-blank` — 공백·부족·시장 기회를 구분

- **공백·목적·책임·우선:** 5개 모두; 특정 구성 실패를 전체 시장 부족으로 확대하지 않는다. 독립 검토자와 제품 전략 책임자가 P0으로 최종 판정한다.
- **필드·단위:** 요구량·가용량의 value/min/max/unit/scope/kind/sources, configuration ID, qualified operating point, 알려진 실패·미평가 항목, 대안 결과, SLO/품질 기준, 불확실성, source checked date. 시장 규모·채택량은 별도 근거가 없으면 null이다.
- **환경·획득:** 동일 workload/품질/SLO에 대한 현재 shipping·qualified 대안과 구성·SW 변경을 비교하는 review table을 만든다. public peak·sample·roadmap·internal measurement를 서로 구별한 원본 기록을 사용한다.
- **절차:** (1) 단위/scope 호환성 (2) 알려진 제약 위반 (3) unknown 목록 (4) 기존 제품·샤딩·precision·cache·path 대안 (5) 독립 산술 (6) 민감도와 반증 (7) 제품 방향 순으로 검토한다. “여기서 조사한 대안”의 범위를 명시한다.
- **통제·표본:** 비교 대상마다 같은 요구·품질·기간을 적용한다. 측정 CI와 시나리오 범위를 섞지 않고 source 갱신 차이를 표시한다. 이 카드는 새 hardware 표본이 아니라 앞 카드의 evidence를 검토하므로 미측정 N을 만들어 넣지 않는다.
- **수락·반증:** `unknown`은 evidence gap, 알려진 required>limit은 해당 구성의 조건부 부족, 모든 정적 입력 충족은 조건부 여유다. matched-workload 검증 전에는 제품 전체 적합이 아니다. 기존 대안 하나라도 요구를 만족하면 “신규 메모리 필수/시장 미충족”의 강한 주장은 기각된다. 제한된 대안 실패만으로 시장 전체를 입증하지 않는다.
- **삽입 경로:** `portfolio.compare_quantity(required, available)`는 unit/scope가 같고 scalar value가 있을 때만 비교한다. range-only는 여기서 자동 판정하지 않는다. 일반 결과의 `status`, `ranking_eligible`, `comparison_conclusive`, `constraints`, `whole_system_validated`를 함께 읽고 `portfolio.axis_trace`/`directions[].falsification`에 검토 결론을 연결한다. 전략 코드를 바꾸는 경우 별도 source review가 필요하다.
- **회귀·결정:** 기존 `test_scope_mismatch_is_not_compared`, `test_unknown_and_zero_are_not_the_same`, `test_directions_bind_evidence_and_keep_targets_honest`와 새 `test_comparison_rejects_different_unit_and_physical_scope`, `test_existing_path_results_never_imply_whole_system_fit`, `test_undisclosed_families_remain_null_and_not_bad_products` 유지. 추가 제안: 기본 API의 eligible이지만 ranking_eligible false인 조합을 명시한 UI 판정 fixture. 결론은 유지·조건부 연구·모델 보완·보류·기각으로 분류하고 근거 없이 세대나 시장을 확정하지 않는다.

### 3.19 `HBF/NAND` — 포지셔닝만 유지, 필수 수집에서 제외

- **공백·목적·책임·우선:** 연결할 측정 공백 ID 없음. 범위 검토 역할이 제외 상태를 확인한다. HBF/NAND/SSD/FLASH/NVMe의 내부 사양·샘플·성능 데이터 수집은 이번 계획의 필수 작업이 아니다.
- **필드·단위:** 포지셔닝용 이름·인접 역할·출처·제외 사유만 필요하다. 용량/BW/W/p99를 본분석 후보로 채우지 않는다. 본 요구의 입력은 `positioning_only`/범위 설명이며 실험 측정값이 아니다.
- **환경·획득·절차:** 기존 공개 scope 메모와 코드의 family exclusion을 읽기 확인한다. 합성 제외 후보를 기존 회귀에 사용해 결과가 랭킹·추천·coverage 합계로 흘러가지 않는지 확인하는 계획만 둔다. 실제 NAND 장비 실험 환경을 요구하지 않는다.
- **통제·표본·불확실성:** hardware sample 수·반복·CI는 적용하지 않는다. 제외 문자열의 표기 변형과 scenario·placement 경로를 소프트웨어 fixture로 검토한다. 수치를 모른다는 이유가 아니라 사용자 범위 결정에 따른 제외임을 명시한다.
- **수락·반증:** HBF/NAND가 후보 랭킹·주요 용량/BW 합계·필수 내부 측정 요청에 들어오면 범위 검토 실패다. 인접 위치 설명이 있는 것은 허용되지만 DRAM 결과를 NAND의 성능 평가로 확대하지 않는다.
- **삽입 경로:** `api._analyze()` family exclusion, `integrated.evaluate_placement()` 제외 경로, `strategy._requirement_trace()[id="HBF/NAND"]`, `portfolio.axis_trace[requirement_id="HBF/NAND"]`. 실제 값 입력/신규 loader/시험 장비 계획은 없다.
- **회귀·결정:** 기존 `test_exclusions_all_scenarios`, `test_exclusion_every_path`, `test_remaining_scope_unknown_not_fabricated_or_excluded_candidate`를 유지한다. 제외 상태 유지가 이 카드의 완료 조건이며 NAND 제품 전략을 만들지 않는다.

## 4. 측정 결과를 제품 판단으로 인계하는 순서

1. **실험 준비 완료:** 19축 중 이번 결정에 필요한 축과 공백 ID를 선택한다. 책임자·요구 SLO·품질·단위/scope·자료 권한·장비 경계·표본 계획·반증 조건이 비어 있으면 해당 시험을 시작하지 않는다. 관련 없는 축은 공란/보류 이유를 남긴다.
2. **측정 유효성:** 원시 hash, 구성/SW 판본, 실패/누락 기록, 계측 오차, run/개체 수, tail CI 방법을 독립 검토한다. sensor 누락이나 phase 혼합이 있으면 전체 traffic/power 값을 확정하지 않는다.
3. **모델 연결:** 실제 지원 필드만 내부 request에 명시적으로 매핑하고 baseline 복사본과 차이를 검토한다. 단위 변환식·scope·overhead·중복 제거를 기록한다. 미지원 필드는 새로운 구현 작업으로 분리하며 기존 demo 수치가 자동 개선됐다고 주장하지 않는다.
4. **회귀 검증:** 내부 측정값을 그대로 공개 테스트에 넣지 않는다. 같은 단위·경계·null·실패 조건을 갖는 합성 fixture로 회귀를 만든다. 계산 구현의 변화는 기존 build/test/lint와 독립 산술을 통과해야 한다. 하드웨어 정확도는 합성 회귀 통과와 별도다.
5. **대안·반증:** 기존 qualified 제품, 모듈/채널 수, 샤딩, precision, recompute, cache, direct/relay, locality, 전력 제한을 해당 품질/SLO에서 비교한다. 해결 가능한 대안이 있으면 신규 세대 요구의 범위를 줄인다.
6. **결정 기록:** 제품 방향 ID(`hbm-throughput-energy`, `capacity-tier-kv`, `edge-qos`)에 연결해 `유지/조건부 연구/모델 보완/보류/기각`을 기록한다. 목표 B/B/s/W와 operating point, 불확실성, 기각될 조건, 다음 검토 시점을 함께 적는다. 시장 규모나 출시 확정은 이 산술 검증의 산출물이 아니다.
7. **배포 검토:** 공개 산출물에는 빈 schema·합성 fixture·공개 source·승인된 비민감 요약만 남긴다. 내부 overlay·원시 trace·HBM5 사양·계정/개인정보·협력사 식별 자료·내부 ledger는 별도 INTERNAL 위치에 보존한다. 문서 링크와 실제 API 이름을 최종 소스에서 다시 확인한다.

### 4.1 내부 인계 기록의 최소 항목

```text
decision_id / requirement_ids / gap_ids / direction_ids:
가설 및 기존 제품·SW 대안:
실험 protocol revision / 입력 request hash / 코드 revision:
자료 승인·접근 등급 / 내부 evidence reference:
측정 scope·단위·조건 / N·독립 run·개체 수 / CI·오차:
알려진 통과·실패·미평가 제약:
품질·SLO·전력·열 결과와 반증 결과:
지원 필드에 연결한 값 / 별도 모델 보완 항목:
제품 목표의 변경 전·후 / 결정 / 남은 불확실성:
시험 책임자 / 독립 검토자 / 요구사항 책임자 / 검토일:
```

이 문서 자체의 완료는 **실행 가능한 계획과 코드 경로를 검토한 상태**다. 빈 내부 필드가 채워졌거나 측정·제품 qualification이 완료됐다는 의미가 아니다.
