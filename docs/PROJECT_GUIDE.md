# DSA Memory Suggestion — 프로젝트 기술 가이드

문서 기준: 2026-10-29. 대상은 이 작업공간의 `memory_dsa` 구현이다. 공개 근거의 확인일은 각 출처 레코드의 `checked_at`, 공개 발표일은 `published`로 별도 관리한다. 이 문서는 실행 방법과 계산의 의미를 설명하며, 하드웨어 실측이나 고객 수요 검증을 완료했다는 보고서가 아니다.

사내 측정 설계, 승인된 데이터의 기록 방법, 반증 기준과 모델 반영 절차는 [사내 검증 플레이북](INTERNAL_VALIDATION_PLAYBOOK.md)을 함께 사용한다. 두 문서는 편집 가능한 기술 원고이며, 계산 결과의 기준은 같은 버전의 소스와 생성 JSON이다.

## 1. 목적과 의사결정 질문

이 프로젝트는 워크로드의 메모리 요구를 용량·논리 트래픽·채널·전송 경로·랙 전력으로 나누고, 공개 제품이 제공하는 범위와 비교한다. 그 결과를 **조건부 구성 부족**, **현재 대안으로 검토 가능한 범위**, **판단에 필요한 미확보 정보**로 구분해 다음 개발·검증 질문을 만든다.

다음 질문에 순서대로 답하는 것이 사용 목적이다.

1. 어떤 모델·정밀도·동시성·처리 단계에서 어느 메모리 객체의 용량과 트래픽이 필요한가?
2. 공개된 현행 제품과 소프트웨어·샤딩·구성 대안으로 이 요구가 완화되는가?
3. 모듈을 늘려도 독립 채널, warm→hot 경로, 냉각 또는 PSU가 먼저 제한하는가?
4. 부족이 남는다면 어느 객체의 용량·BW·전력·지연 목표를 역산할 수 있는가?
5. 어떤 측정값이 들어오면 개발 우선순위 또는 현재 결론이 바뀌는가?

이 도구의 우선순위는 **엔지니어링 검토 순서**다. 시장 규모, 매출, 제품 출시 시점, 고객 채택 확률을 점수화하지 않는다. 특정 구성의 부족이 계산됐다는 사실만으로 전체 시장의 미충족 수요나 특정 미래 메모리 세대의 필요성을 확정하지 않는다.

### 1.1 세 종류의 사용 화면

| 산출물 | 쓰임 | 해석 경계 |
|---|---|---|
| `outputs/index.html` | 워크로드·시나리오·후보 구성, 배치, 경로, 민감도 탐색 | 입력한 조건의 산술·제약 결과. 실제 실행 성능이 아님 |
| `outputs/strategy.html` 상단 포트폴리오 | 원래 19축을 세 제품 방향, 실제 분석, 공개 라인업, 다음 측정으로 연결 | 조건부 목표와 검토 순서. 제품·투자 추천의 확정판이 아님 |
| 같은 전략 화면 하단 심층 사례 | 장문 LLM과 Physical AI의 공개 사실·운영 가정·대안을 자세히 비교 | 두 사례의 근거를 전체 시장으로 일반화하지 않음 |

현재 세 방향은 `hbm-throughput-energy`(HBM 용량·BW·전력 공동 검증), `capacity-tier-kv`(DDR 계층 용량·KV 경로), `edge-qos`(Physical AI의 LPDDR·QoS)다. 이 방향들은 서로 독립적인 제품 출시 계획이 아니라 같은 서버·랙·엣지 조건에 연결된 검토 묶음이다.

## 2. 범위: 원래 요구의 19축

아래 표는 최신 `portfolio.axis_trace`의 요구 ID와 분석 ID를 기준으로 한다. 각 행은 분석을 찾기 위한 지도다. 행 존재나 `null` 표시 자체가 분석 완료를 뜻하지 않는다. 구현 판정과 하드웨어 검증 판정도 다르다.

| # | 요구 ID | 현재 계산·판단과 사내 후속 질문 |
|---:|---|---|
| 1 | `HBM4` | `training-state`, `decode-capacity`, `rack-power`: rank/accelerator 요구를 stack 목표로 역산하고 현행 공개 기록과 비교한다. 상용 출하 사실과 해당 워크로드의 usable·sustained·전력 검증은 별개다. |
| 2 | `HBM4E` | 학습 용량 목표와 샘플 기록을 비교한다. 샘플의 용량·최대 BW가 같은 동작점에서 보장되는지, 시스템 qualification이 있는지는 보류한다. |
| 3 | `HBM5` | 워크로드가 요구하는 목표는 계산하되 미확인 제품 사양은 `null`이다. 현행·샘플·stack 수·샤딩 대안을 확인하기 전 HBM5 필요성을 결정하지 않는다. |
| 4 | `DDR6` | `ddr-tier`, `kv-transfer`, `kv-control`: warm 용량, 모듈 목표, 경로·제어 예산을 계산한다. 미래 모듈 구성을 만들어 넣지 않고 DDR5 대안과 비교한다. |
| 5 | `DDR7` | DDR 계층의 동일 요구를 추적하지만 제품 사양과 세대 선택은 보류한다. DDR7과 GDDR7은 서로 대체되는 이름이 아니다. |
| 6 | `LPDDR6` | `physical-qos`: 표준·소자 개발·플랫폼 검증을 구분하고 엣지 전체 요구의 공백을 표시한다. die 밀도를 SOM usable 용량으로 바꾸지 않는다. |
| 7 | `decode` | GQA KV 및 weight payload, 동시성·정밀도 대안, 논리 scan을 계산한다. 물리 트래픽·실제 token/s·ITL은 별도 검증한다. |
| 8 | `training` | FP32 상태 샤딩, BF16 prefetch, activation, optimizer 부분 트래픽을 계산한다. 전체 step traffic·collective·allocator peak는 미확보다. |
| 9 | `prefill` | 신규 KV write와 prefix reuse의 조건부 절감량을 계산한다. attention/GEMM/compute와 실제 TTFT는 이 하한만으로 판단하지 않는다. |
| 10 | `physical_ai` | 공개 VLA 기준 사례와 미래 다중 카메라·VLA/VLM을 구분한다. 센서 copy 하한은 계산하고 전체 allocation·BW·p99는 보류한다. |
| 11 | `module-capacity-BW-channels` | 객체 용량, module 수, 독립 channel 수, 전기적 bus 구성을 별도로 계산한다. DIMM을 늘리는 것과 채널 BW를 늘리는 것은 같지 않다. |
| 12 | `rack-power-PSU` | N+1 DC 공급·AC 입력·효율·냉각·non-DRAM 예산으로 DRAM 잔여 전력을 역산한다. 배선·과도 응답·부품별 실측은 추가 검증한다. |
| 13 | `heterogeneous-disaggregation` | warm/hot pool의 용량 배분과 directional path의 처리율·copy 시간 하한을 확인한다. 자동 배치 최적화나 queue 시뮬레이션은 아니다. |
| 14 | `kv-control-data` | metadata/control과 payload를 분리해 direct와 relay 예산을 비교한다. CPU 처리량, tail, 장애 복구와 운영비용은 미검증이다. |
| 15 | `model-trends-demand-growth` | context·동시성·warm retention·학습 상태·다중 센서 증가를 명시적인 시나리오로 다룬다. 연도별 확률이나 시장 성장률 예측은 제공하지 않는다. |
| 16 | `model-tech-demand-reduction` | 정밀도 축소, prefix reuse, 샤딩 등 완화 요인이 검토 순서를 바꾸는지 비교한다. 품질·통신비용·실제 hit rate 조건을 유지한다. |
| 17 | `internal-collaboration-inputs` | 의사결정을 바꾸는 측정 필드·단위·조건·수신 계산·임계값을 정의한다. SK hynix·SKT·NAVER 등 비공개 자료를 수집하지 않는다. |
| 18 | `coverage-insufficiency-blank` | 지정 구성의 부족, 명목 envelope 안의 후보, 공개 규격 공백, 시장 수요 미입증을 분리한다. 미확보 규격을 물리적 결함으로 취급하지 않는다. |
| 19 | `HBF/NAND` | DRAM 외부 저장 위치에 대한 포지셔닝만 허용한다. 본분석·수치 추천·최적화·순위·사내 데이터 수집 대상에서 제외한다. |

