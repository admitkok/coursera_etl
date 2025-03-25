import os
import requests
import json
import pandas as pd
from datetime import datetime
from google.cloud import bigquery, storage
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def run_etl():
    try:
        # Configuration
        dataset_id = os.getenv("BIGQUERY_DATASET", "coursera_data")
        table_id = os.getenv("BIGQUERY_TABLE", "courses")
        bucket_name = os.getenv("GCS_BUCKET", "chess_hs_bucket-1")
        file_prefix = os.getenv("FILE_PREFIX", "coursera_ds")
        
        # Extract data
        print("Extracting data from Coursera API...")
        API_URL = "https://www.coursera.org/api/courses.v1"
        params = {
            "q": "search",
            "query": "Data Science",
            "fields": "id,name,description,photoUrl,slug,partners.v1(name)",
            "includes": "partners"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(API_URL, params=params, headers=headers)
        response.raise_for_status()
        raw_data = response.json()

        # Transform data
        print("Transforming data...")
        courses = []
        for course in raw_data.get("elements", []):
            partners = ", ".join([p["name"] for p in course.get("partners", []) if "name" in p])
            courses.append({
                "course_id": course.get("id"),
                "course_name": course.get("name"),
                "description": course.get("description", ""),
                "url": f"https://www.coursera.org/learn/{course.get('slug', '')}",
                "image_url": course.get("photoUrl", ""),
                "partners": partners,
                "extracted_at": datetime.now().isoformat()
            })
        df = pd.DataFrame(courses)

        # Load to BigQuery
        print("Loading to BigQuery...")
        client = bigquery.Client()
        schema = [
            bigquery.SchemaField("course_id", "STRING"),
            bigquery.SchemaField("course_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("url", "STRING"),
            bigquery.SchemaField("image_url", "STRING"),
            bigquery.SchemaField("partners", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP"),
        ]
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_TRUNCATE"
        )
        dataset_ref = client.dataset(dataset_id)
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            client.create_dataset(dataset_ref)
        table_ref = dataset_ref.table(table_id)
        client.load_table_from_dataframe(df, table_ref, job_config=job_config).result()

        # Save to GCS
        print("Saving to GCS...")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_blob = bucket.blob(f"coursera/raw/{file_prefix}_{timestamp}.json")
        json_blob.upload_from_string(
            json.dumps(raw_data, indent=2),
            content_type="application/json"
        )
        
        # Save CSV
        csv_blob = bucket.blob(f"coursera/processed/{file_prefix}_{timestamp}.csv")
        csv_blob.upload_from_string(
            df.to_csv(index=False),
            content_type="text/csv"
        )

        return "ETL Pipeline executed successfully", 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"ETL Pipeline failed: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))