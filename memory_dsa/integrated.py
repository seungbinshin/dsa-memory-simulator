"""Explicit phase budgets, declared placements and independent control/data paths.

All byte budgets are logical inputs. Nothing here estimates calibrated latency.
"""
from copy import deepcopy
from .api import analyze, _analyze, obj, number, mul, InputError


def add(*values):
    return None if None in values else number(sum(values), 'calculated sum')


def check(required, limit):
    return dict(required=required, limit=limit,
                status='unevaluated' if required is None or limit is None else
                ('pass' if required <= limit else 'fail'))


def verdict(constraints):
    states = [c['status'] for c in constraints.values()]
    return 'insufficient' if 'fail' in states else ('unevaluated' if 'unevaluated' in states else 'eligible')


def numeric_object(value, fields, name):
    value = obj(value, fields, name)
    for key, item in value.items():
        number(item, name + '.' + key, nullable=True)
    return value


def analyze_integrated(request):
    """Use the stable KV request plus explicit phase_budget/placement/kv_system.

    The required GQA workload is retained for a separately labeled KV lower bound;
    training and Physical AI never reuse its traffic as their phase traffic.
    """
    obj(request, 'workload scenario candidates rack phase_budget placement kv_system', 'integrated request')
    base = {k: deepcopy(request[k]) for k in ('workload', 'scenario', 'candidates', 'rack') if k in request}
    kv = analyze(base)  # Validate the unchanged public contract before computing.
    w = base['workload']
    s = base.get('scenario', {})
    phase = w.get('phase', 'decode')
    b = numeric_object(request.get('phase_budget', {}),
                       'resident_state_bytes intermediate_state_bytes training_bytes_per_step training_steps_per_s prefill_other_bw_bytes_s frame_bytes frames_per_s physical_other_bw_bytes_s', 'phase_budget')
    d = kv['demand']
    weights = d['resident_weight_bytes']
    if phase == 'decode':
        components = dict(kv=d['kv_total_bytes'], weights=weights, resident_state=b.get('resident_state_bytes'))
        traffic = dict(kv=d['logical_decode_kv_bw_bytes_s'], active_weights=d['logical_active_weight_bw_bytes_s'])
    elif phase == 'prefill':
        components = dict(kv=d['kv_total_bytes'], weights=weights, resident_state=b.get('resident_state_bytes'))
        traffic = dict(kv_write=d['logical_prefill_kv_write_bw_bytes_s'],
                       active_weights=mul(w.get('active_weight_bytes_per_token'), s.get('weight_multiplier', 1), w.get('input_tokens_per_s')),
                       other=b.get('prefill_other_bw_bytes_s'))
    elif phase == 'training':
        components = dict(weights=weights, activations=w.get('activation_bytes'), optimizer=w.get('optimizer_bytes'))
        traffic = dict(training=mul(b.get('training_bytes_per_step'), b.get('training_steps_per_s')))
    else:
        components = dict(weights=weights, resident_state=b.get('resident_state_bytes'), intermediate_state=b.get('intermediate_state_bytes'))
        traffic = dict(frames=mul(b.get('frame_bytes'), b.get('frames_per_s')), other=b.get('physical_other_bw_bytes_s'))
    capacity, bandwidth = add(*components.values()), add(*traffic.values())
    result = _analyze(base, sizing=(capacity, bandwidth))
    result.update(schema_version=2, analysis='integrated_conditional', phase=phase,
                  kv_only_lower_bound=kv, demand=dict(capacity_bytes=capacity, logical_bw_bytes_s=bandwidth,
                  capacity_components_bytes=components, traffic_components_bytes_s=traffic),
                  ranking_basis='Integrated conditional sizing: modules, modeled rack watts; fully evaluated configured constraints only')
    result['assumptions'] = [
        'Logical explicit phase budgets, not measured bus traffic or achieved performance',
        'Missing budget components propagate unknown; enter explicit zero only when justified',
        'Ideal striping and linear module BW subject to declared rack constraints',
        'Active-weight bytes/token explicitly represents dense or selected MoE experts; resident weights include all resident experts',
        'Training bytes/step includes all declared memory traffic; no automatic weight scaling of this independent budget',
        'Placement can explicitly bind capacity coverage to phase demand; traffic routing and KV-system budgets remain independently declared',
        'required_modules counts candidate objects; preserve object_level and units_per_object for assembly interpretation',
        'No calibrated TTFT, p99, energy, thermal dynamics or allocation optimizer']
    result['placement'] = evaluate_placement(request['placement'], demand_capacity_bytes=capacity) if 'placement' in request else None
    result['kv_system'] = evaluate_kv_system(request['kv_system']) if 'kv_system' in request else None
    return result


def named_rows(value, name):
    if not isinstance(value, list) or len(value) > 10000:
        raise InputError(name + ' must be a list of at most 10000 objects')
    seen = set()
    for row in value:
        if not isinstance(row, dict):
            raise InputError(name + ' entries must be objects')
        key = row.get('id')
        if not isinstance(key, str) or not key.strip() or len(key) > 200 or key in seen:
            raise InputError(name + ' requires unique nonempty IDs (<=200 characters)')
        seen.add(key)
    return value