[기존 요구 추적표](REQUIREMENTS_TRACEABILITY.md)의 24개 항목은 이전 계산기 검증을 위한 역사적 체크리스트다. 이 문서의 19개는 원래 요청의 범위 축이다. 개수가 같아야 하거나 1:1로 대응하는 목록이 아니며, 24개 산술 체크 통과가 19축의 제품전략 검토 완료를 자동 보장하지 않는다.

## 3. 구조와 데이터 흐름

런타임은 Python 표준 라이브러리 기반의 오프라인 프로그램이다. HTML은 결과 JSON을 포함한 정적 파일이며 서버, 데이터베이스, 인증, 외부 API 호출이 계산에 필요하지 않다. 출처 링크를 여는 행위는 오프라인 계산과 별개다.

```text
공개 근거 스냅샷 + 명시적 운영/설계 가정
  ├─ catalog.py / portfolio_evidence.py / strategy.py의 출처·제품 레코드
  ├─ JSON request → api.py → KV 하한·후보 객체 수·제약 판정
  ├─ JSON request → integrated.py → phase 수요·배치·KV 제어/데이터 경로
  ├─ exploration.py → 구성·민감도·시나리오·범위 탐색
  └─ portfolio.py → 학습/prefill/channel/path/rack/edge 분석
                      → 조건부 목표·현재 대안·검토 순서·19축 추적
        ↓
demo.py / strategy_study() → JSON·CSV + report.py / strategy_report.py
        ↓
index.html 계산 탐색기 / strategy.html 제품 의사결정 지도
```

| 파일 | 책임과 중요한 인터페이스 |
|---|---|
| `memory_dsa/__main__.py` | 실제 CLI: `demo`, `evaluate`, `integrated`, `compare` |
| `memory_dsa/api.py` | `analyze(request)` 및 엄격한 입력 검증, decode 중심 KV 하한과 후보 제약 |
| `memory_dsa/integrated.py` | `analyze_integrated`, `compare_scenarios`, `evaluate_placement`, `evaluate_kv_system` |
| `memory_dsa/units.py` | 차원이 같은 단위만 변환하는 `convert` |
| `memory_dsa/catalog.py` | 공개 카탈로그, 공개 후보 변환, 향후 내부 입력 공백 스키마 |
| `memory_dsa/exploration.py` | `compose_assembly`, `decision_study`: 객체 구성·시나리오·민감도 |
| `memory_dsa/strategy.py` | `quantity`, `make_llm_case`, `assess_case`, `strategy_study`: 근거형 수치와 심층 사례 |
| `memory_dsa/portfolio.py` | 19축에 연결된 예산 함수, `portfolio_study`, 제품군 비교와 조건부 검토 순서 |
| `memory_dsa/portfolio_evidence.py` | `portfolio_sources`, `product_families`: 날짜·상용화 단계·물리 범위가 있는 공개 기록 |
| `memory_dsa/demo.py` | 재현 예제와 파일 생성. 입력 데이터 수집기가 아님 |
| `memory_dsa/report.py`, `memory_dsa/strategy_report.py` | 계산 결과를 표시하는 self-contained HTML 생성 |
| `tests/`, `verify_reproducibility.py` | 산술·계약·회귀와 소스 불변 검증. 실제 DRAM 성능 시험은 아님 |

계산기 request와 전략 `quantity`는 다른 스키마다. `quantity` 객체를 후보의 숫자 필드에 그대로 넣지 않는다. 전략 HTML은 내장된 `strategy-data` JSON을 읽으며, 화면에서 다시 임의의 점수를 만들어 우선순위를 결정하지 않는다.

## 4. 수치·단위·근거의 계약

### 4.1 단위와 물리 범위

내부 계산의 기본 단위는 byte(`B`), `B/s`, watt(`W`), 지정된 시간 단위다. `GB=10^9 B`, `TB=10^12 B`, `GiB=2^30 B`, `TiB=2^40 B`다. `Gb`는 gigabit이며 GB와 다르다. BW를 bit/s에서 B/s로 바꿀 때 8로 나눈다.

`units.convert`가 지원하는 단위는 `B`, `bit`, `Gb`, `GB`, `TB`, `GiB`, `TiB`, `B/s`, `Gbit/s`, `GB/s`, `TB/s`, `GiB/s`, `TiB/s`, `W`, `kW`, `ns`, `ms`다. 함수는 차원 불일치를 거부하며 `None`은 그대로 전파한다. 모든 임의의 단위 문자열을 해석하는 라이브러리는 아니다. 예를 들어 MiB를 표현할 때 실행 입력에는 `2**20`으로 환산한 byte 수를 넣을 수 있다.

die, stack, package, module, assembly, GPU, SOM, system, rack은 서로 다른 물리 객체다. 같은 GB 값이어도 범위가 다르면 직접 비교하지 않는다. 전략 `compare_quantity(required, available)`는 `unit`과 `scope` 문자열이 정확히 같은 경우만 비교한다. 범위 변환이 필요하면 구성 수·복제·사용 가능 비율을 명시한 별도 계산과 설명을 남긴다.

### 4.2 근거형 수치

전략 수치는 다음 형태다. `kind` 값은 해당 생산 함수가 부여하며, 입력 request의 provenance와 혼동하지 않는다.

```json
{
  "value": null,
  "min": null,
  "max": null,
  "unit": "B/s",
  "scope": "one training rank all traffic",
  "kind": "unknown",
  "sources": [],
  "note": "전체 traffic 미확보"
}
```

