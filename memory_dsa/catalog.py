"""Frozen supplied public evidence. No network lookup and no peak-to-sustained fallback."""
import copy


def source_registry():
    """Metadata transcribed from immutable notes, not freshly fetched web pages."""
    paths = [
        ('S01', 'SK hynix', '2026-01-05 (dateline 2026-01-06)', 'https://news.skhynix.com/cn/sk-hynix-showcases-next-generation-ai-memory-innovations-at-ces-2026/'),
        ('S02', 'SK hynix', '2025-09-12', 'https://news.skhynix.com/en/sk-hynix-completes-worlds-first-hbm4-development-and-readies-mass-production/'),
        ('S03', 'SK hynix', '2026-06-18', 'https://news.skhynix.com/en/sk-hynix-ships-samples-of-12-layer-next-gen-hbm4e-2/'),
        ('S04', 'SK hynix', '2026-03-10', 'https://news.skhynix.com/en/1c-lpddr6-development-2026/'),
        ('S05', 'SK hynix', '2026-04-19 (dateline 2026-04-20)', 'https://news.skhynix.com/en/mass-production-socamm2-192gb/'),
        ('S06', 'SK hynix', '2026-10-16', 'https://news.skhynix.com/en/ocp-global-summit-2026/'),
        ('S07', 'Samsung', '2023-12-04', 'https://semiconductor.samsung.com/kr/news-events/tech-blog/memory-tech-day-memory-in-the-age-of-ai-data/'),
        ('S08', 'NVIDIA', None, 'https://www.nvidia.com/en-us/data-center/dgx-vera-rubin-nvl72/'),
        ('S09', 'AMD', None, 'https://www.amd.com/en/partner/browse-by-resource/partner-insights-articles/helios-open-standards-ai-solution.html'),
        ('S10', 'NVIDIA', '2025-05-20', 'https://developer.nvidia.com/blog/nvidia-800-v-hvdc-architecture-will-power-the-next-generation-of-ai-factories/'),
        ('S11', 'SK hynix', '2026-08-25', 'https://news.skhynix.com/en/tech-note-series-ep2/'),
        ('S12', 'Kingston', '10/08/24 (printed; date order unspecified)', 'https://www.kingston.com/datasheets/KSM64R52BD4-128MB.pdf'),
        ('S13', 'Kingston', None, 'https://www.kingston.com/en/blog/pc-performance/ddr5-overview'),
        ('S14', 'Kingston', None, 'https://www.kingston.com/en/blog/servers-and-data-centers/server-memory-buying-guide')]
    return [dict(id=i, publisher=p, published=date, url=url, supplied_notes_checked='2026-10-27', evidence='inputs/MODEL_TRENDS.md' if i in ('S12', 'S13', 'S14') else 'inputs/PUBLIC_SOURCE_NOTES.md', caveat='Historical roadmap from indexed official text; page extraction incomplete' if i == 'S07' else 'Public evidence snapshot; not independently measured') for i,p,date,url in paths]


def field(value, unit, kind='unknown', sources=(), note='Not established by supplied evidence'):
    return dict(value=value, unit=unit, kind=kind, sources=list(sources), note=note)


def public_catalog():
    specs = [
        ('hbm4-12h', 'HBM', 'stack', 36e9, 'S01', 'announced', 2995.2e9),
        ('hbm4-16h', 'HBM', 'stack', 48e9, 'S01', 'exhibited', None),
        ('hbm4e-12h', 'HBM', 'stack', 48e9, 'S03', 'sampled', None),
        ('hbm5', 'HBM', 'stack', None, 'S11', 'unknown', None),
        ('lpddr6', 'LPDDR6', 'die', 2e9, 'S04', 'development validated; supply plan unconfirmed', None),
        ('socamm2', 'SOCAMM2', 'module', 192e9, 'S05', 'mass production announced', None),
        ('cmm-ddr5-gen2', 'CXL', 'module', 256e9, 'S06', 'exhibited', 80e9),
        ('ddr5-rdimm', 'DDR5', 'module', 128 * 2**30, 'S12', 'specific datasheet: Kingston KSM64R52BD4-128MB Rev.A 4811642A', 51.2e9),
        ('ddr6', 'DDR6', 'module', None, 'S07', 'historical roadmap', None),
        ('ddr7', 'DDR7', 'module', None, None, 'unknown', None)]
    result = []
    for cid, family, level, cap, source, maturity, peak in specs:
        sources = [source] if source else []
        values = {k: field(None, unit) for k, unit in [('capacity_bytes', 'B'), ('peak_bw_bytes_s', 'B/s'), ('sustained_bw_bytes_s', 'B/s'), ('power_w', 'W'), ('p99_latency_ns', 'ns'), ('pin_rate_gbit_s', 'Gbit/s'), ('io_width_bits', 'bit'), ('channels', 'count')]}
        if cap is not None:
            values['capacity_bytes'] = field(int(cap), 'B', 'vendor_reported', sources, 'Decimal GB; LPDDR6 16 Gb die / 8 = 2 GB, not module capacity')
        if peak is not None:
            values['peak_bw_bytes_s'] = field(int(peak), 'B/s', 'derived_theoretical' if cid == 'hbm4-12h' else 'vendor_reported', ['S01', 'S02'] if cid == 'hbm4-12h' else sources, '11.7 Gbit/s * 2048 / 8 = 2995.2 GB/s' if cid == 'hbm4-12h' else 'Exhibition aggregate; not sustained multi-host BW')
        if cid == 'hbm4-12h':
            values['io_width_bits'] = field(2048, 'bit', 'vendor_reported', ['S02'], 'I/O pins, not independent channels')
            values['pin_rate_gbit_s'] = field(11.7, 'Gbit/s', 'vendor_reported', ['S01'], '12H profile')
        if cid == 'hbm4e-12h':
            values['pin_rate_gbit_s'] = field(16, 'Gbit/s', 'vendor_reported', ['S03'], 'Up to; I/O width unverified, BW remains null')
        if cid == 'lpddr6':
            values['pin_rate_gbit_s'] = field(10.7, 'Gbit/s', 'vendor_reported', ['S04'], 'Over 10.7; lower bound wording, not exact peak')
        if cid == 'ddr5-rdimm':
            values['capacity_bytes'] = field(128 * 2**30, 'B', 'derived_from_datasheet', ['S12'], '16G x 64 payload bits / 8; binary DRAM address interpretation gives 128 GiB. Datasheet label: 128GB; excludes ECC width')
            values['peak_bw_bytes_s'] = field(int(51.2e9), 'B/s', 'derived_theoretical', ['S12', 'S13'], '6400 MT/s x 64 payload bits / 8 = 51.2 decimal GB/s; not sustained BW')
            values['io_width_bits'] = field(64, 'bit', 'vendor_reported', ['S12', 'S13'], 'Payload width excluding ECC; two 32-bit DDR5 subchannels are not a host channel count')
        result.append(dict(id=cid, family=family, object_level=level, maturity=maturity, fields=values))
    return result


