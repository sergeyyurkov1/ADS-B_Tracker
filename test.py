import pandas as pd

df = pd.read_csv(
    "D:\My_Projects\Datasets\states\states.csv", nrows=1000000, header=None
)

print(df.sample(500))

print(df.columns)