- **공개값**: 출처·판본·객체 범위가 있는 vendor/논문/표준 기록. peak·nominal·상한을 그대로 표시한다.
- **계산값**: 공개 사실 또는 선언한 가정으로 재현되는 산술. 실측으로 바뀌지 않는다.
- **시나리오·목표**: 동시성, 효율, 처리 창, usable 비율, 미래 조건처럼 사용자가 선택한 값. 사실이나 예측 확률로 표시하지 않는다.
- **미확보값**: `null`/Python `None`. 0, 평균 제품값, 다른 세대의 값으로 채우지 않는다.
- **실측값**: 승인된 실험의 장비·소프트웨어·조건·반복·불확실성과 함께 별도 기록해야 하는 값. 현재 공개 데모에는 사내 실측이 없다.

`value=null`이면서 `min/max`가 있는 레코드는 범위 근거가 있는 경우다. 그 범위를 연속적인 모든 SKU나 용량·BW·전력의 공동 보장 구간으로 읽지 않는다. `compare_envelope`에서 상한을 넘으면 해당 조건의 부족을 판정할 수 있지만, 상한 아래인 `within_envelope_only`는 실제 제품 존재·실행 가능성의 확인이 아니다.

출처 ID `S*`, `P*`, `PF*`, `PX*`는 각각 해당 데이터 모듈의 registry를 찾아야 한다. 본문 숫자를 옮길 때 ID만 남기기보다 원래 레코드의 제목·URL·확인일·주의사항을 함께 보존한다. `checked_at`은 문서 확인일이지 제품 출시일이 아니다.

### 4.3 공개 제품의 상용화 단계

포트폴리오의 제품군 레코드는 `commercial_status`, `status_as_of`, `scope`, `evidence_ids`와 필드별 수치를 가진다. 표준 확정, roadmap, 샘플, 소자 양산·출하, 플랫폼 검증, 완제품 시스템 출하는 서로 다른 주장이다. 샘플 수치가 공개됐다고 양산 SKU나 전체 서버 qualification을 얻은 것으로 표시하지 않는다.

HBM5 및 공개 확인이 없는 DDR6/DDR7 필드는 `null`을 유지한다. HBM4E의 최대 수치, LPDDR6의 die/플랫폼 기록, 시스템 합계는 각 범위와 날짜를 유지한다. 현재 DDR5·LPDDR5X·기존 시스템은 미래 세대만을 추천하지 않도록 비교 대안으로 남긴다. 정확한 기록은 `portfolio.product_families`와 [공개 근거 노트](../inputs/PORTFOLIO_PUBLIC_EVIDENCE.md)를 기준으로 갱신한다.

## 5. 계산 모델과 식

### 5.1 KV 산술 및 decode

`L`=layer 수, `Hkv`=KV head 수, `D`=head dimension, `b`=원소당 byte, `C`=context token 수, `N`=동시 요청 수일 때:

```text
KV bytes/token = 2 × L × Hkv × D × b
KV bytes/request = KV bytes/token × C
전체 resident KV = KV bytes/request × N
decode 논리 KV scan B/s = 전체 resident KV × 요청당 output tokens/s
```

앞의 2는 K와 V다. 시나리오의 `layers_multiplier`, `kv_bytes_multiplier`, `context_multiplier`, `concurrency_multiplier`는 각각 대응 항에 적용된다. 이 scan은 매 decode step에서 선언한 context를 읽는 논리 모델이다. 캐시 재사용·커널·압축·메모리 계층을 측정한 물리 DRAM 트래픽이 아니다.

독립 산술 기준은 `80 layers × 8 KV heads × 128 dimension × BF16 2 bytes`다. 결과는 **327,680 B/token**, `131,072 tokens=128 Ki tokens`에서 **40 GiB/request**, 64개 요청에서 **2.5 TiB resident KV**다. 요청당 20 output tokens/s이면 이 모델의 KV scan은 **50 TiB/s**다. 이 값만으로 GPU 실행 가능성을 주장하지 않는다.

통합 decode 용량은 KV+resident weights+선언한 resident state다. 통합 BW는 KV scan+active weight traffic이다. core request의 weight traffic은 `active_weight_bytes_per_token × concurrency × 요청당 token/s`로 계산한다. 반면 전략의 `make_llm_case`는 선언된 batch step에서 전체 weight를 한 번 읽고 모든 세션의 KV를 읽는 별도 모델이다. 두 식의 결과를 같은 모델인 것처럼 교차 대체하지 않는다.

`make_llm_case`의 70B BF16 사례는 weight payload를 `70e9×2 B`로 근사한다. 4×128 Ki 세션의 weight+KV는 약 **311.80 GB**, 2세션·weight/KV 각각 1 byte 가정은 약 **112.95 GB**다. 정밀도 대안의 품질·scale metadata·runtime 여유는 추가 검증 대상이다. 20 token/s의 역수 50 ms는 설정한 간격 목표이며 실측 ITL/p99가 아니다.

### 5.2 통합 phase 모델

`analyze_integrated`는 네 phase에서 다른 수요를 계산한다. 빠진 합산 항이 있으면 합계도 `null`로 남는다. 유효한 0은 근거가 있는 명시 입력이어야 한다.

| phase | 용량 합계 | 논리 BW 합계 |
|---|---|---|
| `decode` | KV + resident weights + resident state | KV scan + active weight traffic |
| `prefill` | KV + resident weights + resident state | 신규 KV write + input-token 기반 weight traffic + prefill 기타 traffic |
| `training` | weights + activation + optimizer | training bytes/step × steps/s |
| `physical_ai` | weights + resident state + intermediate state | frame bytes × frames/s + physical 기타 traffic |

공통 request 검증은 GQA 차원 필드를 요구하지만, training/physical 수요에 decode scan을 그대로 적용하지 않는다. 결과의 `kv_only_lower_bound`는 별도 참고값이다. phase에 맞지 않는 하한을 전체 수요로 제시하지 않는다.

### 5.3 학습 상태와 optimizer 하한

`portfolio.training_budget`은 특정 FP32 상태 샤딩·BF16 staging 모델이다. 모든 학습 프레임워크의 기본 동작을 대표하지 않는다.

```text
persistent state = parameters × (4 parameter + 4 gradient + 8 Adam moments) / shards
prefetch staging = parameters / layers × prefetch_layers × 2 B
capacity = persistent state + prefetch staging + activation bytes
optimizer BW 하한 = parameters / shards × 28 B / update_window_s
```

28 B는 한 update에 대해 16 B read+12 B write를 선언한 논리 회계다. 기본 예제는 70B, 80 layers, BF16 2-layer staging, activation 32 GiB, update 창 100 ms다. `parameters/layers`는 layer 크기가 같다는 근사이며 embedding, FSDP group, 실제 prefetch peak를 정확히 나타내지 않는다. 4→8 shards에서 용량은 약 **317.86→177.86 GB/rank**로 줄어든다. allocator fragmentation, collective buffers, materialization peak, forward/backward traffic은 포함하지 않는다. `other_traffic_bytes_s=None`이면 `total_bw_bytes_s=None`이다. 공개 프레임워크 자료는 상태와 기법의 근거이며 이 28 B 모델이나 예제 결과가 해당 프레임워크의 benchmark라는 뜻은 아니다.

