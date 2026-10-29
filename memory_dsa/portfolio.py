"""Conditional product targets from explicit workload and infrastructure budgets.

Pure, deterministic arithmetic. Public shipping status, configurable design targets,
logical traffic lower bounds, and unknown application performance are separate.
No calibrated forecast, market-size estimate, placement optimizer or hardware test.
"""
import math
from copy import deepcopy

from .strategy import quantity, make_llm_case, CHECKED_AT
from .integrated import evaluate_kv_system, evaluate_placement

GIB = 2 ** 30
HBM = 'hbm-throughput-energy'
TIER = 'capacity-tier-kv'
EDGE = 'edge-qos'


def _number(value, name, *, positive=False, integer=False, nullable=False):
    if value is None and nullable:
        return value
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0 or (positive and value == 0) or
            (integer and not isinstance(value, int))):
        raise ValueError(name + ' must be a finite ' + ('positive ' if positive else 'nonnegative ') + 'number')
    return value


def _fraction(value, name):
    _number(value, name, positive=True)
    if value > 1:
        raise ValueError(name + ' must be <= 1')
    return value


def q(value=None, unit='B', scope='configured object', *, sources=(), note='', minimum=None, maximum=None, kind=None):
    return quantity(value, unit=unit, scope=scope,
                    kind=kind or ('derived_conditional' if value is not None or minimum is not None else 'unknown'),
                    sources=sources, note=note, minimum=minimum, maximum=maximum)


def training_budget(*, parameters=70e9, shards=4, layers=80, prefetch_layers=2,
                    activation_bytes=32 * GIB, update_window_s=.1,
                    other_traffic_bytes_s=None):
    """Selected FP32-shard/BF16-staging model, not the FSDP default or peak measurement.

    Persistent state: FP32 parameters + FP32 gradients + two FP32 Adam moments.
    Optimizer logical lower bound reads 16 and writes 12 bytes/parameter/update.
    P/layers assumes equally sized layers and is only a prefetch approximation;
    embeddings and actual FSDP groups differ. Real fused kernels, cache reuse,
    materialization, collectives and allocator overhead require measured replacement.
    """
    for name, value in [('parameters', parameters), ('update_window_s', update_window_s)]:
        _number(value, name, positive=True)
    for name, value in [('shards', shards), ('layers', layers), ('prefetch_layers', prefetch_layers)]:
        _number(value, name, positive=True, integer=True)
    if prefetch_layers > layers:
        raise ValueError('prefetch layers exceed model layers')
    _number(activation_bytes, 'activation_bytes', nullable=True)
    _number(other_traffic_bytes_s, 'other_traffic_bytes_s', nullable=True)
    state = parameters * (4 + 4 + 8) / shards
    staging = parameters / layers * prefetch_layers * 2
    capacity = None if activation_bytes is None else state + staging + activation_bytes
    optimizer = parameters / shards * 28 / update_window_s
    return dict(shards=shards, state_bytes=state, prefetch_bytes=staging,
                activation_bytes=activation_bytes, capacity_bytes=capacity,
                optimizer_logical_bw_lower_bound=optimizer,
                total_bw_bytes_s=None if other_traffic_bytes_s is None else optimizer + other_traffic_bytes_s,
                update_window_s=update_window_s, measured=False)


def prefill_budget(*, requests=4, input_tokens=8192, reuse_fraction=0,
                   window_s=.5, kv_bytes_per_token=327680, other_traffic_bytes_s=None):
    for name, value in [('requests', requests), ('input_tokens', input_tokens)]:
        _number(value, name, positive=True, integer=True)
    for name, value in [('window_s', window_s), ('kv_bytes_per_token', kv_bytes_per_token)]:
        _number(value, name, positive=True)
    _number(reuse_fraction, 'reuse_fraction')
    if reuse_fraction > 1:
        raise ValueError('reuse_fraction exceeds 1')
    _number(other_traffic_bytes_s, 'other_traffic_bytes_s', nullable=True)
    resident = requests * input_tokens * kv_bytes_per_token
    written = resident * (1 - reuse_fraction)
    lower = written / window_s
    return dict(new_kv_bytes=written, logical_resident_kv_bytes=resident,
                kv_write_lower_bound_bytes_s=lower,
                total_bw_bytes_s=None if other_traffic_bytes_s is None else lower + other_traffic_bytes_s,
                resident_capacity_savings_bytes=None, achieved_ttft_s=None,
                reuse_fraction=reuse_fraction, window_s=window_s)


def reverse_object_targets(*, capacity_bytes=None, logical_bw_bytes_s=None,
                           objects=8, usable_fraction=.9, bandwidth_efficiency=.7):
    _number(objects, 'objects', positive=True, integer=True)
    _fraction(usable_fraction, 'usable_fraction')
    _fraction(bandwidth_efficiency, 'bandwidth_efficiency')
    _number(capacity_bytes, 'capacity_bytes', nullable=True)
    _number(logical_bw_bytes_s, 'logical_bw_bytes_s', nullable=True)
    return dict(nominal_capacity_per_object_bytes=None if capacity_bytes is None else capacity_bytes / objects / usable_fraction,
                peak_bw_per_object_bytes_s=None if logical_bw_bytes_s is None else logical_bw_bytes_s / objects / bandwidth_efficiency,
                objects=objects, usable_fraction=usable_fraction, bandwidth_efficiency=bandwidth_efficiency,
                qualification='conditional target; capacity/BW/power need a joint qualified operating point')


def channel_budget(*, modules=8, independent_channels=8, transfers_per_s=5.6e9,
                   data_width_bits=64, efficiency=.7, demand_bytes_s=None):
    for name, value in [('modules', modules), ('independent_channels', independent_channels), ('data_width_bits', data_width_bits)]:
        _number(value, name, positive=True, integer=True)
    if independent_channels > modules:
        raise ValueError('this one-channel-per-module model cannot exceed module count')
    _number(transfers_per_s, 'transfers_per_s', positive=True)
    _fraction(efficiency, 'efficiency')
    _number(demand_bytes_s, 'demand_bytes_s', nullable=True)
    peak = transfers_per_s * data_width_bits / 8
    sustained_assumption = peak * efficiency
    return dict(per_channel_peak_bytes_s=peak, per_channel_assumed_bytes_s=sustained_assumption,
                aggregate_assumed_bytes_s=sustained_assumption * independent_channels,
                minimum_independent_channels=None if demand_bytes_s is None else math.ceil(demand_bytes_s / sustained_assumption),
                modules=modules, independent_channels=independent_channels,
                bandwidth_status='unknown' if demand_bytes_s is None else
                ('conditional_shortfall' if demand_bytes_s > sustained_assumption * independent_channels else 'conditional_headroom'))


def transfer_budget(*, payload_bytes, arrival_rate_s, miss_fraction, deadline_s,
                    source_bytes_s=None, destination_bytes_s=None, fabric_bytes_s=None):
    for name, value in [('payload_bytes', payload_bytes), ('deadline_s', deadline_s)]:
        _number(value, name, positive=True)
    for name, value in [('arrival_rate_s', arrival_rate_s), ('miss_fraction', miss_fraction)]:
        _number(value, name)
    if miss_fraction > 1:
        raise ValueError('miss fraction exceeds 1')
    for name, value in [('source_bytes_s', source_bytes_s), ('destination_bytes_s', destination_bytes_s), ('fabric_bytes_s', fabric_bytes_s)]:
        _number(value, name, positive=True, nullable=True)
    rate = payload_bytes * arrival_rate_s * miss_fraction
    has_transfers = arrival_rate_s > 0 and miss_fraction > 0
    # A per-copy deadline constrains even a rare positive miss, but no copy is
    # scheduled when either arrivals or misses are zero. Do not invent demand.
    per_copy = payload_bytes / deadline_s if has_transfers else 0
    required = max(rate, per_copy)
    bounds = [source_bytes_s, destination_bytes_s, fabric_bytes_s]
    known_bounds = [bound for bound in bounds if bound is not None]
    known_ceiling = min(known_bounds) if known_bounds else None
    available = None if None in bounds else min(bounds)
    status = ('conditional_shortfall' if known_ceiling is not None and required > known_ceiling else
              'unknown' if available is None else 'conditional_headroom')
    return dict(steady_state_bytes_s=rate, per_copy_deadline_bytes_s=per_copy,
                transfer_required=has_transfers,
                required_bytes_s=required, path_limit_bytes_s=available,
                known_path_ceiling_bytes_s=known_ceiling,
                known_bound_transfer_time_lower_bound_s=None if known_ceiling is None or not has_transfers else payload_bytes / known_ceiling,
                transfer_time_lower_bound_s=None if available is None or not has_transfers else payload_bytes / available,
                status=status,
                achieved_ttft_s=None, achieved_p99_s=None)


