# 19축 제품전략 보완 — 독립 검토와 한계

검토 기준: 2026-10-29. 이 문서는 공개자료와 명시적 설계 가정을 이용한 분석의 검토 기록이다. 실측, 시장 조사, 제품 qualification 또는 출하 계획의 승인 기록이 아니다.

## 누락 원인과 수정 범위

앞선 검수는 미래 제품 방향을 가상 수요 변화와 사양 필드의 유무로 축소했고, 시각화를 계산값의 가독성 위주로 판정했다. 원래 요청의 ‘어떤 수요에 어떤 제품 역량이 필요한가, 기존 대안으로 어디까지 되는가’를 인수 기준과 대조하지 않은 것이 원인이었다. 공개 사양의 부재만으로 설명할 수 있는 누락이 아니다.

이번 보완은 원요구 19축을 9개 분석, 3개 조건부 제품 방향, 3개 운영 profile에 연결했다. 각 방향에는 대상 수요, 용량/BW/전력/지연 목표 또는 공란, 근거와 가정, 현재 제품·소프트웨어·구성 대안, 반증 조건, 다음 내부 측정이 있다. [19축 추적표](REQUIREMENTS_TRACEABILITY.md)는 기존 24개 계산기 검사와 다른 분류임을 설명하고 모든 축의 제한을 기록한다.

## 검토 결론

- **HexaHarness 실제 적용:** 설치된 HexaHarness 1.0.0의 정책 관찰, 기존 작업의 연속 기록, 실제 명령 실행을 사용했다. simulator의 가상 adapter나 자체 작성 성공 플래그로 대체하지 않았다. `doctor`는 이슈 없음, build/lint/test가 필수 센서임을 확인했다. 이 문서는 최종 close 이전의 독립 검토를 기록하며, 전체 회귀와 완료 여부는 실제 최종 checkpoint의 센서 결과로 판정한다. 무인 운영·배포 준비 완료는 주장하지 않는다.
- **원요구와 다각도 관점:** 독립 의미 검토에서 19축의 조건부 분석 연결을 완료로 평가했다. 14축은 분석과 의사결정 연결, 4축은 필요한 입력과 현재 대안을 명시한 판단 보류, HBF/NAND 1축은 범위 제외다. 미공개 세대의 실제품 적합성, 시장 규모와 고객 채택, 전체 phase 성능은 별도 미검증이다.
- **시각화:** 같은 객체와 단위의 목표–공개 역량 비교, 알려진 부족·판단 보류, profile 전환, 실제 배치·경로 제약, 원요구에서 출처와 비교까지의 연결을 검수한다. 정확한 화면 기록은 [시각 검토](PORTFOLIO_VISUAL_REVIEW.md)를 따른다. 보기 좋은 표의 존재만으로 통과시키지 않는다.

18개 제품군 대조 중 10개는 수치 대조, 4개는 unknown, 4개는 scope 불일치다. 이를 18개 제품의 적합성 통과로 세지 않는다. 알려진 nominal/peak 이하라는 결과도 실행 가능성의 증거가 아니다.

## 제품 검토 방향의 실제 근거

| 방향 | 계산된 조건부 결과 | 먼저 비교할 대안과 판단을 뒤집는 조건 |
|---|---|---|
| HBM 용량·BW·전력 공동 검증 | 선언한 70B 학습 상태에서 4/8 shards는 약317.86/177.86 GB/rank. 8 stack·90% usable 가정은 약44.15/24.70 GB/stack을 요구한다. | 현행36 GB HBM4, 48 GB HBM4E sample, stack/샤딩/정밀도 대안을 비교한다. sample 용량/BW 최대치를 공동 qualified 동작점으로 묶지 않는다. HBM5 사양은 null이다. 현재 대안이 품질·SLO·전력에 맞으면 새 세대 필요성은 약해진다. |
| DDR warm 계층과 KV 경로 | 64×40 GiB warm 수요는2,748.78 GB이며 지정8×128 GB×90% usable=921.6 GB를 넘는다. 40 GiB·4 arrivals/s·miss50%·0.5 s 조건은85.90 GB/s를 요구해80 GB/s 경로도 넘는다. | 현재 고밀도 DDR5/MRDIMM, slot 수, 독립 channel 수, retention/hit rate와 복사 deadline을 함께 비교한다. 용량만 늘리면 경로 문제가 남는다. 작은16-prefix 조건도 hot usable 용량이 미확인이면 전체 적합성을 보류한다. |
| LPDDR Physical AI QoS 검증 | 4-camera 설계 가정의 copy 예산은 평균1.49 GB/s,5 ms window 하한9.95 GB/s. 전체 VLA/VLM 수요와 DRAM rail 전력은 미확인이다. | 기존 Thor/LPDDR5X와 공개 LPDDR6 표준·개발·플랫폼 검증을 구분한다. vendor median을40 ms p99로 바꾸지 않는다. 먼저 동시성·tail·열·품질을 측정하며 현재 구성으로 만족하면 신규 density/BW 요구를 보류한다. |

