"""Evidence-linked product questions, separate from synthetic regression fixtures.

This module evaluates declared workload budgets against public nominal envelopes.
It does not infer sustained performance, confidential specifications, market size,
or all-market unmet demand. Output is deterministic and has no I/O.
"""
from copy import deepcopy
import math


CHECKED_AT = '2026-10-29'
MARKET_UNKNOWN = 'unserved_market_not_established'


def quantity(value=None, *, unit, scope, kind='unknown', sources=(), note='', minimum=None, maximum=None):
    """Keep a quantity's evidence and physical/statistical scope beside its value."""
    for number in (value, minimum, maximum):
        if number is not None and (isinstance(number, bool) or not isinstance(number, (int, float))
                                   or not math.isfinite(number) or number < 0):
            raise ValueError('Quantities must be finite nonnegative numbers or null')
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError('Range minimum exceeds maximum')
    return dict(value=value, min=minimum, max=maximum, unit=unit, scope=scope,
                kind=kind, sources=list(sources), note=note)


def source_registry():
    rows = [
        ('P01', 'Meta Llama 3.1 70B model card', 'https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct', '2024-07-23',
         '70B is a model-size label; 128k context and GQA are model facts, not a deployment concurrency forecast.'),
        ('P02', 'The Llama 3 Herd of Models, Table 3', 'https://arxiv.org/html/2407.21783v3', '2024-11-23 (v3; first version 2024-07-31)',
         'Architecture: 80 layers, dimension 8192, 64 attention heads, 8 KV heads. Derived head dimension is 128.'),
        ('P03', 'NVIDIA H100 specifications', 'https://www.nvidia.com/en-us/data-center/h100/', None,
         'SXM variant only. Public memory bandwidth is a nominal peak; GPU TDP is not DRAM power.'),
        ('P04', 'NVIDIA H200 specifications', 'https://www.nvidia.com/en-us/data-center/h200/', None,
         'SXM variant only. Published values retain vendor qualification; no measured usable capacity or sustained bandwidth is supplied.'),
        ('P05', 'NVIDIA CPU/GPU memory sharing and KV offload', 'https://developer.nvidia.com/blog/accelerate-large-scale-llm-inference-and-kv-cache-offload-with-cpu-gpu-memory-sharing/', '2025-09-05',
         'Llama 70B FP16 weights are approximately 140 GB. CPU/GPU memory sharing is an existing alternative, not proof of its SLO for this workload.'),
        ('P06', 'NVIDIA Jetson Thor platform, Table 1', 'https://developer.nvidia.com/blog/introducing-nvidia-jetson-thor-the-ultimate-platform-for-physical-ai/', '2025-08-25',
         'Jetson T5000 SOM: 128 GB, 256-bit LPDDR5X, 273 GB/s; 40–130 W refers to the SOM, not memory.'),
        ('P07', 'NVIDIA Jetson AI Lab: GR00T 1.7 on Thor', 'https://www.jetson-ai-lab.com/tutorials/groot_n17_on_thor/', None,
         'Vendor benchmark medians, not our measurements or p99. Specific software, batch, camera and denoising conditions apply.'),
        ('P08', 'NVIDIA HGX AI Factory components, Table 1', 'https://docs.nvidia.com/enterprise-reference-architectures/hgx-ai-factory/latest/components.html', None,
         'Direct per-GPU B300 SXM values: 288 GB HBM3e, up to 8 TB/s. Do not divide rounded rack/system memory totals to recreate this value.'),
        ('P09', 'NVIDIA DGX B300 availability', 'https://www.nvidia.com/en-us/data-center/dgx-b300/', None,
         'Current shipping-system context; aggregate memory totals are not used as per-GPU measurements.'),
    ]
    return [dict(id=i, title=t, url=u, published=p, checked_at=CHECKED_AT, caveat=c)
            for i, t, u, p, c in rows]


def _product(identifier, label, scope, family, capacity, peak, source, power=None, power_range=None):
    qscope = 'one GPU attached memory' if scope == 'single_gpu' else 'one SOM unified memory'
    result = dict(id=identifier, label=label, scope=scope, memory_family=family,
                  capacity=quantity(capacity, unit='B', scope=qscope, kind='public_nominal', sources=[source],
                                    note='Vendor capacity label normalized as decimal GB; not measured allocatable capacity. No runtime reserve is inferred.'),
                  peak_bw=quantity(peak, unit='B/s', scope=qscope, kind='public_peak', sources=[source],
                                   note='Vendor peak envelope. Not sustained bandwidth or a measured application result.'),
                  usable_capacity=quantity(unit='B', scope=qscope, note='Runtime allocatable capacity under this workload is not measured.'),
                  sustained_bw=quantity(unit='B/s', scope=qscope, note='Access-pattern-specific sustained bandwidth is not available.'),
                  memory_power=quantity(unit='W', scope='DRAM only', note='Device/SOM TDP cannot populate memory power.'),
                  p99=quantity(unit='ms', scope='application end-to-end p99', note='No matched-workload p99 measurement.'))
    if power_range:
        result['device_power'] = quantity(unit='W', scope='whole SOM configured operating range',
                                         kind='public_nominal', sources=[source], minimum=power_range[0], maximum=power_range[1],
                                         note='Whole SOM operating modes; not DRAM power, achieved application power or a target.')
    else:
        result['device_power'] = quantity(power, unit='W', scope='whole GPU maximum TDP',
                                         kind='public_nominal' if power is not None else 'unknown',
                                         sources=[source] if power is not None else [],
                                         note='Not memory power, wall power or a measured workload draw.')
    return result


