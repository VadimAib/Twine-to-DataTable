#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_parse_twee.py
Parse Twee → intermediate JSON + metadata
"""

import sys
import os
import re
import json
from logger import log_info, log_success, log_error, log_warning

def extract_metadata(content, metadata_file):
    """Extract StoryTitle and StoryData from Twee content"""
    metadata = {}
    
    # StoryTitle — простая однострочная структура
    title_match = re.search(r':: StoryTitle[^\n]*\n([^\n]+)', content)
    if title_match:
        metadata['title'] = title_match.group(1).strip()
        log_info(f"Title: {metadata['title']}")
    else:
        log_warning("StoryTitle not found")
    
    # StoryData
    data_match = re.search(r':: StoryData[^\n]*\n(\{.*?\})\s*(?=\n::|\Z)', content, re.DOTALL)
    if data_match:
        try:
            data = json.loads(data_match.group(1))
            metadata['ifid'] = data.get('ifid', '')
            metadata['format'] = data.get('format', '')
            metadata['format_version'] = data.get('format-version', '')
            metadata['start_node'] = data.get('start', 'Start')
            log_info(f"Format: {metadata.get('format')} {metadata.get('format_version')}")
            log_info(f"Start node: {metadata.get('start_node')}")
        except json.JSONDecodeError as e:
            log_warning(f"Failed to parse StoryData: {e}")
            metadata['start_node'] = 'Start'
    else:
        log_warning("StoryData not found, using defaults")
        metadata['start_node'] = 'Start'
    
    # Save metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    log_success(f"Metadata saved: {metadata_file}")

def parse_twee(input_file, output_file, metadata_file):
    """Parse .twee file into data structure"""
    
    log_info(f"Parsing: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata first
    extract_metadata(content, metadata_file)
    
    # FIX: Add \n at start to ensure first passage is split correctly
    content = '\n' + content
    
    # Parse nodes
    passages = re.split(r'\n::\s+', content)
    
    nodes = []
    skipped = 0
    metadata_skipped = 0
    
    for passage in passages:
        if not passage.strip():
            continue
        
        match = re.match(r'^([^\{]+?)(?:\s+(\{.*?\}))?\s*\n(.*)', passage, re.DOTALL)
        if not match:
            skipped += 1
            continue
        
        title = match.group(1).strip()
        body = match.group(3).strip()
        
        # Skip metadata passages
        if title in ['StoryTitle', 'StoryData']:
            metadata_skipped += 1
            continue
        
        node = parse_passage_body(title, body)
        nodes.append(node)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    
    log_success(f"Parsed {len(nodes)} nodes ({skipped} skipped, {metadata_skipped} metadata)")
    log_info(f"Output: {output_file}")

def parse_passage_body(node_id, body):
    """Parse passage body"""
    
    node = {
        "NodeID": node_id,
        "Text": body,
        "Actions": [],
        "Choices": []
    }
    
    return node

if __name__ == "__main__":
    if len(sys.argv) != 4:
        log_error("Usage: python 02_parse_twee.py <input> <output> <metadata_output>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    metadata_file = sys.argv[3]
    
    if not os.path.exists(input_file):
        log_error(f"File not found: {input_file}")
        sys.exit(1)
    
    parse_twee(input_file, output_file, metadata_file)