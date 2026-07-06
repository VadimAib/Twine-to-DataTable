#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logger.py
Colored logging with file output and timestamps
"""

import sys
import os
import re
from datetime import datetime

# ANSI color codes
COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'WHITE': '\033[97m',
    'BOLD': '\033[1m',
}

# Regex для удаления ANSI escape-последовательностей
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text):
    """Remove ANSI escape sequences from text"""
    return ANSI_ESCAPE.sub('', text)

# Global log file handle
_log_file = None
_log_enabled = True
_console_enabled = True

def init_logger(log_file=None, console=True):
    """Initialize logger"""
    global _log_file, _log_enabled, _console_enabled
    
    _console_enabled = console
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        _log_file = open(log_file, 'a', encoding='utf-8')
        _log_enabled = True
    else:
        _log_enabled = False

def close_logger():
    """Close log file"""
    global _log_file
    if _log_file:
        _log_file.close()
        _log_file = None

def _format_message(level, message, color=None):
    """Format message with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if color and _console_enabled:
        console_msg = f"{color}[{timestamp}] {level}: {message}{COLORS['RESET']}"
    else:
        console_msg = f"[{timestamp}] {level}: {message}"
    
    # Plain text for file (no ANSI codes)
    file_msg = f"[{timestamp}] {level}: {message}"
    
    return console_msg, file_msg

def log_info(message):
    """Info message (blue)"""
    console_msg, file_msg = _format_message('INFO', message, COLORS['BLUE'])
    if _console_enabled:
        print(console_msg)
    if _log_enabled and _log_file:
        _log_file.write(strip_ansi(file_msg) + '\n')
        _log_file.flush()

def log_success(message):
    """Success message (green)"""
    console_msg, file_msg = _format_message('OK', message, COLORS['GREEN'])
    if _console_enabled:
        print(console_msg)
    if _log_enabled and _log_file:
        _log_file.write(strip_ansi(file_msg) + '\n')
        _log_file.flush()

def log_warning(message):
    """Warning message (yellow)"""
    console_msg, file_msg = _format_message('WARN', message, COLORS['YELLOW'])
    if _console_enabled:
        print(console_msg)
    if _log_enabled and _log_file:
        _log_file.write(strip_ansi(file_msg) + '\n')
        _log_file.flush()

def log_error(message):
    """Error message (red)"""
    console_msg, file_msg = _format_message('ERROR', message, COLORS['RED'])
    if _console_enabled:
        print(console_msg, file=sys.stderr)
    if _log_enabled and _log_file:
        _log_file.write(strip_ansi(file_msg) + '\n')
        _log_file.flush()

def log_stage(stage_num, total_stages, message):
    """Stage header (bold cyan)"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    stage_text = f"[Stage {stage_num}/{total_stages}]"
    
    console_msg = f"{COLORS['BOLD']}{COLORS['CYAN']}[{timestamp}] {stage_text} {message}{COLORS['RESET']}"
    file_msg = f"[{timestamp}] {stage_text} {message}"
    
    if _console_enabled:
        print(f"\n{console_msg}")
    if _log_enabled and _log_file:
        _log_file.write(strip_ansi(file_msg) + '\n')
        _log_file.flush()

def log_separator():
    """Print separator line"""
    if _console_enabled:
        print(f"{COLORS['CYAN']}{'=' * 60}{COLORS['RESET']}")
    if _log_enabled and _log_file:
        _log_file.write('=' * 60 + '\n')
        _log_file.flush()

def log_pipeline_start(input_file):
    """Log pipeline start"""
    log_separator()
    log_info("Twine → DataTable Conversion Pipeline")
    log_separator()
    log_info(f"Input file: {input_file}")
    log_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_separator()

def log_pipeline_end(output_file, report_file):
    """Log pipeline end"""
    log_separator()
    log_success("Pipeline completed successfully!")
    log_info(f"Output: {output_file}")
    log_info(f"Report: {report_file}")
    log_info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_separator()