def catalog_candidates():
    return [dict(id=c['id'], family=c['family'], object_level=c['object_level'], component_object_level=c['object_level'], units_per_object=1,
                 capacity_bytes=c['fields']['capacity_bytes']['value'], sustained_bw_bytes_s=None, power_w=None, max_modules=None,
                 channels_per_module=c['fields']['channels']['value'], provenance='public_catalog') for c in public_catalog()]


def gap_schema():
    rows = [
        ('sustained_bw_bytes_s', 'B/s', 'DRAM', 'Read/write mix, access size, queue depth, populated channels, concurrent hosts'),
        ('power_w', 'W', 'DRAM', 'Idle/active/peak/transient, voltage and clock'),
        ('p99_latency_ns', 'ns', 'DRAM', 'Contention, sample count, access pattern; retain p50/p999 separately'),
        ('thermal_throttle_ratio', 'ratio', 'rack', 'Coolant inlet, junction temperature, duration and flow'),
        ('fabric_bw_bytes_s', 'B/s', 'rack', 'Direction, bisection, protocol overhead and shared topology'),
        ('psu_efficiency', 'ratio', 'rack', 'Load, redundancy and transient reserve'),
        ('context_distribution', 'tokens', 'workload', 'p50/p95/p99 and workload class'),
        ('prefix_reuse_ratio', 'ratio', 'workload', 'Hot-set distribution, lifetime, KV policy'),
        ('metadata_bytes_per_request', 'B/request', 'workload', 'Control metadata separate from KV payload')]
    paths = {'sustained_bw_bytes_s': 'candidates[].sustained_bw_bytes_s', 'power_w': 'candidates[].power_w',
             'p99_latency_ns': 'candidates[].p99_latency_ns', 'fabric_bw_bytes_s': 'rack.fabric_bw_bytes_s',
             'psu_efficiency': 'rack.psu_efficiency', 'prefix_reuse_ratio': 'workload.prefix_reuse_ratio',
             'metadata_bytes_per_request': 'workload.metadata_bytes_per_request'}
    return dict(schema_version=1, scope='DRAM/rack/workload only; no internal data collected',
                fields=[dict(name=n, unit=u, scope=s, value=None, source=None, conditions=c,
                             input_path=paths.get(n), implementation_status='input_supported' if n in paths else 'not_implemented') for n,u,s,c in rows],
                override_contract={'candidate_id': None, 'values': {}, 'provenance': 'local_override', 'measurement_conditions': None, 'source_reference': None},
                instruction='Keep overrides in a separate local file; explicitly construct API candidates. Never mutate public catalog or infer missing values. No automatic ingestion or private-data lookup.')


def roadmap_context():
    return copy.deepcopy([
        dict(id='ddr6-2023-roadmap', source='S07', kind='roadmap', year=2028, pin_rate_mbit_s=9600, note='Historical projection; not normative default'),
        dict(id='dgx-vera-rubin-nvl72', source='S08', kind='vendor_reported', object_level='rack', gpu_count=72, cpu_count=36, capacity_bytes=20.7e12, peak_bw_bytes_s=1400e12),
        dict(id='amd-helios', source='S09', kind='vendor_reported', object_level='rack', gpu_count=72, capacity_bytes=31e12, peak_bw_bytes_s=1.7e15, scale_up_bw_bytes_s=260e12, scale_out_bw_bytes_s=43e12),
        dict(id='800-vdc', source='S10', kind='roadmap', year=2027, power_w=1e6, note='Architecture target, not a product TDP')])
