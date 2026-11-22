# Cleaned Data

## Overview
This folder contains the processed datasets used throughout the Pricing, Promotions & Customer Demand Optimization project.

The original datasets were inspected and prepared to improve consistency and usability across Excel, SQL, Python, and Power BI workflows.

## Data Preparation
The cleaning process includes:
- Inspection of dataset structure and column names
- Standardization of column naming conventions
- Removal of duplicate records where applicable
- Text formatting and whitespace handling
- Date-field conversion and standardization
- Preparation of datasets for further analysis

## Dataset Files
- `customers.csv`
- `products.csv`
- `orders.csv`
- `order_items.csv`
- `promotions.csv`
- `sessions.csv`
- `inventory.csv`

## Data Relationships
- Customer IDs connect customers with orders and sessions.
- Order IDs connect orders with order items.
- Product IDs connect products with order items and inventory.
- Promotion IDs connect promotions with orders.

## Purpose
Provide a consistent and analysis-ready data foundation for downstream business intelligence and analytical workflows.

**Note:** The datasets contain synthetic data created for this portfolio project.
