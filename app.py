import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import calendar

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="369 ELITE V39", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; padding: 10px; }
    
    /* Force Metric Colors */
    [data-testid="stMetricDelta"] > div { font-weight: bold !important; }
    /* Green for positive, Red for negative */
    div[data-testid="stMetricDelta"] > div[data-direction="up"] { color: #34d399 !important; }
    div[data-testid="stMetricDelta"] > div[data-direction="down"] { color: #ef4444 !important; }
    
    div[data-testid="stMetric"] { 
        background: rgba(22, 27, 34, 0.8) !important; 
        border: 1px solid #30363d !important; 
        border-radius: 12px;
        padding: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_v39.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, 
              outcome TEXT, pnl REAL, rr REAL, balance REAL, mindset TEXT, setup TEXT)''')
conn.commit()

# --- 3. DATA PREP ---
df = pd.read_sql_query("SELECT * FROM trades", conn)
current_balance = 0.0
last_pnl = 0.0
initial_bal = 1000.0

if not df.empty:
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values('date_dt')
    initial_bal = df['balance'].iloc[0]
    df['cum_pnl'] = df['pnl'].cumsum()
    df['equity_curve'] = initial_bal + df['cum_pnl']
    current_balance = df['equity_curve'].iloc[-1]
    last_pnl = df['pnl'].iloc[-1]

# --- 4. HEADER ---
st.markdown('<h1 class="main-title">369 TRACKER PRO</h1>', unsafe_allow_html=True)
col_eq1, col_eq2, col_eq3 = st.columns([1, 1.5, 1])
with col_eq2:
    st.metric(
        label="CURRENT EQUITY", 
        value=f"${current_balance:,.2f}", 
        delta=f"{last_pnl:+.2f} USD",
        delta_color="normal" # CSS will handle the exact red/green
    )

tabs = st.tabs(["🚀 TERMINAL", "📅 CALENDAR", "📊 GROWTH %", "🧬 ANALYZERS"])

# --- TAB 1: TERMINAL (The Real Chart) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2.5])
    with c1:
        with st.form("entry_v39", clear_on_submit=True):
            st.subheader("Add Trade")
            bal_start = st.number_input("Starting Bal ($)", value=initial_bal)
            d_in = st.date_input("Date", datetime.now())
            asset = st.text_input("Pair", "NAS100").upper()
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            p_val = st.number_input("P&L ($)", value=0.0)
            st.form_submit_button("LOCK", on_click=None)
            c.execute("INSERT INTO trades (date, pair, outcome, pnl, rr, balance) VALUES (?,?,?,?,?,?)",
                      (str(d_in), asset, res, p_val, 0, bal_start))
            conn.commit()
            # Note: For production, use st.rerun() if button is clicked

    with c2:
        if not df.empty:
            # Equity Curve بحال شارت حقيقي
            fig_eq = go.Figure()
            
            # إضافة خط الصفر (Initial Balance) كمرجع
            fig_eq.add_hline(y=initial_bal, line_dash="dash", line_color="rgba(255,255,255,0.2)", annotation_text="Initial")

            fig_eq.add_trace(go.Scatter(
                x=df['date_dt'], 
                y=df['equity_curve'],
                mode='lines+markers',
                line=dict(color='#00ffcc', width=3, shape='spline'),
                fill='tonexty', # تظليل تحت الخط
                fillcolor='rgba(0,255,204,0.1)',
                marker=dict(size=8, color='#00ffcc', line=dict(width=1, color='white')),
                name="Equity"
            ))

            fig_eq.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=450,
                xaxis=dict(title="Timeline (Days)", showgrid=False),
                yaxis=dict(title="Equity ($)", gridcolor='rgba(255,255,255,0.05)', zeroline=False),
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig_eq, use_container_width=True)

# --- TAB 3: GROWTH % (Zero in Middle) ---
with tabs[2]:
    if not df.empty:
        df['month'] = df['date_dt'].dt.strftime('%b %Y')
        m_df = df.groupby('month')['pnl'].sum().reset_index()
        
        # مبيان الأعمدة مع الصفر في الوسط
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(
            x=m_df['month'],
            y=m_df['pnl'],
            marker_color=['#34d399' if x > 0 else '#ef4444' for x in m_df['pnl']],
            text=m_df['pnl'],
            textposition='auto',
        ))
        
        fig_m.update_layout(
            template="plotly_dark",
            title="Monthly Profit/Loss (Zero Centered)",
            yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='white', title="P&L ($)"),
            xaxis=dict(title="Month")
        )
        st.plotly_chart(fig_m, use_container_width=True)
