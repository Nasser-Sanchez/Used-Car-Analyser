import lmstudio as lms
from google.cloud import bigquery
import pandas as pd
import json
import time
import requests
import re
import os
import csv
import numpy as np
from pydantic import BaseModel, Field

output_csv = "carmax_specifications.csv"
error_csv = "carmax_errors.csv"

telemetry_csv = "carmax_telemetry.csv"

# Define columns explicitly to avoid undefined variable errors
columns = [
    'year', 'make', 'model', 'trim',
    'horsepower', 'torque', 'displacement', 'cylinders',
    'top_speed','accel', 'qmile_time', 'qmile_speed',
    'weight', 'fuel_type', 'fuel_economy',
    'quality_rating', 'reliability_rating'
]

telemetry_columns=[
    'model_name', 'model_parameters', 'input_tokens', 'output_tokens', 
    #'json_output_tokens', 'non_json_output_tokens', 
    'time_to_first_token_secs',
    'tokens_per_second'
]

# Create files if they don't exist
if not os.path.exists(output_csv):
    print(f"Creating {output_csv}...")
    pd.DataFrame(columns=columns).to_csv(output_csv, index=False)

# Create Error File if it doesn't exist
if not os.path.exists(error_csv):
    print(f"Creating {error_csv}...")
    pd.DataFrame(columns=["car_name", "error_message"]).to_csv(error_csv, index=False)

if not os.path.exists(telemetry_csv):
    print(f"Creating {telemetry_csv}...")
    pd.DataFrame(columns=telemetry_columns).to_csv(telemetry_csv, index=False)


# read car data
print("Reading Carmax data...\n")

df_original = pd.read_csv("carmax_USA.csv")



df = df_original[['year', 'make', 'model', 'trim']]
df = df.drop_duplicates()

# LM Studio connection

class CarSpec(BaseModel):
    horsepower: int
    torque: int
    displacement: float
    cylinders: int
    top_speed: int
    accel: float = Field(description="0-60 mph acceleration in seconds")
    qmile_time: float = Field(description="Quarter mile time in seconds")
    qmile_speed: int = Field(description="Quarter mile trap speed in mph")
    weight: int = Field(description="Weight in kg")    
    fuel_type: str
    fuel_economy: int
    quality_rating: int
    reliability_rating: int

SERVER_API_HOST = "localhost:1234"
lms.configure_default_client(SERVER_API_HOST)

if lms.Client.is_valid_api_host(SERVER_API_HOST):
    print(f"An LM Studio API server instance is available at {SERVER_API_HOST}")
else:
    print("No LM Studio API server instance found at {SERVER_API_HOST}")

llm_model = lms.llm()


# check for already processed records
processed_data = set()
existing_data = pd.read_csv(output_csv)
processed_data=set(zip(
    existing_data['year'].astype(str),
    existing_data['make'].astype(str),
    existing_data['model'].astype(str),
    existing_data['trim'].astype(str)
))

print(f"Found {len(processed_data)} already processed records\n")

keys = pd.Series(
    zip(
        df['year'].astype(str),
        df['make'].astype(str),
        df['model'].astype(str),
        df['trim'].astype(str),
    ),
    index=df.index,
)
cars_to_process = df[~keys.isin(processed_data)]

cars_to_process.to_csv(
    "test.csv",
    mode="w",
    header=True,  # Only writes header if the file is new/empty
    index=False
)
print(cars_to_process)
print(f"Total unique combinations: {len(df)}")
print(f"Already processed: {len(processed_data)}")
print(f"Remaining to process: {len(cars_to_process)}")


# Step 3: Define LLM request functions

system_prompt = """You are a car specification assistant. Return ONLY JSON with the fields: horsepower, torque,
    engine displacement, cylinders acceleration (0-60mph), quarter mile time, quarter mile trap speed, weight, fuel_type,
    fuel economy, quality rating, reliability rating. Do not include explanations or any thought process in the JSON. Return only the JSON in format like this:
    {
        "horsepower": 469,
        "torque": 516,
        "displacement": 4.0,
        "cylinders": 8,
        "top_speed": 155,
        "accel": 4.4,
        "qmile_time": 12.8,
        "qmile_speed": 112,
        "weight": 2200,
        "fuel_type": "petrol",
        "fuel_economy": 20,
        "quality_rating": 92,
        "reliability_rating": 55
    }
    this is a 2020 Mercedes S560 as the example, replace values with the actual value"""


