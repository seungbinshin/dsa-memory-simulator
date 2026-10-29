# Gate 3 — 최종 후보 독립 시각 검토

**판정: PASS.** 새 후보는 이전 PARTIAL 판정의 핵심 문제를 해결했다. 데이터 표의 존재가 아니라 실제 데스크톱·390px 모바일 캡처에서 수요 변화, 공백, 병목, 구성·경로 차이를 읽을 수 있는지를 기준으로 판정했다. 이 판정은 시각화 Gate 3에 한정하며 전체 시뮬레이터의 물리적 정확성이나 실측 성능 인증을 뜻하지 않는다.

## 직접 확인한 근거

- `screenshots/desktop.png`
- `screenshots/mobile-chart.png`
- `screenshots/mobile-routing.png`
- `screenshots/configuration.png`
- `screenshots/coverage.png`
- `screenshots/sensitivity.png`
- 정적 HTML: `../outputs/index.html`, SHA-256 `92415bb80db2a44d55b8927cd6c8f9dca5686f1e80e27cf6f5fcca1fbb903cc0`.

캡처 6개를 각각 실제로 열어 보았다. HTML에 선택 컨트롤 3개와 `prefers-reduced-motion: reduce`일 때 부드러운 스크롤을 해제하는 CSS가 있음을 확인했다. 브라우저를 직접 제어하거나 작업공간 파일을 변경하지 않았다.

## 이전 지적사항 재판정

| 평가 항목 | 결과 | 현재 화면에서 확인한 전달력 |
|---|---|---|
| 축·단위·전후 변화 | PASS | capacity와 logical BW가 별도 축에 TiB/TiB/s 또는 GiB/GiB/s로 표시된다. 0·중간·최댓값, 선형 척도, 직접 값, baseline 대비 배수, 시나리오 입력 변화가 함께 보인다. 작은 막대도 숫자로 비교 가능하다. |
| 모바일 가독성 | PASS | 390px 캡처에서 라벨과 값이 작은 SVG 전체 축소 없이 읽힌다. 차트와 routing 카드가 한 열로 배치되고, 제목·조건·요구/한도·상태가 화면 안에서 읽힌다. |
| 상태·범례·색 | PASS | 색과 함께 `Within bound`, `Limit exceeded`, `Unknown`이라는 텍스트가 있다. 알려진 공개/계산값과 측정·출처가 필요한 공백의 범례가 있으며, unknown을 성능 부족으로 취급하지 않는 설명이 보인다. |
| 병목 | PASS | fabric의 **256 GiB/s 요구 / 192 GiB/s 한도 / 133.3%**와 실패 상태가 명시된다. 100% 초과 막대는 시각적으로 잘라 표시하며 실제 초과값은 텍스트로 보인다는 설명도 있다. module BW 개선만으로 fabric 한도를 없앨 수 없다는 결정상의 의미가 전달된다. |
| 커버리지·공백 | PASS | 후보별 capacity/peak BW/sustained BW/power/channels/p99의 확보·미확보 상태, 정확한 missing 필드, stack 등 object level, 근거 종류와 source ID가 보인다. HBM5 값은 unknown이며 공개 peak를 sustained처럼 보이지 않는다. |
| 구성·경로 trade-off | PASS | 구성 화면은 integrated capacity·logical BW·module 수와 resident/traffic 분해를 나란히 보여준다. direct/relay 경로는 control/data/metadata 예산을 분리하며, relay의 control-link 병목이 즉시 드러난다. 조건부 모델이라는 경계를 유지한다. |
| 민감도·미래 시나리오 | PASS | 성장·정밀도 감소·기술 개선의 조건과 결과 배수가 함께 표시된다. 수요 범위는 확률분포나 신뢰구간이 아니며, 예시 연도를 제품 예측 이정표로 보지 말라는 설명이 있다. |

## 핵심 수치 독립 대조

화면에 나타난 수치의 산술은 별도로 계산했다.

- fabric: `256 / 192 × 100 = 133.333…%` → 화면 `133.3%`, 실패 판정과 일치.
- direct control: `100 KiB/s / 1 MiB/s × 100 = 9.765625%` → 화면 `9.8%`.
- relay control: `(8 GiB/s + 100 KiB/s) / 1 MiB/s × 100 = 819209.765625%` → 화면 `819,209.8%`.
- data link: `8 / 10 GiB/s = 80%`; metadata: `100 / 128 MiB = 78.125%` → 화면 표시와 일치.
- 민감도: capacity `160 / 64 = 2.5×`, traffic `256 / 128 = 2×`; 효율 사례의 `32 / 64`, `64 / 128`은 각각 `0.5×`로 일치.

relay의 요구값은 읽기 쉬운 단위로 반올림되어 있지만 정확한 초과율과 실패 상태를 함께 표시하므로 판단을 흐리지 않는다. 모든 값은 조건부/합성 계산이라는 화면 설명 아래에 있다.

## 실행 검증과의 경계

부모의 실제 Ego Lite 검증 결과로 다음을 전달받았다: 1440/768/390px에서 document width와 viewport 일치, Tab 이동 phase→scenario, scenario/candidate 변경, training 필터의 옵션 1개, 누락 allocation 96 GiB 표시, 44개 테스트 통과. 이 항목은 **부모의 실행 증거**이며 이 검토에서 다시 실행하지 않았다. 이번 독립 검토는 캡처의 시각적 결과와 위 핵심 수치·정적 CSS를 직접 확인했다.

## 남은 조치

**시각화 Gate 3를 막는 추가 수정은 없다.** 더 많은 차트나 3D 표현을 추가할 필요도 없다. 선택적 작은 다듬기로 breakpoint의 긴 `B/s` 수치를 읽기 쉬운 GiB/s와 함께 표시할 수 있으나, 현재 주 차트·구성 패널에서 이미 단위와 한도가 명확하므로 인수 조건에 추가하지 않는다. 결과는 검토한 HTML 판본과 연결해 보존하면 된다.