def product_profiles():
    return [
        _product('h100-sxm', 'H100 SXM · 80 GB', 'single_gpu', 'HBM3', 80e9, 3.35e12, 'P03', 700),
        _product('h200-sxm', 'H200 SXM · 141 GB', 'single_gpu', 'HBM3e', 141e9, 4.8e12, 'P04', 700),
        _product('b300-sxm', 'B300 SXM · 288 GB', 'single_gpu', 'HBM3e', 288e9, 8e12, 'P08'),
        _product('jetson-thor', 'Jetson T5000 · 128 GB', 'single_som', 'LPDDR5X', 128e9, 273e9, 'P06', power_range=(40, 130)),
    ]


def make_llm_case(identifier, label, *, sessions=1, context_tokens=131072,
                  weight_bytes=2, kv_bytes=2, tokens_per_s=20, kind='operating_assumption'):
    """Llama-3.1-70B-shaped payload model, not automatic hardware inference.

    Nominal parameter count is approximate. KV payload follows public dimensions.
    The traffic model assumes one full KV scan per emitted token and one weight
    read per synchronized batch step. Neither reuse nor physical bus traffic is
    measured here. Context beyond the public supported length is rejected.
    """
    for name, v in [('sessions', sessions), ('context_tokens', context_tokens)]:
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise ValueError(name + ' must be a positive integer')
    if context_tokens > 131072:
        raise ValueError('Context exceeds the public model limit; no automatic extrapolation')
    for name, v in [('weight_bytes', weight_bytes), ('kv_bytes', kv_bytes), ('tokens_per_s', tokens_per_s)]:
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
            raise ValueError(name + ' must be finite and positive')
    weights = 70e9 * weight_bytes
    kv_per_session = 2 * 80 * 8 * 128 * kv_bytes * context_tokens
    kv = kv_per_session * sessions
    payload = weights + kv
    traffic = (weights + kv) * tokens_per_s
    assumptions = [
        f'문맥 {context_tokens} tokens와 동시 독립 세션 {sessions}개는 명시한 운영 조건이다. 동시성은 시장 성장률이 아니다.',
        '가중치는 nominal 70B × bytes/parameter 근사. KV는 공개 구조로 계산하며 압축·공유·eviction을 적용하지 않는다.',
        'activation, allocator, quantization metadata, 커널 workspace와 여유 용량은 미포함이다. 실제 필요 용량은 별도 측정한다.',
        f'세션마다 초당 {tokens_per_s:g} tokens라는 설계 가정. 동기화된 batch step마다 가중치를 한 번 읽고 각 KV를 한 번 스캔하는 논리 트래픽이다.',
        '이 트래픽을 버스 실측 또는 지속 BW로 취급하지 않는다. 캐시·batch scheduling·attention kernel에 따라 달라진다.',
    ]
    if weight_bytes != 2 or kv_bytes != 2:
        assumptions.append('저정밀도는 비교 대안이다. 이 설정의 품질·커널 지원·실제 저장량·metadata 비용은 검증하지 않았다.')
    return dict(id=identifier, label=label, scope='single_gpu', kind=kind, phase='decode',
                evidence_ids=['P01', 'P02', 'P05'], assumptions=assumptions,
                parameters=dict(nominal_parameters=70e9, layers=80, kv_heads=8, head_dim=128,
                                context_tokens=context_tokens, sessions=sessions, weight_bytes=weight_bytes,
                                kv_bytes=kv_bytes, tokens_per_s_per_session=tokens_per_s,
                                weight_reads_per_batch_step=1, full_kv_reads_per_token=1,
                                runtime_overhead_bytes=None, quantization_metadata_bytes=None),
                demand=dict(
                    weights=quantity(weights, unit='B', scope='one GPU resident weight payload', kind='derived_approximate', sources=['P01', 'P05'],
                                     note='70B nominal parameters × declared bytes. Approximate, excludes metadata.'),
                    kv=quantity(kv, unit='B', scope='one GPU uncompressed resident KV payload', kind='derived_conditional', sources=['P01', 'P02'],
                                note='2 × 80 layers × 8 KV heads × 128 head dimension × KV bytes × context × sessions.'),
                    capacity=quantity(payload, unit='B', scope='one GPU weight + KV payload budget', kind='derived_approximate', sources=['P01', 'P02', 'P05'],
                                      note='Approximate weight + exact declared KV payload; runtime reserve is additional and unknown. Not total measured memory.'),
                    logical_bw=quantity(traffic, unit='B/s', scope='one GPU conditional weight + KV read payload/s', kind='derived_conditional', sources=['P01', 'P02', 'P05'],
                                        note='(weight bytes once per synchronized batch step + all sessions KV bytes) × tokens/s/session. Logical model, not sustained bus demand.')),
                latency_target=quantity(1000/tokens_per_s, unit='ms', scope='target generated-token interval per session',
                                        kind='design_assumption', note='Inverse of selected tokens/s; not measured ITL, p99 or TTFT.'),
                market_status=MARKET_UNKNOWN)


