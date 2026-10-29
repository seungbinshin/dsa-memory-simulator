# 제품 방향 판단을 위한 공개 근거 — 2026-10-29

이 문서는 원문을 복제하지 않은 사실·계산 경계의 요약이다. 공개 플랫폼의 메모리 사양, 모델 구조, 공급사 실행 사례를 연결한다. 미래 시장 규모·판매 전망·사내 실측을 확보한 것이 아니다. 기존 `PUBLIC_SOURCE_NOTES.md`의 HBM4/4E/5·DDR6/7·LPDDR6 자료와 이번 소수 플랫폼 사례의 조사 범위를 혼동하지 않는다.

| 근거 | 공개 사실 | 해석 경계 |
|---|---|---|
| [Meta Llama 3.1 70B 모델 카드](https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct), 공개 2024-07-23 | 70B 계열, 128k context, GQA | 실제 고객의 context 분포·동시성·도입 규모를 제공하지 않는다. |
| [Meta 논문 v3 Table 3](https://arxiv.org/html/2407.21783v3), v3 2024-11-23 | 70B 구조: layers 80, hidden dimension 8192, attention heads 64, KV heads 8 | head dimension 128은 8192/64의 파생값. KV 저장 형식과 운영 동시성은 별도 가정. |
| [H100 사양](https://www.nvidia.com/en-us/data-center/h100/), 확인 2026-10-29 | SXM 한 GPU: 80 GB, 3.35 TB/s, 최대 700 W | nominal capacity, vendor peak BW, GPU 전체 TDP. usable 용량·지속 BW·DRAM 소비전력으로 바꾸지 않는다. |
| [H200 데이터시트 p.4](https://dam-cdn.nvd.orangelogic.com/AssetLink/5o2qgy5d2835ve2pm11i62kv8mphqta8.pdf), 확인 2026-10-29 | SXM 한 GPU: 141 GB HBM3e, 4.8 TB/s, 최대 700 W | 같은 구분 적용. [제품 페이지](https://www.nvidia.com/en-us/data-center/h200/)는 preliminary specification 문구도 유지한다. |
| [HGX reference architecture Table 1](https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html), 확인 2026-10-29 | B300 SXM 한 GPU: 288 GB HBM3e, 최대 8 TB/s | per-GPU 직접 표기 사용. [DGX B300](https://www.nvidia.com/en-us/data-center/dgx-b300/)는 출하 중으로 표시하므로 H200만 보고 제품 공백을 주장할 수 없다. |
| [NVIDIA 메모리 공유 설명](https://developer.nvidia.com/blog/accelerate-large-scale-llm-inference-and-kv-cache-offload-with-cpu-gpu-memory-sharing/), 2025-09-05 | FP16 Llama 70B weights 약 140 GB, CPU/GPU 메모리 공유 예시 | offload는 이미 존재하는 대안. 900 GB/s C2C 표기를 단방향 실효 BW로 쓰거나 HBM BW에 합산하지 않는다. |
| [Jetson Thor 기술 문서 Table 1](https://developer.nvidia.com/blog/introducing-nvidia-jetson-thor-the-ultimate-platform-for-physical-ai/), 2025-08-25 | T5000 한 SOM: 128 GB, 256-bit LPDDR5X, 273 GB/s, 40–130 W | SOM 전체 전력 범위이며 LPDDR 전력이 아니다. BW는 공급 측 사양이다. |
| [GR00T 1.7 on Thor](https://www.jetson-ai-lab.com/tutorials/groot_n17_on_thor/), 게시일 미표시·확인 2026-10-29 | TensorRT BF16 약 81 ms, mixed NVFP4 약 40 ms median | JetPack 7.2/MAXN/libero_10, denoising 4, camera 1, batch 1, warmup 5 후 20회 median. 공급사 사례이며 우리의 실측 또는 p99 결과가 아니다. |

B300의 DGX 마케팅 총량 2.1 TB와 [사용자 가이드](https://docs.nvidia.com/dgx/dgxb300-user-guide/introduction-to-dgxb300.html)의 8×288 GB/2.3 TB 표기는 일치하지 않는다. 이번 비교는 직접 명시된 per-GPU 288 GB nominal을 사용한다. 차이의 원인·예약률·usable capacity를 추정하지 않는다.

## 계산으로 연결할 수 있는 범위

- 131072 tokens, KV 2 bytes, 압축·공유·eviction 없는 Llama 70B 구조에서는 `2×80×8×128×2×131072` = **40 GiB KV/세션**. 70B×2 bytes ≈ 140 decimal GB weights는 근사 payload다. activation·allocator·quantization metadata·실행 여유는 별도 측정이 필요하다.
- 1/2/4개 독립 세션과 20 generated tokens/s/session는 **선택한 운영 가정**이다. 실제 시장 수요의 빈도나 미래 연도를 예측하지 않는다. full KV scan, 배치 step마다 weights 한 번 읽기를 가정한 논리 traffic을 계산하며 실효 DRAM BW와 구분한다.
- 제품 nominal capacity보다 payload가 크면 명시한 단일 장치 상주 구성을 배제할 수 있다. nominal/peak 아래라는 이유만으로 실행 가능·SLO 충족을 판정하지 않는다. B300 같은 기존 대안, 정밀도 조정, 멀티 GPU, 계층화를 먼저 비교한다.
- Thor의 단일 VLA 실행은 이미 공개되었다. 더 많은 camera·동시 VLM·긴 이력의 추가 용량/BW는 미확인이다. `p99 ≤40 ms`를 선택하면 새 설계 목표로 표시하며 기존 median 사례가 이를 만족했다고 쓰지 않는다.

## 아직 입증되지 않은 것

두 사례는 전체 시장의 대표 표본이 아니다. 경쟁 제품 전체, 고객의 지불 의사, 실제 SLO·품질 조건, 배치/전력/가격 제약을 조사하지 않았으므로 검증된 미충족 시장이나 확정 개발 우선순위를 주장하지 않는다. 조건부 제품 가설을 채택·기각할 내부 측정 항목을 제시하는 것이 이번 보완의 범위다. 비공개 HBM5 등은 null, HBF/NAND는 포지셔닝만 유지한다.
