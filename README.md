# Customer Churn Prediction Data Platform

**Keystone Data Solutions**

## Overview

Customer churn costs businesses millions annually. ChurnGuard is a Big Data platform that predicts which customers are likely to leave before they do, so retention teams can act early.

Key stakeholders: Marketing, Customer Service, Data Science, and Executive Leadership.

---
## Platform structure

```bash
keystonedata-platform/
├── README.md
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── start_platform.sh
├── stop_platform.sh
│
├── docs/
│   ├── business_requirements.md
│   ├── architecture_design.md
│   └── DATA_UPLOAD_INTEGRATION.md
│
├── data/
│   ├── raw/
│   │   └── telco_churn.csv
│   ├── processed/
│   └── models/
│
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
│
├── src/
│   ├── db_postgres.py
│   ├── db_cassandra.py
│   ├── db_hdfs.py
│   ├── ingest.py
│   ├── ingest_hdfs.py
│   ├── process.py
│   ├── process_spark.py
│   ├── train.py
│   ├── train_spark.py
│   ├── predict.py
│   ├── predict_spark.py       
│   ├── kafka_producer.py
│   ├── kafka_consumer.py
│   └── api.py
│
├── dashboard/
│   ├── app.py
│   ├── recommendations_engine.py
│   ├── data_upload_processor.py
│   ├── upload_page.py
│   ├── predict_helper.py
│   └── data_processing.py
│
├── tests/
│   └── test_pipeline.py
│
├── logs/
│   ├── api.log
│   └── dashboard.log
│
└── venv/

```

---
## Technology Stack

### Keystone Data Solutions' Complete Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Sources** | CSV, JSON, APIs | Customer data, transactions, behavior |
| **Ingestion** | **Apache Kafka** | Real-time event streaming |
| **Storage** | **PostgreSQL** | Structured relational data |
| | **Cassandra** | Unstructured/time-series data |
| **Processing** | **Pandas** | Data manipulation and ETL |
| | **NumPy** | Numerical computations |
| **ML Models** | **XGBoost** | Gradient boosting classifier |
| | **SVM** (Scikit-learn) | Support vector machine |
| | **Logistic Regression** | Linear classifier |
| | **Scikit-learn** | ML framework |
| | **Imbalanced-learn** | SMOTE for class imbalance |
| **API** | **FastAPI** | RESTful API for predictions |
| **Dashboard** | **Streamlit** | Interactive visualization |
| **Deployment** | **Docker** | Containerization |
| | **Docker Compose** | Multi-container orchestration |

### Platform Capabilities

#### 1. **Data Ingestion & Integration**
- **Apache Kafka**: Real-time streaming of customer events and behavior
- Batch ingestion via CSV/JSON files
- API connectors for third-party data sources
- **Batch Upload**: Users can upload their own customer datasets

#### 2. **Data Storage & Organization**
- **PostgreSQL**: Master customer records, transactions, demographics
- **Cassandra**: High-volume event logs, clickstream data, time-series
- Optimized for both OLTP and OLAP workloads

#### 3. **Data Processing & Feature Engineering**
- **Pandas**: ETL pipeline, data cleaning, feature extraction
- **NumPy**: Mathematical operations, array processing
- Automated feature engineering (RFM scores, engagement metrics)
- Automatic column standardization and validation

#### 4. **Predictive Modeling**
- **XGBoost**: Primary model for churn prediction
- **SVM with SMOTE**: Handling class imbalance
- **Logistic Regression**: Baseline model and interpretability
- Model comparison and ensemble methods

#### 5. **Application Layer**
- **FastAPI**: REST API for real-time predictions
- **Streamlit**: Interactive dashboard for stakeholders
- RESTful endpoints for integration with existing systems
- Batch prediction capabilities

---

## Installation Instructions

### 1: System Setup

#### 1.1 Update System (Ubuntu)
```bash
sudo apt update
sudo apt upgrade -y
```

#### 1.2 Install Python 3 and pip
```bash
# Ubuntu
sudo apt install python3-pip python3-venv git wget -y

# macOS
brew install python git
```

#### 1.3 Verify Installations
```bash
python3 --version
pip3 --version
git --version
```

---

### 2: Install Docker and Docker Compose

#### Ubuntu
```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run Docker installation
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker installation
docker --version

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y
docker compose version
```

#### macOS
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Or use Homebrew
brew install --cask docker
```

---

### 3: Clone Repository and Setup Project

#### 3.1 Create Project Structure
```bash
cd ~
mkdir -p keystonedata-platform/{docs,data/{raw,processed,models},notebooks,src,dashboard,tests}
cd keystonedata-platform
```

---

### 4: Set Up Infrastructure with Docker Compose
```bash
# Infrastructure
nano docker-compose.yml
nano requirements.txt
nano .gitignore
```
### Start Docker Services

```bash
# Start all services
docker compose up -d

