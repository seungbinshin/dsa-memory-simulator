"""Small deterministic decision studies with explicit synthetic assumptions.

No hardware calibration, package topology inference or private specifications.
Public component facts and user-selected assembly assumptions stay separate.
"""
from .api import InputError, mul, number
from .catalog import public_catalog, gap_schema
from .integrated import analyze_integrated


def compose_assembly(component_id, unit_count, *, id, pin_rate_gbit_s=None,
                     bus_width_bits=None, sustained_efficiency=None,
                     usable_capacity_bytes=None, channels=None):
    """Compose capacity and an optional declared aggregate electrical BW budget.

    bus_width_bits is the whole assembly's payload width, not width per die.
    It is never multiplied by unit_count. Vendor component peak is aggregated
    only when no electrical override is supplied; it remains a theoretical bound.
    """
    components = {c['id']: c for c in public_catalog()}
    if not isinstance(component_id, str) or component_id not in components:
        raise InputError('component_id must name a public DRAM catalog component')
    if not isinstance(id, str) or not id.strip() or len(id) > 200:
        raise InputError('assembly id must be a nonempty string (<=200 characters)')
    number(unit_count, 'unit_count', positive=True, integer=True)
    number(pin_rate_gbit_s, 'pin_rate_gbit_s', positive=True, nullable=True)
    number(bus_width_bits, 'bus_width_bits', positive=True, integer=True, nullable=True)
    number(sustained_efficiency, 'sustained_efficiency', positive=True, nullable=True)
    number(usable_capacity_bytes, 'usable_capacity_bytes', positive=True, nullable=True)
    number(channels, 'channels', positive=True, integer=True, nullable=True)
    if sustained_efficiency is not None and sustained_efficiency > 1:
        raise InputError('sustained_efficiency must be <= 1')
    if (pin_rate_gbit_s is None) != (bus_width_bits is None):
        raise InputError('pin_rate_gbit_s and aggregate bus_width_bits must be supplied together')
    c = components[component_id]
    gross = mul(c['fields']['capacity_bytes']['value'], unit_count)
    if gross is not None and usable_capacity_bytes is not None and usable_capacity_bytes > gross:
        raise InputError('usable capacity cannot exceed gross assembly capacity')
    if pin_rate_gbit_s is not None:
        peak = mul(pin_rate_gbit_s, 1e9, bus_width_bits, 1/8)
        peak_basis = 'Declared scenario rate x total assembly payload width / 8; no public pin-rate substitution'
    else:
        peak = mul(c['fields']['peak_bw_bytes_s']['value'], unit_count)
        peak_basis = 'Sum of published component theoretical peaks under an explicit ideal independent-interface assumption'
    sustained = mul(peak, sustained_efficiency)
    candidate = dict(id=id, family=c['family'], object_level='assembly', component_object_level=c['object_level'],
                     units_per_object=unit_count, capacity_bytes=gross, sustained_bw_bytes_s=sustained,
                     power_w=None, max_modules=None, channels_per_module=channels, provenance='scenario_assumption')
    if usable_capacity_bytes is not None:
        candidate['usable_capacity_bytes'] = usable_capacity_bytes
    return dict(id=id, component_id=component_id, component_object_level=c['object_level'],
                unit_count=unit_count, object_level='assembly', gross_capacity_bytes=gross,
                usable_capacity_bytes=usable_capacity_bytes, peak_bw_bytes_s=peak,
                conditional_sustained_bw_bytes_s=sustained, channels=channels,
                kind='scenario_assumption', candidate=candidate,
                input_assumptions=dict(pin_rate_gbit_s=pin_rate_gbit_s, bus_width_bits=bus_width_bits,
                                       sustained_efficiency=sustained_efficiency),
                assumptions=[peak_basis, 'Component count is an assembly scenario, not a validated package or supported board',
                             'Sustained BW exists only with explicit efficiency; efficiency is not a measurement',
                             'Gross capacity is preserved; usable capacity is unknown unless explicitly supplied',
                             'I/O width does not imply host channels; channels stay unknown unless explicitly supplied',
                             'All capacity/BW sums ignore controller, routing, thermal and packaging limitations'])


