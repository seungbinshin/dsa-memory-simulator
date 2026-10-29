# DSA Memory Simulator — 공개 입력 근거 메모

확인일: 2026-10-27 UTC. 목적: 문서 기반 신규 구현에 전달할 최소 공개 입력 근거. 조사 범위는 아래 11개 공개 출처이며, 완전한 시장·규격 조사가 아니다. 원 보고서의 수치를 그대로 사실로 승격하지 않았다. 사내 자료·계정·실측 데이터는 조회하지 않았다.

## 입력 분류와 경계

- `vendor_reported`: 공급사가 공개한 제품·전시·최대 성능값. 독립 실측이나 지속 성능으로 취급하지 않는다.
- `derived_theoretical`: 공개 핀 속도·폭 등에서 계산한 이론값. 피연산자·단위·식을 함께 저장한다.
- `roadmap`: 당시 발표된 미래 전망. 현재 양산 사양이나 달성 사실로 바꾸지 않는다.
- `scenario_assumption`: 사용자가 조정할 수 있는 모델링 선택. 미래 확정값이나 공급사 예측으로 표시하지 않는다.
- `unknown`: 미확보값은 `null`. `0`, 평균값 또는 임의 추정값으로 자동 보충하지 않는다. 필수값 누락은 해당 계산·추천을 미평가로 남긴다.
- 모든 숫자는 원래 단위와 객체 수준(`die`, `stack`, `module`, `GPU`, `rack`)을 보존한다. GB/TB와 GiB/TiB를 구분한다.
- HBF/NAND/SSD는 인접 기술의 포지셔닝만 표시한다. 본분석·추천·최적화·주요 데이터 수집 범위에서 제외한다. 아래 자료가 더 넓은 제품군을 다뤄도 사용자 범위가 우선한다.

## 검토 가능한 대표값

