import pandas as pd
import numpy as np
import os

os.makedirs('outputs', exist_ok=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
orders    = pd.read_csv('data/orders_clean.csv', parse_dates=['order_date'])
suppliers = pd.read_csv('data/suppliers.csv')
delivered = orders[orders['status'] == 'Delivered']

# ── BUILD SCORECARD ───────────────────────────────────────────────────────────
scorecard = delivered.groupby('supplier').agg(
    total_orders    = ('order_id',    'count'),
    total_revenue   = ('revenue',     'sum'),
    total_units     = ('quantity',    'sum'),
    avg_lead_time   = ('actual_days', 'mean'),
    otd_pct         = ('on_time',     'mean'),
    total_defects   = ('defects',     'sum'),
    avg_defects     = ('defects',     'mean'),
).reset_index()

# ── CALCULATED METRICS ────────────────────────────────────────────────────────
scorecard['otd_pct']       = (scorecard['otd_pct'] * 100).round(1)
scorecard['avg_lead_time'] = scorecard['avg_lead_time'].round(1)
scorecard['avg_defects']   = scorecard['avg_defects'].round(2)
scorecard['total_revenue'] = scorecard['total_revenue'].round(0)
scorecard['defect_rate']   = (
    scorecard['total_defects'] / scorecard['total_units'] * 100
).round(2)

# ── COMPOSITE SCORE (0–100) ───────────────────────────────────────────────────
# Weight breakdown:
#   OTD %       → 50 points  (most important: did they deliver on time?)
#   Defect rate → 30 points  (quality of goods)
#   Lead time   → 20 points  (speed of delivery)

max_lead   = scorecard['avg_lead_time'].max()
min_lead   = scorecard['avg_lead_time'].min()
max_defect = scorecard['defect_rate'].max()

scorecard['otd_score']     = scorecard['otd_pct'] * 0.50
scorecard['quality_score'] = (1 - scorecard['defect_rate'] / max_defect) * 100 * 0.30
scorecard['speed_score']   = (
    1 - (scorecard['avg_lead_time'] - min_lead) / (max_lead - min_lead + 0.01)
) * 100 * 0.20

scorecard['composite_score'] = (
    scorecard['otd_score'] +
    scorecard['quality_score'] +
    scorecard['speed_score']
).round(1)

# ── STATUS FLAGS ──────────────────────────────────────────────────────────────
def get_status(score):
    if score >= 80:
        return 'Excellent'
    elif score >= 65:
        return 'Good'
    elif score >= 50:
        return 'Watch'
    else:
        return 'At Risk'

scorecard['status'] = scorecard['composite_score'].apply(get_status)

# ── RANK SUPPLIERS ────────────────────────────────────────────────────────────
scorecard = scorecard.sort_values('composite_score', ascending=False).reset_index(drop=True)
scorecard['rank'] = scorecard.index + 1

# ── MERGE WITH SUPPLIER MASTER ────────────────────────────────────────────────
scorecard = scorecard.merge(
    suppliers[['supplier', 'country', 'contract_value', 'rating', 'since_year']],
    on='supplier', how='left'
)

# ── SAVE ──────────────────────────────────────────────────────────────────────
scorecard.to_csv('data/scorecard.csv', index=False)

# ── PRINT SCORECARD ───────────────────────────────────────────────────────────
print("=" * 70)
print("  STEP 4 — SUPPLIER SCORECARD COMPLETE")
print("=" * 70)

print("\n── Full Supplier Scorecard ──────────────────────────────────────────")
display_cols = ['rank','supplier','country','total_orders','total_revenue',
                'otd_pct','avg_lead_time','defect_rate','composite_score','status']
print(scorecard[display_cols].to_string(index=False))

print("\n── Score Breakdown ──────────────────────────────────────────────────")
for _, row in scorecard.iterrows():
    bar_len = int(row['composite_score'] / 2)
    bar     = '█' * bar_len + '░' * (50 - bar_len)
    print(f"  #{int(row['rank'])} {row['supplier']:<12}  {bar}  {row['composite_score']:.1f}  [{row['status']}]")

print("\n── Business Recommendations ─────────────────────────────────────────")
for _, row in scorecard.iterrows():
    if row['status'] == 'At Risk':
        print(f"  {row['supplier']} → URGENT: OTD {row['otd_pct']}%, defect rate {row['defect_rate']}% — consider dual sourcing")
    elif row['status'] == 'Watch':
        print(f"  {row['supplier']} → MONITOR: Lead time {row['avg_lead_time']}d — request improvement plan")
    elif row['status'] == 'Good':
        print(f"  {row['supplier']} → STABLE: Performing well — maintain relationship")
    else:
        print(f"  {row['supplier']} → EXCELLENT: Top performer — prioritize for new contracts")

print("\n" + "=" * 70)
print("  Scorecard saved to data/scorecard.csv. Ready for Step 5.")
print("=" * 70)