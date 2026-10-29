"""Case-sensitive units; no implicit bit/byte or decimal/binary conversion."""
from .api import InputError, number

UNITS = {'B': ('size', 1), 'bit': ('size', 1/8), 'Gb': ('size', 10**9/8),
         'GB': ('size', 10**9), 'TB': ('size', 10**12), 'GiB': ('size', 2**30), 'TiB': ('size', 2**40),
         'B/s': ('rate', 1), 'Gbit/s': ('rate', 10**9/8), 'GB/s': ('rate', 10**9),
         'TB/s': ('rate', 10**12), 'GiB/s': ('rate', 2**30), 'TiB/s': ('rate', 2**40),
         'W': ('power', 1), 'kW': ('power', 1000), 'ns': ('time', 1), 'ms': ('time', 10**6)}


def convert(value, source, target):
    if source not in UNITS or target not in UNITS or UNITS[source][0] != UNITS[target][0]:
        raise InputError('unsupported or incompatible units')
    number(value, 'unit value', nullable=True)
    return None if value is None else number(value * UNITS[source][1] / UNITS[target][1], 'converted value')