def _physical_cases():
    unknowns = dict(
        capacity=quantity(unit='B', scope='one SOM application resident set', note='No measured peak resident set; model checkpoint size is not runtime capacity.'),
        kv=quantity(unit='B', scope='one SOM application KV state', note='Do not apply the Llama GQA formula to this VLA architecture.'),
        weights=quantity(unit='B', scope='one SOM model/runtime weights', note='Mixed precision engine/runtime footprint not established.'),
        logical_bw=quantity(unit='B/s', scope='one SOM application memory traffic', note='No directly measured traffic; latency cannot be inverted to infer DRAM bandwidth.'))
    baseline = dict(id='physical-baseline', label='GR00T 1.7 · 공개 단일 VLA 기준점', scope='single_som', kind='vendor_benchmark', phase='physical_ai',
                    evidence_ids=['P06', 'P07'], assumptions=['공개 벤치마크의 조건으로 한정한다. 모델 실행 가능성은 이 조건에서 vendor가 보였으며 우리 실측이 아니다.'],
                    parameters=dict(cameras=1, batch=1, denoising_steps=4, simultaneous_extra_vlm=False,
                                    software='JetPack 7.2', power_mode='MAXN', model='GR00T-N1.7-LIBERO/libero_10'),
                    demand=deepcopy(unknowns), latency_target=quantity(unit='ms', scope='application p99 target', note='Baseline has a median result, not a p99 target.'),
                    market_status='vendor_supported_baseline')
    future = dict(id='physical-concurrent', label='4 camera + VLA/VLM 동시 실행 · 검증 가설', scope='single_som', kind='operating_assumption', phase='physical_ai',
                  evidence_ids=['P06', 'P07'],
                  assumptions=['카메라 1→4개와 VLA/VLM 동시 실행은 미래 운영 가정이며 공개 수요량 예측이 아니다.',
                               '카메라 수에 비례해 메모리 용량·BW·지연을 자동 배수 계산하지 않는다.',
                               'p99 ≤ 40 ms는 선택한 새 설계 목표이다. 공개 median 약 40 ms가 이를 입증하지 않는다.'],
                  parameters=dict(cameras=4, simultaneous_extra_vlm=True, resident_bytes=None, memory_traffic_bytes_s=None),
                  demand=deepcopy(unknowns), latency_target=quantity(40, unit='ms', scope='application end-to-end p99', kind='design_assumption',
                                                                 note='Proposed 25 Hz service deadline under concurrent load, not a measured result.'),
                  market_status=MARKET_UNKNOWN)
    return [baseline, future]


def _value(q):
    value = q.get('value')
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
        raise ValueError('Invalid quantity value')
    return value


def assess_case(case, product):
    """Assess axis bounds without upgrading them into performance/market claims."""
    result = dict(id=case['id'] + '__' + product['id'], case_id=case['id'], product_id=product['id'],
                  capacity_status='unknown', bw_status='unknown', overall_status='performance_unverified',
                  capacity_shortfall_bytes=None, bw_peak_shortfall_bytes_s=None,
                  evidence_ids=sorted(set(case['evidence_ids'] + product['capacity']['sources'] + product['peak_bw']['sources'])),
                  market_status=MARKET_UNKNOWN, reasons=[])
    if case['scope'] != product['scope']:
        result.update(capacity_status='not_comparable', bw_status='not_comparable', overall_status='not_comparable')
        result['reasons'] = ['서버 GPU와 embedded SOM은 배치 단위가 달라 직접 대체 비교하지 않는다.']
        return result
    if case['scope'] not in ('single_gpu', 'single_som'):
        raise ValueError('Unsupported deployment scope')
    gpu = case['scope'] == 'single_gpu'
    expected = [(case['demand']['capacity'], 'B', 'one GPU weight + KV payload budget' if gpu else 'one SOM application resident set'),
                (case['demand']['logical_bw'], 'B/s', 'one GPU conditional weight + KV read payload/s' if gpu else 'one SOM application memory traffic'),
                (product['capacity'], 'B', 'one GPU attached memory' if gpu else 'one SOM unified memory'),
                (product['peak_bw'], 'B/s', 'one GPU attached memory' if gpu else 'one SOM unified memory')]
    for q, unit, scope in expected:
        if q.get('unit') != unit or q.get('scope') != scope:
            raise ValueError('Quantity unit or memory path scope is incompatible')
    cap, cap_limit = _value(case['demand']['capacity']), _value(product['capacity'])
    bw, peak = _value(case['demand']['logical_bw']), _value(product['peak_bw'])
    if cap is not None and cap_limit is not None:
        binary_label_alternative = cap_limit / 10**9 * 2**30
        result['capacity_unit_sensitivity'] = dict(
            decimal_normalization_bytes=cap_limit, binary_label_alternative_bytes=binary_label_alternative,
            exceeds_both_label_interpretations=cap > max(cap_limit, binary_label_alternative),
            note='A sensitivity to vendor GB label interpretation only; neither interpretation establishes usable capacity.')
        result['capacity_shortfall_bytes'] = max(0, cap - cap_limit)
        result['capacity_status'] = 'conditional_shortfall' if cap > cap_limit else 'within_nominal_only'
        result['reasons'].append('선택한 payload 예산이 nominal 용량을 초과한다; 해당 단일 장치/정밀도/상주 조건의 부족이다.' if cap > cap_limit
                                 else 'payload는 nominal 용량 안에 있으나 usable 여유·runtime overhead를 몰라 실행 가능 판정은 보류한다.')
    else:
        result['reasons'].append('상주 수요 또는 사용 가능한 공급 근거가 없어 용량 판정을 보류한다.')
    if bw is not None and peak is not None:
        result['bw_peak_shortfall_bytes_s'] = max(0, bw - peak)
        result['bw_status'] = 'conditional_peak_exceeded' if bw > peak else 'below_peak_only'
        result['reasons'].append('선택한 full-read 트래픽 모델이 vendor peak를 넘는다. 모델 가정이 성립할 때의 경계이며 실측 실패가 아니다.' if bw > peak
                                 else '논리 트래픽은 vendor peak 아래지만 지속 BW·캐시·경합·SLO는 검증되지 않았다.')
    else:
        result['reasons'].append('수요 트래픽 또는 지속 성능이 미확인이다. 공급 peak만으로 수요를 채우지 않는다.')
    if result['capacity_status'] == 'conditional_shortfall' or result['bw_status'] == 'conditional_peak_exceeded':
        result['overall_status'] = 'conditional_configuration_excluded'
    matched_parameters = dict(cameras=1, batch=1, denoising_steps=4, simultaneous_extra_vlm=False,
                              software='JetPack 7.2', power_mode='MAXN', model='GR00T-N1.7-LIBERO/libero_10')
    benchmark_matches = (case['kind'] == 'vendor_benchmark' and 'P07' in case['evidence_ids']
                         and all(case['parameters'].get(k) == v for k, v in matched_parameters.items()))
    if case['id'] == 'physical-baseline' and product['id'] == 'jetson-thor' and benchmark_matches:
        result['overall_status'] = 'vendor_baseline_demonstrated'
        result['market_status'] = 'vendor_supported_baseline'
        result['reasons'].append('해당 camera/batch/software 조건의 vendor median 실행 사례가 있다. 미래 동시 부하와 p99를 인증하지 않는다.')
    return result


