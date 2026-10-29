import copy
import unittest

from memory_dsa.api import analyze, InputError
from memory_dsa.catalog import catalog_candidates, public_catalog, gap_schema
from memory_dsa.demo import integrated_example
from memory_dsa.integrated import analyze_integrated, evaluate_placement

G = 2**30


class ExplorationTests(unittest.TestCase):
    def test_public_object_levels_and_lpddr_are_preserved(self):
        candidates = {c['id']: c for c in catalog_candidates()}
        self.assertIn('lpddr6', candidates)
        self.assertEqual(candidates['lpddr6'].get('object_level'), 'die')
        q = integrated_example()
        q['candidates'] = [candidates['hbm4-12h']]
        r = analyze_integrated(q)['candidates'][0]
        self.assertEqual(r['object_level'], 'stack')
        self.assertEqual(r['units_per_object'], 1)
        self.assertIsNone(r['required_objects'])

    def test_explicit_lpddr_assembly_uses_decimal_peak_and_efficiency(self):
        from memory_dsa.exploration import compose_assembly
        r = compose_assembly('lpddr6', 8, id='synthetic-lpddr-assembly',
                             pin_rate_gbit_s=12, bus_width_bits=64,
                             sustained_efficiency=.75, usable_capacity_bytes=15e9)
        self.assertEqual(r['gross_capacity_bytes'], 16e9)
        self.assertEqual(r['usable_capacity_bytes'], 15e9)
        self.assertEqual(r['peak_bw_bytes_s'], 96e9)
        self.assertEqual(r['conditional_sustained_bw_bytes_s'], 72e9)
        self.assertEqual(r['candidate']['object_level'], 'assembly')
        self.assertEqual(r['candidate']['component_object_level'], 'die')
        self.assertEqual(r['candidate']['units_per_object'], 8)
        self.assertEqual(r['candidate']['provenance'], 'scenario_assumption')

    def test_hbm_stacks_unknown_channels_and_no_implicit_sustained(self):
        from memory_dsa.exploration import compose_assembly
        r = compose_assembly('hbm4-12h', 4, id='four-stack-layout')
        self.assertEqual(r['gross_capacity_bytes'], 144e9)
        self.assertEqual(r['component_object_level'], 'stack')
        self.assertIsNone(r['channels'])
        self.assertIsNone(r['conditional_sustained_bw_bytes_s'])
        self.assertIsNone(r['usable_capacity_bytes'])
        r = compose_assembly('hbm5', 4, id='unknown-future-layout')
        self.assertIsNone(r['gross_capacity_bytes'])
        self.assertIsNone(r['peak_bw_bytes_s'])

    def test_assembly_usable_capacity_drives_sizing(self):
        from memory_dsa.exploration import compose_assembly
        c = compose_assembly('lpddr6', 8, id='synthetic-lpddr', pin_rate_gbit_s=12,
                             bus_width_bits=64, sustained_efficiency=.75,
                             usable_capacity_bytes=8*G)['candidate']
        c.update(power_w=1, max_modules=100)
        q = integrated_example();q['workload']['output_tokens_per_s_per_request']=0
        q['candidates']=[c]
        r=analyze_integrated(q)['candidates'][0]
        self.assertEqual(r['required_modules'],8)
        self.assertEqual(r['required_objects'],8)
        self.assertEqual(r['required_components'],64)
        self.assertEqual(r['capacity_basis'],'declared_usable_capacity')

    def test_invalid_assembly_inputs(self):
        from memory_dsa.exploration import compose_assembly
        for kwargs in ({'unit_count':0},{'unit_count':True},{'unit_count':1.5},
                       {'unit_count':8,'sustained_efficiency':1.1},
                       {'unit_count':8,'usable_capacity_bytes':17e9},
                       {'unit_count':8,'pin_rate_gbit_s':float('nan')}):
            with self.assertRaises(InputError):
                compose_assembly('lpddr6',id='test',**kwargs)
        with self.assertRaises(InputError):
            compose_assembly('NAND',8,id='excluded')

    def test_placement_binding_catches_unassigned_future_capacity(self):
        q=integrated_example();q['placement']['bind_to_demand']=True
        before=copy.deepcopy(q)
        r=analyze_integrated(q)
        self.assertEqual(r['placement']['coverage']['unassigned_bytes'],0)
        self.assertEqual(r['placement']['coverage']['status'],'pass')
        self.assertEqual(q,before)
        q['scenario']={'weight_multiplier':3}
        r=analyze_integrated(q)
        self.assertEqual(r['demand']['capacity_bytes'],160*G)
        self.assertEqual(r['placement']['coverage']['assigned_bytes'],64*G)
        self.assertEqual(r['placement']['coverage']['unassigned_bytes'],96*G)
        self.assertEqual(r['placement']['status'],'eligible')
        self.assertEqual(r['placement']['coverage']['whole_demand_status'],'unevaluated')
        q['workload']['resident_weight_bytes']=None
        self.assertIsNone(analyze_integrated(q)['placement']['coverage']['unassigned_bytes'])

    def test_ddr5_public_peak_does_not_become_sustained(self):
        c=next(c for c in public_catalog() if c['id']=='ddr5-rdimm')
        self.assertEqual(c['fields']['capacity_bytes']['value'],128*G)
        self.assertEqual(c['fields']['peak_bw_bytes_s']['value'],51.2e9)
        self.assertIsNone(c['fields']['sustained_bw_bytes_s']['value'])
        self.assertIsNone(c['fields']['channels']['value'])

    def test_unknown_usable_capacity_and_excluded_placement_do_not_fill_gaps(self):
        q=integrated_example()
        q['candidates'][0]['usable_capacity_bytes']=None
        c=analyze_integrated(q)['candidates'][0]
        self.assertIsNone(c['required_objects'])
        self.assertEqual(c['capacity_basis'],'declared_usable_capacity')
        placement=dict(bind_to_demand=True, paths=[], pools=[
            dict(id='flash', family='NAND', capacity_bytes=200*G,
                 sustained_bw_bytes_s=100*G, assigned_bytes=160*G, access_bw_bytes_s=0)])
        r=evaluate_placement(placement,demand_capacity_bytes=160*G)
        self.assertEqual(r['pools'][0]['status'],'excluded')
        self.assertEqual(r['coverage']['assigned_bytes'],0)
        self.assertEqual(r['coverage']['unassigned_bytes'],160*G)
        self.assertEqual(r['coverage']['whole_demand_status'],'unevaluated')

    def test_named_sensitivity_and_fabric_breakpoint(self):
        from memory_dsa.exploration import decision_study
        d=decision_study();rows={r['id']:r for r in d['sensitivity']}
        self.assertEqual((rows['baseline']['capacity_bytes'],rows['baseline']['logical_bw_bytes_s']),(64*G,128*G))
        self.assertEqual((rows['model-growth']['capacity_bytes'],rows['model-growth']['logical_bw_bytes_s'],rows['model-growth']['required_modules']),(160*G,256*G,2))
        self.assertEqual((rows['efficiency-offset']['capacity_bytes'],rows['efficiency-offset']['logical_bw_bytes_s']),(32*G,64*G))
        self.assertEqual(rows['fabric-limited']['required_modules'],1)
        self.assertEqual(rows['fabric-limited']['fabric_status'],'fail')
        self.assertEqual(d['envelope']['kind'],'scenario_range_not_confidence_interval')
        self.assertEqual(decision_study(),d)
        q=copy.deepcopy(d['scenarios'][1]['request'])
        q['rack']['fabric_bw_bytes_s']=256*G
        self.assertEqual(analyze_integrated(q)['candidates'][0]['constraints']['fabric']['status'],'pass')
        q['rack']['fabric_bw_bytes_s']-=1
        self.assertEqual(analyze_integrated(q)['candidates'][0]['constraints']['fabric']['status'],'fail')

    def test_coverage_does_not_claim_unimplemented_gap_fields(self):
        from memory_dsa.exploration import decision_study
        coverage={r['id']:r for r in decision_study()['coverage']}
        for name in ('hbm4-12h','hbm4e-12h','hbm5','ddr6','ddr7','lpddr6',
                     'decode','prefill','training','physical_ai','dense-moe'):
            self.assertIn(name,coverage)
        self.assertEqual(coverage['hbf-nand']['status'],'excluded')
        self.assertEqual(coverage['mla']['status'],'not_implemented')
        gaps={r['name']:r for r in gap_schema()['fields']}
        self.assertEqual(gaps['thermal_throttle_ratio']['implementation_status'],'not_implemented')
        self.assertEqual(gaps['context_distribution']['implementation_status'],'not_implemented')
        self.assertIsNone(gaps['thermal_throttle_ratio']['input_path'])
        self.assertEqual(gaps['prefix_reuse_ratio']['input_path'],'workload.prefix_reuse_ratio')