def requirement_coverage():
    """Machine-readable implementation and evidence boundaries, not a pass score."""
    rows = []
    for c in public_catalog():
        missing = [k for k in ('capacity_bytes', 'sustained_bw_bytes_s', 'power_w', 'channels')
                   if c['fields'][k]['value'] is None]
        rows.append(dict(id=c['id'], axis='memory_family', status='partial_public_evidence' if c['fields']['capacity_bytes']['value'] is not None else 'unknown',
                         input_paths=['candidates[].capacity_bytes', 'candidates[].sustained_bw_bytes_s', 'candidates[].power_w', 'candidates[].channels_per_module'],
                         calculation='Conditional object sizing retains ' + c['object_level'] + ' unit basis',
                         limitations=['Unknown fields: ' + ', '.join(missing), 'Missing evidence is not evidence of poor performance'],
                         code_paths=['memory_dsa/catalog.py:public_catalog', 'memory_dsa/api.py:_analyze'],
                         result_paths=['catalog[]', 'integrated_scenarios[].result.candidates[]']))
    definitions = [
        ('decode', 'phase', ['workload.resident_weight_bytes', 'workload.active_weight_bytes_per_token', 'workload.context_tokens', 'phase_budget.resident_state_bytes'],
         'Resident weights + KV + explicit resident state; full logical KV scan and active-weight bytes per generated token', 'No measured bus amplification or latency'),
        ('prefill', 'phase', ['workload.input_tokens_per_s', 'workload.prefix_reuse_ratio', 'phase_budget.prefill_other_bw_bytes_s'],
         'Input tokens/s x new-KV bytes/token x (1-prefix reuse), active-weight traffic and explicit other traffic', 'Prefix reuse changes prefill writes only; cannot infer decode capacity sharing'),
        ('training', 'phase', ['workload.resident_weight_bytes', 'workload.activation_bytes', 'workload.optimizer_bytes', 'phase_budget.training_bytes_per_step', 'phase_budget.training_steps_per_s'],
         'Weights + activations + optimizer capacity; bytes/step x steps/s traffic', 'No automatic optimizer, gradient, collective or checkpoint traffic inference'),
        ('physical_ai', 'phase', ['phase_budget.resident_state_bytes', 'phase_budget.intermediate_state_bytes', 'phase_budget.frame_bytes', 'phase_budget.frames_per_s', 'phase_budget.physical_other_bw_bytes_s'],
         'Resident weights/states/intermediates; frame bytes x frames/s plus explicit other traffic', 'Sensor, temporal reuse and control-loop scheduling must be budgeted by caller'),
        ('dense-moe', 'model_architecture', ['workload.resident_weight_bytes', 'workload.active_weight_bytes_per_token', 'workload.expert_fabric_bytes_per_token'],
         'Separate all-resident expert capacity from active expert bytes/token and expert link traffic', 'Explicit budgets only; no model-name lookup, routing imbalance or automatic dense/MoE architecture inference'),
        ('rack-power-psu', 'infrastructure', ['candidates[].power_w', 'rack.base_power_w', 'rack.power_limit_w', 'rack.psu_efficiency', 'rack.psu_capacity_w', 'rack.cooling_limit_w'],
         'Object count x watts + rack base; wall power = rack power / efficiency; declared ceilings', 'Static budget only; no transient, temperature, PSU redundancy or dynamic throttling model'),
        ('heterogeneous-placement', 'topology', ['placement.pools', 'placement.paths', 'placement.bind_to_demand'],
         'Per-pool capacity/BW and declared migration paths; optional total-demand capacity coverage', 'No optimizer, shared-link discovery or inferred end-to-end traffic coverage'),
        ('kv-control-data', 'topology', ['kv_system.control_operations_per_s', 'kv_system.control_bytes_per_operation', 'kv_system.payload_bw_bytes_s', 'kv_system.server_metadata_capacity_bytes'],
         'Compare direct data bypass with relay: metadata capacity, control BW, payload links', 'Independent declared traffic budgets; latency and service implementation are unknown'),
        ('future-demand', 'sensitivity', ['scenario.weight_multiplier', 'scenario.kv_bytes_multiplier', 'scenario.context_multiplier', 'scenario.technology_bw_multiplier'],
         'Named growth, efficiency and technology factors with capacity/BW/module/fabric deltas', 'Conditional scenario envelope, not a dated forecast or probability distribution'),
    ]
    for name, axis, paths, calculation, limit in definitions:
        rows.append(dict(id=name, axis=axis, status='conditional_arithmetic', input_paths=paths,
                         calculation=calculation, limitations=[limit],
                         code_paths=['memory_dsa/integrated.py:analyze_integrated' if axis == 'phase' else 'memory_dsa/api.py:_analyze',
                                     'memory_dsa/integrated.py'],
                         result_paths=['integrated_scenarios[].result', 'decision_study.scenarios[].result']))
    rows += [dict(id='mla', axis='model_architecture', status='not_implemented', input_paths=[],
                  calculation=None, limitations=['MLA needs explicit latent-cache and reconstruction traffic inputs; GQA formula must not be reused']),
             dict(id='hbf-nand', axis='scope', status='excluded', input_paths=[], calculation=None,
                  limitations=['Positioning only; excluded from sizing, ranking and internal input requests'])]
    for gap in gap_schema()['fields']:
        rows.append(dict(id='gap-' + gap['name'], axis='internal_gap', status=gap['implementation_status'],
                         input_paths=[gap['input_path']] if gap['input_path'] else [],
                         calculation='Caller supplies a documented value under the stated measurement conditions' if gap['input_path'] else None,
                         limitations=[gap['conditions'], 'No private input collected; default remains null']))
    return rows


