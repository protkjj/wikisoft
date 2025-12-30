import sys
import pathlib
from pprint import pprint

# Ensure project root on path
root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from internal.parsers.ceragem_parser import parse_all


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 internal/tools/run_parse_summary.py <excel_file_path>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, 'rb') as f:
        parsed = parse_all(f.read())
    summary = {
        'active': parsed['active']['summary'],
        'retired_dc': parsed['retired_dc']['summary'],
        'additional': parsed['additional']['summary'],
        'core_present': parsed['core_info'] is not None,
        'core_info_keys': list(parsed['core_info'].keys()) if parsed['core_info'] else None,
        'cross_checks': parsed['cross_checks'],
    }
    pprint(summary)


if __name__ == '__main__':
    main()
