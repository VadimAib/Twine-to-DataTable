#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_normalize_encoding.py
Remove BOM and normalize to UTF-8
"""

import sys
import os
from logger import log_info, log_success, log_error, log_warning

def normalize_encoding(input_file, output_file):
    """Read file, remove BOM, save as UTF-8"""
    
    log_info(f"Reading: {input_file}")
    
    with open(input_file, 'rb') as f:
        content = f.read()
    
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
        log_warning("BOM detected and removed")
    
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError as e:
        log_error(f"File is not UTF-8: {e}")
        sys.exit(1)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    log_success(f"Encoding normalized: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        log_error("Usage: python 01_normalize_encoding.py <input> <output>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        log_error(f"File not found: {input_file}")
        sys.exit(1)
    
    normalize_encoding(input_file, output_file)