def _study_request():
    g = 2**30
    return dict(workload=dict(layers=1, kv_heads=1, head_dim=1, bytes_per_element=1,
                             context_tokens=8*g, concurrency=1, output_tokens_per_s_per_request=4,
                             resident_weight_bytes=48*g, active_weight_bytes_per_token=16*g),
                phase_budget=dict(resident_state_bytes=0), scenario={},
                candidates=[dict(id='synthetic-balanced', family='DRAM', object_level='module', capacity_bytes=256*g,
                                 sustained_bw_bytes_s=128*g, power_w=50, max_modules=10,
                                 channels_per_module=1, provenance='synthetic_test'),
                            dict(id='synthetic-capacity-rich', family='DRAM', object_level='module', capacity_bytes=512*g,
                                 sustained_bw_bytes_s=64*g, power_w=20, max_modules=10,
                                 channels_per_module=1, provenance='synthetic_test')],
                rack=dict(base_power_w=1000, power_limit_w=20000, fabric_bw_bytes_s=1024*g, max_channels=100),
                placement=dict(bind_to_demand=True,
                    pools=[dict(id='hot', family='HBM', capacity_bytes=32*g, sustained_bw_bytes_s=128*g, assigned_bytes=16*g, access_bw_bytes_s=72*g),
                           dict(id='warm', family='CXL DRAM', capacity_bytes=64*g, sustained_bw_bytes_s=32*g, assigned_bytes=48*g, access_bw_bytes_s=8*g)],
                    paths=[dict(id='migration', source='hot', destination='warm', traffic_bytes_s=8*g, bandwidth_bytes_s=10*g)]))


