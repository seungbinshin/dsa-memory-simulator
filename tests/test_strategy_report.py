"""Display contracts for strategy claims, numeric unknowns and untrusted provenance."""
import copy
from html import escape
from html.parser import HTMLParser
import json
import os
import re
import shutil
import subprocess
import unittest

from memory_dsa.strategy_report import render_strategy_report


def quantity(value, unit='B'):
    return dict(value=value, min=None, max=None, unit=unit, kind='unknown' if value is None else 'derived_conditional',
                sources=['P1'], note='Explicit test input', scope='one GPU')


def fixture():
    return dict(checked_at='2026-10-29', sources=[dict(id='P1', title='Example', url='https://example.org/source')],
                products=[dict(id='test-gpu', label='Test GPU', scope='single_gpu',
                               capacity=quantity(100e9), peak_bw=quantity(200e9, 'B/s'))],
                cases=[dict(id='known-zero', label='Zero traffic', scope='single_gpu',
                            demand=dict(capacity=quantity(50e9), logical_bw=quantity(0, 'B/s')),
                            evidence_ids=['P1'], assumptions=['A declared test input']),
                       dict(id='unknown-demand', label='Unknown demand', scope='single_gpu',
                            demand=dict(capacity=quantity(None), logical_bw=quantity(None, 'B/s')),
                            evidence_ids=['P1'], assumptions=[])],
                assessments=[dict(case_id='known-zero', product_id='test-gpu',
                                  capacity_status='within_nominal_only', bw_status='below_peak_only',
                                  overall_status='performance_unverified', reasons=['No sustained measurements']),
                             dict(case_id='unknown-demand', product_id='test-gpu', capacity_status='unknown',
                                  bw_status='unknown', overall_status='performance_unverified', reasons=[])],
                directions=[], benchmarks=[], remaining_axes=[], boundaries=[])