이 값들은 설계 시나리오의 목표·하한·상한이다. 고객 수요 예측 확률이나 확정 제품 사양이 아니다. 랙 조건별12.5/50 W per-stack은 서로 다른 조건에서의 잔여 전력 **상한**이며 허용 최소–최대 또는 측정값이 아니다. prefilling에서75% reuse는 KV write 예산을21.47→5.37 GB/s로 줄이지만 전체 prefill traffic나 resident KV 감소를 입증하지 않는다.

## 독립 검토에서 발견하고 고친 결함

1. zero arrival/miss에도 per-copy deadline이 가짜 BW 요구를 만들던 경계값을 수정했다. 양수 miss에는 per-copy 요구가 유지된다.
2. 일부 경로가 unknown이면 알려진 다른 병목의 위반까지 unknown으로 숨기던 계산을 수정했다. 전체 경로 성능과 실제 SLO는 계속 미확인이다.
3. 40 ms p99 설계 목표에 vendor 출처가 자동 전파되던 표기를 scenario assumption으로 분리했다.
4. growth의64-prefix 수요를16-prefix 배치와 연결하던 불일치를 profile별 동일 수요 바인딩으로 수정했다. warm과 대표 hot destination은 disjoint KV slice이며 전체 active deployment를 뜻하지 않는다.
5. 원요구 추적에 제품 공급 근거와 비교 ID가 빠지던 연결, 중복 `#` 링크를 고쳤다.
6. 숫자만 나열한 제품 대조에 같은 영점·단위의 막대 비교를 추가하고 범위/상한과 unknown을 구분했다.

최종 core에서 독립 검토자가21개 probe를 실행해21/21 PASS 및 전후 hash 불변을 확인했다. 별도 의미 검토자가 소스·수식·출처 연결과 19축을 대조했다. 작성자 회귀는 portfolio29개, renderer13개가 실제 HexaHarness 실행에서 각각 통과했다. 이는 서로 다른 검증 범위이며 단순 합계를 전체 suite의 개수로 주장하지 않는다.

## 재현과 추가 입력

```sh
python3.13 -B -m memory_dsa demo --output outputs
python3.13 -B -m unittest discover -s tests -v
```

결과는 `outputs/strategy.html`과 `outputs/strategy.json`이다. [프로젝트 가이드](PROJECT_GUIDE.md)는 실행·식·화면 해석을, [내부 검증 플레이북](INTERNAL_VALIDATION_PLAYBOOK.md)은 19축별 필드·실험·통제·불확실성·반증·반영 위치를 제공한다. 자동 내부자료 loader는 없으며 비공개 입력은 승인된 내부 overlay에 분리한다. thermal/context 분포와 tail 모델의 미지원 상태를 실제 입력 지원으로 표시하지 않는다.

## 소스·산출물 바인딩

| 대상 | SHA-256 |
|---|---|
| `memory_dsa/portfolio.py` | `dc81a26e33ee14b1c6300d2bf68714ea94f5c0e13f5f6145cc6282d488b9a112` |
| `memory_dsa/portfolio_evidence.py` | `83883ee51dabf2c91455b23a53cb1abcccdf6b11419bb6f52fd1e57454980ab3` |
| `memory_dsa/strategy.py` | `bbad0d030d44122f3010d6f17e82c53d780abc8a554b9c9a8cb1eb72571b3870` |
| `memory_dsa/strategy_report.py` | `fefc9f09298fdd3935ef84bb8e498784955f8dce77cbf11ae2571c36450922a2` |
| `outputs/strategy.html` | `716ba7ebc27642f1e8f399a8f59cb27563d64efdbda07d3b8b64923ba968de29` |
| `outputs/strategy.json` | `c9179210d9a7eed73589e8b304cbc5af32ea9225b9dfb548c56f7b0be49b37f5` |

공개자료에 기반한 조건부 제품 전략은 재현 가능하지만 실측으로 보정된 성능·전력 예측, 시장 미충족의 입증, 제품 우월성·출시 승인까지 제공하지 않는다. 사내 측정과 고객/운영 분포가 들어오면 목표와 우선순위를 다시 평가해야 한다. HBF/NAND는 본분석과 필수 사내 수집에서 제외된다.
