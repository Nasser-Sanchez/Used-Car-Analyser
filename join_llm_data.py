import pandas as pd
import json
import time
import requests
import re
import os
import csv

df = pd.read_csv("carmax_USA.csv")
df_llm = pd.read_csv("carmax_specifications.csv")

df['year'] = df['year'].astype(str)
df_llm['year'] = df_llm['year'].astype(str)


df_enriched = pd.merge(df,df_llm,
                       how = "left",
                       left_on = ["year","make","model","trim"],
                       right_on = ["year","make","model","trim"]
                       )

df_llm.to_csv("test_join.csv",mode="w",header=True)

df_enriched.to_csv(
    "carmax_usa_enriched.csv",
    mode = "w",
    header = True
)