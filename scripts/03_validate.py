#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_validate.py
Validate integrity (links, duplicates, types)
"""

import sys
import os
import json
import re
from logger import log_info, log_success, log_error, log_warning

def load_metadata(metadata_file):
    """Load metadata from file, return dict with defaults"""
    metadata = {
        'title': 'Unknown',
        'start_node': 'Start',
        'format': 'Unknown',
        'ifid': ''
    }
    
    if metadata_file and os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            metadata.update(data)
            log_info(f"Loaded metadata: start_node='{metadata['start_node']}'")
        except (json.JSONDecodeError, IOError) as e:
            log_warning(f"Failed to load metadata: {e}")
    
    return metadata

def validate(input_file, metadata_file=None):
    """Validate intermediate JSON (always strict)"""
    
    log_info(f"Validating: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    
    # Load metadata for start node
    metadata = load_metadata(metadata_file)
    start_node = metadata['start_node']
    
    errors = []
    
    # 1. Check for duplicate NodeIDs
    node_ids = [n['NodeID'] for n in nodes]
    duplicates = [x for x in node_ids if node_ids.count(x) > 1]
    if duplicates:
        errors.append(f"Duplicate NodeIDs: {set(duplicates)}")
    
    # 2. Check for start node (from metadata, not hardcoded)
    if start_node not in node_ids:
        errors.append(f"Missing start node: '{start_node}'")
    else:
        log_info(f"Start node '{start_node}' found")
    
    # 3. Check for nested if (not supported)
    for node in nodes:
        text = node['Text']
        if_blocks = re.findall(r'<<if.*?>>.*?<<endif>>', text, re.DOTALL)
        for block in if_blocks:
            nested = re.findall(r'<<if.*?>>', block)
            if len(nested) > 1:
                errors.append(f"Node {node['NodeID']}: nested <<if>> not supported")
    
    # 4. Check for broken links
    for node in nodes:
        text = node['Text']
        links = re.findall(r'\[\[(.*?)\]\]', text)
        for link in links:
            if '|' in link:
                target = link.split('|')[1]
            elif '->' in link:
                target = link.split('->')[1]
            elif '<-' in link:
                target = link.split('<-')[0]
            else:
                target = link
            
            target = target.strip()
            if target not in node_ids:
                errors.append(f"Node {node['NodeID']}: link to non-existent node '{target}'")
    
    if errors:
        log_error(f"VALIDATION FAILED ({len(errors)} errors):")
        for err in errors[:10]:
            log_error(f"  - {err}")
        if len(errors) > 10:
            log_error(f"  ... and {len(errors) - 10} more")
        log_error("Please fix the errors above and run again.")
        sys.exit(1)
    
    log_success("Validation passed")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log_error("Usage: python 03_validate.py <input> [metadata]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Parse arguments: metadata file is optional
    metadata_file = None
    
    for arg in sys.argv[2:]:
        if not arg.startswith('--'):
            metadata_file = arg
    
    if not os.path.exists(input_file):
        log_error(f"File not found: {input_file}")
        sys.exit(1)
    
    validate(input_file, metadata_file)