#!/usr/bin/env python3
"""
scripts/verify.py - Comprehensive Verification Runner for LungRay Platform.
Usage: python scripts/verify.py or powershell -File scripts/verify.ps1
"""
import sys
import subprocess
import shutil

# Reconfigure stdout/stderr to utf-8 if possible
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_step(step_name: str, cmd: list) -> bool:
    print(f"\n[+] Running: {step_name}...")
    try:
        res = subprocess.run(cmd, check=False)
        if res.returncode != 0:
            print(f"[FAIL] {step_name} (Exit code: {res.returncode})")
            return False
        print(f"[PASS] {step_name}")
        return True
    except Exception as e:
        print(f"[ERROR] {step_name} - {e}")
        return False

def main():
    print("=" * 60)
    print(" [LungRay] AUTOMATED CODE VERIFICATION RUNNER")
    print("=" * 60)
    
    # 1. Compile & Syntax Check
    if not run_step("Compileall (Python Syntax Check)", [sys.executable, "-m", "compileall", "src", "tests", "-q"]):
        sys.exit(1)
        
    # 2. Linting (Ruff or Flake8 if available)
    if shutil.which("ruff"):
        if not run_step("Ruff Linting", ["ruff", "check", "src", "tests", "--select", "E9,F63,F7,F82"]):
            sys.exit(1)
    elif shutil.which("flake8"):
        if not run_step("Flake8 Linting", ["flake8", "src", "tests", "--select=E9,F63,F7,F82"]):
            sys.exit(1)
    else:
        print("\n[*] Notice: Ruff/Flake8 not installed in this environment; basic syntax validated by compileall.")

    # 3. Pytest Unit Tests
    if not run_step("Pytest Unit Tests", [sys.executable, "-m", "pytest", "tests", "-q", "--tb=short"]):
        sys.exit(1)

    print("\n" + "=" * 60)
    print(">>> SUCCESS: ALL CHECKS PASSED - READY FOR GATEKEEPER REVIEW <<<")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
