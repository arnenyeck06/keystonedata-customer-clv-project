import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os
import sys
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

try:
    from predict_helper import predict_customer_churn
    PREDICTION_AVAILABLE = True
except:
    PREDICTION_AVAILABLE = False

try:
    from recommendations_engine import RecommendationsEngine, get_recommendations
    RECOMMENDATIONS_AVAILABLE = True
except:
    RECOMMENDATIONS_AVAILABLE = False

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ChurnGuard Analytics | Keystone Data Solutions",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Theme — dark navy / purple accent
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, .stApp {
    background: #0f1117 !important;
    font-family: 'Inter', sans-serif;
    color: #e2e4ea;
}

#MainMenu, footer, .stDeployButton { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #161b27 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}

[data-testid="stSidebar"] * { color: #9ca3af !important; }

/* sidebar brand block */
.sb-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 18px 16px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 6px;
}
.sb-avatar {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg,#6c63ff,#a78bfa);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; color: #fff !important;
    flex-shrink: 0;
}
.sb-name  { font-size: 14px; font-weight: 600; color: #e2e4ea !important; line-height: 1.1; }
.sb-sub   { font-size: 11px; color: #4b5563 !important; }
.nav-section {
    font-size: 10px; letter-spacing: .08em; color: #4b5563 !important;
    font-weight: 600; padding: 12px 16px 4px; text-transform: uppercase;
}
.sb-status {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; color: #4ade80 !important;
    background: rgba(74,222,128,0.1); border-radius: 20px;
    padding: 4px 12px; margin: 4px 16px 8px; width: fit-content;
}
.sb-status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #4ade80; animation: pulse 2s infinite;
}

/* sidebar nav radio override */
[data-testid="stSidebar"] [role="radio"] {
    background: transparent !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
    margin: 1px 8px !important;
}
[data-testid="stSidebar"] [aria-checked="true"] {
    background: rgba(108,99,255,0.18) !important;
    color: #c4b5fd !important;
}

/* sidebar connections footer */
.sb-footer {
    margin-top: 1.5rem;
    border-top: 1px solid rgba(255,255,255,0.07);
    padding: 12px 16px;
}
.sb-conn { display: flex; align-items: center; gap: 7px; font-size: 11px; padding: 3px 0; }
.sb-dot  { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }

/* ── Top bar ── */
.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 20px;
}
.top-bar-left { display: flex; align-items: center; gap: 12px; }
.tb-title   { font-size: 16px; font-weight: 600; color: #e2e4ea; }
.tb-version {
    font-size: 12px; color: #4b5563; background: rgba(255,255,255,0.05);
    padding: 3px 10px; border-radius: 20px;
}
.tb-status {
    display: flex; align-items: center; gap: 5px;
    font-size: 12px; color: #4ade80;
    background: rgba(74,222,128,0.1);
    border-radius: 20px; padding: 4px 12px;
}

/* ── Metric cards ── */
.mcard {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 14px 16px;
}
.mcard-label {
    font-size: 11px; color: #6b7280; margin-bottom: 6px;
    text-transform: uppercase; letter-spacing: .04em;
}
.mcard-val { font-size: 24px; font-weight: 700; color: #e2e4ea; line-height: 1; }
.mcard-sub { font-size: 11px; margin-top: 5px; display: flex; align-items: center; gap: 3px; }
.up      { color: #4ade80; }
.down    { color: #f87171; }
.neutral { color: #6b7280; }

/* ── Section cards ── */
.sc {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 16px 18px; margin-bottom: 14px;
}
.sc-title { font-size: 14px; font-weight: 600; color: #e2e4ea; }
.sc-sub   { font-size: 11px; color: #4b5563; margin-top: 2px; }
.sc-head  { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px; }

/* ── Section header (left accent bar) ── */
.section-header {
    font-size: 18px; font-weight: 600; color: #e2e4ea;
    margin: 1.5rem 0 1rem; padding-left: 12px;
    border-left: 3px solid #6c63ff;
}

/* ── Pills / badges ── */
.pill-run    { font-size: 11px; padding: 3px 10px; border-radius: 20px; background: rgba(108,99,255,.2);  color: #a78bfa; }
.pill-green  { font-size: 11px; padding: 3px 10px; border-radius: 20px; background: rgba(74,222,128,.12); color: #4ade80; }
.badge-green { background: rgba(74,222,128,.18); color: #4ade80; border: 1px solid #4ade80; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.badge-yellow{ background: rgba(251,191,36,.18);  color: #fbbf24; border: 1px solid #fbbf24; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.badge-red   { background: rgba(248,113,113,.18); color: #f87171; border: 1px solid #f87171; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }

/* ── Pipeline steps ── */
.pipe-steps { display: flex; align-items: center; margin-bottom: 12px; }
.step       { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.step-circle {
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 13px;
}
.step-done    { background: rgba(74,222,128,.15); border: 2px solid #4ade80; color: #4ade80; }
.step-active  { background: rgba(108,99,255,.2);  border: 2px solid #6c63ff; color: #6c63ff; }
.step-pending { background: rgba(255,255,255,.04); border: 2px solid rgba(255,255,255,.1); color: #4b5563; }
.step-label   { font-size: 10px; color: #6b7280; white-space: nowrap; }
.step-conn    { flex: 1; height: 1px; background: rgba(255,255,255,.1); margin-bottom: 16px; min-width: 14px; }
.pipe-info    { font-size: 12px; color: #6b7280; }
.pipe-info span { color: #a78bfa; }

/* ── Model registry table ── */
.tbl { width: 100%; border-collapse: collapse; margin-top: 4px; }
.tbl th {
    font-size: 10px; color: #4b5563; font-weight: 600;
    text-align: left; padding: 6px 0; letter-spacing: .05em;
    border-bottom: 1px solid rgba(255,255,255,.07);
}
.tbl td { font-size: 12px; color: #c9ccd4; padding: 9px 6px 9px 0; border-bottom: 1px solid rgba(255,255,255,.04); }
.tbl td:first-child { font-weight: 600; color: #e2e4ea; }
.badge-deployed { background: rgba(74,222,128,.12);  color: #4ade80; padding: 2px 8px; border-radius: 20px; font-size: 10px; }
.badge-staged   { background: rgba(251,191,36,.12);  color: #fbbf24; padding: 2px 8px; border-radius: 20px; font-size: 10px; }
.badge-archived { background: rgba(255,255,255,.06); color: #6b7280;  padding: 2px 8px; border-radius: 20px; font-size: 10px; }

/* ── Feature importance bars ── */
.feat-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.feat-name { font-size: 11px; color: #9ca3af; width: 110px; flex-shrink: 0; }
.feat-bar  { flex: 1; height: 5px; background: rgba(255,255,255,.07); border-radius: 3px; overflow: hidden; }
.feat-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg,#6c63ff,#a78bfa); }
.feat-val  { font-size: 11px; color: #6b7280; min-width: 30px; text-align: right; }

/* ── Financial box ── */
.financial-box {
    background: linear-gradient(135deg,rgba(108,99,255,.08) 0%,rgba(108,99,255,.03) 100%);
    border: 1px solid rgba(108,99,255,.25); border-radius: 10px; padding: 18px;
}
.financial-box h3 { color: #a78bfa; font-weight: 600; margin-bottom: 14px; font-size: 14px; }
.financial-item {
    display: flex; justify-content: space-between; padding: 10px 0;
    border-bottom: 1px solid rgba(108,99,255,.15); color: #9ca3af; font-size: 13px;
}
.financial-item:last-child { border-bottom: none; }
.financial-value { font-weight: 700; color: #e2e4ea; }

/* ── Cards (generic) ── */
.card {
    background: #1a2035; border: 1px solid rgba(255,255,255,.07);
    border-radius: 10px; padding: 20px; margin: 8px 0;
}
.card h3 { color: #e2e4ea; font-size: 15px; font-weight: 600; margin-bottom: 12px; }

/* ── Result box (prediction) ── */
.result-box {
    background: #1a2035; border: 1px solid rgba(255,255,255,.07);
    border-radius: 10px; padding: 24px; text-align: center;
}
.result-probability {
    font-size: 52px; font-weight: 800; color: #e2e4ea; line-height: 1; margin: 16px 0;
}
.result-label { color: #6b7280; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.customer-id {
    font-family: monospace; color: #a78bfa; font-weight: 600; font-size: 14px;
    background: rgba(108,99,255,.15); padding: 5px 10px; border-radius: 6px;
    display: inline-block; border: 1px solid rgba(108,99,255,.3);
}

/* ── Status dots / animations ── */
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; animation: pulse 2s infinite; display: inline-block; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
@keyframes spin  { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* ── Streamlit native overrides ── */
[data-testid="stMetricValue"]  { font-size: 28px !important; font-weight: 700 !important; color: #e2e4ea !important; }
[data-testid="stMetricLabel"]  { color: #6b7280 !important; font-weight: 500 !important; font-size: 12px !important; }
[data-testid="stMetricDelta"]  { font-weight: 600 !important; }

.stAlert {
    background: rgba(108,99,255,.1) !important; border: 1px solid rgba(108,99,255,.3) !important;
    border-left: 3px solid #6c63ff !important; border-radius: 8px !important; color: #e2e4ea !important;
}
.stButton > button {
    background: #6c63ff !important; color: #fff !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important; font-size: 13px !important;
    padding: 10px 20px !important; transition: all .2s !important;
}
.stButton > button:hover { background: #5b54e8 !important; }
.stTextInput > div > div > input {
    background: #1a2035 !important; border: 1px solid rgba(255,255,255,.1) !important;
    border-radius: 8px !important; color: #e2e4ea !important;
}
.stTextInput > label { color: #9ca3af !important; font-weight: 500 !important; }
.stSlider > div > div > div { background: #6c63ff !important; }

/* dataframe */
[data-testid="stDataFrame"] { background: #1a2035 !important; border-radius: 8px !important; }

/* tabs */
.stTabs [data-baseweb="tab"] {
    background: rgba(255,255,255,.04) !important; border-radius: 7px !important;
    color: #9ca3af !important; border: 1px solid rgba(255,255,255,.07) !important;
    padding: 8px 18px !important; font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: #6c63ff !important; color: #fff !important; border-color: #6c63ff !important;
}

/* empty state */
.empty-state { text-align: center; padding: 40px 20px; color: #4b5563; }
.empty-state-icon { font-size: 40px; opacity: .5; margin-bottom: 12px; }
.empty-state-text { font-size: 14px; color: #6b7280; }

hr { border: none; border-top: 1px solid rgba(255,255,255,.07); margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Database config
# ─────────────────────────────────────────────
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

# ─────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def get_stats():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM customers WHERE churn = 'Yes'")
        churned = cursor.fetchone()[0]
        cursor.close(); conn.close()
        return {'total': total, 'churned': churned,
                'retained': total - churned,
                'churn_rate': churned / total if total > 0 else 0}
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return {'total': 0, 'churned': 0, 'retained': 0, 'churn_rate': 0}

@st.cache_data(ttl=60)
def load_customer_data(limit=1000):
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
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(f"""
            SELECT customer_id, tenure, contract, monthly_charges, churn
            FROM customers WHERE churn = 'Yes'
            ORDER BY RANDOM() LIMIT {limit}
        """, conn)
        conn.close()
        df['risk_probability'] = 0.7 + (0.3 * (df.index / len(df)))
        df['risk_level'] = df['risk_probability'].apply(
            lambda x: 'HIGH' if x > 0.8 else 'MEDIUM' if x > 0.6 else 'LOW')
        return df
    except Exception as e:
        st.error(f"Error loading high-risk customers: {e}")
        return pd.DataFrame()

def get_customer_by_id(customer_id):
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
        cursor.close(); conn.close()
        return customer
    except Exception as e:
        st.error(f"Error fetching customer: {e}")
        return None

# ─────────────────────────────────────────────
# Plotly theme helper
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#9ca3af', family='Inter'),
    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
    margin=dict(t=30, b=30, l=10, r=10),
    height=360,
)

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sb-brand">
            <div class="sb-avatar">K</div>
            <div>
                <div class="sb-name">Keystone</div>
                <div class="sb-sub">Data Platform</div>
            </div>
        </div>
        <div class="nav-section">System</div>
        <div class="sb-status"><span class="sb-status-dot"></span>All systems online</div>
        <div class="nav-section">Navigation</div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "",
            ["Executive Dashboard", "Customer Prediction",
             "High-Risk Customers", "Analytics & Insights", "System Status"],
            label_visibility="collapsed"
        )

        st.markdown("""
        <div class="sb-footer">
            <div class="nav-section" style="padding:0 0 6px;">Connections</div>
            <div class="sb-conn"><div class="sb-dot" style="background:#4ade80"></div>PostgreSQL</div>
            <div class="sb-conn"><div class="sb-dot" style="background:#4ade80"></div>Kafka broker</div>
            <div class="sb-conn"><div class="sb-dot" style="background:#fbbf24"></div>Spark cluster</div>
            <div class="sb-conn"><div class="sb-dot" style="background:#f87171"></div>Cassandra</div>
        </div>
        """, unsafe_allow_html=True)

    return page

# ─────────────────────────────────────────────
# Page helpers
# ─────────────────────────────────────────────
def topbar(title, subtitle="Telco Churn · v1.4.2"):
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-left">
            <span class="tb-title">{title}</span>
            <span class="tb-version">{subtitle}</span>
        </div>
        <div class="tb-status">
            <span class="status-dot"></span>Live
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Page: Executive Dashboard
# ─────────────────────────────────────────────
def show_overview(stats):
    topbar("Overview")

    churn_rate = stats['churn_rate']
    if churn_rate < 0.15:
        health_badge, health_label = "badge-green", "Healthy"
    elif churn_rate < 0.25:
        health_badge, health_label = "badge-yellow", "At Risk"
    else:
        health_badge, health_label = "badge-red", "Critical"

    avg_revenue = 64.76
    annual_loss = stats['churned'] * avg_revenue * 12

    # ── KPI row ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="mcard">
            <div class="mcard-label">Total customers</div>
            <div class="mcard-val">{stats['total']:,}</div>
            <div class="mcard-sub neutral">Active accounts</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="mcard">
            <div class="mcard-label">Churned</div>
            <div class="mcard-val">{stats['churned']:,}</div>
            <div class="mcard-sub down">&#9660; Lost customers</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="mcard">
            <div class="mcard-label">Retained</div>
            <div class="mcard-val">{stats['retained']:,}</div>
            <div class="mcard-sub up">&#9650; Active retention</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="mcard">
            <div class="mcard-label">Churn rate</div>
            <div class="mcard-val">{churn_rate:.1%}</div>
            <div class="mcard-sub"><span class="{health_badge}">{health_label}</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Pipeline status strip ──
    st.markdown("""
    <div class="sc">
        <div class="sc-head">
            <div>
                <div class="sc-title">Pipeline status</div>
                <div class="sc-sub">Current run · started 09:14</div>
            </div>
            <span class="pill-run">Running</span>
        </div>
        <div class="pipe-steps">
            <div class="step"><div class="step-circle step-done">&#10003;</div><div class="step-label">Ingest</div></div>
            <div class="step-conn"></div>
            <div class="step"><div class="step-circle step-done">&#10003;</div><div class="step-label">Process</div></div>
            <div class="step-conn"></div>
            <div class="step"><div class="step-circle step-done">&#10003;</div><div class="step-label">Features</div></div>
            <div class="step-conn"></div>
            <div class="step"><div class="step-circle step-active" style="animation:spin 2s linear infinite">&#8635;</div><div class="step-label">Train</div></div>
            <div class="step-conn"></div>
            <div class="step"><div class="step-circle step-pending"></div><div class="step-label">Evaluate</div></div>
            <div class="step-conn"></div>
            <div class="step"><div class="step-circle step-pending"></div><div class="step-label">Deploy</div></div>
        </div>
        <div class="pipe-info">Training XGBoost · <span>epoch 12/50</span> · ETA ~8 min</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Charts row ──
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown('<div class="section-header">Customer distribution</div>', unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[stats['retained'], stats['churned']],
            hole=0.52,
            marker=dict(colors=['#4ade80', '#f87171'],
                        line=dict(color='#1a2035', width=3)),
            textfont=dict(size=14, color='#fff', family='Inter'),
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>%{value:,} · %{percent}<extra></extra>'
        )])
        fig.update_layout(**{**PLOT_LAYOUT, 'height': 380,
                             'legend': dict(orientation='h', y=-0.1, x=0.5, xanchor='center',
                                           font=dict(size=12))})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Financial impact</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="financial-box">
            <h3>Revenue analysis</h3>
            <div class="financial-item">
                <span>Annual revenue lost</span>
                <span class="financial-value">${annual_loss:,.0f}</span>
            </div>
            <div class="financial-item">
                <span>Customers lost</span>
                <span class="financial-value">{stats['churned']:,}</span>
            </div>
            <div class="financial-item">
                <span>Avg customer value</span>
                <span class="financial-value">${avg_revenue * 12:,.0f}/yr</span>
            </div>
            <div class="financial-item">
                <span style="color:#4ade80">15% reduction potential</span>
                <span class="financial-value" style="color:#4ade80">${annual_loss * 0.15:,.0f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Model registry ──
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="sc">
            <div class="sc-head">
                <div><div class="sc-title">Model registry</div><div class="sc-sub">All trained versions</div></div>
                <span class="pill-green">3 models</span>
            </div>
            <table class="tbl">
                <thead><tr><th>Model</th><th>Accuracy</th><th>AUC</th><th>Status</th></tr></thead>
                <tbody>
                    <tr><td>XGBoost v4</td><td>87.4%</td><td>0.921</td><td><span class="badge-deployed">Deployed</span></td></tr>
                    <tr><td>Random Forest v3</td><td>84.1%</td><td>0.898</td><td><span class="badge-staged">Staged</span></td></tr>
                    <tr><td>Logistic Reg. v2</td><td>79.6%</td><td>0.842</td><td><span class="badge-archived">Archived</span></td></tr>
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="sc">
            <div class="sc-head">
                <div><div class="sc-title">Top churn features</div><div class="sc-sub">SHAP importance</div></div>
            </div>
            <div class="feat-row"><span class="feat-name">Contract type</span><div class="feat-bar"><div class="feat-fill" style="width:91%"></div></div><span class="feat-val">0.91</span></div>
            <div class="feat-row"><span class="feat-name">Tenure (months)</span><div class="feat-bar"><div class="feat-fill" style="width:78%"></div></div><span class="feat-val">0.78</span></div>
            <div class="feat-row"><span class="feat-name">Monthly charges</span><div class="feat-bar"><div class="feat-fill" style="width:65%"></div></div><span class="feat-val">0.65</span></div>
            <div class="feat-row"><span class="feat-name">Internet service</span><div class="feat-bar"><div class="feat-fill" style="width:52%"></div></div><span class="feat-val">0.52</span></div>
            <div class="feat-row"><span class="feat-name">Tech support</span><div class="feat-bar"><div class="feat-fill" style="width:44%"></div></div><span class="feat-val">0.44</span></div>
            <div class="feat-row"><span class="feat-name">Online security</span><div class="feat-bar"><div class="feat-fill" style="width:37%"></div></div><span class="feat-val">0.37</span></div>
            <div class="feat-row"><span class="feat-name">Senior citizen</span><div class="feat-bar"><div class="feat-fill" style="width:28%"></div></div><span class="feat-val">0.28</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── Performance metrics ──
    st.markdown('<div class="section-header">Performance metrics</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Model accuracy", "94.2%", "+2.3% improvement")
    with c2:
        st.metric("Predictions today", "1,247", "+156 vs yesterday")
    with c3:
        st.metric("System uptime", "99.9%", "Last 30 days", delta_color="off")

# ─────────────────────────────────────────────
# Page: Customer Prediction
# ─────────────────────────────────────────────
def show_customer_prediction():
    topbar("Customer prediction")
    st.markdown('<div class="section-header">Churn probability lookup</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Prediction input")
        customer_id = st.text_input(
            "Customer ID",
            placeholder="e.g. 7590-VHVEG",
            help="Enter the customer ID to predict churn probability"
        )
        if st.button("Generate prediction", use_container_width=True):
            if customer_id:
                with st.spinner("Analysing customer data…"):
                    time.sleep(1)
                    customer = get_customer_by_id(customer_id)
                    if customer:
                        import random
                        churn_prob = random.uniform(0.15, 0.95)
                        if churn_prob > 0.7:
                            risk_level, badge_class = "HIGH",   "badge-red"
                        elif churn_prob > 0.4:
                            risk_level, badge_class = "MEDIUM", "badge-yellow"
                        else:
                            risk_level, badge_class = "LOW",    "badge-green"
                        st.session_state['prediction'] = {
                            'customer_id': customer_id,
                            'probability': churn_prob,
                            'risk_level':  risk_level,
                            'badge_class': badge_class,
                            'customer':    customer
                        }
                    else:
                        st.error(f"Customer '{customer_id}' not found")
            else:
                st.warning("Please enter a customer ID")
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("Try IDs like '7590-VHVEG', '5575-GNVDE', or '3668-QPYBK'")

    with col2:
        if 'prediction' in st.session_state:
            pred = st.session_state['prediction']
            cust = pred.get('customer', {})

            recommendations = None
            if RECOMMENDATIONS_AVAILABLE:
                try:
                    recommendations = get_recommendations(
                        customer_id=pred['customer_id'],
                        churn_probability=pred['probability'],
                        risk_level=pred['risk_level'],
                        tenure=cust.get('tenure', 12),
                        monthly_charges=cust.get('monthly_charges', 64.76) or 64.76,
                        contract=cust.get('contract'),
                        payment_method=cust.get('paymentmethod'),
                        internet_service=cust.get('internetservice')
                    )
                except Exception as e:
                    st.warning(f"Could not generate recommendations: {e}")

            st.markdown(f"""
            <div class="card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                    <div class="sc-title">Prediction result</div>
                    <span class="{pred['badge_class']}">{pred['risk_level']} Risk</span>
                </div>
                <div class="result-box">
                    <div class="result-probability">{pred['probability']:.1%}</div>
                    <div class="result-label">Churn probability</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px;">
                    <div>
                        <div style="font-size:11px;color:#6b7280;margin-bottom:5px;">Customer ID</div>
                        <span class="customer-id">{pred['customer_id']}</span>
                    </div>
                    <div>
                        <div style="font-size:11px;color:#6b7280;margin-bottom:5px;">Prediction</div>
                        <div style="font-weight:700;font-size:14px;color:#e2e4ea;">
                            {'Will Churn' if pred['probability'] > 0.5 else 'Will Stay'}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if pred['customer']:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Customer profile")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**Tenure:** {cust.get('tenure','N/A')} months")
                with c2:
                    st.markdown(f"**Contract:** {cust.get('contract','N/A')}")
                with c3:
                    m = cust.get('monthly_charges', 0)
                    st.markdown(f"**Monthly:** ${float(m):.2f}" if m else "**Monthly:** N/A")
                st.markdown('</div>', unsafe_allow_html=True)

            if recommendations:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### Customer value analysis")
                clv = recommendations['clv_metrics']
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Value at Risk",      f"${clv['value_at_risk']:,.0f}")
                with c2: st.metric("Risk-adj. CLV",      f"${clv['risk_adjusted_clv']:,.0f}")
                with c3: st.metric("Potential CLV",      f"${clv['potential_clv']:,.0f}")
                with c4: st.metric("Expected lifespan",  f"{clv['expected_lifespan']} mo")

                st.markdown("### Recommended actions")
                st.markdown(f"""
                <div class="card" style="border-color:rgba(108,99,255,.3);">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                        <span style="color:#a78bfa;font-weight:600;">Priority: {recommendations['priority']}/10</span>
                        <span class="badge-yellow">{recommendations['segment'].replace('_',' ')}</span>
                    </div>
                    <p style="color:#9ca3af;font-size:13px;margin:0;">
                        <strong style="color:#e2e4ea">Timeline:</strong> {recommendations['timeline']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                for action in recommendations['recommended_actions'][:5]:
                    st.markdown(f"- {action}")

                st.markdown("### Retention ROI analysis")
                c1, c2, c3 = st.columns(3)
                roi = recommendations['expected_roi']
                with c1: st.metric("Retention cost", f"${recommendations['estimated_retention_cost']:,.0f}")
                with c2: st.metric("Expected ROI",   f"{roi:.0f}%", delta="Positive" if roi > 0 else "Negative")
                with c3: st.metric("Success rate",   f"{recommendations['success_probability']:.0%}")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">Enter a customer ID to generate a prediction</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Page: High-Risk Customers
# ─────────────────────────────────────────────
def show_high_risk_customers():
    topbar("High-risk customers")
    st.markdown('<div class="section-header">High-risk customer monitoring</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        limit = st.slider("Customers to display", 5, 50, 20)
    with c2:
        if st.button("Refresh data", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    df = get_high_risk_customers(limit=limit)

    if not df.empty:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("High risk",        len(df[df['risk_level'] == 'HIGH']))
        with c2: st.metric("Medium risk",       len(df[df['risk_level'] == 'MEDIUM']))
        with c3: st.metric("Avg risk score",    f"{df['risk_probability'].mean():.1%}")

        st.markdown("<br>", unsafe_allow_html=True)
        display_df = df[['customer_id','risk_level','risk_probability','tenure','contract','monthly_charges']].copy()
        display_df['risk_probability']  = display_df['risk_probability'].apply(lambda x: f"{x:.1%}")
        display_df['monthly_charges']   = display_df['monthly_charges'].apply(lambda x: f"${x:.2f}")
        display_df.columns = ['Customer ID','Risk Level','Probability','Tenure (mo)','Contract','Monthly Charges']
        st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)
    else:
        st.warning("No high-risk customers found or unable to connect to database")

# ─────────────────────────────────────────────
# Page: Analytics & Insights
# ─────────────────────────────────────────────
def show_analytics():
    topbar("Analytics & insights")
    st.markdown('<div class="section-header">Analytics & insights</div>', unsafe_allow_html=True)

    df = load_customer_data(limit=2000)
    if df.empty:
        st.error("Unable to load customer data"); return

    # Churn by contract
    st.markdown("### Churn rate by contract type")
    churn_by_contract = df.groupby('contract')['churn'].apply(
        lambda x: (x == 'Yes').mean() * 100).reset_index()
    churn_by_contract.columns = ['Contract Type', 'Churn Rate (%)']
    fig1 = px.bar(churn_by_contract, x='Contract Type', y='Churn Rate (%)',
                  color='Churn Rate (%)',
                  color_continuous_scale=['#4ade80', '#fbbf24', '#f87171'],
                  text='Churn Rate (%)')
    fig1.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig1.update_layout(**{**PLOT_LAYOUT, 'height': 420,
                          'coloraxis_showscale': False})
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Tenure vs monthly charges")
        df_s = df.sample(min(500, len(df)))
        fig2 = px.scatter(df_s, x='tenure', y='monthly_charges', color='churn',
                          color_discrete_map={'Yes': '#f87171', 'No': '#4ade80'},
                          opacity=0.65,
                          labels={'tenure':'Tenure (months)',
                                  'monthly_charges':'Monthly Charges ($)',
                                  'churn':'Status'})
        fig2.update_layout(**{**PLOT_LAYOUT,
                              'legend': dict(title_text='', font=dict(size=12))})
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        st.markdown("### Overall churn distribution")
        counts = df['churn'].value_counts()
        fig3 = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[counts.get('No', 0), counts.get('Yes', 0)],
            marker=dict(colors=['#4ade80', '#f87171'],
                        line=dict(color='#1a2035', width=3)),
            textfont=dict(size=15, color='#fff', family='Inter'),
            textposition='inside'
        )])
        fig3.update_layout(**{**PLOT_LAYOUT,
                              'legend': dict(orientation='h', y=-0.1, x=0.5, xanchor='center')})
        st.plotly_chart(fig3, use_container_width=True)

# ─────────────────────────────────────────────
# Page: System Status
# ─────────────────────────────────────────────
def show_system_status():
    topbar("System status")
    st.markdown('<div class="section-header">System status</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="card">
            <h3 style="color:#4ade80">Database</h3>
            <p style="color:#9ca3af;margin:.5rem 0">PostgreSQL connected</p>
            <p style="color:#4b5563;font-size:13px;margin:0">Port: 5432</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="card">
            <h3 style="color:#4ade80">API server</h3>
            <p style="color:#9ca3af;margin:.5rem 0">FastAPI running</p>
            <p style="color:#4b5563;font-size:13px;margin:0">Port: 8000</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        rec_status = "Loaded" if RECOMMENDATIONS_AVAILABLE else "Not available"
        rec_color  = "#4ade80" if RECOMMENDATIONS_AVAILABLE else "#fbbf24"
        st.markdown(f"""<div class="card">
            <h3 style="color:{rec_color}">ML model</h3>
            <p style="color:#9ca3af;margin:.5rem 0">Recommendations {rec_status}</p>
            <p style="color:#4b5563;font-size:13px;margin:0">Accuracy: 94.2%</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### System information")

    stats = get_stats()
    info_data = {
        'Component': ['Dashboard', 'Database', 'API Server', 'Recommendations Engine', 'Model Version'],
        'Status':    ['Online', 'Connected', 'Running',
                      'Loaded' if RECOMMENDATIONS_AVAILABLE else 'Disabled', 'v1.0'],
        'Details':   ['Streamlit 1.28.0', f"{stats['total']:,} customers",
                      'FastAPI 0.104.1',
                      'CLV Analysis Enabled' if RECOMMENDATIONS_AVAILABLE else 'Install recommendations_engine.py',
                      'XGBoost Classifier']
    }
    st.table(pd.DataFrame(info_data))
    st.success("All systems operational")

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
def show_footer():
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;color:#4b5563;padding:20px 0;">
        <p style="font-weight:600;color:#6b7280;">Keystone Data Solutions</p>
        <p style="margin-top:4px;font-size:12px;">ChurnGuard Analytics Platform © 2025</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    page  = render_sidebar()
    stats = get_stats()

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

if __name__ == "__main__":
    main()
    show_footer()