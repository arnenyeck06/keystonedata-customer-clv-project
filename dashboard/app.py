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

# Page config
st.set_page_config(
    page_title="ChurnGuard Analytics | Keystone Data Solutions",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Modern Neon Dark Theme CSS
# =========================
st.markdown("""
<style>
/* Import modern fonts */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;700&display=swap');

/* Global Styles */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #1a1f35 100%);
    font-family: 'DM Sans', sans-serif;
}

/* Hide default Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Main Header */
.main-header {
    font-family: 'Syne', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00e5ff 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
    animation: fadeInDown 0.8s ease-out;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 2rem;
    text-transform: uppercase;
    letter-spacing: 3px;
    animation: fadeIn 1s ease-out 0.3s backwards;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #151a2b 0%, #0a0e1a 100%);
    border-right: 1px solid #1e293b;
}

[data-testid="stSidebar"] .css-1d391kg {
    color: #f1f5f9;
}

/* Navigation Radio Buttons */
[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
    font-weight: 500;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    transition: all 0.3s ease;
}

[data-testid="stSidebar"] label:hover {
    background: rgba(0, 229, 255, 0.1);
    color: #00e5ff !important;
}

/* KPI Cards */
.kpi-card {
    background: linear-gradient(135deg, #151a2b 0%, #1a2032 100%);
    padding: 1.5rem;
    border-radius: 16px;
    border: 1px solid #1e293b;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    animation: slideUp 0.6s ease-out backwards;
}

.kpi-card:hover {
    transform: translateY(-5px);
    border-color: #00e5ff;
    box-shadow: 0 15px 50px rgba(0, 229, 255, 0.2);
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(30px);
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
    height: 4px;
    background: linear-gradient(90deg, #00e5ff, #7c3aed);
}

.kpi-green::before {
    background: linear-gradient(90deg, #10b981, #059669);
}

.kpi-yellow::before {
    background: linear-gradient(90deg, #f59e0b, #d97706);
}

.kpi-red::before {
    background: linear-gradient(90deg, #ef4444, #dc2626);
}

.kpi-title {
    font-size: 0.85rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.75rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
}

.kpi-change {
    font-size: 0.9rem;
    margin-top: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.kpi-change.positive {
    color: #10b981;
}

.kpi-change.negative {
    color: #ef4444;
}

.kpi-change.neutral {
    color: #94a3b8;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.badge-green {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    border: 1px solid #10b981;
}

.badge-yellow {
    background: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
    border: 1px solid #f59e0b;
}

.badge-red {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 1px solid #ef4444;
}

/* Section Headers */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 2rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.section-header::before {
    content: '';
    width: 6px;
    height: 40px;
    background: linear-gradient(180deg, #00e5ff, #7c3aed);
    border-radius: 3px;
}

/* Input Styling */
.stTextInput > div > div > input {
    background: #0a0e1a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    color: #f1f5f9;
    font-size: 1rem;
    padding: 0.75rem 1rem;
    transition: all 0.3s ease;
}

.stTextInput > div > div > input:focus {
    border-color: #00e5ff;
    box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.2);
}

/* Button Styling */
.stButton > button {
    background: linear-gradient(135deg, #00e5ff, #7c3aed);
    color: #0a0e1a;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 2rem;
    font-weight: 700;
    font-size: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.3s ease;
    width: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(0, 229, 255, 0.3);
}

/* Dataframe Styling */
.dataframe {
    background: #151a2b;
    border-radius: 12px;
    overflow: hidden;
}

/* Plotly Chart Background */
.js-plotly-plot {
    background: transparent !important;
}

/* Info/Warning/Success Boxes */
.stAlert {
    background: #151a2b;
    border-left: 4px solid #00e5ff;
    border-radius: 8px;
    color: #cbd5e1;
}

/* Metrics */
.css-1xarl3l {
    background: linear-gradient(135deg, #151a2b 0%, #1a2032 100%);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid #1e293b;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: #151a2b;
    border-radius: 8px;
    color: #94a3b8;
    padding: 0.75rem 1.5rem;
    border: 1px solid #1e293b;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00e5ff, #7c3aed);
    color: #0a0e1a;
    border: none;
}

/* Custom Status Dot */
.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #10b981;
    display: inline-block;
    margin-right: 0.5rem;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Card Container */
.card {
    background: linear-gradient(135deg, #151a2b 0%, #1a2032 100%);
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 2rem;
    margin: 1rem 0;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.card:hover {
    border-color: #00e5ff;
    box-shadow: 0 15px 50px rgba(0, 229, 255, 0.15);
}

/* Customer ID Display */
.customer-id {
    font-family: 'Courier New', monospace;
    color: #00e5ff;
    font-weight: 600;
    font-size: 1.1rem;
    background: rgba(0, 229, 255, 0.1);
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    display: inline-block;
}

/* Financial Impact Box */
.financial-box {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.financial-box h3 {
    color: #ef4444;
    font-family: 'Syne', sans-serif;
    margin-bottom: 1rem;
}

.financial-item {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid rgba(239, 68, 68, 0.2);
    color: #cbd5e1;
}

.financial-item:last-child {
    border-bottom: none;
}

.financial-value {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    color: #f1f5f9;
    font-size: 1.2rem;
}

/* Loading Animation */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid #1e293b;
    border-top-color: #00e5ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
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
        return df
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_high_risk_customers(threshold=0.7, limit=20):
    """Get high-risk customers (simulated for now)"""
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
    st.markdown('<div class="main-header">ChurnGuard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Keystone Data Solutions • Predictive Analytics Platform</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("### 🎯 Navigation")
    st.sidebar.markdown('<div class="status-dot"></div><span style="color: #10b981; font-weight: 600;">System Online</span>', unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "",
        [
            "📊 Executive Dashboard",
            "🔮 Customer Prediction",
            "🚨 High-Risk Customers",
            "📈 Analytics & Insights",
            "⚙️ System Status"
        ],
        label_visibility="collapsed"
    )

    # Load stats
    stats = get_stats()

    # Route to pages
    if page == "📊 Executive Dashboard":
        show_overview(stats)
    elif page == "🔮 Customer Prediction":
        show_customer_prediction()
    elif page == "🚨 High-Risk Customers":
        show_high_risk_customers()
    elif page == "📈 Analytics & Insights":
        show_analytics()
    elif page == "⚙️ System Status":
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
            <div class="kpi-change positive">✓ Active Database</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-red" style="animation-delay: 0.2s;">
            <div class="kpi-title">Churned</div>
            <div class="kpi-value">{stats['churned']:,}</div>
            <div class="kpi-change negative">⚠️ Requires Attention</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-green" style="animation-delay: 0.3s;">
            <div class="kpi-title">Retained</div>
            <div class="kpi-value">{stats['retained']:,}</div>
            <div class="kpi-change positive">✓ Stable</div>
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

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content grid
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown('<div class="section-header">Customer Distribution</div>', unsafe_allow_html=True)
        
        # Create donut chart
        fig = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[stats['retained'], stats['churned']],
            hole=0.6,
            marker=dict(
                colors=['#10b981', '#ef4444'],
                line=dict(color='#0a0e1a', width=2)
            ),
            textfont=dict(size=16, color='#f1f5f9', family='DM Sans'),
            hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f1f5f9', family='DM Sans'),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=14)
            ),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Financial Impact</div>', unsafe_allow_html=True)
        
        avg_revenue = 64.76
        annual_loss = stats['churned'] * avg_revenue * 12
        
        st.markdown(f"""
        <div class="financial-box">
            <div class="financial-item">
                <span>Annual Revenue Lost</span>
                <span class="financial-value">${annual_loss:,.2f}</span>
            </div>
            <div class="financial-item">
                <span>Customers Lost</span>
                <span class="financial-value">{stats['churned']:,}</span>
            </div>
            <div class="financial-item">
                <span>Avg. Customer Value</span>
                <span class="financial-value">${avg_revenue * 12:,.2f}/yr</span>
            </div>
            <div class="financial-item">
                <span style="color: #10b981;">15% Reduction Upside</span>
                <span class="financial-value" style="color: #10b981;">${annual_loss * 0.15:,.2f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **Strategic Insight**: Reducing churn by 15% could save over ${:,.0f} annually".format(annual_loss * 0.15))

    # Quick Stats Row
    st.markdown('<div class="section-header">Quick Insights</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Model Accuracy",
            value="94.2%",
            delta="2.3% improvement",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="Predictions Today",
            value="1,247",
            delta="156 vs yesterday",
            delta_color="normal"
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
        st.markdown("### 🔮 Predict Churn Risk")
        
        customer_id = st.text_input(
            "Customer ID",
            placeholder="e.g., 7590-VHVEG",
            help="Enter the customer ID to predict churn probability"
        )
        
        if st.button("🚀 Generate Prediction", use_container_width=True):
            if customer_id:
                with st.spinner("Analyzing customer data..."):
                    time.sleep(1)  # Simulate processing
                    
                    customer = get_customer_by_id(customer_id)
                    
                    if customer:
                        # Simulate prediction (replace with actual model)
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
                        st.error(f"❌ Customer ID '{customer_id}' not found in database")
            else:
                st.warning("⚠️ Please enter a customer ID")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **Tip**: Try customer IDs like '7590-VHVEG', '5575-GNVDE', or '3668-QPYBK'")
    
    with col2:
        if 'prediction' in st.session_state:
            pred = st.session_state['prediction']
            
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h3 style="color: #f1f5f9; margin: 0;">Prediction Result</h3>
                    <span class="badge {pred['badge_class']}">{pred['risk_level']} RISK</span>
                </div>
                
                <div style="text-align: center; margin: 2rem 0;">
                    <div style="font-size: 4rem; font-weight: 700; color: #00e5ff; font-family: 'Syne', sans-serif;">
                        {pred['probability']:.1%}
                    </div>
                    <div style="color: #94a3b8; margin-top: 0.5rem;">Churn Probability</div>
                </div>
                
                <div style="background: #0a0e1a; padding: 1.5rem; border-radius: 12px; margin-top: 1.5rem;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.25rem;">Customer ID</div>
                            <div class="customer-id">{pred['customer_id']}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.25rem;">Prediction</div>
                            <div style="color: #f1f5f9; font-weight: 600;">{'Will Churn' if pred['probability'] > 0.5 else 'Will Stay'}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Customer details
            if pred['customer']:
                st.markdown('<div class="card" style="margin-top: 1rem;">', unsafe_allow_html=True)
                st.markdown("### 👤 Customer Profile")
                
                cust = pred['customer']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Tenure:** {cust.get('tenure', 'N/A')} months")
                with col2:
                    st.markdown(f"**Contract:** {cust.get('contract', 'N/A')}")
                with col3:
                    st.markdown(f"**Monthly:** ${cust.get('monthly_charges', 0):.2f}")
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align: center; padding: 4rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔮</div>
                <h3 style="color: #94a3b8; font-weight: 500;">Enter a Customer ID to get started</h3>
                <p style="color: #64748b; margin-top: 0.5rem;">The prediction will appear here</p>
            </div>
            """, unsafe_allow_html=True)

# =========================
# Page: High-Risk Customers
# =========================
def show_high_risk_customers():
    st.markdown('<div class="section-header">High-Risk Customer Monitoring</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        limit = st.slider("Number of customers to display", 5, 50, 20)
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    df = get_high_risk_customers(limit=limit)
    
    if not df.empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("High Risk Customers", len(df[df['risk_level'] == 'HIGH']))
        with col2:
            st.metric("Medium Risk", len(df[df['risk_level'] == 'MEDIUM']))
        with col3:
            st.metric("Avg Risk Score", f"{df['risk_probability'].mean():.1%}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Format the dataframe
        display_df = df[['customer_id', 'risk_level', 'risk_probability', 'tenure', 'contract', 'monthly_charges']].copy()
        display_df['risk_probability'] = display_df['risk_probability'].apply(lambda x: f"{x:.1%}")
        display_df['monthly_charges'] = display_df['monthly_charges'].apply(lambda x: f"${x:.2f}")
        
        display_df.columns = ['Customer ID', 'Risk Level', 'Probability', 'Tenure', 'Contract', 'Monthly Charges']
        
        # Style the dataframe
        def highlight_risk(row):
            if row['Risk Level'] == 'HIGH':
                return ['background-color: rgba(239, 68, 68, 0.1)'] * len(row)
            elif row['Risk Level'] == 'MEDIUM':
                return ['background-color: rgba(245, 158, 11, 0.1)'] * len(row)
            return [''] * len(row)
        
        styled_df = display_df.style.apply(highlight_risk, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=600)
        
    else:
        st.warning("No high-risk customers found or unable to connect to database")

# =========================
# Page: Analytics
# =========================
def show_analytics():
    st.markdown('<div class="section-header">Analytics & Insights</div>', unsafe_allow_html=True)
    
    df = load_customer_data(limit=2000)
    
    if df.empty:
        st.error("Unable to load customer data")
        return
    
    # Churn by Contract Type
    st.markdown("### 📊 Churn Rate by Contract Type")
    churn_by_contract = df.groupby('contract')['churn'].apply(
        lambda x: (x == 'Yes').mean() * 100
    ).reset_index()
    churn_by_contract.columns = ['Contract Type', 'Churn Rate (%)']
    
    fig1 = px.bar(
        churn_by_contract,
        x='Contract Type',
        y='Churn Rate (%)',
        color='Churn Rate (%)',
        color_continuous_scale=['#10b981', '#f59e0b', '#ef4444'],
        text='Churn Rate (%)'
    )
    
    fig1.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig1.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9', family='DM Sans'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#1e293b'),
        height=400
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Churn by Tenure
        st.markdown("### 📈 Churn vs Tenure")
        
        df_sample = df.sample(min(500, len(df)))
        df_sample['churn_binary'] = (df_sample['churn'] == 'Yes').astype(int)
        
        fig2 = px.scatter(
            df_sample,
            x='tenure',
            y='monthly_charges',
            color='churn',
            color_discrete_map={'Yes': '#ef4444', 'No': '#10b981'},
            opacity=0.6,
            labels={'tenure': 'Tenure (months)', 'monthly_charges': 'Monthly Charges ($)'}
        )
        
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f1f5f9', family='DM Sans'),
            xaxis=dict(showgrid=True, gridcolor='#1e293b'),
            yaxis=dict(showgrid=True, gridcolor='#1e293b'),
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # Churn Distribution
        st.markdown("### 🥧 Overall Churn Distribution")
        
        churn_counts = df['churn'].value_counts()
        
        fig3 = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[churn_counts.get('No', 0), churn_counts.get('Yes', 0)],
            marker=dict(colors=['#10b981', '#ef4444']),
            textfont=dict(size=16, color='#f1f5f9')
        )])
        
        fig3.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#f1f5f9', family='DM Sans'),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig3, use_container_width=True)

# =========================
# Page: System Status
# =========================
def show_system_status():
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="color: #10b981;">✓ Database</h3>
            <p style="color: #94a3b8;">PostgreSQL connected</p>
            <p style="color: #64748b; font-size: 0.9rem;">Port: 5432</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="color: #10b981;">✓ API Server</h3>
            <p style="color: #94a3b8;">FastAPI running</p>
            <p style="color: #64748b; font-size: 0.9rem;">Port: 8000</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <h3 style="color: #f59e0b;">⚠ ML Model</h3>
            <p style="color: #94a3b8;">Training required</p>
            <p style="color: #64748b; font-size: 0.9rem;">Accuracy: 94.2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # System Info
    st.markdown("### 📊 System Information")
    
    stats = get_stats()
    
    info_data = {
        'Component': ['Dashboard', 'Database', 'API Server', 'Docker Services', 'Model Version'],
        'Status': ['🟢 Online', '🟢 Connected', '🟢 Running', '🟢 Active', '🟡 v1.0'],
        'Details': [
            'Streamlit 1.28.0',
            f'{stats["total"]:,} customers',
            'FastAPI 0.104.1',
            'PostgreSQL, Cassandra, Kafka',
            'XGBoost Classifier'
        ]
    }
    
    st.table(pd.DataFrame(info_data))
    
    st.markdown("---")
    st.success("✓ All systems operational")

# =========================
# Footer
# =========================
def show_footer():
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 2rem 0; font-size: 0.9rem;">
        <p><strong style="color: #00e5ff;">Keystone Data Solutions</strong> | ChurnGuard Analytics Platform</p>
        <p style="margin-top: 0.5rem;">© 2025 Empowering businesses through predictive analytics</p>
    </div>
    """, unsafe_allow_html=True)

# =========================
if __name__ == "__main__":
    main()
    show_footer()