import lmstudio as lms
from google.cloud import bigquery
import pandas as pd
import pandas as pd
import json
import time
import requests
import re

delay_seconds=2

client = bigquery.Client()

SERVER_API_HOST= "localhost:1234"
lms.configure_default_client(SERVER_API_HOST)

if lms.Client.is_valid_api_host(SERVER_API_HOST):
    print(f"An LM Studio API server instance is available at {SERVER_API_HOST}")
else:
    print("No LM Studio API server instance found at {SERVER_API_HOST}")

llm_model=lms.llm()


# Step 1: Load original CSV
print(f"\nReading carmax_USA.csv...")
original_df = pd.read_csv("carmax_USA.csv")
print(f"Loaded {len(original_df)} rows with columns: {original_df.columns.tolist()}")

# Step 2: Create unique (year, make, model, trim) combinations
print("\nCreating unique year/make/model/trim combinations...")
columns_to_check = ['year', 'make', 'model', 'trim']
missing_cols = set(columns_to_check) - set(original_df.columns)
if missing_cols:
    print(f"Warning: Missing columns {missing_cols}. Using first 4 columns from data.")
    df_subset = original_df.iloc[:, :4].copy()
    unique_combinations = df_subset.drop_duplicates().to_dict(orient='records')
else:
    unique_df = original_df[[*columns_to_check]].drop_duplicates()
    print(f"Found {len(unique_df)} unique year/make/model/trim combinations")
    unique_combinations = unique_df.to_dict(orient='records')

# Step 3: Define LLM request helper functions
def create_llm_prompt(row):
    prompt = f"""You are a car database expert. Provide specifications for the following vehicle:\n
        Year: {row['year']}\n
        Make: {row['make']}\n
        Model: {row['model']}\n
        Trim: {row['trim']}\n\n
        Please return ONLY valid JSON with these exact fields:\n
        

horsepower to be given in imperial BHP, not PS, torque is lb-ft, engine displacement is in litres, cylinders is num of cylinders in the engine,
accel is 0-60mph seconds, quarter mile time is in seconds, quarter mile trap speed mph,
weight in kg,
fuel_type is petrol, diesel, hybrid, electric,
fuel economy is mpg or mpg equivalent in US mpg,
quality rating is a numeric score from 1-100 with 1 being poor and 100 being the epitome of luxury,
reliability rating is how reliable the car is on a scale from 1-100 with 1 being terrible and 100 being almost bulletproof
        """
        # {'horsepower': ..., 'torque': ...,'accel': ..., 'fuel_type': ..., 'fuel_economy':...,
        #         'transmission': ..., 'quality_rating': ..., 'reliability_rating':...}
    
    return prompt

