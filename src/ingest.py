import pandas as pd
import psycopg2
import argparse
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

def ingest_batch(csv_file):
    """Ingest CSV file into PostgreSQL"""
    try:
        # Read CSV
        print(f"Reading {csv_file}...")
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} rows")
        
        # Connect to PostgreSQL
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Insert data
        print("Inserting data...")
        inserted = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO customers (
                        customer_id, gender, senior_citizen, partner, dependents,
                        tenure, phone_service, multiple_lines, internet_service,
                        online_security, online_backup, device_protection,
                        tech_support, streaming_tv, streaming_movies, contract,
                        paperless_billing, payment_method, monthly_charges,
                        total_charges, churn
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO NOTHING
                """, (
                    row['customerID'], row['gender'], row['SeniorCitizen'],
                    row['Partner'], row['Dependents'], row['tenure'],
                    row['PhoneService'], row['MultipleLines'], row['InternetService'],
                    row['OnlineSecurity'], row['OnlineBackup'], row['DeviceProtection'],
                    row['TechSupport'], row['StreamingTV'], row['StreamingMovies'],
                    row['Contract'], row['PaperlessBilling'], row['PaymentMethod'],
                    row['MonthlyCharges'], row['TotalCharges'], row['Churn']
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting row: {e}")
                continue
        
        conn.commit()
        print(f"✓ Successfully inserted {inserted} rows into PostgreSQL")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ingest churn data')
    parser.add_argument('--batch', required=True, help='Path to CSV file')
    
    args = parser.parse_args()
    ingest_batch(args.batch)