`reverse_object_targets`로 `objects=n`, usable 비율 `u`, BW 효율 `e`를 선언하면 `nominal capacity/object = demand capacity/(n×u)`, `peak BW target/object = logical BW/(n×e)`다. 8 stack·90% usable의 4-shard 용량 목표는 약 **44.15 GB/stack**이다. 70% BW 효율은 설계 가정이며 실측 상수나 제품 보장이 아니다. 부분 optimizer 하한으로 역산한 BW는 전체 학습 BW 목표로 확정할 수 없다.

### 5.4 Prefill과 prefix reuse

`portfolio.prefill_budget`은 `resident KV=requests×input_tokens×KV B/token`, `new write=resident KV×(1−reuse_fraction)`, `write BW 하한=new write/window_s`를 계산한다. 기본 4 requests×8,192 tokens, 0.5 s 창에서 reuse 0→75%이면 **21.47→5.37 GB/s**다.

reuse는 같은 prefix에 대한 조건부 입력이다. resident KV의 실제 공유·축출·할당 감소는 자동 추정하지 않으므로 `resident_capacity_savings_bytes`는 `None`이다. attention/GEMM·weights·compute가 빠진 상태에서 달성 TTFT나 전체 prefill BW를 계산했다고 하지 않는다.

### 5.5 모듈·채널·assembly

`channel_budget`의 기본값은 **5600 MT/s**, 64 data bits, 70% 효율이다. `peak/channel=transfers_per_s×data_width_bits/8=44.8 GB/s`, 가정한 유효 budget은 **31.36 GB/s/channel**, 8 independent channels는 **250.88 GB/s**다. 80 GiB/s 수요의 최소 독립 채널 수는 `ceil(demand/per_channel_assumed)=3`이다. 기본값 변경을 피하려면 재현 스크립트에 값을 명시한다.

module 수와 independent channel 수는 별도 입력이다. 현재 함수는 한 모듈당 최대 한 채널인 단순 모델로 `independent_channels≤modules`를 검증한다. 2DPC의 속도 저하, DIMM의 복수 subchannel, 플랫폼 지원과 배선은 별도 검증한다.

새 포트폴리오의 Micron 128 GB/DDR5-5600 기록은 decimal GB 기준이다. 기존 카탈로그의 S12 Kingston 128 GiB/DDR5-6400 기록은 다른 SKU와 출처다. 숫자 차이를 단위 변환 오류로 단정하거나 한 제품의 두 표기로 합치지 않는다.

`compose_assembly`는 소자 수로 gross 용량을 합산한다. pin rate와 bus width를 둘 다 지정하면 assembly 전체 인터페이스의 peak는 `pin_rate_gbit_s×1e9×bus_width_bits/8`이며 소자 수를 한 번 더 곱하지 않는다. 전기적 override가 없을 때의 개별 peak 합산은 독립 인터페이스 가정이다. sustained 효율도 명시된 경우에만 계산하며 실제 보장 수치가 아니다.

### 5.6 이기종 메모리 경로와 KV control/data

`transfer_budget`은 한 방향의 payload 전송을 다룬다.

```text
steady-state B/s = payload bytes × arrival rate/s × miss fraction
copy deadline B/s = payload bytes / deadline_s  # arrival>0, miss>0인 경우
required B/s = max(steady-state, copy deadline)
path limit = min(source, destination, fabric)  # 세 항 모두 알려진 경우
transfer time 하한 = payload bytes / path limit
```

일부 경로 성능이 미확보여도 알려진 구간의 최소 상한은 `known_path_ceiling_bytes_s`로 보존한다. 요구 BW가 이 상한을 넘으면 `conditional_shortfall`이며, 미확보 항이 있다는 이유로 알려진 위반을 `unknown`으로 숨기지 않는다. 이때 전체 `path_limit_bytes_s`와 `transfer_time_lower_bound_s`는 `None`이고, 알려진 상한에서 얻은 별도 시간 하한 `known_bound_transfer_time_lower_bound_s`도 실제 전송 시간이나 SLO가 아니다.

40 GiB, 4 arrivals/s, 50% miss, 0.5 s copy 창은 **85.90 GB/s**를 요구한다. path 80 GB/s에서 순수 전송 하한은 약 **536.87 ms**다. miss 25%·1 s 창 대안은 **42.95 GB/s**로 줄어든다. handshake, queue, burst 경쟁, serialization, 장애 복구 시간을 포함한 실제 TTFT/p99는 반환하지 않는다. arrival rate 또는 miss fraction이 0이면 `transfer_required=false`, 필요 BW와 copy deadline BW는 0이고 전송 시간은 `None`이다. 경로 성능도 미확보이면 상태는 여전히 `unknown`이다. 양의 miss가 드물게 발생하는 경우에는 per-copy deadline을 유지한다.

`evaluate_kv_system`은 metadata=`sessions×metadata_bytes_per_session`, control=`ops/s×bytes/op`를 계산한다. direct control link에는 control만, relay control link에는 control+payload를 부과한다. 두 방식의 data link에는 payload를 부과한다. 이것은 방향별 budget이며 duplex라는 이유로 자동 ×2하지 않는다. ingress/egress가 물리적으로 다른 제한이면 각각의 경로·실험으로 검증해야 한다.

`evaluate_placement`는 pool별 assigned bytes/access BW와 path별 traffic/BW를 검사한다. `bind_to_demand=true`이면 전체 용량 수요 대비 배분 누락을 추가 검사한다. 예를 들어 수요 160 GiB에 64 GiB만 배분하면 **96 GiB unassigned**다. 개별 pool의 pass가 전체 수요 충족을 뜻하지 않는다. traffic coverage 검증이나 자동 배치 최적화는 구현하지 않는다.

포트폴리오의 `profiles[].placement`는 선택한 프로필의 수요에 연결된다. `growth`와 `power-constrained`는 BF16 warm prefix 64개×40 GiB, `efficient`는 16개×40 GiB이며, 각각 warm 목록과 겹치지 않는 hot destination 40 GiB를 더해 배분한다. 이 배치 범위는 warm cache와 한 전송 목적지이며 별도의 1-byte decode 대안이나 전체 GPU 실행 구성과 합치지 않는다. 이동 중 임시 복제량은 `transient_replication_bytes=null`, hot usable capacity도 미확보다. `placement.evaluation.coverage.status`는 배분 누락 검사이므로 용량·경로의 판정인 `placement.evaluation.status`와 `coverage.whole_demand_status`를 함께 읽는다.

### 5.7 랙·PSU·냉각과 DRAM 전력

