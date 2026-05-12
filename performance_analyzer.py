import pandas as pd

# Load dataset
df = pd.read_csv("data/catch_ball_dataset.csv")

# Basic stats
avg_reaction = df["reaction_time_ms"].mean()
avg_accuracy = df["accuracy"].mean()

fast_players = len(df[df["performance_label"] == "Fast"])
slow_players = len(df[df["performance_label"] == "Slow"])

print("===== AI PERFORMANCE ANALYSIS =====")
print(f"Average Reaction Time: {avg_reaction:.2f} ms")
print(f"Average Accuracy: {avg_accuracy:.2f}%")
print(f"Fast Sessions: {fast_players}")
print(f"Slow Sessions: {slow_players}")