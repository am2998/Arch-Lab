#!/usr/bin/env python3

import subprocess

def test_script_generation():
    # Test script generation with both methods
    script_lines = ["#!/bin/bash", "set -e", "echo 'Hello World'"]
    
    # Method 1 (old, problematic)
    script_content1 = '\n'.join(script_lines)
    
    # Method 2 (fixed)
    script_content2 = '\\n'.join(script_lines)
    
    print("===== Method 1 (old) =====")
    print(repr(script_content1))
    print("\nRunning bash script from Method 1:")
    try:
        result1 = subprocess.run(['bash', '-c', script_content1], 
                              check=True, capture_output=True, text=True)
        print(f"Output: {result1.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    
    print("\n===== Method 2 (fixed) =====")
    print(repr(script_content2))
    print("\nRunning bash script from Method 2:")
    try:
        result2 = subprocess.run(['bash', '-c', script_content2], 
                              check=True, capture_output=True, text=True)
        print(f"Output: {result2.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_script_generation()
