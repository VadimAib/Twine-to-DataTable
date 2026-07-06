#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
00_backup.py
Create numbered backups only if files changed
"""

import sys
import os
import shutil
import hashlib
import re

def get_file_hash(filepath):
    """Calculate MD5 hash of file"""
    if not os.path.exists(filepath):
        return None
    
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def get_next_backup_number(filepath, backup_dir):
    """Find next available backup number"""
    filename = os.path.basename(filepath)
    
    if not os.path.exists(backup_dir):
        return 1
    
    # Find all existing backups for this file
    pattern = re.escape(filename) + r'\.(\d+)\.backup'
    max_num = 0
    
    for f in os.listdir(backup_dir):
        match = re.match(pattern, f)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    return max_num + 1

def get_latest_backup(filepath, backup_dir):
    """Get the most recent backup of this file"""
    filename = os.path.basename(filepath)
    
    if not os.path.exists(backup_dir):
        return None
    
    pattern = re.escape(filename) + r'\.(\d+)\.backup'
    latest_num = 0
    latest_path = None
    
    for f in os.listdir(backup_dir):
        match = re.match(pattern, f)
        if match:
            num = int(match.group(1))
            if num > latest_num:
                latest_num = num
                latest_path = os.path.join(backup_dir, f)
    
    return latest_path

def backup_file(filepath, backup_dir):
    """Backup file if it changed"""
    
    if not os.path.exists(filepath):
        print(f"[00] SKIP: {filepath} does not exist")
        return False
    
    # Get current hash
    current_hash = get_file_hash(filepath)
    
    # Check latest backup
    latest_backup = get_latest_backup(filepath, backup_dir)
    
    if latest_backup:
        last_hash = get_file_hash(latest_backup)
        if current_hash == last_hash:
            print(f"[00] SKIP: {filepath} unchanged")
            return False
    
    # Get next backup number
    backup_num = get_next_backup_number(filepath, backup_dir)
    # FIX: Removed :03d formatting, use plain number
    backup_name = f"{os.path.basename(filepath)}.{backup_num}.backup"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Create backup
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(filepath, backup_path)
    
    file_size = os.path.getsize(filepath) / 1024  # KB
    print(f"[00] BACKUP: {filepath} → {backup_name} ({file_size:.1f} KB)")
    
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python 00_backup.py <backup_dir> <file1> [file2] [file3] ...")
        sys.exit(1)
    
    backup_dir = sys.argv[1]
    files = sys.argv[2:]
    
    backed_up = 0
    skipped = 0
    
    print(f"\n[00] Checking {len(files)} files for backup...")
    
    for filepath in files:
        if backup_file(filepath, backup_dir):
            backed_up += 1
        else:
            skipped += 1
    
    print(f"[00] Summary: {backed_up} backed up, {skipped} skipped\n")

if __name__ == "__main__":
    main()