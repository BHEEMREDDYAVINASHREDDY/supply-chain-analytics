import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
import os

os.makedirs('outputs', exist_ok=True)

# ── STYLE SETUP ───────────────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor'  : '#0d1117',
    'axes.facecolor'    : '#161b22',
    'axes.edgecolor'    : '#30363d',
    'axes.labelcolor'   : '#c9d1d9',
    'axes.titlecolor'   : '#f0f6fc',
    'text.color'        : '#c9d1d9',
    'xtick.color'       : '#8b949e',
    'ytick.color'       : '#8b949e',
    'grid.color'        : '#21262d',
    'grid.linewidth'    : 0.6,
    'font.family'       : 'DejaVu Sans',
    'axes.titlesize'    : 13,
    'axes.titleweight'  : 'bold',
    'axes.labelsize'    : 10,
})

BLUE    = '#2196F3'
GREEN   = '#4CAF50'
ORANGE  = '#FF9800'
RED     = '#F44336'
PURPLE  = '#9C27B0'
TEAL    = '#009688'
YELLOW  = '#FFC107'
COLORS  = [BLUE, GREEN, ORANGE, RED, PURPLE]

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
orders    = pd.read_csv('data/orders_clean.csv',   parse_dates=['order_date'])
inventory = pd.read_csv('data/inventory_clean.csv')
scorecard = pd.read_csv('data/scorecard.csv')
monthly   = pd.read_csv('data/monthly_forecast.csv')
future    = pd.read_csv('data/future_forecast.csv')
cat_fc    = pd.read_csv('data/category_forecast.csv')

delivered = orders[orders['status'] == 'Delivered']

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 1 — EXECUTIVE KPI DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(18, 10), facecolor='#0d1117')
fig.suptitle('Supply Chain Analytics — Executive KPI Dashboard',
             fontsize=18, fontweight='bold', color='#f0f6fc', y=0.98)

gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.4)

# KPI Metric Cards (top row)
kpis = [
    ('Total Revenue',       f"₹{orders['revenue'].sum()/1e6:.1f}M",    BLUE),
    ('On-Time Delivery',    f"{delivered['on_time'].mean()*100:.1f}%",  GREEN),
    ('Avg Lead Time',       f"{delivered['actual_days'].mean():.1f}d",  ORANGE),
    ('Stockout Risk Rate',  f"{(inventory['current_stock']<inventory['reorder_point']).mean()*100:.1f}%", RED),
]
for i, (label, value, color) in enumerate(kpis):
    ax = fig.add_subplot(gs[0, i])
    ax.set_facecolor('#161b22')
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')
    ax.add_patch(mpatches.FancyBboxPatch(
        (0.05, 0.05), 0.9, 0.9,
        boxstyle='round,pad=0.05',
        facecolor='#21262d', edgecolor=color, linewidth=2
    ))
    ax.text(0.5, 0.65, value,  ha='center', va='center', fontsize=22,
            fontweight='bold', color=color)
    ax.text(0.5, 0.28, label,  ha='center', va='center', fontsize=9,
            color='#8b949e')

# Chart: Monthly Revenue
ax2 = fig.add_subplot(gs[1, :2])
months_short = [m[-7:] for m in monthly['month'].tolist()]
bars = ax2.bar(months_short, monthly['actual_revenue']/1e6,
               color=BLUE, alpha=0.8, width=0.6)
ax2.plot(months_short, monthly['forecast_revenue']/1e6,
         color=ORANGE, linewidth=2, marker='o', markersize=4, label='Forecast', zorder=5)
ax2.set_title('Monthly Revenue — Actual vs Forecast')
ax2.set_ylabel('Revenue (₹M)')
ax2.legend(fontsize=8)
ax2.tick_params(axis='x', rotation=45, labelsize=7)
ax2.yaxis.grid(True, alpha=0.3)

# Chart: OTD by Supplier
ax3 = fig.add_subplot(gs[1, 2:])
otd = delivered.groupby('supplier')['on_time'].mean().mul(100).sort_values()
colors_otd = [RED if v < 70 else ORANGE if v < 85 else GREEN for v in otd.values]
bars2 = ax3.barh(otd.index, otd.values, color=colors_otd, alpha=0.85)
ax3.axvline(x=85, color=YELLOW, linestyle='--', linewidth=1.5, label='Target 85%')
for bar, val in zip(bars2, otd.values):
    ax3.text(val + 0.3, bar.get_y() + bar.get_height()/2,
             f'{val:.1f}%', va='center', fontsize=9, color='#c9d1d9')
ax3.set_title('On-Time Delivery % by Supplier')
ax3.set_xlabel('OTD %')
ax3.set_xlim(0, 105)
ax3.legend(fontsize=8)
ax3.xaxis.grid(True, alpha=0.3)

