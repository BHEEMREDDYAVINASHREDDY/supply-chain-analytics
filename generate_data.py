import pandas as pd
import numpy as np
import os

np.random.seed(42)
os.makedirs('data', exist_ok=True)

# ── TABLE 1: ORDERS ──────────────────────────────────────────────────────────
n = 2000

suppliers  = ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D', 'Supplier E']
categories = ['Electronics', 'Apparel', 'Packaging', 'Raw Materials', 'Finished Goods']
statuses   = ['Delivered', 'Pending', 'Cancelled']

orders = pd.DataFrame({
    'order_id'      : range(1001, 1001 + n),
    'order_date'    : pd.date_range(start='2024-06-01', periods=n, freq='6h'),
    'supplier'      : np.random.choice(suppliers,  n, p=[0.25, 0.15, 0.25, 0.20, 0.15]),
    'category'      : np.random.choice(categories, n),
    'quantity'      : np.random.randint(10, 500, n),
    'unit_price'    : np.random.uniform(50, 2000, n).round(2),
    'promised_days' : np.random.randint(3, 10, n),
    'actual_days'   : np.random.randint(2, 14, n),
    'defects'       : np.random.randint(0, 20, n),
    'status'        : np.random.choice(statuses, n, p=[0.80, 0.15, 0.05]),
    'warehouse'     : np.random.choice(['Mumbai', 'Delhi', 'Hyderabad', 'Chennai'], n),
})

orders['revenue'] = (orders['quantity'] * orders['unit_price']).round(2)
orders['on_time'] = (orders['actual_days'] <= orders['promised_days']).astype(int)

orders.to_csv('data/orders.csv', index=False)

# ── TABLE 2: INVENTORY ───────────────────────────────────────────────────────
products = [f'SKU-{i:03d}' for i in range(1, 31)]

inventory = pd.DataFrame({
    'product_id'     : products,
    'category'       : np.random.choice(categories, 30),
    'supplier'       : np.random.choice(suppliers,  30),
    'current_stock'  : np.random.randint(20, 600, 30),
    'reorder_point'  : np.random.randint(50, 200, 30),
    'max_capacity'   : np.random.randint(400, 1000, 30),
    'monthly_demand' : np.random.randint(100, 400, 30),
    'warehouse'      : np.random.choice(['Mumbai', 'Delhi', 'Hyderabad', 'Chennai'], 30),
    'unit_cost'      : np.random.uniform(30, 1500, 30).round(2),
})

inventory['days_of_stock'] = (
    inventory['current_stock'] / inventory['monthly_demand'] * 30
).round(1)

inventory['stockout_risk'] = inventory['days_of_stock'].apply(
    lambda x: 'High' if x < 10 else ('Medium' if x < 20 else 'Low')
)

inventory['turnover_ratio'] = (
    inventory['monthly_demand'] / inventory['current_stock']
).round(2)

inventory.to_csv('data/inventory.csv', index=False)

# ── TABLE 3: SUPPLIERS ───────────────────────────────────────────────────────
supplier_master = pd.DataFrame({
    'supplier'       : suppliers,
    'country'        : ['India', 'China', 'India', 'Vietnam', 'India'],
    'contract_value' : [5000000, 3200000, 4500000, 2800000, 3900000],
    'rating'         : [4.5, 3.1, 4.2, 3.8, 4.7],
    'since_year'     : [2015, 2019, 2017, 2020, 2016],
    'payment_terms'  : ['Net 30', 'Net 45', 'Net 30', 'Net 60', 'Net 30'],
    'category_focus' : ['Electronics', 'Apparel', 'Packaging', 'Raw Materials', 'Finished Goods'],
})

supplier_master.to_csv('data/suppliers.csv', index=False)

# ── PREVIEW ──────────────────────────────────────────────────────────────────
print("=" * 55)
print("  DATASET CREATED SUCCESSFULLY")
print("=" * 55)
print(f"\n orders.csv    → {len(orders)} rows × {len(orders.columns)} columns")
print(f" inventory.csv → {len(inventory)} rows × {len(inventory.columns)} columns")
print(f" suppliers.csv → {len(supplier_master)} rows × {len(supplier_master.columns)} columns")
print(f"\n Date range    : {orders['order_date'].min().date()} → {orders['order_date'].max().date()}")
print(f" Total revenue : ₹{orders['revenue'].sum():,.0f}")
print(f" Delivered     : {(orders['status']=='Delivered').sum()} orders")
print(f" High stockout : {(inventory['stockout_risk']=='High').sum()} products")
print("=" * 55)
print("  Files saved to data/ folder. Ready for Step 2.")
print("=" * 55)