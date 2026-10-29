# 메모리 계열·제품 단계의 공개 근거

확인 기준일: **2026-10-29**. 이 문서는 공개 표준, 공급사 발표, 플랫폼 검증을
연결하는 사실 요약이다. `memory_dsa/portfolio_evidence.py`의 `portfolio_sources()`와
`product_families()`가 같은 범위의 구조화 데이터를 제공한다. 공개 자료는 전체 시장의
전수조사가 아니며, 확인하지 못한 후속 발표가 없다고 주장하지 않는다.

## 수치와 상태를 읽는 방법

- 표준 발표, 로드맵, 샘플 출하, 부품 양산·출하 주장, 플랫폼 검증, 시스템 출하 주장은
  서로 다른 상태다. 과거 공급 계획의 날짜가 지났다고 완료로 바꾸지 않는다.
- 레코드의 `status_as_of`는 그 주장의 발표일이다. 날짜 없는 현재 페이지는 확인일을
  사용하며 본문에 이를 표시한다. 전체 근거에는 별도의 `checked_at`이 있다.
- GB/Gb 원문을 보존하고 decimal 배수로 B를 계산한다. 이 정규화가 실제 allocatable
  bytes나 binary 표기 해석을 입증하지 않는다. 경계 근처 비교에서는 단위 민감도를 유지한다.
- die, stack, module, GPU, SOM, CPU 구성, 8-GPU 시스템은 서로 다른 비교 단위다.
  집계 수치를 나눠 정확한 하위 부품 사양을 만들지 않는다.
- `value/min/max`는 점·상한·하한·포트폴리오 범위를 구분한다. `>11`처럼 엄격한 하한은
  `min=11`과 설명으로 보존하며, 11이 실제 제품값·보장값·상한이라는 뜻이 아니다.
  포트폴리오 범위는 모든 중간 SKU나 속도·용량 조합을 보장하지 않는다.
- peak/pin rate는 애플리케이션 지속 BW가 아니다. usable capacity, sustained BW,
  DRAM 절대 전력, p99는 이번 근거로 채우지 않는다. GPU/SOM 전력은 DRAM 전력이 아니다.

## 공식 근거와 적용 범위

