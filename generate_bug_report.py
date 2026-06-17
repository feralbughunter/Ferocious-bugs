#!/usr/bin/env python3
"""
Bug Report HTML Generator. Coded with Claude.
Scans Bugs_Map_* folders and generates a comprehensive HTML report.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from PIL import Image


def parse_overall_info(filepath):
    """Parse OVERALL_INFO.txt to extract version and common information."""
    info = {
        'version': '',
        'count': '',
        'bug_types': [],
        'severity_desc': '',
        'severity_options': '',
        'bug_status_info': [],
        'extra_info': [],
        'valid_bug_types': set(),
        'valid_severities': set(),
        'valid_statuses': set()
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')

    in_bug_types = False
    in_bug_status = False

    for line in lines:
        line = line.strip()

        if line.startswith('Version:'):
            info['version'] = line.split(':', 1)[1].strip()
        elif line.startswith('Count:'):
            info['count'] = line.split(':', 1)[1].strip()
        elif line.startswith('Bug types:'):
            in_bug_types = True
            in_bug_status = False
        elif line.startswith('Severity:'):
            info['severity_desc'] = line.split(':', 1)[1].strip()
            in_bug_types = False
        elif line.startswith('Options:') and 'severity_desc' in info and info['severity_desc']:
            info['severity_options'] = line.split(':', 1)[1].strip()
            # Extract valid severities from Options line
            for severity in info['severity_options'].split(','):
                info['valid_severities'].add(severity.strip())
        elif line.startswith('Bug Status:'):
            in_bug_status = True
            in_bug_types = False
        elif in_bug_types and ' - ' in line:
            info['bug_types'].append(line)
            # Extract bug type name (before the " - ")
            type_name = line.split(' - ')[0].strip()
            info['valid_bug_types'].add(type_name)
        elif in_bug_status and ' - ' in line:
            info['bug_status_info'].append(line)
            # Extract status name (before the " - ")
            status_name = line.split(' - ')[0].strip().lower()
            info['valid_statuses'].add(status_name)
        elif line and not in_bug_types and not in_bug_status:
            info['extra_info'].append(line)

    return info


def parse_bug_info(filepath):
    """Parse bug_info.txt to extract bug details."""
    bug = {
        'number': '',
        'description': '',
        'type': '',
        'severity': '',
        'reproducibility': '',
        'campfire': '',
        'status': 'unfixed',
        'version': ''
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        if line_stripped.startswith('Bug #'):
            bug['number'] = line_stripped.replace('Bug #', '').strip()
        elif line_stripped.startswith('Description:'):
            desc_lines = []
            for j in range(i + 1, len(lines)):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith('Type:') and not next_line.startswith('Campfire:'):
                    desc_lines.append(next_line)
                else:
                    break
            bug['description'] = ' '.join(desc_lines)
        elif line_stripped.startswith('Campfire:'):
            bug['campfire'] = line_stripped.split(':', 1)[1].strip()
        elif line_stripped.startswith('Type:'):
            bug['type'] = line_stripped.split(':', 1)[1].strip()
        elif line_stripped.startswith('Severity:'):
            bug['severity'] = line_stripped.split(':', 1)[1].strip()
        elif line_stripped.startswith('Reproducibility:'):
            bug['reproducibility'] = line_stripped.split(':', 1)[1].strip()
        elif line_stripped.startswith('Status:'):
            bug['status'] = line_stripped.split(':', 1)[1].strip().lower()
        elif line_stripped.startswith('Version:'):
            bug['version'] = line_stripped.split(':', 1)[1].strip()

    return bug


def get_severity_color(severity):
    """Return CSS color class based on severity."""
    severity_lower = severity.lower()
    if severity_lower == 'low':
        return 'severity-low'
    elif severity_lower == 'medium':
        return 'severity-medium'
    elif severity_lower == 'high':
        return 'severity-high'
    elif severity_lower == 'critical':
        return 'severity-critical'
    else:
        return 'severity-unknown'


def get_status_info(status):
    """Return status display text and CSS class."""
    status_lower = status.lower()
    if status_lower == 'fixed':
        return 'Fixed', 'status-fixed'
    elif status_lower == 'notabug':
        return 'Not a Bug', 'status-notabug'
    else:
        return 'Unfixed', 'status-unfixed'


def find_images(bug_dir):
    """Find all image files in a bug directory."""
    image_extensions = {'.jpg', '.jpeg', '.png'}
    images = []

    for file in sorted(os.listdir(bug_dir)):
        if Path(file).suffix.lower() in image_extensions:
            images.append(file)

    return images


def validate_bug_values(bugs_by_map, overall_info):
    """Validate that all bug values match the allowed values from overall_info.txt."""
    errors = []

    valid_bug_types = overall_info['valid_bug_types']
    valid_severities = overall_info['valid_severities']
    valid_statuses = overall_info['valid_statuses']

    for map_name, map_info in bugs_by_map.items():
        for bug_id, bug_data in map_info['bugs'].items():
            bug_path = bug_data['path']

            # Validate bug types (handle comma-separated types)
            bug_types = [t.strip() for t in bug_data['type'].split(',') if t.strip()]
            for bug_type in bug_types:
                if bug_type not in valid_bug_types:
                    errors.append(
                        f"Invalid Bug type '{bug_type}' in {bug_path}/bug_info.txt\n"
                        f"  Valid types: {', '.join(sorted(valid_bug_types))}"
                    )

            # Validate severity
            if bug_data['severity'] and bug_data['severity'] not in valid_severities:
                errors.append(
                    f"Invalid Severity '{bug_data['severity']}' in {bug_path}/bug_info.txt\n"
                    f"  Valid severities: {', '.join(sorted(valid_severities))}"
                )

            # Validate status
            if bug_data['status'] and bug_data['status'] not in valid_statuses:
                errors.append(
                    f"Invalid Bug Status '{bug_data['status']}' in {bug_path}/bug_info.txt\n"
                    f"  Valid statuses: {', '.join(sorted(valid_statuses))}"
                )

    return errors


def calculate_bug_statistics(bugs_by_map):
    """Calculate bug type, status, and severity statistics from all bugs."""
    type_counts = defaultdict(int)
    status_counts = defaultdict(int)
    severity_counts = defaultdict(int)

    for map_info in bugs_by_map.values():
        for bug_data in map_info['bugs'].values():
            # Count bug types (handle comma-separated types)
            bug_types = [t.strip() for t in bug_data['type'].split(',') if t.strip()]
            for bug_type in bug_types:
                type_counts[bug_type] += 1

            # Count bug statuses
            status_counts[bug_data['status']] += 1

            # Count severities
            severity_counts[bug_data['severity']] += 1

    return dict(type_counts), dict(status_counts), dict(severity_counts)


def generate_html(bugs_by_map, overall_info, total_bugs, type_counts, status_counts, severity_counts):
    """Generate the complete HTML document."""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ferocious bug reports</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}

        h3 {{
            color: #2c3e50;
            margin-top: 20px;
            margin-bottom: 10px;
        }}

        .info-section {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}

        .bug-types, .severity-info {{
            margin: 10px 0;
        }}

        .bug-types ul, .severity-info p, .severity-info ul {{
            margin-left: 20px;
        }}

        .map-section {{
            margin-top: 40px;
            border-top: 2px solid #bdc3c7;
            padding-top: 20px;
        }}

        .bug-list {{
            list-style: none;
            margin: 20px 0;
        }}

        .bug-list li {{
            margin: 8px 0;
            padding: 10px;
            background: #f8f9fa;
            border-left: 4px solid transparent;
            transition: all 0.2s;
        }}

        .bug-list li.bug-unfixed {{
            background: #ffebee;
        }}

        .bug-list li.bug-fixed {{
            background: #e8f5e9;
        }}

        .bug-list li.bug-notabug {{
            background: #e0e0e0;
        }}

        .bug-list li:hover {{
            transform: translateX(5px);
        }}

        .bug-list li.bug-unfixed:hover {{
            background: #ffcdd2;
        }}

        .bug-list li.bug-fixed:hover {{
            background: #c8e6c9;
        }}

        .bug-list li.bug-notabug:hover {{
            background: #bdbdbd;
        }}

        .bug-list a {{
            text-decoration: none;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .severity-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
            min-width: 70px;
            text-align: center;
        }}

        .severity-low {{
            background: #2ecc71;
            color: white;
        }}

        .severity-medium {{
            background: #f39c12;
            color: white;
        }}

        .severity-high {{
            background: #e74c3c;
            color: white;
        }}

        .severity-critical {{
            background: #c0392b;
            color: white;
        }}

        .severity-unknown {{
            background: #95a5a6;
            color: white;
        }}

        .bug-type {{
            color: #7f8c8d;
            font-style: italic;
        }}

        .bug-type-gamebreaking {{
            color: #c0392b;
            font-weight: bold;
            font-style: normal;
        }}

        .bug-detail {{
            margin: 40px 0;
            padding: 20px;
            background: #fafafa;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}

        .bug-detail h3 {{
            color: #2980b9;
            margin-top: 0;
        }}

        .bug-info {{
            margin: 15px 0;
        }}

        .bug-info strong {{
            color: #34495e;
        }}

        .status-badge {{
            display: inline-block;
            padding: 5px 10px;
            margin-left: 10px;
            border-radius: 3px;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .status-fixed {{
            background: #27ae60;
            color: white;
        }}

        .status-unfixed {{
            background: #e67e22;
            color: white;
        }}

        .status-notabug {{
            background: #95a5a6;
            color: white;
        }}

        .bug-images {{
            margin-top: 20px;
        }}

        .bug-images img {{
            max-width: 100%;
            height: auto;
            margin: 10px 10px 10px 0;
            border: 1px solid #ddd;
            border-radius: 3px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.2s;
        }}

        .bug-images img:hover {{
            transform: scale(1.02);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}

        .back-to-top {{
            display: inline-block;
            margin-top: 15px;
            padding: 8px 15px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            transition: background 0.2s;
        }}

        .back-to-top:hover {{
            background: #2980b9;
        }}

        .version-tag {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.9em;
            margin-left: 10px;
        }}

        .bug-count {{
            display: inline-block;
            background: #95a5a6;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 0.9em;
            margin-left: 10px;
        }}

        .github-link {{
            display: inline-block;
            margin-top: 10px;
            padding: 10px 15px;
            background: #24292e;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.2s;
        }}

        .github-link:hover {{
            background: #0366d6;
        }}

        .github-link::before {{
            content: "\\1F517 ";
            margin-right: 5px;
        }}

        .map-quick-links {{
            margin-top: 15px;
        }}

        .map-quick-links ul {{
            list-style: none;
            margin-left: 0;
            padding-left: 0;
        }}

        .map-quick-links li {{
            display: inline-block;
            margin-right: 15px;
        }}

        .map-quick-links a {{
            display: inline-block;
            padding: 8px 12px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            transition: background 0.2s;
        }}

        .map-quick-links a:hover {{
            background: #2980b9;
        }}

        .status-legend {{
            margin-top: 15px;
        }}

        .status-legend ul {{
            margin-left: 20px;
        }}

        .filter-section {{
            background: #e3f2fd;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border: 2px solid #2196f3;
        }}

        .filter-section h3 {{
            color: #1976d2;
            margin-top: 0;
            margin-bottom: 15px;
        }}

        .filter-group {{
            margin-bottom: 15px;
        }}

        .filter-group h4 {{
            color: #424242;
            margin-bottom: 8px;
            font-size: 1em;
        }}

        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .filter-btn {{
            padding: 8px 16px;
            border: 2px solid #90caf9;
            background: white;
            color: #1976d2;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.2s;
            user-select: none;
        }}

        .filter-btn:hover {{
            background: #e3f2fd;
            transform: translateY(-1px);
        }}

        .filter-btn.active {{
            background: #2196f3;
            color: white;
            border-color: #1976d2;
        }}

        .filter-btn.active:hover {{
            background: #1976d2;
        }}

        .bug-list li.filtered-hidden {{
            display: none;
        }}

        .clear-filters-btn {{
            padding: 10px 20px;
            border: 2px solid #d32f2f;
            background: #f44336;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.2s;
            margin-top: 10px;
        }}

        .clear-filters-btn:hover {{
            background: #d32f2f;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .clear-filters-btn:active {{
            transform: translateY(0);
        }}

        .filter-mode-container {{
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border: 2px solid #90caf9;
        }}

        .filter-mode-label {{
            font-weight: bold;
            color: #1976d2;
            margin-right: 15px;
            font-size: 1em;
        }}

        .switch-container {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }}

        .switch {{
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }}

        .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #2196f3;
            transition: 0.4s;
            border-radius: 34px;
        }}

        .slider:before {{
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: 0.4s;
            border-radius: 50%;
        }}

        input:checked + .slider {{
            background-color: #ff9800;
        }}

        input:checked + .slider:before {{
            transform: translateX(26px);
        }}

        .mode-text {{
            font-weight: bold;
            font-size: 1em;
            min-width: 40px;
        }}

        .mode-text.and-mode {{
            color: #2196f3;
        }}

        .mode-text.or-mode {{
            color: #ff9800;
        }}

        .filter-mode-description {{
            margin-top: 8px;
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Ferocious bug reports</h1>

        <div class="info-section">
            <p><a href="https://github.com/feralbughunter/Ferocious-bugs" target="_blank" class="github-link">GitHub bug repository</a></p>
            <h2>General Information</h2>
            <p><strong>Total Bugs Found:</strong> {total_bugs}</p>

            <div class="bug-types">
                <h3>Bug Types</h3>
                <ul>
{bug_types_list}
                </ul>
            </div>

            <div class="severity-info">
                <h3>Severity</h3>
                <p>{severity_desc}</p>
                <ul>
{severity_counts_list}
                </ul>
            </div>

            <div class="status-legend">
                <h3>Bug Status</h3>
                <ul>
{bug_status_list}
                </ul>
            </div>
        </div>
"""

    # Extract bug type names from overall_info (format: "Type name - Description")
    bug_type_names = {}
    for bt in overall_info['bug_types']:
        if ' - ' in bt:
            type_name = bt.split(' - ')[0].strip()
            bug_type_names[type_name] = bt

    # Generate bug types list with counts at the start
    bug_types_list = []
    for bt in overall_info['bug_types']:
        if ' - ' in bt:
            type_name = bt.split(' - ')[0].strip()
            count = type_counts.get(type_name, 0)
            bug_types_list.append(f'                    <li><strong>({count})</strong> {bt}</li>\n')
        else:
            bug_types_list.append(f'                    <li>{bt}</li>\n')

    # Generate severity counts list (as a list, not nested)
    severity_counts_list = []
    for severity in sorted(severity_counts.keys()):
        count = severity_counts[severity]
        severity_counts_list.append(f'                    <li><strong>{severity}:</strong> {count}</li>\n')

    # Generate bug status list with counts (show all statuses, even with 0 count)
    status_display_info = []
    for status_line in overall_info['bug_status_info']:
        if ' - ' in status_line:
            status_name = status_line.split(' - ')[0].strip()
            description = status_line.split(' - ')[1].strip()
            # Map status names to internal keys
            status_key_map = {
                'fixed': 'fixed',
                'unfixed': 'unfixed',
                'notabug': 'notabug'
            }
            status_key = status_key_map.get(status_name.lower(), status_name.lower())
            count = status_counts.get(status_key, 0)
            status_display_info.append(f'                    <li><strong>{status_name.capitalize()}:</strong> {count} - {description}</li>\n')

    html = html.format(
        total_bugs=total_bugs,
        bug_types_list=''.join(bug_types_list),
        severity_desc=overall_info['severity_desc'],
        severity_counts_list=''.join(severity_counts_list),
        bug_status_list=''.join(status_display_info)
    )

    # Sort maps by map number
    sorted_maps = sorted(bugs_by_map.items(), key=lambda x: x[1]['map_number'])

    # Generate map quick links section
    html += """
            <div class="map-quick-links">
                <h3>Jump to Bug Lists</h3>
                <ul>
"""
    for map_name, map_info in sorted_maps:
        map_number = map_info['map_number']
        html += f'                    <li><a href="#map-{map_number}">Map {map_number}: {map_name}</a></li>\n'

    html += """                </ul>
            </div>

            <div class="filter-section">
                <h3>Filter Bugs</h3>

                <div class="filter-group">
                    <h4>Bug Type:</h4>
                    <div class="filter-buttons" id="filter-type">
"""

    # Add bug type filter buttons
    for bt in overall_info['bug_types']:
        if ' - ' in bt:
            type_name = bt.split(' - ')[0].strip()
            html += f'                        <button class="filter-btn" data-filter-type="type" data-value="{type_name}">{type_name}</button>\n'

    html += """                    </div>
                </div>

                <div class="filter-group">
                    <h4>Severity:</h4>
                    <div class="filter-buttons" id="filter-severity">
"""

    # Add severity filter buttons
    for severity in sorted(severity_counts.keys()):
        html += f'                        <button class="filter-btn" data-filter-type="severity" data-value="{severity}">{severity}</button>\n'

    html += """                    </div>
                </div>

                <div class="filter-group">
                    <h4>Status:</h4>
                    <div class="filter-buttons" id="filter-status">
"""

    # Add status filter buttons
    status_options = [
        ('unfixed', 'Unfixed'),
        ('fixed', 'Fixed'),
        ('notabug', 'Not a Bug')
    ]
    for status_key, status_label in status_options:
        html += f'                        <button class="filter-btn" data-filter-type="status" data-value="{status_key}">{status_label}</button>\n'

    html += """                    </div>
                </div>

                <div class="filter-mode-container">
                    <span class="filter-mode-label">Filter Logic:</span>
                    <div class="switch-container">
                        <span class="mode-text or-mode" id="mode-text">OR</span>
                        <label class="switch">
                            <input type="checkbox" id="filter-mode-toggle" checked>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="filter-mode-description" id="mode-description">
                        OR mode: Bugs match if they satisfy ANY selected filter
                    </div>
                </div>

                <button class="clear-filters-btn" id="clear-filters">Clear All Filters</button>
            </div>
"""

    for map_name, map_info in sorted_maps:
        bugs = map_info['bugs']
        bug_count = len(bugs)
        map_number = map_info['map_number']

        html += f"""
        <div class="map-section" id="map-{map_number}">
            <h2>Map {map_number}: {map_name}<span class="bug-count" data-map-id="map-{map_number}" data-total-count="{bug_count}"><span class="visible-count">{bug_count}</span> / {bug_count} bugs</span></h2>

            <ul class="bug-list" data-map-id="map-{map_number}">
"""

        for bug_id, bug_data in sorted(bugs.items(), key=lambda x: int(x[0])):
            severity_class = get_severity_color(bug_data['severity'])
            status_text, status_class = get_status_info(bug_data['status'])

            # Get list item background class based on status
            list_bg_class = f"bug-{bug_data['status']}"

            # Format bug type with special styling for 'Game breaking'
            bug_type_html = bug_data['type']
            if 'Game breaking' in bug_data['type']:
                # Split by comma and process each part, filtering out empty strings
                parts = [part.strip() for part in bug_data['type'].split(',') if part.strip()]
                formatted_parts = []
                for part in parts:
                    if part == 'Game breaking':
                        formatted_parts.append(f'<span class="bug-type-gamebreaking">{part}</span>')
                    else:
                        formatted_parts.append(f'<span class="bug-type">{part}</span>')
                bug_type_html = ', '.join(formatted_parts)
            else:
                bug_type_html = f'<span class="bug-type">{bug_data["type"]}</span>'

            # Create data attributes for filtering (handle comma-separated types)
            bug_types_for_filter = ','.join([t.strip() for t in bug_data['type'].split(',') if t.strip()])

            html += f"""                <li class="{list_bg_class}" id="list-{map_name}-{bug_id}" data-bug-types="{bug_types_for_filter}" data-severity="{bug_data['severity']}" data-status="{bug_data['status']}">
                    <a href="#bug-{map_name}-{bug_id}">
                        <span class="severity-badge {severity_class}">{bug_data['severity']}</span>
                        <span>Map {map_number} Bug #{bug_id} - {bug_type_html} - <strong>{status_text}</strong> - v{bug_data['version']}</span>
                    </a>
                </li>
"""

        html += """            </ul>
        </div>
"""

    html += """
        <h2>Bug Details</h2>
"""

    # Sort maps by map number for bug details section
    for map_name, map_info in sorted_maps:
        bugs = map_info['bugs']
        map_number = map_info['map_number']

        for bug_id, bug_data in sorted(bugs.items(), key=lambda x: int(x[0])):
            status_text, status_class = get_status_info(bug_data['status'])
            severity_class = get_severity_color(bug_data['severity'])

            html += f"""
        <div class="bug-detail" id="bug-{map_name}-{bug_id}">
            <h3>Map {map_number} Bug #{bug_id} <span class="status-badge {status_class}">{status_text}</span></h3>

            <div class="bug-info">
                <p><strong>Map:</strong> {map_number} - {map_name}</p>
                <p><strong>Description:</strong> {bug_data['description']}</p>
                <p><strong>Type:</strong> {bug_data['type']}</p>
                <p><strong>Severity:</strong> <span class="severity-badge {severity_class}">{bug_data['severity']}</span></p>
                <p><strong>Reproducibility:</strong> {bug_data['reproducibility']}</p>
                <p><strong>Version:</strong> {bug_data['version']}</p>"""

            if bug_data['campfire']:
                html += f"""
                <p><strong>Campfire:</strong> {bug_data['campfire']}</p>"""

            html += """
            </div>
"""

            if bug_data['images']:
                html += """
            <div class="bug-images">
                <h4>Screenshots</h4>
"""
                for img in bug_data['images']:
                    img_path = f"{bug_data['path']}/{img}"
                    thumb = optimize_img(Path(img_path))
                    html += f'                <a href="{img_path}" target="_blank"><img src="{thumb}" alt="Bug #{bug_id} screenshot"></a>\n'

                html += """            </div>
"""

            html += f"""            <a href="#list-{map_name}-{bug_id}" class="back-to-top">↑ Back to list</a>
        </div>
"""

    html += """
    </div>

    <script>
        // Filter functionality
        const filterState = {
            type: new Set(),
            severity: new Set(),
            status: new Set()
        };

        let filterMode = 'OR'; // 'AND' or 'OR'

        // Get all filter buttons
        const filterButtons = document.querySelectorAll('.filter-btn');
        const bugListItems = document.querySelectorAll('.bug-list li');
        const clearFiltersBtn = document.getElementById('clear-filters');
        const filterModeToggle = document.getElementById('filter-mode-toggle');
        const modeText = document.getElementById('mode-text');
        const modeDescription = document.getElementById('mode-description');

        // Add click event listeners to all filter buttons
        filterButtons.forEach(button => {
            button.addEventListener('click', () => {
                const filterType = button.getAttribute('data-filter-type');
                const value = button.getAttribute('data-value');

                // Toggle button active state
                button.classList.toggle('active');

                // Update filter state
                if (button.classList.contains('active')) {
                    filterState[filterType].add(value);
                } else {
                    filterState[filterType].delete(value);
                }

                // Apply filters
                applyFilters();
            });
        });

        // Clear all filters button
        clearFiltersBtn.addEventListener('click', () => {
            // Clear all filter states
            filterState.type.clear();
            filterState.severity.clear();
            filterState.status.clear();

            // Remove active class from all filter buttons
            filterButtons.forEach(button => {
                button.classList.remove('active');
            });

            // Apply filters (will show all bugs since no filters are active)
            applyFilters();
        });

        // Filter mode toggle (AND/OR)
        filterModeToggle.addEventListener('change', () => {
            if (filterModeToggle.checked) {
                filterMode = 'OR';
                modeText.textContent = 'OR';
                modeText.classList.remove('and-mode');
                modeText.classList.add('or-mode');
                modeDescription.textContent = 'OR mode: Bugs match if they satisfy ANY selected filter';
            } else {
                filterMode = 'AND';
                modeText.textContent = 'AND';
                modeText.classList.remove('or-mode');
                modeText.classList.add('and-mode');
                modeDescription.textContent = 'AND mode: Bugs must match ALL selected filters in each category';
            }

            // Re-apply filters with new mode
            applyFilters();
        });

        function applyFilters() {
            console.log('applyFilters called, mode:', filterMode, 'filters:', filterState);

            // If no filters are active, show all bugs
            const hasActiveFilters = filterState.type.size > 0 ||
                                    filterState.severity.size > 0 ||
                                    filterState.status.size > 0;

            bugListItems.forEach(item => {
                if (!hasActiveFilters) {
                    // Show all bugs if no filters are active
                    item.classList.remove('filtered-hidden');
                    return;
                }

                // Get bug attributes
                const bugTypes = item.getAttribute('data-bug-types').split(',').map(t => t.trim());
                const bugSeverity = item.getAttribute('data-severity');
                const bugStatus = item.getAttribute('data-status');

                let shouldShow = false;

                if (filterMode === 'AND') {
                    // AND mode: Bug must match ALL selected filters
                    // Collect all selected filters into one array
                    const allSelectedFilters = [
                        ...Array.from(filterState.type),
                        ...Array.from(filterState.severity),
                        ...Array.from(filterState.status)
                    ];

                    // Collect all bug attributes into one array
                    const allBugAttributes = [
                        ...bugTypes,
                        bugSeverity,
                        bugStatus
                    ];

                    // Check if bug has ALL selected filters
                    shouldShow = allSelectedFilters.every(filter =>
                        allBugAttributes.includes(filter)
                    );

                } else {
                    // OR mode: Bug matches if it satisfies ANY selected filter
                    let matches = false;

                    // Check type filter (bug can have multiple types)
                    for (let bugType of bugTypes) {
                        if (filterState.type.has(bugType)) {
                            matches = true;
                            break;
                        }
                    }

                    // Check severity filter
                    if (filterState.severity.has(bugSeverity)) {
                        matches = true;
                    }

                    // Check status filter
                    if (filterState.status.has(bugStatus)) {
                        matches = true;
                    }

                    shouldShow = matches;
                }

                if (shouldShow) {
                    item.classList.remove('filtered-hidden');
                } else {
                    item.classList.add('filtered-hidden');
                }
            });

            // Update bug counts for each map
            updateBugCounts();
        }

        function updateBugCounts() {
            // Get all bug lists
            const bugLists = document.querySelectorAll('.bug-list');

            bugLists.forEach(list => {
                const mapId = list.getAttribute('data-map-id');
                const items = list.querySelectorAll('li');

                // Count visible bugs
                let visibleCount = 0;
                items.forEach(item => {
                    if (!item.classList.contains('filtered-hidden')) {
                        visibleCount++;
                    }
                });

                // Update the corresponding bug count badge
                const badge = document.querySelector(`.bug-count[data-map-id="${mapId}"]`);
                if (badge) {
                    const totalCount = badge.getAttribute('data-total-count');
                    const visibleSpan = badge.querySelector('.visible-count');
                    if (visibleSpan) {
                        visibleSpan.textContent = visibleCount;
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

    return html

# todo here
def optimize_img(path: Path) -> Path:
    """
    Generate thumbnail and optimize it.
    :param path: Path to the original image.
    :return: Path to the thumbnail.
    """
    global t_id
    if not Path(Path.cwd() / "thumbnails").exists():
        Path.mkdir(Path.cwd() / "thumbnails")

    full_img_path = Path.cwd() / path
    thumb_dir_path = (Path.cwd() / "thumbnails" / path.parent / f"thumb_{full_img_path.name}").parent
    thumb_img_path = (Path.cwd() / "thumbnails" / path.parent / f"thumb_{full_img_path.name}")
    thumb_html_path = Path("thumbnails" / path.parent / f"thumb_{full_img_path.name}")

    if not thumb_dir_path.exists():
        Path.mkdir(thumb_dir_path, parents=True)

    if not thumb_img_path.exists():
        optimize_image(full_img_path, thumb_img_path)

    return thumb_html_path


def optimize_image(src_img_path: Path, dst_img_path: Path) -> None:
    """
    Optimize and overwrite jpg and png images.
    :param img_path: Full path to the image on disk.
    :return: None
    """
    img = Image.open(src_img_path)

    resized = img.resize((1999, 837))
    resized.save(dst_img_path)

    img = Image.open(dst_img_path)
    img.save(dst_img_path, optimize=True, quality=60)
    print(f"✓ Optimized image: {dst_img_path}")


def main():
    """Main function to generate the bug report."""
    script_dir = Path(__file__).parent
    bugs_by_map = {}

    # Read overall info from root directory
    overall_info_path = script_dir / 'overall_info.txt'
    if not overall_info_path.exists():
        print("Error: overall_info.txt not found in root directory!")
        return

    overall_info = parse_overall_info(overall_info_path)

    for item in sorted(script_dir.iterdir()):
        if item.is_dir() and item.name.startswith('Bugs_Map_'):
            match = re.match(r'Bugs_Map_(\d+)_(.+)', item.name)
            if match:
                map_number = match.group(1)
                map_name_raw = match.group(2)
                map_name = map_name_raw.replace('_', ' ')

                bugs = {}

                for bug_dir in sorted(item.iterdir()):
                    if bug_dir.is_dir() and bug_dir.name.startswith('Bug_'):
                        bug_info_path = bug_dir / 'bug_info.txt'
                        if bug_info_path.exists():
                            bug_data = parse_bug_info(bug_info_path)
                            bug_data['images'] = find_images(bug_dir)
                            bug_data['path'] = str(bug_dir.relative_to(script_dir))

                            bug_id = bug_data['number']
                            bugs[bug_id] = bug_data

                bugs_by_map[map_name] = {
                    'bugs': bugs,
                    'version': overall_info['version'],
                    'map_number': int(map_number)
                }

    if not bugs_by_map:
        print("Error: No Bugs_Map_* folders found!")
        return

    # Validate bug values against overall_info.txt
    validation_errors = validate_bug_values(bugs_by_map, overall_info)
    if validation_errors:
        print("ERROR: Found invalid values in bug_info.txt files:")
        print()
        for error in validation_errors:
            print(error)
            print()
        sys.exit(1)

    # Calculate statistics
    total_bugs = sum(len(map_info['bugs']) for map_info in bugs_by_map.values())
    type_counts, status_counts, severity_counts = calculate_bug_statistics(bugs_by_map)

    # Update overall_info.txt with new bug count
    overall_info_path = script_dir / 'overall_info.txt'
    if overall_info_path.exists():
        with open(overall_info_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update the Count: line
        updated_content = re.sub(r'Count:\s*\d+', f'Count: {total_bugs}', content)

        with open(overall_info_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    # Generate HTML
    try:
        html_content = generate_html(bugs_by_map, overall_info, total_bugs, type_counts, status_counts, severity_counts)
    except ValueError as e:
        print(f"Format error: {e}")
        return

    output_path = script_dir / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Bug report generated successfully: {output_path}")
    print(f"  Total maps: {len(bugs_by_map)}")
    print(f"  Total bugs: {total_bugs}")
    print(f"✓ Updated overall_info.txt with bug count: {total_bugs}")


if __name__ == '__main__':
    main()