| 대상·프로필 | 확인된 공개값 | 출처·발표일 | 입력 처리와 미확보 항목 |
|---|---|---|---|
| SK hynix HBM4 12H | 36 GB, 11.7 Gbit/s라는 CES 발표. HBM4 세대의 2,048 I/O는 별도 개발완료 발표에서 확인 | S01: 페이지 2026-01-05 / 본문 dateline 2026-01-06. S02: 2025-09-12 | `vendor_reported`. 두 근거를 결합한 `11.7 × 2048 / 8 = 2995.2 GB/s`는 `derived_theoretical`; 지속 BW·W/stack·p99는 `null`. 2,048 I/O를 2,048 독립 메모리 채널로 오기하지 않는다 |
| SK hynix HBM4 16H | 48 GB 전시, 개발 진행 상태 | S01 | 12H의 11.7 Gbit/s를 16H에 복사하지 않는다. 16H 속도·BW·전력은 이 자료로 확정하지 않는다 |
| SK hynix HBM4E 12H | 48 GB, 최대 16 Gbit/s/pin, 고객 샘플 출하 | S03: 2026-06-18 | `vendor_reported`·`sampled`. 이 문서만으로 제품 I/O 폭·채널 topology를 확정하지 않는다. 미검증 폭을 곱한 BW를 확정 스펙으로 넣지 않는다. 전력효율 상대 개선은 절대 W로 환산 불가 |
| HBM5 | 아래 S11은 hybrid bonding의 향후 적용 방향을 논하는 기술 노트이며 제품 정량 사양서가 아님 | S11: 2026-08-25 | 사용자 요구에 따라 capacity/BW/pin rate/channel/power/latency 모두 미확보 시 `null`. 후보 유지·미평가. 사양 미확보를 성능 부족·기술 공백의 증명으로 쓰지 않는다 |
| SK hynix 1c LPDDR6 | 16 Gb **die**; base operating speed **over 10.7 Gbit/s**; 개발 검증 완료. 당시 2026년 하반기 공급 계획 | S04: 2026-03-10 | 16 Gb를 16 GB로 변환하지 않는다. 10.7은 문구상 하한에 가까운 발표값이므로 정확한 peak로 단정하지 않는다. 제품 채널·버스폭을 모르면 module BW=`null`. 공급 계획을 실제 공급 완료로 승격하지 않는다 |
| SK hynix SOCAMM2 | 192 GB LPDDR5X module, 양산 개시 발표. RDIMM 대비 BW·효율의 상대 개선 주장 | S05: 페이지 2026-04-19 / 본문 dateline 2026-04-20 | capacity는 `vendor_reported`; absolute BW·latency·W/module·populated-channel 성능은 `null`. 상대 개선을 특정 RDIMM 기준 없이 절대값으로 환산하지 않는다 |
| SK hynix CMM-DDR5 Gen2 | 256 GB, CXL 3.2, 80 GB/s, pooling 기능을 전시 | S06: 2026-10-16 | `vendor_reported`, 전시/데모 상태. 80 GB/s를 동시 다중 host의 지속값으로 취급하지 않는다. p50/p99/p999·contention·총 fabric 병목은 별도 `null` |
| DDR6 | 2023년 Samsung roadmap은 2028년 9,600 Mbit/s DDR6를 전망 | S07: 2023-12-04 | `roadmap`, historical projection. 현재의 확정 JEDEC 규격·양산 제품으로 사용하지 않는다. future sensitivity profile에서 명시적으로 켤 수 있으나 normative default는 `null` |
| DDR7 | 이번 제한된 공식 자료 조사에서 정량 제품/규격을 검증하지 못함 | 조사 한계 | 모든 미확보 정량 필드 `null`. GDDR7을 DDR7의 근거로 사용하지 않는다. “존재하지 않는다”는 결론이 아님 |
| NVIDIA **DGX** Vera Rubin NVL72 | 72 Rubin GPU + 36 Vera CPU, rack HBM4 20.7 TB, memory BW 1,400 TB/s | S08: 날짜 미표시, 2026-10-27 확인 | 정확한 DGX 프로필에 고정. vendor system specification, sustained 아님. 다른 Vera Rubin 자료·판본의 수치를 섞지 않는다. rack capacity 합산이 단일 GPU에서 자유롭게 주소 가능한 메모리를 의미하지 않음 |
| AMD Helios | 72 MI455X, 최대 HBM4 31 TB, memory BW 1.7 PB/s, scale-up 260 TB/s, scale-out 43 TB/s | S09: 날짜 미표시, 2026-10-27 확인 | vendor maximum/aggregate specification. BW 방향·프로토콜 overhead·bisection·실효 efficiency가 같다고 가정하지 않는다. 이 메모는 CPU memory BW 또는 GPU별 값으로 나누어 확정하지 않음 |
| Rack power delivery | 800 VDC, 2027년부터 1 MW급 이상 IT rack을 지원한다는 아키텍처 방향 | S10: 2025-05-20 | `roadmap`/architecture target. 현재 모든 rack 전력 또는 특정 Rubin 제품의 TDP가 아님. PSU efficiency·redundancy·transient·cooling 조건은 시나리오/입력으로 분리 |

## 출처 목록 — 공개 문서만

