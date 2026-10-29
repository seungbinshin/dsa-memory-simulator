"""Strict, offline analytical demand and homogeneous DRAM configuration model."""
import math


class InputError(ValueError):
    """Unsupported or dimensionally invalid request."""


def obj(value, allowed, name):
    if not isinstance(value, dict):
        raise InputError(f'{name} must be an object')
    extra = value.keys() - set(allowed.split())
    if extra:
        raise InputError(f'{name}: unsupported fields {sorted(extra)}')
    return value


def number(value, name, *, positive=False, integer=False, nullable=False):
    if value is None and nullable:
        return None
    if type(value) not in (int, float):
        raise InputError(f'{name} must be a finite number')
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or value < 0 or (positive and value == 0):
        raise InputError(f'{name} must be finite and {"positive" if positive else "nonnegative"}')
    if integer and value != int(value):
        raise InputError(f'{name} must be an integer')
    return value


def mul(*values):
    if None in values:
        return None
    result = math.prod(values)
    return number(result, 'calculated value')


def analyze(request: dict) -> dict:
    """Evaluate conditional KV sizing; does not predict hardware throughput."""
    return _analyze(request)


def _analyze(request, sizing=None):
    """Shared configuration evaluator; integrated sizing is an internal argument."""
    obj(request, 'workload scenario candidates rack', 'request')
    w = obj(request.get('workload'), 'layers kv_heads head_dim bytes_per_element context_tokens concurrency output_tokens_per_s_per_request architecture phase resident_weight_bytes active_weight_bytes_per_token expert_fabric_bytes_per_token activation_bytes optimizer_bytes multimodal_state_bytes input_tokens_per_s prefix_reuse_ratio metadata_bytes_per_request control_operations_per_s control_bytes_per_operation', 'workload')
    required = 'layers kv_heads head_dim bytes_per_element context_tokens concurrency output_tokens_per_s_per_request'.split()
    for key in required:
        if key not in w:
            raise InputError(f'workload.{key} is required')
        number(w[key], key, positive=key != required[-1], integer=key in ('layers', 'kv_heads', 'head_dim', 'context_tokens', 'concurrency'))
    if w.get('architecture', 'gqa') not in ('gqa', 'mha', 'moe_gqa'):
        raise InputError('architecture requires explicit supported GQA/MHA KV structure')
    if w.get('phase', 'decode') not in ('decode', 'prefill', 'training', 'physical_ai'):
        raise InputError('unsupported phase')
    optional = set(w) - set(required) - {'architecture', 'phase'}
    for key in optional:
        number(w[key], key, nullable=True)
    if w.get('prefix_reuse_ratio') is not None and w['prefix_reuse_ratio'] > 1:
        raise InputError('prefix_reuse_ratio must be <= 1')
    s = obj(request.get('scenario', {}), 'context_multiplier concurrency_multiplier kv_bytes_multiplier layers_multiplier weight_multiplier technology_capacity_multiplier technology_bw_multiplier technology_power_multiplier', 'scenario')
    for key, value in s.items():
        number(value, key, positive=True)
    sm = lambda key: s.get(key + '_multiplier', 1)
    context = mul(w['context_tokens'], sm('context'))
    concurrency = mul(w['concurrency'], sm('concurrency'))
    token = mul(2, w['layers'], sm('layers'), w['kv_heads'], w['head_dim'], w['bytes_per_element'], sm('kv_bytes'))
    per_request = mul(token, context)
    total = mul(per_request, concurrency)
    bw = mul(total, w['output_tokens_per_s_per_request'])
    tps = mul(concurrency, w['output_tokens_per_s_per_request'])
    expert_tps = tps
    if sizing is not None and w.get('phase', 'decode') != 'decode':
        expert_tps = w.get('input_tokens_per_s') if w['phase'] == 'prefill' else None
    demand = dict(kv_bytes_per_token=token, kv_bytes_per_request=per_request, kv_total_bytes=total, logical_decode_kv_bw_bytes_s=bw,
                  effective_context_tokens=context, effective_concurrency=concurrency,
                  resident_weight_bytes=mul(w.get('resident_weight_bytes'), sm('weight')),
                  logical_active_weight_bw_bytes_s=mul(w.get('active_weight_bytes_per_token'), sm('weight'), tps),
                  expert_fabric_bw_bytes_s=mul(w.get('expert_fabric_bytes_per_token'), expert_tps),
                  logical_prefill_kv_write_bw_bytes_s=mul(token, w.get('input_tokens_per_s'), None if w.get('prefix_reuse_ratio') is None else 1-w['prefix_reuse_ratio']),
                  metadata_bytes=mul(w.get('metadata_bytes_per_request'), concurrency),
                  control_bw_bytes_s=mul(w.get('control_operations_per_s'), w.get('control_bytes_per_operation')),
                  activation_bytes=w.get('activation_bytes'), optimizer_bytes=w.get('optimizer_bytes'), multimodal_state_bytes=w.get('multimodal_state_bytes'))
    phase = w.get('phase', 'decode')
    if sizing is not None:
        total, bw = sizing
        phase = 'decode'
    demand['training_state_bytes'] = (number(demand['resident_weight_bytes'] + w['activation_bytes'] + w['optimizer_bytes'], 'training state')
                                      if all(w.get(k) is not None for k in ('resident_weight_bytes', 'activation_bytes', 'optimizer_bytes')) else None)
    rack = obj(request.get('rack'), 'base_power_w power_limit_w fabric_bw_bytes_s max_channels psu_efficiency psu_capacity_w cooling_limit_w scale_up_bw_bytes_s scale_out_bw_bytes_s control_bw_bytes_s latency_slo_ns', 'rack')
    for key, value in rack.items():
        number(value, key, nullable=True, positive=key == 'psu_efficiency', integer=key == 'max_channels')
    if rack.get('psu_efficiency') is not None and rack['psu_efficiency'] > 1:
        raise InputError('psu_efficiency must be <= 1')
    candidates = request.get('candidates')
    if not isinstance(candidates, list) or len(candidates) > 10000:
        raise InputError('candidates must be a list of at most 10000 objects')
    results, ids = [], set()
    for c in candidates:
        obj(c, 'id family capacity_bytes usable_capacity_bytes sustained_bw_bytes_s power_w max_modules channels_per_module p99_latency_ns provenance object_level component_object_level units_per_object', 'candidate')
        cid, family = c.get('id'), c.get('family')
        if not isinstance(cid, str) or not cid.strip() or len(cid) > 200 or cid in ids:
            raise InputError('candidate id must be a unique nonempty string (<=200 characters)')
        ids.add(cid)
        if not isinstance(family, str):
            raise InputError('family must be a string')
        family = family.upper().strip()
        excluded = any(x in family for x in ('HBF', 'NAND', 'FLASH', 'SSD', 'NVME'))
        if not excluded and family not in ('HBM', 'DDR', 'DDR5', 'DDR6', 'DDR7', 'LPDDR', 'LPDDR5X', 'LPDDR6', 'SOCAMM', 'SOCAMM2', 'CXL', 'CXL DRAM', 'DRAM'):
            raise InputError(f'unsupported memory family: {family}')
        for key in ('capacity_bytes', 'usable_capacity_bytes', 'sustained_bw_bytes_s', 'power_w', 'max_modules', 'channels_per_module', 'p99_latency_ns'):
            number(c.get(key), key, nullable=True, positive=key in ('capacity_bytes', 'usable_capacity_bytes', 'sustained_bw_bytes_s', 'channels_per_module'), integer=key in ('max_modules', 'channels_per_module'))
        if c.get('usable_capacity_bytes') is not None and c.get('capacity_bytes') is not None and c['usable_capacity_bytes'] > c['capacity_bytes']:
            raise InputError('usable capacity cannot exceed declared gross capacity')
        level = c.get('object_level', 'module')
        component_level = c.get('component_object_level', level)
        if level not in ('die', 'stack', 'package', 'module', 'assembly') or component_level not in ('die', 'stack', 'package', 'module', 'assembly'):
            raise InputError('unsupported candidate object level')
        units = number(c.get('units_per_object', 1), 'units_per_object', positive=True, integer=True)
        provenance = c.get('provenance', 'user_supplied_unverified')
        if not isinstance(provenance, str) or provenance not in ('user_supplied_unverified', 'synthetic_test', 'scenario_assumption', 'public_catalog', 'local_override'):
            raise InputError('unsupported candidate provenance')
        r = dict(id=cid, family=family, status='unevaluated', required_modules=None, required_objects=None,
                 required_components=None, object_level=level, component_object_level=component_level,
                 units_per_object=units, gross_capacity_bytes=c.get('capacity_bytes'), usable_capacity_bytes=c.get('usable_capacity_bytes'),
                 capacity_basis='declared_usable_capacity' if 'usable_capacity_bytes' in c else 'declared_capacity',
                 required_channels=None, rack_power_w=None, wall_power_w=None, constraints={}, reasons=[], provenance=provenance)
        results.append(r)
        if excluded:
            r.update(status='excluded', reasons=['Positioning only; excluded from analysis and ranking'])
            continue
        capacity = mul(c.get('usable_capacity_bytes') if 'usable_capacity_bytes' in c else c.get('capacity_bytes'), sm('technology_capacity'))
        bandwidth = mul(c.get('sustained_bw_bytes_s'), sm('technology_bw'))
        if capacity is None or bandwidth is None or total is None or bw is None or phase != 'decode':
            r['reasons'].append('Essential capacity/sustained BW missing or phase sizing unsupported')
            if sizing is not None:
                bounds = [math.ceil(need / unit) for need, unit in ((total, capacity), (bw, bandwidth)) if need is not None and unit is not None]
                lower = max(bounds) if bounds else None
                r['known_module_lower_bound'] = lower
                for name, need, limit in (('modules_lower_bound', lower, c.get('max_modules')), ('fabric', bw, rack.get('fabric_bw_bytes_s'))):
                    state = 'unevaluated' if need is None or limit is None else ('pass' if need <= limit else 'fail')
                    r['constraints'][name] = dict(status=state, required=need, limit=limit)
                    if state == 'fail':
                        r['status'] = 'insufficient'
                        r['reasons'].append('Violated known constraint: ' + name)
            continue
        n = max(math.ceil(total / capacity), math.ceil(bw / bandwidth))
        r['required_modules'] = n
        r['required_objects'] = n
        r['required_components'] = mul(n, units)
        r['required_channels'] = mul(n, c.get('channels_per_module'))
        memory_power = mul(n, c.get('power_w'), sm('technology_power'))
        if memory_power is not None and rack.get('base_power_w') is not None:
            r['rack_power_w'] = number(memory_power + rack['base_power_w'], 'rack power')
        if r['rack_power_w'] is not None and rack.get('psu_efficiency') is not None:
            r['wall_power_w'] = number(r['rack_power_w'] / rack['psu_efficiency'], 'wall power')
        def constraint(name, needed, limit):
            status = 'unevaluated' if needed is None or limit is None else ('pass' if needed <= limit else 'fail')
            r['constraints'][name] = dict(status=status, required=needed, limit=limit)
        constraint('modules', n, c.get('max_modules'))
        constraint('fabric', bw, rack.get('fabric_bw_bytes_s'))
        constraint('rack_power', r['rack_power_w'], rack.get('power_limit_w'))
        for name, needed, limit in (
            ('channels', r['required_channels'], rack.get('max_channels')),
            ('psu', r['wall_power_w'], rack.get('psu_capacity_w')),
            ('cooling', r['rack_power_w'], rack.get('cooling_limit_w')),
            ('latency', c.get('p99_latency_ns'), rack.get('latency_slo_ns')),
            ('scale_up', demand['expert_fabric_bw_bytes_s'], rack.get('scale_up_bw_bytes_s')),
            ('scale_out', bw, rack.get('scale_out_bw_bytes_s')),
            ('control', demand['control_bw_bytes_s'], rack.get('control_bw_bytes_s'))):
            if limit is not None:
                constraint(name, needed, limit)
        failed = [k for k, v in r['constraints'].items() if v['status'] == 'fail']
        unknown = [k for k, v in r['constraints'].items() if v['status'] == 'unevaluated']
        r['status'] = 'insufficient' if failed else 'eligible'
        r['reasons'] = ['Violated: ' + k for k in failed] + ['Not evaluated: ' + k for k in unknown]
        r['ranking_eligible'] = not failed and not unknown
        r['whole_system_validated'] = False
        r['reasons'].append(('Integrated' if sizing is not None else 'KV-only') + ' homogeneous sizing; latency/thermal/placement not validated')
    ranked = sorted((r for r in results if r.get('ranking_eligible')), key=lambda r: (r['required_modules'], r['rack_power_w'], r['id']))
    return dict(schema_version=1, demand=demand, candidates=results,
                ranking=[r['id'] for r in ranked], ranking_basis='Conditional KV sizing: modules, then modeled rack watts; only fully evaluated configured constraints',
                comparison_conclusive=bool(ranked) and all(r.get('ranking_eligible') or r['status'] in ('excluded', 'insufficient') for r in results),
                scenario={k: s.get(k, 1) for k in 'context_multiplier concurrency_multiplier kv_bytes_multiplier layers_multiplier weight_multiplier technology_capacity_multiplier technology_bw_multiplier technology_power_multiplier'.split()},
                predictions=dict(ttft_ms=None, itl_ms=None, p99_ms=None, tokens_per_joule=None),
                assumptions=['Logical full KV scan per generated token; not physical bus traffic', 'Perfect capacity striping and linear object BW before explicit fabric ceilings', 'required_modules is the compatibility name for required_objects; retain object_level when comparing counts', 'Declared capacity is gross unless usable_capacity_bytes is explicitly supplied; no automatic usable fraction', 'No quantization metadata, fragmentation, replication or placement overhead', 'Unknown constraints are not passed; eligibility is conditional KV capacity/BW only', 'No calibrated latency, power, cooling or performance prediction'])
