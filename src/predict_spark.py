"""
Spark ML-based Churn Prediction
Loads models saved by train_spark.py
"""
from pyspark.sql import SparkSession
from pyspark.ml.classification import RandomForestClassificationModel, LogisticRegressionModel
from pyspark.ml.feature import StandardScalerModel, VectorAssembler
import psycopg2
import pandas as pd
import argparse
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

MODEL_PATH    = "data/models/spark_best_model"
SCALER_PATH   = "data/models/spark_scaler"
FEATURES_PATH = "data/models/spark_features.txt"


def create_spark_session():
    spark = SparkSession.builder \
        .appName("ChurnGuard-Predict") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_artifacts(spark):
    print("Loading model artifacts...")

    with open(FEATURES_PATH, "r") as f:
        feature_cols = [line.strip() for line in f if line.strip()]

    scaler_model = StandardScalerModel.load(SCALER_PATH)

    try:
        model = RandomForestClassificationModel.load(MODEL_PATH)
        print("Loaded: Random Forest model")
    except Exception:
        model = LogisticRegressionModel.load(MODEL_PATH)
        print("Loaded: Logistic Regression model")

    print(f"Features: {len(feature_cols)}")
    return model, scaler_model, feature_cols


def get_customer_data(customer_id):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        row = cursor.fetchone()
        if not row:
            print(f"Customer {customer_id} not found.")
            cursor.close()
            conn.close()
            return None
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return dict(zip(columns, row))
    except Exception as e:
        print(f"DB error: {e}")
        return None


def get_all_customers():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql("SELECT * FROM customers", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"DB error: {e}")
        return None


def build_spark_df(spark, data, feature_cols):
    pdf = pd.DataFrame([data]) if isinstance(data, dict) else data.copy()

    # PostgreSQL returns snake_case — rename to match train_spark.py column names
    pdf.rename(columns={
        'customer_id':       'customerID',
        'senior_citizen':    'SeniorCitizen',
        'monthly_charges':   'MonthlyCharges',
        'total_charges':     'TotalCharges',
        'partner':           'Partner',
        'dependents':        'Dependents',
        'phone_service':     'PhoneService',
        'paperless_billing': 'PaperlessBilling',
        'contract':          'Contract',
        'internet_service':  'InternetService',
        'gender':            'gender',
    }, inplace=True)

    # Fix TotalCharges
    pdf['TotalCharges'] = pd.to_numeric(pdf['TotalCharges'], errors='coerce')
    pdf['TotalCharges'] = pdf['TotalCharges'].fillna(pdf['MonthlyCharges'])

    # Binary encodings
    pdf['gender_encoded']           = (pdf['gender'] == 'Male').astype(int)
    pdf['Partner_encoded']          = (pdf['Partner'] == 'Yes').astype(int)
    pdf['Dependents_encoded']       = (pdf['Dependents'] == 'Yes').astype(int)
    pdf['PhoneService_encoded']     = (pdf['PhoneService'] == 'Yes').astype(int)
    pdf['PaperlessBilling_encoded'] = (pdf['PaperlessBilling'] == 'Yes').astype(int)

    # Contract
    pdf['Contract_MTM']     = (pdf['Contract'] == 'Month-to-month').astype(int)
    pdf['Contract_OneYear'] = (pdf['Contract'] == 'One year').astype(int)
    pdf['Contract_TwoYear'] = (pdf['Contract'] == 'Two year').astype(int)

    # Internet service
    pdf['InternetService_DSL']   = (pdf['InternetService'] == 'DSL').astype(int)
    pdf['InternetService_Fiber'] = (pdf['InternetService'] == 'Fiber optic').astype(int)
    pdf['InternetService_No']    = (pdf['InternetService'] == 'No').astype(int)

    # Ensure all feature cols exist
    for c in feature_cols:
        if c not in pdf.columns:
            pdf[c] = 0

    # Keep customerID for reference if present
    keep_cols = feature_cols + (['customerID'] if 'customerID' in pdf.columns else [])
    pdf = pdf[[c for c in keep_cols if c in pdf.columns]]

    sdf = spark.createDataFrame(pdf)

    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    sdf = assembler.transform(sdf)
    return sdf


