"""High-signal synthetic dataset used for reliable capstone demonstrations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_retail_demo_dataset(seed: int = 42) -> pd.DataFrame:
    """Build two years of retail performance with explainable business signals."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-07", "2025-12-28", freq="W")
    regions = {
        "North": 1.12,
        "South": 0.92,
        "East": 1.04,
        "West": 0.98,
    }
    products = {
        "Electronics": (155.0, 0.69),
        "Home": (82.0, 0.61),
        "Apparel": (54.0, 0.55),
        "Sports": (71.0, 0.58),
    }
    rows = []

    for week_index, date in enumerate(dates):
        annual_seasonality = 1 + 0.14 * np.sin(2 * np.pi * week_index / 52)
        holiday_lift = 1.32 if date.month in (11, 12) else 1.0
        trend = 1 + 0.0028 * week_index

        for region, region_factor in regions.items():
            for product, (price, cost_ratio) in products.items():
                product_factor = {
                    "Electronics": 1.18,
                    "Home": 0.94,
                    "Apparel": 1.06,
                    "Sports": 0.88,
                }[product]
                demand = (
                    74
                    * trend
                    * annual_seasonality
                    * holiday_lift
                    * region_factor
                    * product_factor
                    * rng.normal(1, 0.07)
                )

                # Explainable demo events.
                if region == "East" and product == "Electronics" and date.month == 11:
                    demand *= 1.38  # successful holiday campaign
                if (
                    region == "West"
                    and product == "Electronics"
                    and pd.Timestamp("2025-04-01") <= date <= pd.Timestamp("2025-05-31")
                ):
                    demand *= 0.58  # supply disruption

                units = max(8, int(round(demand)))
                discount_rate = float(np.clip(rng.normal(0.075, 0.025), 0.01, 0.18))
                gross_revenue = units * price
                revenue = gross_revenue * (1 - discount_rate)
                marketing_spend = revenue * rng.uniform(0.055, 0.095)
                return_rate = rng.uniform(0.025, 0.065)
                if region == "South" and product == "Apparel":
                    return_rate += 0.055  # persistent sizing/quality issue
                returns = int(round(units * return_rate))
                net_revenue = revenue * (1 - return_rate)
                cogs = gross_revenue * cost_ratio
                profit = net_revenue - cogs - marketing_spend
                target_revenue = 74 * price * trend * region_factor * product_factor * 0.96
                satisfaction = float(
                    np.clip(4.55 - return_rate * 5 + rng.normal(0, 0.09), 3.2, 4.9)
                )

                rows.append(
                    {
                        "Parsed_Date": date,
                        "Region": region,
                        "Product": product,
                        "Units_Sold": units,
                        "Revenue": round(net_revenue, 2),
                        "Revenue_Target": round(target_revenue, 2),
                        "Marketing_Spend": round(marketing_spend, 2),
                        "Returns": returns,
                        "Return_Rate": round(return_rate, 4),
                        "COGS": round(cogs, 2),
                        "Profit": round(profit, 2),
                        "Profit_Margin": round(profit / max(net_revenue, 1), 4),
                        "Customer_Satisfaction": round(satisfaction, 2),
                        "Target_Achieved": "Yes" if net_revenue >= target_revenue else "No",
                    }
                )

    return pd.DataFrame(rows).sort_values(["Parsed_Date", "Region", "Product"]).reset_index(drop=True)
