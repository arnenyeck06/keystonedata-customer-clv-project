import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

# Page config
st.set_page_config(
    page_title="ChurnGuard Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .high-risk {
        color: #d62728;
        font-weight: bold;
    }
    .medium-risk {
        color: #ff7f0e;
        font-weight: bold;
    }
    .low-risk {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

@st.cache_data
def get_stats():
    """Get database statistics"""
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

@st.cache_data
def load_customer_data():
    """Load customer data from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    query = "SELECT * FROM customers LIMIT 1000"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def main():
    # Header
    st.markdown('<h1 class="main-header">ChurnGuard Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Predictive Customer Churn Analysis Platform")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", [
        "Overview",
        "Customer Lookup",
        "High-Risk Customers",
        "Analytics"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.info("**ChurnGuard Analytics**\n\nPredicting customer churn with machine learning")
    
    # Load data
    try:
        stats = get_stats()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    
    # Page routing
    if page == "Overview":
        show_overview(stats)
    elif page == "Customer Lookup":
        show_customer_lookup()
    elif page == "High-Risk Customers":
        show_high_risk_customers()
    elif page == "Analytics":
        show_analytics()

def show_overview(stats):
    """Overview page with key metrics"""
    st.header("Platform Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Customers",
            value=f"{stats['total']:,}"
        )
    
    with col2:
        st.metric(
            label="Churned Customers",
            value=f"{stats['churned']:,}",
            delta=f"{stats['churn_rate']:.1%}",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Retained Customers",
            value=f"{stats['retained']:,}",
            delta=f"{(1-stats['churn_rate']):.1%}",
            delta_color="normal"
        )
    
    with col4:
        at_risk = int(stats['total'] * 0.15)
        st.metric(
            label="Estimated At-Risk",
            value=f"{at_risk:,}",
            delta="15% of total"
        )
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Churn Distribution")
        fig = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[stats['retained'], stats['churned']],
            hole=0.4,
            marker_colors=['#2ca02c', '#d62728']
        )])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Business Impact")
        
        avg_revenue = 64.76
        annual_revenue_loss = stats['churned'] * avg_revenue * 12
        
        st.markdown(f"""
        **Current Churn Impact:**
        - Monthly Revenue Loss: **${stats['churned'] * avg_revenue:,.2f}**
        - Annual Revenue Loss: **${annual_revenue_loss:,.2f}**
        - Customers Lost: **{stats['churned']:,}**
        
        **Potential Savings (15% reduction):**
        - Customers Saved: **{int(stats['churned'] * 0.15):,}**
        - Revenue Saved: **${annual_revenue_loss * 0.15:,.2f}/year**
        """)

def show_customer_lookup():
    """Customer lookup page"""
    st.header("Customer Churn Prediction")
    
    st.markdown("Enter a customer ID to get churn prediction and risk analysis.")
    
    customer_id = st.text_input("Customer ID", value="7590-VHVEG")
    
    if st.button("Predict Churn", type="primary"):
        st.info("Prediction feature requires trained model. Please run training script first.")

def show_high_risk_customers():
    """High-risk customers page"""
    st.header("High-Risk Customers")
    
    st.markdown("Customers with high churn probability requiring immediate attention.")
    st.info("This feature requires trained model integration.")

def show_analytics():
    """Analytics page"""
    st.header("Customer Analytics")
    
    try:
        df = load_customer_data()
        
        # Churn by contract
        st.subheader("Churn Rate by Contract Type")
        churn_by_contract = df.groupby('contract')['churn'].apply(
            lambda x: (x == 'Yes').sum() / len(x) * 100
        ).reset_index()
        churn_by_contract.columns = ['Contract', 'Churn Rate (%)']
        
        fig = px.bar(churn_by_contract, x='Contract', y='Churn Rate (%)', 
                     color='Churn Rate (%)', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly charges distribution
        st.subheader("Monthly Charges Distribution")
        fig = px.histogram(df, x='monthly_charges', color='churn', 
                         barmode='overlay', nbins=30,
                         color_discrete_map={'Yes': '#d62728', 'No': '#2ca02c'})
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

if __name__ == "__main__":
    main()