`portfolio.rack_residual`의 입력 경계를 지킨다.

```text
survivable DC supply = shelf_count × shelf_nplus1_dc_w
AC가 허용하는 DC = available_ac_w × psu_efficiency
known DC ceiling = min(알려진 supply DC, AC→DC, cooling DC)
signed memory residual = known DC ceiling − non_dram_dc_w
memory W/object ceiling = signed residual / memory_objects
proposed total DC = non_dram_dc_w + memory_objects × proposed_memory_w
wall AC = proposed total DC / psu_efficiency
```

N+1 DC 출력에는 PSU 효율을 다시 곱하지 않는다. 기본 2 shelves×15 kW N+1 DC, AC 35 kW, 효율 94%, 냉각 28 kW, non-DRAM 24 kW, 80 memory objects는 **50 W/object**를 남긴다. 냉각을 25 kW로 낮추면 **12.5 W/object**다. 제안 25 W/object는 후자의 예산을 넘는다.

잔여량이 음수이면 기존 non-DRAM 부하부터 제한을 넘은 것이다. `residual_memory_dc_w`와 객체별 상한은 부호를 보존하고, 배정 가능한 비음수량은 별도 `allocatable_memory_dc_w`로 제공한다. 일부 ceiling이 미확보이면 알려진 제약 위반은 판정할 수 있어도 전체 clearance는 `unknown`이다.

**기존 core의 `rack.psu_capacity_w`는 wall/AC 입력측 한계이고, 새 함수의 `shelf_nplus1_dc_w`는 DC 출력측 한계다.** 이름만 보고 같은 값으로 복사하지 않는다. GPU/SOM/server TDP는 DRAM-only rail 전력이나 DRAM을 제외한 부하가 아니다. 현재 예제의 non-DRAM은 별도로 선언한 설계 budget이다. busbar·전압강하·reserve·transient·냉각 분포·fault domain을 모두 모델링하지 않는다.

### 5.8 Physical AI와 미래 모델 변화

`edge_sensor_budget` 기본 4×1920×1080 RGB8, 30 fps, 두 memory copies에서는 원시 센서 유입 **0.7465 GB/s**, copy 평균 하한 **1.4930 GB/s**, 5 ms 창의 copy 하한 **9.9533 GB/s**를 계산한다. VLA/VLM workspace·activation·attention·공유 메모리 경쟁이 빠져 전체 BW·용량은 `None`이다.

공개 단일 카메라 VLA의 vendor median과 미래 4-camera+VLM의 p99≤40 ms 요구를 구분한다. median은 p99가 아니며 현재 예제는 후자의 달성 성능을 측정하지 않았다. LPDDR peak보다 센서 하한이 작다는 사실만으로 전체 workload가 실행 가능하다고 판단하지 않는다.

`model-trends`는 MoE의 total resident parameters와 token당 activated parameters를 구분한다. 공개 모델의 parameter 수에 선택한 저장 byte를 곱한 payload는 산술 결과이며 BW나 실제 allocation이 아니다. MLA의 KV 차원이 입력되지 않았으므로 Llama GQA 식을 재사용하지 않는다. 미래 수요는 성장·완화 축을 비교하는 what-if 분석이며, 확률이 보정된 수요 예측이나 연도별 보급 전망이 아니다.

## 6. 실행과 입출력

### 6.1 환경과 기본 생성

저장소 루트에서 실행한다. 구현은 Python 3.11+를 대상으로 하며 저장소의 표준 검증 명령은 `python3.13`을 사용한다. 패키지 설치나 서비스 시작은 필요하지 않다. 아래 경로는 공개·가상 예제를 쓰는 새로운 출력 디렉터리다. `demo`를 같은 경로에 다시 실행하면 정해진 출력 파일들을 다시 쓴다.

```sh
cd /path/to/dsa-memory-simulator
python3.13 -B -m memory_dsa demo --output /tmp/dsa-project-guide-demo
```

| 생성 파일 | 의미 |
|---|---|
| `index.html` | 계산 탐색기 |
| `strategy.html`, `strategy.json` | 제품전략 화면과 그 데이터. `portfolio`는 상단 19축 지도, 기존 cases/products는 하단 심층 사례 |
| `results.json` | core·통합 시나리오와 decision study 데이터 |
| `baseline-request.json`, `integrated-request.json` | 실제 CLI에 다시 넣을 수 있는 입력 예제 |
| `results.csv`, `integrated-results.csv` | 계산 결과 표 |
| `decision-coverage.csv`, `sensitivity.csv` | coverage·민감도 데이터 |
| `assembly-examples.json` | 객체 구성 예제 |
| `internal-gap-schema.json` | 향후 내부 측정 필드와 수신 경로 설명. 자동 overlay loader의 입력 파일이 아님 |

HTML 파일을 열어 화면을 읽을 수 있다. 두 HTML의 연결을 유지하려면 같은 출력 폴더 안에 둔다. `evaluate/integrated/compare`는 JSON만 쓰므로 단독 실행으로 새 HTML이 생긴다고 기대하지 않는다.

### 6.2 이미 생성한 입력으로 단일 실행

```sh
python3.13 -B -m memory_dsa evaluate \
  --input /tmp/dsa-project-guide-demo/baseline-request.json \
  --output /tmp/dsa-project-guide-demo/baseline-evaluated.json

python3.13 -B -m memory_dsa integrated \
  --input /tmp/dsa-project-guide-demo/integrated-request.json \
  --output /tmp/dsa-project-guide-demo/integrated-evaluated.json
```

`demo`는 디렉터리를 만들지만 나머지 세 명령은 출력 파일의 상위 디렉터리가 이미 있어야 한다. 입력 JSON의 중복 key·허용되지 않은 필드·부적합한 단위성 값·NaN/무한 값 등은 검증 대상이다. 오류는 stderr의 `error:`와 종료 코드 2로 반환한다. 현재 `check`, `portfolio`, `strategy`, `overlay`라는 CLI subcommand는 없다.

### 6.3 request 주요 필드

모든 임의 필드를 수용하는 유연한 스키마가 아니다. 아래 설명과 실제 생성 입력을 출발점으로 삼고, 단위·자료 출처 메타데이터를 request에 임의로 추가하지 않는다.