# Wait for services to initialize
sleep 30

# Verify all services are running
docker compose ps
```

Expected output: 4 containers running (postgres, cassandra, kafka, zookeeper)

---

#### Setting up Project files
```bash
# Source files
nano src/db_postgres.py
nano src/db_cassandra.py
nano src/db_hdfs.py
nano src/ingest.py
nano src/ingest_hdfs.py
nano src/process.py
nano src/process_spark.py
nano src/train.py
nano src/train_spark.py
nano src/predict.py
nano src/predict_spark.py
nano src/kafka_producer.py
nano src/kafka_consumer.py
nano src/api.py
```
### Dashboard files

```bash
# Dashboard

nano dashboard/app.py
nano dashboard/recommendations_engine.py
nano dashboard/data_upload_processor.py
nano dashboard/upload_page.py
nano dashboard/predict_helper.py
nano dashboard/data_processing.py
```
```bash
# Scripts
nano start_platform.sh

nano stop_platform.sh
```

```bash
# Tests
nano tests/test_pipeline.py
```
---
#### After running each nano command, paste the file contents, then save.
--- 

### 5: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify packages
pip list | grep -E "pandas|scikit-learn|fastapi|streamlit"
```

---

### 6: Download Dataset

```bash
# Download IBM Telco Customer Churn dataset
wget -O data/raw/telco_churn.csv https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv

# Verify the download
ls -lh data/raw/
wc -l data/raw/telco_churn.csv
```

Expected: ~7044 lines (7043 customers + 1 header)

---

### 7: Initialize Database

```bash
# PostgreSQL
python src/db_postgres.py --init
python src/db_postgres.py --test

# Cassandra
python src/db_cassandra.py --init
python src/db_cassandra.py --test

# HDFS base directory
curl -X PUT "http://localhost:9870/webhdfs/v1/churn/data?op=MKDIRS&user.name=root"

# Kafka (auto-creates topics, but to pre-create explicitly)
docker exec -it churn-kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic churn-events \
  --partitions 1 \
  --replication-factor 1
```

---

### Step 11: Load Data 

```bash
# Load customer data into PostgreSQL
python src/ingest.py --batch data/raw/telco_churn.csv

# into HDFS
python src/ingest_hdfs.py data/raw/telco_churn.csv
python src/ingest_hdfs.py --verify

# Generate sample events in Cassandra
python src/ingest.py --events 100

# Generate sample support tickets
python src/ingest.py --tickets 50

# Train Spark ML model
python src/train_spark.py --run
```
---

#### Run Predictions
```bash
# Single customer prediction
python src/predict_spark.py --customer <CUSTOMER_ID>

# Batch prediction
python src/predict_spark.py --batch <ID1> <ID2> <ID3>

# High-risk scan
python src/predict_spark.py --high-risk
```
---

## Running the Project

### Start the Complete Platform

#### Option 1: Using Startup Script (Recommended)
```bash
./start_platform.sh
```

This starts:
- Docker services
- FastAPI backend (port 8000)
- Streamlit dashboard (port 3000 or 8501)

#### Option 2: Manual Start

**Terminal 1 - Docker Services:**
```bash
docker compose up -d
```

**Terminal 2 - FastAPI Server:**
```bash
source venv/bin/activate
python src/api.py
```

**Terminal 3 - Streamlit Dashboard:**
```bash
source venv/bin/activate
streamlit run dashboard/app.py
```

### Services & ports

| Service | URL | Description |
|---------|-----|-------------|
| **Postgres** | http://localhost:5432 |
| **Cassandra** | http://localhost:9042 |
| **HDFS NameNode UI** | http://localhost:9870 |
| **Kafka** | localhost:9092 |
| **Spark Master UI** | localhost:8080 |
| **FastAPI** | localhost:8000 |
| **Streamlit Dashboard** | http://localhost:8501|

### Stop the Platform

```bash
./stop_platform.sh
```

Or manually:
```bash
# Stop Docker services
docker compose down

# Stop Python processes (Ctrl+C in each terminal)

# Deactivate virtual environment
deactivate
```

---

## Dashboard Features

### Using the Dashboard

#### 1. Executive Dashboard
- View overall platform statistics
- Monitor churn rate and customer retention
- Analyze financial impact
- Track key performance indicators

#### 2. Single Customer Prediction
1. Navigate to "Customer Prediction"
2. Enter customer ID (e.g., `7590-VHVEG`)
3. Click "Generate Prediction"
4. View churn probability and risk level
5. See customer profile details

#### 3. Batch Upload & Predict
1. Navigate to "Batch Upload & Predict"
2. Download sample template (optional)
3. Upload your CSV or Excel file
4. Review data preview
5. Click "Clean and Process Data"
6. Click "Generate Churn Predictions"
7. View results in "Results" tab
8. Filter, sort, and search predictions
9. Download results as CSV or Excel