def _benchmarks():
    conditions = dict(hardware='Jetson AGX Thor Developer Kit', software='JetPack 7.2', power_mode='MAXN',
                      model='GR00T-N1.7-LIBERO/libero_10', denoising_steps=4, cameras=1, batch=1,
                      warmup_iterations=5, measured_iterations=20, statistic='median')
    return [dict(id=i, case_id='physical-baseline', product_id='jetson-thor', label=label,
                 median_latency_ms=ms, frequency_hz=hz, conditions=deepcopy(conditions), source_ids=['P07'],
                 p99_latency_ms=None, measured_by='vendor', note='Rounded published median, not our hardware experiment.')
            for i, label, ms, hz in [('thor-bf16', 'TensorRT BF16', 81, 12.3),
                                    ('thor-nvfp4', 'TensorRT mixed NVFP4 + graph optimization', 40, 25.1)]]


def _directions(cases, assessments):
    llm = [c for c in cases if c['id'] in ('llm-bf16-1', 'llm-bf16-2', 'llm-bf16-4')]
    capacity = [c['demand']['capacity']['value'] for c in llm]
    bw = [c['demand']['logical_bw']['value'] for c in llm]
    first_cases = [c['id'] for c in cases if c['scope'] == 'single_gpu']
    second_cases = ['physical-baseline', 'physical-concurrent']
    return [dict(
        id='long-context-capacity', title='장문 동시 서비스: 기존 고용량 GPU·정밀도 대안부터 검증',
        decision='조건부 개발 가설 — B300과 소프트웨어 대안으로 목표가 충족되지 않을 때 추가 usable 용량/계층화 검토',
        case_ids=first_cases, assessment_ids=[a['id'] for a in assessments if a['case_id'] in first_cases and a['product_id'] in ('h200-sxm', 'b300-sxm')],
        evidence_ids=['P01', 'P02', 'P04', 'P05', 'P08', 'P09'],
        targets=dict(
            capacity=quantity(unit='B', scope='one serving GPU resident weight + KV payload; measured runtime margin additional',
                              kind='conditional_target_range', sources=['P01', 'P02', 'P05'], minimum=min(capacity), maximum=max(capacity),
                              note='Approximate 1–4 independent 128 Ki context BF16 sessions, 70B weights. Scenario range, not product roadmap or confidence interval.'),
            bw=quantity(unit='B/s', scope='conditional full-read logical payload/s for one GPU', kind='conditional_target_range',
                        sources=['P01', 'P02', 'P05'], minimum=min(bw), maximum=max(bw),
                        note='20 tokens/s/session with one weight read per synchronized batch step. Not a sustained-DRAM specification; profile physical traffic before setting one.'),
            memory_power=quantity(unit='W', scope='DRAM-only product target', note='Unknown. Existing GPU TDP cannot set this field.'),
            latency=quantity(50, unit='ms', scope='per-session target generated-token interval', kind='design_assumption',
                             note='20 tokens/s operating target; no p99, TTFT or achieved ITL claim.'),
            p99=quantity(unit='ms', scope='application tail-latency target', note='Customer SLO and matched workload measurement are still needed.')),
        why='공개 128k/GQA 구조는 KV 크기를 계산하게 한다. 독립 세션 증가가 resident 용량을 키우지만, 그 운영 조건의 실제 채택 규모는 확인하지 않았다.',
        existing_fit='B300 288 GB는 1·2 세션 payload를 nominal 용량 내에 담는다. 4세션 BF16 payload 약 312 GB는 이를 넘는다. 저정밀도 2세션은 H200 nominal 용량 안으로 내려오므로 기존 제품을 배제할 수 없다.',
        alternatives=['B300 등 현재 고용량 GPU를 먼저 비교하고 usable capacity와 목표 SLO를 측정한다.',
                      '가중치/KV 정밀도, 문맥·동시성 제한, prefix 공유·eviction을 품질 조건과 함께 검토한다.',
                      '멀티 GPU와 CPU DRAM/LPDDR 계층화를 비교한다. 활성 KV를 느린 tier로 옮기면 migration/read 경로가 새 병목이 될 수 있다.'],
        disconfirming_conditions=['현재 GPU 또는 압축·스케줄링으로 품질·SLO·비용을 충족하면 신규 용량 제품의 우선순위를 낮춘다.',
                                 '실제 context·동시성 분포가 4세션×128 Ki보다 작거나 KV 공유율이 높으면 제시한 용량 목표를 낮춘다.',
                                 'BW 또는 compute/fabric이 지배 병목이면 용량 확대만의 효과를 주장하지 않는다.'],
        internal_validation=['고객 workload의 context/동시성/입출력 길이 분포와 서비스 빈도',
                             '정밀도별 정확도·KV hotness·공유율·실제 allocator/activation/workspace 여유',
                             '현재 B300/H200의 usable memory, 실제 DRAM read/write·지속 BW, ITL·TTFT·p99',
                             'tier 이동량·방향·fabric 경합, DRAM 전력, 전체 랙 전력·PSU·비용을 분리한 비교']),
        dict(
        id='edge-qos-first', title='Physical AI: LPDDR 용량 신제품보다 경합·지연·효율 검증 우선',
        decision='측정 우선 — 공개 단일 VLA는 이미 실행된다. 동시 부하의 p99 문제가 확인될 때 메모리 QoS/BW 방향을 구체화',
        case_ids=second_cases, assessment_ids=[a['id'] for a in assessments if a['case_id'] in second_cases and a['product_id'] == 'jetson-thor'],
        evidence_ids=['P06', 'P07'],
        targets=dict(
            capacity=quantity(unit='B', scope='one SOM concurrent application peak resident set', note='Need peak-resident measurement; do not reuse 128 GB supply as a demand target.'),
            bw=quantity(unit='B/s', scope='one SOM sustained memory traffic under concurrent applications', note='Need traffic measurement; do not derive demand by multiplying camera count or copying 273 GB/s peak.'),
            memory_power=quantity(unit='W', scope='LPDDR-only target', note='Unknown; 40–130 W is whole SOM operating range.'),
            latency=quantity(40, unit='ms', scope='proposed concurrent application deadline', kind='design_assumption', note='25 Hz service design choice; not the published median statistic.'),
            p99=quantity(40, unit='ms', scope='application end-to-end p99 under concurrent VLA/VLM/camera load', kind='design_assumption',
                         note='New target to test. The vendor reports a median over 20 iterations, which cannot establish p99.')),
        why='공개 Thor 사례는 혼합 정밀도와 graph 최적화로 단일 VLA가 약 25 Hz median으로 실행됨을 보인다. 미충족 시장 또는 용량 부족의 증거로 뒤집을 수 없다.',
        existing_fit='JetPack 7.2/MAXN, 1 camera, batch 1, denoising 4회 조건의 공개 실행 기준점이 있다. 4 camera와 VLA/VLM 동시 실행은 별도 검증 가설이다.',
        alternatives=['정밀도와 graph 최적화, KV 재사용, 스케줄링·서비스 격리를 기존 플랫폼에서 먼저 시험한다.',
                      '카메라 주기·해상도·VLM 호출 빈도를 제어하고 품질/제어 안정성을 함께 비교한다.'],
        disconfirming_conditions=['기존 Thor와 소프트웨어 최적화로 concurrent p99·작업 성공률·전력을 충족하면 새 메모리 제품 근거가 약하다.',
                                 '병목이 compute·camera pipeline·scheduler이면 LPDDR BW 확대를 우선 처방하지 않는다.',
                                 '실제 서비스가 동시 VLM이나 4개 camera를 요구하지 않으면 이 미래 조건의 우선순위를 낮춘다.'],
        internal_validation=['동시 부하별 resident peak와 실제 DRAM traffic·access pattern',
                             '충분한 표본의 end-to-end p99/p999 및 제어 주기 위반률',
                             '장시간 온도/throttling·LPDDR 전력과 SOM 전력을 분리한 측정',
                             '정밀도·스케줄링 변경 전후 작업 성공률 및 품질'])]


