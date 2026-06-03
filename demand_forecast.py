import pandas as pd
import numpy as np
import os

os.makedirs('outputs', exist_ok=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
orders   = pd.read_csv('data/orders_clean.csv', parse_dates=['order_date'])
delivered = orders[orders['status'] == 'Delivered']

# ── MONTHLY DEMAND (ACTUAL) ───────────────────────────────────────────────────
monthly = delivered.groupby('month').agg(
    actual_demand = ('quantity', 'sum'),
    actual_revenue = ('revenue', 'sum'),
    order_count    = ('order_id', 'count'),
).reset_index().sort_values('month').reset_index(drop=True)

# ── MOVING AVERAGE FORECAST ───────────────────────────────────────────────────
# 3-month weighted moving average
# Weights: most recent month = 50%, previous = 30%, oldest = 20%
weights = np.array([0.20, 0.30, 0.50])

forecast_demand  = []
forecast_revenue = []

for i in range(len(monthly)):
    if i < 3:
        forecast_demand.append(np.nan)
        forecast_revenue.append(np.nan)
    else:
        last_3_demand  = monthly['actual_demand'].iloc[i-3:i].values
        last_3_revenue = monthly['actual_revenue'].iloc[i-3:i].values
        forecast_demand.append(round(np.dot(weights, last_3_demand), 0))
        forecast_revenue.append(round(np.dot(weights, last_3_revenue), 0))

monthly['forecast_demand']  = forecast_demand
monthly['forecast_revenue'] = forecast_revenue

# ── FORECAST ACCURACY (MAPE) ──────────────────────────────────────────────────
# MAPE = Mean Absolute Percentage Error
# Lower MAPE = more accurate forecast
valid = monthly.dropna(subset=['forecast_demand'])
mape  = (
    abs(valid['actual_demand'] - valid['forecast_demand']) / valid['actual_demand']
).mean() * 100

accuracy = 100 - mape

# ── FORECAST NEXT 3 MONTHS ────────────────────────────────────────────────────
last_3_demand  = monthly['actual_demand'].tail(3).values
last_3_revenue = monthly['actual_revenue'].tail(3).values

next_months = []
last_month  = pd.Period(monthly['month'].iloc[-1], freq='M')

for i in range(1, 4):
    next_month   = last_month + i
    next_demand  = round(np.dot(weights, last_3_demand), 0)
    next_revenue = round(np.dot(weights, last_3_revenue), 0)
    next_months.append({
        'month'           : str(next_month),
        'forecast_demand' : next_demand,
        'forecast_revenue': next_revenue,
        'lower_bound'     : round(next_demand * 0.90, 0),
        'upper_bound'     : round(next_demand * 1.10, 0),
        'type'            : 'Forecast'
    })
    last_3_demand  = np.append(last_3_demand[1:],  next_demand)
    last_3_revenue = np.append(last_3_revenue[1:], next_revenue)

future_df = pd.DataFrame(next_months)

# ── SEASONAL ANALYSIS ─────────────────────────────────────────────────────────
orders['month_num'] = pd.to_datetime(orders['order_date']).dt.month
season_demand = (
    delivered.groupby(delivered['order_date'].dt.month)['quantity']
    .sum()
    .reset_index()
)
season_demand.columns = ['month_num', 'total_demand']
season_demand['month_name'] = pd.to_datetime(
    season_demand['month_num'], format='%m'
).dt.strftime('%B')
peak_month = season_demand.loc[season_demand['total_demand'].idxmax(), 'month_name']
low_month  = season_demand.loc[season_demand['total_demand'].idxmin(), 'month_name']

# ── CATEGORY-LEVEL FORECAST ───────────────────────────────────────────────────
cat_monthly = delivered.groupby(['month', 'category'])['quantity'].sum().reset_index()
cat_forecast = cat_monthly.groupby('category').agg(
    avg_monthly_demand = ('quantity', 'mean'),
    total_demand       = ('quantity', 'sum'),
    peak_demand        = ('quantity', 'max'),
).round(0).reset_index()
cat_forecast['recommended_safety_stock'] = (cat_forecast['avg_monthly_demand'] * 0.5).round(0)

# ── SAVE ──────────────────────────────────────────────────────────────────────
monthly.to_csv('data/monthly_forecast.csv',     index=False)
future_df.to_csv('data/future_forecast.csv',    index=False)
cat_forecast.to_csv('data/category_forecast.csv', index=False)

# ── PRINT RESULTS ─────────────────────────────────────────────────────────────
print("=" * 60)
print("  STEP 5 — DEMAND FORECASTING COMPLETE")
print("=" * 60)

print(f"\n── Forecast Accuracy ───────────────────────────────────────")
print(f"  MAPE (error rate) : {mape:.1f}%")
print(f"  Accuracy          : {accuracy:.1f}%")
print(f"  Method            : 3-month weighted moving average")

print(f"\n── Seasonal Insights ───────────────────────────────────────")
print(f"  Peak demand month : {peak_month}")
print(f"  Lowest demand     : {low_month}")

print(f"\n── Next 3 Months Forecast ──────────────────────────────────")
print(f"  {'Month':<12} {'Demand':>10} {'Lower':>10} {'Upper':>10} {'Revenue':>15}")
print(f"  {'-'*57}")
for _, row in future_df.iterrows():
    print(f"  {row['month']:<12} {row['forecast_demand']:>10,.0f} "
          f"{row['lower_bound']:>10,.0f} {row['upper_bound']:>10,.0f} "
          f"₹{row['forecast_revenue']:>14,.0f}")

print(f"\n── Category Safety Stock Recommendations ───────────────────")
print(cat_forecast[['category','avg_monthly_demand','peak_demand',
                     'recommended_safety_stock']].to_string(index=False))

print("\n" + "=" * 60)
print("  Forecast saved. Ready for Step 6 — Visualizations.")
print("=" * 60)