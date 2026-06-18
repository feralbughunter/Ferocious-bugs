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
from typing import Dict, List, Any


# Validation constants based on overall_info.txt
ALLOWED_TYPES = {
    'Item placement',
    'Collision missing',
    'Level escape',
    'Broken model',
    'Interaction issue',
    'Player confusion',
    'Invisible wall',
    'Game breaking',
    'Broken logic'
}

ALLOWED_SEVERITIES = {'High', 'Medium', 'Low'}
ALLOWED_STATUSES = {'fixed', 'unfixed', 'notabug'}
REQUIRED_FIELDS = {'bug_number', 'description', 'type', 'severity', 'status'}


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


def validate_bug_data(bug_data: Dict[str, Any], file_path: Path) -> List[str]:
    """
    Validate bug data against required fields and allowed values.
    Returns a list of validation errors (empty list if valid).
    """
    errors = []

    # Check required fields
    missing_fields = REQUIRED_FIELDS - bug_data.keys()
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")

    # Validate bug_number is an integer
    if 'bug_number' in bug_data:
        if not isinstance(bug_data['bug_number'], int):
            errors.append(f"bug_number must be an integer, got: {type(bug_data['bug_number']).__name__}")

    # Validate type field (must be a list and all values must be in allowed types)
    if 'type' in bug_data:
        if not isinstance(bug_data['type'], list):
            errors.append(f"type must be a list, got: {type(bug_data['type']).__name__}")
        elif not bug_data['type']:
            errors.append("type list cannot be empty")
        else:
            invalid_types = [t for t in bug_data['type'] if t not in ALLOWED_TYPES]
            if invalid_types:
                errors.append(f"Invalid type values: {', '.join(invalid_types)}. "
                            f"Allowed: {', '.join(sorted(ALLOWED_TYPES))}")

    # Validate severity
    if 'severity' in bug_data:
        if bug_data['severity'] not in ALLOWED_SEVERITIES:
            errors.append(f"Invalid severity: '{bug_data['severity']}'. "
                         f"Allowed: {', '.join(sorted(ALLOWED_SEVERITIES))}")

    # Validate status
    if 'status' in bug_data:
        if bug_data['status'] not in ALLOWED_STATUSES:
            errors.append(f"Invalid status: '{bug_data['status']}'. "
                         f"Allowed: {', '.join(sorted(ALLOWED_STATUSES))}")

    # Validate description is not empty (free-form text but should exist)
    if 'description' in bug_data:
        if not isinstance(bug_data['description'], str) or not bug_data['description'].strip():
            errors.append("description must be a non-empty string")

    # Validate campfire if present (free-form text, optional field)
    if 'campfire' in bug_data:
        if not isinstance(bug_data['campfire'], str):
            errors.append(f"campfire must be a string, got: {type(bug_data['campfire']).__name__}")

    return errors


def convert_bug_to_yaml(txt_file_path):
    """Convert a single bug_info.txt file to YAML format with validation."""
    try:
        # Parse the text file
        bug_data = parse_bug_info(txt_file_path)

        # Validate the parsed data
        validation_errors = validate_bug_data(bug_data, txt_file_path)
        if validation_errors:
            print(f"✗ Validation failed for {txt_file_path}:")
            for error in validation_errors:
                print(f"  - {error}")
            return False

        # Create the YAML file path (same directory, different extension)
        yaml_file_path = txt_file_path.parent / 'bug_info.yaml'

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
        else:
            return

    print(f"\n{'='*50}")
    print(f"Conversion complete: {success_count}/{len(bug_files)} files converted successfully")


if __name__ == '__main__':
    main()
