import pandas as pd
import json
import time
import requests
import re
import os
import csv

df = pd.read_csv("data/carmax_USA.csv")
df_llm = pd.read_csv("data/carmax_specifications.csv")

df['year'] = df['year'].astype(str)
df_llm['year'] = df_llm['year'].astype(str)


df_enriched = pd.merge(df,df_llm,
                       how = "inner",
                       left_on = ["year","make","model","trim"],
                       right_on = ["year","make","model","trim"]
                       )


df_enriched.to_csv(
    "data/carmax_usa_enriched.csv",
    mode = "w",
    header = True
)