import subprocess
import sys

scripts = [
    "scripts/update_fees.py",
    "scripts/update_dexs.py",
    "scripts/update_bridges.py",
]

for script in scripts:
    print(f"\n{'='*50}\n🚀 Running {script}\n{'='*50}")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"❌ {script} failed")
        sys.exit(1)

print("\n✅ All scripts completed")
