
import pandas as pd
import numpy as np
import time
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

start_time = time.perf_counter()

input_file = "output/hospital_cleaned/part-m-00000"
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

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

df["lag_1"] = df.groupby("hospital_pk")["occupied_beds"].shift(1)
df["lag_2"] = df.groupby("hospital_pk")["occupied_beds"].shift(2)

df["rolling_mean_4"] = (
    df.groupby("hospital_pk")["occupied_beds"]
    .transform(lambda x: x.shift(1).rolling(4, min_periods=2).mean())
)

df = df.dropna(
    subset=["lag_1", "lag_2", "rolling_mean_4"]
).copy()

features = ["total_beds", "lag_1", "lag_2", "rolling_mean_4"]
target = "occupied_beds"

weeks = sorted(df["collection_week"].unique())
split_week = weeks[-8]

train = df[df["collection_week"] < split_week]
test = df[df["collection_week"] >= split_week]

evaluation_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

evaluation_model.fit(train[features], train[target])

predictions = evaluation_model.predict(test[features])
baseline_predictions = test["lag_1"].to_numpy()

mae = mean_absolute_error(test[target], predictions)
rmse = np.sqrt(mean_squared_error(test[target], predictions))

baseline_mae = mean_absolute_error(
    test[target], baseline_predictions
)
baseline_rmse = np.sqrt(
    mean_squared_error(test[target], baseline_predictions)
)

print("HOLDOUT MODEL EVALUATION")
print("------------------------")
print("Training records:", len(train))
print("Testing records:", len(test))
print("Training cutoff:", split_week)
print("Random Forest MAE:", round(mae, 3))
print("Random Forest RMSE:", round(rmse, 3))
print("Previous-week baseline MAE:", round(baseline_mae, 3))
print("Previous-week baseline RMSE:", round(baseline_rmse, 3))

final_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

final_model.fit(df[features], df[target])

importance = pd.DataFrame({
    "feature": features,
    "importance": final_model.feature_importances_
}).sort_values("importance", ascending=False)

importance.to_csv(
    output_dir / "feature_importance.csv",
    index=False
)

latest = df.groupby("hospital_pk", as_index=False).tail(1).copy()

latest["last_reporting_week"] = latest["collection_week"]

latest["forecast_occupied_beds"] = final_model.predict(
    latest[features]
).clip(min=0)

latest["recommended_beds"] = np.ceil(
    latest["forecast_occupied_beds"] * 1.10
)

latest["recommended_beds"] = np.minimum(
    latest["recommended_beds"],
    latest["total_beds"]
)

latest["unmet_demand"] = np.maximum(
    latest["forecast_occupied_beds"] - latest["recommended_beds"],
    0
)

latest["forecast_week"] = (
    latest["last_reporting_week"] + pd.Timedelta(days=7)
)

forecast_columns = [
    "hospital_pk",
    "hospital_name",
    "state",
    "last_reporting_week",
    "forecast_week",
    "total_beds",
    "forecast_occupied_beds",
    "recommended_beds",
    "unmet_demand"
]

latest[forecast_columns].to_csv(
    output_dir / "hospital_forecast.csv",
    index=False
)

elapsed = time.perf_counter() - start_time

pd.DataFrame([{
    "MAE": mae,
    "RMSE": rmse,
    "Baseline_MAE": baseline_mae,
    "Baseline_RMSE": baseline_rmse,
    "Execution_Time_Seconds": elapsed
}]).to_csv(
    output_dir / "model_metrics.csv",
    index=False
)

print("\nFINAL FORECAST")
print("--------------")
print("Final model trained on all records:", len(df))
print("Forecast hospitals:", len(latest))
print("Execution time:", round(elapsed, 2), "seconds")
print("Forecast saved to output/hospital_forecast.csv")
print("Feature importance saved to output/feature_importance.csv")
print("Metrics saved to output/model_metrics.csv")