1. **S01 — SK hynix CES 2026 제품 발표(CN)**. HBM4 12H 36GB/11.7Gbps와 16H 48GB 전시를 본문에서 확인. [공식 발표](https://news.skhynix.com/cn/sk-hynix-showcases-next-generation-ai-memory-innovations-at-ces-2026/)
2. **S02 — SK hynix, HBM4 개발 완료·양산 준비**. 2,048 I/O와 세대 변화의 공급사 발표. [공식 발표](https://news.skhynix.com/en/sk-hynix-completes-worlds-first-hbm4-development-and-readies-mass-production/)
3. **S03 — SK hynix, 12-layer HBM4E samples**. 48GB/12H, 최대16Gbps/pin, 샘플 출하를 본문에서 확인. [공식 발표](https://news.skhynix.com/en/sk-hynix-ships-samples-of-12-layer-next-gen-hbm4e-2/)
4. **S04 — SK hynix, 1c LPDDR6 development**. 16Gb, over10.7Gbps, sub-channel/DVFS와 당시 공급 계획. [공식 발표](https://news.skhynix.com/en/1c-lpddr6-development-2026/)
5. **S05 — SK hynix, 192GB SOCAMM2 mass production**. 절대 BW는 해당 발표에서 확보되지 않음. [공식 발표](https://news.skhynix.com/en/mass-production-socamm2-192gb/)
6. **S06 — SK hynix, OCP Global Summit 2026**. CMM-DDR5 Gen2 256GB/CXL3.2/80GB/s와 pooled memory demo. [공식 행사 보고](https://news.skhynix.com/en/ocp-global-summit-2026/)
7. **S07 — Samsung, Memory Tech Day 2023**. DDR6 2028/9600Mbps는 2023년의 로드맵 전망. 검색 인덱스의 공식 본문에서 해당 문구를 확인했으나 현재 page extraction의 본문 검색은 반환하지 않았으므로 `historical_roadmap`으로만 보관한다. [공식 기술 블로그](https://semiconductor.samsung.com/kr/news-events/tech-blog/memory-tech-day-memory-in-the-age-of-ai-data/)
8. **S08 — NVIDIA DGX Vera Rubin NVL72 product specs**. 제품 페이지의 quick/full specs가 20.7TB 및1400TB/s를 반복 표기. [공식 제품 사양](https://www.nvidia.com/en-us/data-center/dgx-vera-rubin-nvl72/)
9. **S09 — AMD Helios Rackscale Platform**. 72GPU/31TB/1.7PB/s/260TB/s/43TB/s. [공식 플랫폼 설명](https://www.amd.com/en/partner/browse-by-resource/partner-insights-articles/helios-open-standards-ai-solution.html)
10. **S10 — NVIDIA 800 VDC architecture**. 미래 power-delivery 방향과 기존54V의 scaling 제약. [공식 개발자 글](https://developer.nvidia.com/blog/nvidia-800-v-hvdc-architecture-will-power-the-next-generation-of-ai-factories/)
11. **S11 — Hybrid Bonding technical note**. SK hynix Newsroom 게재 전문가 기술 해설. HBM5 packaging 방향의 논의이며 제품 사양·채택 시점 확정 근거로 쓰지 않음. [기술 노트](https://news.skhynix.com/en/tech-note-series-ep2/)

JEDEC 사이트는 이번 도구에서 robots.txt 접근 제한을 반환했다. 이를 우회하지 않았다. 따라서 DDR6/DDR7 규격 공표 여부를 이 메모만으로 확정하지 않는다. 수치 출처가 공개되어 있다는 사실과 기술 표준으로 확정되었다는 사실은 별개다.

## 시뮬레이터에 넘길 모델링 주의점

1. 위 자료는 미래 시장 수요의 확률분포를 제공하지 않는다. 연도·성장률·보수/기준/가속 값은 조정 가능한 scenario assumptions로 두고, 확정 예측과 구분한다. 특정 연도 묶음은 사용자 확정값이 아니다.
2. 모델 규모만 늘리는 단일 축 대신 active weights, KV 구조/정밀도, context distribution, concurrency, generated-token duration, prefix reuse, prefill/decode 분리의 이동량, multimodal/VLA 중간 상태를 독립 입력으로 만든다. 효율화가 수요 증가를 상쇄하는 반대 시나리오도 허용한다.
3. `2 × layers × kv_heads × head_dim × bytes_per_element`는 해당 K/V 구조를 사용하는 architecture의 logical KV payload 식이다. MLA 등 다른 구조에 보편 적용하지 않는다. 양자화 scale/metadata·padding·fragmentation·replication을 생략했다면 명시한다.
4. logical tensor bytes와 DRAM bus traffic, rack memory 합계와 placement feasibility, aggregate BW와 경로별 가용 BW, GPU/전체 rack power와 DRAM power를 구분한다. 실측 없는 TTFT/ITL·tokens/J는 calibrated measurement처럼 표시하지 않는다.
5. 사내 보완은 입력 필드와 측정 계획만: sustained BW, p99 under contention, W/module/stack, thermal throttling, KV hot-set/reuse, workload distribution, PSU transient/headroom. SKT/NAVER·사내 데이터에 실제 접근했다는 주장을 하지 않는다.

이 메모에서 실행한 것은 공개 문서 검색·읽기와 요약뿐이다. 실제 하드웨어 측정, 모델 benchmark, 시뮬레이터 실행 또는 코드 테스트를 수행하지 않았다.
