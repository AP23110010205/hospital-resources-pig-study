
import pandas as pd
import numpy as np
from pathlib import Path
import time

start_time = time.perf_counter()

df = pd.read_csv("output/hospital_forecast.csv")
output_dir = Path("output")

safety_buffer = 1.10

df["target_beds"] = np.ceil(
    df["forecast_occupied_beds"] * safety_buffer
)

df["additional_beds_needed"] = np.maximum(
    df["target_beds"] - df["total_beds"], 0
)

df["spare_beds"] = np.maximum(
    df["total_beds"] - df["target_beds"], 0
)

df["capacity_status"] = np.select(
    [
        df["additional_beds_needed"] > 0,
        df["spare_beds"] > 0
    ],
    [
        "Capacity shortage",
        "Spare capacity"
    ],
    default="Capacity balanced"
)

columns = [
    "hospital_pk",
    "hospital_name",
    "state",
    "total_beds",
    "forecast_occupied_beds",
    "target_beds",
    "additional_beds_needed",
    "spare_beds",
    "capacity_status"
]

df[columns].to_csv(
    output_dir / "bed_optimization_results.csv",
    index=False
)

state_summary = df.groupby("state").agg(
    hospitals=("hospital_pk", "nunique"),
    total_beds=("total_beds", "sum"),
    forecast_demand=("forecast_occupied_beds", "sum"),
    additional_beds_needed=("additional_beds_needed", "sum"),
    spare_beds=("spare_beds", "sum")
).reset_index()

state_summary.to_csv(
    output_dir / "bed_optimization_state_summary.csv",
    index=False
)

print("BED CAPACITY PLANNING RESULTS")
print("--------------------------------")
print("Hospitals analysed:", len(df))
print("Hospitals needing additional beds:",
      (df["additional_beds_needed"] > 0).sum())
print("Hospitals with spare capacity:",
      (df["spare_beds"] > 0).sum())
print("Total additional beds needed:",
      int(df["additional_beds_needed"].sum()))
print("Total spare beds:",
      int(df["spare_beds"].sum()))
print("Execution time:",
      round(time.perf_counter() - start_time, 2), "seconds")

print("\nTop 10 hospitals needing additional beds:")
print(
    df[df["additional_beds_needed"] > 0]
    .sort_values("additional_beds_needed", ascending=False)
    [["hospital_name", "state", "total_beds",
      "forecast_occupied_beds", "additional_beds_needed"]]
    .head(10).to_string(index=False)
)

print("\nSaved optimisation results successfully.")
