import argparse
import json
import sys
from pathlib import Path
from .api import analyze, InputError
from .demo import demo, encode
from .integrated import analyze_integrated, compare_scenarios


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise InputError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description='Offline conditional DRAM analytical simulator')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('evaluate')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('integrated')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('compare')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('demo')
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            demo(args.output)
        else:
            request = json.loads(args.input.read_text(encoding='utf-8'), object_pairs_hook=pairs)
            if args.command == 'compare':
                from .api import obj
                obj(request, 'request scenarios', 'comparison')
                result = compare_scenarios(request.get('request'), request.get('scenarios'))
            else:
                result = (analyze_integrated if args.command == 'integrated' else analyze)(request)
            args.output.write_text(encode(result), encoding='utf-8')
    except (ValueError, TypeError, OverflowError, OSError, RecursionError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
