import hashlib
import pandas as pd
import json
import time
import requests
import re
import os
import csv

df = pd.read_csv("carmax_USA.csv")
df.to_csv('carmax_USA copy.csv', index=False)
# 2. Create a consistent string key (lowercase to avoid case-sensitivity issues)
df['car_key'] = (df['year'].astype(str) + '-' + 
                 df['make'].str.lower() + '-' + 
                 df['model'].str.lower() + '-' + 
                 df['trim'].str.lower())

# 3. Generate the numeric hash
# We convert the hex hash to a large integer
df['car_id'] = df['car_key'].apply(lambda x: int(hashlib.md5(x.encode()).hexdigest(), 16))

# 4. Save as a new file (so you don't lose the original)
df.to_csv('carmax_USA.csv', index=False)
print("Done! You now have a 'car_id' column in your CSV.")