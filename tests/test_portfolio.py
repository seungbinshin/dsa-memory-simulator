"""Independent boundary and counterexample checks for conditional strategy models."""
import json
import unittest
from copy import deepcopy

from memory_dsa.integrated import evaluate_placement

from memory_dsa.portfolio import (
    GIB, HBM, TIER, EDGE, training_budget, prefill_budget,
    reverse_object_targets, channel_budget, transfer_budget, rack_residual,
    edge_sensor_budget, compare_quantity, compare_envelope, portfolio_study, q,
)


class PortfolioEquations(unittest.TestCase):
    def test_training_sharding_keeps_unsharded_staging_and_activations(self):
        four, eight = training_budget(shards=4), training_budget(shards=8)
        self.assertEqual(four['capacity_bytes'], 317859738368)
        self.assertEqual(eight['capacity_bytes'], 177859738368)
        # Doubling sharding halves persistent state, not the entire peak budget.
        self.assertEqual(four['state_bytes'], 2 * eight['state_bytes'])
        self.assertGreater(eight['capacity_bytes'], four['capacity_bytes'] / 2)
        self.assertEqual(four['optimizer_logical_bw_lower_bound'], 4.9e12)
        self.assertIsNone(four['total_bw_bytes_s'])
        self.assertIsNone(training_budget(activation_bytes=None)['capacity_bytes'])

    def test_unknown_total_traffic_is_not_zero_or_lower_bound(self):
        partial = prefill_budget()
        self.assertEqual(partial['new_kv_bytes'], 10 * GIB)
        self.assertEqual(partial['kv_write_lower_bound_bytes_s'], 20 * GIB)
        self.assertIsNone(partial['total_bw_bytes_s'])
        explicit_zero = prefill_budget(other_traffic_bytes_s=0)
        self.assertEqual(explicit_zero['total_bw_bytes_s'], 20 * GIB)
        self.assertIsNone(explicit_zero['achieved_ttft_s'])

    def test_prefix_reuse_does_not_invent_resident_capacity_reduction(self):
        baseline, reused = prefill_budget(), prefill_budget(reuse_fraction=.75)
        self.assertEqual(reused['kv_write_lower_bound_bytes_s'], baseline['kv_write_lower_bound_bytes_s'] / 4)
        self.assertEqual(reused['logical_resident_kv_bytes'], baseline['logical_resident_kv_bytes'])
        self.assertIsNone(reused['resident_capacity_savings_bytes'])
        self.assertEqual(prefill_budget(reuse_fraction=1)['kv_write_lower_bound_bytes_s'], 0)
        self.assertIsNone(prefill_budget(reuse_fraction=1)['total_bw_bytes_s'])

    def test_reverse_sizing_honors_reserve_and_efficiency(self):
        target=reverse_object_targets(capacity_bytes=720,logical_bw_bytes_s=560,objects=8)
        self.assertAlmostEqual(target['nominal_capacity_per_object_bytes'],100)
        self.assertAlmostEqual(target['peak_bw_per_object_bytes_s'],100)
        self.assertIsNone(reverse_object_targets()['nominal_capacity_per_object_bytes'])
        self.assertGreater(reverse_object_targets(capacity_bytes=720,usable_fraction=.8)['nominal_capacity_per_object_bytes'],100)

    def test_modules_on_same_channel_do_not_multiply_bandwidth(self):
        eight=channel_budget(modules=8,independent_channels=4,demand_bytes_s=200e9)
        sixteen=channel_budget(modules=16,independent_channels=4,demand_bytes_s=200e9)
        self.assertEqual(eight['aggregate_assumed_bytes_s'],sixteen['aggregate_assumed_bytes_s'])
        self.assertEqual(eight['per_channel_peak_bytes_s'],44.8e9)
        self.assertEqual(eight['bandwidth_status'],'conditional_shortfall')
        self.assertEqual(channel_budget(demand_bytes_s=80*GIB)['minimum_independent_channels'],3)
        with self.assertRaises(ValueError):
            channel_budget(modules=4,independent_channels=8)

    def test_transfer_deadline_can_fail_even_when_average_rate_fits(self):
        result=transfer_budget(payload_bytes=1000,arrival_rate_s=1,miss_fraction=.5,
                               deadline_s=.1,source_bytes_s=9000,destination_bytes_s=5000,fabric_bytes_s=8000)
        self.assertEqual(result['steady_state_bytes_s'],500)
        self.assertEqual(result['required_bytes_s'],10000)
        self.assertEqual(result['path_limit_bytes_s'],5000)
        self.assertEqual(result['transfer_time_lower_bound_s'],.2)
        self.assertEqual(result['status'],'conditional_shortfall')
        self.assertIsNone(result['achieved_ttft_s'])

    def test_zero_arrivals_or_misses_do_not_create_copy_deadline_demand(self):
        for arrival_rate,miss_fraction in ((0,1),(1,0),(0,0)):
            with self.subTest(arrival_rate=arrival_rate,miss_fraction=miss_fraction):
                result=transfer_budget(payload_bytes=1000,arrival_rate_s=arrival_rate,miss_fraction=miss_fraction,
                                       deadline_s=.1,source_bytes_s=5000,destination_bytes_s=5000,fabric_bytes_s=5000)
                self.assertFalse(result['transfer_required'])
                self.assertEqual(result['required_bytes_s'],0)
                self.assertEqual(result['per_copy_deadline_bytes_s'],0)
                self.assertEqual(result['status'],'conditional_headroom')
                self.assertIsNone(result['transfer_time_lower_bound_s'])
                self.assertIsNone(result['achieved_ttft_s'])
                self.assertIsNone(result['achieved_p99_s'])
        unknown_path=transfer_budget(payload_bytes=1000,arrival_rate_s=0,miss_fraction=1,deadline_s=.1)
        self.assertEqual(unknown_path['required_bytes_s'],0)
        self.assertEqual(unknown_path['status'],'unknown')
        self.assertIsNone(unknown_path['path_limit_bytes_s'])

    def test_rare_positive_miss_still_requires_per_copy_deadline(self):
        result=transfer_budget(payload_bytes=1000,arrival_rate_s=1,miss_fraction=1e-9,
                               deadline_s=.1,source_bytes_s=5000,destination_bytes_s=5000,fabric_bytes_s=5000)
        self.assertTrue(result['transfer_required'])
        self.assertAlmostEqual(result['steady_state_bytes_s'],1e-6)
        self.assertEqual(result['required_bytes_s'],10000)
        self.assertEqual(result['status'],'conditional_shortfall')
        self.assertIsNone(result['achieved_p99_s'])

    def test_unknown_link_cannot_be_declared_feasible(self):
        result=transfer_budget(payload_bytes=1000,arrival_rate_s=1,miss_fraction=1,
                               deadline_s=1,source_bytes_s=10000,destination_bytes_s=None,fabric_bytes_s=10000)
        self.assertIsNone(result['path_limit_bytes_s'])
        self.assertEqual(result['status'],'unknown')
        self.assertIsNone(result['achieved_p99_s'])

    def test_known_transfer_bottleneck_is_not_hidden_by_an_unknown_link(self):
        result=transfer_budget(payload_bytes=1000,arrival_rate_s=1,miss_fraction=1,
                               deadline_s=.1,source_bytes_s=1,destination_bytes_s=None,fabric_bytes_s=20000)
        self.assertEqual(result['required_bytes_s'],10000)
        self.assertEqual(result['status'],'conditional_shortfall')
        self.assertEqual(result['known_path_ceiling_bytes_s'],1)
        self.assertEqual(result['known_bound_transfer_time_lower_bound_s'],1000)
        self.assertIsNone(result['path_limit_bytes_s'])
        self.assertIsNone(result['transfer_time_lower_bound_s'])
        self.assertIsNone(result['achieved_ttft_s'])
        self.assertIsNone(result['achieved_p99_s'])
        inactive=transfer_budget(payload_bytes=1000,arrival_rate_s=0,miss_fraction=1,
                                 deadline_s=.1,source_bytes_s=1,destination_bytes_s=None,fabric_bytes_s=20000)
        self.assertEqual(inactive['required_bytes_s'],0)
        self.assertEqual(inactive['status'],'unknown')
        self.assertIsNone(inactive['known_bound_transfer_time_lower_bound_s'])

    def test_nplus1_rating_is_dc_and_efficiency_applies_only_to_ac(self):
        result=rack_residual()
        self.assertEqual(result['survivable_supply_dc_w'],30000)
        self.assertEqual(result['ac_limited_dc_w'],32900)
        self.assertEqual(result['effective_known_dc_ceiling_w'],28000)
        self.assertEqual(result['memory_w_per_object_ceiling'],50)
        self.assertAlmostEqual(result['proposed_wall_ac_w'],26000/.94)
        self.assertEqual(result['status'],'conditional_headroom')
        self.assertEqual(rack_residual(cooling_dc_w=25000)['status'],'conditional_shortfall')

    def test_negative_rack_residual_is_preserved_and_unknown_limit_blocks_pass(self):
        deficit=rack_residual(non_dram_dc_w=29000)
        self.assertEqual(deficit['residual_memory_dc_w'],-1000)
        self.assertEqual(deficit['allocatable_memory_dc_w'],0)
        self.assertTrue(deficit['baseline_already_exceeds_ceiling'])
        self.assertEqual(deficit['status'],'conditional_shortfall')
        incomplete=rack_residual(psu_efficiency=None)
        self.assertEqual(incomplete['effective_known_dc_ceiling_w'],28000)
        self.assertFalse(incomplete['all_limits_known'])
        self.assertEqual(incomplete['status'],'unknown')
        # A known ceiling violation remains an exclusion even if another limit is missing.
        self.assertEqual(rack_residual(psu_efficiency=None,cooling_dc_w=25000)['status'],'conditional_shortfall')

    def test_edge_sensor_copy_is_not_total_inference_traffic(self):
        result=edge_sensor_budget()
        self.assertEqual(result['raw_ingress_bytes_s'],746496000)
        self.assertEqual(result['sensor_memory_lower_bound_bytes_s'],1492992000)
        self.assertEqual(result['transfer_window_lower_bound_bytes_s'],9953280000)
        self.assertIsNone(result['total_bw_bytes_s'])
        self.assertIsNone(result['total_capacity_bytes'])
        self.assertIsNone(result['achieved_p99_ms'])

    def test_comparison_rejects_different_unit_and_physical_scope(self):
        required=q(100,scope='one stack')
        self.assertEqual(compare_quantity(required,q(200,scope='one GPU')),'not_comparable')
        self.assertEqual(compare_quantity(required,q(200,'bit',scope='one stack')),'not_comparable')
        self.assertEqual(compare_quantity(required,q(scope='one stack')),'unknown')
        self.assertEqual(compare_quantity(required,q(99,scope='one stack')),'conditional_shortfall')

    def test_vendor_ranges_are_envelopes_not_continuous_qualified_products(self):
        required=q(44,scope='one stack')
        self.assertEqual(compare_envelope(required,q(scope='one stack',minimum=24,maximum=36)),'conditional_shortfall')
        self.assertEqual(compare_envelope(q(30,scope='one stack'),q(scope='one stack',minimum=24,maximum=36)),'within_envelope_only')
        self.assertEqual(compare_envelope(required,q(scope='one stack',minimum=40)),'unknown')

    def test_invalid_inputs_do_not_create_infinite_or_negative_targets(self):
        for call in (lambda:training_budget(shards=True),lambda:training_budget(prefetch_layers=81),
                     lambda:prefill_budget(reuse_fraction=1.1),lambda:reverse_object_targets(usable_fraction=0),
                     lambda:channel_budget(efficiency=1.01),lambda:rack_residual(psu_efficiency=-1),
                     lambda:transfer_budget(payload_bytes=100,arrival_rate_s=1,miss_fraction=2,deadline_s=1),
                     lambda:edge_sensor_budget(fps=float('inf'))):
            with self.assertRaises(ValueError):
                call()


