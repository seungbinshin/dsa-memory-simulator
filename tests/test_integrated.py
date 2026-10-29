import copy
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from memory_dsa.api import InputError
from memory_dsa.demo import integrated_example, integrated_runs, demo
from memory_dsa.integrated import analyze_integrated, evaluate_placement, evaluate_kv_system, compare_scenarios

G = 2**30
ROOT = Path(__file__).resolve().parents[1]


class IntegratedTests(unittest.TestCase):
    def test_prefill_expert_fabric_uses_input_token_rate(self):
        q = integrated_example()
        q['workload'].update(phase='prefill', architecture='moe_gqa',
                            output_tokens_per_s_per_request=0, input_tokens_per_s=1000,
                            prefix_reuse_ratio=0, active_weight_bytes_per_token=0,
                            expert_fabric_bytes_per_token=2**20)
        q['phase_budget']['prefill_other_bw_bytes_s'] = 0
        q['rack']['scale_up_bw_bytes_s'] = 512*2**20
        r = analyze_integrated(q)
        c = r['candidates'][0]['constraints']['scale_up']
        self.assertEqual(c['required'], 1000*2**20)
        self.assertEqual(c['status'], 'fail')
        self.assertEqual(r['candidates'][0]['status'], 'insufficient')

    def test_non_token_phases_do_not_infer_expert_fabric(self):
        for phase in ('training', 'physical_ai'):
            q = next(x['request'] for x in integrated_runs() if x['id'] == phase)
            q['workload'].update(output_tokens_per_s_per_request=0,
                                expert_fabric_bytes_per_token=2**20)
            q['rack']['scale_up_bw_bytes_s'] = 512*2**20
            r = analyze_integrated(q)
            c = r['candidates'][0]['constraints']['scale_up']
            self.assertIsNone(c['required'])
            self.assertEqual(c['status'], 'unevaluated')
            self.assertFalse(r['candidates'][0]['ranking_eligible'])

    def test_resident_weights_change_sizing(self):
        q = integrated_example()
        q['candidates'][0].update(capacity_bytes=32*G, sustained_bw_bytes_s=1024*G, max_modules=1)
        r = analyze_integrated(q)
        self.assertEqual(r['demand']['capacity_bytes'], 64*G)
        self.assertEqual(r['candidates'][0]['required_modules'], 2)
        self.assertEqual(r['candidates'][0]['status'], 'insufficient')
        self.assertEqual(r['kv_only_lower_bound']['candidates'][0]['required_modules'], 1)

    def test_training_explicit_step_budget(self):
        r = next(x['result'] for x in integrated_runs() if x['id'] == 'training')
        self.assertEqual(r['demand']['capacity_bytes'], 128*G)
        self.assertEqual(r['demand']['logical_bw_bytes_s'], 512*G)
        self.assertEqual(r['candidates'][0]['required_modules'], 4)

    def test_prefill_rate_reuse(self):
        q = integrated_example()
        q['workload'].update(phase='prefill', input_tokens_per_s=100, prefix_reuse_ratio=.25, active_weight_bytes_per_token=3)
        q['phase_budget']['prefill_other_bw_bytes_s'] = 20
        r = analyze_integrated(q)
        self.assertEqual(r['demand']['traffic_components_bytes_s']['kv_write'], 150)
        self.assertEqual(r['demand']['logical_bw_bytes_s'], 470)
        del q['workload']['input_tokens_per_s']
        self.assertIsNone(analyze_integrated(q)['demand']['logical_bw_bytes_s'])

    def test_physical_ai_frame_traffic(self):
        r = next(x['result'] for x in integrated_runs() if x['id'] == 'physical_ai')
        self.assertEqual(r['demand']['logical_bw_bytes_s'], 240*2**20)
        self.assertEqual(r['demand']['capacity_bytes'], 50*G)
        self.assertIsNone(r['predictions']['tokens_per_joule'])

    def test_unknown_propagation_and_known_violation(self):
        q = integrated_example()
        del q['workload']['active_weight_bytes_per_token']
        q['candidates'][0].update(capacity_bytes=32*G, max_modules=1)
        r = analyze_integrated(q)
        self.assertIsNone(r['demand']['logical_bw_bytes_s'])
        self.assertIsNone(r['candidates'][0]['required_modules'])
        self.assertEqual(r['candidates'][0]['status'], 'insufficient')
        self.assertEqual(r['candidates'][0]['known_module_lower_bound'], 2)
        q['candidates'][0]['max_modules'] = 10
        self.assertEqual(analyze_integrated(q)['candidates'][0]['status'], 'unevaluated')
        q = integrated_example()
        del q['phase_budget']['resident_state_bytes']
        self.assertIsNone(analyze_integrated(q)['demand']['capacity_bytes'])

    def test_model_and_technology_change_modules(self):
        runs = integrated_runs()[:3]
        self.assertEqual([r['result']['demand']['logical_bw_bytes_s']/G for r in runs], [128, 256, 256])
        self.assertEqual([r['result']['candidates'][0]['required_modules'] for r in runs], [1, 2, 1])
        self.assertTrue(all(next(c for c in r['result']['candidates'] if c['id'] == 'hbm5')['status'] == 'unevaluated' for r in runs))

    def test_local_pool_and_link_deficits(self):
        q = integrated_example()['placement']
        self.assertEqual(evaluate_placement(q)['status'], 'eligible')
        q['pools'][0]['capacity_bytes'] = 1000*G
        q['pools'][1]['assigned_bytes'] = 96*G
        r = evaluate_placement(q)
        self.assertEqual(r['pools'][1]['constraints']['capacity']['status'], 'fail')
        self.assertEqual(r['status'], 'insufficient')
        q['pools'][1]['assigned_bytes'] = 48*G
        q['paths'][0]['traffic_bytes_s'] = 16*G
        self.assertEqual(evaluate_placement(q)['paths'][0]['status'], 'insufficient')
        q['paths'][0]['bandwidth_bytes_s'] = None
        self.assertEqual(evaluate_placement(q)['status'], 'unevaluated')

    def test_control_data_separation(self):
        q = integrated_example()['kv_system']
        r = evaluate_kv_system(q)
        self.assertEqual(r['metadata_bytes'], 100*2**20)
        self.assertEqual(r['control_bw_bytes_s'], 100*1024)
        self.assertEqual(r['modes']['direct']['status'], 'eligible')
        self.assertEqual(r['modes']['relay']['status'], 'insufficient')
        del q['server_metadata_capacity_bytes']
        self.assertEqual(evaluate_kv_system(q)['modes']['direct']['status'], 'unevaluated')
        q['server_metadata_capacity_bytes'] = 99*2**20
        self.assertEqual(evaluate_kv_system(q)['modes']['direct']['status'], 'insufficient')

    def test_zero_and_missing_are_distinct(self):
        q = integrated_example()
        q['workload']['output_tokens_per_s_per_request'] = 0
        self.assertEqual(analyze_integrated(q)['demand']['logical_bw_bytes_s'], 0)
        q['workload']['active_weight_bytes_per_token'] = None
        self.assertIsNone(analyze_integrated(q)['demand']['logical_bw_bytes_s'])

    def test_integrated_rack_constraints(self):
        for field, value, name in [('max_channels', 0, 'channels'), ('fabric_bw_bytes_s', 127*G, 'fabric'), ('power_limit_w', 1049, 'rack_power'), ('cooling_limit_w', 1049, 'cooling'), ('psu_capacity_w', 1312, 'psu')]:
            q = integrated_example()
            q['rack'].update(psu_efficiency=.8)
            q['rack'][field] = value
            self.assertEqual(analyze_integrated(q)['candidates'][0]['constraints'][name]['status'], 'fail')

    def test_exclusion_every_path(self):
        for family in ('HBF', 'NAND', 'flash', 'SSD', 'NVMe'):
            q = integrated_example()
            q['candidates'][0]['family'] = family
            q['placement']['pools'][0]['family'] = family
            r = analyze_integrated(q)
            self.assertEqual(r['candidates'][0]['status'], 'excluded')
            self.assertIsNone(r['candidates'][0]['required_modules'])
            self.assertEqual(r['placement']['pools'][0]['status'], 'excluded')
            self.assertEqual(r['placement']['paths'][0]['status'], 'excluded')
            self.assertEqual(r['placement']['status'], 'unevaluated')

    def test_invalid_and_no_mutation(self):
        q = integrated_example()
        before = copy.deepcopy(q)
        analyze_integrated(q)
        self.assertEqual(q, before)
        for value in (-1, True, '8 MiB', float('nan'), float('inf')):
            q = integrated_example()
            q['phase_budget']['frame_bytes'] = value
            with self.assertRaises(InputError):
                analyze_integrated(q)
        q = integrated_example()
        q['placement']['paths'][0]['destination'] = 'missing'
        with self.assertRaises(InputError):
            analyze_integrated(q)
        with self.assertRaises(InputError):
            evaluate_kv_system({'sessions': 1.5})
        with self.assertRaises(InputError):
            compare_scenarios(integrated_example(), [{'id': 'x', 'year': 2030, 'scenario': {'weight_multiplier': 0}}])

    def test_cli_parity_and_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, out = root/'input.json', root/'out.json'
            q = integrated_example()
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT))
            for command, request, expected in [('integrated', q, analyze_integrated(q)), ('compare', dict(request=q, scenarios=[dict(id='future', year=2031, scenario={'weight_multiplier': 2})]), compare_scenarios(q, [dict(id='future', year=2031, scenario={'weight_multiplier': 2})]))]:
                src.write_text(json.dumps(request))
                p = subprocess.run([sys.executable, '-B', '-m', 'memory_dsa', command, '--input', str(src), '--output', str(out)], cwd=ROOT, env=env, capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(json.loads(out.read_text()), expected)
            demo(root/'a')
            demo(root/'b')
            for file in (root/'a').iterdir():
                self.assertEqual(file.read_bytes(), (root/'b'/file.name).read_bytes())
            with (root/'a/integrated-results.csv').open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual({r['section'] for r in rows}, {'phase', 'pools', 'paths', 'control_data'})
            self.assertEqual({r['phase'] for r in rows}, {'decode', 'training', 'prefill', 'physical_ai'})
            self.assertIn('id="control-modes"', (root/'a/index.html').read_text())
            self.assertIn('"kv_system"', (root/'a/index.html').read_text())
