#!/usr/bin/env python3
"""
Parse and display bug_info.yaml
"""
import sys

import yaml
import argparse
from pathlib import Path


def parse_yaml_file(yaml_path):
    """Parse a single YAML file."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as _:
        return None


def main():
    parser = argparse.ArgumentParser(description='Parse and display bug YAML file')
    parser.add_argument('path', nargs='?', default=None,
                       help='Path to a bug_info.yaml file.')
    args = parser.parse_args()

    if args.path:
        path = Path(args.path)
        if not path.is_file():
            print(f"Error: {args.path} is not a valid file.", file=sys.stderr)
            return
    else:
        print(f"Not a valid path.", file=sys.stderr)
        return

    bug_data = parse_yaml_file(path)
    if bug_data:
        print('')
        for k, v in bug_data.items():
            print(f"{k}: {v}")
        print('\nRaw data:\n', bug_data)
    else:
        print(f"Error parsing {path}", file=sys.stderr)


if __name__ == '__main__':
    main()
