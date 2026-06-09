#!/usr/bin/env python3
"""
Bug Report HTML Generator. Coded with Claude.
Scans Bugs_Map_* folders and generates a comprehensive HTML report.
"""

import os
import re
from pathlib import Path
from collections import defaultdict


def parse_overall_info(filepath):
    """Parse OVERALL_INFO.txt to extract version and common information."""
    info = {
        'version': '',
        'count': '',
        'bug_types': [],
        'severity_desc': '',
        'extra_info': []
    }

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')

    in_bug_types = False
    bug_type_section = []

    for line in lines:
        line = line.strip()

        if line.startswith('Version:'):
            info['version'] = line.split(':', 1)[1].strip()
        elif line.startswith('Count:'):
            info['count'] = line.split(':', 1)[1].strip()
        elif line.startswith('Bug types:'):
            in_bug_types = True
        elif line.startswith('Severity:'):
            info['severity_desc'] = line.split(':', 1)[1].strip()
            in_bug_types = False
        elif in_bug_types and ' - ' in line:
            info['bug_types'].append(line)
        elif line and not in_bug_types:
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
        'fixed': 'Unfixed'
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
        elif 'fixed' in line_stripped.lower():
            if 'unfixed' not in line_stripped.lower():
                bug['fixed'] = 'Fixed'

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


def find_images(bug_dir):
    """Find all image files in a bug directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    images = []

    for file in sorted(os.listdir(bug_dir)):
        if Path(file).suffix.lower() in image_extensions:
            images.append(file)

    return images


def generate_html(bugs_by_map, overall_info, total_bugs):
    """Generate the complete HTML document."""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bug Report</title>
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

        .bug-types ul, .severity-info p {{
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

        .bug-list li:hover {{
            background: #e9ecef;
            transform: translateX(5px);
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Bug Report</h1>

        <div class="info-section">
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
            </div>
        </div>
""".format(
        total_bugs=total_bugs,
        bug_types_list=''.join([f'                    <li>{bt}</li>\n' for bt in overall_info['bug_types']]),
        severity_desc=overall_info['severity_desc']
    )

    # Sort maps by map number
    sorted_maps = sorted(bugs_by_map.items(), key=lambda x: x[1]['map_number'])

    for map_name, map_info in sorted_maps:
        bugs = map_info['bugs']
        version = map_info['version']
        bug_count = len(bugs)
        map_number = map_info['map_number']

        html += f"""
        <div class="map-section">
            <h2>Map {map_number}: {map_name}<span class="version-tag">Version: {version}</span><span class="bug-count">{bug_count} bugs</span></h2>

            <ul class="bug-list">
"""

        for bug_id, bug_data in sorted(bugs.items(), key=lambda x: int(x[0])):
            severity_class = get_severity_color(bug_data['severity'])
            html += f"""                <li>
                    <a href="#bug-{map_name}-{bug_id}">
                        <span class="severity-badge {severity_class}">{bug_data['severity']}</span>
                        <span>Map {map_number} Bug #{bug_id} - <span class="bug-type">{bug_data['type']}</span></span>
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
            status_class = 'status-fixed' if bug_data['fixed'] == 'Fixed' else 'status-unfixed'
            severity_class = get_severity_color(bug_data['severity'])

            html += f"""
        <div class="bug-detail" id="bug-{map_name}-{bug_id}">
            <h3>Map {map_number} Bug #{bug_id} <span class="status-badge {status_class}">{bug_data['fixed']}</span></h3>

            <div class="bug-info">
                <p><strong>Map:</strong> {map_number} - {map_name}</p>
                <p><strong>Description:</strong> {bug_data['description']}</p>
                <p><strong>Type:</strong> {bug_data['type']}</p>
                <p><strong>Severity:</strong> <span class="severity-badge {severity_class}">{bug_data['severity']}</span></p>
                <p><strong>Reproducibility:</strong> {bug_data['reproducibility']}</p>"""

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
                    html += f'                <a href="{img_path}" target="_blank"><img src="{img_path}" alt="Bug #{bug_id} screenshot"></a>\n'

                html += """            </div>
"""

            html += """            <a href="#" class="back-to-top">↑ Back to Top</a>
        </div>
"""

    html += """
    </div>
</body>
</html>
"""

    return html


def main():
    """Main function to generate the bug report."""
    script_dir = Path(__file__).parent
    bugs_by_map = {}
    overall_info = None

    for item in sorted(script_dir.iterdir()):
        if item.is_dir() and item.name.startswith('Bugs_Map_'):
            match = re.match(r'Bugs_Map_(\d+)_(.+)', item.name)
            if match:
                map_number = match.group(1)
                map_name_raw = match.group(2)
                map_name = map_name_raw.replace('_', ' ')

                overall_info_path = item / 'OVERALL_INFO.txt'
                if overall_info_path.exists():
                    map_overall_info = parse_overall_info(overall_info_path)
                    if overall_info is None:
                        overall_info = map_overall_info
                else:
                    print(f"Warning: OVERALL_INFO.txt not found in {item.name}")
                    continue

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
                    'version': map_overall_info['version'],
                    'map_number': int(map_number)
                }

    if not bugs_by_map:
        print("Error: No Bugs_Map_* folders found!")
        return

    if overall_info is None:
        print("Error: No OVERALL_INFO.txt found!")
        return

    total_bugs = sum(len(map_info['bugs']) for map_info in bugs_by_map.values())
    html_content = generate_html(bugs_by_map, overall_info, total_bugs)

    output_path = script_dir / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Bug report generated successfully: {output_path}")
    print(f"  Total maps: {len(bugs_by_map)}")
    print(f"  Total bugs: {total_bugs}")


if __name__ == '__main__':
    main()