def run_prediction(spark, model, scaler_model, feature_cols, customer):
    sdf = build_spark_df(spark, customer, feature_cols)
    scaled = scaler_model.transform(sdf)
    result = model.transform(scaled)
    row = result.select("prediction", "probability").first()

    prediction = int(row['prediction'])
    churn_prob = float(row['probability'][1])
    risk_level = 'HIGH' if churn_prob > 0.7 else 'MEDIUM' if churn_prob > 0.4 else 'LOW'
    return prediction, churn_prob, risk_level


def predict_customer(spark, model, scaler_model, feature_cols, customer_id):
    customer = get_customer_data(customer_id)
    if customer is None:
        return None

    prediction, churn_prob, risk_level = run_prediction(spark, model, scaler_model, feature_cols, customer)

    print("\n" + "=" * 60)
    print("PREDICTION RESULTS")
    print("=" * 60)
    print(f"Customer ID    : {customer_id}")
    print(f"Prediction     : {'WILL CHURN' if prediction == 1 else 'WILL NOT CHURN'}")
    print(f"Churn Prob     : {churn_prob:.1%}")
    print(f"Risk Level     : {risk_level}")
    print("=" * 60)
    print(f"\nCustomer Profile:")
    print(f"  Tenure         : {customer.get('tenure')} months")
    print(f"  Contract       : {customer.get('contract')}")
    print(f"  Monthly Charges: ${customer.get('monthly_charges')}")
    print(f"  Payment Method : {customer.get('payment_method')}")

    return {
        'customer_id': customer_id,
        'prediction': prediction,
        'churn_probability': churn_prob,
        'risk_level': risk_level,
        'timestamp': datetime.now().isoformat()
    }


def predict_batch(spark, model, scaler_model, feature_cols, customer_ids):
    results = []
    for cid in customer_ids:
        r = predict_customer(spark, model, scaler_model, feature_cols, cid)
        if r:
            results.append(r)
    print(f"\nCompleted {len(results)}/{len(customer_ids)} predictions")
    return results


def predict_high_risk(spark, model, scaler_model, feature_cols):
    print("Loading all customers from PostgreSQL...")
    pdf = get_all_customers()
    if pdf is None or pdf.empty:
        print("No customers found.")
        return

    sdf = build_spark_df(spark, pdf, feature_cols)
    scaled = scaler_model.transform(sdf)
    result = model.transform(scaled)

    rows = result.select("customerID", "prediction", "probability").collect()
    high_risk = []
    for row in rows:
        prob = float(row['probability'][1])
        if prob > 0.7:
            high_risk.append((row['customerID'], prob))

    high_risk.sort(key=lambda x: x[1], reverse=True)
    print(f"\nFound {len(high_risk)} HIGH RISK customers (prob > 70%):")
    print("-" * 40)
    for cid, prob in high_risk[:20]:
        print(f"  {cid}  ->  {prob:.1%}")
    if len(high_risk) > 20:
        print(f"  ... and {len(high_risk) - 20} more")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spark Churn Prediction')
    parser.add_argument('--customer',  type=str,            help='Single customer ID')
    parser.add_argument('--batch',     type=str, nargs='+', help='Multiple customer IDs')
    parser.add_argument('--high-risk', action='store_true', help='Find all high-risk customers')
    args = parser.parse_args()

    spark = create_spark_session()
    try:
        model, scaler_model, feature_cols = load_artifacts(spark)

        if args.customer:
            predict_customer(spark, model, scaler_model, feature_cols, args.customer)

        elif args.batch:
            predict_batch(spark, model, scaler_model, feature_cols, args.batch)

        elif args.high_risk:
            predict_high_risk(spark, model, scaler_model, feature_cols)

        else:
            print("Usage examples:")
            print("  python src/predict_spark.py --customer 9237-HQITU")
            print("  python src/predict_spark.py --batch 9237-HQITU 5575-GNVDE")
            print("  python src/predict_spark.py --high-risk")

    finally:
        spark.stop()