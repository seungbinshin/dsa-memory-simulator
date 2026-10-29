"""Deterministic examples and self-contained HTML; writes only to requested output."""
import csv
import hashlib
import json
from pathlib import Path
from .api import analyze
from .catalog import public_catalog, catalog_candidates, gap_schema, roadmap_context, source_registry
from .integrated import analyze_integrated, compare_scenarios
from .exploration import decision_study
from .report import render_report


def encode(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def baseline():
    return dict(workload=dict(layers=80, kv_heads=8, head_dim=128, bytes_per_element=2, context_tokens=131072, concurrency=64, output_tokens_per_s_per_request=20),
                scenario={}, candidates=[dict(id='synthetic-hbm', family='HBM', capacity_bytes=68719476736, sustained_bw_bytes_s=10**12, power_w=50, max_modules=100, channels_per_module=1, provenance='synthetic_test')] + catalog_candidates(),
                rack=dict(base_power_w=1000, power_limit_w=20000, fabric_bw_bytes_s=100e12, max_channels=100))


def integrated_example():
    """Synthetic owner arithmetic examples; no product specification claims."""
    g = 2**30
    q = baseline()
    q['workload'] = dict(layers=1, kv_heads=1, head_dim=1, bytes_per_element=1,
                         context_tokens=8*g, concurrency=1, output_tokens_per_s_per_request=4,
                         resident_weight_bytes=48*g, active_weight_bytes_per_token=16*g)
    q['phase_budget'] = dict(resident_state_bytes=0)
    q['candidates'] = [dict(id='synthetic-integrated', family='HBM', capacity_bytes=256*g,
                            sustained_bw_bytes_s=128*g, power_w=50, max_modules=10,
                            channels_per_module=1, provenance='synthetic_test')] + catalog_candidates()
    q['placement'] = dict(pools=[dict(id='hot', family='HBM', capacity_bytes=32*g, sustained_bw_bytes_s=128*g, assigned_bytes=16*g, access_bw_bytes_s=72*g),
                                  dict(id='warm', family='CXL DRAM', capacity_bytes=64*g, sustained_bw_bytes_s=32*g, assigned_bytes=48*g, access_bw_bytes_s=8*g)],
                          paths=[dict(id='migration', source='hot', destination='warm', traffic_bytes_s=8*g, bandwidth_bytes_s=10*g)])
    q['kv_system'] = dict(sessions=100, metadata_bytes_per_session=2**20, control_operations_per_s=100,
                          control_bytes_per_operation=1024, payload_bw_bytes_s=8*g,
                          control_link_bw_bytes_s=2**20, data_link_bw_bytes_s=10*g, server_metadata_capacity_bytes=128*2**20)
    return q


def integrated_runs():
    q = integrated_example()
    runs = compare_scenarios(q, [dict(id='integrated-baseline', year=2026, scenario={}),
                                 dict(id='model-growth', year=2028, scenario={'weight_multiplier': 3}),
                                 dict(id='technology-offset', year=2030, scenario={'weight_multiplier': 3, 'technology_bw_multiplier': 2})])
    for phase in ('training', 'prefill', 'physical_ai'):
        q = integrated_example()
        q['workload']['phase'] = phase
        if phase == 'training':
            q['candidates'][0]['capacity_bytes'] = 64*2**30
            q['workload'].update(resident_weight_bytes=40*2**30, activation_bytes=8*2**30, optimizer_bytes=80*2**30)
            q['phase_budget'] = dict(training_bytes_per_step=256*2**30, training_steps_per_s=2)
        elif phase == 'prefill':
            q['workload'].update(input_tokens_per_s=1024, prefix_reuse_ratio=.5)
            q['phase_budget'].update(prefill_other_bw_bytes_s=0)
        else:
            q['phase_budget'] = dict(resident_state_bytes=2**30, intermediate_state_bytes=2**30,
                                     frame_bytes=8*2**20, frames_per_s=30, physical_other_bw_bytes_s=0)
        runs.append(dict(id=phase, year=2026, kind='synthetic_test', request=q, result=analyze_integrated(q)))
    for run in runs:
        run['input_sha256'] = hashlib.sha256(encode(run['request']).encode()).hexdigest()
    return runs


def demo(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    presets = [('baseline', 2026, {}), ('conservative', 2027, dict(context_multiplier=2, concurrency_multiplier=1.25, kv_bytes_multiplier=.5)),
               ('base', 2028, dict(context_multiplier=4, concurrency_multiplier=2, layers_multiplier=1.25, technology_bw_multiplier=1.5, technology_capacity_multiplier=2)),
               ('accelerated', 2030, dict(context_multiplier=8, concurrency_multiplier=4, layers_multiplier=1.5, technology_bw_multiplier=2, technology_capacity_multiplier=4, technology_power_multiplier=1.2)),
               ('efficiency-offset', 2030, dict(context_multiplier=2, kv_bytes_multiplier=.25, technology_bw_multiplier=1.5))]
    runs = []
    for name, year, scenario in presets:
        request = baseline()
        request['scenario'] = scenario
        runs.append(dict(name=name, year=year, kind='synthetic_test' if name == 'baseline' else 'scenario_assumption', request=request, input_sha256=hashlib.sha256(encode(request).encode()).hexdigest(), result=analyze(request)))
    data = dict(schema_version=1, scenarios=runs, catalog=public_catalog(), public_context=roadmap_context(), internal_gaps=gap_schema(), positioning='HBF/NAND/flash/SSD: positioning only; excluded from analysis, rankings and measurement requests', limitations='Conditional analytical sensitivity, not forecasts or measured hardware performance. Years and presets are configurable example choices.')
    data['sources'] = source_registry()
    data['integrated_scenarios'] = integrated_runs()
    data['decision_study'] = decision_study()
    (output/'results.json').write_text(encode(data), encoding='utf-8')
    (output/'baseline-request.json').write_text(encode(baseline()), encoding='utf-8')
    (output/'integrated-request.json').write_text(encode(integrated_example()), encoding='utf-8')
    (output/'internal-gap-schema.json').write_text(encode(gap_schema()), encoding='utf-8')
    columns = ['scenario', 'year', 'kind', 'kv_total_bytes', 'logical_decode_kv_bw_bytes_s', 'id', 'status', 'required_modules', 'rack_power_w', 'reasons']
    with (output/'results.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        for run in runs:
            for c in run['result']['candidates']:
                writer.writerow(dict(scenario=run['name'], year=run['year'], kind=run['kind'], **{k: run['result']['demand'][k] for k in columns[3:5]}, **{k: c.get(k) for k in columns[5:-1]}, reasons='; '.join(c['reasons'])))
    # A normalized companion table preserves every phase, pool and path constraint.
    integrated_rows = []
    for run in data['integrated_scenarios']:
        r = run['result']
        common = dict(scenario=run['id'], year=run['year'], phase=r['phase'], kind=run['kind'])
        for c in r['candidates']:
            integrated_rows.append(dict(common, section='phase', id=c['id'], status=c['status'], capacity_bytes=r['demand']['capacity_bytes'], logical_bw_bytes_s=r['demand']['logical_bw_bytes_s'], required_modules=c['required_modules'], constraints=encode(c['constraints']).strip()))
        for section in ('pools', 'paths'):
            for c in r['placement'][section]:
                integrated_rows.append(dict(common, section=section, id=c['id'], status=c['status'], constraints=encode(c['constraints']).strip()))
        for mode, c in r['kv_system']['modes'].items():
            integrated_rows.append(dict(common, section='control_data', id=mode, status=c['status'], constraints=encode(c['constraints']).strip()))
    fields = ['scenario', 'year', 'phase', 'kind', 'section', 'id', 'status', 'capacity_bytes', 'logical_bw_bytes_s', 'required_modules', 'constraints']
    with (output/'integrated-results.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(integrated_rows)
    study = data['decision_study']
    for name, records in [('decision-coverage', study['coverage']), ('sensitivity', study['sensitivity'])]:
        columns = sorted({key for row in records for key in row})
        with (output/(name+'.csv')).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, lineterminator='\n')
            writer.writeheader()
            writer.writerows({k: encode(v).strip() if isinstance(v, (dict, list)) else v for k,v in row.items()} for row in records)
    (output/'assembly-examples.json').write_text(encode(study['assembly_examples']), encoding='utf-8')
    (output/'index.html').write_text(render_report(data)+'\n', encoding='utf-8')
    return data
