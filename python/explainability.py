
import pandas as pd
import numpy as np
from pathlib import Path

input_file = "output/hospital_cleaned/part-m-00000"
forecast_file = "output/hospital_forecast.csv"

columns = [
    "hospital_pk",
    "collection_week",
    "state",
    "hospital_name",
    "total_beds",
    "occupied_beds",
    "occupancy_rate"
]

df = pd.read_csv(input_file, sep="\t", names=columns)
df["collection_week"] = pd.to_datetime(df["collection_week"])

df = df.sort_values(["hospital_pk", "collection_week"])

latest = df.groupby("hospital_pk", as_index=False).tail(1).copy()

latest["previous_week_beds"] = latest["occupied_beds"]

latest["four_week_average"] = (
    df.groupby("hospital_pk")["occupied_beds"]
    .transform(lambda x: x.shift(0).rolling(4, min_periods=1).mean())
    .groupby(df["hospital_pk"])
    .transform("last")
)

forecast = pd.read_csv(forecast_file)

result = forecast.merge(
    latest[
        [
            "hospital_pk",
            "previous_week_beds",
            "four_week_average"
        ]
    ],
    on="hospital_pk",
    how="left"
)

result["demand_change"] = (
    result["forecast_occupied_beds"] - result["previous_week_beds"]
)

def explain(row):
    if row["demand_change"] > 0.5:
        trend = "increasing"
    elif row["demand_change"] < -0.5:
        trend = "decreasing"
    else:
        trend = "stable"

    return (
        f"Forecast demand is {trend}. "
        f"Previous occupancy was {row['previous_week_beds']:.1f} beds. "
        f"Recent four-observation average was "
        f"{row['four_week_average']:.1f} beds. "
        f"Predicted occupancy is "
        f"{row['forecast_occupied_beds']:.1f} beds."
    )

result["explanation"] = result.apply(explain, axis=1)

output_columns = [
    "hospital_pk",
    "hospital_name",
    "state",
    "forecast_week",
    "previous_week_beds",
    "four_week_average",
    "forecast_occupied_beds",
    "recommended_beds",
    "unmet_demand",
    "explanation"
]

result[output_columns].to_csv(
    "output/hospital_explanations.csv",
    index=False
)

print("HOSPITAL EXPLAINABILITY REPORT")
print("------------------------------")
print("Hospitals explained:", len(result))
print("\nSample explanations:")
print(
    result[
        ["hospital_name", "state", "explanation"]
    ].head(5).to_string(index=False)
)

print("\nSaved to output/hospital_explanations.csv")
