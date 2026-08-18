import pandas as pd

##Data Filteration. happening over here.



# Read the original deliveries dataset
df = pd.read_csv("data/deliveries.csv")

# Read the already trimmed matches dataset
matches = pd.read_csv("data/matches_2020_2024.csv")

# Get match IDs from 2020-2024
match_ids = matches["id"].tolist()

# Keep only deliveries from 2020-2024 matches
df = df[df["match_id"].isin(match_ids)]

# Save the trimmed deliveries dataset
df.to_csv("data/deliveries_2020_2024.csv", index=False)

# Verify the result
print("Delivery rows:", len(df))