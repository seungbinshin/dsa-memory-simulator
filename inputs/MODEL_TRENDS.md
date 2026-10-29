# 공개 근거 보강 메모 — DSA Memory Simulator

확인일: 2026-10-27. 기존 `PUBLIC_SOURCE_NOTES.md`, 저장소 `memory_dsa/catalog.py`, `demo.py`, `integrated.py`, README를 읽고 작성했다. 코드·카탈로그·원 보고서는 수정하지 않았다. 아래는 계산 입력을 정당화하는 공개 1차 근거이며, 특정 메모리 제품 추천이나 미래 시장 예측이 아니다.

## 1. DDR5 기준점을 채울 수 있는 근거

| 공개 근거와 날짜 | 확인한 값 | 계산 입력·제약 |
|---|---|---|
| [Kingston KSM64R52BD4-128MB datasheet](https://www.kingston.com/datasheets/KSM64R52BD4-128MB.pdf), Rev. A, 문서 번호 4811642A, 표기일 `10/08/24` (날짜 순서는 원문 그대로 보존) | 128GB, DDR5-6400, 2Rx4, 16G × 80bit ECC RDIMM, 288pin. 40개의 8G × 4bit 소자. 1.1V는 전압이며 소비전력이 아니다. | `capacity_label="128GB"`, `transfer_rate_mt_s=6400`, `rank_count=2`, `ecc_bus_bits=80`. 16G 주소 깊이를 이진 DRAM 주소 단위로 해석하면 사용자 용량은 `16*2**30*64/8 = 137438953472 B` (128GiB). 이 단위 해석을 명시한 파생값으로 기록하고 128e9와 혼합하지 않는다. 제품 구매 가능성이나 특정 CPU 호환성까지 확인한 것은 아니다. |
| [Kingston DDR5 overview](https://www.kingston.com/en/blog/pc-performance/ddr5-overview), 발행일 미표시, 확인일 위와 같음 | DIMM 사용자 데이터 폭 64bit, 독립 32bit subchannel 두 개. 서버 ECC 포함 시 각 subchannel 40bit. | `payload_width_bits=64`, `subchannels_per_dimm=2`. 호스트의 64bit 채널 기준과 32bit subchannel 기준을 구분한다. ECC 80bit나 rank 수를 payload BW에 곱하지 않는다. |
| [Kingston server memory buying guide](https://www.kingston.com/en/blog/servers-and-data-centers/server-memory-buying-guide), 발행일 미표시 | DDR5-6400 / PC5-51200에 51.2GB/s 표기. CPU와 DIMM 구성에 따라 동작 속도가 낮아질 수 있음. | 이론 peak `6400e6*64/8 = 51.2e9 B/s`. `sustained_bw_bytes_s`, `power_w`, 실제 지연은 계속 `null`. 독립 채널 수와 실제 협상 속도를 받아 합산해야 하며, 같은 채널에 DIMM을 더 꽂았다고 채널 peak를 중복 합산하지 않는다. |

따라서 현재 `ddr5-rdimm`의 전면 공란을 위 **특정 부품의 용량·이론 peak**로 보강할 근거는 있다. 지속 BW·전력이 없는 public 후보의 순위 보류는 유지한다. 큰 DIMM의 용량 증가는 동일 전송률·64bit 버스에서 peak BW 증가와 동의어가 아니다. `capacity_modules = ceil(required_capacity/module_capacity)`와 `bandwidth_modules = ceil(required_bw/sustained_bw)`를 따로 보여 주면 이 tradeoff가 드러난다. sustained 미확인 시 peak로 산출하는 값은 이상적인 최소 자원 하한일 뿐, 실행 가능 판정으로 쓰지 않는다.

## 2. AI 변화 → 계산 가능한 입력

| 기제 | 공개 1차 근거·날짜 | 입력과 계산 범위 |
|---|---|---|
| Dense / MoE의 용량과 활성 접근량 분리 | [DeepSeek-V3 Technical Report v1](https://arxiv.org/html/2412.19437v1), 2024-12-27, §2·§4.2: 전체 671B, 토큰당 활성 37B. | `total_parameters`, `active_parameters_per_token`, `resident_fraction`, `weight_bits`, `weight_metadata_bytes`, `replicas`에서 상주 가중치와 활성 payload를 별도로 산출. MoE의 활성 수치로 전체 상주 용량을 계산하면 안 된다. 실제 DRAM read는 batching·캐시 재사용·expert 배치에 따라 달라져 `active_weight_bytes_per_token`은 논리 접근 가정이다. 원격 expert dispatch/combine 바이트도 별도 입력. Dense 비교는 `active=total`이라는 명시적 단순화로 둔다. |
| GQA / MQA의 KV 감소 | [GQA, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.298/), 2023-12: query head보다 적은 KV head를 공유하는 구조. | `query_heads`와 `kv_heads`를 구분. MHA는 같은 수, MQA는 KV head 하나, GQA는 그 사이. 비압축 KV payload `2*layers*kv_heads*head_dim*bytes_per_element*context*concurrency`. 나머지를 고정할 때 KV head 수에 비례한다. 모델 품질·지연도 같은 비율로 좋아진다는 뜻은 아니다. |
| MLA의 다른 cache 구조 | [DeepSeek-V3 v1](https://arxiv.org/html/2412.19437v1), §2.1.1·§4.2: generation에서 압축 KV latent와 decoupled RoPE key를 보존; 각각 차원 512·64. | 향후 `kv_latent_dim`, `rope_key_dim`, `latent_bytes_per_element`, `rope_bytes_per_element` 필요. 논리 cache/layer/token은 `512*b_latent + 64*b_rope`; 두 dtype을 2B로 **가정**하면 1152B. 별도 K와 V로 다시 두 배 하지 않는다. 구현별 layout·추가 buffer는 별도. 현 구현이 MLA를 거부하는 것은 정직한 경계다. 일반 GQA `kv_heads`나 임의 multiplier로 지원을 가장하지 않는다. |
| 긴 context·동시 세션과 agent 호출의 증가 | 위 GQA 식; [ReAct v3](https://arxiv.org/abs/2210.03629v3), 2023-03-10 (최초 2022-10-06): reasoning·행동·외부 관측을 반복하는 구조. | `context_tokens`, `live_sessions`, `requests_per_task`, `output_tokens_per_request`, `tool_observation_tokens`, `retained_history_tokens`, `parallel_branches`를 시나리오 입력으로 분리. task당 호출 수와 순간 동시성은 같지 않다. `tasks/s * calls/task * output_tokens/call`은 명시한 workload의 aggregate 생성률. 논문은 미래 증가율을 보장하지 않으므로 숫자는 사용자 가정/측정이어야 한다. |
| Prefix / 대화 이력 재사용 | [vLLM Automatic Prefix Caching](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/), 페이지 표기 2026-10-13, rolling 문서 | 공통 prefix의 재계산을 건너뛰는 prefill 효과. `prefix_reuse_ratio`를 prefill에서만 적용하는 현 방향은 타당하다. decode 토큰 생성 시간 감소로 적용하지 않는다. resident 용량 절감까지 계산하려면 shared live block 수·참조 관계·retention/eviction·block 크기가 추가로 필요하다. 단일 cache hit 비율만으로 전체 KV 용량을 줄이지 않는다. |
| KV 저정밀화 | [KIVI v2](https://arxiv.org/html/2402.02750v2), 2024-07-25 (최초 2024-02-05): key는 per-channel, value는 per-token 양자화; full-precision residual cache 유지. 실험 기본 group 32, residual length 128. | `key_bits`, `value_bits`, `group_size`, `scale_zero_point_bytes`, `residual_tokens`, `residual_dtype_bytes`, `padding_bytes`로 packed payload+metadata+residual을 합산. 단순 16→2bit를 전체 메모리 8배 감소로 쓰지 않는다. 현재 `kv_bytes_multiplier`는 overhead가 생략된 시나리오 근사로 표시. 모델별 품질·kernel 지원은 검증 입력이며 논문 성능 배수를 일반화하지 않는다. |
| 가중치 저정밀화 | [AWQ v6](https://arxiv.org/abs/2306.00978v6), 2026-04-25 (최초 2023-06-01): low-bit **weight-only** quantization. | `weight_bits`, group/scale/zero-point overhead, 비양자화 텐서 용량을 받는다. weight precision과 KV precision을 각각 바꿀 수 있어야 한다. 가중치 INT4가 KV·activation·optimizer까지 INT4라는 의미는 아니다. 동작 모델·정확도·kernel에 따라 효율이 다르다. |
| Physical AI / VLA | [OpenVLA v3](https://arxiv.org/abs/2406.09246v3), 2024-09-05 (최초 2024-06-13): 7B VLA, Llama 2와 DINOv2/SigLIP visual encoder 결합. [공식 config](https://huggingface.co/openvla/openvla-7b/blob/main/config.json), 확인 2026-10-27, 페이지 표시 revision `cf0c8cb`: `image_sizes=[224,224]`. | 모델 입력 크기 사례를 제시할 수 있다. 두 값은 두 vision backbone의 크기이며 카메라 두 대라는 뜻이 아니다. `camera_count,width,height,channels,bytes_per_component,frame_rate,history_frames,intermediate_state_bytes,action_rate`를 명시한다. 224×224 RGB8 프레임 하나는 파생값 150528B; **가정한** 30fps는 4515840B/s의 원시 입력 payload. full sensor readout·encoder 중간 tensor·가중치 traffic·action latency는 이 값에 포함되지 않는다. |

## 3. 현 구현에 연결할 최소 보강과 검증

1. **증가와 감소를 함께 제시:** 미래 scenario에는 context·live concurrency·모델 상주량·생성률 증가와 GQA/MLA·KV/weight precision·prefix reuse의 효율 개선을 독립 축으로 둔다. 예를 들어 context 4배 × concurrency 2배 × KV head 1/4 × KV bytes 1/2는 논리 KV 용량 1배다. 이는 산술 감도 예시이며 예측이 아니다. agent의 순차 호출 수를 concurrency에 다시 곱해 중복 계산하지 않는다.
2. **현재 함수와 맞추기:** 현 workload의 `resident_weight_bytes`, `active_weight_bytes_per_token`, `expert_fabric_bytes_per_token`, `prefix_reuse_ratio`와 phase_budget의 `frame_bytes`, `frames_per_s`는 위 입력의 도착점이 될 수 있다. 상위 입력 → 이 바이트 입력으로 변환하는 명시적 worksheet/preset과 provenance가 있으면 설명 가능한 demo가 된다. 아직 지원하지 않는 MLA는 unsupported로 남겨도 된다.
3. **검증할 불변식:** 고정 조건에서 context/concurrency/KV heads에 대한 선형성; MoE active 변경만으로 상주 용량이 줄지 않음; prefix hit 변경이 decode 용량·BW를 자동 감소시키지 않음; quantization metadata/residual이 음수·누락되지 않음; weight/KV precision 독립; camera 수·fps가 입력 traffic에 선형 반영; ECC/rank를 DDR5 payload BW에 중복 적용하지 않음.
4. **추천에 필요한 미확인값:** 지속 BW의 read/write mix·접근 크기·queue depth·NUMA, memory/path latency, fabric overhead, 부하별 전력, 공급/폼팩터/패키징 제약. 공개 peak와 논리 traffic만으로 SLO·실측 성능·최적 메모리를 확정하지 않는다. 불확실성 범위와 미입력 목록을 출력한다.

HBM5 비공개 값, DDR7 미확인 값은 계속 `null`; HBF/NAND는 위치 설명만 하고 추천 후보에서 제외한다. 공개자료의 빈칸을 임의의 사내 수치로 채우지 않는다.

접근 상태: 공식 OpenVLA `main/config.json`은 읽었으나 commit 전체 해시 URL 조회는 web 도구의 `not accessible` 결과였다. 우회·재시도하지 않았으며 위 문서는 읽힌 main 페이지와 표시 revision만 근거로 쓴다. 그 외 이 메모 작성의 차단 없음. 사내 자료·원 보고서 본문·자격증명은 포함하지 않았다.

