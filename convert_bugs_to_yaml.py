#!/usr/bin/env python3
"""
Convert bug_info.txt files to YAML format.
This script recursively finds all bug_info.txt files and converts them to bug_info.yaml
in the same directory.
"""

import os
import re
import yaml
from pathlib import Path


def parse_bug_info(file_path):
    """Parse a bug_info.txt file and return a dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    bug_data = {}

    # Extract bug number from the first line
    bug_match = re.search(r'Bug #(\d+)', content)
    if bug_match:
        bug_data['bug_number'] = int(bug_match.group(1))

    # Extract description (everything between "Description:" and the next field)
    desc_match = re.search(r'Description:\s*\n(.*?)(?=\nType:|$)', content, re.DOTALL)
    if desc_match:
        full_description = desc_match.group(1).strip()

        # Check if there's a Campfire line in the description
        campfire_match = re.search(r'^Campfire:\s*(.+)$', full_description, re.MULTILINE)
        if campfire_match:
            # Extract campfire and remove it from description
            bug_data['campfire'] = campfire_match.group(1).strip()
            # Remove the campfire line from description
            description = re.sub(r'\n*Campfire:\s*.+$', '', full_description, flags=re.MULTILINE).strip()
            bug_data['description'] = description
        else:
            bug_data['description'] = full_description

    # Extract Type and convert to list
    type_match = re.search(r'Type:\s*(.+)', content)
    if type_match:
        type_string = type_match.group(1).strip()
        # Split by comma and strip whitespace from each type
        bug_data['type'] = [t.strip() for t in type_string.split(',')]

    # Extract Severity
    severity_match = re.search(r'Severity:\s*(.+)', content)
    if severity_match:
        bug_data['severity'] = severity_match.group(1).strip()

    # Extract Reproducibility
    repro_match = re.search(r'Reproducibility:\s*(.+)', content)
    if repro_match:
        bug_data['reproducibility'] = repro_match.group(1).strip()

    # Extract Status
    status_match = re.search(r'Status:\s*(.+)', content)
    if status_match:
        bug_data['status'] = status_match.group(1).strip()

    # Extract Version
    version_match = re.search(r'Version:\s*(.+)', content)
    if version_match:
        bug_data['version'] = version_match.group(1).strip()

    return bug_data


def convert_bug_to_yaml(txt_file_path):
    """Convert a single bug_info.txt file to YAML format."""
    try:
        # Parse the text file
        bug_data = parse_bug_info(txt_file_path)

        # Create the YAML file path (same directory, different extension)
        yaml_file_path = txt_file_path.parent / 'bug_info.yaml'
        if yaml_file_path.exists:
            print(f"File: {yaml_file_path} already exists")
            return 

        # Write to YAML file
        with open(yaml_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(bug_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"✓ Converted: {txt_file_path} -> {yaml_file_path}")
        return True

    except Exception as e:
        print(f"✗ Error converting {txt_file_path}: {e}")
        return False


def main():
    """Find all bug_info.txt files and convert them to YAML."""
    # Get the script's directory (ClaudePlayground)
    base_dir = Path(__file__).parent

    # Find all bug_info.txt files recursively
    bug_files = list(base_dir.rglob('bug_info.txt'))

    if not bug_files:
        print("No bug_info.txt files found!")
        return

    print(f"Found {len(bug_files)} bug_info.txt files\n")

    # Convert each file
    success_count = 0
    for bug_file in bug_files:
        if convert_bug_to_yaml(bug_file):
            success_count += 1

    print(f"\n{'='*50}")
    print(f"Conversion complete: {success_count}/{len(bug_files)} files converted successfully")


if __name__ == '__main__':
    main()