def create_llm_prompt(row):
    print(f"Creating prompt for {row['year']} {row['make']} {row['model']} {row['trim']}...\n\n\n")
    return f"""Provide specifications for the following vehicle:
Year: {row['year']}
Make: {row['make']}
Model: {row['model']}
Trim: {row['trim']}

Guidelines:
- Horsepower in imperial BHP, torque in lb-ft, displacement in litres.
- Acceleration (0-60mph) and quarter-mile time in seconds.
- Weight in kg.
- fuel types: electric, petrol, diesel, hybrid
- Quality score (1-100) with 1 being poor and 100 being perfect refined luxury (eg Rolls Royce, private jet), 
factor in material usage, sound deadening, build quality etc.
- Reliability score (1-100) with 1 being the most unreliable and 100 being able to reach 1m miles with very little maintenance.
For reference a 2020 Mercedes S560 has a quality rating of 92 and a reliability rating of 55, and a 2004 Toyota Prius has quality 40 and reliability 92.

"""
    return prompt

def send_llm_request(user_prompt):
    chat = lms.Chat(system_prompt)
    chat.add_user_message(user_prompt)

    response = llm_model.respond(
        chat,
        response_format = CarSpec
    )
    return response


def extract_json_block(text: str) -> str:
    #Find the last json object in the text
    end_idx = text.rfind("}")
    
    if end_idx == -1:
        return text.strip()  # No closing brace found
        
    # Search backwards from end_idx to find the matching opening brace
    # We use rfind, but we only search the portion of the string up to end_idx
    start_idx = text.rfind("{", 0, end_idx)
    
    if start_idx != -1:
        # Extract everything from the last '{' before the last '}'
        json_str = text[start_idx : end_idx + 1]
        return json_str.strip()
        
    return text.strip()
def parse_llm_response(raw_response, row_df):
    print("Parsing data...")
    content_str = raw_response.content if hasattr(raw_response, "content") else str(raw_response)

    cleaned_json_str = extract_json_block(content_str)
    print(cleaned_json_str)
    # parse llm response with pydantic using the provided format
    parsed_data = CarSpec.model_validate_json(cleaned_json_str)
    
    # Now .model_dump() and .model_dump_json() work as expected:
    data_dict = parsed_data.model_dump()
    
    combined_dict = {**row_df.to_dict(), **data_dict}
    combined_row_df = pd.DataFrame([combined_dict])
    print(combined_row_df)
    return combined_row_df


def append_to_csv(appending_row):
    print(f"Appending data to {output_csv}...")
    file_exists = os.path.exists(output_csv) and os.path.getsize(output_csv) > 0

    ordered_data=appending_row.reindex(columns=columns)
    ordered_data.to_csv(
    output_csv,
    mode="a",
    header=not file_exists,  # Only writes header if the file is new/empty
    index=False
)
    print(f"Operation Complete!\n\n\n")

    
def extract_llm_telemetry(response):
    file_exists = os.path.exists(telemetry_csv) and os.path.getsize(telemetry_csv) > 0
    
    row_data = {
        'model_name': response.model_info.display_name,
        'model_parameters': response.model_info.params_string,
        'input_tokens': int(response.stats.prompt_tokens_count),
        'output_tokens': int(response.stats.predicted_tokens_count),
        'time_to_first_token_secs': int(response.stats.time_to_first_token_sec),
        'tokens_per_second': int(response.stats.tokens_per_second)
    }
    
    # 2. Initialize the DataFrame with the row data
    df = pd.DataFrame([row_data], columns=telemetry_columns)

    print(f"Appending telemetry data to {telemetry_csv}...\n")
    print(df)
    df.to_csv(
        telemetry_csv,
        mode="a",
        header=not file_exists,  
        index=False
    )





for index, row in cars_to_process.iterrows():
    prompt=create_llm_prompt(row)
    response=send_llm_request(prompt)
    extract_llm_telemetry(response)
    parsed_data=parse_llm_response(response, row)
    append_to_csv(parsed_data)