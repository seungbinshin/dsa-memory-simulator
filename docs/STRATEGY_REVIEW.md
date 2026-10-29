# 독립 제품전략 재검토 — 2026-10-29

**전체 원요구 Gate 2·3: PARTIAL. 두 선택 사례의 근거 연결·조건부 방향·시각 전달: 확인됨.** 두 사례의 산술과 의미에 차단할 오류는 독립 검토에서 발견되지 않았다. 이 판정을 전체 제품군·시장 분석 완료로 확대하지 않는다.

## 왜 이전에 누락됐는가

요구를 구현과 검수로 번역하는 과정에서 미래 제품 의사결정을 합성 시나리오 계산으로, 시장/워크로드 커버리지를 사양 필드의 확보 여부로 축소했다. 계산·단위·모바일 표현 검사를 통과한 뒤에도 사용자가 어떤 제품 역량을 왜 개발해야 하는지 답을 얻는지 대조하지 않았다. 원 요구의 제품전략 질문을 최종 검수 기준으로 유지하지 못한 책임이며, 자료 부족만으로 설명되는 문제가 아니다.

## 실제로 연결된 두 방향

1. **장문 LLM의 추가 usable 용량/계층화는 조건부 검토 대상이다.** 공개 Llama 3.1 70B 구조에 128 Ki 문맥, BF16 weights/KV, 1/2/4 독립 세션, 20 tokens/s/session라는 운영 가정을 붙였다. payload는 약 182.950/225.899/311.799 GB다. B300의 288 GB nominal은 1·2세션을 용량만으로 배제하지 못하며 4세션은 초과한다. 낮은 정밀도의 2세션은 약 112.950 GB로 H200 nominal 안에 들어간다. 기존 제품·소프트웨어 대안을 검증한 뒤에도 품질/SLO/비용 조건에서 부족할 때 신규 용량 역량을 검토한다. 모든 수치가 단일 GPU 상주 조건이며 시장 성장률이 아니다.
2. **Physical AI는 새 LPDDR 용량보다 경합·지연·효율 검증이 우선이다.** Thor의 공개 단일 VLA 사례는 이미 실행된다. vendor median 81/40 ms와 미래 동시 부하의 p99 목표를 구분했다. 추가 용량·BW·DRAM 전력 목표는 근거가 없어 null이다. 동시 VLA/VLM·다중 camera에서 실제 병목과 tail SLO를 측정한 뒤 QoS/BW 역량의 필요성을 판단한다.

각 방향은 source IDs → workload parameters → assessment IDs → target quantities → alternatives → disconfirming conditions → internal validation으로 연결된다. `outputs/strategy.json`이 정확한 데이터이며 HTML은 이를 그대로 포함한다. 공급사의 측정, 공개 명목/peak, 근사 파생값, 운영 가정, 미확인을 별도 유형으로 유지한다.

## 독립 검토가 확인한 반례와 경계

- B300을 현재 비교군에 포함하여 H200 한계를 신제품 시장 공백으로 오인하지 않는다.
- nominal 용량 안에 들어가는 경우도 usable capacity·overhead·sustained BW·SLO가 없으므로 실행 성능 미검증으로 남긴다.
- 4세션 payload는 B300 표기를 288 decimal GB 또는 288 GiB로 해석해도 초과하지만, 여전히 선언한 구성의 조건부 제외다. 단위 민감도는 실제 usable 용량을 알아냈다는 뜻이 아니다.
- low-precision 대안의 품질·metadata·kernel 지원은 검증하지 않았다. 가중치/KV의 감소 가능성을 새로운 제품이 불필요할 수 있는 반증으로 명시한다.
- Thor의 median 실행 성공을 p99 또는 미래 동시 부하의 성공으로 바꾸지 않는다. GPU/SOM 전력을 DRAM 전력으로 전용하지 않는다.
- 하드웨어 실험·고객 수요 빈도·시장 크기·전체 경쟁 대안·확정 개발 우선순위는 확인하지 않았다. 신규 미충족 시장이 입증됐다는 문구를 사용하지 않는다.

## 원 요구와 남은 상태

19개 추적 행은 **8개 미평가, 4개 부분 산술, 5개 조건부 사례, 1개 입력 지도, 1개 포지셔닝 제외**다. 각 행에 근거/입력/출력/화면/검증 및 전략 상태를 기록했다.

HBM4/4E/5·DDR6/7·LPDDR6, training/prefill의 제품 전략은 미평가다. 랙/PSU, module/channel, disaggregation, KV control/data는 기존 산술 또는 대안 연결 수준이다. Dense/MoE 전반의 제품 전략도 입증되지 않았다. 이 영역들은 단순히 명칭이 등장하거나 null을 잘 보존한다는 이유로 완료가 되지 않는다. HBF/NAND는 요청대로 포지셔닝만 유지한다.

## 검수 방식과 재현

- 구현 작성자와 별도 검토자가 소스·JSON·근거 문서·저장된 실제 화면을 읽고 위 결론과 반례를 독립적으로 확인했다. 별도 사실 검토자는 공개 근거와 데이터 매핑에 차단할 오류를 발견하지 않았다.
- 신규 의미 회귀 12개와 renderer 검사 5개가 실제 HexaHarness 경로에서 통과했다. 최종 build/syntax/full-regression 결과는 현재 완료 checkpoint의 실제 sensor 로그로 판정한다. 미실행 결과를 여기서 선기록하지 않는다.
- owner sensor의 7개 그룹은 별도 수식 대조, 기존 제품 반례, precision 상쇄, median/p99 구분, 추천 연결, legacy null/exclusion 보존, HTML/JSON 완전 일치를 검사한다. 구현자 작성 검사이므로 독립 도메인 검토와 동일시하지 않는다.
- [실제 시각 확인](STRATEGY_VISUAL_REVIEW.md)은 Ego Lite 실행·선택 변경·단위·viewport·키보드 확인과 캡처를 기록한다. 독립 검토자는 저장 캡처를 읽었으며 브라우저를 직접 조작했다고 주장하지 않았다.
- 재현: `python3.13 -B -m memory_dsa demo --output outputs`, `python3.13 -B -m unittest discover -s tests -v`. `outputs/strategy.html`을 열면 제품전략 보완 화면을 볼 수 있다.

이 보완은 검토용 로컬 사본이며 기존 공개 main을 변경하지 않았다.
