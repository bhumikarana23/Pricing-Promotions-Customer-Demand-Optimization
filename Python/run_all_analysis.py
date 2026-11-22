from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Expected structure:
# Project/
#   Dataset/  (seven CSV files)
#   Python/  (this script)
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "Dataset"
OUT = Path(__file__).resolve().parent / "outputs"
CLEAN = Path(__file__).resolve().parent / "cleaned_data"
OUT.mkdir(exist_ok=True)
CLEAN.mkdir(exist_ok=True)

print("STAGE 1: LOAD AND INSPECT DATA")
files = ["customers", "products", "orders", "order_items",
         "promotions", "sessions", "inventory"]
date_cols = {
    "customers": ["signup_date"], "products": ["launch_date"],
    "orders": ["order_date"], "promotions": ["start_date", "end_date"],
    "sessions": ["session_date"], "inventory": ["snapshot_month"]
}
data = {}
summary = []
for name in files:
    df = pd.read_csv(DATA / f"{name}.csv")
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace("-", "_", regex=False)
        )
    for col in date_cols.get(name, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    data[name] = df
    summary.append([name, len(df), len(df.columns), int(df.duplicated().sum()),
                    int(df.isna().sum().sum())])
    print(f"{name}: {df.shape}; duplicates={df.duplicated().sum()}; missing={df.isna().sum().sum()}")
pd.DataFrame(summary, columns=["dataset","rows","columns","duplicate_rows","missing_cells"]).to_csv(
    OUT / "01_dataset_summary.csv", index=False)

print("\nSTAGE 2: CLEAN DATA")
for name, df in data.items():
    df = df.drop_duplicates().copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    df.to_csv(CLEAN / f"{name}.csv", index=False)
    data[name] = df
print("Cleaned CSV files saved.")

customers = data["customers"]
products = data["products"]
orders = data["orders"]
items = data["order_items"]
promos = data["promotions"]
sessions = data["sessions"]
inventory = data["inventory"]

# Use delivered orders as completed purchases. Keep cancelled/returned records out of sales KPIs.
delivered_orders = orders[orders["order_status"].eq("Delivered")].copy()
item_sales = items.merge(
    delivered_orders[["order_id","customer_id","order_date","promotion_id","device"]],
    on="order_id", how="inner"
).merge(products[["product_id","brand","category","sub_category","list_price","unit_cost"]],
        on="product_id", how="left")
item_sales["discount_pct"] = item_sales["discount_rate"] * 100
item_sales["gross_margin_pct"] = (
    item_sales["gross_profit"] / item_sales["net_revenue"].replace(0, np.nan) * 100
)

print("\nSTAGE 3: PRICING ANALYSIS")
item_sales["discount_band"] = pd.cut(
    item_sales["discount_pct"], [-0.01,5,10,20,30,40,100],
    labels=["0-5%","5-10%","10-20%","20-30%","30-40%","40%+"],
    include_lowest=True
)
discount_analysis = item_sales.groupby("discount_band", observed=False).agg(
    units=("quantity","sum"), gross_revenue=("gross_revenue","sum"),
    discount_amount=("discount_amount","sum"), net_revenue=("net_revenue","sum"),
    gross_profit=("gross_profit","sum"), avg_discount_pct=("discount_pct","mean")
).reset_index()
discount_analysis["gross_margin_pct"] = (
    discount_analysis["gross_profit"] / discount_analysis["net_revenue"].replace(0,np.nan) * 100
)
discount_analysis.to_csv(OUT / "03_discount_band_analysis.csv", index=False)

category_analysis = item_sales.groupby("category").agg(
    orders=("order_id","nunique"), units=("quantity","sum"),
    net_revenue=("net_revenue","sum"), gross_profit=("gross_profit","sum"),
    avg_discount_pct=("discount_pct","mean")
).reset_index()
category_analysis["gross_margin_pct"] = (
    category_analysis["gross_profit"] / category_analysis["net_revenue"].replace(0,np.nan) * 100
)
category_analysis.to_csv(OUT / "03_category_pricing_analysis.csv", index=False)

plt.figure(figsize=(9,5))
plt.bar(discount_analysis["discount_band"].astype(str), discount_analysis["net_revenue"])
plt.title("Net Revenue by Discount Band"); plt.xlabel("Discount band"); plt.ylabel("Net revenue")
plt.tight_layout(); plt.savefig(OUT / "03_revenue_by_discount_band.png", dpi=160); plt.close()

plt.figure(figsize=(10,5))
plt.bar(category_analysis["category"], category_analysis["gross_margin_pct"])
plt.title("Gross Margin by Category"); plt.xticks(rotation=35, ha="right")
plt.ylabel("Gross margin (%)"); plt.tight_layout()
plt.savefig(OUT / "03_margin_by_category.png", dpi=160); plt.close()
print("Pricing analysis saved.")

print("\nSTAGE 4: PROMOTION ANALYSIS")
order_totals = items.groupby("order_id", as_index=False).agg(
    gross_revenue=("gross_revenue","sum"), discount_amount=("discount_amount","sum"),
    net_revenue=("net_revenue","sum"), total_cost=("total_cost","sum"),
    gross_profit=("gross_profit","sum"), units=("quantity","sum"))
promo_orders = delivered_orders.merge(order_totals, on="order_id", how="left")
promo_perf = promo_orders.groupby("promotion_id", as_index=False).agg(
    delivered_orders=("order_id","nunique"), net_revenue=("net_revenue","sum"),
    discount_amount=("discount_amount","sum"), gross_profit=("gross_profit","sum"),
    units=("units","sum"))
promo_perf = promo_perf.merge(promos, on="promotion_id", how="left")
promo_perf["gross_margin_pct"] = promo_perf["gross_profit"] / promo_perf["net_revenue"].replace(0,np.nan) * 100
promo_perf["marketing_spend"] = promo_perf["marketing_spend"].fillna(0)
promo_perf["profit_after_marketing_spend_proxy"] = promo_perf["gross_profit"] - promo_perf["marketing_spend"]
promo_perf.to_csv(OUT / "04_promotion_performance.csv", index=False)

promo_type = promo_perf.groupby("promotion_type", dropna=False).agg(
    promotions=("promotion_id","nunique"), orders=("delivered_orders","sum"),
    net_revenue=("net_revenue","sum"), gross_profit=("gross_profit","sum"),
    discount_amount=("discount_amount","sum"), marketing_spend=("marketing_spend","sum")
).reset_index()
promo_type["gross_margin_pct"] = promo_type["gross_profit"] / promo_type["net_revenue"].replace(0,np.nan) * 100
promo_type.to_csv(OUT / "04_promotion_type_analysis.csv", index=False)
print("Promotion analysis saved. Promotion comparisons are descriptive, not causal.")

print("\nSTAGE 5: CUSTOMER RFM SEGMENTATION")
order_value = items.groupby("order_id", as_index=False)["net_revenue"].sum()
customer_orders = delivered_orders.merge(order_value, on="order_id", how="left")
reference_date = customer_orders["order_date"].max() + pd.Timedelta(days=1)
rfm = customer_orders.groupby("customer_id").agg(
    recency_days=("order_date", lambda x: (reference_date - x.max()).days),
    frequency=("order_id","nunique"), monetary=("net_revenue","sum")
).reset_index()
rfm["R_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), 4, labels=[4,3,2,1]).astype(int)
rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
def label_segment(r):
    if r.R_score >= 3 and r.F_score >= 3 and r.M_score >= 3: return "Champions"
    if r.R_score >= 3 and r.F_score >= 2: return "Loyal / Active"
    if r.R_score >= 3 and r.F_score == 1: return "Recent Customers"
    if r.R_score <= 2 and r.F_score >= 3: return "At Risk - Previously Frequent"
    if r.R_score == 1: return "Inactive / Lost"
    return "Potential / Developing"
rfm["customer_segment"] = rfm.apply(label_segment, axis=1)
rfm = rfm.merge(customers[["customer_id","gender","city_tier","acquisition_channel"]], on="customer_id", how="left")
rfm.to_csv(OUT / "05_customer_rfm_segments.csv", index=False)
rfm_summary = rfm.groupby("customer_segment").agg(
    customers=("customer_id","nunique"), avg_recency_days=("recency_days","mean"),
    avg_orders=("frequency","mean"), avg_customer_revenue=("monetary","mean"),
    total_revenue=("monetary","sum")).reset_index()
rfm_summary.to_csv(OUT / "05_rfm_segment_summary.csv", index=False)
print("RFM segmentation saved.")

print("\nSTAGE 6: COHORT RETENTION")
cohort_orders = delivered_orders[["customer_id","order_date"]].copy()
cohort_orders["order_month"] = cohort_orders["order_date"].dt.to_period("M")
cohort_first = cohort_orders.groupby("customer_id")["order_month"].min().rename("cohort_month")
cohort_orders = cohort_orders.join(cohort_first, on="customer_id")
cohort_orders["cohort_index"] = (
    (cohort_orders["order_month"].dt.year - cohort_orders["cohort_month"].dt.year)*12
    + cohort_orders["order_month"].dt.month - cohort_orders["cohort_month"].dt.month)
cohort_counts = cohort_orders.groupby(["cohort_month","cohort_index"])["customer_id"].nunique().unstack()
retention = cohort_counts.divide(cohort_counts.iloc[:,0], axis=0)
cohort_counts.to_csv(OUT / "06_cohort_customer_counts.csv")
retention.to_csv(OUT / "06_cohort_retention_rates.csv")
plt.figure(figsize=(12,7))
sns.heatmap(retention, cmap="YlGnBu", annot=True, fmt=".0%", vmin=0, vmax=1)
plt.title("Customer Cohort Retention"); plt.xlabel("Months Since First Purchase")
plt.ylabel("First Purchase Cohort"); plt.tight_layout()
plt.savefig(OUT / "06_cohort_retention_heatmap.png", dpi=160); plt.close()
print("Cohort analysis saved.")

print("\nSTAGE 7: CATEGORY DEMAND FORECASTING")
forecast_source = (delivered_orders[["order_id","order_date"]]
    .merge(items[["order_id","product_id","quantity"]], on="order_id")
    .merge(products[["product_id","category"]], on="product_id"))
forecast_source["month"] = forecast_source["order_date"].dt.to_period("M").dt.to_timestamp()
monthly = forecast_source.groupby(["month","category"], as_index=False)["quantity"].sum()
monthly.to_csv(OUT / "07_monthly_category_demand.csv", index=False)
forecast_rows = []
for category, group in monthly.groupby("category"):
    series = group.sort_values("month").set_index("month")["quantity"].asfreq("MS", fill_value=0)
    if len(series) < 6: continue
    test_n = min(3, max(1, len(series)//4))
    train, test = series.iloc[:-test_n], series.iloc[-test_n:]
    test_pred = np.repeat(train.iloc[-1], len(test))
    mae = mean_absolute_error(test, test_pred)
    rmse = np.sqrt(mean_squared_error(test, test_pred))
    next_months = pd.date_range(series.index.max() + pd.offsets.MonthBegin(1), periods=3, freq="MS")
    baseline = series.tail(3).mean()
    for month in next_months:
        forecast_rows.append([category, month, round(float(baseline),2), round(float(mae),2), round(float(rmse),2)])
forecast = pd.DataFrame(forecast_rows, columns=["category","forecast_month","forecast_units","holdout_mae","holdout_rmse"])
forecast.to_csv(OUT / "07_category_demand_forecast.csv", index=False)
print("Forecast saved. This is a simple baseline, not a production model.")

print("\nSTAGE 8: BUSINESS RECOMMENDATIONS")
report = [
    "# Business Recommendations",
    "",
    "This project uses synthetic practice data, not actual Myntra data.",
    "Promotion results are descriptive associations and do not establish causal lift.",
    ""
]
if not discount_analysis.empty:
    best = discount_analysis.dropna(subset=["gross_margin_pct"]).sort_values("gross_margin_pct", ascending=False).iloc[0]
    report += [f"- Highest observed gross-margin discount band: **{best['discount_band']}** ({best['gross_margin_pct']:.1f}%).",
               "- Review revenue and units alongside margin before recommending discount depth."]
if not category_analysis.empty:
    best_cat = category_analysis.sort_values("net_revenue", ascending=False).iloc[0]
    report.append(f"- Highest net-revenue category in the sample: **{best_cat['category']}**.")
if not promo_type.empty:
    best_promo = promo_type.sort_values("gross_profit", ascending=False).iloc[0]
    report.append(f"- Highest aggregate gross-profit promotion type: **{best_promo['promotion_type']}**.")
    report.append("- Test promotional lift using a holdout/control group before claiming incremental impact.")
if not rfm_summary.empty:
    at_risk = rfm_summary[rfm_summary["customer_segment"].str.contains("At Risk|Inactive", na=False)]
    if not at_risk.empty:
        report.append(f"- Customers classified as at-risk/inactive by the RFM rules: {int(at_risk['customers'].sum()):,}.")
        report.append("- Consider a controlled win-back test and measure incremental repeat purchases.")
report += ["", "## Forecasting", "- Treat forecast values as planning baselines; improve with seasonality, promotions, price and stock features."]
(OUT / "08_business_recommendations.md").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))

print(f"\nDONE. Cleaned files: {CLEAN}")
print(f"Analysis outputs: {OUT}")
