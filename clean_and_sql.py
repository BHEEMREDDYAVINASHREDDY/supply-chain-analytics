import pandas as pd
import sqlite3
import os

os.makedirs('outputs', exist_ok=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
orders    = pd.read_csv('data/orders.csv',    parse_dates=['order_date'])
inventory = pd.read_csv('data/inventory.csv')
suppliers = pd.read_csv('data/suppliers.csv')

# ── CLEAN ORDERS ──────────────────────────────────────────────────────────────
orders = orders.drop_duplicates(subset='order_id')
orders = orders[orders['quantity'] > 0]
orders = orders[orders['unit_price'] > 0]
orders['month']      = orders['order_date'].dt.to_period('M').astype(str)
orders['month_name'] = orders['order_date'].dt.strftime('%b %Y')
orders['year']       = orders['order_date'].dt.year
orders['quarter']    = orders['order_date'].dt.quarter.apply(lambda x: f'Q{x}')

# ── CLEAN INVENTORY ───────────────────────────────────────────────────────────
inventory = inventory.drop_duplicates(subset='product_id')
inventory['below_reorder'] = (
    inventory['current_stock'] < inventory['reorder_point']
).astype(int)
inventory['fill_rate_pct'] = (
    inventory['current_stock'] / inventory['max_capacity'] * 100
).round(1)

# ── SAVE CLEANED FILES ────────────────────────────────────────────────────────
orders.to_csv('data/orders_clean.csv',       index=False)
inventory.to_csv('data/inventory_clean.csv', index=False)

# ── SQL ANALYSIS ──────────────────────────────────────────────────────────────
conn = sqlite3.connect(':memory:')
orders.to_sql('orders',       conn, index=False, if_exists='replace')
inventory.to_sql('inventory', conn, index=False, if_exists='replace')
suppliers.to_sql('suppliers', conn, index=False, if_exists='replace')

# SQL 1 — Revenue and performance by supplier
sql_supplier = pd.read_sql("""
    SELECT
        supplier,
        COUNT(order_id)                    AS total_orders,
        ROUND(SUM(revenue), 0)             AS total_revenue,
        ROUND(AVG(actual_days), 2)         AS avg_lead_time,
        ROUND(AVG(on_time) * 100, 1)       AS otd_pct,
        ROUND(AVG(defects), 2)             AS avg_defects,
        ROUND(SUM(quantity), 0)            AS total_units
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY supplier
    ORDER BY total_revenue DESC
""", conn)

# SQL 2 — Monthly revenue trend
sql_monthly = pd.read_sql("""
    SELECT
        month,
        month_name,
        COUNT(order_id)              AS total_orders,
        ROUND(SUM(revenue), 0)       AS monthly_revenue,
        ROUND(SUM(quantity), 0)      AS total_units,
        ROUND(AVG(on_time)*100, 1)   AS otd_pct
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY month
    ORDER BY month
""", conn)

# SQL 3 — Category performance
sql_category = pd.read_sql("""
    SELECT
        category,
        COUNT(order_id)              AS total_orders,
        ROUND(SUM(revenue), 0)       AS total_revenue,
        ROUND(AVG(actual_days), 2)   AS avg_lead_time,
        ROUND(AVG(on_time)*100, 1)   AS otd_pct
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY category
    ORDER BY total_revenue DESC
""", conn)

# SQL 4 — Products at stockout risk
sql_stockout = pd.read_sql("""
    SELECT
        product_id, category, supplier, warehouse,
        current_stock, reorder_point,
        days_of_stock, stockout_risk
    FROM inventory
    WHERE current_stock < reorder_point
    ORDER BY days_of_stock ASC
""", conn)

# SQL 5 — Warehouse performance
sql_warehouse = pd.read_sql("""
    SELECT
        warehouse,
        COUNT(order_id)             AS total_orders,
        ROUND(SUM(revenue), 0)      AS total_revenue,
        ROUND(AVG(on_time)*100, 1)  AS otd_pct,
        ROUND(AVG(actual_days), 2)  AS avg_lead_time
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY warehouse
    ORDER BY total_revenue DESC
""", conn)

conn.close()

# ── SAVE SQL RESULTS ──────────────────────────────────────────────────────────
sql_supplier.to_csv('data/sql_supplier.csv',   index=False)
sql_monthly.to_csv('data/sql_monthly.csv',     index=False)
sql_category.to_csv('data/sql_category.csv',   index=False)
sql_stockout.to_csv('data/sql_stockout.csv',   index=False)
sql_warehouse.to_csv('data/sql_warehouse.csv', index=False)

# ── PRINT RESULTS ─────────────────────────────────────────────────────────────
print("=" * 60)
print("  STEP 2 — DATA CLEANING + SQL ANALYSIS COMPLETE")
print("=" * 60)

print("\n── Supplier Revenue Table ──────────────────────────────────")
print(sql_supplier.to_string(index=False))

print("\n── Monthly Revenue (last 6 months) ─────────────────────────")
print(sql_monthly.tail(6).to_string(index=False))

print("\n── Category Performance ────────────────────────────────────")
print(sql_category.to_string(index=False))

print("\n── Products Below Reorder Point (Stockout Risk) ────────────")
if len(sql_stockout) == 0:
    print("  All products are above reorder point.")
else:
    print(sql_stockout.to_string(index=False))

print("\n── Warehouse Performance ───────────────────────────────────")
print(sql_warehouse.to_string(index=False))

print("\n── Cleaned Data Summary ────────────────────────────────────")
print(f"  Total orders (after cleaning) : {len(orders)}")
print(f"  Delivered orders              : {(orders['status']=='Delivered').sum()}")
print(f"  Date range                    : {orders['order_date'].min().date()} → {orders['order_date'].max().date()}")
print(f"  Products below reorder point  : {len(sql_stockout)}")
print("=" * 60)
print("  SQL results saved to data/ folder. Ready for Step 3.")
print("=" * 60)