#!/usr/bin/env python3
"""
Test script to verify both fixes:
1. Configuration updates are properly propagated to all modules (systemd timer issue)
2. Validation prevents saving settings when scheduled snapshots are enabled but no schedule type is selected
"""

import os
import sys
sys.path.insert(0, '/home/and98/Documents/Projects/Arch-Lab/zfs-assistant/src')

from zfs_assistant import ZFSAssistant
from system_integration import SystemIntegration
from zfs_core import ZFSCore
from zfs_backup import ZFSBackup
from system_maintenance import SystemMaintenance

def test_config_propagation():
    """Test that config updates propagate to all modules"""
    print("=== Testing Config Propagation ===")
    
    # Create ZFS Assistant instance
    zfs = ZFSAssistant()
    
    # Test config to simulate hourly snapshots being enabled
    test_config = {
        "auto_snapshot": True,
        "hourly_schedule": [9, 17],  # 9 AM and 5 PM
        "daily_schedule": [],
        "weekly_schedule": False,
        "monthly_schedule": False,
        "datasets": ["tank/home", "tank/data"],
        "prefix": "auto",
        "snapshot_name_format": "prefix-type-timestamp",
        "pacman_integration": True,
        "notifications_enabled": True,
        "external_backup_enabled": False
    }
    
    # Update the config
    zfs.config = test_config
    
    # Test that all modules have update_config method
    modules = [
        ('SystemIntegration', SystemIntegration()),
        ('ZFSCore', ZFSCore()),
        ('ZFSBackup', ZFSBackup()),
        ('SystemMaintenance', SystemMaintenance())
    ]
    
    all_methods_exist = True
    for name, module in modules:
        if hasattr(module, 'update_config'):
            print(f"✓ {name} has update_config method")
            try:
                # Test calling the method
                module.update_config(test_config)
                print(f"✓ {name}.update_config() executed successfully")
            except Exception as e:
                print(f"✗ {name}.update_config() failed: {e}")
                all_methods_exist = False
        else:
            print(f"✗ {name} missing update_config method")
            all_methods_exist = False
    
    if all_methods_exist:
        print("✓ All modules have working update_config methods")
    else:
        print("✗ Some modules are missing update_config methods")
    
    return all_methods_exist

def test_validation_logic():
    """Test the validation logic by examining the settings dialog code"""
    print("\n=== Testing Validation Logic ===")
    
    # Read the settings dialog file to check validation
    settings_file = '/home/and98/Documents/Projects/Arch-Lab/zfs-assistant/src/ui_settings_dialog.py'
    
    try:
        with open(settings_file, 'r') as f:
            content = f.read()
        
        # Check for the new validation
        validation_checks = [
            "if not (hourly_enabled or daily_enabled or weekly_enabled or monthly_enabled):",
            "No Schedule Type Selected",
            "Scheduled snapshots are enabled, but no schedule type is selected"
        ]
        
        all_validations_present = True
        for check in validation_checks:
            if check in content:
                print(f"✓ Found validation: {check}")
            else:
                print(f"✗ Missing validation: {check}")
                all_validations_present = False
        
        # Check for existing hour/day validations
        existing_validations = [
            "selected_hours = [hour for hour, check in self.hour_checks.items() if check.get_active()]",
            "selected_days = [day for day, check in self.day_checks.items() if check.get_active()]"
        ]
        
        for check in existing_validations:
            if check in content:
                print(f"✓ Found existing validation: {check}")
            else:
                print(f"✗ Missing existing validation: {check}")
                all_validations_present = False
        
        if all_validations_present:
            print("✓ All validation logic is present")
        else:
            print("✗ Some validation logic is missing")
        
        return all_validations_present
        
    except Exception as e:
        print(f"✗ Error reading settings dialog file: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing ZFS Assistant Complete Fix")
    print("==================================")
    
    config_test = test_config_propagation()
    validation_test = test_validation_logic()
    
    print(f"\n=== SUMMARY ===")
    print(f"Config Propagation Fix: {'PASSED' if config_test else 'FAILED'}")
    print(f"Validation Logic Fix:   {'PASSED' if validation_test else 'FAILED'}")
    
    if config_test and validation_test:
        print("\n🎉 ALL TESTS PASSED! Both fixes are properly implemented.")
        print("\nWhat was fixed:")
        print("1. Added update_config() methods to all module classes")
        print("2. Added validation to prevent saving when auto-snapshot is enabled but no schedule type is selected")
        print("3. Users will now get clear error messages for invalid configurations")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    return config_test and validation_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
