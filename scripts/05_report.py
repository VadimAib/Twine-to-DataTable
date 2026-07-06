#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_report.py
Generate report (statistics, variables, diff)
"""

import sys
import os
import json
from collections import defaultdict
from logger import log_info, log_success, log_error, log_warning

def generate_report(input_file, report_file, variables_file, metadata_file=None):
    """Generate report"""
    
    log_info(f"Reading: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    
    # Load metadata
    metadata = {}
    start_node = 'Start'  # default fallback
    if metadata_file and os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            start_node = metadata.get('start_node', 'Start')
        except (json.JSONDecodeError, IOError):
            log_warning("Failed to load metadata, using default start_node='Start'")
    
    report = []
    report.append("=" * 60)
    report.append("TWINE → DATATABLE PARSER REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Project info from metadata
    if metadata:
        report.append("PROJECT INFO:")
        report.append(f"  Title: {metadata.get('title', 'Unknown')}")
        if metadata.get('ifid'):
            report.append(f"  IFID: {metadata.get('ifid')}")
        report.append(f"  Format: {metadata.get('format', 'Unknown')} {metadata.get('format_version', '')}")
        report.append(f"  Start node: {start_node}")
        report.append("")
    
    # 1. Statistics
    total_nodes = len(nodes)
    total_choices = sum(len(n.get('Choices', [])) for n in nodes)
    total_actions = sum(len(n.get('Actions', [])) for n in nodes)
    total_segments = sum(len(n.get('TextSegments', [])) for n in nodes)
    
    report.append("STATISTICS:")
    report.append(f"  Nodes: {total_nodes}")
    report.append(f"  Choices: {total_choices}")
    report.append(f"  Actions: {total_actions}")
    report.append(f"  Text segments: {total_segments}")
    report.append("")
    
    # 2. Variables
    variables = defaultdict(lambda: {"type": None, "initial_value": None, "usages": 0})
    
    for node in nodes:
        node_id = node.get('RowName') or node.get('NodeID', '')
        
        for action in node.get('Actions', []):
            var_name = action.get('VariableName', '')
            value = action.get('Value', '')
            operation = action.get('Operation', '')
            
            if value.lower() in ['true', 'false']:
                var_type = 'Boolean'
            elif '.' in value:
                try:
                    float(value)
                    var_type = 'Float'
                except:
                    var_type = 'String'
            else:
                try:
                    int(value)
                    var_type = 'Integer'
                except:
                    var_type = 'String'
            
            if var_name:
                variables[var_name]['type'] = var_type
                variables[var_name]['usages'] += 1
                
                # FIX: использовать start_node из metadata вместо хардкода "Start"
                if node_id == start_node and operation.startswith('SET'):
                    variables[var_name]['initial_value'] = value
    
    report.append("VARIABLES:")
    for var_name, var_data in sorted(variables.items()):
        initial = var_data['initial_value'] if var_data['initial_value'] is not None else 'N/A'
        report.append(f"  ${var_name}: {var_data['type']} = {initial} (usages: {var_data['usages']})")
    report.append("")
    
    # 3. Save variables for diff
    with open(variables_file, 'w', encoding='utf-8') as f:
        json.dump(dict(variables), f, ensure_ascii=False, indent=2)
    
    report.append("=" * 60)
    report.append("End of report")
    report.append("=" * 60)
    
    report_text = '\n'.join(report)
    
    print(report_text)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    log_success(f"Report saved: {report_file}")
    log_info(f"Variables saved: {variables_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        log_error("Usage: python 05_report.py <input_json> <report_file> <variables_file> [metadata_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    report_file = sys.argv[2]
    variables_file = sys.argv[3]
    metadata_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    if not os.path.exists(input_file):
        log_error(f"File not found: {input_file}")
        sys.exit(1)
    
    generate_report(input_file, report_file, variables_file, metadata_file)