def portfolio_fixture():
    data = fixture()
    directions = [dict(id=name, title='방향 '+name, action_stage='measure_first', priority_reason='Declared constraint',
                       targets=dict(capacity=quantity(None), bw=quantity(20e9, 'B/s')),
                       workload_ids=['analysis-a'], family_ids=['HBM5'], evidence_ids=['PX'], analysis_refs=['analysis-a'],
                       current_coverage=['Existing option remains'], falsification=['Measured relief reverses priority'],
                       alternatives=['Existing software'], next_measurements=['Measure p99'], deep_dive_refs=[])
                  for name in ('first', 'second')]
    data['portfolio'] = dict(
        title='Integrated test', decision_scope='No market claim', priority_method='Use backend order',
        sources=[dict(id='PX', title='Portfolio source', url='https://example.org/portfolio')],
        directions=directions,
        profiles=[dict(id='growth', label='Growth condition', ordered_direction_ids=['second', 'first'],
                       assumptions=['Growing condition'], change_reasons=['Capacity pressure'], analysis_ids=['analysis-a'], triggers=['Declared trigger']),
                  dict(id='efficient', label='Efficiency condition', ordered_direction_ids=['first', 'second'],
                       assumptions=['Reuse helps'], change_reasons=['Pressure removed'], analysis_ids=[], triggers=['Existing option succeeds'])],
        analyses=[dict(id='analysis-a', title='Actual calculation', scope='one stack', decision_status='conditional_analysis',
                       metrics=[dict(id='energy', label='Energy ceiling', quantity=quantity(12e-12, 'J/B')),
                                dict(id='control', label='Metadata traffic', quantity=quantity(1024e3, 'B/s')),
                                dict(id='unknown-total', label='Unknown total traffic', quantity=quantity(None, 'B/s'))],
                       conclusion='Partial traffic only', assumptions=['Test assumption'], evidence_ids=['PX'],
                       direction_ids=['first'], inputs=dict(count=4))],
        product_families=[dict(id='HBM5', label='HBM5', unpublished_fields=['capacity'], records=[
            dict(id='sample-record', scope='one stack', commercial_status='samples_shipped', status_as_of='2026-06-01',
                 evidence_ids=['PX'], note='Different operating points', capacity_bytes=quantity(None),
                 peak_bw_bytes_s=dict(quantity(None, 'B/s'), max=3.6e12),
                 pin_rate_bps=dict(quantity(None, 'bit/s/pin'), min=14e9), bus_width_bits=quantity(None, 'bit'))])],
        family_assessments=[dict(id='comparison-known', family_id='HBM5', record_id='sample-record', profile_id='growth',
                                 metric='capacity', target=quantity(44e9), available=quantity(48e9),
                                 comparison_status='conditional_headroom', availability_limit='samples_shipped',
                                 conclusion='No deployment qualification', scope_mapping_note='Same stack, sample only',
                                 evidence_ids=['PX'], analysis_refs=['analysis-a']),
                            dict(id='comparison-unknown', family_id='HBM5', record_id='sample-record', profile_id='efficient',
                                 metric='bw', target=quantity(None, 'B/s'), available=dict(quantity(None, 'B/s'), max=3.6e12),
                                 comparison_status='unknown', availability_limit='samples_shipped', conclusion='Unknown demand',
                                 scope_mapping_note='No full demand measurement', evidence_ids=['PX'], analysis_refs=['analysis-a'])],
        axis_trace=[dict(requirement_id=f'axis-{i}', requirement_label=f'Requirement {i}', direction_ids=['first'] if i % 2 else [],
                         evidence_refs=['PX'], analysis_refs=['analysis-a'], result_refs=['analysis-a.metrics'],
                         family_assessment_refs=['comparison-known', 'comparison-unknown'] if i == 0 else [],
                         screen_refs=['#portfolio-analyses'], verification_refs=['tests/test_portfolio.py'],
                         assessment_status='conditional_analysis', withheld_judgment='Real measurement pending',
                         result_summary=f'Calculated result {i}') for i in range(19)],
        internal_inputs=[dict(id='extension', label='Unimplemented receiver', unit='ms', scope='one workload',
                              receiver_field=None, ingestion_status='required_model_extension',
                              threshold=quantity(None, 'ms'), needed_for='Future tail', measurement_condition='Fixed sample count',
                              decision_rule='Only measured tail can change conclusion', verification_method='Trace timing',
                              owner_role='Validation', direction_ids=['first'], status='missing_internal_measurement')])
    for profile, warm, path, whole in zip(data['portfolio']['profiles'], (640e9, 160e9), (80e9, 20e9), ('insufficient', 'unevaluated')):
        profile['placement'] = dict(
            profile_id=profile['id'], demand_scope='Test-only disjoint warm and hot payload',
            allocation_semantics='Weights and transient copies excluded', assumptions=['Synthetic renderer contract'],
            metrics=[dict(id='warm-payload', label='Warm payload', quantity=quantity(warm)),
                     dict(id='path-required', label='Required path', quantity=quantity(path, 'B/s'))],
            evaluation=dict(status=whole, whole_system_validated=False,
                coverage=dict(required_bytes=warm+40e9, assigned_bytes=warm+40e9, unassigned_bytes=0,
                              status='pass', whole_demand_status=whole),
                pools=[dict(id='warm-ddr', family='DDR5', status='insufficient' if whole == 'insufficient' else 'eligible',
                            constraints=dict(capacity=dict(required=warm, limit=512e9, status='fail' if whole == 'insufficient' else 'pass'),
                                             bandwidth=dict(required=path, limit=100e9, status='pass'))),
                       dict(id='hot-hbm', family='HBM', status='unevaluated',
                            constraints=dict(capacity=dict(required=40e9, limit=None, status='unevaluated'),
                                             bandwidth=dict(required=path, limit=100e9, status='pass')))],
                paths=[dict(id='warm-to-hot', source='warm-ddr', destination='hot-hbm', status='insufficient' if whole == 'insufficient' else 'eligible',
                            constraints=dict(bandwidth=dict(required=path, limit=50e9, status='fail' if whole == 'insufficient' else 'pass')))],
                assumptions=['No hardware validation']))
    return data