| 위치 | 허용하는 핵심 입력과 주의점 |
|---|---|
| `workload` | 필수 `layers`, `kv_heads`, `head_dim`, `bytes_per_element`, `context_tokens`, `concurrency`, `output_tokens_per_s_per_request`. 선택 `architecture`, `phase`, `resident_weight_bytes`, `active_weight_bytes_per_token`, `expert_fabric_bytes_per_token`, `activation_bytes`, `optimizer_bytes`, `multimodal_state_bytes`, `input_tokens_per_s`, `prefix_reuse_ratio`, `metadata_bytes_per_request`, `control_operations_per_s`, `control_bytes_per_operation` |
| `scenario` | `context_multiplier`, `concurrency_multiplier`, `kv_bytes_multiplier`, `layers_multiplier`, `weight_multiplier`, `technology_capacity_multiplier`, `technology_bw_multiplier`, `technology_power_multiplier`. 모두 양수 |
| `candidates[]` | `id`, `family`, `capacity_bytes`, `usable_capacity_bytes`, `sustained_bw_bytes_s`, `power_w`, `max_modules`, `channels_per_module`, `p99_latency_ns`, `provenance`, `object_level`, `component_object_level`, `units_per_object`. `usable_capacity_bytes`가 명시적으로 null이면 gross로 fallback하지 않음 |
| `rack` | `base_power_w`, `power_limit_w`, `fabric_bw_bytes_s`, `max_channels`, `psu_efficiency`, `psu_capacity_w`, `cooling_limit_w`, `scale_up_bw_bytes_s`, `scale_out_bw_bytes_s`, `control_bw_bytes_s`, `latency_slo_ns` |
| `phase_budget` | 통합 모델 전용: `resident_state_bytes`, `intermediate_state_bytes`, `training_bytes_per_step`, `training_steps_per_s`, `prefill_other_bw_bytes_s`, `frame_bytes`, `frames_per_s`, `physical_other_bw_bytes_s` |
| `placement` | `pools`, `paths`, `bind_to_demand`. pool: `id/family/capacity_bytes/sustained_bw_bytes_s/assigned_bytes/access_bw_bytes_s`; path: `id/source/destination/traffic_bytes_s/bandwidth_bytes_s` |
| `kv_system` | `sessions`, `metadata_bytes_per_session`, `control_operations_per_s`, `control_bytes_per_operation`, `payload_bw_bytes_s`, `control_link_bw_bytes_s`, `data_link_bw_bytes_s`, `server_metadata_capacity_bytes` |

core `analyze`의 top-level은 `workload/scenario/candidates/rack`이고, 통합 함수가 마지막 세 확장 객체를 추가 수용한다. `candidates[].provenance` 허용값은 `user_supplied_unverified`, `synthetic_test`, `scenario_assumption`, `public_catalog`, `local_override`다. `local_override`라는 문자열 자체가 측정의 진실성·권한·적합성을 인증하지는 않는다.

### 6.4 시나리오 비교의 재현 예

다음은 생성 입력을 복사해 `compare`의 실제 wrapper를 만든다. 연도는 시나리오 식별 정보이며 2028년을 예측했다는 뜻이 아니다.

```sh
python3.13 -B - <<'PY'
import json
from pathlib import Path
root = Path('/tmp/dsa-project-guide-demo')
request = json.loads((root / 'integrated-request.json').read_text())
comparison = {
    'request': request,
    'scenarios': [
        {'id': 'base', 'year': 2026, 'scenario': {}},
        {'id': 'context-x2', 'year': 2028,
         'scenario': {'context_multiplier': 2}},
        {'id': 'context-x2-kv-half', 'year': 2028,
         'scenario': {'context_multiplier': 2, 'kv_bytes_multiplier': 0.5}},
    ],
}
(root / 'comparison-request.json').write_text(
    json.dumps(comparison, indent=2, allow_nan=False) + '\n')
PY
python3.13 -B -m memory_dsa compare \
  --input /tmp/dsa-project-guide-demo/comparison-request.json \
  --output /tmp/dsa-project-guide-demo/comparison-result.json
```

각 scenario 객체의 factor는 기본 request의 `scenario`에 얕게 병합되며 같은 key는 해당 scenario 값으로 덮어쓴다. 이전 비교 행의 factor를 다음 행에 누적하지 않는다. ID는 유일해야 하며 year는 양의 정수다. 정밀도 축소가 실제 품질을 유지하는지는 이 비교 밖에서 검증한다.

### 6.5 순수 함수로 핵심 수치를 재현

CLI에 없는 신규 포트폴리오 함수를 사용하려면 다음처럼 Python에서 명시적으로 호출한다. 이 예제는 기본 가정과 결과를 출력하며 실험을 실행하지 않는다.

```sh
python3.13 -B - <<'PY'
from memory_dsa.portfolio import (
    training_budget, prefill_budget, reverse_object_targets,
    channel_budget, transfer_budget, rack_residual, edge_sensor_budget,
)
GiB = 2 ** 30
kv_per_token = 2 * 80 * 8 * 128 * 2
print('KV B/token:', kv_per_token)
print('KV GiB/request:', kv_per_token * 131072 / GiB)

for shards in (4, 8):
    training = training_budget(shards=shards)
    target = reverse_object_targets(
        capacity_bytes=training['capacity_bytes'],
        logical_bw_bytes_s=training['optimizer_logical_bw_lower_bound'],
        objects=8, usable_fraction=0.9, bandwidth_efficiency=0.7)
    print('training:', shards, training, target)
for reuse in (0, 0.75):
    print('prefill:', prefill_budget(reuse_fraction=reuse))
channels = channel_budget(modules=8, independent_channels=8,
    transfers_per_s=5.6e9, data_width_bits=64, efficiency=0.7,
    demand_bytes_s=80 * GiB)
print('channels:', channels)
print('transfer:', transfer_budget(payload_bytes=40 * GiB,
    arrival_rate_s=4, miss_fraction=0.5, deadline_s=0.5,
    source_bytes_s=channels['aggregate_assumed_bytes_s'],
    destination_bytes_s=1e12, fabric_bytes_s=80e9))
for cooling in (28000, 25000):
    print('rack:', rack_residual(cooling_dc_w=cooling))
print('edge:', edge_sensor_budget())
PY
```

함수 기본값을 변경하면 그 함수에 의존하는 포트폴리오·회귀 기대값·문서 예제를 함께 검토한다. 사용자 전용 변형은 별도 스크립트에서 인자를 명시해 보관하는 편이 비교 기준을 유지하기 쉽다.

## 7. 결과 판정과 화면 읽기

### 7.1 후보 상태의 정확한 의미

core의 객체 수는 대체로 `max(ceil(capacity demand/usable capacity), ceil(BW demand/sustained BW))`다. `required_modules`는 호환성 이름이며 실제 표현은 `required_objects`다. assembly이면 `required_components=required_objects×units_per_object`를 별도로 읽는다.