def rack_residual(*, shelf_count=2, shelf_nplus1_dc_w=15000, available_ac_w=35000,
                  psu_efficiency=.94, cooling_dc_w=28000, non_dram_dc_w=24000,
                  memory_objects=80, proposed_memory_w=25):
    """N+1 shelf rating is already DC: never multiply it by PSU efficiency twice."""
    for name, value in [('shelf_count', shelf_count), ('memory_objects', memory_objects)]:
        _number(value, name, positive=True, integer=True)
    for name, value in [('shelf_nplus1_dc_w', shelf_nplus1_dc_w), ('available_ac_w', available_ac_w),
                        ('cooling_dc_w', cooling_dc_w), ('non_dram_dc_w', non_dram_dc_w),
                        ('proposed_memory_w', proposed_memory_w)]:
        _number(value, name, nullable=True)
    if psu_efficiency is not None:
        _fraction(psu_efficiency, 'psu_efficiency')
    supply_dc = None if shelf_nplus1_dc_w is None else shelf_count * shelf_nplus1_dc_w
    ac_dc = None if available_ac_w is None or psu_efficiency is None else available_ac_w * psu_efficiency
    bounds = [supply_dc, ac_dc, cooling_dc_w]
    # Known upper bounds remain useful, but cannot establish full constraint clearance.
    known = [v for v in bounds if v is not None]
    cap = min(known) if known else None
    residual = None if cap is None or non_dram_dc_w is None else cap - non_dram_dc_w
    per_object = None if residual is None else residual / memory_objects
    demand = None if non_dram_dc_w is None or proposed_memory_w is None else non_dram_dc_w + memory_objects * proposed_memory_w
    status = ('unknown' if cap is None or demand is None else 'conditional_shortfall' if demand > cap else
              'unknown' if None in bounds else 'conditional_headroom')
    return dict(survivable_supply_dc_w=supply_dc, ac_limited_dc_w=ac_dc,
                cooling_dc_w=cooling_dc_w, effective_known_dc_ceiling_w=cap,
                residual_memory_dc_w=residual, memory_w_per_object_ceiling=per_object,
                allocatable_memory_dc_w=None if residual is None else max(0, residual),
                proposed_total_dc_w=demand,
                proposed_wall_ac_w=None if demand is None or psu_efficiency is None else demand / psu_efficiency,
                all_limits_known=None not in bounds, status=status,
                baseline_already_exceeds_ceiling=cap is not None and non_dram_dc_w is not None and non_dram_dc_w > cap)


def edge_sensor_budget(*, cameras=4, width=1920, height=1080, bytes_per_pixel=3,
                       fps=30, memory_copies=2, transfer_window_s=.005,
                       other_traffic_bytes_s=None):
    for name, value in [('cameras', cameras), ('width', width), ('height', height), ('memory_copies', memory_copies)]:
        _number(value, name, positive=True, integer=True)
    for name, value in [('bytes_per_pixel', bytes_per_pixel), ('fps', fps), ('transfer_window_s', transfer_window_s)]:
        _number(value, name, positive=True)
    _number(other_traffic_bytes_s, 'other_traffic_bytes_s', nullable=True)
    frames = cameras * width * height * bytes_per_pixel
    traffic = frames * fps * memory_copies
    return dict(raw_frame_bytes=frames, raw_ingress_bytes_s=frames * fps,
                sensor_memory_lower_bound_bytes_s=traffic,
                transfer_window_lower_bound_bytes_s=frames * memory_copies / transfer_window_s,
                total_bw_bytes_s=None if other_traffic_bytes_s is None else traffic + other_traffic_bytes_s,
                total_capacity_bytes=None, achieved_p99_ms=None)


def compare_quantity(required, available):
    """Only identical physical scope and unit can be compared directly."""
    if required['unit'] != available['unit'] or required['scope'] != available['scope']:
        return 'not_comparable'
    if required['value'] is None or available['value'] is None:
        return 'unknown'
    return 'conditional_shortfall' if required['value'] > available['value'] else 'conditional_headroom'


def compare_envelope(required, available):
    """An upper envelope can exclude; being below it is not a qualified SKU fit."""
    status = compare_quantity(required, available)
    if status != 'unknown' or required['value'] is None:
        return status
    upper, lower = available.get('max'), available.get('min')
    if upper is not None:
        return 'conditional_shortfall' if required['value'] > upper else 'within_envelope_only'
    if lower is not None and required['value'] <= lower:
        return 'within_envelope_only'
    return 'unknown'


def calculation_sources():
    rows = [
        ('PX01', 'PyTorch FSDP2 tutorial', 'https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html', None,
         'Sharding, FP32 persistent state, BF16 gathered parameters and prefetch mechanisms; the 70B/4–8-shard budgets here are design assumptions, not its benchmark.'),
        ('PX02', 'TensorRT-LLM KV cache reuse', 'https://nvidia.github.io/TensorRT-LLM/advanced/kv-cache-reuse.html', None,
         'Paged context attention can reuse identical prefix pages. A selected hit fraction is not measured cache behavior or automatic resident-capacity savings.'),
        ('PX03', 'TensorRT-LLM disaggregated serving', 'https://nvidia.github.io/TensorRT-LLM/features/disagg-serving.html', '2026-10-26 documentation update',
         'Separate context/generation workers transfer KV via a declared path. Link/layout/connection overhead and E2E SLO require measurement.'),
        ('PX04', 'Eaton ORV3 power shelf — OCP', 'https://www.opencompute.org/marketplace/facilities-physical-infrastructure/eaton-open-rack-v3-orv3-power-shelf/', None,
         '18 kW DC nominal, 15 kW DC at N+1. Efficiency and non-DRAM load used here are separate assumptions, not product measurements.'),
        ('PX05', 'DeepSeek-V3 Technical Report v1', 'https://arxiv.org/html/2412.19437v1', '2024-12-27',
         '671B total versus 37B activated parameters; MLA and phase-specific deployment. Activated count is neither residency nor measured bytes/token.'),
        ('PX06', 'NIXL metadata handler', 'https://github.com/ai-dynamo/nixl/blob/main/docs/doxygen/nixl_doxygen.md#metadata-handler', None,
         'Metadata control and bulk data transfer are distinct. Mutable main checked on the stated date; no runtime performance claim.'),
        ('PX07', 'DeepSpeed ZeRO: Adam state partitioning', 'https://www.deepspeed.ai/tutorials/zero/', None,
         'FP32 weights and two Adam moment states motivate the selected state accounting. The FSDP configuration and 28 B/parameter logical update model here are explicit assumptions, not this tutorial benchmark.'),
    ]
    return [dict(id=i, title=t, url=u, published=p, checked_at=CHECKED_AT, caveat=c) for i, t, u, p, c in rows]


def _metric(identifier, label, value=None, unit='B', scope='configured object', *, note='', sources=(), minimum=None, maximum=None, kind=None):
    return dict(id=identifier, label=label,
                quantity=q(value, unit, scope, note=note, sources=sources, minimum=minimum, maximum=maximum, kind=kind))


def _analysis(identifier, title, scope, sources, assumptions, metrics, conclusion, directions, *, inputs=None, status='conditional_analysis'):
    for metric in metrics:
        if not metric['quantity']['sources'] and metric['quantity']['kind'] not in ('unknown', 'scenario_assumption'):
            metric['quantity']['sources'] = list(sources)
    return dict(id=identifier, title=title, scope=scope, evidence_ids=sources, assumptions=assumptions,
                inputs=inputs or {}, metrics=metrics, decision_status=status, conclusion=conclusion,
                direction_ids=directions, market_status='unserved_market_not_established')