def _requirement_trace():
    """Every original axis has a trace, including an honest unassessed verdict."""
    rows = []
    for family, reason in [
        ('HBM4', '공개 stack 용량·이론 peak는 원본 explorer에 있다. 이 workload에 맞춘 qualified platform/지속 BW 역량은 미평가.'),
        ('HBM4E', '공개 sample 사실은 유지한다. 샘플 수치를 application capability frontier로 승격하지 않는다.'),
        ('HBM5', '미공개 사양은 null. 근거 부족을 제품 성능 부족이나 시장 공백으로 표시하지 않는다.'),
        ('DDR6', '역사적 roadmap을 양산 사양이나 workload 역량으로 사용하지 않는다.'),
        ('DDR7', '확인되지 않은 사양은 null이며 미래 제품 목표에서 실제 사양을 역산하지 않는다.'),
        ('LPDDR6', 'LPDDR5X Thor 벤치마크를 LPDDR6 실측처럼 이전하지 않는다. 전기적 조합 예와 application qualification은 별개.')]:
        rows.append(dict(id=family, status='not_evaluated', reason=reason,
                         evidence_paths=['inputs/PUBLIC_SOURCE_NOTES.md', 'memory_dsa/catalog.py:public_catalog'],
                         input_paths=['catalog[].fields', 'candidates[].sustained_bw_bytes_s', 'candidates[].power_w'],
                         output_paths=['results.json:catalog', 'results.json:decision_study.coverage'],
                         screen_paths=['index.html#coverage'],
                         verification='Existing catalog/null/exclusion regressions; no matched workload product-strategy evidence is claimed.',
                         strategy_status='제품전략 미평가 — 공란 또는 조건부 조합만 유지'))
    rows.extend([
        dict(id='decode', status='conditional_case_assessed', reason='Llama 3.1 70B 장문 1/2/4세션과 저정밀도 대안을 현재 단일 GPU envelope에 비교한다.',
             evidence_paths=['P01', 'P02', 'P03', 'P04', 'P05', 'P08', 'P09'],
             input_paths=['strategy.json:cases[llm-*].parameters', 'strategy.json:products[*]'],
             output_paths=['strategy.json:assessments', 'strategy.json:directions[long-context-capacity]'],
             screen_paths=['strategy.html'], verification='test_public_architecture_kv_and_payload_are_distinct; test_current_b300_refutes_blanket_new_capacity_claim',
             strategy_status='조건부 방향 제시 — 상용 서비스 실측/시장 규모 미확인'),
        dict(id='training', status='not_evaluated', reason='기존 weights/activation/optimizer 및 bytes/step 계산은 존재한다. training용 제품 개발 방향은 이번 두 사례에서 별도 검증하지 않았다.',
             evidence_paths=['docs/REQUIREMENTS_TRACEABILITY.md', 'memory_dsa/integrated.py:analyze_integrated'],
             input_paths=['workload.activation_bytes', 'workload.optimizer_bytes', 'phase_budget.training_bytes_per_step', 'phase_budget.training_steps_per_s'],
             output_paths=['results.json:integrated_scenarios[training]'], screen_paths=['index.html#configuration'],
             verification='Existing training phase arithmetic regressions; no workload-evidence-to-product recommendation claimed.', strategy_status='계산 있음 / 제품전략 미평가'),
        dict(id='prefill', status='not_evaluated', reason='입력률·prefix reuse와 other traffic 예산은 존재한다. decode의 장문 결과를 prefill 제품 추천으로 확대하지 않는다.',
             evidence_paths=['inputs/MODEL_TRENDS.md', 'memory_dsa/integrated.py:analyze_integrated'],
             input_paths=['workload.input_tokens_per_s', 'workload.prefix_reuse_ratio', 'phase_budget.prefill_other_bw_bytes_s'],
             output_paths=['results.json:integrated_scenarios[prefill]'], screen_paths=['index.html#configuration'],
             verification='Existing prefill/aggregate input-rate regressions; not a measured prefill SLO.', strategy_status='계산 있음 / 제품전략 미평가'),
        dict(id='physical_ai', status='conditional_case_assessed', reason='공개 GR00T/Thor 단일 VLA 실행과 미래 동시성·p99 목표를 분리하며, 필요 BW/용량은 측정 전 null로 유지한다.',
             evidence_paths=['P06', 'P07'], input_paths=['strategy.json:cases[physical-*].parameters', 'strategy.json:benchmarks[].conditions'],
             output_paths=['strategy.json:benchmarks', 'strategy.json:directions[edge-qos-first]'], screen_paths=['strategy.html'],
             verification='test_vendor_baseline_does_not_establish_future_tail_slo', strategy_status='기존 지원 확인 / 다음 측정 우선순위 제시'),
        dict(id='module-capacity-BW-channels', status='partial_analytical', reason='기존 die/stack/module·capacity·peak/sustained·channel 구분은 유지한다. 새 지도는 GPU 또는 SOM 한 개의 memory envelope라 직접 DIMM/stack 수로 바꾸지 않는다.',
             evidence_paths=['inputs/PUBLIC_SOURCE_NOTES.md', 'inputs/MODEL_TRENDS.md', 'docs/MODELING_EXTENSIONS.md'],
             input_paths=['candidates[].capacity_bytes', 'candidates[].usable_capacity_bytes', 'candidates[].channels_per_module', 'compose_assembly(unit_count, bus_width_bits)'],
             output_paths=['results.json:decision_study.assembly_examples', 'assembly-examples.json'], screen_paths=['index.html#coverage', 'index.html#configuration'],
             verification='Existing assembly/unit/DDR5 channel regressions plus test_metric_units_and_memory_path_cannot_be_relabeled', strategy_status='단위·조합 계산 있음 / 물리적 제품 구성 최적화 미평가'),
        dict(id='rack-power-PSU', status='partial_analytical', reason='랙·PSU·냉각의 정적 budget은 존재한다. GPU/SOM TDP를 DRAM 또는 wall power로 쓰지 않으며 실제 랙 제품 전략은 측정이 필요하다.',
             evidence_paths=['inputs/PUBLIC_SOURCE_NOTES.md:S08-S10', 'P03', 'P04', 'P06'],
             input_paths=['rack.base_power_w', 'rack.power_limit_w', 'rack.psu_efficiency', 'rack.psu_capacity_w', 'rack.cooling_limit_w'],
             output_paths=['results.json:integrated_scenarios[].result.candidates[].constraints', 'strategy.json:directions[].internal_validation'],
             screen_paths=['index.html#configuration', 'strategy.html'],
             verification='Existing rack/PSU limit oracles; test_peak_is_only_a_ceiling_not_sustained_pass retains DRAM power null.', strategy_status='정적 제약 계산 / 실제 power·PSU 개발 목표 미확정'),
        dict(id='heterogeneous-disaggregation', status='partial_analytical', reason='기존 pool/path와 전체 수요 할당 coverage가 있다. CPU/GPU 계층화는 공개된 대안이며 migration·fabric 경합·SLO 실측이 선행돼야 한다.',
             evidence_paths=['P05', 'docs/MODELING_EXTENSIONS.md:Placement coverage'],
             input_paths=['placement.pools', 'placement.paths', 'placement.bind_to_demand'],
             output_paths=['results.json:integrated_scenarios[].result.placement', 'strategy.json:directions[long-context-capacity].alternatives'],
             screen_paths=['index.html#system', 'strategy.html'],
             verification='Existing unassigned-demand and exclusion regressions; no allocation optimizer or measured offload benefit.', strategy_status='조건부 대안 연결 / end-to-end 최적 배치 미평가'),
        dict(id='kv-control-data', status='partial_analytical', reason='control metadata와 payload direct/relay 예산을 분리한다. relay 실패는 경로 설계 문제일 수 있으며 신규 DRAM 시장 공백으로 주장하지 않는다.',
             evidence_paths=['docs/MODELING_EXTENSIONS.md', 'memory_dsa/integrated.py:evaluate_kv_system'],
             input_paths=['kv_system.control_operations_per_s', 'kv_system.payload_bw_bytes_s', 'kv_system.control_link_bw_bytes_s', 'kv_system.data_link_bw_bytes_s'],
             output_paths=['results.json:integrated_scenarios[].result.kv_system'], screen_paths=['index.html#system'],
             verification='Existing direct/relay independent arithmetic oracle; no latency or controller implementation claim.', strategy_status='조건부 경로 비교 / 제품 개발 필요성 미확정'),
        dict(id='model-trends-demand-growth', status='conditional_case_assessed', reason='공개 GQA/128k 모델 구조와 명시한 동시성 증가를 연결한다. 동시성 1→2→4는 운영 가정이며 채택 전망이 아니다.',
             evidence_paths=['P01', 'P02', 'inputs/MODEL_TRENDS.md'], input_paths=['strategy.json:cases[llm-bf16-*].parameters.sessions'],
             output_paths=['strategy.json:cases[].demand', 'strategy.json:directions[long-context-capacity]'], screen_paths=['strategy.html', 'index.html#sensitivity'],
             verification='test_public_architecture_kv_and_payload_are_distinct; test_current_b300_refutes_blanket_new_capacity_claim', strategy_status='근거 연결 조건부 수요 시나리오 / 연도별 시장 예측 아님'),
        dict(id='model-tech-demand-reduction', status='conditional_case_assessed', reason='가중치/KV 저정밀도 비교와 실제 Thor graph/정밀도 최적화 사례를 제시한다. 효율 개선이 신제품 필요성을 줄이는 반증 조건이다.',
             evidence_paths=['P07', 'inputs/MODEL_TRENDS.md'], input_paths=['strategy.json:cases[llm-lowprecision-2].parameters', 'strategy.json:benchmarks'],
             output_paths=['strategy.json:assessments', 'strategy.json:directions[].disconfirming_conditions'], screen_paths=['strategy.html', 'index.html#sensitivity'],
             verification='test_precision_alternative_can_remove_capacity_exclusion; test_vendor_baseline_does_not_establish_future_tail_slo', strategy_status='감소 대안 제시 / LLM 품질·실제 저장량 미검증'),
        dict(id='internal-collaboration-inputs', status='input_map', reason='실제 고객 workload, 협력사 측정과 사내 비공개 사양으로 채울 항목·조건을 표시한다. 자료를 취득하거나 값을 추정하지 않는다.',
             evidence_paths=['outputs/internal-gap-schema.json', 'inputs/PUBLIC_SOURCE_NOTES.md'],
             input_paths=['candidates[].sustained_bw_bytes_s', 'candidates[].power_w', 'candidates[].p99_latency_ns', 'rack.fabric_bw_bytes_s'],
             output_paths=['internal-gap-schema.json', 'strategy.json:directions[].internal_validation'], screen_paths=['index.html#sources', 'strategy.html'],
             verification='Existing supported-input versus not-implemented gap-schema regressions; no private-data ingestion.', strategy_status='필요 항목/조건 제시 / 사내·협력사 데이터 미수집'),
        dict(id='coverage-insufficiency-blank', status='conditional_case_assessed', reason='자료 공백·단일 구성의 조건부 부족·vendor 지원 기준점·미입증 시장 공백을 분리한다. 전체 시장의 미충족은 아직 확인하지 않았다.',
             evidence_paths=['P01-P09', 'docs/REQUIREMENTS_TRACEABILITY.md'], input_paths=['strategy.json:cases', 'strategy.json:products'],
             output_paths=['strategy.json:assessments', 'strategy.json:remaining_axes'], screen_paths=['strategy.html', 'index.html#coverage'],
             verification='test_unknown_and_zero_are_not_the_same; test_directions_bind_evidence_and_keep_targets_honest', strategy_status='구분·조건부 방향 제시 / 전체 시장 커버리지 미조사'),
        dict(id='HBF/NAND', status='positioning_only', reason='인접 기술 위치만 표시하고 본 분석·추천 후보·측정 요청에서 제외한다.',
             evidence_paths=['inputs/PUBLIC_SOURCE_NOTES.md:Scope'], input_paths=['user scope exclusion'],
             output_paths=['results.json:positioning', 'strategy.json:boundaries'], screen_paths=['index.html#sources', 'strategy.html'],
             verification='test_remaining_scope_unknown_not_fabricated_or_excluded_candidate', strategy_status='사용자 요청에 따른 제외'),
    ])
    return rows


