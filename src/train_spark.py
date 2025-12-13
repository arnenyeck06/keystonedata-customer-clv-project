"""
Spark ML-based Model Training
Trains directly from raw CSV data
"""
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql.functions import col, when
import argparse
from datetime import datetime
import os

def create_spark_session():
    print("Creating Spark session...")
    spark = SparkSession.builder \
        .appName("ChurnGuard-ML") \
        .master("local[*]") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    print("Spark session created")
    return spark

def load_and_prepare_data(spark):
    print("Loading raw data...")
    
    df = spark.read.csv(
        "data/raw/telco_churn.csv",
        header=True,
        inferSchema=True
    )
    print(f"Loaded {df.count():,} records")
    
    # Clean TotalCharges
    df = df.withColumn(
        "TotalCharges",
        when(col("TotalCharges") == " ", col("MonthlyCharges"))
        .otherwise(col("TotalCharges").cast("double"))
    )
    
    # Drop nulls
    df = df.dropna()
    print(f"After cleaning: {df.count():,} records")
    
    # Select numeric features
    feature_cols = [
        'SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges'
    ]
    
    # Binary encode categorical
    df = df.withColumn("gender_encoded", when(col("gender") == "Male", 1).otherwise(0))
    df = df.withColumn("Partner_encoded", when(col("Partner") == "Yes", 1).otherwise(0))
    df = df.withColumn("Dependents_encoded", when(col("Dependents") == "Yes", 1).otherwise(0))
    df = df.withColumn("PhoneService_encoded", when(col("PhoneService") == "Yes", 1).otherwise(0))
    df = df.withColumn("PaperlessBilling_encoded", when(col("PaperlessBilling") == "Yes", 1).otherwise(0))
    
    # Contract type
    df = df.withColumn("Contract_MTM", when(col("Contract") == "Month-to-month", 1).otherwise(0))
    df = df.withColumn("Contract_OneYear", when(col("Contract") == "One year", 1).otherwise(0))
    df = df.withColumn("Contract_TwoYear", when(col("Contract") == "Two year", 1).otherwise(0))
    
    # Internet service
    df = df.withColumn("InternetService_DSL", when(col("InternetService") == "DSL", 1).otherwise(0))
    df = df.withColumn("InternetService_Fiber", when(col("InternetService") == "Fiber optic", 1).otherwise(0))
    df = df.withColumn("InternetService_No", when(col("InternetService") == "No", 1).otherwise(0))
    
    feature_cols.extend([
        'gender_encoded', 'Partner_encoded', 'Dependents_encoded',
        'PhoneService_encoded', 'PaperlessBilling_encoded',
        'Contract_MTM', 'Contract_OneYear', 'Contract_TwoYear',
        'InternetService_DSL', 'InternetService_Fiber', 'InternetService_No'
    ])
    
    # Assemble features
    assembler = VectorAssembler(
        inputCols=feature_cols,
        outputCol="features",
        handleInvalid="skip"
    )
    df = assembler.transform(df)
    
    # Create label
    df = df.withColumn("label", when(col("Churn") == "Yes", 1).otherwise(0))
    
    df = df.select("features", "label").dropna()
    print(f"Final dataset: {df.count():,} records with {len(feature_cols)} features")
    
    return df, feature_cols

def train_models(df):
    print("\nTraining models...")
    print("=" * 60)
    
    train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
    print(f"Train: {train_df.count():,} | Test: {test_df.count():,}")
    
    # Scale
    scaler = StandardScaler(inputCol="features", outputCol="scaled_features", withStd=True, withMean=False)
    scaler_model = scaler.fit(train_df)
    train_df = scaler_model.transform(train_df)
    test_df = scaler_model.transform(test_df)
    
    models = {
        "Logistic Regression": LogisticRegression(featuresCol="scaled_features", labelCol="label", maxIter=100),
        "Random Forest": RandomForestClassifier(featuresCol="scaled_features", labelCol="label", numTrees=50, seed=42)
    }
    
    results = {}
    eval_auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")
    eval_acc = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
    
    for name, model in models.items():
        print(f"\nTraining {name}...")
        start = datetime.now()
        
        trained = model.fit(train_df)
        preds = trained.transform(test_df)
        
        auc = eval_auc.evaluate(preds)
        acc = eval_acc.evaluate(preds)
        dur = (datetime.now() - start).total_seconds()
        
        results[name] = {'model': trained, 'auc': auc, 'accuracy': acc, 'duration': dur}
        print(f"Time: {dur:.2f}s | Accuracy: {acc:.4f} | AUC: {auc:.4f}")
    
    return results, scaler_model

def save_models(results, scaler_model, feature_cols):
    print("\nSaving models...")
    
    best_name = max(results.keys(), key=lambda k: results[k]['auc'])
    best = results[best_name]['model']
    print(f"Best: {best_name} (AUC: {results[best_name]['auc']:.4f})")
    
    os.makedirs("data/models", exist_ok=True)
    
    best.write().overwrite().save("data/models/spark_best_model")
    scaler_model.write().overwrite().save("data/models/spark_scaler")
    
    with open("data/models/spark_features.txt", "w") as f:
        f.write("\n".join(feature_cols))
    
    with open("data/models/spark_metrics.txt", "w") as f:
        f.write("Spark Model Results\n" + "="*60 + "\n\n")
        for name, res in results.items():
            f.write(f"{name}:\n  Accuracy: {res['accuracy']:.4f}\n  AUC: {res['auc']:.4f}\n  Time: {res['duration']:.2f}s\n\n")
        f.write(f"Best: {best_name}\n")
    
    print("Models saved to data/models/")

def train_pipeline():
    print("="*60)
    print("SPARK ML TRAINING PIPELINE")
    print("="*60)
    
    start = datetime.now()
    spark = create_spark_session()
    
    try:
        df, features = load_and_prepare_data(spark)
        if df.count() == 0:
            print("No data available")
            return
        
        results, scaler = train_models(df)
        save_models(results, scaler, features)
        
        print(f"\n{'='*60}")
        print(f"COMPLETE | Duration: {(datetime.now()-start).total_seconds():.2f}s")
        print("="*60)
        
    finally:
        spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    
    if args.run:
        train_pipeline()
    else:
        print("Usage: python src/train_spark.py --run")
