"""
Spark-based Data Processing Pipeline
Uses PySpark for distributed data processing
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, count, lit
)
import psycopg2
from datetime import datetime
import argparse

# Database configs
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

# HDFS paths
HDFS_NAMENODE = "hdfs://namenode:8020"
HDFS_RAW_PATH = f"{HDFS_NAMENODE}/churnguard/data/raw"
HDFS_PROCESSED_PATH = f"{HDFS_NAMENODE}/churnguard/data/processed"

def create_spark_session():
    """Create Spark session with HDFS support"""
    print("Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName("ChurnGuard-Processing") \
        .master("local[*]") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "1g") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("Spark session created")
    return spark

def load_from_csv(spark, filepath):
    """Load data from CSV"""
    print(f"Loading data from CSV: {filepath}")
    
    try:
        df = spark.read.csv(
            filepath,
            header=True,
            inferSchema=True
        )
        print(f"Loaded {df.count():,} records")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def clean_data_spark(df):
    """Clean and prepare data using Spark"""
    print("\nCleaning data...")
    
    original_count = df.count()
    
    # Handle TotalCharges - convert to numeric
    df = df.withColumn(
        "TotalCharges",
        when(col("TotalCharges") == " ", None)
        .otherwise(col("TotalCharges").cast("double"))
    )
    
    # Fill missing TotalCharges with MonthlyCharges
    df = df.withColumn(
        "TotalCharges",
        when(col("TotalCharges").isNull(), col("MonthlyCharges"))
        .otherwise(col("TotalCharges"))
    )
    
    # Drop rows with nulls in critical columns
    critical_cols = ["customerID", "tenure", "MonthlyCharges", "Churn"]
    df = df.dropna(subset=critical_cols)
    
    final_count = df.count()
    print(f"Cleaned data: {final_count:,} records (removed {original_count - final_count} rows)")
    return df

def engineer_features_spark(df):
    """Create features using Spark"""
    print("\nEngineering features...")
    
    # Tenure categories
    df = df.withColumn(
        "tenure_group",
        when(col("tenure") <= 12, "0-1yr")
        .when(col("tenure") <= 24, "1-2yr")
        .when(col("tenure") <= 48, "2-4yr")
        .otherwise("4yr+")
    )
    
    # Service counts
    service_cols = [
        'PhoneService', 'MultipleLines', 'InternetService',
        'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
        'TechSupport', 'StreamingTV', 'StreamingMovies'
    ]
    
    total_services_expr = lit(0)
    for c in service_cols:
        if c in df.columns:
            total_services_expr = total_services_expr + when(col(c) == "Yes", 1).otherwise(0)
    
    df = df.withColumn("total_services", total_services_expr)
    
    # Contract risk score
    df = df.withColumn(
        "contract_risk",
        when(col("Contract") == "Month-to-month", 1.0)
        .when(col("Contract") == "One year", 0.5)
        .when(col("Contract") == "Two year", 0.2)
        .otherwise(0.5)
    )
    
    # Payment method risk
    df = df.withColumn(
        "payment_risk",
        when(col("PaymentMethod") == "Electronic check", 1.0)
        .when(col("PaymentMethod") == "Mailed check", 0.7)
        .otherwise(0.3)
    )
    
    # Average monthly revenue
    df = df.withColumn(
        "avg_monthly_revenue",
        col("TotalCharges") / (col("tenure") + 1)
    )
    
    # Has family
    df = df.withColumn(
        "has_family",
        when((col("Partner") == "Yes") | (col("Dependents") == "Yes"), 1)
        .otherwise(0)
    )
    
    print("Created new features")
    return df

def encode_categorical_spark(df):
    """Encode categorical variables"""
    print("\nEncoding categorical variables...")
    
    # Binary encoding
    binary_cols = ['gender', 'Partner', 'Dependents', 'PhoneService', 
                   'PaperlessBilling', 'Churn']
    
    for col_name in binary_cols:
        if col_name in df.columns:
            df = df.withColumn(
                col_name,
                when(col(col_name) == "Yes", 1).otherwise(0)
            )
    
    # Convert SeniorCitizen to int
    if "SeniorCitizen" in df.columns:
        df = df.withColumn("SeniorCitizen", col("SeniorCitizen").cast("int"))
    
    print("Encoded categorical variables")
    return df

def save_to_csv(df, output_path):
    """Save DataFrame to CSV"""
    print(f"\nSaving to CSV: {output_path}")
    
    try:
        df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path)
        print(f"Saved successfully")
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

def process_pipeline_spark():
    """Run the complete Spark processing pipeline"""
    print("=" * 60)
    print("STARTING SPARK DATA PROCESSING PIPELINE")
    print("=" * 60)
    
    start_time = datetime.now()
    
    spark = create_spark_session()
    
    try:
        # Load data
        df = load_from_csv(spark, "data/raw/telco_churn.csv")
        
        if df is None:
            print("Error: Could not load data")
            return
        
        # Process data
        df = clean_data_spark(df)
        df = engineer_features_spark(df)
        df = encode_categorical_spark(df)
        
        # Save results
        output_path = "data/processed/processed_churn_data_spark"
        save_to_csv(df, output_path)
        
        # Print statistics
        row_count = df.count()
        col_count = len(df.columns)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("SPARK PROCESSING COMPLETE")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Final dataset: {row_count:,} rows x {col_count:,} columns")
        print(f"Output: {output_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error in pipeline: {e}")
        
    finally:
        spark.stop()
        print("Spark session stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spark Data Processing Pipeline')
    parser.add_argument('--run', action='store_true', help='Run the Spark processing pipeline')
    
    args = parser.parse_args()
    
    if args.run:
        process_pipeline_spark()
    else:
        print("Usage: python src/process_spark.py --run")