# Chart: Revenue by Category
ax4 = fig.add_subplot(gs[2, :2])
cat_rev = delivered.groupby('category')['revenue'].sum().sort_values(ascending=False)
ax4.bar(cat_rev.index, cat_rev.values/1e6, color=COLORS, alpha=0.85)
ax4.set_title('Revenue by Category')
ax4.set_ylabel('Revenue (₹M)')
ax4.tick_params(axis='x', rotation=15, labelsize=8)
ax4.yaxis.grid(True, alpha=0.3)

# Chart: Status breakdown donut
ax5 = fig.add_subplot(gs[2, 2:])
status_counts = orders['status'].value_counts()
wedge_colors  = [GREEN, ORANGE, RED]
wedges, texts, autotexts = ax5.pie(
    status_counts.values,
    labels=status_counts.index,
    colors=wedge_colors[:len(status_counts)],
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops=dict(width=0.6),
    textprops=dict(color='#c9d1d9', fontsize=9)
)
for at in autotexts:
    at.set_color('#f0f6fc')
    at.set_fontsize(9)
ax5.set_title('Order Status Distribution')

plt.savefig('outputs/chart1_kpi_dashboard.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print("  Saved: chart1_kpi_dashboard.png")

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 2 — SUPPLIER PERFORMANCE DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(16, 10), facecolor='#0d1117')
fig.suptitle('Supplier Performance Analysis',
             fontsize=16, fontweight='bold', color='#f0f6fc', y=0.98)

# Composite Score Bar
ax = axes[0, 0]
score_colors = [
    GREEN if s >= 80 else ORANGE if s >= 65 else RED
    for s in scorecard['composite_score']
]
bars = ax.bar(scorecard['supplier'], scorecard['composite_score'],
              color=score_colors, alpha=0.85, width=0.5)
ax.axhline(y=80, color=GREEN,  linestyle='--', linewidth=1, alpha=0.7, label='Excellent (80)')
ax.axhline(y=65, color=ORANGE, linestyle='--', linewidth=1, alpha=0.7, label='Watch (65)')
for bar, val in zip(bars, scorecard['composite_score']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}', ha='center', fontsize=9, color='#f0f6fc', fontweight='bold')
ax.set_title('Composite Supplier Score (0–100)')
ax.set_ylabel('Score')
ax.set_ylim(0, 110)
ax.legend(fontsize=8)
ax.yaxis.grid(True, alpha=0.3)

# Lead Time vs OTD Scatter
ax = axes[0, 1]
sc_colors = [
    GREEN if s == 'Excellent' else ORANGE if s == 'Good' else
    YELLOW if s == 'Watch' else RED
    for s in scorecard['status']
]
scatter = ax.scatter(
    scorecard['avg_lead_time'], scorecard['otd_pct'],
    s=scorecard['total_orders'] * 0.3,
    c=sc_colors, alpha=0.85, edgecolors='white', linewidths=0.5
)
for _, row in scorecard.iterrows():
    ax.annotate(row['supplier'],
                (row['avg_lead_time'], row['otd_pct']),
                textcoords='offset points', xytext=(6, 3),
                fontsize=8, color='#c9d1d9')
ax.axhline(y=85, color=YELLOW, linestyle='--', linewidth=1, alpha=0.7, label='OTD target')
ax.set_xlabel('Avg Lead Time (days)')
ax.set_ylabel('On-Time Delivery %')
ax.set_title('Lead Time vs OTD % (bubble = order volume)')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Defect Rate by Supplier
ax = axes[1, 0]
defects = scorecard.sort_values('defect_rate', ascending=False)
d_colors = [RED if v > 5 else ORANGE if v > 3 else GREEN for v in defects['defect_rate']]
bars = ax.bar(defects['supplier'], defects['defect_rate'],
              color=d_colors, alpha=0.85, width=0.5)
for bar, val in zip(bars, defects['defect_rate']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f'{val:.2f}%', ha='center', fontsize=9, color='#f0f6fc')
ax.set_title('Defect Rate by Supplier (%)')
ax.set_ylabel('Defect Rate %')
ax.yaxis.grid(True, alpha=0.3)

# Revenue share by supplier
ax = axes[1, 1]
rev_share = scorecard.set_index('supplier')['total_revenue']
wedges, texts, autotexts = ax.pie(
    rev_share.values,
    labels=rev_share.index,
    colors=COLORS,
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops=dict(width=0.55),
    textprops=dict(color='#c9d1d9', fontsize=9)
)
for at in autotexts:
    at.set_color('#f0f6fc')
    at.set_fontsize(9)