def evaluate_placement(request, *, demand_capacity_bytes=None):
    """Validate explicitly allocated pool demand and explicitly routed transfers."""
    obj(request, 'pools paths bind_to_demand', 'placement')
    if type(request.get('bind_to_demand', False)) is not bool:
        raise InputError('placement.bind_to_demand must be a boolean')
    number(demand_capacity_bytes, 'demand_capacity_bytes', nullable=True)
    pools, paths = [], []
    for p in named_rows(request.get('pools'), 'pools'):
        obj(p, 'id family capacity_bytes sustained_bw_bytes_s assigned_bytes access_bw_bytes_s', 'pool')
        # Share family validation/exclusion with the stable contract.
        family = p.get('family')
        if not isinstance(family, str):
            raise InputError('pool family must be a string')
        normalized = family.strip().upper()
        excluded = any(x in normalized for x in ('HBF', 'NAND', 'FLASH', 'SSD', 'NVME'))
        if not excluded and normalized not in ('HBM', 'DDR', 'DDR5', 'DDR6', 'DDR7', 'LPDDR', 'LPDDR5X', 'LPDDR6', 'SOCAMM', 'SOCAMM2', 'CXL', 'CXL DRAM', 'DRAM'):
            raise InputError('unsupported pool family')
        for key in ('capacity_bytes', 'sustained_bw_bytes_s', 'assigned_bytes', 'access_bw_bytes_s'):
            number(p.get(key), key, nullable=True)
        constraints = {} if excluded else dict(capacity=check(p.get('assigned_bytes'), p.get('capacity_bytes')), bandwidth=check(p.get('access_bw_bytes_s'), p.get('sustained_bw_bytes_s')))
        pools.append(dict(id=p['id'], family=normalized, status='excluded' if excluded else verdict(constraints), constraints=constraints))
    pool_map = {p['id']: p for p in pools}
    for p in named_rows(request.get('paths'), 'paths'):
        obj(p, 'id source destination traffic_bytes_s bandwidth_bytes_s', 'path')
        if any(not isinstance(p.get(k), str) or p[k] not in pool_map for k in ('source', 'destination')):
            raise InputError('path endpoints must reference declared pools')
        for key in ('traffic_bytes_s', 'bandwidth_bytes_s'):
            number(p.get(key), key, nullable=True)
        excluded = any(pool_map[p[k]]['status'] == 'excluded' for k in ('source', 'destination'))
        constraints = {} if excluded else dict(bandwidth=check(p.get('traffic_bytes_s'), p.get('bandwidth_bytes_s')))
        paths.append(dict(id=p['id'], source=p['source'], destination=p['destination'], status='excluded' if excluded else verdict(constraints), constraints=constraints))
    states = [p['status'] for p in pools + paths]
    status = ('insufficient' if 'insufficient' in states else 'unevaluated' if not pools or any(x in states for x in ('unevaluated', 'excluded')) else 'eligible')
    coverage = None
    if request.get('bind_to_demand', False):
        assigned = add(*(p.get('assigned_bytes') for p in request['pools'] if pool_map[p['id']]['status'] != 'excluded'))
        unassigned = None if demand_capacity_bytes is None or assigned is None else max(0, demand_capacity_bytes - assigned)
        state = 'unevaluated' if unassigned is None else ('pass' if unassigned == 0 else 'fail')
        coverage = dict(required_bytes=demand_capacity_bytes, assigned_bytes=assigned, unassigned_bytes=unassigned,
                        status=state, whole_demand_status='insufficient' if status == 'insufficient' else
                        ('eligible' if state == 'pass' and status == 'eligible' else 'unevaluated'),
                        basis='Declared allocations compared with total phase capacity; traffic coverage is not inferred')
    return dict(status=status, pools=pools, paths=paths, coverage=coverage, whole_system_validated=False,
                assumptions=['Declared pool allocations only; no optimizer or deduplication of replicated bytes', 'Optional capacity coverage requires non-overlapping declared demand allocations', 'Each path is a separate link budget; aggregate shared-link traffic before input', 'Pool access BW must include migration reads/writes where applicable', 'No latency or power inferred from placement'])


def evaluate_kv_system(request):
    b = numeric_object(request, 'sessions metadata_bytes_per_session control_operations_per_s control_bytes_per_operation payload_bw_bytes_s control_link_bw_bytes_s data_link_bw_bytes_s server_metadata_capacity_bytes', 'kv_system')
    number(b.get('sessions'), 'sessions', integer=True, nullable=True)
    metadata = mul(b.get('sessions'), b.get('metadata_bytes_per_session'))
    control = mul(b.get('control_operations_per_s'), b.get('control_bytes_per_operation'))
    payload = b.get('payload_bw_bytes_s')
    modes = {}
    for mode, control_need in (('direct', control), ('relay', add(control, payload))):
        constraints = dict(control_link=check(control_need, b.get('control_link_bw_bytes_s')),
                           data_link=check(payload, b.get('data_link_bw_bytes_s')),
                           metadata_capacity=check(metadata, b.get('server_metadata_capacity_bytes')))
        modes[mode] = dict(status=verdict(constraints), constraints=constraints)
    return dict(metadata_bytes=metadata, control_bw_bytes_s=control, payload_bw_bytes_s=payload,
                modes=modes, p99_ms=None, ttft_ms=None,
                assumptions=['Direct payload bypasses the metadata/control server', 'Relay sends payload plus control over the control link and payload over the data link', 'Traffic inputs are directional logical budgets; include duplex overhead explicitly', 'Missing server metadata capacity leaves the complete mode unevaluated'])


def compare_scenarios(request, scenarios):
    """Evaluate named, dated conditional factors against the same input baseline."""
    obj(request, 'workload scenario candidates rack phase_budget placement kv_system', 'comparison request')
    runs = []
    for item in named_rows(scenarios, 'scenarios'):
        obj(item, 'id year scenario', 'scenario comparison')
        number(item.get('year'), 'year', positive=True, integer=True)
        factors = item.get('scenario')
        if not isinstance(factors, dict):
            raise InputError('scenario factors must be an object')
        q = deepcopy(request)
        q['scenario'] = {**q.get('scenario', {}), **factors}
        runs.append(dict(id=item['id'], year=item['year'], kind='scenario_assumption', request=q, result=analyze_integrated(q)))
    return runs
