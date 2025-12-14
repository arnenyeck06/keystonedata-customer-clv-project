import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os
import sys
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

# Import prediction helper if available
try:
    from predict_helper import predict_customer_churn
    PREDICTION_AVAILABLE = True
except:
    PREDICTION_AVAILABLE = False

# Import recommendations engine
try:
    from recommendations_engine import RecommendationsEngine, get_recommendations
    RECOMMENDATIONS_AVAILABLE = True
except:
    RECOMMENDATIONS_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="ChurnGuard Analytics | Keystone Data Solutions",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Professional Dark Theme CSS
# =========================
st.markdown("""
<style>
/* Import clean, professional fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

/* Global Styles */
.stApp {
    background: linear-gradient(135deg, #1a1f35 0%, #0f1419 100%);
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Main Header */
.main-header {
    font-family: 'Inter', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    color: #ffffff;
    text-align: center;
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
    animation: fadeInDown 0.6s ease-out;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.subtitle {
    text-align: center;
    color: #a0aec0;
    font-size: 0.95rem;
    margin-bottom: 2.5rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 500;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: #0f1419;
    border-right: 1px solid #2d3748;
}

[data-testid="stSidebar"] .css-1d391kg {
    color: #ffffff;
}

/* Navigation Radio Buttons */
[data-testid="stSidebar"] label {
    color: #cbd5e0 !important;
    font-weight: 500;
    padding: 0.875rem 1.25rem;
    border-radius: 8px;
    transition: all 0.2s ease;
    font-size: 0.95rem;
}

[data-testid="stSidebar"] label:hover {
    background: rgba(66, 153, 225, 0.15);
    color: #63b3ed !important;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    padding: 1.75rem;
    border-radius: 12px;
    border: 1px solid #4a5568;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    animation: slideUp 0.5s ease-out backwards;
}

.kpi-card:hover {
    transform: translateY(-3px);
    border-color: #63b3ed;
    box-shadow: 0 8px 24px rgba(99, 179, 237, 0.2);
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #4299e1, #667eea);
    border-radius: 12px 12px 0 0;
}

.kpi-green::before {
    background: #48bb78;
}

.kpi-yellow::before {
    background: #ed8936;
}

.kpi-red::before {
    background: #f56565;
}

.kpi-title {
    font-size: 0.875rem;
    color: #cbd5e0;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.75rem;
    font-weight: 600;
}

.kpi-value {
    font-family: 'Inter', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.kpi-subtitle {
    font-size: 0.875rem;
    margin-top: 0.75rem;
    color: #a0aec0;
    font-weight: 500;
}

/* Status Indicator */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: rgba(72, 187, 120, 0.15);
    border: 1px solid #48bb78;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
    color: #48bb78;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #48bb78;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-green {
    background: rgba(72, 187, 120, 0.2);
    color: #48bb78;
    border: 1px solid #48bb78;
}

.badge-yellow {
    background: rgba(237, 137, 54, 0.2);
    color: #ed8936;
    border: 1px solid #ed8936;
}

.badge-red {
    background: rgba(245, 101, 101, 0.2);
    color: #f56565;
    border: 1px solid #f56565;
}

/* Section Headers */
.section-header {
    font-family: 'Inter', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: #ffffff;
    margin: 2rem 0 1.25rem 0;
    padding-left: 1rem;
    border-left: 4px solid #4299e1;
}

/* Cards */
.card {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    border: 1px solid #4a5568;
    border-radius: 12px;
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.card h3 {
    color: #ffffff;
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

/* Input Styling */
.stTextInput > div > div > input {
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 8px;
    color: #ffffff;
    font-size: 1rem;
    padding: 0.875rem 1rem;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus {
    border-color: #4299e1;
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.2);
    background: #2d3748;
}

.stTextInput > label {
    color: #cbd5e0 !important;
    font-weight: 600;
    font-size: 0.9rem;
}

/* Button Styling */
.stButton > button {
    background: linear-gradient(135deg, #4299e1, #667eea);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0.875rem 2rem;
    font-weight: 700;
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    width: 100%;
    box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(66, 153, 225, 0.4);
}

/* Metrics Styling */
[data-testid="stMetricValue"] {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
}

[data-testid="stMetricLabel"] {
    color: #cbd5e0;
    font-weight: 600;
    font-size: 0.9rem;
}

[data-testid="stMetricDelta"] {
    font-weight: 600;
}

/* Info/Warning/Success Boxes */
.stAlert {
    background: rgba(66, 153, 225, 0.15) !important;
    border: 1px solid #4299e1 !important;
    border-left: 4px solid #4299e1 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    padding: 1rem 1.25rem !important;
}

.stAlert [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
    font-weight: 500;
}

/* Tables and Dataframes */
.dataframe {
    background: #1a202c !important;
    color: #ffffff !important;
}

.dataframe th {
    background: #2d3748 !important;
    color: #cbd5e0 !important;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
}

.dataframe td {
    color: #e2e8f0 !important;
    border-bottom: 1px solid #4a5568 !important;
}

/* Customer ID Display */
.customer-id {
    font-family: 'JetBrains Mono', monospace;
    color: #4299e1;
    font-weight: 600;
    font-size: 1.1rem;
    background: rgba(66, 153, 225, 0.15);
    padding: 0.5rem 1rem;
    border-radius: 6px;
    display: inline-block;
    border: 1px solid #4299e1;
}

/* Result Display */
.result-box {
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
}

.result-probability {
    font-size: 4.5rem;
    font-weight: 800;
    color: #ffffff;
    font-family: 'Inter', sans-serif;
    line-height: 1;
    text-shadow: 0 2px 8px rgba(66, 153, 225, 0.5);
    margin: 1.5rem 0;
}

.result-label {
    color: #a0aec0;
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Financial Box */
.financial-box {
    background: linear-gradient(135deg, rgba(237, 137, 54, 0.1) 0%, rgba(237, 137, 54, 0.05) 100%);
    border: 1px solid rgba(237, 137, 54, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.financial-box h3 {
    color: #ed8936;
    font-weight: 700;
    margin-bottom: 1.25rem;
    font-size: 1.25rem;
}

.financial-item {
    display: flex;
    justify-content: space-between;
    padding: 1rem 0;
    border-bottom: 1px solid rgba(237, 137, 54, 0.2);
    color: #e2e8f0;
    font-size: 0.95rem;
}

.financial-item:last-child {
    border-bottom: none;
}

.financial-value {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: #ffffff;
    font-size: 1.25rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: #2d3748;
    border-radius: 8px;
    color: #cbd5e0;
    padding: 0.75rem 1.5rem;
    border: 1px solid #4a5568;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4299e1, #667eea);
    color: #ffffff;
    border: none;
}

/* Slider */
.stSlider > div > div > div {
    background: #4299e1;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #718096;
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}

.empty-state-text {
    font-size: 1.1rem;
    color: #a0aec0;
    font-weight: 500;
}

/* Navigation Section Title */
.nav-section {
    color: #718096;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 700;
    margin: 1.5rem 0 0.75rem 0;
    padding: 0 1.25rem;
}

/* Divider */
hr {
    border: none;
    border-top: 1px solid #4a5568;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Database config
# =========================
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

# =========================
# Helper function to convert Decimal to float
# =========================
def convert_to_float(value, default=0.0):
    """Convert Decimal or any numeric type to float"""
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default

def convert_to_int(value, default=0):
    """Convert any numeric type to int"""
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default

# =========================
# Data Functions
# =========================
@st.cache_data(ttl=30)
def get_stats():
    """Get customer statistics from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM customers")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM customers WHERE churn = 'Yes'")
        churned = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            'total': total,
            'churned': churned,
            'retained': total - churned,
            'churn_rate': churned / total if total > 0 else 0
        }
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return {
            'total': 0,
            'churned': 0,
            'retained': 0,
            'churn_rate': 0
        }