| 필드/상태 | 읽는 방법 |
|---|---|
| constraint `pass/fail/unevaluated` | 그 제약 하나의 산술 판정. unknown 한계는 pass가 아님 |
| candidate `eligible` | 평가한 제약에서 fail이 없다는 뜻. **미평가 제약과 공존할 수 있다** |
| `ranking_eligible` | fail과 unknown이 없어 내부 비교 순위에 포함할 수 있는지. 성능 실증과 별개 |
| `comparison_conclusive` | 비교 집합에 미결 후보가 남아 있는지까지 고려한 비교 완결성. `eligible`와 다른 조건 |
| `insufficient` | 알려진 제약을 위반하는 입력 구성. 시장 전체 부족을 뜻하지 않음 |
| `known_module_lower_bound` | 일부 수요만 알려진 경우의 객체 수 하한. 확정 필요 수가 아님 |
| `whole_system_validated` | 현재 계산 결과에서는 false. TTFT/ITL/p99/tokens-per-joule의 실증을 포함하지 않음 |
| `conditional_headroom` | 선언한 조건·범위에서 계산상 여유. 애플리케이션 성능 검증을 대신하지 않음 |
| `within_nominal_only` / `below_peak_only` | 명목 용량/peak 이내. usable/sustained·SLO 검증은 보류 |
| `within_envelope_only` | 공개 범위 상한 안. 실제 SKU·공동 동작점의 존재를 확정하지 않음 |
| `not_comparable` | unit 또는 physical scope 불일치. 임의 환산으로 판정을 만들지 않음 |

### 7.2 제품 의사결정 지도

`strategy.html`은 다음 순서로 읽는다.

1. **`#portfolio`**: 운영 조건 `growth`, `efficient`, `power-constrained`를 선택한다. 카드의 목표, 현재 대안, 판단을 뒤집는 조건을 함께 읽는다. 선택은 백엔드 `ordered_direction_ids`의 검토 순서를 표시한다.
2. **`#portfolio-analysis`**: 학습·prefill·decode·DDR·transfer·KV control·rack·physical·model trends의 수치와 계산 범위를 읽는다. ‘전체 traffic 미확보’와 ‘계산된 부분 하한’을 구별한다.
3. **`#portfolio-families`**: `#portfolio-family-comparisons`의 역산 목표/공개 수치 비교와 `#portfolio-family-cards`의 원문 기록을 함께 읽는다. `portfolio.family_assessments`의 용량과 BW 평가는 별개이며 공동 보장 동작점을 뜻하지 않는다. 공개 제품의 객체 범위·상용화 단계·기준일·원문 주의사항을 펼치고 시스템 공급 가능성과 동작점 검증을 따로 확인한다.
4. **`#portfolio-trace`**: 19축에서 근거→분석→제품 방향→화면→검증 경로와 보류 판단을 추적한다. 방향 선택은 관련 행을 강조하며 나머지 요구를 숨겨 완료처럼 보이게 하지 않는다.
5. **`#portfolio-inputs`**: 어떤 측정이 어느 임계값을 넘어 결론을 바꾸는지 읽고 플레이북으로 이어간다.

하단 `#directions`, `#matrix`, `#capability`, `#recommendations`는 두 심층 사례다. 단일 GPU와 단일 SOM을 같은 좌표에 직접 비교하지 않는다. 수요·공급 plot은 축의 GB/GB/s와 범위를 먼저 확인하고, 수요의 logical·제품의 nominal/peak 라벨을 함께 읽는다. unknown은 0 좌표의 제품이 아니다. 색은 판정을 보조하며 텍스트 배지·범례·수치와 함께 읽는다.

`index.html`에서는 phase→scenario→candidate를 선택한 뒤 capacity/BW, 구성 제약, 배치 누락, direct/relay와 민감도를 함께 읽는다. 예를 들어 기술 효율 개선으로 객체 수가 줄어도 fabric 제한이 남을 수 있다. 민감도 envelope는 선언한 매개변수 범위의 결과이며 확률적 신뢰구간이 아니다. 2D 표현을 사용한 이유는 범위와 단위를 유지한 비교에 집중하기 위해서이며, 3D plot이 없어도 요구를 충족할 수 있다.

## 8. 사내 후속 작업과 private overlay

현재 구현에는 사내 데이터 연결, 자동 overlay loader, 비공개 스키마 조회 기능이 없다. `internal-gap-schema.json`의 `override_contract`는 문서용 계약이다. 이를 CLI request에 그대로 합치는 동작은 지원하지 않는다.

권한을 가진 담당자가 사내에서 후속 작업할 때의 흐름은 다음과 같다.

1. 공개 기준본과 코드 버전·입력·산출물의 식별자를 보존한다.
2. 승인된 측정만 별도의 private artifact에 기록한다. 표본 수·장비·소프트웨어·온도·전력 경계·동시 workload·오차·출처 접근 조건을 함께 남긴다. 공개 저장소나 배포 HTML에 넣을지 여부는 별도 승인 범위다.
3. 실제 수신 필드가 있는지 검토한다. 필요한 부분만 명시적으로 새 request 또는 함수 인자로 옮기고 `local_override`와 별도 측정 메타데이터의 연결을 유지한다.
4. 동일 조건의 공개/가정 기준과 대체 입력 결과를 비교한다. unknown이 해소된 필드, 판정이 바뀐 제약, 남은 unknown을 기록한다.
5. 구현이 없는 입력은 먼저 모델 확장과 검증을 설계한다. JSON에 필드를 추가해도 모델이 자동 활용하지 않는다.

| 측정 항목 | 현재 수신 위치 또는 한계 |
|---|---|
| usable capacity, sustained BW, DRAM power, p99 latency | 검토한 객체에 대응하는 `candidates[].usable_capacity_bytes/sustained_bw_bytes_s/power_w/p99_latency_ns` |
| fabric BW, PSU efficiency | `rack.fabric_bw_bytes_s`, `rack.psu_efficiency`. 측정 경계가 기존 AC/core 계약과 맞는지 확인 |
| prefix reuse | `workload.prefix_reuse_ratio` 또는 `prefill_budget(reuse_fraction=...)`. 이 두 입력의 모델 범위를 따로 확인 |
| stack별 측정 용량 | 같은 unit/scope의 quantity를 구성해 `compare_quantity`로 비교. 자동 파일 수신 경로 없음 |
| memory rail power | `rack_residual(proposed_memory_w=...)`; `non_dram_dc_w`는 중복 집계를 피하도록 별도 갱신 |
| source/destination/fabric의 directional sustained BW | `transfer_budget`의 세 BW 인자. p99 전체 경로는 별도 실험 결과로 남김 |
| phase의 기타 트래픽 | `training_budget/prefill_budget`의 `other_traffic_bytes_s`. 이미 모델링한 부분을 빼고 넣어 중복 합산을 피함 |
| thermal throttle ratio, context distribution | 공개 gap schema의 `input_path=null`, `not_implemented`. 현재 ingestion field가 아님 |
| 4-camera+VLA/VLM 실제 p99 | 포트폴리오 `edge-tail`은 모델 확장/별도 검증 필요. 현재 센서 산술로 자동 예측하지 않음 |

SKT/NAVER 등 협력사 자료가 보완할 수 있는 공백은 모델별 trace, cache hit·burst 도착, 실제 allocation·traffic, SLO·quality·power 측정 등이다. 이것은 향후 승인된 실험의 입력 요구이며 이 프로젝트가 해당 자료를 확보했다는 뜻이 아니다. HBF/NAND 관련 측정 수집 요구를 이 흐름에 추가하지 않는다. 자세한 조건·입력 경로·반증 기준은 [사내 검증 플레이북](INTERNAL_VALIDATION_PLAYBOOK.md)을 따른다.