def run_nodes(data, actions=()):
    page = render_strategy_report(data)
    script = re.findall(r'<script>(.*?)</script>', page, re.S)[0]
    runner = r'''
const fs=require('fs'),vm=require('vm'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const nodes={};const document={documentElement:{dataset:{}},getElementById(id){
 if(!nodes[id])nodes[id]={innerHTML:'',textContent:'',value:'',dataset:{},events:{},addEventListener(type,fn){this.events[type]=fn;}};
 return nodes[id];}};
document.getElementById('strategy-data').textContent=JSON.stringify(input.data);
vm.runInNewContext(input.script,{document,Intl,URL});
for(const action of input.actions){const node=document.getElementById(action.id);node.value=action.value;
 if(!node.events[action.event||'change'])throw new Error('Missing control event: '+action.id);
 node.events[action.event||'change']();}
process.stdout.write(JSON.stringify({nodes,ready:document.documentElement.dataset.strategyReady}));
'''
    result = subprocess.run([shutil.which('node'), f'--openssl-config={os.devnull}', '-e', runner],
                            input=json.dumps(dict(data=data, script=script, actions=actions)), capture_output=True,
                            text=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class Assets(HTMLParser):
    def __init__(self):
        super().__init__(); self.remote = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('img', 'script', 'link'):
            value = attrs.get('src', attrs.get('href', ''))
            if value.startswith(('https:', 'http:')):
                self.remote.append(value)


class StrategyReportTests(unittest.TestCase):
    def test_embedded_evidence_exact_deterministic_and_no_external_assets(self):
        data = portfolio_fixture(); before = copy.deepcopy(data)
        page = render_strategy_report(data)
        raw = re.search(r'<script id="strategy-data" type="application/json">(.*?)</script>', page, re.S).group(1)
        self.assertEqual(json.loads(raw), before)
        self.assertEqual(data, before)
        self.assertEqual(page, render_strategy_report(data))
        parser = Assets(); parser.feed(page)
        self.assertEqual(parser.remote, [])
        self.assertIn('lang="ko"', page)

    def test_script_breakout_and_nonfinite_inputs(self):
        data = fixture(); data['sources'][0]['title'] = '</script><img src=x onerror=alert(1)> &'
        page = render_strategy_report(data)
        self.assertNotIn('</script><img', page)
        self.assertIn('\\u003c/script', page)
        data['bad'] = float('inf')
        with self.assertRaises(ValueError):
            render_strategy_report(data)
        with self.assertRaises(ValueError):
            render_strategy_report([])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_unknown_not_a_zero_point_and_below_peak_not_measured_pass(self):
        output = run_nodes(fixture())
        self.assertEqual(output['ready'], 'true')
        nodes = output['nodes']
        self.assertIn('0 GB/s', nodes['map-legend']['innerHTML'])
        self.assertNotIn('Unknown demand', nodes['map-legend']['innerHTML'])
        self.assertIn('Unknown demand', nodes['matrix-table']['innerHTML'])
        self.assertIn('근거 부족', nodes['matrix-table']['innerHTML'])
        self.assertIn('실행 성능 미검증', nodes['selected-comparison']['innerHTML'])
        self.assertIn('지속 BW 미확인', nodes['selected-comparison']['innerHTML'])
        self.assertNotIn('class="badge measured"', nodes['selected-comparison']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_provenance_links_reject_script_urls_and_escape_display_strings(self):
        data = fixture()
        data['sources'][0].update(url='javascript:alert(1)', title='<unsafe-source>')
        data['products'][0]['label'] = '<unsafe-product>'
        nodes = run_nodes(data)['nodes']
        self.assertNotIn('href="javascript:', nodes['source-list']['innerHTML'])
        self.assertNotIn('<unsafe-source>', nodes['source-list']['innerHTML'])
        self.assertNotIn('<unsafe-product>', nodes['matrix-table']['innerHTML'])
        self.assertIn('&lt;unsafe-product&gt;', nodes['matrix-table']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_full_model_exposes_direction_falsification_and_scope_trace(self):
        from memory_dsa.strategy import strategy_study
        data = strategy_study()
        nodes = run_nodes(data)['nodes']
        for direction in data['directions']:
            self.assertIn(direction['title'], nodes['recommendation-cards']['innerHTML'])
            for text in direction['disconfirming_conditions']:
                self.assertIn(text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                              .replace('"', '&quot;').replace("'", '&#39;'), nodes['recommendation-cards']['innerHTML'])
        self.assertIn('B300', nodes['matrix-table']['innerHTML'])
        self.assertIn('약 ', nodes['selected-metrics']['innerHTML'])
        self.assertIn('median', nodes['benchmark-chart']['innerHTML'])
        self.assertIn('목표', nodes['physical-next']['innerHTML'])
        self.assertIn('요구 → 근거 → 분석 → 화면 → 검증', nodes['remaining-axes']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_profile_uses_exact_backend_order_and_preserves_all_analysis_links(self):
        data = portfolio_fixture()
        initial = run_nodes(data)['nodes']
        changed = run_nodes(data, [dict(id='portfolio-profile', value='efficient')])['nodes']
        for profile, nodes in zip(data['portfolio']['profiles'], (initial, changed)):
            actual = re.findall(r'data-direction-id="([^"]+)"', nodes['portfolio-board']['innerHTML'])
            self.assertEqual(actual, profile['ordered_direction_ids'])
            for reason in profile['change_reasons']:
                self.assertIn(reason, nodes['portfolio-change']['innerHTML'])
            self.assertIn('data-analysis-id="analysis-a"', nodes['portfolio-analyses']['innerHTML'])
        self.assertIn('함께 검토할 참조 분석', changed['portfolio-analyses']['innerHTML'])
        self.assertNotIn('data-direction-id="', changed['portfolio-change']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_all_original_axes_and_results_survive_direction_highlight(self):
        nodes = run_nodes(portfolio_fixture(), [dict(id='portfolio-trace-filter', value='first')])['nodes']
        rows = re.findall(r'data-requirement-id="([^"]+)"', nodes['portfolio-trace-table']['innerHTML'])
        self.assertEqual(rows, [f'axis-{i}' for i in range(19)])
        self.assertIn('전체 19축 유지', nodes['portfolio-trace-count']['textContent'])
        for i in range(19):
            self.assertIn(f'Calculated result {i}', nodes['portfolio-trace-table']['innerHTML'])
        self.assertIn('href="#analysis-analysis-a"', nodes['portfolio-trace-table']['innerHTML'])
        self.assertIn('모델 확장', nodes['portfolio-internal-inputs']['innerHTML'])
        self.assertIn('Fixed sample count', nodes['portfolio-internal-inputs']['innerHTML'])
        for identifier in ('comparison-known', 'comparison-unknown'):
            self.assertIn('href="#family-assessment-'+identifier+'"', nodes['portfolio-trace-table']['innerHTML'])
            self.assertIn('id="family-assessment-'+identifier+'"', nodes['portfolio-family-comparisons']['innerHTML'])
        self.assertIn('명목 용량 내 · 실행 미검증', nodes['portfolio-trace-table']['innerHTML'])
        self.assertIn('근거 부족', nodes['portfolio-trace-table']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_selected_profile_uses_matching_demand_and_never_upgrades_assignment_pass(self):
        data = portfolio_fixture()
        for profile, warm_text, whole_text in [('growth', '640 GB', '알려진 제약 초과'),
                                              ('efficient', '160 GB', '필수 한계 미확인')]:
            nodes = run_nodes(data, [dict(id='portfolio-profile', value=profile)])['nodes']
            display = nodes['portfolio-placement-content']['innerHTML']
            self.assertIn('data-placement-profile-id="'+profile+'"', display)
            self.assertIn(warm_text, display)
            self.assertIn('선언 payload 할당 누락 없음', display)
            self.assertIn('전체 선언 수요: '+whole_text, display)
            self.assertIn('전체 시스템 성능은 미검증', display)
            self.assertIn('수요 40 GB / 한계 미확인', display)
            self.assertNotIn('class="badge measured"', display)
        self.assertNotIn('640 GB', display)
        data['portfolio']['profiles'][1].pop('placement')
        nodes = run_nodes(data, [dict(id='portfolio-profile', value='efficient')])['nodes']
        self.assertIn('다른 조건의 결과를 대입하지 않습니다', nodes['portfolio-placement-content']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_bounds_small_positive_values_and_unknown_total_have_distinct_displays(self):
        nodes = run_nodes(portfolio_fixture())['nodes']
        self.assertIn('≤ 3,600 GB/s', nodes['portfolio-family-cards']['innerHTML'])
        self.assertIn('≥ 14 Gbit/s/pin', nodes['portfolio-family-cards']['innerHTML'])
        self.assertIn('12 pJ/B', nodes['portfolio-analyses']['innerHTML'])
        self.assertIn('1.02 MB/s', nodes['portfolio-analyses']['innerHTML'])
        self.assertIn('Unknown total traffic</span><strong>미확인</strong>', nodes['portfolio-analyses']['innerHTML'])
        comparisons = nodes['portfolio-family-comparisons']['innerHTML']
        self.assertIn('44 GB', comparisons)
        self.assertIn('48 GB', comparisons)
        self.assertIn('샘플 출하', comparisons)
        self.assertIn('명목 용량 내 · 실행 미검증', comparisons)
        self.assertIn('No deployment qualification', comparisons)
        self.assertNotIn('class="badge measured"', comparisons)

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_family_gap_bars_share_zero_and_unit_without_plotting_unknown_or_different_scope(self):
        data = portfolio_fixture()
        base = data['portfolio']['family_assessments'][0]
        bounded = dict(copy.deepcopy(base), id='bounded-bandwidth', metric='bw',
                       target=quantity(2.4e12, 'B/s'), available=dict(quantity(None, 'B/s'), max=3.6e12),
                       comparison_status='within_envelope_only')
        mismatched = dict(copy.deepcopy(base), id='different-scope',
                          available=dict(quantity(48e9), scope='eight GPU system'), comparison_status='not_comparable')
        unbounded = dict(copy.deepcopy(base), id='lower-bound-only',
                        available=dict(quantity(None), min=48e9), comparison_status='within_envelope_only')
        interval = dict(copy.deepcopy(base), id='target-interval', target=dict(quantity(None), min=32e9, max=44e9),
                        comparison_status='within_envelope_only')
        data['portfolio']['family_assessments'] += [bounded, mismatched, unbounded, interval]
        display = run_nodes(data)['nodes']['portfolio-family-comparisons']['innerHTML']
        charts = re.findall(r'data-gap-chart="([^"]+)"', display)
        self.assertEqual(charts, ['comparison-known', 'bounded-bandwidth', 'target-interval'])
        known_chart = re.search(r'data-gap-chart="comparison-known"(.*?)</article>', display, re.S).group(1)
        self.assertIn('data-shared-maximum="48000000000"', known_chart)
        self.assertIn('0 GB · 공통 영점', known_chart)
        widths = re.findall(r'data-gap-role="([^"]+)" data-raw-value="([^"]+)" style="width:([\d.]+)%"', known_chart)
        self.assertEqual([r[0] for r in widths], ['target', 'available'])
        self.assertAlmostEqual(float(widths[0][2]) / float(widths[1][2]), 44 / 48, places=5)
        bound_chart = re.search(r'data-gap-chart="bounded-bandwidth"(.*?)</article>', display, re.S).group(1)
        self.assertIn('0 GB/s · 공통 영점', bound_chart)
        self.assertIn('2,400 GB/s', bound_chart)
        self.assertIn('≤ 3,600 GB/s', bound_chart)
        self.assertIn('공개 상한', bound_chart)
        self.assertIn('public bound', display)
        interval_chart = re.search(r'data-gap-chart="target-interval"(.*?)</article>', display, re.S).group(1)
        self.assertIn('32–44 GB', interval_chart)
        self.assertIn('조건부 목표 범위 · 상한 위치', interval_chart)
        self.assertIn('target-bound', interval_chart)
        self.assertIn('확정 단일값이 아닙니다', interval_chart)
        for identifier in ('comparison-unknown', 'different-scope', 'lower-bound-only'):
            self.assertIn('data-gap-withheld="'+identifier+'"', display)
            self.assertNotIn('data-gap-chart="'+identifier+'"', display)
        self.assertIn('미확인값을 0으로 그리지 않습니다', display)
        self.assertIn('명목 용량 내 · 실행 미검증', display)

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_portfolio_text_and_sources_cannot_inject_markup_or_urls(self):
        data = portfolio_fixture()
        data['portfolio']['directions'][0]['title'] = '<bad-direction>'
        data['portfolio']['sources'][0].update(url='javascript:alert(1)', title='<bad-source>')
        data['portfolio']['family_assessments'][0]['conclusion'] = '<bad-comparison>'
        data['portfolio']['axis_trace'][0]['screen_refs'] = ['javascript:alert(1)']
        nodes = run_nodes(data)['nodes']
        for node in nodes.values():
            self.assertNotIn('href="javascript:', node['innerHTML'])
        self.assertIn('&lt;bad-direction&gt;', nodes['portfolio-board']['innerHTML'])
        self.assertIn('&lt;bad-comparison&gt;', nodes['portfolio-family-comparisons']['innerHTML'])
        self.assertNotIn('<bad-', nodes['portfolio-board']['innerHTML'])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_actual_portfolio_trace_metrics_and_family_comparisons_reach_screen(self):
        from memory_dsa.portfolio import portfolio_study
        data = fixture(); data['portfolio'] = portfolio_study()
        portfolio = data['portfolio']; nodes = run_nodes(data)['nodes']
        self.assertEqual(len(portfolio['axis_trace']), 19)
        for profile in portfolio['profiles']:
            self.assertIn(escape(profile['label'], quote=True), nodes['portfolio-profile']['innerHTML'])
        for analysis in portfolio['analyses']:
            self.assertIn('data-analysis-id="'+analysis['id']+'"', nodes['portfolio-analyses']['innerHTML'])
            for metric in analysis['metrics']:
                self.assertIn(escape(metric['label'], quote=True), nodes['portfolio-analyses']['innerHTML'])
        for row in portfolio['axis_trace']:
            self.assertIn('data-requirement-id="'+row['requirement_id']+'"', nodes['portfolio-trace-table']['innerHTML'])
            self.assertIn(escape(row['result_summary'], quote=True).replace('&#x27;', '&#39;'), nodes['portfolio-trace-table']['innerHTML'])
            for ref in row['family_assessment_refs']:
                self.assertIn('href="#family-assessment-'+ref+'"', nodes['portfolio-trace-table']['innerHTML'])
                self.assertIn('id="family-assessment-'+ref+'"', nodes['portfolio-family-comparisons']['innerHTML'])
        for assessment in portfolio['family_assessments']:
            self.assertIn('data-family-assessment-id="'+assessment['id']+'"', nodes['portfolio-family-comparisons']['innerHTML'])
            self.assertIn(escape(assessment['conclusion'], quote=True).replace('&#x27;', '&#39;'), nodes['portfolio-family-comparisons']['innerHTML'])
        self.assertIn('범위 불일치 · 비교 제외', nodes['portfolio-family-comparisons']['innerHTML'])
        self.assertIn('근거 부족', nodes['portfolio-family-comparisons']['innerHTML'])
        self.assertIn('수치 대조 10건 · 근거 부족 4건 · 범위 불일치 4건', nodes['portfolio-family-comparisons']['innerHTML'])
        plotted = re.findall(r'data-gap-chart="([^"]+)"', nodes['portfolio-family-comparisons']['innerHTML'])
        self.assertEqual(plotted, [row['id'] for row in portfolio['family_assessments']
                                  if row['comparison_status'] in ('conditional_shortfall', 'conditional_headroom', 'within_envelope_only')])

    @unittest.skipUnless(shutil.which('node'), 'Offline rendering checks require Node')
    def test_actual_profile_placement_keeps_growth_and_efficiency_separate(self):
        from memory_dsa.portfolio import portfolio_study
        data = fixture(); data['portfolio'] = portfolio_study()
        for profile in data['portfolio']['profiles']:
            nodes = run_nodes(data, [dict(id='portfolio-profile', value=profile['id'])])['nodes']
            display = nodes['portfolio-placement-content']['innerHTML']
            self.assertIn('data-placement-profile-id="'+profile['id']+'"', display)
            for metric in profile['placement']['metrics']:
                self.assertIn(escape(metric['label'], quote=True).replace('&#x27;', '&#39;'), display)
            self.assertIn('전체 시스템 성능은 미검증', display)
            self.assertIn('선언 payload 할당 누락 없음', display)
            self.assertIn('한계 미확인', display)
            if profile['id'] == 'efficient':
                self.assertIn('전체 선언 수요: 필수 한계 미확인', display)
                self.assertNotIn('2,748.78 GB', display)
            else:
                self.assertIn('전체 선언 수요: 알려진 제약 초과', display)
                self.assertIn('2,748.78 GB', display)


if __name__ == '__main__':
    unittest.main()