| ID | 근거·발표일 | 사용한 사실과 제한 |
|---|---|---|
| PF01 | [JEDEC JESD270-4 발표](https://www.businesswire.com/news/home/20250416843598/en/JEDEC-and-Industry-Leaders-Collaborate-to-Release-JESD270-4-HBM4-Standard-Advancing-Bandwidth-Efficiency-and-Capacity-for-AI-and-HPC), 2025-04-16 | 최초 표준 기준 8 Gb/s/pin, 2048-bit/stack, 32 channels와 채널당 2 pseudo-channels. 24/32 Gb die와 4/8/12/16-high, 최대 64 GB. `8e9×2048/8=2.048e12 B/s`는 이론 산술이며 발표문은 약 2 TB/s로 표기한다. 최신 모든 제품의 상한이 아니다. |
| PF02 | [Samsung HBM4 상용 출하](https://news.samsung.com/global/samsung-ships-industry-first-commercial-hbm4-with-ultimate-performance-for-ai-computing), 2026-02-12 | 양산·상용 고객 출하 주장. 12-high는 24 또는 36 GB, 2048 I/O, 11.7 Gb/s와 최대 13 Gb/s 향상 가능치, 최대 3.3 TB/s/stack. 16-high 최대 48 GB는 향후 옵션이다. |
| PF03 | [Micron HBM4·SOCAMM2 생산 발표](https://investors.micron.com/news/press-release/2026/Micron-in-High-Volume-Production-of-HBM4-Designed-for-NVIDIA-Vera-Rubin-PCIe-Gen6-SSD-and-SOCAMM2-03-16-2026/default.aspx), 2026-03-16 | HBM4 36 GB 12H는 2026 Q1 volume shipment, >11 Gb/s/pin·>2.8 TB/s/stack. 48 GB 16H는 샘플. 192 GB SOCAMM2는 high-volume production. 속도 근거는 내부 시험·고객 test vehicle이며 공개 workload 실측이 아니다. Vera CPU 최대 2 TB·1.2 TB/s는 CPU 구성 범위다. |
| PF04 | [NVIDIA HGX](https://www.nvidia.com/en-us/data-center/hgx/), 게시일 미표시 | 확인일 현재 제조사는 Vera Rubin 시스템 제조·출하를 설명한다. HGX Rubin NVL8의 2 TB HBM4·130 TB/s는 8-GPU 시스템 수치다. 실제 재고·고객 인수는 미확인이고 GPU당 정확한 값으로 역산하지 않는다. |
| PF05 | [Samsung HBM4E 샘플](https://news.samsung.com/uk/samsung-begins-shipment-of-industry-first-hbm4e-samples), 2026-06-01 | 12-high 48 GB 샘플 출하. 안정 14 Gb/s, 확장 가능 16 Gb/s, 발표 최대 3.6 TB/s/stack은 각각의 주장으로 보존한다. 16 Gb/s를 이용해 4.096 TB/s 제품 사양을 만들지 않는다. 8H 32 GB·16H 64 GB와 양산은 계획이다. |
| PF06 | [Samsung GTC 2026 아키텍처 설명](https://semiconductor.samsung.com/news-events/tech-blog/architecting-the-ai-era-samsung-electronics-and-nvidia-define-the-future-at-gtc-2026/), 본문 게시일 미표시 | HBM5 아키텍처와 1c core die·2 nm base die 계획을 소개한다. 용량·pin rate·버스 폭·BW·전력·출하일을 확정 사양으로 제공한 근거로 쓰지 않는다. 수치 필드는 null이다. |
| PF07 | [Samsung Memory Tech Day 회고](https://semiconductor.samsung.com/news-events/tech-blog/memory-tech-day-memory-in-the-age-of-ai-data/), 2023-12-04 | 2023-10-20 행사 당시 DDR6 9600 Mbps·2028 가용 전망이다. 역사적 로드맵만 보존하며 현재 DDR6 확정 사양 필드는 null이다. |
| PF08 | [JEDEC GDDR7](https://www.businesswire.com/news/home/20240305637931/en/JEDEC-Publishes-GDDR7-Graphics-Memory-Standard), 2024-03-05 | JESD239는 그래픽 메모리 GDDR7이다. 일반 DDR7로 이름을 바꾸지 않는다. 이번 조사에서 DDR7 확정 사양을 확인하지 못한 것은 자료 공백이며 비존재 증명이 아니다. |
| PF09 | [JEDEC LPDDR6](https://www.businesswire.com/news/home/20250709315796/en/JEDEC-Releases-New-LPDDR6-Standard-to-Enhance-Mobile-and-AI-Memory-Performance), 2025-07-09 | JESD209-6: die당 2 sub-channels, 각각 12 DQ, 32-byte 접근 단위와 32/64-byte 접근. 24 DQ 파생값을 유효 payload 버스 폭으로 단정하거나 package BW로 옮기지 않는다. |
| PF10 | [SK hynix LPDDR6 개발 검증](https://news.skhynix.com/en/1c-lpddr6-development-2026/), 2026-03-10 | 16 Gb die 개발·validation, base speed >10.7 Gb/s. 16 Gb는 16 GB package가 아니다. H1 준비·H2 공급은 당시 계획으로 보존한다. |
| PF11 | [Samsung LPDDR6 플랫폼 검증](https://semiconductor.samsung.com/news-events/tech-blog/samsung-lpddr6-advancing-low-power-memory-for-ai-with-industry-first-validation-on-qualcomm-technologies-new-snapdragon-platform/), 본문 날짜 미표시 | 검색 색인은 2026-09-22이나 공식 본문 날짜는 미표시다. 16 GB·최대 10.7 Gb/s를 Snapdragon 8 Elite Extreme Gen 6에서 sampling/validation 완료했다고 설명한다. 114 GB/s는 버스 구성·물리 범위가 충분히 특정되지 않아 정규화한 BW 필드는 null이다. 단말 상용 출하를 주장하지 않는다. |
| PF12 | [Micron 128 GB DDR5 출하](https://investors.micron.com/news/press-release/2024/Micron-First-to-Ship-Critical-Memory-for-AI-Data-Centers-05-01-2024/default.aspx), 2024-05-01 | 32 Gb monolithic die 기반 128 GB RDIMM, 최대 5600 MT/s, 검증·volume shipment. 데이터율은 물리 클럭 또는 socket BW가 아니다. |
| PF13 | [Micron MRDIMM 제품](https://www.micron.com/products/memory/dram-modules/mrdimm), 게시일 미표시 | 32–256 GB·최대 8800 MT/s, 호환 Intel 서버 CPU에서 배치 가능한 포트폴리오라는 설명이다. 모든 속도·용량 조합, 일반 DDR5 슬롯 호환, 재고를 보장하지 않는다. |
| PF14 | [NVIDIA Thor 일반 공급](https://developer.nvidia.com/blog/introducing-nvidia-jetson-thor-the-ultimate-platform-for-physical-ai/), 2025-08-25 | T5000 SOM 128 GB·256-bit LPDDR5X·273 GB/s. T5000 및 개발 키트의 일반 공급 개시. 40–130 W는 전체 SOM 전력 범위다. |
| PF15 | [Micron LPDDR5X SOCAMM2 샘플](https://investors.micron.com/news/press-release/2025/Micron-Delivers-Industrys-Highest-Capacity-SOCAMM2-for-Low-Power-DRAM-in-the-AI-Data-Center-10-22-2025/default.aspx), 2025-10-22 | 192 GB LPDDR5X SOCAMM2, 당시 최대 192 GB·9.6 Gb/s 샘플 포트폴리오. 이후 PF03의 192 GB 양산 상태를 별도 레코드로 둔다. 다른 용량의 비교 각주에서 192 GB bus 폭·W를 가져오지 않는다. |
| PF16 | [JEDEC DDR5 JESD79-5C](https://www.businesswire.com/news/home/20240417886230/en/JEDEC-Updates-JESD79-5C-DDR5-SDRAM-Standard-Elevating-Performance-and-Security-for-Next-Gen-Technologies), 2024-04-17 | DDR5 timing을 8800 Mbps까지 확장하고 PRAC를 도입한 표준 개정이다. 모든 상용 module/controller의 지원 속도가 아니다. |

## 구현에 사용한 경계

HBM4의 표준·부품·시스템을 분리했고 HBM4E 계획 variant도 샘플과 구별했다.
HBM5·DDR6·DDR7의 미검증 사양은 `null`이다. LPDDR6의 표준·die 개발·package/platform
검증을 나눴다. 현재 대안은 DDR5 RDIMM/MRDIMM과 LPDDR5X Thor/SOCAMM2이며 이들의
단위를 그대로 유지한다. HBF/NAND는 사용자 범위에 따라 인접 기술 위치만 표시하며
이 파일의 평가·추천 후보로 넣지 않는다.

직접 JEDEC 표준 사이트는 이번 도구에서 접근 제한으로 열리지 않았다. 이를 우회하지
않았고 JEDEC가 발행한 공개 Business Wire 발표문으로 표준 발표 근거를 확보했다.
HBM4 최신 개정 전문이나 공개되지 않은 사양을 읽었다고 주장하지 않는다. 이 데이터는
제품 가설과 측정 우선순위를 정리하는 입력이며 시장 미충족·고객 채택·실제품 SLO를
입증하는 결과가 아니다.
