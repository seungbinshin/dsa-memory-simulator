# 통합 제품전략 화면 검토

2026-10-29. **조건부 제품전략 시각화 목적에 대해 PASS, 아래 범위 제한을 유지한다.** 현재 산출물은 `outputs/strategy.html`이다. 공개 main의 이전 결과와 구분되는 로컬 보완본이며 이 문서는 게시 승인이 아니다.

## 실제 브라우저 확인

Ego Lite에서 생성된 파일을 열고 완료 표시를 기다린 뒤 확인했다. desktop1440×1100, mobile390×844에서 문서 폭은 각각1440/390 px로 가로 넘침이 없었다. 현재 화면은 수치 대조10개, 근거 부족4개, 범위 불일치4개와 원요구19축을 표시한다. 실제 내부 링크의 깨진 target은0개였다.

- **제품 방향:** HBM·DDR·LPDDR 카드에 대상 수요, 용량/BW/조건별 전력 상한/지연 목표 또는 공란, 현재 대안, 반증 조건과 출처를 연결한다. 개발 검토 순서는 시장규모나 수익성 순위가 아님을 표시한다.
- **같은 단위 비교:**10개 수치 대조의 목표와 공개 명목값/peak/상한을 같은 행의 영점·단위로 그린다. 각 행의 scale은 독립적이며 서로 다른 행의 막대 길이를 비교하면 안 된다. 범위/상한은 빗금과 `≤`/범위 표기를 유지한다. 공개 범위가 중간 SKU나 공동 동작점을 보장하지 않는다고 표시한다.
- **미확인 처리:** HBM5의44.15 GB 조건부 목표와 미확인 공급 사양은 함께 보이지만 그래프는 보류된다. missing 값을0으로 그리거나 성능 부족으로 분류하지 않는다. scope 불일치도 수치 비교에서 제외한다.
- **시나리오 전환:** growth에서 HBM→DDR→LPDDR, efficient에서 LPDDR→DDR→HBM, power-constrained에서 HBM→LPDDR→DDR의 검토 순서와 그 이유가 바뀌는 것을 실제 조작으로 확인했다. 이것은 backend 규칙이 출력한 검토 순서다.
- **같은 수요의 배치:** growth의 warm2,748.78 GB/usable921.6 GB와 경로85.90/80 GB/s의 부족을 표시한다. efficient는 warm687.19 GB와 경로42.95 GB/s로 바뀌지만 hot usable 미확인 때문에 전체 판단을 보류한다. `미배정0`과 whole-demand 적합성을 혼동하지 않는다.
- **19축 추적:** 전체19행을 유지하며 edge 방향 선택 시 연결6축을 강조한다. 출처·실제 분석·제품 비교·화면·시험 참조를 따라갈 수 있다. 행 개수를 완료 개수로 주장하지 않는다.

마지막 paired-bar 변경 후 renderer13개 검사가 통과했고 실제 HTML을 재생성해 다시 캡처했다. 제품 BW 상한 비교에서 `≤3,300 GB/s`와 빗금 배경이 실제 렌더링되는 것을 확인했다. 반응형 화면과 그래프 의미를 검사했으며 모든 픽셀·모든 행의 모든 viewport 조합을 검증했다는 뜻은 아니다.

## 독립 시각 검토

UI 작성자와 다른 검토자가 아래5개 최종 스크린샷을 읽었다. 목표→공개 후보→조건부 부족의 연결, 출하/sample 구분, unknown, 배분과 실행 가능성의 차이, 대안·반증·출처 연결이 제품전략 질문에 유용하다고 판정했다. 막대의 행별 scale 제한과 모바일 표시도 확인했다. 차단할 만한 오해를 유발하는 시각 오류는 발견하지 않았다.

그 검토자는 브라우저 상호작용을 직접 실행하지 않았다. 캡처는 대표 HBM 대조·growth 배치·추적표를 포함하며 모든 제품 행이나 모든 모바일 구간의 개별 캡처는 아니다. 위 조작·DOM 확인은 별도의 소유자 브라우저 검수 결과다. 실제 하드웨어·고객 시장 검증은 어느 시각 검토의 범위에도 포함되지 않는다.

## 최종 캡처와 생성물 바인딩

| 캡처 | 내용 | SHA-256 |
|---|---|---|
| [portfolio-overview.png](screenshots/portfolio-overview.png) | 세 방향의 목표·공란·대안 | `2b6b0696cb394a36732a5ae7723eb9fc27e55cb74db0a673de986d2671736f29` |
| [portfolio-placement.png](screenshots/portfolio-placement.png) | 같은 growth 수요의 pool/path 부족 | `2c85007d4c39442fe51bd5c3336e8b08dcb3f644c909012fe78e1468fbd54bbf` |
| [portfolio-comparison.png](screenshots/portfolio-comparison.png) | 수요–현재 제품의 동일 단위 비교 | `ec33010c50e4cc2881dd2c8c15fb39ac29a57adf24fd49d3b5dcf3a293bc555b` |
| [portfolio-trace.png](screenshots/portfolio-trace.png) | 원요구→근거→분석→제품 비교 | `1cf64df993b64ba0a18a3ab181ecbc940933ddd5e9b35822730ce45bf87fbf53` |
| [portfolio-mobile.png](screenshots/portfolio-mobile.png) |390px 수치·판정·막대 비교 | `f121b2eb5de894bdffbeb50a7a4bca3256b4c40769acebc1d57a2b0ab869617c` |

HTML SHA-256: `716ba7ebc27642f1e8f399a8f59cb27563d64efdbda07d3b8b64923ba968de29`.
JSON SHA-256: `c9179210d9a7eed73589e8b304cbc5af32ea9225b9dfb548c56f7b0be49b37f5`.

기존 두 심층 사례의2축 지도와 상세 행은 유지된다. 이번 판정은 공개 근거와 명시적 가정에서 조건부 제품 검토 방향·현재 대안·부족·입력 공백이 드러나는지에 대한 것이다. 입증된 미충족 시장이나 제품 출시 추천을 확정하는 시각화로 해석하지 않는다.
