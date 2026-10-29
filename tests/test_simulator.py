import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from memory_dsa.api import analyze, InputError
from memory_dsa.catalog import public_catalog, gap_schema
from memory_dsa.demo import baseline, demo
from memory_dsa.units import convert

ROOT = Path(__file__).resolve().parents[1]


class ArithmeticTests(unittest.TestCase):
    def test_owner_contract_arithmetic(self):
        d = analyze(baseline())['demand']
        self.assertEqual(d['kv_bytes_per_token'], 327680)
        self.assertEqual(d['kv_bytes_per_request'], 42949672960)
        self.assertEqual(d['kv_total_bytes'], 2748779069440)
        self.assertEqual(d['logical_decode_kv_bw_bytes_s'], 50 * 2**40)
        self.assertEqual(analyze(baseline())['candidates'][0]['required_modules'], 55)

    def test_small_independent_fixture_capacity_and_bw(self):
        q = baseline()
        q['workload'] = dict(layers=1, kv_heads=1, head_dim=1, bytes_per_element=1, context_tokens=10, concurrency=2, output_tokens_per_s_per_request=3)
        q['candidates'] = [dict(id='small', family='DDR', capacity_bytes=10, sustained_bw_bytes_s=100, power_w=2, max_modules=4)]
        r = analyze(q)
        self.assertEqual(r['demand']['kv_total_bytes'], 40)
        self.assertEqual(r['demand']['logical_decode_kv_bw_bytes_s'], 120)
        self.assertEqual(r['candidates'][0]['required_modules'], 4)
        q['candidates'][0]['sustained_bw_bytes_s'] = 10
        r = analyze(q)['candidates'][0]
        self.assertEqual(r['required_modules'], 12)
        self.assertEqual(r['status'], 'insufficient')

    def test_units(self):
        self.assertEqual(convert(16, 'Gb', 'GB'), 2)
        self.assertEqual(convert(1, 'TiB', 'GiB'), 1024)
        self.assertEqual(convert(8, 'Gbit/s', 'GB/s'), 1)
        self.assertEqual(convert(1, 'TB', 'B'), 10**12)
        self.assertIsNone(convert(None, 'GB', 'B'))
        for pair in [('GB', 'W'), ('gb', 'B'), ('GB/s', 'GB')]:
            with self.assertRaises(InputError):
                convert(1, *pair)

    def test_scenario_and_zero_rate(self):
        q = baseline()
        q['scenario'] = dict(context_multiplier=3, concurrency_multiplier=2, kv_bytes_multiplier=.5)
        self.assertEqual(analyze(q)['demand']['kv_total_bytes'], 3 * 2748779069440)
        q['workload']['output_tokens_per_s_per_request'] = 0
        r = analyze(q)
        self.assertEqual(r['demand']['logical_decode_kv_bw_bytes_s'], 0)
        self.assertGreater(r['candidates'][0]['required_modules'], 0)

    def test_constraints_boundaries(self):
        for field, value, constraint in [('fabric_bw_bytes_s', 1, 'fabric'), ('power_limit_w', 1000, 'rack_power'), ('max_channels', 54, 'channels'), ('psu_capacity_w', 100, 'psu'), ('cooling_limit_w', 100, 'cooling')]:
            q = baseline()
            q['rack'][field] = value
            q['rack']['psu_efficiency'] = .8
            r = analyze(q)['candidates'][0]
            self.assertEqual(r['constraints'][constraint]['status'], 'fail')
            self.assertEqual(r['status'], 'insufficient')
        q = baseline()
        q['rack']['power_limit_w'] = 3750
        self.assertEqual(analyze(q)['candidates'][0]['constraints']['rack_power']['status'], 'pass')
        q['rack']['power_limit_w'] = 3749
        self.assertEqual(analyze(q)['candidates'][0]['status'], 'insufficient')

    def test_unknown_not_zero_or_insufficient(self):
        for field in ('capacity_bytes', 'sustained_bw_bytes_s'):
            q = baseline()
            q['candidates'][0][field] = None
            c = analyze(q)['candidates'][0]
            self.assertEqual(c['status'], 'unevaluated')
            self.assertIsNone(c['required_modules'])
        q = baseline()
        q['candidates'][0]['power_w'] = None
        r = analyze(q)
        self.assertIsNone(r['candidates'][0]['rack_power_w'])
        self.assertNotIn('synthetic-hbm', r['ranking'])
        self.assertFalse(r['comparison_conclusive'])

    def test_no_mutation(self):
        q = baseline()
        before = copy.deepcopy(q)
        self.assertEqual(analyze(q), analyze(q))
        self.assertEqual(q, before)

    def test_other_phases_are_explicit(self):
        q = baseline()
        q['workload'].update(phase='training', resident_weight_bytes=100, activation_bytes=20, optimizer_bytes=300)
        r = analyze(q)
        self.assertEqual(r['demand']['training_state_bytes'], 420)
        self.assertEqual(r['candidates'][0]['status'], 'unevaluated')
        self.assertIsNone(r['predictions']['ttft_ms'])


