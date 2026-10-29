"""Public memory-family evidence with component and commercialization scopes.

These are declarations, not a capability ranking or hardware measurements. Each
call returns fresh data. A missing value is unknown, never an absent market.
"""
from .strategy import quantity


CHECKED_AT = '2026-10-29'


def portfolio_sources():
    """Return issuer-authored sources and the limited claims used below."""
    rows = [
        ('PF01', 'JEDEC announces JESD270-4 HBM4',
         'https://www.businesswire.com/news/home/20250416843598/en/JEDEC-and-Industry-Leaders-Collaborate-to-Release-JESD270-4-HBM4-Standard-Advancing-Bandwidth-Efficiency-and-Capacity-for-AI-and-HPC', '2025-04-16',
         'Issuer-authored JEDEC release. Original 2025 standard baseline, not a ceiling for all later products or revisions; the later standard text was not verified.',
         ['Original baseline: up to 8 Gb/s per pin, 2048-bit interface per stack, and approximately 2 TB/s.',
          '32 independent channels per stack, with two pseudo-channels per channel.',
          '24 or 32 Gb dies; 4/8/12/16-high configurations; up to 64 GB for a 32 Gb 16-high stack.']),
        ('PF02', 'Samsung announces commercial HBM4 shipments',
         'https://news.samsung.com/global/samsung-ships-industry-first-commercial-hbm4-with-ultimate-performance-for-ai-computing', '2026-02-12',
         'Vendor component-production and shipment claim, not a matched-workload system result. Pin speed is not sustained application bandwidth.',
         ['Mass production and commercial customer shipments announced.',
          '12-high capacity options of 24 and 36 GB; 2048 I/O pins.',
          '11.7 Gb/s pin speed, potentially up to 13 Gb/s; vendor maximum 3.3 TB/s per stack.',
          '16-high capacity up to 48 GB is a future offering tied to customer timing.']),
        ('PF03', 'Micron announces HBM4 and SOCAMM2 volume production',
         'https://investors.micron.com/news/press-release/2026/Micron-in-High-Volume-Production-of-HBM4-Designed-for-NVIDIA-Vera-Rubin-PCIe-Gen6-SSD-and-SOCAMM2-03-16-2026/default.aspx', '2026-03-16',
         'HBM speed uses internal testing and confidential customer test vehicles. Relative power claims do not supply absolute DRAM watts. Component shipments do not prove a customer workload SLO.',
         ['36 GB 12-high HBM4 volume shipments began in calendar Q1 2026; greater than 11 Gb/s per pin and greater than 2.8 TB/s per stack.',
          '48 GB 16-high HBM4 samples shipped to customers.',
          '192 GB SOCAMM2 in high-volume production.',
          'Vera CPU configurations enable up to 2 TB and 1.2 TB/s per CPU; these are not one-module figures.']),
        ('PF04', 'NVIDIA HGX platform and Rubin system specifications',
         'https://www.nvidia.com/en-us/data-center/hgx/', None,
         'Undated rolling product page checked on the stated date. Manufacturer reports system shipping; live inventory and customer acceptance were not independently verified. Do not divide rounded system totals into exact per-GPU values.',
         ['NVIDIA describes manufacturing at scale and shipping Vera Rubin-based systems.',
          'HGX Rubin NVL8 includes eight Rubin GPUs; the system table lists 2 TB HBM4 and 130 TB/s.']),
        ('PF05', 'Samsung announces HBM4E sample shipments',
         'https://news.samsung.com/uk/samsung-begins-shipment-of-industry-first-hbm4e-samples', '2026-06-01',
         'Samples and roadmap options, not verified volume production or system availability. Do not combine 16 Gb/s and 3.6 TB/s as a single qualified operating point.',
         ['12-high 48 GB samples shipped to major customers.',
          'Stable pin speed 14 Gb/s, scalable to 16 Gb/s; vendor-reported bandwidth up to 3.6 TB/s per stack.',
          '8-high 32 GB and 16-high 64 GB are planned options; mass production follows customer schedules.']),
        ('PF06', 'Samsung describes HBM5 architecture at GTC 2026',
         'https://semiconductor.samsung.com/news-events/tech-blog/architecting-the-ai-era-samsung-electronics-and-nvidia-define-the-future-at-gtc-2026/', None,
         'Official account of GTC 2026; publication date is not displayed in the retrieved body. Architecture plans do not disclose qualified memory specifications or shipment dates.',
         ['Samsung describes an HBM5 architecture and plans for a 1c core die and a 2 nm base die.',
          'No HBM5 capacity, bus width, pin rate, bandwidth or power value is used in this evidence set.']),
        ('PF07', 'Samsung Memory Tech Day: historical DDR6 roadmap',
         'https://semiconductor.samsung.com/news-events/tech-blog/memory-tech-day-memory-in-the-age-of-ai-data/', '2023-12-04',
         'Historical vendor roadmap from the October 20, 2023 event. It does not establish a current finalized JEDEC DDR6 specification, delivery commitment or available product.',
         ['Samsung projected DDR6 at 9600 Mbps and availability in 2028.',
          'The historical projection remains narrative evidence; current product specification fields stay unknown.']),
        ('PF08', 'JEDEC publishes GDDR7 graphics-memory standard',
         'https://www.businesswire.com/news/home/20240305637931/en/JEDEC-Publishes-GDDR7-Graphics-Memory-Standard', '2024-03-05',
         'Issuer-authored release for GDDR7, not general-purpose DDR7. Its existence neither establishes DDR7 specifications nor proves their absence.',
         ['JESD239 is the GDDR7 graphics-memory standard; it must not be relabeled DDR7.']),
        ('PF09', 'JEDEC publishes JESD209-6 LPDDR6',
         'https://www.businesswire.com/news/home/20250709315796/en/JEDEC-Releases-New-LPDDR6-Standard-to-Enhance-Mobile-and-AI-Memory-Performance', '2025-07-09',
         'Issuer-authored JEDEC release establishes the standard, not a shipping device or sustained application result. Data-signal width is not assumed to equal useful-payload width.',
         ['Two sub-channels per die, each with 12 DQ signals.',
          '32-byte access granularity and on-the-fly 32/64-byte access.',
          'DVFSL, dynamic efficiency mode, PRAC and reliability features are described.']),
        ('PF10', 'SK hynix validates development of 1c LPDDR6',
         'https://news.skhynix.com/en/1c-lpddr6-development-2026/', '2026-03-10',
         'Development validation and a production/supply plan, not retrospective proof that the plan was completed. A 16 Gb die is not a 16 GB package.',
         ['16 Gb LPDDR6 DRAM developed and development validation completed.',
          'Base operating speed is greater than 10.7 Gb/s.',
          'Mass-production preparations were planned for H1 2026 and supply for H2 2026.']),
        ('PF11', 'Samsung validates LPDDR6 on Qualcomm Snapdragon platform',
         'https://semiconductor.samsung.com/news-events/tech-blog/samsung-lpddr6-advancing-low-power-memory-for-ai-with-industry-first-validation-on-qualcomm-technologies-new-snapdragon-platform/', None,
         'The search index dates the page September 22, 2026, but the retrieved body does not display a publication date. Sampling/platform validation is not consumer-device shipment. The physical scope of the separate 114 GB/s claim is not sufficiently resolved for a normalized product point.',
         ['16 GB LPDDR6 validated at I/O speeds up to 10.7 Gb/s on Snapdragon 8 Elite Extreme Gen 6.',
          'Samsung reports sampling and validation completed.',
          'A separate up-to-114 GB/s bandwidth claim is retained only as narrative evidence; module/die bandwidth remains unknown here.']),
        ('PF12', 'Micron announces volume shipments of 128 GB DDR5 RDIMMs',
         'https://investors.micron.com/news/press-release/2024/Micron-First-to-Ship-Critical-Memory-for-AI-Data-Centers-05-01-2024/default.aspx', '2024-05-01',
         'Vendor shipment and platform-validation evidence. Module data rate is not a physical clock or socket bandwidth, and availability does not establish live stock.',
         ['128 GB RDIMMs using monolithic 32 Gb dies, at data rates up to 5600 MT/s.',
          'Validated and shipping in volume on leading server platforms.']),
        ('PF13', 'Micron DDR5 MRDIMM product portfolio',
         'https://www.micron.com/products/memory/dram-modules/mrdimm', None,
         'Undated current product page, not a live inventory check. Requires compatible Intel server CPUs; module ranges do not imply every capacity/speed combination is qualified.',
         ['MRDIMM capacity range 32 to 256 GB; data rates up to 8800 MT/s.',
          'Vendor describes readiness for data-center deployment with compatible Intel server CPUs.']),
        ('PF14', 'NVIDIA Jetson Thor general-availability announcement',
         'https://developer.nvidia.com/blog/introducing-nvidia-jetson-thor-the-ultimate-platform-for-physical-ai/', '2025-08-25',
         'T5000 is one SOM, not one LPDDR die/package. 40–130 W is the whole-SOM operating range, not DRAM power. Bandwidth is a vendor envelope.',
         ['Jetson T5000 module and Jetson AGX Thor developer kit generally available.',
          'T5000: 128 GB, 256-bit LPDDR5X, 273 GB/s; whole-SOM operating range 40–130 W.']),
        ('PF15', 'Micron introduces LPDDR5X SOCAMM2 samples',
         'https://investors.micron.com/news/press-release/2025/Micron-Delivers-Industrys-Highest-Capacity-SOCAMM2-for-Low-Power-DRAM-in-the-AI-Data-Center-10-22-2025/default.aspx', '2025-10-22',
         'Sampling-stage specification envelope. Later production status for 192 GB is sourced separately. Do not apply the power-comparison footnote for a 128 GB configuration to infer a 192 GB module bus width or watts.',
         ['192 GB SOCAMM2 built with LPDDR5X; customer samples up to 192 GB and 9.6 Gb/s.',
          'High-volume production was to align with customer launch schedules.']),
        ('PF16', 'JEDEC updates DDR5 JESD79-5C',
         'https://www.businesswire.com/news/home/20240417886230/en/JEDEC-Updates-JESD79-5C-DDR5-SDRAM-Standard-Elevating-Performance-and-Security-for-Next-Gen-Technologies', '2024-04-17',
         'A published standard revision is not a promise that every DDR5 module or memory controller supports its maximum rate.',
         ['DDR5 timing parameters were extended to 8800 Mbps in JESD79-5C.',
          'The update introduces Per-Row Activation Counting.']),
    ]
    return [dict(id=i, title=t, url=u, published=p, checked_at=CHECKED_AT,
                 caveat=c, claims=list(claims)) for i, t, u, p, c, claims in rows]


