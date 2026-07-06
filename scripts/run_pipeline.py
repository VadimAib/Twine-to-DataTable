#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py
Main pipeline runner with logging
"""

import sys
import os
import re
import hashlib
import subprocess
from logger import (
    init_logger, close_logger, log_info, log_success,
    log_error, log_warning, log_stage, log_pipeline_start,
    log_pipeline_end
)

# Устанавливаем UTF-8 для дочерних процессов
ENV = os.environ.copy()
ENV['PYTHONIOENCODING'] = 'utf-8'


def run_stage(stage_num, total_stages, script, args, description):
    """Run a pipeline stage with output capture"""
    log_stage(stage_num, total_stages, description)

    try:
        result = subprocess.run(
            [sys.executable, script] + args,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            env=ENV
        )

        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    log_info(f"  {line}")

        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Stage {stage_num} failed with exit code {e.returncode}")
        if e.stderr:
            for line in e.stderr.strip().split('\n'):
                if line.strip():
                    log_error(f"  {line}")
        return False


def run_backup(backups_dir, output_json):
    """Run backup script with output capture"""
    result = subprocess.run(
        [sys.executable, 'scripts/00_backup.py', backups_dir, output_json],
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=ENV
    )
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                log_info(f"  {line}")


def generate_output_filename(input_file):
    """Generate output JSON filename from input .twee filename"""
    basename = os.path.splitext(os.path.basename(input_file))[0]
    return f"{basename}.json"


def get_next_run_number(logs_dir):
    """Find the next run number by scanning existing files in logs_dir"""
    if not os.path.exists(logs_dir):
        return 1
    
    max_num = 0
    pattern = re.compile(r'\.(\d+)\.(log|txt|json)$')
    
    for f in os.listdir(logs_dir):
        match = pattern.search(f)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    return max_num + 1


def get_file_hash(filepath):
    """Calculate MD5 hash of file"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def check_for_changes(input_file, hash_file):
    """Check if input file changed since last run"""
    current_hash = get_file_hash(input_file)
    
    if not os.path.exists(hash_file):
        return True, current_hash
    
    with open(hash_file, 'r', encoding='utf-8') as f:
        previous_hash = f.read().strip()
    
    if current_hash == previous_hash:
        return False, current_hash
    else:
        return True, current_hash


def save_hash(hash_file, file_hash):
    """Save file hash for future comparison"""
    with open(hash_file, 'w', encoding='utf-8') as f:
        f.write(file_hash)


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_pipeline.py <input_file> <logs_dir>")
        sys.exit(1)

    input_file = sys.argv[1]
    logs_dir = sys.argv[2]

    # Set up paths
    temp_dir = 'temp'
    backups_dir = 'backups'
    
    hash_file = os.path.join(temp_dir, 'input_hash.txt')

    # Check if input file changed BEFORE anything else
    has_changes, current_hash = check_for_changes(input_file, hash_file)
    
    if not has_changes:
        print(f"\n[INFO] No changes detected in: {input_file}")
        print(f"[INFO] Pipeline skipped. Output is up to date.\n")
        sys.exit(0)

    # Generate run number
    run_num = get_next_run_number(logs_dir)

    # Generate log filename
    log_file = os.path.join(logs_dir, f"pipeline.{run_num}.log")

    # Initialize logger
    init_logger(log_file)

    log_pipeline_start(input_file)

    temp_normalized = os.path.join(temp_dir, 'normalized.twee')
    temp_raw = os.path.join(temp_dir, 'raw_story.json')
    temp_metadata = os.path.join(temp_dir, 'metadata.json')
    
    output_json = generate_output_filename(input_file)
    log_info(f"Output file: {output_json}")
    log_info(f"Run number: {run_num}")
    
    report_file = os.path.join(logs_dir, f'report.{run_num}.txt')
    variables_file = os.path.join(logs_dir, f'variables.{run_num}.json')

    # Stage 1: Backup
    log_stage(1, 6, "Checking for backups...")
    run_backup(backups_dir, output_json)

    # Stage 2: Normalize
    if not run_stage(2, 6, 'scripts/01_normalize_encoding.py',
                     [input_file, temp_normalized], "Normalizing encoding"):
        close_logger()
        sys.exit(1)

    # Stage 3: Parse (with metadata output)
    if not run_stage(3, 6, 'scripts/02_parse_twee.py',
                     [temp_normalized, temp_raw, temp_metadata], "Parsing Twee"):
        close_logger()
        sys.exit(1)

    # Stage 4: Validate (with metadata input)
    if not run_stage(4, 6, 'scripts/03_validate.py',
                     [temp_raw, temp_metadata], "Validating"):
        close_logger()
        sys.exit(1)

    # Stage 5: Transform
    if not run_stage(5, 6, 'scripts/04_transform.py',
                     [temp_raw, output_json], "Transforming"):
        close_logger()
        sys.exit(1)

    # Stage 6: Report (with metadata input)
    if not run_stage(6, 6, 'scripts/05_report.py',
                     [output_json, report_file, variables_file, temp_metadata], "Generating report"):
        close_logger()
        sys.exit(1)

    # Final backup
    log_info("Running final backup check...")
    run_backup(backups_dir, output_json)

    # Save hash for future comparison
    save_hash(hash_file, current_hash)
    log_info(f"Input hash saved: {hash_file}")

    log_pipeline_end(output_json, report_file)
    close_logger()
    
    # Print log file location for the user
    print(f"\nLog saved: {log_file}\n")


if __name__ == "__main__":
    main()