class PortfolioDecisionSemantics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study=portfolio_study()
        cls.analyses={a['id']:a for a in cls.study['analyses']}

    def test_json_determinism_and_no_unserved_market_assertion(self):
        self.assertEqual(json.dumps(self.study,sort_keys=True,allow_nan=False),
                         json.dumps(portfolio_study(),sort_keys=True,allow_nan=False))
        self.assertTrue(all(a['market_status']=='unserved_market_not_established' for a in self.study['analyses']))

    def test_rule_based_priority_changes_when_capacity_pressure_relaxes(self):
        profiles={p['id']:p for p in self.study['profiles']}
        self.assertEqual(profiles['growth']['ordered_direction_ids'],[HBM,TIER,EDGE])
        self.assertEqual(profiles['efficient']['ordered_direction_ids'],[EDGE,TIER,HBM])
        self.assertEqual(profiles['power-constrained']['ordered_direction_ids'],[HBM,EDGE,TIER])
        self.assertIn('rack_memory_power_exceeds_residual',profiles['power-constrained']['triggers'])

    def test_complete_trace_is_connected_to_results_but_preserves_withheld_judgment(self):
        trace={r['requirement_id']:r for r in self.study['axis_trace']}
        self.assertEqual(len(trace),19)
        self.assertEqual(trace['HBF/NAND']['analysis_refs'],[])
        for key,row in trace.items():
            self.assertTrue(row['result_summary'])
            self.assertTrue(row['withheld_judgment'])
            self.assertTrue(row['verification_refs'])
            for ref in row['analysis_refs']:
                self.assertIn(ref,self.analyses)
        for key in ('HBM5','DDR6','DDR7'):
            self.assertIn('withheld',trace[key]['assessment_status'])

    def test_product_trace_reaches_supply_sources_and_resolved_family_comparisons(self):
        trace={r['requirement_id']:r for r in self.study['axis_trace']}
        rows={r['id']:r for r in self.study['family_assessments']}
        for family,source in [('HBM4','PF02'),('HBM4E','PF05'),('HBM5','PF06'),
                              ('DDR6','PF07'),('DDR7','PF08'),('LPDDR6','PF11')]:
            self.assertIn(source,trace[family]['evidence_refs'])
            self.assertTrue(trace[family]['family_assessment_refs'])
        for axis in trace.values():
            for ref in axis['family_assessment_refs']:
                self.assertIn(ref,rows)
                self.assertTrue(set(rows[ref]['evidence_ids']).issubset(axis['evidence_refs']))
            for ref in axis['verification_refs']:
                path,testname=ref.split('::')
                self.assertEqual(path,'tests/test_portfolio.py')
                class_name,method=testname.split('.')
                self.assertTrue(callable(getattr(globals()[class_name],method)))
        self.assertEqual(trace['HBF/NAND']['family_assessment_refs'],[])

    def test_undisclosed_families_remain_null_and_not_bad_products(self):
        families={f['id']:f for f in self.study['product_families']}
        for family in ('HBM5','DDR6','DDR7'):
            for record in families[family]['records']:
                for field in ('capacity_bytes','peak_bw_bytes_s','pin_rate_bps','bus_width_bits'):
                    item=record[field]
                    self.assertIsNone(item['value'])
                    self.assertIsNone(item['min'])
                    self.assertIsNone(item['max'])

    def test_family_matrix_is_computed_and_samples_never_become_deployment_pass(self):
        rows={r['id']:r for r in self.study['family_assessments']}
        self.assertEqual(rows['hbm4-micron-36gb-12h-growth-capacity']['comparison_status'],'conditional_shortfall')
        self.assertEqual(rows['hbm4-micron-36gb-12h-efficient-capacity']['comparison_status'],'conditional_headroom')
        sample=rows['hbm4e-samsung-48gb-12h-sample-growth-capacity']
        self.assertEqual(sample['comparison_status'],'conditional_headroom')
        self.assertEqual(sample['availability_limit'],'samples_shipped')
        self.assertFalse(sample['whole_system_validated'])
        self.assertEqual(rows['hbm5-architecture-roadmap-growth-capacity']['comparison_status'],'unknown')
        self.assertEqual(rows['hbm4-hgx-rubin-nvl8-system-growth-capacity']['comparison_status'],'not_comparable')
        self.assertEqual(rows['ddr5-micron-mrdimm-portfolio-growth-capacity']['comparison_status'],'conditional_shortfall')
        self.assertEqual(rows['ddr6-historical-roadmap-growth-capacity']['comparison_status'],'unknown')
        self.assertEqual(rows['lpddr6-skhynix-16gb-die-development-growth-capacity']['comparison_status'],'not_comparable')
        self.assertTrue(all(not row['whole_system_validated'] for row in rows.values()))

    def test_existing_path_results_never_imply_whole_system_fit(self):
        placement=self.analyses['kv-transfer']['inputs']['placement']
        self.assertEqual(placement['status'],'insufficient')
        self.assertFalse(placement['whole_system_validated'])
        modes=self.analyses['kv-control']['inputs']['evaluation']['modes']
        self.assertEqual(modes['direct']['constraints']['control_link']['status'],'pass')
        self.assertEqual(modes['direct']['constraints']['data_link']['status'],'fail')
        self.assertEqual(modes['direct']['status'],'insufficient')
        self.assertEqual(modes['relay']['constraints']['control_link']['status'],'fail')

    def test_profile_placement_uses_same_demand_and_preserves_growth_shortfall(self):
        profiles={p['id']:p for p in self.study['profiles']}
        growth=profiles['growth']['placement']
        efficient=profiles['efficient']['placement']
        self.assertTrue(growth['request']['bind_to_demand'])
        self.assertEqual(growth['request']['pools'][0]['assigned_bytes'],64*40*GIB)
        self.assertEqual(efficient['request']['pools'][0]['assigned_bytes'],16*40*GIB)
        self.assertEqual(growth['demand_capacity_bytes'],65*40*GIB)
        self.assertEqual(efficient['demand_capacity_bytes'],17*40*GIB)
        warm=growth['evaluation']['pools'][0]['constraints']['capacity']
        self.assertEqual(warm['required'],2748779069440)
        self.assertEqual(warm['limit'],921600000000)
        self.assertEqual(warm['status'],'fail')
        self.assertEqual(growth['evaluation']['status'],'insufficient')
        self.assertEqual(growth['evaluation']['coverage']['required_bytes'],growth['demand_capacity_bytes'])
        self.assertEqual(growth['evaluation']['coverage']['assigned_bytes'],growth['demand_capacity_bytes'])
        self.assertEqual(growth['evaluation']['coverage']['whole_demand_status'],'insufficient')
        self.assertEqual(efficient['evaluation']['pools'][0]['constraints']['capacity']['status'],'pass')
        self.assertEqual(efficient['evaluation']['paths'][0]['constraints']['bandwidth']['status'],'pass')
        self.assertEqual(efficient['evaluation']['status'],'unevaluated')
        self.assertFalse(efficient['evaluation']['whole_system_validated'])
        self.assertIsNone(efficient['transient_replication_bytes'])

    def test_stale_small_allocation_cannot_cover_growth_demand(self):
        growth=next(p for p in self.study['profiles'] if p['id']=='growth')['placement']
        stale_request=deepcopy(growth['request'])
        stale_request['pools'][0]['assigned_bytes']=16*40*GIB
        result=evaluate_placement(stale_request,demand_capacity_bytes=growth['demand_capacity_bytes'])
        self.assertEqual(result['coverage']['status'],'fail')
        self.assertEqual(result['coverage']['unassigned_bytes'],48*40*GIB)
        self.assertNotEqual(result['coverage']['whole_demand_status'],'eligible')

    def test_internal_tail_gap_is_an_extension_not_fake_ingestion(self):
        gaps={g['id']:g for g in self.study['internal_inputs']}
        self.assertIsNone(gaps['edge-tail']['receiver_field'])
        self.assertEqual(gaps['edge-tail']['ingestion_status'],'required_model_extension')
        self.assertEqual(gaps['memory-rail']['decision_threshold']['value'],12.5)
        for g in gaps.values():
            self.assertTrue(g['measurement_condition'])
            self.assertEqual(g['status'],'missing_internal_measurement')

    def test_moe_active_parameters_not_reused_as_residency_or_kv(self):
        metrics={m['id']:m['quantity'] for m in self.analyses['model-trends']['metrics']}
        self.assertEqual(metrics['moe-total-bf16']['value'],1342e9)
        self.assertEqual(metrics['moe-active']['value'],74e9)
        self.assertNotEqual(metrics['moe-active']['scope'],metrics['moe-total-bf16']['scope'])
        self.assertIsNone(metrics['mla-kv']['value'])

    def test_edge_p99_target_is_assumption_and_not_vendor_median(self):
        direction=next(d for d in self.study['directions'] if d['id']==EDGE)
        self.assertEqual(direction['targets']['p99']['value'],40)
        self.assertEqual(direction['targets']['p99']['kind'],'scenario_assumption')
        metrics={m['id']:m['quantity'] for m in self.analyses['physical-qos']['metrics']}
        self.assertEqual(metrics['p99-target']['kind'],'scenario_assumption')
        self.assertEqual(metrics['p99-target']['sources'],[])
        self.assertIn('vendor median',metrics['p99-target']['note'])
        self.assertIsNone(metrics['p99-measured']['value'])
        self.assertIsNone(direction['targets']['memory_power']['value'])

    def test_selected_latency_requirements_are_not_inherited_vendor_measurements(self):
        for direction in self.study['directions']:
            for key in ('latency','p99'):
                target=direction['targets'][key]
                if target['value'] is not None or target['min'] is not None:
                    self.assertEqual(target['kind'],'scenario_assumption')
                    self.assertEqual(target['sources'],[])
                    self.assertTrue(target['note'])
        gap=next(g for g in self.study['internal_inputs'] if g['id']=='edge-tail')
        self.assertEqual(gap['threshold']['kind'],'scenario_assumption')
        self.assertEqual(gap['threshold']['sources'],[])


if __name__=='__main__':
    unittest.main()
