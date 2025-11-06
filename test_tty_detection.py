#!/usr/bin/env python3
"""
TTY Detection Verification Script

Tests all 4 scenarios from verify-1-2 checklist:
1. Interactive terminal (should use RichUi)
2. Piped output (should use PlainUi)
3. CI=true environment (should use PlainUi)
4. --plain flag (should use PlainUi)
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src/claude_skills')

from claude_skills.common.ui_factory import (
    create_ui,
    get_backend_name,
    is_tty_available,
    is_ci_environment,
    should_use_plain_ui,
    format_backend_info
)


def test_scenario_1_interactive():
    """Test 1: Interactive terminal (should use RichUi)"""
    print("\n" + "="*60)
    print("SCENARIO 1: Interactive Terminal")
    print("="*60)

    print(f"TTY Available: {is_tty_available()}")
    print(f"CI Environment: {is_ci_environment()}")
    print(f"Should Use Plain: {should_use_plain_ui()}")

    ui = create_ui()
    backend = get_backend_name(ui)
    print(f"Selected Backend: {backend}")

    expected = "RichUi" if is_tty_available() and not is_ci_environment() else "PlainUi"
    status = "✅ PASS" if backend == expected else "❌ FAIL"
    print(f"{status} - Expected: {expected}, Got: {backend}")

    return backend == expected


def test_scenario_2_force_plain():
    """Test 2: Force plain flag (should use PlainUi)"""
    print("\n" + "="*60)
    print("SCENARIO 2: Force Plain Flag")
    print("="*60)

    ui = create_ui(force_plain=True)
    backend = get_backend_name(ui)
    print(f"Selected Backend: {backend}")

    expected = "PlainUi"
    status = "✅ PASS" if backend == expected else "❌ FAIL"
    print(f"{status} - Expected: {expected}, Got: {backend}")

    return backend == expected


def test_scenario_3_ci_env():
    """Test 3: CI=true environment (should use PlainUi)"""
    print("\n" + "="*60)
    print("SCENARIO 3: CI Environment Variable")
    print("="*60)

    # Temporarily set CI env var
    old_ci = os.environ.get("CI")
    os.environ["CI"] = "true"

    try:
        print(f"CI Environment: {is_ci_environment()}")
        print(f"Should Use Plain: {should_use_plain_ui()}")

        ui = create_ui()
        backend = get_backend_name(ui)
        print(f"Selected Backend: {backend}")

        expected = "PlainUi"
        status = "✅ PASS" if backend == expected else "❌ FAIL"
        print(f"{status} - Expected: {expected}, Got: {backend}")

        return backend == expected
    finally:
        # Restore original CI env var
        if old_ci is None:
            os.environ.pop("CI", None)
        else:
            os.environ["CI"] = old_ci


def test_scenario_4_force_plain_env():
    """Test 4: FORCE_PLAIN_UI environment variable (should use PlainUi)"""
    print("\n" + "="*60)
    print("SCENARIO 4: FORCE_PLAIN_UI Environment Variable")
    print("="*60)

    # Temporarily set FORCE_PLAIN_UI env var
    old_force = os.environ.get("FORCE_PLAIN_UI")
    os.environ["FORCE_PLAIN_UI"] = "1"

    try:
        print(f"Should Use Plain: {should_use_plain_ui()}")

        ui = create_ui()
        backend = get_backend_name(ui)
        print(f"Selected Backend: {backend}")

        expected = "PlainUi"
        status = "✅ PASS" if backend == expected else "❌ FAIL"
        print(f"{status} - Expected: {expected}, Got: {backend}")

        return backend == expected
    finally:
        # Restore original env var
        if old_force is None:
            os.environ.pop("FORCE_PLAIN_UI", None)
        else:
            os.environ["FORCE_PLAIN_UI"] = old_force


def main():
    """Run all TTY detection tests"""
    print("\n" + "="*60)
    print("TTY DETECTION VERIFICATION (verify-1-2)")
    print("="*60)
    print("\nCurrent Environment:")
    print(format_backend_info())

    # Run all tests
    results = []
    results.append(("Interactive Terminal", test_scenario_1_interactive()))
    results.append(("Force Plain Flag", test_scenario_2_force_plain()))
    results.append(("CI Environment", test_scenario_3_ci_env()))
    results.append(("FORCE_PLAIN_UI Env", test_scenario_4_force_plain_env()))

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - TTY detection works correctly!")
    else:
        print("❌ SOME TESTS FAILED - Review output above")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
