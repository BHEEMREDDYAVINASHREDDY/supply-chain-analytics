import pandas as pd
import numpy as np
import os

os.makedirs('outputs', exist_ok=True)

# ── LOAD CLEANED DATA ─────────────────────────────────────────────────────────
orders    = pd.read_csv('data/orders_clean.csv',    parse_dates=['order_date'])
inventory = pd.read_csv('data/inventory_clean.csv')

delivered = orders[orders['status'] == 'Delivered']
pending   = orders[orders['status'] == 'Pending']
cancelled = orders[orders['status'] == 'Cancelled']

# ── KPI 1: On-Time Delivery Rate ──────────────────────────────────────────────
otd_rate        = delivered['on_time'].mean() * 100
otd_by_supplier = (
    delivered.groupby('supplier')['on_time'].mean() * 100
).round(1).reset_index()
otd_by_supplier.columns = ['supplier', 'otd_pct']

# ── KPI 2: Stockout Rate ──────────────────────────────────────────────────────
stockout_rate      = (inventory['current_stock'] < inventory['reorder_point']).mean() * 100
high_risk_products = inventory[inventory['stockout_risk'] == 'High']
medium_risk        = inventory[inventory['stockout_risk'] == 'Medium']

# ── KPI 3: Average Lead Time ──────────────────────────────────────────────────
avg_lead_time        = delivered['actual_days'].mean()
lead_time_by_supplier = delivered.groupby('supplier')['actual_days'].mean().round(1)

# ── KPI 4: Order Fulfillment Rate ─────────────────────────────────────────────
fulfillment_rate = len(delivered) / len(orders) * 100
cancellation_rate = len(cancelled) / len(orders) * 100

# ── KPI 5: Revenue KPIs ───────────────────────────────────────────────────────
total_revenue          = orders['revenue'].sum()
avg_order_value        = orders['revenue'].mean()
revenue_by_category    = delivered.groupby('category')['revenue'].sum().sort_values(ascending=False)
revenue_by_supplier    = delivered.groupby('supplier')['revenue'].sum().sort_values(ascending=False)
revenue_by_warehouse   = delivered.groupby('warehouse')['revenue'].sum().sort_values(ascending=False)

# ── KPI 6: Inventory Turnover ─────────────────────────────────────────────────
avg_turnover           = inventory['turnover_ratio'].mean()
turnover_by_category   = inventory.groupby('category')['turnover_ratio'].mean().round(2)

# ── KPI 7: Defect Rate ────────────────────────────────────────────────────────
total_units_ordered    = delivered['quantity'].sum()
total_defects          = delivered['defects'].sum()
defect_rate            = (total_defects / total_units_ordered * 100)
defect_by_supplier     = (
    delivered.groupby('supplier')
    .apply(lambda x: (x['defects'].sum() / x['quantity'].sum() * 100))
    .round(2)
    .reset_index()
)
defect_by_supplier.columns = ['supplier', 'defect_rate_pct']

# ── MONTHLY TREND ─────────────────────────────────────────────────────────────
monthly = delivered.groupby('month').agg(
    orders        = ('order_id',    'count'),
    revenue       = ('revenue',     'sum'),
    units         = ('quantity',    'sum'),
    otd_pct       = ('on_time',     'mean'),
    avg_lead_time = ('actual_days', 'mean'),
).reset_index()
monthly['otd_pct']       = (monthly['otd_pct'] * 100).round(1)
monthly['avg_lead_time'] = monthly['avg_lead_time'].round(1)
monthly['revenue']       = monthly['revenue'].round(0)

# ── SAVE KPI RESULTS ──────────────────────────────────────────────────────────
monthly.to_csv('data/monthly_kpi.csv',             index=False)
otd_by_supplier.to_csv('data/otd_by_supplier.csv', index=False)
defect_by_supplier.to_csv('data/defects.csv',      index=False)

# ── PRINT KPI DASHBOARD ───────────────────────────────────────────────────────
print("=" * 60)
print("  STEP 3 — KPI ANALYSIS COMPLETE")
print("=" * 60)

print("\n── CORE KPIs ───────────────────────────────────────────────")
print(f"  Total Revenue          : ₹{total_revenue:>15,.0f}")
print(f"  Average Order Value    : ₹{avg_order_value:>15,.0f}")
print(f"  On-Time Delivery Rate  :  {otd_rate:>14.1f}%")
print(f"  Order Fulfillment Rate :  {fulfillment_rate:>14.1f}%")
print(f"  Cancellation Rate      :  {cancellation_rate:>14.1f}%")
print(f"  Avg Lead Time          :  {avg_lead_time:>13.1f} days")
print(f"  Stockout Risk Rate     :  {stockout_rate:>14.1f}%")
print(f"  Avg Inventory Turnover :  {avg_turnover:>14.2f}x")
print(f"  Overall Defect Rate    :  {defect_rate:>14.2f}%")

print("\n── OTD % by Supplier ───────────────────────────────────────")
for _, row in otd_by_supplier.iterrows():
    bar = '█' * int(row['otd_pct'] / 5)
    print(f"  {row['supplier']:<12} {row['otd_pct']:>5.1f}%  {bar}")

print("\n── Revenue by Category ─────────────────────────────────────")
for cat, rev in revenue_by_category.items():
    print(f"  {cat:<16} ₹{rev:>15,.0f}")

print("\n── Revenue by Warehouse ────────────────────────────────────")
for wh, rev in revenue_by_warehouse.items():
    print(f"  {wh:<12} ₹{rev:>15,.0f}")

print("\n── Defect Rate by Supplier ─────────────────────────────────")
for _, row in defect_by_supplier.iterrows():
    print(f"  {row['supplier']:<12}  {row['defect_rate_pct']:>5.2f}%")

print("\n── Inventory Turnover by Category ──────────────────────────")
for cat, tr in turnover_by_category.items():
    print(f"  {cat:<16}  {tr:.2f}x")

print("\n── High Stockout Risk Products ─────────────────────────────")
if len(high_risk_products) == 0:
    print("  None — all products are safe.")
else:
    print(high_risk_products[['product_id','category','current_stock','reorder_point','days_of_stock']].to_string(index=False))

print("\n" + "=" * 60)
print("  KPI data saved. Ready for Step 4.")
print("=" * 60)