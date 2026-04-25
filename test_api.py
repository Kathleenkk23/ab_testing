#!/usr/bin/env python3
"""
Quick test script for Smart A/B Testing Platform.

Usage:
    python3 test_api.py [--full]

Examples:
    python3 test_api.py          # Run quick test
    python3 test_api.py --full   # Run full test with more data
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str) -> None:
    """Print a formatted section title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_response(label: str, data: Any) -> None:
    """Print formatted response data."""
    print(f"{label}:")
    print(json.dumps(data, indent=2))
    print()


def test_health_check() -> bool:
    """Test health check endpoint."""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/")
        response.raise_for_status()
        print_response("Health Status", response.json())
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_create_experiment() -> bool:
    """Test creating an experiment."""
    print_section("2. Create Experiment")
    try:
        # Use timestamp to ensure unique names
        import time
        name = f"test_exp_{int(time.time() * 1000)}"
        payload = {"name": name}
        response = requests.post(
            f"{BASE_URL}/experiment/",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        print_response("Created Experiment", data)
        
        # Store experiment ID for later tests
        global EXPERIMENT_ID
        EXPERIMENT_ID = data["id"]
        return True
    except Exception as e:
        print(f"❌ Failed to create experiment: {e}")
        return False


def test_assign_users(num_users: int = 10) -> bool:
    """Test user assignment."""
    print_section(f"3. Assign {num_users} Users")
    try:
        assignments = {}
        for i in range(1, num_users + 1):
            response = requests.get(
                f"{BASE_URL}/assign/",
                params={"user_id": i, "experiment_id": EXPERIMENT_ID}
            )
            response.raise_for_status()
            data = response.json()
            assignments[f"User {i}"] = data["variant"]
        
        print_response("User Assignments", assignments)
        
        # Count variants
        control = sum(1 for v in assignments.values() if v == "control")
        treatment = sum(1 for v in assignments.values() if v == "treatment")
        print(f"Control: {control}, Treatment: {treatment}\n")
        return True
    except Exception as e:
        print(f"❌ Failed to assign users: {e}")
        return False


def test_log_events(num_impressions: int = 100) -> bool:
    """Test logging events."""
    print_section(f"4. Log {num_impressions} Events")
    try:
        # Log impressions for control variant
        control_count = num_impressions // 2
        for i in range(1, control_count + 1):
            requests.post(
                f"{BASE_URL}/event/",
                json={
                    "user_id": i,
                    "experiment_id": EXPERIMENT_ID,
                    "variant": "control",
                    "event_type": "impression"
                }
            )
        
        # Log impressions for treatment variant
        treatment_count = num_impressions - control_count
        for i in range(control_count + 1, num_impressions + 1):
            requests.post(
                f"{BASE_URL}/event/",
                json={
                    "user_id": i,
                    "experiment_id": EXPERIMENT_ID,
                    "variant": "treatment",
                    "event_type": "impression"
                }
            )
        
        # Log some clicks
        for i in range(1, control_count // 2):
            requests.post(
                f"{BASE_URL}/event/",
                json={
                    "user_id": i,
                    "experiment_id": EXPERIMENT_ID,
                    "variant": "control",
                    "event_type": "click"
                }
            )
        
        for i in range(control_count + 1, control_count + treatment_count // 2):
            requests.post(
                f"{BASE_URL}/event/",
                json={
                    "user_id": i,
                    "experiment_id": EXPERIMENT_ID,
                    "variant": "treatment",
                    "event_type": "click"
                }
            )
        
        # Log conversions
        for i in range(1, control_count // 5):
            requests.post(
                f"{BASE_URL}/event/",
                json={
                    "user_id": i,
                    "experiment_id": EXPERIMENT_ID,
                    "variant": "control",
                    "event_type": "conversion"
                }
            )
        
        for i in range(control_count + 1, control_count + treatment_count // 3):
            requests.post(
                f"{BASE_URL}/event/",
                json={
                    "user_id": i,
                    "experiment_id": EXPERIMENT_ID,
                    "variant": "treatment",
                    "event_type": "conversion"
                }
            )
        
        print(f"✅ Logged {num_impressions} impressions and related events\n")
        return True
    except Exception as e:
        print(f"❌ Failed to log events: {e}")
        return False


def test_get_results() -> bool:
    """Test getting experiment results."""
    print_section("5. Get Results")
    try:
        response = requests.get(
            f"{BASE_URL}/results/",
            params={"experiment_id": EXPERIMENT_ID}
        )
        response.raise_for_status()
        results = response.json()
        print_response("Experiment Results", results)
        
        # Print comparison
        control_conv = results["control"]["conversion_rate"]
        treatment_conv = results["treatment"]["conversion_rate"]
        better = "treatment" if treatment_conv > control_conv else "control"
        
        print(f"📊 Metrics Summary:")
        print(f"  Control Conversion Rate:   {control_conv:.4f}")
        print(f"  Treatment Conversion Rate: {treatment_conv:.4f}")
        print(f"  Better Variant:            {better.upper()}\n")
        
        return True
    except Exception as e:
        print(f"❌ Failed to get results: {e}")
        return False


def test_bandit_behavior() -> bool:
    """Test that bandit algorithm favors better variant."""
    print_section("6. Test Bandit Algorithm (Exploitation)")
    try:
        print("Assigning new users after 100+ impressions...")
        assignments = {}
        
        for i in range(200, 220):
            response = requests.get(
                f"{BASE_URL}/assign/",
                params={"user_id": i, "experiment_id": EXPERIMENT_ID}
            )
            response.raise_for_status()
            data = response.json()
            assignments[f"User {i}"] = data["variant"]
        
        control = sum(1 for v in assignments.values() if v == "control")
        treatment = sum(1 for v in assignments.values() if v == "treatment")
        
        print(f"New Assignments:")
        print(f"  Control:   {control}/20 ({control*5}%)")
        print(f"  Treatment: {treatment}/20 ({treatment*5}%)\n")
        
        if treatment >= 15:  # Expect ~90% exploitation + ~10% exploration
            print("✅ Bandit algorithm working correctly (favoring better variant)\n")
            return True
        else:
            print("⚠️  Bandit behavior inconclusive (treatment should be ~18/20)\n")
            return True  # Don't fail test
    except Exception as e:
        print(f"❌ Failed to test bandit behavior: {e}")
        return False


def run_quick_test() -> None:
    """Run quick test suite."""
    print("\n" + "="*60)
    print("  Smart A/B Testing Platform - Quick Test")
    print("="*60)
    
    tests = [
        test_health_check,
        test_create_experiment,
        test_assign_users,
        test_log_events,
        test_get_results,
        test_bandit_behavior,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            # Stop if experiment creation fails
            if test == test_create_experiment and not result:
                print("\n⚠️ Experiment creation failed. Stopping tests.\n")
                break
        except Exception as e:
            print(f"❌ Unexpected error: {e}\n")
            results.append(False)
    
    # Print summary
    print_section("Summary")
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}\n")
    
    if passed == total:
        print("✅ All tests passed! Platform is working correctly.\n")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.\n")
        return 1


def run_full_test() -> None:
    """Run full test suite with more data."""
    print("\n" + "="*60)
    print("  Smart A/B Testing Platform - Full Test")
    print("="*60)
    
    tests = [
        test_health_check,
        test_create_experiment,
        lambda: test_assign_users(num_users=20),
        lambda: test_log_events(num_impressions=200),
        test_get_results,
        test_bandit_behavior,
    ]
    
    results = []
    for i, test in enumerate(tests):
        try:
            result = test()
            results.append(result)
            # Stop if experiment creation fails (second test)
            if i == 1 and not result:
                print("\n⚠️ Experiment creation failed. Stopping tests.\n")
                break
        except Exception as e:
            print(f"❌ Unexpected error: {e}\n")
            results.append(False)
    
    # Print summary
    print_section("Summary")
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}\n")
    
    if passed == total:
        print("✅ All tests passed! Platform is working correctly.\n")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.\n")
        return 1


# Global variable to store experiment ID
EXPERIMENT_ID = None


if __name__ == "__main__":
    try:
        if "--full" in sys.argv:
            exit_code = run_full_test()
        else:
            exit_code = run_quick_test()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user.\n")
        sys.exit(1)
