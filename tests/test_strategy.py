import copy
import json
import unittest

from memory_dsa.strategy import assess_case, make_llm_case, strategy_study


class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.study = strategy_study()
        self.products = {p['id']: p for p in self.study['products']}
        self.cases = {c['id']: c for c in self.study['cases']}

    def test_public_architecture_kv_and_payload_are_distinct(self):
        c = self.cases['llm-bf16-1']
        self.assertEqual(c['demand']['kv']['value'], 40 * 2**30)
        self.assertEqual(c['demand']['capacity']['value'], 140e9 + 40 * 2**30)
        self.assertEqual(c['demand']['capacity']['kind'], 'derived_approximate')
        self.assertNotEqual(c['demand']['capacity']['value'], 180e9)
        self.assertEqual(c['demand']['logical_bw']['value'], (140e9 + 40 * 2**30) * 20)

    def test_current_b300_refutes_blanket_new_capacity_claim(self):
        b300 = self.products['b300-sxm']
        one = assess_case(self.cases['llm-bf16-1'], b300)
        two = assess_case(self.cases['llm-bf16-2'], b300)
        four = assess_case(self.cases['llm-bf16-4'], b300)
        self.assertEqual(one['capacity_status'], 'within_nominal_only')
        self.assertEqual(two['capacity_status'], 'within_nominal_only')
        self.assertEqual(one['overall_status'], 'performance_unverified')
        self.assertEqual(four['capacity_status'], 'conditional_shortfall')
        self.assertAlmostEqual(four['capacity_shortfall_bytes'], 140e9 + 160 * 2**30 - 288e9)
        self.assertTrue(four['capacity_unit_sensitivity']['exceeds_both_label_interpretations'])
        self.assertEqual(four['market_status'], 'unserved_market_not_established')

    def test_precision_alternative_can_remove_capacity_exclusion(self):
        h200 = self.products['h200-sxm']
        before = assess_case(self.cases['llm-bf16-2'], h200)
        after = assess_case(self.cases['llm-lowprecision-2'], h200)
        self.assertEqual(before['capacity_status'], 'conditional_shortfall')
        self.assertEqual(after['capacity_status'], 'within_nominal_only')
        self.assertEqual(after['overall_status'], 'performance_unverified')
        self.assertEqual(self.cases['llm-lowprecision-2']['demand']['capacity']['value'], 70e9 + 40 * 2**30)

    def test_peak_is_only_a_ceiling_not_sustained_pass(self):
        h100 = self.products['h100-sxm']
        h200 = self.products['h200-sxm']
        c = self.cases['llm-bf16-1']
        self.assertEqual(assess_case(c, h100)['bw_status'], 'conditional_peak_exceeded')
        self.assertEqual(assess_case(c, h200)['bw_status'], 'below_peak_only')
        for p in self.products.values():
            self.assertIsNone(p['sustained_bw']['value'])
            self.assertIsNone(p['usable_capacity']['value'])
            self.assertIsNone(p['memory_power']['value'])

    def test_unknown_and_zero_are_not_the_same(self):
        p = copy.deepcopy(self.products['h200-sxm'])
        c = self.cases['llm-bf16-1']
        p['capacity']['value'] = None
        self.assertEqual(assess_case(c, p)['capacity_status'], 'unknown')
        self.assertIsNone(assess_case(c, p)['capacity_shortfall_bytes'])
        p['capacity']['value'] = 0
        self.assertEqual(assess_case(c, p)['capacity_status'], 'conditional_shortfall')

    def test_scope_mismatch_is_not_compared(self):
        r = assess_case(self.cases['llm-bf16-1'], self.products['jetson-thor'])
        self.assertEqual(r['overall_status'], 'not_comparable')
        self.assertIsNone(r['capacity_shortfall_bytes'])

    def test_metric_units_and_memory_path_cannot_be_relabeled(self):
        for target, field, replacement in [('case', 'unit', 'GB'), ('case', 'scope', 'whole rack memory'),
                                            ('product', 'unit', 'GB/s'), ('product', 'scope', 'one GPU PCIe link')]:
            c = copy.deepcopy(self.cases['llm-bf16-1'])
            p = copy.deepcopy(self.products['h200-sxm'])
            q = c['demand']['capacity'] if target == 'case' else p['peak_bw']
            q[field] = replacement
            with self.assertRaises(ValueError):
                assess_case(c, p)

    def test_custom_assumptions_describe_actual_inputs(self):
        c = make_llm_case('custom', 'custom', sessions=3, context_tokens=4096, tokens_per_s=7)
        notes = ' '.join(c['assumptions'])
        self.assertIn('4096 tokens', notes)
        self.assertIn('세션 3개', notes)
        self.assertIn('초당 7 tokens', notes)
        self.assertNotIn('초당 20 tokens', notes)

    def test_vendor_baseline_does_not_establish_future_tail_slo(self):
        p = self.products['jetson-thor']
        baseline = assess_case(self.cases['physical-baseline'], p)
        future = assess_case(self.cases['physical-concurrent'], p)
        self.assertEqual(baseline['overall_status'], 'vendor_baseline_demonstrated')
        self.assertEqual(future['overall_status'], 'performance_unverified')
        self.assertEqual(future['capacity_status'], 'unknown')
        self.assertEqual(future['bw_status'], 'unknown')
        self.assertIsNone(self.cases['physical-concurrent']['demand']['capacity']['value'])
        for b in self.study['benchmarks']:
            self.assertIsNone(b['p99_latency_ms'])
            self.assertEqual(b['conditions']['statistic'], 'median')
        self.assertEqual(self.cases['physical-concurrent']['latency_target']['kind'], 'design_assumption')
        for key, value in [('cameras', 4), ('batch', 2), ('software', 'different'), ('simultaneous_extra_vlm', True)]:
            changed = copy.deepcopy(self.cases['physical-baseline'])
            changed['parameters'][key] = value
            self.assertEqual(assess_case(changed, p)['overall_status'], 'performance_unverified')
        changed = copy.deepcopy(self.cases['physical-baseline'])
        changed['kind'] = 'operating_assumption'
        self.assertEqual(assess_case(changed, p)['overall_status'], 'performance_unverified')

    def test_directions_bind_evidence_and_keep_targets_honest(self):
        source_ids = {s['id'] for s in self.study['sources']}
        assessment_ids = {a['id'] for a in self.study['assessments']}
        for d in self.study['directions']:
            self.assertTrue(d['case_ids'])
            self.assertTrue(set(d['evidence_ids']) <= source_ids)
            self.assertTrue(set(d['assessment_ids']) <= assessment_ids)
            self.assertTrue(d['alternatives'])
            self.assertTrue(d['disconfirming_conditions'])
            self.assertTrue(d['internal_validation'])
            self.assertIsNone(d['targets']['memory_power']['value'])
        edge = next(d for d in self.study['directions'] if d['id'] == 'edge-qos-first')
        self.assertIsNone(edge['targets']['capacity']['value'])
        self.assertIsNone(edge['targets']['bw']['value'])
        self.assertEqual(edge['targets']['p99']['value'], 40)

    def test_remaining_scope_unknown_not_fabricated_or_excluded_candidate(self):
        axes = {a['id']: a for a in self.study['remaining_axes']}
        for axis in ('HBM5', 'DDR7'):
            self.assertIn('withheld', axes[axis]['status'])
        analyses = {a['id']: a for a in self.study['portfolio']['analyses']}
        for identifier in ('training-state', 'prefill-reuse'):
            metrics = analyses[identifier]['metrics']
            self.assertTrue(any(m['quantity']['value'] is not None and m['quantity']['value'] > 0 for m in metrics))
            self.assertTrue(any(m['quantity']['value'] is None for m in metrics))
        self.assertEqual(axes['HBF/NAND']['status'], 'positioning_only_excluded')
        self.assertTrue(all('NAND' not in p['memory_family'] for p in self.study['products']))
        for axis in ('HBM4', 'HBM4E', 'HBM5', 'DDR6', 'DDR7', 'LPDDR6', 'training', 'prefill', 'decode', 'physical_ai',
                     'module-capacity-BW-channels', 'rack-power-PSU', 'heterogeneous-disaggregation', 'kv-control-data',
                     'model-trends-demand-growth', 'model-tech-demand-reduction', 'internal-collaboration-inputs',
                     'coverage-insufficiency-blank'):
            row = axes[axis]
            for field in ('evidence_paths', 'input_paths', 'output_paths', 'screen_paths', 'verification', 'strategy_status'):
                self.assertTrue(row[field], (axis, field))
            self.assertTrue(all(path.startswith('strategy.html#') and '##' not in path
                                for path in row['screen_paths']))

    def test_input_validation_determinism_and_no_mutation(self):
        c = self.cases['llm-bf16-1']; p = self.products['h200-sxm']
        before = copy.deepcopy((c, p))
        assess_case(c, p)
        self.assertEqual((c, p), before)
        for kwargs in ({'sessions': 0}, {'sessions': True}, {'weight_bytes': -1}, {'kv_bytes': float('nan')}, {'tokens_per_s': float('inf')}):
            with self.assertRaises(ValueError):
                make_llm_case('invalid', 'invalid', **kwargs)
        self.assertEqual(self.study, strategy_study())
        json.dumps(self.study, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