def send_llm_request(prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": """You are a car specification assistant. Return ONLY JSON with the fields: horsepower, torque,
             engine displacement, cylinders acceleration (0-60mph), quarter mile time, quarter mile trap speed, weight, fuel_type,
             quality rating, reliability rating. Do not include explanations. Return in a CSV format like this:
             {
            "horsepower": None,
            "torque": None,
            "displacement": None,
            "cylinders": None,
            "accel": None,
            "qmile_time": None,
            "qmile_speed": None,
            "fuel_type": None,
            "fuel_economy": None,
            "quality_rating": None,
            "reliability_rating": None
            }
            replace 'None' with the actual value
             """},
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(LM_STUDIO_API_URL, json=payload)
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
    return response.json()

def parse_llm_response(response):
    content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
    try:
        specs = json.loads(content)
        return specs
    except json.JSONDecodeError:
        print("Raw response:", content[:500])
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        spec_dict = {
            "horsepower": None,
            "torque": None,
            "displacement": None,
            "cylinders": None,
            "accel": None,
            "qmile_time": None,
            "qmile_speed": None,
            "fuel_type": None,
            "fuel_economy": None,
            "quality_rating": None,
            "reliability_rating": None
        }
        for field in ["horsepower", "torque", "displacement", "cylinders", "accel", "qmile_time", "qmile_speed",  "fuel_type", "fuel_economy", "quality_rating", "reliability_rating"]: # fix this
            pattern = rf"{field}[:\s]*(.+?)(?:\n|$)"
            match = re.search(pattern, content)
            if match:
                spec_dict[field] = match.group(1).strip()
        return spec_dict

# Step 4: Process cars in batches
print(f"\nStarting processing of {len(unique_combinations)} records...")
print(f"Batch size: 10, Delay between batches: {delay_seconds}s")
print("-" * 80)

processed_specs = []
all_errors = []
processed_count = 0

for row in unique_combinations:
    print(row)
x=1
for row in unique_combinations:
    print(x)
    x=x+1
    year = row.get('year', '')
    make = row.get('make', '')
    model = row.get('model', '')
    trim = row.get('trim', '')
    
    prompt = create_llm_prompt(row)
    
    try:
        response = llm_model.respond(prompt)
        #specs = parse_llm_response(response)
        print(response)
        entry = {
            'year': year,
            'make': make,
            'model': model,
            'trim': trim,
            **response
        }
        print(entry)
        processed_specs.append(entry)
        processed_count += 1
        
        # if i % 25 == 0 or (i == len(unique_combinations) and processed_count > 0):
        #     print(f"Progress: {processed_count}/{len(unique_combinations)}")
            
    except Exception as e:
        error_entry = {
            'year': year,
            'make': make,
            'model': model,
            'trim': trim,
            'error': str(e),
            'specs': None
        }
        all_errors.append(error_entry)
        
        if "rate" in str(e).lower():
            print(f"Rate limit detected. Waiting {delay_seconds} seconds...")
            time.sleep(delay_seconds)
    
    # Add delay between requests to avoid rate limiting
    # if i % 10 == 0 and i < len(unique_combinations):
    #     time.sleep(delay_seconds)

# Step 5: Save processed specifications to CSV
print("\n" + "-" * 80)
print("Saving specifications...")
if processed_specs:
    output_df = pd.DataFrame(processed_specs)
    print(f"Saved {len(output_df)} records")
    
    # Ensure proper data types
    numeric_cols = ['horsepower', 'torque','displacement', 'accel', 'qmile_time', 'qmile_speed' 'reliability_rating','safety_rating']
    for col in numeric_cols:
        if col in output_df.columns:
            output_df[col] = pd.to_numeric(output_df[col], errors='coerce')
    
    output_file = "carmax_specifications.csv"
    output_df.to_csv(output_file, index=False)
    print(f"Specifications saved to {output_file}")
else:
    print("No specs were successfully retrieved. Saving error log only.")
    if all_errors:
        df_errors = pd.DataFrame(all_errors)
        df_errors.to_csv("carmax_errors.csv", index=False)
        print(f"Errors saved to carmax_errors.csv ({len(df_errors)} records)")

# Step 6: Optional - Join back to original data
print("\n" + "=" * 80)
print("OPTIONAL: JOIN RESULTS BACK TO ORIGINAL DATA")
print("=" * 80)

try:
    if processed_specs:
        df_joined = pd.merge(
            original_df, 
            output_df, 
            on=['year', 'make', 'model', 'trim'], 
            how='inner'
        )
        
        joined_file = "carmax_USA_enriched.csv"
        df_joined.to_csv(joined_file, index=False)
        print(f"\nJoined dataset saved to {joined_file}")
        print(f"Original rows: {len(original_df)}, Joined rows: {len(df_joined)}")
except Exception as e:
    print(f"Join operation failed: {e}")
    if all_errors:
        df_errors = pd.DataFrame(all_errors)
        df_errors.to_csv("carmax_errors.csv", index=False)
        print(f"Errors saved to carmax_errors.csv ({len(df_errors)} records)")

print("\n" + "=" * 80)
print("PROCESSING COMPLETE!")
print("=" * 80)