def _profile_placement(profile_id, warm_payload, path, source_bw):
    """Bind one explicitly disjoint KV slice to its own profile's payload demand."""
    hot_payload=40*GIB
    total_payload=warm_payload+hot_payload
    warm_capacity=8*128e9*.9
    request=dict(bind_to_demand=True,pools=[
        dict(id='warm-ddr',family='DDR5',capacity_bytes=warm_capacity,
             sustained_bw_bytes_s=source_bw,assigned_bytes=warm_payload,
             access_bw_bytes_s=path['required_bytes_s']),
        dict(id='hot-hbm',family='HBM',capacity_bytes=None,sustained_bw_bytes_s=1e12,
             assigned_bytes=hot_payload,access_bw_bytes_s=path['required_bytes_s'])],
        paths=[dict(id='warm-to-hot',source='warm-ddr',destination='hot-hbm',
                    traffic_bytes_s=path['required_bytes_s'],bandwidth_bytes_s=80e9)])
    evaluation=evaluate_placement(request,demand_capacity_bytes=total_payload)
    return dict(profile_id=profile_id,
                demand_scope='this profile: BF16 warm-cache payload plus one disjoint hot-transfer destination; not the complete active decode deployment',
                allocation_semantics='disjoint logical KV sets; the hot prefix is not counted in warm retention',
                assumptions=[
                    'Warm prefix는 비활성 BF16 KV 40 GiB이고 hot destination은 warm 목록과 겹치지 않는 한 prefix 40 GiB다.',
                    '이 배치 검사는 해당 warm-cache/한-copy slice만 다룬다. 별도 1-byte decode 대안과 한 실행 구성으로 합치지 않는다.',
                    '이동 도중 임시 복제·weights·allocator·전체 active sessions는 제외하며 추가 메모리는 미확인이다.',
                    'Pool access BW는 이 migration traffic budget만 포함한다. 기타 access traffic와 hot usable capacity는 미확인이다.',
                    'coverage.status는 수요 배분 누락 검사다. 용량/경로 적합성은 evaluation.status와 coverage.whole_demand_status를 함께 읽는다.'],
                transient_replication_bytes=None,request=request,demand_capacity_bytes=total_payload,
                metrics=[
                    _metric('warm-payload','선택 profile warm KV 수요',warm_payload,scope='one warm-KV pool payload',sources=['P02']),
                    _metric('hot-payload','분리된 hot destination 수요',hot_payload,scope='one hot-transfer destination payload',sources=['P02']),
                    _metric('total-payload','배치에 연결한 총 KV slice 수요',total_payload,scope='disjoint warm plus hot KV slice',sources=['P02']),
                    _metric('warm-capacity','선언 DDR5 usable 예산',warm_capacity,scope='one warm-KV pool usable budget',sources=['PF12'],note='8×128 decimal GB×assumed90% usable; not measured allocation.'),
                    _metric('path-required','선택 profile 전송 요구',path['required_bytes_s'],'B/s','one warm-to-hot path',sources=['PX03']),
                    _metric('path-limit','선언 전송 경로 상한',path['path_limit_bytes_s'],'B/s','one warm-to-hot path',sources=['PX03'],note='Configured source/destination/fabric budgets, not public measured throughput.')],
                evaluation=evaluation)


def _triage(training_target, tier_target, rack, *, hbm_reference=36e9, ddr_reference=128e9):
    """Transparent review order, not an investment score or measured market priority."""
    if rack['status'] == 'conditional_shortfall':
        return [HBM, EDGE, TIER], ['rack_memory_power_exceeds_residual'], '랙 잔여 전력이 먼저 위반되어 HBM 효율 검증을 선행한다. 엣지 QoS/전력을 다음에 검토한다.'
    if training_target > hbm_reference:
        return [HBM, TIER, EDGE], ['configured_hbm4_stack_capacity_shortfall'], '명시한 8-stack·4-shard 구성에서 36 GB/stack을 넘으므로 HBM 구성/용량 대안을 먼저 검토한다.'
    if tier_target > ddr_reference:
        return [TIER, EDGE, HBM], ['configured_ddr5_module_capacity_shortfall'], '지정 DDR5 모듈의 용량 상한을 넘는 warm tier부터 검토한다.'
    return [EDGE, TIER, HBM], ['known_capacity_pressure_relaxed', 'edge_tail_latency_missing'], '정밀도·샤딩·cache 규모 완화로 지정 용량 배제가 사라져, 미확인 엣지 tail QoS를 먼저 측정한다.'