## 9. 검증과 재현성 관리

저장소 표준 명령은 다음과 같다. 이 가이드의 예제는 실행 계약을 설명하며, 문서 작성 자체가 이 명령의 최신 PASS 증거를 대신하지 않는다.

```sh
python3.13 -B -m memory_dsa demo --output outputs
python3.13 -B -m unittest discover -s tests -v
python3.13 -B -m compileall -q memory_dsa tests
python3.13 -B verify_reproducibility.py
```

`compileall`은 문법 컴파일 검증이며 명시적으로 bytecode 파일을 만들 수 있다. `verify_reproducibility.py`는 소스를 임시 복사본으로 옮기고 읽기 전용으로 만든 뒤 테스트를 실행하여 소스 해시 불변성과 종료 상태를 확인한다. 같은 HTML 두 개의 byte 동일성만 확인하는 도구나 하드웨어 성능 benchmark가 아니다.

검증은 단순히 19개 이름의 존재를 확인하는 것을 넘어서야 한다. 독립 산술, SI/IEC 및 bit/byte, null 전파, phase별 다른 식, component/system 범위 거부, channel 수 불변성, signed rack residual, AC/DC 회계, direct/relay와 directional transfer, 알려진 제약 위반, 운영 대안에 따른 우선순위 전환, HBF 제외가 실제 결과로 이어지는지 확인한다. HTML은 표 존재 여부에 더해 입력 변경, 축·범례·unknown 표현, 키보드·모바일 가독성을 별도로 확인한다.

재현 기록에는 코드 버전 또는 소스 해시, 입력 원본, Python 버전, 실행 명령, 결과 파일, 검증 로그를 남긴다. 공개 출처가 바뀌면 계산 가정의 변경과 출처 업데이트를 분리해 기록한다. 컴퓨팅 검증 PASS는 실측 성능 PASS가 아니다.

## 10. 현재 가능한 일과 남은 한계

| 현재 가능한 일 | 아직 할 수 없는 일 |
|---|---|
| 명시한 GQA/phase 수요, 객체 수, 채널/경로/전력의 조건부 산술 | cycle-accurate DRAM/controller·실행 queue·실제 kernel 시뮬레이션 |
| 알려진 용량/peak 상한 초과로 지정 구성을 배제 | 명목/peak 안에 있다는 이유만으로 실제 성능·품질·SLO 충족 확정 |
| 훈련·prefill 부분 하한과 누락된 전체 traffic 구분 | 미입력 traffic·activation·allocator peak의 자동 추정 |
| 공개 제품군 상태와 현재 대안, 미래 목표의 비교 | 미공개 HBM5/DDR 규격 생성, 샘플을 상용 시스템으로 승격 |
| 성장·절감 가정 및 제약 변화에 따른 검토 순서 비교 | 시장 규모·고객 채택·제품 출시·연도별 확률 예측 |
| 입력받은 pool/path 배분을 검증 | 최적 placement·적응형 cache controller·routing 정책 자동 생성 |
| 의사결정을 바꾸는 사내 측정 항목과 수신 위치 정의 | 사내/협력사 데이터 조회·자동 merge·실측 인증 |

명시적인 외부 데이터 한계를 남긴 분석은 유용한 결과가 될 수 있다. 다만 빠진 수요 모델·미연결 분석을 단순한 ‘데이터 부족’ 라벨로 덮어 완료 처리하지 않는다. 제품 개발 결론은 워크로드→요구→현재 대안→제약→조건부 목표→반증·측정의 연결을 확인한 뒤 내려야 한다.

## 11. 용어

| 용어 | 이 프로젝트에서의 의미 |
|---|---|
| nominal / gross | 공개 표기 또는 물리 총용량. runtime usable과 다름 |
| usable | 선언한 allocation 조건에서 실제 사용할 수 있는 용량 |
| peak BW | 인터페이스 또는 vendor의 이론/최대 BW. sustained와 다름 |
| sustained BW | 명시한 workload·열·전력·시간 조건에서 유지되는 측정/입력 BW |
| logical traffic | 모델이 회계한 데이터 양. 물리 버스 전송과 반드시 같지 않음 |
| lower bound | 알려진 일부 항만으로 계산한 하한. 합계나 성능 예측으로 승격하지 않음 |
| scope | 한 수치가 적용되는 객체와 동작 범위. 단위가 같아도 scope가 다르면 비교 불가 |
| conditional target | 선언한 객체 수·효율·운영 조건에서 역산한 개발 목표 |
| qualification | 특정 부품·플랫폼·동작점·workload에서 함께 검증하는 과정 |
| GQA / KV | grouped-query attention / key-value cache |
| prefill / decode | 입력 context 처리 단계 / 새 token을 생성하는 단계 |
| TTFT / ITL / p99 | 첫 token까지 시간 / token 간 지연 / 관측 분포의 99백분위 |
| MoE / MLA | total/activated parameters를 분리해야 하는 모델 구조 / 별도 KV 형상이 필요한 attention 구조 |
| DIMM / DPC / channel | 모듈 / 채널당 DIMM 수 / 독립 데이터 전송 경로 |
| warm / hot | 예제의 저장·재사용 계층 역할. 실제 배치 정책의 최적성을 뜻하지 않음 |
| control plane / data plane | metadata·제어 메시지 경로 / 실제 KV payload 경로 |
| N+1 | 한 공급 단위 손실을 고려한 명시된 전원 구성 조건. 전체 시스템 가용성 보장과 다름 |
| evidence / assumption / measurement | 공개 근거 / 선택한 가정 / 조건과 불확실성이 기록된 관측값 |

## 12. 문서·코드 참조 점검 범위

이 원고는 `__main__.py`, `api.py`, `integrated.py`, `units.py`, `catalog.py`, `exploration.py`, `strategy.py`, `portfolio.py`, `portfolio_evidence.py`, `demo.py`, `strategy_report.py`, `verify_reproducibility.py`와 저장소 설계 문서를 기준으로 작성했다. 실행 예제의 함수명·인자명·CLI와 파일 경로는 해당 소스의 인터페이스를 기준으로 한다. 현재 검증 결과와 변경 내역은 소유자의 최신 테스트·리뷰 산출물에서 확인해야 한다.

계속 읽을 문서: [제품전략 설계](PRODUCT_STRATEGY_DESIGN.md), [통합 모델 확장](MODELING_EXTENSIONS.md), [시각화 가이드](VISUAL_GUIDE.md), [감사 설계](AUDIT_DESIGN.md), [테스트 환경](TEST_ENVIRONMENT.md), [모델 트렌드 입력 노트](../inputs/MODEL_TRENDS.md), [사내 검증 플레이북](INTERNAL_VALIDATION_PLAYBOOK.md).
