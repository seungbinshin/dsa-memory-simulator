# 제품전략 화면의 실제 확인 — 2026-10-29

이 기록은 `outputs/strategy.html`의 실제 Ego Lite 실행 확인이다. 원래 모든 제품/시장 축이 완료됐다는 판정이 아니다. 기존 Gate 3 PASS를 제품전략 전체 완료로 확대한 오류는 `VISUAL_AUDIT.md`의 정정에 남겨 두었다.

## 화면이 답하는 질문

| 사용자 질문 | 실제 화면·내용 | 증거 |
|---|---|---|
| 어떤 조건에서 추가 용량이 필요한가? | 단일 GPU의 1/2/4세션 BF16 및 저정밀도 대안을 H100/H200/B300과 비교한다. B300의 현재 범위를 포함하고 구성 부족과 시장 미충족을 분리한다. | [요구 충족표](screenshots/strategy-matrix.png), HTML `#matrix` |
| 미래 운영 가정이 현재 역량과 어디서 충돌하는가? | 같은 단일 GPU 범위에서 decimal GB와 GB/s를 표시한다. 제품 명목/peak와 조건부 payload/logical traffic의 종류 차이를 명시한다. 4세션 선택 시 B300 용량 초과가 보이고, 저정밀도 2세션은 H200 nominal 안으로 돌아온다. | [역량 지도](screenshots/strategy-map.png), HTML `#capability` |
| 그 결과로 무엇을 개발·검증해야 하는가? | 고용량 현존 GPU·정밀도 대안을 먼저 비교하고, 충족되지 않는 조건에서 추가 usable 용량/계층화를 검토한다. Physical AI는 이미 지원된 baseline이 있어 경합·tail latency·효율 검증을 우선한다. 목표값 또는 null, 근거, 대안, 반증, 내부 측정으로 이어진다. | [추천 요약](screenshots/strategy-desktop.png), HTML `#recommendations` |
| 미확인값을 시장 공백으로 잘못 읽지는 않는가? | Thor의 공개 median 사례와 미래 동시 부하의 null 수요·가정 p99를 별도 패널로 나눈다. 공급 사양을 수요 목표로 복사하지 않는다. | [Physical AI](screenshots/strategy-edge.png) |

## 실제 조작 및 가독성

- 실제 viewport/document width: **1440/1440, 768/768, 390/390**. 모바일에서는 2D 지도를 축별 막대로 전환해 단위와 제품 상한을 유지한다. [모바일 화면](screenshots/strategy-mobile.png).
- `#case-select`에서 `llm-bf16-4`와 `llm-lowprecision-2`를 선택해 값·판정 변경을 확인했다. 단순 초기 렌더링 확인만으로 상호작용을 주장하지 않았다.
- 키보드 Tab은 선택 컨트롤에서 근거 링크로 이동했다. 6개 workload 데이터, 19개 원요구 추적 행, 추천 카드의 반증 문구를 실제 DOM에서 확인했다.
- 내부 anchor의 대상 누락 0개, 외부 runtime asset 0개. 외부 근거 링크는 사용자가 열기 전 로딩하지 않는다.
- HTML에 포함된 JSON과 `strategy.json`의 완전 일치는 별도 owner sensor가 확인한다. 시각적 표현을 맞추기 위해 계산 결과를 바꾸지 않았다.

## 판정 경계

**두 선택 사례의 제품전략 연결과 시각 전달은 확인했다. 전체 원요구의 Gate 2/3는 PARTIAL로 유지한다.** HBM4/4E/5, DDR6/7, LPDDR6에 대한 제품별 개발 결론이나 전체 시장 기회 지도는 완성되지 않았다. 19개 추적 행은 완료율이 아니라 분석·미평가·입력 공백·제외 상태를 구분하는 기록이다. 2D 지도가 존재한다는 이유로 미평가 축을 완료로 셈하지 않는다.

스크린샷은 실제 브라우저 페이지 캡처이며 생성한 그림이나 mock이 아니다. 하드웨어 실측, 시장 크기, 고객의 지불 의사, 출하 전망, calibrated p99를 검증한 기록은 아니다.
