
import pandas as pd
import numpy as np

df = pd.read_csv("output/hospital_forecast.csv")

df["last_reporting_week"] = pd.to_datetime(
    df["last_reporting_week"]
)

latest_reporting = df["last_reporting_week"].max()

df["reporting_age_days"] = (
    latest_reporting - df["last_reporting_week"]
).dt.days

df["has_unmet_demand"] = df["unmet_demand"] > 0

audit = df.groupby("state").agg(
    hospitals=("hospital_pk", "nunique"),
    total_forecast_demand=("forecast_occupied_beds", "sum"),
    total_recommended_beds=("recommended_beds", "sum"),
    total_unmet_demand=("unmet_demand", "sum"),
    hospitals_with_unmet_demand=("has_unmet_demand", "sum"),
    average_reporting_age_days=("reporting_age_days", "mean"),
    oldest_reporting_age_days=("reporting_age_days", "max")
).reset_index()

audit["unmet_demand_percentage"] = (
    audit["hospitals_with_unmet_demand"]
    / audit["hospitals"] * 100
)

audit["demand_coverage_percentage"] = np.where(
    audit["total_forecast_demand"] > 0,
    audit["total_recommended_beds"]
    / audit["total_forecast_demand"] * 100,
    np.nan
)

audit["stale_hospitals"] = df.groupby("state")[
    "reporting_age_days"
].apply(lambda x: (x > 14).sum()).values

audit["stale_hospital_percentage"] = (
    audit["stale_hospitals"] / audit["hospitals"] * 100
)

audit = audit.sort_values(
    "unmet_demand_percentage",
    ascending=False
)

audit.to_csv(
    "output/state_fairness_audit.csv",
    index=False
)

print("UPDATED STATE-WISE FAIRNESS AUDIT")
print("---------------------------------")
print("States/territories:", len(audit))
print("Total hospitals:", df["hospital_pk"].nunique())
print("Latest reporting date:", latest_reporting)
print(
    "Hospitals with reporting older than 14 days:",
    (df["reporting_age_days"] > 14).sum()
)
print(
    "Hospitals with unmet demand:",
    df["has_unmet_demand"].sum()
)

print("\nTop 10 jurisdictions by unmet-demand percentage:")

print(
    audit[
        [
            "state",
            "hospitals",
            "unmet_demand_percentage",
            "total_unmet_demand",
            "demand_coverage_percentage",
            "average_reporting_age_days",
            "stale_hospital_percentage"
        ]
    ].head(10).round(2).to_string(index=False)
)

print("\nSaved: output/state_fairness_audit.csv")