def decision_study():
    """Return serializable named requests, computed results and coverage records."""
    g = 2**30
    definitions = [
        ('baseline', 'Synthetic baseline', {}, None, ['All multipliers 1; KV 16 GiB and resident weights 48 GiB']),
        ('model-growth', 'Larger resident and active weights', {'weight_multiplier': 3}, None, ['Resident and active-weight bytes scale together by 3; KV unchanged']),
        ('efficiency-offset', 'Weight and KV precision reduction', {'weight_multiplier': .5, 'kv_bytes_multiplier': .5}, None,
         ['Weight and KV bytes scale by 0.5; quantization metadata and residual buffers excluded']),
        ('fabric-limited', 'Technology BW cannot fix fabric ceiling', {'weight_multiplier': 3, 'technology_bw_multiplier': 2}, 192*g,
         ['Memory object BW doubles; fabric ceiling remains a separately declared 192 GiB/s']),
    ]
    scenarios, sensitivity = [], []
    for sid, label, factors, fabric, assumptions in definitions:
        request = _study_request()
        request['scenario'] = factors
        if fabric is not None:
            request['rack']['fabric_bw_bytes_s'] = fabric
        result = analyze_integrated(request)
        d, candidate = result['demand'], result['candidates'][0]
        capacity_ratio, bw_ratio = d['capacity_bytes']/(64*g), d['logical_bw_bytes_s']/(128*g)
        scenarios.append(dict(id=sid, label=label, kind='synthetic_test' if sid == 'baseline' else 'scenario_assumption',
                              assumptions=assumptions, request=request, result=result,
                              capacity_ratio=capacity_ratio, bw_ratio=bw_ratio))
        sensitivity.append(dict(id=sid, label=label, capacity_bytes=d['capacity_bytes'], logical_bw_bytes_s=d['logical_bw_bytes_s'],
                                required_modules=candidate['required_modules'], fabric_status=candidate['constraints']['fabric']['status'],
                                capacity_ratio=capacity_ratio, bw_ratio=bw_ratio, candidate_id=candidate['id']))
    return dict(schema_version=1, kind='synthetic_test', scenarios=scenarios, sensitivity=sensitivity,
                assumptions=['All profiles, workloads, rates and efficiency factors are illustrative synthetic inputs, not product recommendations',
                             'Two generic profiles expose module-count versus static-watt tradeoffs; physical compatibility is not checked',
                             'Sensitivity rows refer to synthetic-balanced; full candidate comparisons are in each scenario result',
                             'Year selection and factor ranges are configurable modeling choices, not measured trends'],
                coverage=requirement_coverage(),
                assembly_examples=[compose_assembly('lpddr6', 8, id='synthetic-eight-die-lpddr6', pin_rate_gbit_s=12, bus_width_bits=64, sustained_efficiency=.75),
                                   compose_assembly('hbm4-12h', 4, id='conditional-four-hbm4-stacks'),
                                   compose_assembly('hbm5', 4, id='unknown-four-hbm5-stacks')],
                envelope=dict(kind='scenario_range_not_confidence_interval',
                              capacity_bytes=dict(min=min(r['capacity_bytes'] for r in sensitivity), max=max(r['capacity_bytes'] for r in sensitivity)),
                              logical_bw_bytes_s=dict(min=min(r['logical_bw_bytes_s'] for r in sensitivity), max=max(r['logical_bw_bytes_s'] for r in sensitivity))),
                breakpoints=[dict(id='balanced-one-object-weight-limit', input_path='scenario.weight_multiplier', value=1,
                                  unit='multiplier', basis='BW 64 + 64*weight GiB/s reaches the declared 128 GiB/s object BW at 1; capacity is not binding'),
                             dict(id='growth-fabric-minimum', input_path='rack.fabric_bw_bytes_s', value=256*g,
                                  unit='B/s', basis='Model-growth logical demand; equality passes, any lower declared fabric ceiling fails'),
                             dict(id='growth-one-object-bw-factor', input_path='scenario.technology_bw_multiplier', value=2,
                                  unit='multiplier', basis='256/128 bandwidth factor; independent fabric, power and channels constraints still apply')])