ax.set_title('Revenue Share by Supplier')

plt.tight_layout()
plt.savefig('outputs/chart2_supplier_analysis.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print("  Saved: chart2_supplier_analysis.png")

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 3 — INVENTORY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(16, 10), facecolor='#0d1117')
fig.suptitle('Inventory Analysis & Stockout Risk',
             fontsize=16, fontweight='bold', color='#f0f6fc', y=0.98)

# Stock vs Reorder Point (top 15 products)
ax = axes[0, 0]
top15 = inventory.nsmallest(15, 'days_of_stock')
bar_colors = [RED if r == 'High' else ORANGE if r == 'Medium' else GREEN
              for r in top15['stockout_risk']]
ax.barh(top15['product_id'], top15['current_stock'],  color=bar_colors, alpha=0.7, label='Current Stock')
ax.barh(top15['product_id'], top15['reorder_point'],  color=YELLOW, alpha=0.4, label='Reorder Point', height=0.3)
ax.set_title('Current Stock vs Reorder Point (Top 15 Risk)')
ax.set_xlabel('Units')
ax.legend(fontsize=8)
ax.xaxis.grid(True, alpha=0.3)

# Stockout Risk Distribution
ax = axes[0, 1]
risk_counts = inventory['stockout_risk'].value_counts()
risk_colors = {'High': RED, 'Medium': ORANGE, 'Low': GREEN}
bars = ax.bar(risk_counts.index,
              risk_counts.values,
              color=[risk_colors.get(r, BLUE) for r in risk_counts.index],
              alpha=0.85, width=0.4)
for bar, val in zip(bars, risk_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            str(val), ha='center', fontsize=11, color='#f0f6fc', fontweight='bold')
ax.set_title('Products by Stockout Risk Level')
ax.set_ylabel('Number of Products')
ax.yaxis.grid(True, alpha=0.3)

# Inventory Turnover by Category
ax = axes[1, 0]
turnover = inventory.groupby('category')['turnover_ratio'].mean().sort_values(ascending=False)
ax.bar(turnover.index, turnover.values, color=TEAL, alpha=0.8, width=0.5)
ax.axhline(y=turnover.mean(), color=YELLOW, linestyle='--',
           linewidth=1.5, label=f'Avg: {turnover.mean():.2f}x')
for i, (cat, val) in enumerate(turnover.items()):
    ax.text(i, val + 0.005, f'{val:.2f}x', ha='center', fontsize=9, color='#f0f6fc')
ax.set_title('Avg Inventory Turnover Ratio by Category')
ax.set_ylabel('Turnover Ratio')
ax.tick_params(axis='x', rotation=15)
ax.legend(fontsize=8)
ax.yaxis.grid(True, alpha=0.3)

# Days of Stock Heatmap by Category + Warehouse
ax = axes[1, 1]
heat_data = inventory.pivot_table(
    values='days_of_stock', index='category', columns='warehouse', aggfunc='mean'
).fillna(0)
sns.heatmap(heat_data, ax=ax, cmap='RdYlGn', annot=True, fmt='.0f',
            linewidths=0.5, linecolor='#0d1117',
            cbar_kws={'label': 'Days of Stock'})
ax.set_title('Days of Stock — Category × Warehouse')
ax.tick_params(axis='x', rotation=15, labelsize=8)
ax.tick_params(axis='y', rotation=0,  labelsize=8)

plt.tight_layout()
plt.savefig('outputs/chart3_inventory_analysis.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print("  Saved: chart3_inventory_analysis.png")

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 4 — DEMAND FORECAST
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(16, 10), facecolor='#0d1117')
fig.suptitle('Demand Forecasting & Trend Analysis',
             fontsize=16, fontweight='bold', color='#f0f6fc', y=0.98)

# Actual vs Forecast line chart
ax = axes[0, 0]
valid = monthly.dropna(subset=['forecast_demand'])
ax.fill_between(monthly.index, monthly['actual_demand'],
                alpha=0.2, color=BLUE)
ax.plot(monthly.index, monthly['actual_demand'],
        color=BLUE, linewidth=2, marker='o', markersize=4, label='Actual Demand')
ax.plot(valid.index, valid['forecast_demand'],
        color=ORANGE, linewidth=2, linestyle='--', marker='s',
        markersize=4, label='Forecast (WMA)')

# Future forecast
future_idx = [monthly.index[-1] + i for i in range(1, 4)]
ax.plot(future_idx, future['forecast_demand'],
        color=RED, linewidth=2, linestyle=':', marker='^', markersize=5, label='Future Forecast')
ax.fill_between(future_idx, future['lower_bound'], future['upper_bound'],
                alpha=0.15, color=RED, label='90% Confidence')
