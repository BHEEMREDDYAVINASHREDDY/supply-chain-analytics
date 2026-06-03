import subprocess
import sys
import time

steps = [
    ('generate_data.py',      'Step 1 — Generate Dataset'),
    ('clean_and_sql.py',      'Step 2 — Clean Data + SQL'),
    ('kpi_analysis.py',       'Step 3 — KPI Analysis'),
    ('supplier_scorecard.py', 'Step 4 — Supplier Scorecard'),
    ('demand_forecast.py',    'Step 5 — Demand Forecast'),
    ('visualizations.py',     'Step 6 — Visualizations'),
]

print("=" * 60)
print("  SUPPLY CHAIN ANALYTICS — RUNNING FULL PIPELINE")
print("=" * 60)

for script, label in steps:
    print(f"\n── {label} {'─'*(45-len(label))}")
    start = time.time()
    result = subprocess.run([sys.executable, script], capture_output=False)
    elapsed = time.time() - start
    if result.returncode == 0:
        print(f"  DONE in {elapsed:.1f}s")
    else:
        print(f"  FAILED — check {script}")
        break

print("\n" + "=" * 60)
print("  PIPELINE COMPLETE — check outputs/ for all charts")
print("=" * 60)