def _q(value=None, *, unit, scope, sources=(), kind='unknown', note='', minimum=None, maximum=None):
    return quantity(value, unit=unit, scope=scope, sources=sources, kind=kind,
                    note=note, minimum=minimum, maximum=maximum)


def _record(identifier, scope, status, status_as_of, sources, note, **values):
    units = dict(capacity_bytes='B', peak_bw_bytes_s='B/s', pin_rate_bps='bit/s/pin', bus_width_bits='bit')
    record = dict(id=identifier, scope=scope, commercial_status=status,
                  status_as_of=status_as_of, evidence_ids=list(sources), note=note)
    for field, unit in units.items():
        record[field] = values.get(field, _q(unit=unit, scope=scope, sources=sources,
                                            note='No sufficiently scoped value established by these sources.'))
    return record


def _nominal(value=None, *, unit, scope, sources, note='', minimum=None, maximum=None):
    return _q(value, unit=unit, scope=scope, sources=sources, kind='public_nominal',
              note=note, minimum=minimum, maximum=maximum)


def product_families():
    """Return six requested families plus current DDR5/LPDDR5X alternatives.

    GB/Gb labels are preserved in notes and normalized using decimal multipliers.
    No record contains measured usable capacity, sustained BW, DRAM watts or p99.
    """
    unknowns = ['usable_capacity_bytes', 'sustained_bw_bytes_s', 'dram_power_w', 'p99_latency_ns']
    capacity_note = 'Vendor GB label normalized as decimal GB; not measured allocatable bytes. Preserve unit interpretation when comparing close boundaries.'
    peak_note = 'Vendor peak/envelope; not sustained bandwidth or a matched-workload result.'
    families = []

    scope = 'one HBM stack'
    families.append(dict(id='HBM4', label='HBM4', unpublished_fields=list(unknowns), records=[
        _record('hbm4-jedec-2025-baseline', scope, 'published_standard_baseline', '2025-04-16', ['PF01'],
                'Original JESD270-4 baseline only; not a shipping SKU or a maximum across later revisions. 32 channels, two pseudo-channels/channel.',
                capacity_bytes=_q(unit='B', scope=scope, sources=['PF01'], kind='public_standard_limit', maximum=64e9,
                                  note='32 Gb die × 16-high gives the standard stated maximum 64 GB; not a shipping-device claim.'),
                peak_bw_bytes_s=_q(2.048e12, unit='B/s', scope=scope, sources=['PF01'], kind='derived_theoretical',
                                   note='8e9 bit/s/pin × 2048 / 8. Original release rounds this to about 2 TB/s; not payload/sustained BW.'),
                pin_rate_bps=_q(unit='bit/s/pin', scope=scope, sources=['PF01'], kind='public_standard_limit', maximum=8e9),
                bus_width_bits=_q(2048, unit='bit', scope=scope, sources=['PF01'], kind='public_standard')),
        _record('hbm4-samsung-12h', scope, 'vendor_claimed_mass_production_and_commercial_shipments', '2026-02-12', ['PF02'],
                '12-high family envelope. Capacity options are the discrete 24 and 36 GB values, not every value in the interval. Speed/capacity combinations are not individually qualified here.',
                capacity_bytes=_nominal(unit='B', scope=scope, sources=['PF02'], minimum=24e9, maximum=36e9, note=capacity_note + ' Discrete options: 24 GB or 36 GB.'),
                peak_bw_bytes_s=_q(unit='B/s', scope=scope, sources=['PF02'], kind='public_peak', maximum=3.3e12, note=peak_note),
                pin_rate_bps=_q(unit='bit/s/pin', scope=scope, sources=['PF02'], kind='public_vendor_envelope', minimum=11.7e9, maximum=13e9,
                                note='11.7 Gb/s announced pin speed; up to 13 Gb/s enhancement. Neither is application sustained BW.'),
                bus_width_bits=_nominal(2048, unit='bit', scope=scope, sources=['PF02'])),
        _record('hbm4-samsung-16h-plan', scope, 'vendor_planned_variant', '2026-02-12', ['PF02'],
                '16-high capacity extension tied to future customer timelines; do not inherit 12-high speed or shipment status.',
                capacity_bytes=_q(unit='B', scope=scope, sources=['PF02'], kind='public_roadmap', maximum=48e9, note=capacity_note)),
        _record('hbm4-micron-36gb-12h', scope, 'vendor_claimed_volume_shipments', '2026-03-16', ['PF03'],
                '36 GB 12-high; volume shipments began in calendar Q1 2026. Open-ended lower bounds are vendor claims, not measured sustained performance.',
                capacity_bytes=_nominal(36e9, unit='B', scope=scope, sources=['PF03'], note=capacity_note),
                peak_bw_bytes_s=_q(unit='B/s', scope=scope, sources=['PF03'], kind='public_vendor_lower_bound', minimum=2.8e12,
                                   note='Vendor says strictly greater than 2.8 TB/s. min encodes the quoted threshold, not an inclusive guarantee or an upper limit.'),
                pin_rate_bps=_q(unit='bit/s/pin', scope=scope, sources=['PF03'], kind='public_vendor_lower_bound', minimum=11e9,
                                note='Vendor says strictly greater than 11 Gb/s based on internal testing/customer test vehicles.')),
        _record('hbm4-micron-48gb-16h-sample', scope, 'samples_shipped', '2026-03-16', ['PF03'],
                '48 GB 16-high samples; no speed or volume-production inference from the 36 GB product.',
                capacity_bytes=_nominal(48e9, unit='B', scope=scope, sources=['PF03'], note=capacity_note)),
        _record('hbm4-hgx-rubin-nvl8-system', 'eight GPU system HBM memory', 'vendor_reported_system_shipping', CHECKED_AT, ['PF04'],
                'Undated current system page. Aggregate 2 TB/130 TB/s belong to HGX Rubin NVL8, not one stack or GPU. No division into exact per-GPU values.',
                capacity_bytes=_nominal(2e12, unit='B', scope='eight GPU system HBM memory', sources=['PF04'], note='Rounded vendor 2 TB system total normalized as decimal; not measured usable memory.'),
                peak_bw_bytes_s=_q(130e12, unit='B/s', scope='eight GPU system HBM memory', sources=['PF04'], kind='public_peak', note=peak_note)),
    ]))

    families.append(dict(id='HBM4E', label='HBM4E', unpublished_fields=list(unknowns), records=[
        _record('hbm4e-samsung-48gb-12h-sample', scope, 'samples_shipped', '2026-06-01', ['PF05'],
                '12-high samples. Mass production was planned against customer schedules; no later completion is inferred. 14/16 Gb/s and 3.6 TB/s are separately reported claims, not one qualified point.',
                capacity_bytes=_nominal(48e9, unit='B', scope=scope, sources=['PF05'], note=capacity_note),
                peak_bw_bytes_s=_q(unit='B/s', scope=scope, sources=['PF05'], kind='public_peak', maximum=3.6e12, note=peak_note + ' Do not replace with a rate×width extrapolation.'),
                pin_rate_bps=_q(unit='bit/s/pin', scope=scope, sources=['PF05'], kind='public_vendor_envelope', minimum=14e9, maximum=16e9,
                                note='14 Gb/s stable pin speed; 16 Gb/s scalable potential. Bus width is not assumed from another family record.')),
        _record('hbm4e-samsung-32gb-8h-plan', scope, 'vendor_planned_variant', '2026-06-01', ['PF05'],
                'Planned 8-high option; no inherited sample/volume status or performance.',
                capacity_bytes=_q(32e9, unit='B', scope=scope, sources=['PF05'], kind='public_roadmap', note=capacity_note)),
        _record('hbm4e-samsung-64gb-16h-plan', scope, 'vendor_planned_variant', '2026-06-01', ['PF05'],
                'Planned 16-high option; no inherited sample/volume status or performance.',
                capacity_bytes=_q(64e9, unit='B', scope=scope, sources=['PF05'], kind='public_roadmap', note=capacity_note)),
    ]))

    future_fields = ['capacity_bytes', 'peak_bw_bytes_s', 'pin_rate_bps', 'bus_width_bits'] + unknowns
    families.append(dict(id='HBM5', label='HBM5', unpublished_fields=list(future_fields), records=[
        _record('hbm5-architecture-roadmap', scope, 'architecture_roadmap', CHECKED_AT, ['PF06'],
                'Official GTC 2026 architecture plan, publication date not displayed. Numeric memory specifications and delivery dates remain unknown; 1c/2 nm process plans are not memory performance.')]))
    families.append(dict(id='DDR6', label='DDR6', unpublished_fields=list(future_fields), records=[
        _record('ddr6-historical-roadmap', 'future DDR6 device', 'historical_vendor_roadmap', '2023-12-04', ['PF07'],
                'Historical 9600 Mbps/2028 projection stays in source claims only. It is not a current qualified specification or production commitment; all numerical product fields remain null.')]))
    families.append(dict(id='DDR7', label='DDR7', unpublished_fields=list(future_fields), records=[
        _record('ddr7-public-spec-not-verified', 'future general-purpose DDR7 device', 'not_verified_in_public_sources', CHECKED_AT, ['PF08'],
                'No general-purpose DDR7 specification was verified in this bounded search. This is an evidence gap, not proof of nonexistence. PF08 establishes only that GDDR7 is a different graphics standard.')]))

    families.append(dict(id='LPDDR6', label='LPDDR6', unpublished_fields=list(unknowns), records=[
        _record('lpddr6-jedec-standard', 'one LPDDR6 die', 'published_standard', '2025-07-09', ['PF09'],
                'Two sub-channels/die, 12 DQ/sub-channel; 32-byte granularity and 32/64-byte accesses. Do not infer package capacity or effective payload BW from the signal count.',
                bus_width_bits=_q(24, unit='bit', scope='one LPDDR6 die data signal interface', sources=['PF09'], kind='derived_standard_structure',
                                  note='2 sub-channels × 12 DQ. Physical data signal count; not an assumed effective-payload bus width.')),
        _record('lpddr6-skhynix-16gb-die-development', 'one LPDDR6 die', 'development_validated', '2026-03-10', ['PF10'],
                '16 Gb die, not 16 GB package. H1 preparation/H2 supply were plans at publication; calendar passage is not production evidence.',
                capacity_bytes=_q(2e9, unit='B', scope='one LPDDR6 die', sources=['PF10'], kind='derived_nominal',
                                  note='Vendor 16 Gb density divided by 8 with decimal Gb normalization; not measured allocatable capacity.'),
                pin_rate_bps=_q(unit='bit/s/pin', scope='one LPDDR6 die interface', sources=['PF10'], kind='public_vendor_lower_bound', minimum=10.7e9,
                                note='Vendor base operating speed is strictly greater than 10.7 Gb/s; threshold is not a maximum.')),
        _record('lpddr6-samsung-16gb-platform-validation', '16 GB LPDDR6 package on named mobile platform', 'vendor_claimed_platform_validation', CHECKED_AT, ['PF11'],
                '16 GB LPDDR6 validated on Snapdragon 8 Elite Extreme Gen 6. Retrieved body is undated; sampling/validation is not commercial handset shipment. Separate 114 GB/s claim has unresolved physical scope and stays narrative only.',
                capacity_bytes=_nominal(16e9, unit='B', scope='16 GB LPDDR6 package on named mobile platform', sources=['PF11'], note=capacity_note),
                pin_rate_bps=_q(unit='bit/s/pin', scope='validated LPDDR6 I/O', sources=['PF11'], kind='public_peak', maximum=10.7e9,
                                note='Up to 10.7 Gb/s validation claim; not a standard ceiling or sustained application rate.')),
    ]))

    families.append(dict(id='DDR5', label='DDR5 RDIMM / MRDIMM alternatives', unpublished_fields=list(unknowns), records=[
        _record('ddr5-jedec-5c', 'DDR5 SDRAM interface', 'published_standard', '2024-04-17', ['PF16'],
                'JESD79-5C timing extension; does not establish module/controller support for every speed.',
                pin_rate_bps=_q(unit='bit/s/pin', scope='DDR5 SDRAM interface', sources=['PF16'], kind='public_standard_limit', maximum=8.8e9,
                                note='8800 Mbps timing extension, not physical clock frequency.')),
        _record('ddr5-micron-128gb-rdimm', 'one DDR5 RDIMM', 'vendor_claimed_volume_shipments', '2024-05-01', ['PF12'],
                '128 GB RDIMM using monolithic 32 Gb dies; vendor platform-validation and volume-shipment claim. Socket bandwidth and memory power are unknown.',
                capacity_bytes=_nominal(128e9, unit='B', scope='one DDR5 RDIMM', sources=['PF12'], note=capacity_note),
                pin_rate_bps=_q(unit='bit/s/pin', scope='DDR5 RDIMM data interface', sources=['PF12'], kind='derived_nominal', maximum=5.6e9,
                                note='Published up to 5600 MT/s; one bit/DQ transfer. Not a 5.6 GHz physical clock; no socket BW inferred.')),
        _record('ddr5-micron-mrdimm-portfolio', 'one DDR5-based MRDIMM', 'vendor_described_deployable_portfolio', CHECKED_AT, ['PF13'],
                'Current portfolio on an undated page; compatible Intel server CPU required. Bounds do not enumerate discrete SKUs or qualify all capacity/rate combinations.',
                capacity_bytes=_nominal(unit='B', scope='one DDR5-based MRDIMM', sources=['PF13'], minimum=32e9, maximum=256e9, note=capacity_note + ' Portfolio bounds, not a continuous capacity offering.'),
                pin_rate_bps=_q(unit='bit/s/pin', scope='MRDIMM host data interface', sources=['PF13'], kind='derived_nominal', maximum=8.8e9,
                                note='Published up to 8800 MT/s at module host interface; not constituent DRAM clock or general DDR5-slot compatibility.')),
    ]))

    families.append(dict(id='LPDDR5X', label='LPDDR5X SOM / SOCAMM2 alternatives', unpublished_fields=list(unknowns), records=[
        _record('lpddr5x-jetson-t5000', 'one T5000 SOM unified memory', 'vendor_announced_general_availability', '2025-08-25', ['PF14'],
                'One SOM includes CPU/GPU and unified LPDDR5X. Its 40–130 W range is whole-SOM power; DRAM-only watts remain unknown.',
                capacity_bytes=_nominal(128e9, unit='B', scope='one T5000 SOM unified memory', sources=['PF14'], note=capacity_note),
                peak_bw_bytes_s=_q(273e9, unit='B/s', scope='one T5000 SOM unified memory', sources=['PF14'], kind='public_peak', note=peak_note),
                bus_width_bits=_nominal(256, unit='bit', scope='one T5000 SOM memory interface', sources=['PF14'])),
        _record('lpddr5x-socamm2-192gb-sampling-envelope', 'one LPDDR5X SOCAMM2 module', 'samples_shipped', '2025-10-22', ['PF15'],
                'Historical sampling envelope. Later 192 GB production is a separate record; no published bus width is transferred from another capacity configuration.',
                capacity_bytes=_nominal(192e9, unit='B', scope='one LPDDR5X SOCAMM2 module', sources=['PF15'], note=capacity_note),
                pin_rate_bps=_q(unit='bit/s/pin', scope='SOCAMM2 memory interface', sources=['PF15'], kind='public_peak', maximum=9.6e9,
                                note='Up to 9.6 Gb/s sampling-portfolio claim; no per-module byte bandwidth derived without a matched bus configuration.')),
        _record('lpddr5x-socamm2-192gb-production', 'one LPDDR5X SOCAMM2 module', 'vendor_claimed_high_volume_production', '2026-03-16', ['PF03', 'PF15'],
                '192 GB high-volume production confirmed by the later vendor release; earlier source establishes LPDDR5X family. Production release does not independently qualify the earlier maximum pin-rate bin.',
                capacity_bytes=_nominal(192e9, unit='B', scope='one LPDDR5X SOCAMM2 module', sources=['PF03', 'PF15'], note=capacity_note)),
    ]))
    return families
