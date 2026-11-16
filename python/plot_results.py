
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

df = pd.read_csv("output/model_metrics.csv")
metrics = df.iloc[0]

names = ["Random Forest", "Previous-week Baseline"]
mae = [metrics["MAE"], metrics["Baseline_MAE"]]
rmse = [metrics["RMSE"], metrics["Baseline_RMSE"]]

fig, axes = plt.subplots(1, 2, figsize=(11, 5))

for ax, values, title in zip(
    axes,
    [mae, rmse],
    ["Mean Absolute Error (MAE)", "Root Mean Squared Error (RMSE)"]
):
    bars = ax.bar(names, values)
    ax.set_title(title)
    ax.set_ylabel("Error (beds)")
    ax.bar_label(bars, fmt="%.2f", padding=4)
    ax.set_ylim(0, max(values) * 1.25)
    ax.tick_params(axis="x", rotation=10)

fig.suptitle("Random Forest vs Previous-week Baseline")
plt.tight_layout()

Path("output/graphs").mkdir(parents=True, exist_ok=True)
plt.savefig("output/graphs/model_comparison.png", dpi=300)
plt.show()

print("Graph saved: output/graphs/model_comparison.png")

bed_df = pd.read_csv("output/bed_optimization_results.csv")

shortages = bed_df[bed_df["additional_beds_needed"] > 0]
top_10 = shortages.nlargest(10, "additional_beds_needed")
top_10 = top_10.sort_values("additional_beds_needed")

plt.figure(figsize=(11, 7))
bars = plt.barh(
    top_10["hospital_name"],
    top_10["additional_beds_needed"]
)

plt.xlabel("Additional beds needed")
plt.title("Top 10 Hospitals Requiring Additional Beds")
plt.bar_label(bars, fmt="%.1f", padding=4)
plt.tight_layout()

plt.savefig("output/graphs/top_10_bed_shortages.png", dpi=300)
plt.show()

print("Graph saved: output/graphs/top_10_bed_shortages.png")

fairness = pd.read_csv("output/state_fairness_audit.csv")

top_states = fairness.nlargest(10, "unmet_demand_percentage")
top_states = top_states.sort_values("unmet_demand_percentage")

plt.figure(figsize=(10, 6))

bars = plt.barh(
    top_states["state"],
    top_states["unmet_demand_percentage"]
)

plt.xlabel("Hospitals with unmet demand (%)")
plt.ylabel("State / Territory")
plt.title("Top 10 Jurisdictions by Hospital Unmet Demand")
plt.bar_label(bars, fmt="%.2f%%", padding=4)

plt.tight_layout()
plt.savefig("output/graphs/geographic_fairness.png", dpi=300)
plt.show()

print("Graph saved: output/graphs/geographic_fairness.png")