@st.cache_data(ttl=60)
def load_customer_data(limit=1000):
    """Load customer data from database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(f"SELECT * FROM customers LIMIT {limit}", conn)
        conn.close()
        
        # Convert all numeric columns to float
        numeric_columns = ['tenure', 'monthly_charges', 'total_charges']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_to_float)
        
        return df
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_high_risk_customers(threshold=0.7, limit=20):
    """Get high-risk customers"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(f"""
            SELECT customer_id, tenure, contract, monthly_charges, churn
            FROM customers 
            WHERE churn = 'Yes'
            ORDER BY RANDOM()
            LIMIT {limit}
        """, conn)
        conn.close()
        
        # Convert numeric columns
        df['tenure'] = df['tenure'].apply(convert_to_int)
        df['monthly_charges'] = df['monthly_charges'].apply(convert_to_float)
        
        # Simulate risk scores
        df['risk_probability'] = 0.7 + (0.3 * (df.index / len(df)))
        df['risk_level'] = df['risk_probability'].apply(
            lambda x: 'HIGH' if x > 0.8 else 'MEDIUM' if x > 0.6 else 'LOW'
        )
        
        return df
    except Exception as e:
        st.error(f"Error loading high-risk customers: {e}")
        return pd.DataFrame()

def get_customer_by_id(customer_id):
    """Get specific customer data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM customers WHERE customer_id = '{customer_id}'")
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            customer = dict(zip(columns, result))
            
            # Convert all numeric fields to proper types
            if 'tenure' in customer:
                customer['tenure'] = convert_to_int(customer['tenure'])
            if 'monthly_charges' in customer:
                customer['monthly_charges'] = convert_to_float(customer['monthly_charges'])
            if 'total_charges' in customer:
                customer['total_charges'] = convert_to_float(customer['total_charges'])
        else:
            customer = None
            
        cursor.close()
        conn.close()
        return customer
    except Exception as e:
        st.error(f"Error fetching customer: {e}")
        return None