class RegressionTests(unittest.TestCase):
    def test_exclusions_all_scenarios(self):
        for family in ('HBF', 'NAND', 'flash', 'SSD', 'NVMe', 'CXL NAND'):
            q = baseline()
            q['candidates'][0]['family'] = family
            q['scenario'] = dict(technology_bw_multiplier=100)
            r = analyze(q)
            self.assertEqual(r['candidates'][0]['status'], 'excluded')
            self.assertIsNone(r['candidates'][0]['required_modules'])
            self.assertEqual(r['ranking'], [])

    def test_catalog_corrections(self):
        c = {c['id']: c for c in public_catalog()}
        self.assertTrue(all(f['value'] is None for f in c['hbm5']['fields'].values()))
        self.assertIsNone(c['hbm4e-12h']['fields']['peak_bw_bytes_s']['value'])
        self.assertEqual(c['hbm4-12h']['fields']['peak_bw_bytes_s']['value'], 2995200000000)
        self.assertEqual(c['lpddr6']['fields']['capacity_bytes']['value'], 2000000000)
        self.assertEqual(c['lpddr6']['object_level'], 'die')
        self.assertTrue(all(c['fields']['sustained_bw_bytes_s']['value'] is None for c in public_catalog()))
        self.assertNotIn('HBF', json.dumps(gap_schema()))

    def test_invalid_inputs(self):
        for value in (None, 0, -1, True, '80', float('nan'), float('inf'), 1.5, 10**400):
            q = baseline()
            q['workload']['layers'] = value
            with self.subTest(value=str(value)), self.assertRaises(InputError):
                analyze(q)
        for mutation in (lambda q: q['scenario'].update(context_multiplier=-1), lambda q: q['rack'].update(psu_efficiency=2), lambda q: q['candidates'][0].update(family='mystery'), lambda q: q['workload'].update(architecture='mla'), lambda q: q.update(units='GB'), lambda q: q['candidates'].append(q['candidates'][0])):
            q = baseline()
            mutation(q)
            with self.assertRaises(InputError):
                analyze(q)

    def test_immutable_inputs(self):
        manifest = json.loads((ROOT/'inputs/INPUT_MANIFEST.json').read_text())
        for name, expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected)


class IntegrationTests(unittest.TestCase):
    def cli(self, *args):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT))
        return subprocess.run([sys.executable, '-B', '-m', 'memory_dsa', *map(str, args)], cwd=ROOT, env=env, text=True, capture_output=True)

    def test_cli_api_parity_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp)/'input.json', Path(tmp)/'output.json'
            q = baseline()
            src.write_text(json.dumps(q))
            r = self.cli('evaluate', '--input', src, '--output', out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(out.read_text()), analyze(q))
            src.write_text('{"workload":{},"workload":{}}')
            self.assertNotEqual(self.cli('evaluate', '--input', src, '--output', out).returncode, 0)

    def test_deterministic_demo_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a', Path(tmp)/'b'
            r = self.cli('demo', '--output', a)
            self.assertEqual(r.returncode, 0, r.stderr)
            demo(b)
            self.assertEqual(sorted(p.name for p in a.iterdir()), sorted(p.name for p in b.iterdir()))
            for p in a.iterdir():
                self.assertEqual(p.read_bytes(), (b/p.name).read_bytes())
            runs = json.loads((a/'results.json').read_text())['scenarios']
            self.assertGreaterEqual(len(runs), 4)
            self.assertGreater(runs[3]['result']['demand']['kv_total_bytes'], runs[0]['result']['demand']['kv_total_bytes'])
            self.assertLess(runs[4]['result']['demand']['kv_total_bytes'], runs[0]['result']['demand']['kv_total_bytes'])


if __name__ == '__main__':
    unittest.main()