def portfolio_study():
    from .portfolio_evidence import portfolio_sources, product_families

    train4, train8 = training_budget(shards=4), training_budget(shards=8)
    pf0, pf75 = prefill_budget(), prefill_budget(reuse_fraction=.75)
    decode = make_llm_case('portfolio-decode', '4-session BF16', sessions=4)
    low = make_llm_case('portfolio-efficient', '2-session 1-byte', sessions=2, weight_bytes=1, kv_bytes=1)
    h4 = reverse_object_targets(capacity_bytes=train4['capacity_bytes'], logical_bw_bytes_s=train4['optimizer_logical_bw_lower_bound'])
    h8 = reverse_object_targets(capacity_bytes=train8['capacity_bytes'], logical_bw_bytes_s=train8['optimizer_logical_bw_lower_bound'])
    hd = reverse_object_targets(capacity_bytes=decode['demand']['capacity']['value'], logical_bw_bytes_s=decode['demand']['logical_bw']['value'])
    tier_small, tier_large = 16 * 40 * GIB, 64 * 40 * GIB
    module_small, module_large = tier_small / 8 / .9, tier_large / 8 / .9
    channel = channel_budget(demand_bytes_s=80 * GIB)
    path = transfer_budget(payload_bytes=40 * GIB, arrival_rate_s=4, miss_fraction=.5, deadline_s=.5,
                           source_bytes_s=channel['aggregate_assumed_bytes_s'], destination_bytes_s=1e12, fabric_bytes_s=80e9)
    efficient_path = transfer_budget(payload_bytes=40 * GIB, arrival_rate_s=4, miss_fraction=.25, deadline_s=1,
                                     source_bytes_s=channel['aggregate_assumed_bytes_s'], destination_bytes_s=1e12, fabric_bytes_s=80e9)
    rack, tight = rack_residual(), rack_residual(cooling_dc_w=25000)
    edge = edge_sensor_budget()
    kv = evaluate_kv_system(dict(sessions=64, metadata_bytes_per_session=4096,
                                control_operations_per_s=1000, control_bytes_per_operation=1024,
                                payload_bw_bytes_s=path['required_bytes_s'], control_link_bw_bytes_s=1e9,
                                data_link_bw_bytes_s=80e9, server_metadata_capacity_bytes=GIB))
    placements_by_profile={
        'growth':_profile_placement('growth',tier_large,path,channel['aggregate_assumed_bytes_s']),
        'efficient':_profile_placement('efficient',tier_small,efficient_path,channel['aggregate_assumed_bytes_s']),
        'power-constrained':_profile_placement('power-constrained',tier_large,path,channel['aggregate_assumed_bytes_s']),
    }
    placement=placements_by_profile['growth']['evaluation']

    analyses = [
        _analysis('training-state', '학습: 샤딩과 prefetch를 포함한 메모리 목표', 'one configured training rank', ['P01', 'PX01', 'PX07'],
          ['70B nominal, FP32 parameter/gradient/Adam moments = 16 B/parameter; 4 또는 8 shard.',
           'BF16 두 layer staging은 P/layers 균등 layer 근사 + activation32 GiB 가정. Embedding/FSDP group 크기는 다르며 실제 peak/prefetch/collective buffer/fragmentation은 측정으로 대체해야 한다.',
           'optimizer 한 번의 28 B/parameter 논리 read+write를 100 ms 창에 처리한다는 가정. 전체 step BW와 시간은 미확인.'],
          [_metric('capacity-4', '4 shard payload', train4['capacity_bytes'], scope='one training rank'),
           _metric('capacity-8', '8 shard payload', train8['capacity_bytes'], scope='one training rank'),
           _metric('optimizer-4', '4 shard optimizer window BW 하한', train4['optimizer_logical_bw_lower_bound'], 'B/s', 'one training rank optimizer logical payload'),
           _metric('optimizer-8', '8 shard optimizer window BW 하한', train8['optimizer_logical_bw_lower_bound'], 'B/s', 'one training rank optimizer logical payload'),
           _metric('total-training-bw', '전체 training traffic', unit='B/s', scope='one training rank all traffic', note='forward/backward/collective traffic 미입력'),
           _metric('stack-target', '8 stack·90% usable 용량 목표', unit='B', scope='one HBM stack nominal capacity', minimum=h8['nominal_capacity_per_object_bytes'], maximum=h4['nominal_capacity_per_object_bytes'])],
          '4→8 shard는 약 318→178 GB/rank로 낮춘다. 8 stack의 약 44.15 GB 목표는 48 GB sample 후보·stack 수·샤딩 대안을 먼저 비교하며 HBM5 필요성을 확정하지 않는다.', [HBM], inputs={'four_shards':train4, 'eight_shards':train8}),
        _analysis('prefill-reuse', 'Prefill: 생성 KV 하한과 prefix 재사용', 'one declared prefill batch', ['P01', 'P02', 'PX02', 'PX03'],
          ['4 requests × 8192 tokens, BF16 GQA KV 327680 B/token, 처리 창 0.5 s.',
           '75% 동일 prefix reuse는 조건부 입력이다. resident KV savings는 자동 계산하지 않는다.',
           'GEMM/attention/weight traffic·compute time은 미입력. 이 하한으로 전체 prefill 성능을 판정할 수 없다.'],
          [_metric('kv-resident', 'logical resident KV', pf0['logical_resident_kv_bytes'], scope='one prefill batch KV payload'),
           _metric('write-0', 'reuse 0% KV write 하한', pf0['kv_write_lower_bound_bytes_s'], 'B/s', 'one prefill batch KV write'),
           _metric('write-75', 'reuse 75% KV write 하한', pf75['kv_write_lower_bound_bytes_s'], 'B/s', 'one prefill batch KV write'),
           _metric('total-prefill', '전체 prefill BW', unit='B/s', scope='one prefill worker all traffic'),
           _metric('ttft', '실제 TTFT', unit='ms', scope='end-to-end TTFT')],
          '재사용은 계산할 KV write를 21.47→5.37 GB/s로 낮춘다. 새 고속 메모리 요구보다 compute·cache hit·전체 traffic을 먼저 측정한다.', [HBM,TIER], inputs={'without_reuse':pf0,'with_reuse':pf75}),
        _analysis('decode-capacity', 'Decode: 동시성 증가와 정밀도 대안', 'one configured accelerator payload', ['P01','P02','P05','P08'],
          ['4×128 Ki-token, BF16 70B weights/KV, 세션당 20 output tokens/s.',
           '비교 대안은 2-session 1-byte weights/KV이며 품질·metadata overhead는 미검증.',
           '8 stack, 90% usable fraction, 70% peak-to-traffic efficiency는 설계 가정. BW는 full scan 논리 모델.'],
          [_metric('bf16-4', '4-session BF16 payload', decode['demand']['capacity']['value'], scope='one accelerator payload'),
           _metric('low-2', '2-session low precision payload', low['demand']['capacity']['value'], scope='one accelerator payload'),
           _metric('read-model', '4-session logical scan', decode['demand']['logical_bw']['value'], 'B/s', 'one accelerator logical payload traffic'),
           _metric('stack-bw', '8 stack·70% 효율에서 peak BW 목표', hd['peak_bw_per_object_bytes_s'], 'B/s', 'one HBM stack peak target'),
           _metric('stack-cap', '8 stack·90% usable에서 용량 목표', hd['nominal_capacity_per_object_bytes'], scope='one HBM stack nominal capacity')],
          '4-session 구성은 약 312 GB payload를 요구하지만 2-session 정밀도 대안은 약 113 GB다. B300만으로 현재 시장 전체를 대표하지 않으며 shipping HBM4 시스템과 새 구성도 비교해야 한다.', [HBM,TIER]),
        _analysis('ddr-tier', 'Warm KV: 모듈 밀도와 채널 수는 다른 제약', 'one warm-KV server / one declared DIMM', ['P02','PX02','PX03','PF12','PF13'],
          ['128 Ki BF16 KV 40 GiB/prefix, 비활성 warm prefix 16 또는 64개.',
           '8 modules, 90% usable. DDR5 128 GB RDIMM은 vendor label을 decimal GB로 정규화한 한 후보이며 시장 최대가 아니다.',
           '5600 MT/s × 64 data bits, 70% 효율. 8 DIMM과 8 independent channels를 별도 선언하며 2DPC 성능은 미검증.'],
          [_metric('tier-capacity', 'warm tier 목표', unit='B', scope='one warm-KV server usable payload', minimum=tier_small,maximum=tier_large),
           _metric('module-capacity', '8-slot nominal module 목표', unit='B', scope='one DDR module nominal capacity',minimum=module_small,maximum=module_large),
           _metric('channel-peak', 'DDR5-5600 64-bit channel peak', channel['per_channel_peak_bytes_s'],'B/s','one independent DDR channel peak'),
           _metric('channel-assumed', '70% 효율의 channel budget',channel['per_channel_assumed_bytes_s'],'B/s','one independent DDR channel assumed sustainable'),
           _metric('channels-needed','80 GiB/s에 필요한 independent channels',channel['minimum_independent_channels'],'channels','one warm-KV server'),
           _metric('slots-128','64-prefix용 128 GB 모듈 최소 수',math.ceil(tier_large/(128e9*.9)),'modules','one warm-KV server capacity only'),
           _metric('slots-256','64-prefix용 256 GB MRDIMM 최소 수',math.ceil(tier_large/(256e9*.9)),'modules','one warm-KV server capacity only')],
          '16-prefix는 지정 8×128 GB 용량 내지만 64-prefix는 넘는다. 88.9–355.6 GiB/module 목표에 대해 현재 256 GB MRDIMM×12라는 용량 대안도 있다(호환 CPU/slot·BW·전력 별도). DDR6/7 세대 선택은 qualification 전 보류한다.', [TIER], inputs={'channel':channel}),
        _analysis('kv-transfer', '이기종 warm→hot: 용량 충족 뒤에도 경로가 막힌다', 'one directional warm-to-hot transfer', ['PX03','PX06'],
          ['4 arrivals/s, miss 50%, copy 40 GiB, transfer allowance 0.5 s.',
           'Fabric 800 Gbit/s × 80% payload = 80 GB/s는 설계 입력. source DDR=250.88 GB/s, destination=1 TB/s 가정.',
           'B_path=min(source,destination,fabric); 필요량=max(arrival×miss×bytes,bytes/deadline). queue/handshake는 추가된다.'],
          [_metric('required','필요 directional payload BW',path['required_bytes_s'],'B/s','one warm-to-hot path'),
           _metric('available','선언 path 상한',path['path_limit_bytes_s'],'B/s','one warm-to-hot path'),
           _metric('transfer-lower','순수 전송 시간 하한',path['transfer_time_lower_bound_s']*1000,'ms','one 40 GiB transfer lower bound'),
           _metric('efficient-required','miss25%·1 s copy window 필요 BW',efficient_path['required_bytes_s'],'B/s','one warm-to-hot path'),
           _metric('wire-target','80% payload 효율에서 최소 wire rate',path['required_bytes_s']/.8*8,'bit/s','one fabric direction')],
          'Growth는 warm64-prefix 2748.78 GB가 DDR예산921.6 GB를 넘고, 85.90 GB/s 요구도80 GB/s 경로를 넘는다. Efficient16-prefix·miss25%·1 s는 warm용량과 경로를 충족하지만 hot usable capacity 등은 미확인이다.', [TIER,HBM], inputs={'base':path,'efficiency_alternative':efficient_path,'placement':placement,'placements_by_profile':placements_by_profile},status='conditional_configuration_shortfall'),
        _analysis('kv-control', 'KV 제어 서버: metadata 경로와 payload relay 구분', 'one KV metadata server and directional links', ['PX03','PX06'],
          ['64 sessions × 4096 B metadata, 1000 control ops/s × 1024 B/op.',
           'Control 1 GB/s, data 80 GB/s. Direct는 payload를 control server에 통과시키지 않는다.',
           '실제 CPU ops/s·p99·장애 복구는 미측정. metadata capacity와 link만 판정.'],
          [_metric('metadata','metadata 저장량',kv['metadata_bytes'],scope='one metadata server'),
           _metric('control','direct control traffic',kv['control_bw_bytes_s'],'B/s','one control link'),
           _metric('relay','relay control+payload traffic',kv['control_bw_bytes_s']+kv['payload_bw_bytes_s'],'B/s','one control link'),
           _metric('p99','실제 KV service p99',unit='ms',scope='end-to-end KV request')],
          'Direct control 예산은 충족하지만 data 병목은 남는다. Relay는 1 GB/s control link까지 넘는다. KV-only controller의 필요성은 CPU·tail/장애 비용으로 별도 검증한다.',[TIER],inputs={'evaluation':kv}),
        _analysis('rack-power','랙/PSU: N+1 DC와 AC 입력으로 DRAM 전력 역산','one declared rack / one HBM stack',['PX04'],
          ['2 Eaton shelf × 15 kW N+1 DC. AC35 kW·PSU94%·냉각28 kW(제약 시25 kW)는 별도 가정.',
           'Non-DRAM DC24 kW는 DRAM을 제외한 별도 예산이다. GPU TDP를 non-DRAM이라고 간주하지 않는다.',
           '10 accelerators × 8 stacks = 80 memory objects, 제안 DRAM25 W/object 가정. 배선·전압강하·과도 응답은 미모델링.'],
          [_metric('nplus1','N+1 DC supply',rack['survivable_supply_dc_w'],'W','one rack DC supply'),
           _metric('dc-cap','유효 DC ceiling',rack['effective_known_dc_ceiling_w'],'W','one rack DC ceiling'),
           _metric('memory-ceiling','DRAM/object 전력 상한 범위',unit='W',scope='one HBM stack DRAM only',minimum=tight['memory_w_per_object_ceiling'],maximum=rack['memory_w_per_object_ceiling']),
           _metric('proposed-ac','25 W/object 구성 wall input',rack['proposed_wall_ac_w'],'W','one rack AC input'),
           _metric('energy-ceiling','서비스 논리-byte당 전력예산 비율',unit='J/B',scope='DRAM power budget divided by service logical payload rate',minimum=tight['memory_w_per_object_ceiling']/(decode['demand']['logical_bw']['value']/8),maximum=rack['memory_w_per_object_ceiling']/(decode['demand']['logical_bw']['value']/8),note='하드웨어 energy/byte 목표가 아님. 실측 physical traffic·DRAM pJ/bit는 unknown. Static 포함 전력예산을 조건부 논리 서비스율로 나눈 비율.')],
          '28 kW cooling에서는 50 W/stack 잔여 예산, 25 kW에서는 12.5 W/stack이다. 가정한 25 W/stack 구성은 후자에서 제외되어 BW/용량과 전력의 공동 qualification이 우선이다.',[HBM,TIER],inputs={'base':rack,'power_constrained':tight}),
        _analysis('physical-qos','Physical AI: 센서 증가보다 tail/동시성 검증 우선','one edge SOM',['P06','P07'],
          ['4×1920×1080 RGB8 cameras, 30 fps, 두 memory copies, 5 ms 전송 창이라는 설계 가정.',
           'GR00T vendor 1-camera mixed precision ~40 ms는 median이다. 4-camera+VLM p99≤40 ms 요구를 입증하지 않는다.',
           'VLA/VLM activation·attention·workspace traffic 및 measured DRAM power는 미입력. 전체 BW/용량은 null.'],
          [_metric('raw-ingress','원시 센서 유입',edge['raw_ingress_bytes_s'],'B/s','one SOM raw camera input'),
           _metric('copy-bw','두-copy memory traffic 하한',edge['sensor_memory_lower_bound_bytes_s'],'B/s','one SOM camera copy payload'),
           _metric('window-bw','5 ms 창에서 copy BW 하한',edge['transfer_window_lower_bound_bytes_s'],'B/s','one SOM camera copy payload'),
           _metric('total-bw','VLA/VLM 포함 전체 BW',unit='B/s',scope='one SOM all memory traffic'),
           _metric('p99-target','설계 p99 목표',40,'ms','end-to-end application p99',kind='scenario_assumption',
                   note='이 분석에서 선택한 요구 가정이다. 사용자 확정 SLO나 P06/P07 vendor median에서 도출한 p99가 아니며 실측되지 않았다.'),
           _metric('p99-measured','실측 p99',unit='ms',scope='end-to-end application p99')],
          '추가 센서의 1.49 GB/s 평균 copy 하한은 LPDDR5X 273 GB/s peak보다 작지만 feasibility 근거는 아니다. LPDDR6 용량/BW 제품 베팅 전에 동시 추론의 QoS·열·memory rail을 측정한다.',[EDGE],inputs={'sensor_lower_bound':edge}),
        _analysis('model-trends','미래 수요: total/active·정밀도·cache 효과를 분리','declared model logical storage, not a growth forecast',['PX05','PX02','P01'],
          ['DeepSeek-V3 public 671B total vs 37B activated/token; 저장 정밀도 2 또는 1 B/parameter를 가정.',
           'Activated expert 합집합, 통신 및 MLA KV 형상은 별도 입력이다. Llama GQA KV 공식을 적용하지 않는다.',
           '미래연도 성장률·시장규모는 추정하지 않는다. concurrency·prefix retention·quality 허용 정밀도를 민감도 축으로 사용한다.'],
          [_metric('moe-total-bf16','671B 전체 weight payload / 2 B',671e9*2,scope='entire model weight payload'),
           _metric('moe-total-one','671B 전체 weight payload / 1 B',671e9,scope='entire model weight payload'),
           _metric('moe-active','37B activated logical parameter bytes / 2 B',37e9*2,scope='one token activated parameter payload',note='BW가 아님. batched expert union·reuse·communication 제외.'),
           _metric('mla-kv','이 구현의 MLA KV 요구',scope='one declared DeepSeek workload KV',note='MLA workload dimensions 미입력; GQA 값을 재사용하지 않음')],
          'MoE는 전체 resident capacity와 토큰당 활성 연산을 분리한다. 정밀도 축소·reuse·샤딩이 큰 capacity 수요를 상쇄할 수 있으므로 단순 모델크기 성장만으로 신세대 메모리를 추천하지 않는다.',[HBM,TIER,EDGE]),
    ]

    families = product_families()
    records = {r['id']:(f['id'],r) for f in families for r in f['records']}
    family_assessments = []
    def assess_family(record_id, profile_id, target, analysis_refs, *, metric='capacity', available_override=None, mapping_note=''):
        family, record = records[record_id]
        available = deepcopy(available_override if available_override is not None else record['capacity_bytes' if metric=='capacity' else 'peak_bw_bytes_s'])
        status = compare_envelope(target, available)
        explanation = {
            'conditional_shortfall': '명시한 구성의 목표가 공개 nominal/envelope 상한보다 크다. 해당 구성만 배제하며 시장 공백을 뜻하지 않는다.',
            'conditional_headroom': 'nominal 용량 안에 드는 조건부 후보. usable allocation·BW·power·SLO qualification은 미확인.',
            'within_envelope_only': '공개 포트폴리오/상한 envelope 안이다. 실제 SKU 존재·동시 동작점·SLO 충족은 미확인.',
            'unknown': '비교에 필요한 공개 규격 또는 전체 workload 수요가 없어 수치 판단을 보류한다.',
            'not_comparable': 'component/SOM/system 단위 또는 metric scope가 달라 직접 비교하지 않는다.',
        }[status]
        family_assessments.append(dict(id=record_id+'-'+profile_id+'-'+metric,family_id=family,record_id=record_id,
            profile_id=profile_id,analysis_refs=analysis_refs,evidence_ids=record['evidence_ids'],metric=metric,
            target=target,available=available,comparison_status=status,availability_limit=record['commercial_status'],
            conclusion=explanation,scope_mapping_note=mapping_note,whole_system_validated=False,
            market_status='unserved_market_not_established'))
    for profile,target in [('growth',h4),('efficient',h8)]:
        target_q=q(target['nominal_capacity_per_object_bytes'],scope='one HBM stack',sources=['PX01'],
                   note='Configured rank payload /8 stacks /90% usable; approximate weights and assumed activation.')
        assess_family('hbm4-micron-36gb-12h',profile,target_q,['training-state'])
        assess_family('hbm4e-samsung-48gb-12h-sample',profile,target_q,['training-state'],
                      mapping_note='Samples are numerically comparable, but are not a shipping/qualified system.')
    stack_target=q(h4['nominal_capacity_per_object_bytes'],scope='one HBM stack',sources=['PX01'])
    assess_family('hbm5-architecture-roadmap','growth',stack_target,['training-state'])
    stack_bw_target=q(hd['peak_bw_per_object_bytes_s'],'B/s','one HBM stack',sources=['P01','P02'],
                      note='Full-scan decode logical traffic /8 stacks /assumed70% efficiency; not measured sustained demand.')
    for record_id in ['hbm4-samsung-12h','hbm4e-samsung-48gb-12h-sample']:
        assess_family(record_id,'growth',stack_bw_target,['decode-capacity'],metric='bw',
                      mapping_note='Peak envelope only; published capacity and speed maxima are not assumed to be a jointly qualified operating point.')
    assess_family('hbm4-hgx-rubin-nvl8-system','growth',stack_target,['training-state'],
                  mapping_note='Rounded eight-GPU totals are retained as a current alternative, never divided into an exact per-stack point.')
    for profile,value in [('growth',module_large),('efficient',module_small)]:
        assess_family('ddr5-micron-128gb-rdimm',profile,q(value,scope='one DDR5 RDIMM',sources=['P02','PF12']),['ddr-tier'],
                      mapping_note='Per-module nominal reverse target; CPU/channel/slot qualification is a separate condition.')
        assess_family('ddr5-micron-mrdimm-portfolio',profile,q(value,scope='one DDR5-based MRDIMM',sources=['P02','PF13']),['ddr-tier'],
                      mapping_note='Same capacity objective on a compatible MRDIMM platform only; ranges do not enumerate discrete SKU combinations.')
    for record_id in ['ddr6-historical-roadmap','ddr7-public-spec-not-verified']:
        family, record=records[record_id]
        module_scope='one prospective '+family+' module'
        assess_family(record_id,'growth',q(module_large,scope=module_scope,sources=['P02']),['ddr-tier'],
                      available_override=q(scope=module_scope,note='No public module composition or capacity; device roadmap does not populate module fields.'),
                      mapping_note='A prospective module target is provided, but no composition from unknown future devices is invented.')
    for record_id in ['lpddr6-skhynix-16gb-die-development','lpddr6-samsung-16gb-platform-validation']:
        assess_family(record_id,'growth',q(scope='one edge SOM usable memory',note='Concurrent VLA/VLM memory peak unknown.'),['physical-qos'],
                      mapping_note='Die/package density cannot substitute for complete SOM usable memory or its unknown workload requirement.')
    assess_family('lpddr5x-jetson-t5000','growth',q(scope='one T5000 SOM unified memory',note='Total concurrent VLA/VLM capacity unknown.'),['physical-qos'])
    # The sensor-copy lower bound is never relabeled as the entire SOM bandwidth demand.
    assess_family('lpddr5x-jetson-t5000','growth',q(edge['transfer_window_lower_bound_bytes_s'],'B/s',
                  'one edge SOM sensor-copy lower-bound target',sources=['P06']),['physical-qos'],metric='bw',
                  mapping_note='Partial camera traffic and full-SOM vendor bandwidth are intentionally not a feasibility comparison.')

    profiles=[]
    for identifier,label,tcap,dcap,r,assumptions,ids in [
        ('growth','장문·학습·warm retention 확대',h4['nominal_capacity_per_object_bytes'],module_large,rack,
         ['4 training shards; 4 BF16 decode sessions; warm prefixes64; transfer miss50%; cooling28 kW.'],['training-state','decode-capacity','ddr-tier','kv-transfer','rack-power']),
        ('efficient','품질 허용 정밀도·reuse·샤딩 우선',h8['nominal_capacity_per_object_bytes'],module_small,rack,
         ['8 training shards; 2-session 1-byte decode; warm prefixes16; prefill reuse75%; transfer miss25%/1 s window.'],['training-state','prefill-reuse','model-trends','physical-qos']),
        ('power-constrained','랙 cooling 제약',h4['nominal_capacity_per_object_bytes'],module_large,tight,
         ['growth 조건 유지; cooling25 kW; DRAM25 W/stack 가정은 잔여12.5 W/stack 초과.'],['rack-power','kv-transfer','physical-qos'])]:
        order,triggers,reason=_triage(tcap,dcap,r)
        profiles.append(dict(id=identifier,label=label,assumptions=assumptions,ordered_direction_ids=order,
                             change_reasons=[reason,'순서는 선택한 제약의 검증 순서이며 수익성·시장규모·기술 세대 순위가 아니다.'],
                             analysis_ids=ids,triggers=triggers,placement=placements_by_profile[identifier]))

    directions=[
        dict(id=HBM,title='HBM: 목표 용량·논리 BW와 랙 전력을 함께 검증',action_stage='조건부 구성 검증; HBM5 세대 선택 보류',
             priority_reason='4-shard/장문 동시성에서는 지정 8-stack 용량이, 냉각 제약에서는 DRAM 잔여 전력이 먼저 제한된다.',
             workload_ids=['training-state','prefill-reuse','decode-capacity'],requirement_ids=['HBM4','HBM4E','HBM5','training','prefill','decode','rack-power-PSU'],
             family_ids=['HBM4','HBM4E','HBM5'],evidence_ids=['P01','P02','PX01','PX04'],analysis_refs=['training-state','decode-capacity','prefill-reuse','rack-power','model-trends'],
             targets=dict(capacity=q(unit='B',scope='one HBM stack nominal capacity',minimum=h8['nominal_capacity_per_object_bytes'],maximum=h4['nominal_capacity_per_object_bytes'],note='4–8 training shards, 8 stacks, 90% usable; not a future product specification.'),
                          bw=q(unit='B/s',scope='one HBM stack peak target',minimum=h8['peak_bw_per_object_bytes_s'],maximum=hd['peak_bw_per_object_bytes_s'],note='Optimizer-window lowerbound to full-scan decode model; 8 stacks/70% efficiency. Not total-training BW.'),
                          memory_power=q(unit='W',scope='one HBM stack DRAM only',minimum=tight['memory_w_per_object_ceiling'],maximum=rack['memory_w_per_object_ceiling'],note='Rack residual upper ceilings for two cooling assumptions; not measured DRAM TDP.'),
                          latency=q(50,'ms','per-session decode output-token interval design budget',kind='scenario_assumption',note='20 token/s assumption, not achieved latency.'),p99=q(unit='ms',scope='application p99')),
             current_coverage=['공개 shipping HBM4 stack/system은 현재 대안이다. 36 GB/stack과 역산44.15 GB/stack을 같은 component scope에서 비교하면 지정 구성만 초과한다.',
                               '48 GB HBM4E sample envelope는 수치상 capacity 대안이나 shipping/qualification과 다르다. capacity와 BW 최대치를 동시 보장점으로 묶지 않는다.',
                               'B300은 유일한 최신 frontier가 아니다. HBM5 미공개 값은 null이며 성능 부족으로 분류하지 않는다.'],
             alternatives=['8-shard training·activation recomputation·현재 qualified HBM4 system·packaging이 허용하는 stack 수 증가.',
                           '품질을 검증한 lower precision, batch/concurrency 조정, warm KV tier; 추가 통신/전력/SLO 비용을 함께 비교.'],
             falsification=['현재 qualified HBM4/4E 구성 또는 샤딩이 품질·SLO·랙 한도를 충족하면 추가 density 세대 필요성은 기각한다.',
                            '실제 traffic가 논리 full-scan보다 작거나 compute-bound이면 BW 증설 우선순위를 내린다.'],
             next_measurements=['training peak allocation/collective buffer, usable GB, per-phase DRAM bytes/s.',
                                '동일 capacity/BW 동작점의 rail W·thermal derating·N+1 rack telemetry·SLO.'],deep_dive_refs=['long-context-capacity']),
        dict(id=TIER,title='DDR 계층: warm KV 용량보다 경로·cache hit를 함께 설계',action_stage='DDR5 대안 검증 후 DDR6/7 요구 제안',
             priority_reason='64-prefix retention은 지정 8-slot 용량을 넘고, 16-prefix도 0.5 s transfer 조건에서 fabric가 막힌다.',
             workload_ids=['ddr-tier','kv-transfer','kv-control','prefill-reuse'],requirement_ids=['DDR6','DDR7','module-capacity-BW-channels','heterogeneous-disaggregation','kv-control-data'],
             family_ids=['DDR5','DDR6','DDR7'],evidence_ids=['P02','PX02','PX03','PX06'],analysis_refs=['ddr-tier','kv-transfer','kv-control','prefill-reuse','rack-power','model-trends'],
             targets=dict(capacity=q(unit='B',scope='one DDR module nominal capacity',minimum=module_small,maximum=module_large,note='16–64 warm prefixes ×40GiB /8 slots /90% usable.'),
                          bw=q(unit='B/s',scope='one independent DDR channel sustainable target',minimum=efficient_path['required_bytes_s']/3,maximum=path['required_bytes_s']/3,note='Three independent channels; 1 s/0.5 s transfer alternatives, not DIMM-count scaling.'),
                          memory_power=q(unit='W',scope='one DDR module DRAM only',note='Rack residual after CPU/NIC/HBM load and DDR module count must be measured.'),
                          latency=q(unit='ms',scope='one 40 GiB warm-to-hot transfer design allowance',minimum=500,maximum=1000,kind='scenario_assumption',note='Selected transfer-only design allowances; not a source-reported or achieved TTFT/p99.'),p99=q(unit='ms',scope='end-to-end KV request p99')),
             current_coverage=['DDR5 128 GB×8 구성은 16-prefix capacity는 충족하나 64-prefix에는 부족하다. 현재 256 GB MRDIMM×12 capacity 대안도 있어 전체 DDR5 시장 배제가 아니다.',
                               'DDR5-5600의 64-bit peak44.8 GB/s와 assumed70% 효율에서3 independent channels가 필요하다. MRDIMM 호환 CPU/slot qualification은 별개다.',
                               'DDR6/7 공개 미확인 값은 null. 차세대 속도만으로 80 GB/s fabric나 controller relay 병목을 해결할 수 없다.'],
             alternatives=['prefix eviction/reuse·retention 축소·DDR5 모듈/채널 증가·현재 CPU/GPU memory sharing·prefill/decode locality.',
                           '단순 metadata controller + direct transfer를 먼저 검증; relay는 복제/보안/장애요건상 필요할 때만 비용 비교.'],
             falsification=['hit rate·miss arrival 또는 허용 transfer window가 완화돼 기존 DDR5+path로 SLO를 달성하면 새 세대 요구는 기각한다.',
                            'warm reuse가 없거나 serialization/compute가 지배하면 대용량 tier ROI가 사라질 수 있다.'],
             next_measurements=['prefix reuse/eviction histogram·bytes/session·arrival burst·migration rate·E2E TTFT/p99.',
                                'source/destination/fabric directional sustained BW, controller CPU ops/s, per-module W·2DPC 영향.'],deep_dive_refs=['long-context-capacity']),
        dict(id=EDGE,title='LPDDR: Physical AI의 동시성·tail QoS를 먼저 입증',action_stage='측정 우선; 새 density/BW 제품 확정 보류',
             priority_reason='vendor one-camera median은 확인됐지만 four-camera+VLM의 p99·memory power가 미확인이다.',
             workload_ids=['physical-qos'],requirement_ids=['LPDDR6','physical_ai','model-trends-demand-growth','model-tech-demand-reduction'],
             family_ids=['LPDDR5X','LPDDR6'],evidence_ids=['P06','P07'],analysis_refs=['physical-qos','model-trends','rack-power'],
             targets=dict(capacity=q(unit='B',scope='one edge SOM usable memory',note='concurrent VLA/VLM peak allocations 미측정; sensor buffer는 total capacity 목표가 아니다.'),
                          bw=q(unit='B/s',scope='one edge SOM sensor-copy lower-bound target',minimum=edge['sensor_memory_lower_bound_bytes_s'],maximum=edge['transfer_window_lower_bound_bytes_s'],note='Average2copy to5ms burst window; full inference traffic unknown.'),
                          memory_power=q(unit='W',scope='one edge SOM DRAM rail',note='SOM40–130W를 DRAM W로 사용하지 않음.'),
                          latency=q(5,'ms','four-camera copy design allowance',kind='scenario_assumption',note='5 ms copy budget only.'),
                          p99=q(40,'ms','end-to-end application p99 design target',kind='scenario_assumption',note='Unmeasured requirement assumption; vendor40ms is median.')),
             current_coverage=['Thor LPDDR5X128 GB/273 GB/s와 GR00T vendor baseline은 기존 대안이다. 실측 p99·열·memory rail의 대체 자료가 아니다.',
                               'LPDDR6 표준/개발/샘플/플랫폼 qualification은 구분하며 공개 필드만 표시한다. 동일 미래 workload qualification은 미검증.'],
             alternatives=['기존 LPDDR5X에서 mixed precision·camera scheduling·activation lifetime·copy 제거·VLM 비동기화.',
                           'QoS partitioning 또는 memory controller 개선이 새 density보다 효과적인지 비교.'],
             falsification=['기존 SOM에서 목표 품질·4-camera+VLM p99≤40 ms·열/전력 한도를 충족하면 LPDDR6 증설 필요성을 기각한다.',
                            'tail의 주원인이 compute/큐/센서 I/O이면 BW/density 증가는 직접 처방이 아니다.'],
             next_measurements=['카메라 동시 입력+VLA/VLM trace에서 peak memory·DRAM traffic·p50/p95/p99와 throttling.',
                                '정밀도별 제어 품질·안전한 업데이트 주기·memory rail W·SOM 전체 W 분리.'],deep_dive_refs=['edge-qos-first']),
    ]

    internal_inputs = [
        dict(id='usable-stack',label='동작점별 usable stack capacity',unit='B',scope='one HBM stack',owner_role='메모리/플랫폼 qualification',direction_ids=[HBM],needed_for='44.15 GB nominal target의 실제 구성 대체 가능성',decision_rule='8×usable_stack ≥ measured training/decode peak이면 density 증설 보류',threshold=q(train4['capacity_bytes']/8,scope='one HBM stack usable allocation'),verification_method='동일 SW·온도에서 peak allocation과 ECC/runtime reserve 측정'),
        dict(id='memory-rail',label='랙 제한 시 DRAM rail',unit='W',scope='one HBM stack',owner_role='power/thermal 협업',direction_ids=[HBM],needed_for='냉각 제약에서 BW/capacity 동시 충족 여부',decision_rule='25 kW cooling scenario에서 측정 stack W≤12.5이면 잔여 예산 통과; 실제 non-DRAM 재입력 필수',threshold=q(tight['memory_w_per_object_ceiling'],'W','one HBM stack'),verification_method='메모리 rail/기타 부하 분리, sustained/thermal/N+1 동작점 동시 계측'),
        dict(id='migration',label='warm→hot directional sustained transfer',unit='B/s',scope='one path',owner_role='플랫폼/네트워크 및 승인된 고객 실측',direction_ids=[TIER],needed_for='copy deadline와 arrival rate 동시 만족',decision_rule='실제 min(source,destination,fabric)≥85.90 GB/s이며 E2E tail budget 충족 시 path 후보 유지',threshold=q(path['required_bytes_s'],'B/s','one path'),verification_method='40 GiB transfer·burst arrival trace, metadata/queue 시간을 분리하여 p99 기록'),
        dict(id='edge-tail',label='4-camera+VLA/VLM p99',unit='ms',scope='end-to-end application',owner_role='Physical AI/시스템 협업',direction_ids=[EDGE],needed_for='LPDDR5X에서 해결되는지 또는 LPDDR6/QoS 개선이 필요한지',decision_rule='품질·열·전력 유지하며 p99≤40 ms이면 density/BW 증설 추천 보류',threshold=q(40,'ms','end-to-end application',kind='scenario_assumption',note='선택한 설계 요구이며 vendor median에서 유도한 p99나 사용자 확정 SLO가 아니다.'),verification_method='warmup/표본수/온도/품질/동시 workload를 고정한 p99 및 CI 기록'),
        dict(id='phase-traffic',label='Training/prefill 전체 traffic와 compute',unit='B/s',scope='one rank/worker, phase separate',owner_role='학습/서빙 compiler 및 승인된 파트너 실측',direction_ids=[HBM,TIER],needed_for='부분 traffic 하한을 전체 제품 BW 목표로 확정하지 않기 위해',decision_rule='BW stall 지배와 실측 SLO 미달이 확인될 때에만 낮은 하한 대신 전체traffic target으로 갱신',threshold=q(unit='B/s',scope='one phase all physical traffic'),verification_method='hardware counter·allocator trace·compute utilization·collective timing 교차 검증'),
    ]
    receiver_fields = {
        'usable-stack': 'compare_quantity(available): measured usable-capacity quantity; same unit/scope required',
        'memory-rail': 'rack_residual.proposed_memory_w; non_dram_dc_w updated separately',
        'migration': 'transfer_budget.source_bytes_s / destination_bytes_s / fabric_bytes_s',
        'edge-tail': None,
        'phase-traffic': 'training_budget.other_traffic_bytes_s / prefill_budget.other_traffic_bytes_s (exclude modeled lower-bound component)',
    }
    for row in internal_inputs:
        row['status']='missing_internal_measurement'
        row['receiver_field'] = receiver_fields[row['id']]
        row['measurement_condition'] = row['verification_method']
        row['decision_threshold'] = row['threshold']
        row['ingestion_status'] = 'manual_function_input' if row['receiver_field'] else 'required_model_extension'
    for direction in directions:
        for target in direction['targets'].values():
            if target['kind'] not in ('unknown', 'scenario_assumption') and not target['sources']:
                target['sources'] = list(direction['evidence_ids'])

    # Each original axis points to a computed result or an explicit withheld decision.
    mappings=[
        ('HBM4',[HBM],['training-state','decode-capacity','rack-power'],'conditional_current_product_comparison','shipping은 workload qualification이 아님'),
        ('HBM4E',[HBM],['training-state','rack-power'],'sample_target_comparison','sample 최대 capacity/BW의 동시보장·양산 qualification 미확인'),
        ('HBM5',[HBM],['training-state','decode-capacity'],'target_derived_spec_withheld','공개 미확인 규격 null; 48 GB sample/current 대안을 배제하지 않아 세대 선택 보류'),
        ('DDR6',[TIER],['ddr-tier','kv-transfer','kv-control'],'target_derived_spec_withheld','공개 필드 미확인; DDR5와 구성 대안 기준으로 목표만 역산'),
        ('DDR7',[TIER],['ddr-tier','kv-transfer'],'target_derived_spec_withheld','공개 필드 미확인; roadmap을 확정 규격으로 사용하지 않음'),
        ('LPDDR6',[EDGE],['physical-qos'],'target_derived_qualification_withheld','개발/표준 상태와 미래 4-camera workload qualification 별개'),
        ('decode',[HBM,TIER],['decode-capacity','kv-transfer'],'conditional_analysis','논리 scan이 물리 sustained BW 또는 실측 SLO가 아님'),
        ('training',[HBM],['training-state','rack-power'],'conditional_partial_traffic_model','configured state/optimizer 하한 계산; 전체 traffic/peak 미측정'),
        ('prefill',[HBM,TIER],['prefill-reuse','kv-transfer'],'conditional_partial_traffic_model','KV write만 계산; compute/attention/GEMM 전체가 없으므로 제품 BW 확정 보류'),
        ('physical_ai',[EDGE],['physical-qos'],'vendor_baseline_and_conditional_extension','vendor median과 미래 p99 요구 분리; total allocation/traffic unknown'),
        ('module-capacity-BW-channels',[HBM,TIER],['training-state','ddr-tier','decode-capacity'],'conditional_component_sizing','module 수가 독립 channel 수가 아니며 같은 operating point qualification 미확인'),
        ('rack-power-PSU',[HBM,TIER],['rack-power'],'conditional_residual_power_model','DC N+1과 AC 효율 구분; transient/배선/실측 non-DRAM 미확인'),
        ('heterogeneous-disaggregation',[TIER,HBM],['kv-transfer','ddr-tier','rack-power'],'conditional_path_capacity_tradeoff','pool 배분/성능 최적화 아님; path capacity-only 검증'),
        ('kv-control-data',[TIER],['kv-control','kv-transfer'],'conditional_direct_relay_comparison','control CPU tail/장애 복구/운영 복잡도 미측정'),
        ('model-trends-demand-growth',[HBM,TIER,EDGE],['model-trends','training-state','decode-capacity','physical-qos'],'configurable_demand_sensitivity','연도별 확률/시장규모/실측 forecast 미제공'),
        ('model-tech-demand-reduction',[HBM,TIER,EDGE],['prefill-reuse','model-trends','training-state'],'configurable_offset_sensitivity','precision 품질/cache hit/샤딩 통신비용 추가 검증'),
        ('internal-collaboration-inputs',[HBM,TIER,EDGE],['training-state','kv-transfer','physical-qos','rack-power'],'measurement_thresholds_defined','사내/파트너 자료 수집하지 않음; 승인된 향후 계측 필드만 제시'),
        ('coverage-insufficiency-blank',[HBM,TIER,EDGE],['training-state','ddr-tier','kv-transfer','physical-qos'],'conditional_configuration_coverage','지정 구성 부족·공개 데이터 공백·시장 미충족을 구분; market unserved 입증 없음'),
        ('HBF/NAND',[],[],'positioning_only_excluded','NAND/HBF는 위치 설명만; 용량·BW·추천·랭킹 계산 제외'),
    ]
    analysis_map={a['id']:a for a in analyses}
    family_map={f['id']:f for f in families}
    comparison_families={
        'HBM4':{'HBM4'}, 'HBM4E':{'HBM4E','HBM4'}, 'HBM5':{'HBM5','HBM4','HBM4E'},
        'DDR6':{'DDR6','DDR5'}, 'DDR7':{'DDR7','DDR5'}, 'LPDDR6':{'LPDDR6','LPDDR5X'},
        'coverage-insufficiency-blank':set(family_map),
    }
    test_map={
        'training':['PortfolioEquations.test_training_sharding_keeps_unsharded_staging_and_activations'],
        'prefill':['PortfolioEquations.test_unknown_total_traffic_is_not_zero_or_lower_bound','PortfolioEquations.test_prefix_reuse_does_not_invent_resident_capacity_reduction'],
        'physical_ai':['PortfolioEquations.test_edge_sensor_copy_is_not_total_inference_traffic','PortfolioDecisionSemantics.test_edge_p99_target_is_assumption_and_not_vendor_median'],
        'module-capacity-BW-channels':['PortfolioEquations.test_modules_on_same_channel_do_not_multiply_bandwidth','PortfolioEquations.test_reverse_sizing_honors_reserve_and_efficiency'],
        'rack-power-PSU':['PortfolioEquations.test_nplus1_rating_is_dc_and_efficiency_applies_only_to_ac','PortfolioEquations.test_negative_rack_residual_is_preserved_and_unknown_limit_blocks_pass'],
        'heterogeneous-disaggregation':['PortfolioEquations.test_known_transfer_bottleneck_is_not_hidden_by_an_unknown_link','PortfolioDecisionSemantics.test_profile_placement_uses_same_demand_and_preserves_growth_shortfall'],
        'kv-control-data':['PortfolioDecisionSemantics.test_existing_path_results_never_imply_whole_system_fit'],
        'model-trends-demand-growth':['PortfolioDecisionSemantics.test_moe_active_parameters_not_reused_as_residency_or_kv'],
        'model-tech-demand-reduction':['PortfolioDecisionSemantics.test_rule_based_priority_changes_when_capacity_pressure_relaxes','PortfolioEquations.test_prefix_reuse_does_not_invent_resident_capacity_reduction'],
        'internal-collaboration-inputs':['PortfolioDecisionSemantics.test_internal_tail_gap_is_an_extension_not_fake_ingestion'],
        'coverage-insufficiency-blank':['PortfolioDecisionSemantics.test_json_determinism_and_no_unserved_market_assertion','PortfolioDecisionSemantics.test_family_matrix_is_computed_and_samples_never_become_deployment_pass'],
    }
    trace=[]
    for requirement,dirs,refs,status,withheld in mappings:
        linked_comparisons=[row for row in family_assessments
                            if (row['family_id'] in comparison_families[requirement]
                                if requirement in comparison_families else bool(set(row['analysis_refs']) & set(refs)))]
        evidence={e for ref in refs for e in analysis_map[ref]['evidence_ids']}
        evidence.update(e for row in linked_comparisons for e in row['evidence_ids'])
        # Requested family status also needs its standard/roadmap/qualification
        # evidence, even when the numeric comparison is withheld or cross-scope.
        if requirement in family_map:
            evidence.update(e for record in family_map[requirement]['records'] for e in record['evidence_ids'])
        checks=test_map.get(requirement, ['PortfolioDecisionSemantics.test_family_matrix_is_computed_and_samples_never_become_deployment_pass']
                            if dirs else ['PortfolioDecisionSemantics.test_complete_trace_is_connected_to_results_but_preserves_withheld_judgment'])
        if requirement in ('HBM5','DDR6','DDR7'):
            checks=checks+['PortfolioDecisionSemantics.test_undisclosed_families_remain_null_and_not_bad_products']
        trace.append(dict(requirement_id=requirement,requirement_label=requirement,direction_ids=dirs,
                          evidence_refs=sorted(evidence),analysis_refs=refs,result_refs=[r+'.metrics' for r in refs],
                          family_assessment_refs=[row['id'] for row in linked_comparisons],
                          screen_refs=['#portfolio-board','#portfolio-analyses','#portfolio-family-comparisons'] if refs else ['#portfolio-trace'],
                          verification_refs=['tests/test_portfolio.py::'+name for name in checks],assessment_status=status,withheld_judgment=withheld,
                          result_summary=(analysis_map[refs[0]]['conclusion'] if refs else 'NAND/HBF는 제품 추천과 모든 수치 비교에서 제외하고 DRAM 외부 저장 위치로만 구분한다.')))
    return dict(title='워크로드 → 제품 목표 → 기존 대안 → 반증: 19축 조건부 포트폴리오',
                decision_scope='공개 근거와 명시한 design scenario의 capability gap 분석. 실제 시장 미충족·실측 성능·제품 출시 예측은 입증하지 않는다.',
                priority_method='실제 계산한 구성 위반(전력→용량)부터, 위반이 완화되면 의사결정을 막는 QoS 측정을 우선한다. 수익성 점수·시장규모 순위가 아니다.',
                profiles=profiles,directions=directions,analyses=analyses,
                calculated_workloads=[a for a in analyses if a['id'] in ('training-state','prefill-reuse','decode-capacity','physical-qos','model-trends')],
                axis_trace=trace,internal_inputs=internal_inputs,product_families=families,family_assessments=family_assessments,
                sources=portfolio_sources()+calculation_sources(),
                boundaries=['모든 미래 수치는 설정 가능한 설계 시나리오이며 forecast confidence interval이 아니다.',
                            'Unknown public specification ≠ physical deficiency ≠ unserved market.',
                            'Component, GPU, SOM, system, rack scope는 직접 혼합하지 않는다.',
                            'Known partial traffic는 하한으로 보존하고 full traffic는 missing component가 있으면 null.',
                            'NAND/HBF는 positioning only. 실제 파트너/사내 자료는 포함하거나 조회하지 않았다.'])
