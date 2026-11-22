# Python Analysis – Pricing, Promotions & Customer Demand Optimization

## Overview
This folder contains the Python-based analytical workflow developed to investigate pricing performance, promotional effectiveness, customer segmentation, retention, and product demand.

The analysis uses interconnected synthetic fashion e-commerce datasets.

## Analysis Workflow

### 1. Data Loading & Inspection
- Importing datasets
- Reviewing data structures
- Inspecting missing values and duplicates
- Standardizing column names

### 2. Data Cleaning
- Removing duplicate records where applicable
- Formatting text fields
- Converting date columns
- Exporting cleaned datasets

### 3. Pricing Analysis
- Discount band analysis
- Category-level revenue analysis
- Profitability analysis
- Pricing performance visualization

### 4. Promotion Analysis
- Campaign performance analysis
- Promotion type comparisons
- Revenue and discount evaluation

### 5. Customer Segmentation
- RFM analysis
- Customer value segmentation
- Customer behaviour evaluation

### 6. Cohort Analysis
- Customer acquisition cohorts
- Retention analysis
- Cohort retention heatmap

### 7. Demand Forecasting
- Category-level demand analysis
- Baseline forecasting
- Forecast evaluation using error metrics

### 8. Business Recommendations
- Pricing opportunities
- Promotional planning insights
- Customer retention opportunities
- Demand management recommendations

## Libraries Used
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn

## Project Files
- `run_all_analysis.py` – Main analytical script.
- `requirements.txt` – Required Python libraries.
- `cleaned_data/` – Processed datasets.
- `outputs/` – Generated reports, charts, and analytical results.

## Execution
Install dependencies:

```bash
py -m pip install -r requirements.txt
```

Run the analysis:

```bash
py run_all_analysis.py
```

## Objective
Use Python to transform raw e-commerce data into analytical outputs that support pricing decisions, customer understanding, promotional evaluation, and demand planning.

**Forecasting Note:** The forecasting component uses a simple baseline methodology for learning and exploratory analysis, not a production forecasting system.
