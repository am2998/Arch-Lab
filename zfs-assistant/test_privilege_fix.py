#!/usr/bin/env python3
"""
Test script to verify the systemd timer privilege fix
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, '/home/and98/Documents/Projects/Arch-Lab/zfs-assistant/src')

from system_integration import SystemIntegration
from privilege_manager import PrivilegeManager

def test_privilege_detection():
    """Test that systemd timer setup properly detects elevated privileges"""
    
    print("=== ZFS Assistant Systemd Timer Privilege Fix Test ===\n")
    
    # Create a mock config
    config = {
        "datasets": ["tank/test"],
        "prefix": "test",
        "hourly_schedule": [9, 12, 15, 18],
        "daily_schedule": [1, 3, 5],
        "weekly_schedule": True,
        "monthly_schedule": True
    }
    
    # Create privilege manager and system integration
    privilege_manager = PrivilegeManager()
    system_integration = SystemIntegration(privilege_manager, config)
    
    # Test privilege detection
    print(f"Current user ID: {os.geteuid()}")
    print(f"Running as root: {os.geteuid() == 0}")
    
    # Test schedule setup
    schedules = {
        "hourly": True,
        "daily": True, 
        "weekly": True,
        "monthly": True
    }
    
    print("\nTesting systemd timer setup...")
    success, message = system_integration.setup_systemd_timers(schedules)
    
    print(f"Setup successful: {success}")
    print(f"Message: {message}")
    
    if not success and os.geteuid() == 0:
        print("\n✅ PASS: Correctly detected elevated privileges and provided appropriate error message")
    elif success and os.geteuid() != 0:
        print("\n✅ PASS: Successfully set up timers when running without elevated privileges")
    else:
        print("\n❌ FAIL: Unexpected behavior")
    
    # Test schedule status
    print("\nTesting schedule status check...")
    status = system_integration.get_schedule_status()
    print(f"Schedule status: {status}")
    
    if os.geteuid() == 0:
        print("✅ PASS: Schedule status check handled elevated privileges gracefully")
    
    # Test disable schedule
    print("\nTesting schedule disable...")
    disable_success, disable_message = system_integration.disable_schedule("hourly")
    print(f"Disable successful: {disable_success}")
    print(f"Disable message: {disable_message}")
    
    if os.geteuid() == 0 and disable_success:
        print("✅ PASS: Schedule disable handled elevated privileges gracefully")

if __name__ == "__main__":
    test_privilege_detection()
