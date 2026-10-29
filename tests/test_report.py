import copy
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from memory_dsa.report import render_report


def run_node(arguments, **kwargs):
    # These pure offline JS checks do not consume system TLS/OpenSSL settings.
    # Keep startup/JS failures visible; this only selects an explicit empty config.
    return subprocess.run([shutil.which('node'), f'--openssl-config={os.devnull}',
                           *arguments], **kwargs)


def fixture():
    return {'scenarios': [], 'integrated_scenarios': [], 'catalog': [],
            'sources': [], 'internal_gaps': {},
            'decision_study': {'sample': {'capacity_bytes': None, 'logical_bw_bytes_s': 0}}}


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.remote = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'link', 'img'):
            value = attrs.get('src', attrs.get('href', ''))
            if value.startswith(('http:', 'https:')):
                self.remote.append(value)


class ReportTests(unittest.TestCase):
    def test_embedded_data_preserves_exact_unknowns_and_zero(self):
        data = fixture(); original = copy.deepcopy(data)
        page = render_report(data)
        raw = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', page, re.S).group(1)
        self.assertEqual(json.loads(raw), data)
        self.assertEqual(data, original)
        self.assertEqual(render_report(data), page)

    def test_report_payload_cannot_escape_into_html(self):
        data = fixture(); data['sources'] = [{'id': '</script><img src=x onerror=alert(1)>\u2028&'}]
        page = render_report(data)
        self.assertNotIn('</script><img', page)
        raw = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', page, re.S).group(1)
        self.assertEqual(json.loads(raw), data)
        self.assertIn('\\u003c', raw)

    def test_no_external_runtime_assets_and_invalid_numbers_rejected(self):
        parser = AssetParser(); parser.feed(render_report(fixture()))
        self.assertEqual(parser.remote, [])
        data = fixture(); data['bad'] = float('nan')
        with self.assertRaises(ValueError):
            render_report(data)

    @unittest.skipUnless(shutil.which('node'), 'Offline JavaScript checks need Node')
    def test_node_checks_ignore_ambient_openssl_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'malformed-openssl.cnf'
            config.write_text('This is intentionally not a valid OpenSSL configuration.\n')
            environment = dict(os.environ, OPENSSL_CONF=str(config))
            result = run_node(['-e', 'process.stdout.write(String(6 * 7))'],
                              env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '42')

    @unittest.skipUnless(shutil.which('node'), 'Optional JavaScript syntax check needs Node')
    def test_generated_javascript_is_valid(self):
        script = re.findall(r'<script>(.*?)</script>', render_report(fixture()), re.S)[0]
        result = run_node(['--check'], input=script,
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Optional JavaScript readout check needs Node')
    def test_rendered_unknown_budget_has_no_invented_utilization(self):
        data = fixture()
        data['scenarios'] = [{'name': 'missing', 'year': 2030, 'request': {},
                              'result': {'demand': {'kv_total_bytes': None,
                                                   'logical_decode_kv_bw_bytes_s': 0}}}]
        data['integrated_scenarios'] = [{'id': 'example', 'request': {}, 'result': {
            'phase': 'decode', 'demand': {'capacity_bytes': None, 'logical_bw_bytes_s': 0},
            'candidates': [{'id': '<unsafe>', 'status': 'unevaluated',
                            'required_modules': None, 'constraints': {
                                'bandwidth': {'required': 0, 'limit': None, 'status': 'unknown'}}}]}}]
        page = render_report(data)
        script = re.findall(r'<script>(.*?)</script>', page, re.S)[0]
        # A tiny DOM sink verifies displayed model values; actual layout and controls
        # are tested separately in a browser, not simulated by this unit check.
        runner = r'''
const fs=require('fs'),vm=require('vm'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const nodes={}; const document={documentElement:{dataset:{}},getElementById(id){
 if(!nodes[id])nodes[id]={innerHTML:'',textContent:'',value:'0',dataset:{},addEventListener(){}};
 return nodes[id];}};
document.getElementById('report-data').textContent=JSON.stringify(input.data);
vm.runInNewContext(input.script,{document,Intl,URL});
process.stdout.write(JSON.stringify(nodes));
'''
        result = run_node(['-e', runner],
                                input=json.dumps({'data': data, 'script': script}),
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        nodes = json.loads(result.stdout)
        self.assertIn('Unknown utilization', nodes['constraint-bars']['innerHTML'])
        self.assertNotIn('% of limit', nodes['constraint-bars']['innerHTML'])
        self.assertIn('Unknown', nodes['capacity-chart']['innerHTML'])
        self.assertIn('class="value">Unknown</span>', nodes['capacity-chart']['innerHTML'])
        self.assertIn('class="value">0 TiB/s</span>', nodes['bandwidth-chart']['innerHTML'])
        self.assertNotIn('<unsafe>', nodes['candidate-tradeoff']['innerHTML'])


if __name__ == '__main__':
    unittest.main()