def strategy_study():
    # Local import keeps the shared quantity/model helpers usable by the portfolio
    # without introducing an import-time cycle or changing the original deep dives.
    from .portfolio import portfolio_study

    products = product_profiles()
    cases = [make_llm_case('llm-bf16-1', '70B BF16 · 128 Ki · 1 session', sessions=1),
             make_llm_case('llm-bf16-2', '70B BF16 · 128 Ki · 2 sessions', sessions=2),
             make_llm_case('llm-bf16-4', '70B BF16 · 128 Ki · 4 sessions', sessions=4),
             make_llm_case('llm-lowprecision-2', '8-bit weight/KV 가정 · 2 sessions', sessions=2, weight_bytes=1, kv_bytes=1,
                           kind='software_alternative_assumption')] + _physical_cases()
    assessments = [assess_case(c, p) for c in cases for p in products if c['scope'] == p['scope']]
    portfolio = portfolio_study()
    by_axis = {row['requirement_id']: row for row in portfolio['axis_trace']}
    remaining = _requirement_trace()
    if set(by_axis) != {row['id'] for row in remaining}:
        raise ValueError('Portfolio must preserve exactly the original 19 requirement axes')
    for row in remaining:
        trace = by_axis[row['id']]
        row.update(
            status=trace['assessment_status'],
            reason=trace.get('result_summary') or trace['withheld_judgment'],
            evidence_paths=trace['evidence_refs'] or ['User scope exclusion: HBF/NAND'],
            input_paths=[
                'strategy.json:portfolio.analyses[id=' + ref + '].' + field
                for ref in trace['analysis_refs'] for field in ('inputs', 'assumptions')
            ] or ['User scope exclusion'],
            output_paths=[
                'strategy.json:portfolio.analyses[id=' + ref.split('.', 1)[0] + '].'
                + ref.split('.', 1)[1] for ref in trace['result_refs']
            ] or ['strategy.json:portfolio.boundaries'],
            screen_paths=['strategy.html#' + ref.lstrip('#') for ref in trace['screen_refs']],
            verification='; '.join(trace['verification_refs']),
            strategy_status=trace['assessment_status'] + ' — ' + trace['withheld_judgment'])
    sources = source_registry() + portfolio['sources']
    if len({source['id'] for source in sources}) != len(sources):
        raise ValueError('Source IDs must remain unique across deep dives and portfolio')
    return dict(schema_version=2, checked_at=CHECKED_AT, title='메모리 제품 방향 — 19개 요구를 잇는 조건부 의사결정 지도',
                summary=['HBM: 학습·decode의 역산 용량/BW와 랙 전력을 함께 비교하고 현재 HBM4 구성·샤딩 대안을 먼저 검증한다.',
                         'DDR 계층: warm KV 저장 용량과 채널·fabric·전송 시간·제어 경로를 함께 설계한다. DDR6/7 미확인 사양은 채우지 않는다.',
                         'LPDDR: 기존 Physical AI 기준점을 유지하면서 동시 부하의 p99·전력·열·품질이 실제로 새 제품을 요구하는지 검증한다.',
                         '우선순위는 선언한 제약의 검증 순서이다. 조건부 구성 부족·제품 데이터 공백·입증된 시장 공백을 구분하며 전체 시장 미충족을 주장하지 않는다.'],
                portfolio=portfolio, sources=sources, products=products, cases=cases, assessments=assessments,
                directions=_directions(cases, assessments), benchmarks=_benchmarks(), remaining_axes=remaining,
                boundaries=['공개 workload/제품 사실 + 명시한 운영 가정의 분석이다. 가정한 동시성은 시장 성장률·고객 채택량·출하 전망이 아니다.',
                            '서버는 GPU 한 개, embedded는 SOM 한 개를 각각 비교한다. GB/GB/s는 decimal이다. nominal/peak 공급을 usable/sustained처럼 표시하지 않는다.',
                            'Payload 용량은 runtime 여유를 제외한다. BW는 조건부 logical full-read 모델이며 실측 버스 수요·달성 throughput이 아니다.',
                            '출처의 GB 표기와 집계치에는 차이가 있을 수 있다. B300은 직접 per-GPU 288 GB/8 TB/s 표를 사용하며 DGX aggregate의 반올림 총량으로 역산하지 않는다.',
                            'Physical AI 공개 median은 p99가 아니다. GPU/SOM 전력은 DRAM 전력이 아니다. 미확인값은 null이며 0 좌표·시장 공백으로 바꾸지 않는다.',
                            'HBM5 및 미공개 미래 사양은 null을 유지한다. HBF/NAND는 포지셔닝만 남기고 분석 후보에서 제외한다.',
                            '통합 지도는 원래 19개 축을 조건부 계산·공개 상태·판단 보류 기준으로 연결한다. 두 심층 사례와 설계 시나리오는 전체 시장을 대표하지 않는다.',
                            'eligible 상태만으로 전체 시스템 적합을 판정하지 않는다. ranking_eligible/comparison_conclusive와 미확인 제약, workload qualification을 별도로 확인한다.'])