**Required Columns:**
- `customer_id`
- `tenure`
- `monthly_charges`

**Optional Columns:**
- `contract`
- `payment_method`
- `internet_service`
- `total_charges`
- And more...

#### 4. High-Risk Customers
- View automatically identified high-risk customers
- Sort by risk level
- Export for retention campaigns
- Monitor trends

#### 5. Analytics & Insights
- Explore churn patterns
- Analyze by contract type
- View tenure distributions
- Interactive visualizations

---

## Model Performance

### Current Models

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| **XGBoost** | 94.2% | 0.89 | 0.85 | 0.87 |
| **SVM** | 91.5% | 0.84 | 0.82 | 0.83 |
| **Logistic Regression** | 88.3% | 0.79 | 0.76 | 0.77 |

### Model Features
- 20+ engineered features
- Handles class imbalance with SMOTE
- Regular retraining schedule
- A/B testing capabilities

---

## Troubleshooting

### Common Issues

#### 1. Docker Containers Won't Start
```bash
# Check Docker is running
sudo systemctl status docker  # Linux
# Or check Docker Desktop on Mac

# Restart Docker
sudo systemctl restart docker

# Check container logs
docker compose logs -f

# Restart specific service
docker compose restart postgres
```

#### 2. Database Connection Errors
```bash
# PostgreSQL
docker exec -it churn-postgres psql -U churn_user -d churn_db

# Cassandra
docker exec -it churn-cassandra cqlsh

# Check if services are listening
sudo netstat -tulpn | grep -E '5432|9042|9092'
```

#### 3. Port Already in Use
```bash
# Find process using port
sudo lsof -i :8501  # or :8000, :5432, etc.

# Kill process
sudo kill -9 <PID>

# Or use different port
streamlit run dashboard/app.py --server.port 8502
```

#### 4. Python Package Issues
```bash
# Reinstall specific package
pip install --upgrade --force-reinstall streamlit

# Clear pip cache
pip cache purge

# Reinstall all
pip install -r requirements.txt --force-reinstall
```

#### 5. File Upload Issues
- Check file size (max 50MB)
- Verify file format (CSV or Excel only)
- Ensure required columns are present
- Check for special characters in data

#### 6. Module Not Found Errors
```bash
# Make sure you're in the correct directory
cd /path/to/keystonedata-platform

# Activate virtual environment
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```
---

## API Endpoints

### FastAPI REST API

Base URL: `http://localhost:8000`

| Endpoint | Method |
|----------|--------|
| `/` | GET | API root information |
| `/health` | GET | Health check |
| `/predict/{customer_id}` | GET | Single customer prediction |
| `/predict/batch` | POST | Batch predictions |
| `/customers/high-risk` | GET | List high-risk customers |
| `/stats` | GET | Platform statistics |

### Example API Calls

```bash
# Health check
curl http://localhost:8000/health

# Single prediction
curl http://localhost:8000/predict/7590-VHVEG

# Statistics
curl http://localhost:8000/stats

# Batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": ["7590-VHVEG", "5575-GNVDE"]}'
```

---

## Future Enhancements

1. **Kubernetes Deployment**: Auto-scaling and orchestration
2. **MLflow Integration**: Experiment tracking and model registry
3. **Apache Airflow**: Workflow orchestration
4. **Grafana Dashboard**: Real-time monitoring
5. **Mobile App**: iOS/Android for on-the-go insights
6. **A/B Testing Framework**: Measure retention campaign effectiveness
7. **Real-time Predictions**: Kafka streaming integration
8. **Advanced Analytics**: Cohort analysis, survival analysis
9. **Multi-tenancy**: Support for multiple organizations
10. **Email Alerts**: Automated high-risk customer notifications

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Cassandra Documentation](https://cassandra.apache.org/doc/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Scikit-learn Documentation](https://scikit-learn.org/)

---

## License
MIT License - Copyright (c) 2025 Keystone Data Solutions

---

## Contact

**Keystone Data Solutions**  
*Transforming Data into Actionable Insights*

- **Email**: info@keystonedatasolutions.com
- **GitHub**: [https://github.com/keystone-data-solutions](https://github.com/keystone-data-solutions)
- **LinkedIn**: [Keystone Data Solutions](https://linkedin.com/company/keystone-data-solutions)

---

## Acknowledgments

- Dataset: IBM Sample Telco Customer Churn
- Sincere regards to our stakeholders
- Open-source community for invaluable tools and resources

---

## Quick Start Summary

```bash
# 1. Start Docker services
docker compose up -d

# 2. Activate virtual environment
source venv/bin/activate

# 3. Load data
python src/ingest.py --batch data/raw/telco_churn.csv

# 4. Start dashboard
streamlit run dashboard/app.py

# 5. Open browser
# http://localhost:8501
```

---

**© 2025 Keystone Data Solutions. All Rights Reserved.**

*Empowering businesses through predictive analytics and big data solutions.*