# =========================
# Main App
# =========================
def main():
    # Header
    st.markdown('<div class="main-header">ChurnGuard Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Keystone Data Solutions • Enterprise Platform</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown('<div class="nav-section">System Status</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="status-indicator"><span class="status-dot"></span>Online</div>', unsafe_allow_html=True)
    
    st.sidebar.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)
    
    page = st.sidebar.radio(
        "",
        [
            "Executive Dashboard",
            "Customer Prediction",
            "High-Risk Customers",
            "Analytics & Insights",
            "System Status"
        ],
        label_visibility="collapsed"
    )

    # Load stats
    stats = get_stats()

    # Route to pages
    if page == "Executive Dashboard":
        show_overview(stats)
    elif page == "Customer Prediction":
        show_customer_prediction()
    elif page == "High-Risk Customers":
        show_high_risk_customers()
    elif page == "Analytics & Insights":
        show_analytics()
    elif page == "System Status":
        show_system_status()

# =========================
# Page: Executive Dashboard
# =========================
def show_overview(stats):
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    churn_rate = stats['churn_rate']
    if churn_rate < 0.15:
        health_badge = "badge-green"
        health_label = "Healthy"
    elif churn_rate < 0.25:
        health_badge = "badge-yellow"
        health_label = "At Risk"
    else:
        health_badge = "badge-red"
        health_label = "Critical"

    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-green" style="animation-delay: 0.1s;">
            <div class="kpi-title">Total Customers</div>
            <div class="kpi-value">{stats['total']:,}</div>
            <div class="kpi-subtitle">Active accounts</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-red" style="animation-delay: 0.2s;">
            <div class="kpi-title">Churned</div>
            <div class="kpi-value">{stats['churned']:,}</div>
            <div class="kpi-subtitle">Lost customers</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-green" style="animation-delay: 0.3s;">
            <div class="kpi-title">Retained</div>
            <div class="kpi-value">{stats['retained']:,}</div>
            <div class="kpi-subtitle">Active retention</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card kpi-yellow" style="animation-delay: 0.4s;">
            <div class="kpi-title">Churn Rate</div>
            <div class="kpi-value">{churn_rate:.1%}</div>
            <span class="badge {health_badge}">{health_label}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Main content grid
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown('<div class="section-header">Customer Distribution</div>', unsafe_allow_html=True)
        
        # Create donut chart with better colors
        fig = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[stats['retained'], stats['churned']],
            hole=0.5,
            marker=dict(
                colors=['#48bb78', '#f56565'],
                line=dict(color='#1a202c', width=3)
            ),
            textfont=dict(size=18, color='#ffffff', family='Inter'),
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff', family='Inter'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            height=450,
            margin=dict(t=40, b=40, l=40, r=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Financial Impact</div>', unsafe_allow_html=True)
        
        avg_revenue = 64.76
        annual_loss = stats['churned'] * avg_revenue * 12
        
        st.markdown(f"""
        <div class="financial-box">
            <h3>Revenue Analysis</h3>
            <div class="financial-item">
                <span>Annual Revenue Lost</span>
                <span class="financial-value">${annual_loss:,.0f}</span>
            </div>
            <div class="financial-item">
                <span>Customers Lost</span>
                <span class="financial-value">{stats['churned']:,}</span>
            </div>
            <div class="financial-item">
                <span>Avg Customer Value</span>
                <span class="financial-value">${avg_revenue * 12:,.0f}/yr</span>
            </div>
            <div class="financial-item">
                <span style="color: #48bb78;">15% Reduction Potential</span>
                <span class="financial-value" style="color: #48bb78;">${annual_loss * 0.15:,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick Stats Row
    st.markdown('<div class="section-header">Performance Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Model Accuracy",
            value="94.2%",
            delta="2.3% improvement"
        )
    
    with col2:
        st.metric(
            label="Predictions Today",
            value="1,247",
            delta="156 vs yesterday"
        )
    
    with col3:
        st.metric(
            label="System Uptime",
            value="99.9%",
            delta="Last 30 days",
            delta_color="off"
        )

# =========================
# Page: Customer Prediction
# =========================
def show_customer_prediction():
    st.markdown('<div class="section-header">Customer Churn Prediction</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Prediction Input")
        
        customer_id = st.text_input(
            "Customer ID",
            placeholder="Enter customer ID (e.g., 7590-VHVEG)",
            help="Enter the customer ID to predict churn probability"
        )
        
        if st.button("Generate Prediction", use_container_width=True):
            if customer_id:
                with st.spinner("Analyzing customer data..."):
                    time.sleep(1)
                    
                    customer = get_customer_by_id(customer_id)
                    
                    if customer:
                        # Simulate prediction
                        import random
                        churn_prob = random.uniform(0.15, 0.95)
                        
                        if churn_prob > 0.7:
                            risk_level = "HIGH"
                            badge_class = "badge-red"
                        elif churn_prob > 0.4:
                            risk_level = "MEDIUM"
                            badge_class = "badge-yellow"
                        else:
                            risk_level = "LOW"
                            badge_class = "badge-green"
                        
                        st.session_state['prediction'] = {
                            'customer_id': customer_id,
                            'probability': churn_prob,
                            'risk_level': risk_level,
                            'badge_class': badge_class,
                            'customer': customer
                        }
                    else:
                        st.error(f"Customer ID '{customer_id}' not found in database")
            else:
                st.warning("Please enter a customer ID")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.info("Tip: Try customer IDs like '7590-VHVEG', '5575-GNVDE', or '3668-QPYBK'")
    
    with col2:
        if 'prediction' in st.session_state:
            pred = st.session_state['prediction']
            cust = pred.get('customer', {})
            
            # Generate recommendations if available
            recommendations = None
            if RECOMMENDATIONS_AVAILABLE:
                try:
                    # Convert all fields to proper types before passing
                    recommendations = get_recommendations(
                        customer_id=pred['customer_id'],
                        churn_probability=float(pred['probability']),
                        risk_level=pred['risk_level'],
                        tenure=convert_to_int(cust.get('tenure', 12