ax.set_title('Demand Forecast — Actual vs Predicted')
ax.set_ylabel('Units')
ax.set_xlabel('Month Index')
ax.legend(fontsize=8)
ax.yaxis.grid(True, alpha=0.3)

# Monthly order count trend
ax = axes[0, 1]
ax.bar(monthly.index, monthly['order_count'],
       color=PURPLE, alpha=0.7, width=0.6, label='Order Count')
ax2b = ax.twinx()
ax2b.plot(monthly.index, monthly['actual_demand'] / monthly['actual_demand'].max() * 100,
          color=GREEN, linewidth=2, marker='o', markersize=4, label='OTD %')
ax2b.set_ylabel('OTD %', color=GREEN)
ax2b.tick_params(axis='y', colors=GREEN)
ax.set_title('Monthly Orders & OTD Trend')
ax.set_ylabel('Order Count')
ax.set_xlabel('Month Index')
ax.yaxis.grid(True, alpha=0.3)

# Category demand distribution
ax = axes[1, 0]
cat_demand = delivered.groupby('category')['quantity'].sum().sort_values(ascending=False)
ax.bar(cat_demand.index, cat_demand.values, color=COLORS, alpha=0.85, width=0.5)
ax.set_title('Total Demand by Category')
ax.set_ylabel('Total Units Sold')
ax.tick_params(axis='x', rotation=15, labelsize=8)
for i, (cat, val) in enumerate(cat_demand.items()):
    ax.text(i, val + 500, f'{val:,.0f}', ha='center', fontsize=8, color='#c9d1d9')
ax.yaxis.grid(True, alpha=0.3)

# Safety stock recommendation
ax = axes[1, 1]
x     = np.arange(len(cat_fc))
width = 0.35
ax.bar(x - width/2, cat_fc['avg_monthly_demand'],
       width=width, color=BLUE,   alpha=0.85, label='Avg Monthly Demand')
ax.bar(x + width/2, cat_fc['recommended_safety_stock'],
       width=width, color=ORANGE, alpha=0.85, label='Recommended Safety Stock')
ax.set_xticks(x)
ax.set_xticklabels(cat_fc['category'], rotation=15, fontsize=8)
ax.set_title('Safety Stock Recommendation by Category')
ax.set_ylabel('Units')
ax.legend(fontsize=8)
ax.yaxis.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/chart4_demand_forecast.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print("  Saved: chart4_demand_forecast.png")

# ═══════════════════════════════════════════════════════════════════════════════
# CHART 5 — WAREHOUSE & OPERATIONS HEATMAP
# ═══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor='#0d1117')
fig.suptitle('Warehouse & Operations Analysis',
             fontsize=16, fontweight='bold', color='#f0f6fc', y=1.02)

# Supplier × Category Revenue Heatmap
ax = axes[0]
heat2 = delivered.pivot_table(
    values='revenue', index='supplier', columns='category', aggfunc='sum'
).fillna(0) / 1e6
sns.heatmap(heat2, ax=ax, cmap='Blues', annot=True, fmt='.1f',
            linewidths=0.5, linecolor='#0d1117',
            cbar_kws={'label': 'Revenue (₹M)'})
ax.set_title('Revenue Heatmap — Supplier × Category (₹M)')
ax.tick_params(axis='x', rotation=20, labelsize=8)
ax.tick_params(axis='y', rotation=0,  labelsize=8)

# Warehouse × Supplier Order Volume Heatmap
ax = axes[1]
heat3 = delivered.pivot_table(
    values='order_id', index='warehouse', columns='supplier', aggfunc='count'
).fillna(0)
sns.heatmap(heat3, ax=ax, cmap='Purples', annot=True, fmt='.0f',
            linewidths=0.5, linecolor='#0d1117',
            cbar_kws={'label': 'Order Count'})
ax.set_title('Order Volume Heatmap — Warehouse × Supplier')
ax.tick_params(axis='x', rotation=20, labelsize=8)
ax.tick_params(axis='y', rotation=0,  labelsize=8)

plt.tight_layout()
plt.savefig('outputs/chart5_heatmaps.png', dpi=150,
            bbox_inches='tight', facecolor='#0d1117')
plt.close()
print("  Saved: chart5_heatmaps.png")

print("\n" + "=" * 60)
print("  STEP 6 — ALL 5 CHARTS SAVED TO outputs/ FOLDER")
print("=" * 60)
print("  chart1_kpi_dashboard.png")
print("  chart2_supplier_analysis.png")
print("  chart3_inventory_analysis.png")
print("  chart4_demand_forecast.png")
print("  chart5_heatmaps.png")
print("=" * 60)