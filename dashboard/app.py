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
    page_title="ChurnGuard Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Custom Executive CSS
# =========================
st.markdown("""
<style>
body {
    background-color: #f7f9fc;
}

.main-header {
    font-size: 3rem;
    font-weight: 800;
    color: #1f2937;
    text-align: center;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    margin-bottom: 2rem;
}

.kpi-card {
    background: white;
    padding: 1.25rem;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}

.kpi-green {
    border-top: 6px solid #16a34a;
}

.kpi-yellow {
    border-top: 6px solid #facc15;
}

.kpi-red {
    border-top: 6px solid #dc2626;
}

.kpi-title {
    font-size: 0.9rem;
    color: #6b7280;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
}

.badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-green {
    background: #dcfce7;
    color: #166534;
}

.badge-yellow {
    background: #fef9c3;
    color: #854d0e;
}

.badge-red {
    background: #fee2e2;
    color: #7f1d1d;
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

@st.cache_data
def get_stats():
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
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM customers LIMIT 1000", conn)
    conn.close()
    return df

# =========================
# Main App
# =========================
def main():
    st.markdown('<div class="main-header">ChurnGuard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Executive Customer Retention Dashboard</div>', unsafe_allow_html=True)

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", [
        "Executive Overview",
        "Customer Lookup",
        "High-Risk Customers",
        "Analytics"
    ])

    stats = get_stats()

    if page == "Executive Overview":
        show_overview(stats)
    elif page == "Customer Lookup":
        show_customer_lookup()
    elif page == "High-Risk Customers":
        show_high_risk_customers()
    elif page == "Analytics":
        show_analytics()

# =========================
# Pages
# =========================
def show_overview(stats):
    st.subheader("📌 Executive Summary")

    churn_rate = stats['churn_rate']

    if churn_rate < 0.15:
        badge = "badge-green"
        label = "Healthy"
    elif churn_rate < 0.25:
        badge = "badge-yellow"
        label = "At Risk"
    else:
        badge = "badge-red"
        label = "Critical"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-green">
            <div class="kpi-title">Total Customers</div>
            <div class="kpi-value">{stats['total']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-red">
            <div class="kpi-title">Churned Customers</div>
            <div class="kpi-value">{stats['churned']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-green">
            <div class="kpi-title">Retained Customers</div>
            <div class="kpi-value">{stats['retained']:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card kpi-yellow">
            <div class="kpi-title">Churn Health</div>
            <span class="badge {badge}">{label}</span>
            <div class="kpi-value">{churn_rate:.1%}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[stats['retained'], stats['churned']],
            hole=0.5,
            marker_colors=['#16a34a', '#dc2626']
        )])
        fig.update_layout(title="Customer Base Composition")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        avg_revenue = 64.76
        annual_loss = stats['churned'] * avg_revenue * 12

        st.markdown(f"""
        ### 💰 Financial Impact

        - **Annual Revenue Lost:** `${annual_loss:,.2f}`
        - **Customers Lost:** `{stats['churned']:,}`
        - **15% Reduction Upside:** `${annual_loss * 0.15:,.2f} / year`
        """)

def show_customer_lookup():
    st.header("🔍 Customer Lookup")
    st.info("Model integration required for live predictions.")

def show_high_risk_customers():
    st.header("🚨 High-Risk Customers")
    st.warning("This view will surface customers with highest churn probability.")

def show_analytics():
    st.header("📈 Analytics")

    df = load_customer_data()

    churn_by_contract = df.groupby('contract')['churn'].apply(
        lambda x: (x == 'Yes').mean() * 100
    ).reset_index()

    fig = px.bar(
        churn_by_contract,
        x='contract',
        y='churn',
        color='churn',
        color_continuous_scale=['#16a34a', '#facc15', '#dc2626'],
        labels={'churn': 'Churn Rate (%)'}
    )
    st.plotly_chart(fig, use_container_width=True)

# =========================
if __name__ == "__main__":
    main()
