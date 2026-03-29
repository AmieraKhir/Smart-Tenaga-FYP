
# region IMPORTS & INITIAL SETUP
import sys
import os
import streamlit as st
import pandas as pd
import joblib
import pickle
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_autorefresh import st_autorefresh
import numpy as np
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')
# endregion

# ====================================
# PERMANENT HISTORY STORAGE
# ====================================
DATA_STORE = "data/permanent_history.csv"

# def load_local_history():
#     if os.path.exists(DATA_STORE):
#         return pd.read_csv(DATA_STORE, parse_dates=['created_at'])
#     return pd.DataFrame()

def load_local_history():
    if os.path.exists(DATA_STORE):
        df = pd.read_csv(DATA_STORE, parse_dates=['created_at'])

        # If timestamp is naive → localize
        if df['created_at'].dt.tz is None:
            df['created_at'] = df['created_at'].dt.tz_localize("UTC")
        else:
            # If timestamp already has timezone → ensure it's UTC
            df['created_at'] = df['created_at'].dt.tz_convert("UTC")

        return df
    return pd.DataFrame()


def save_local_history(df):
    os.makedirs(os.path.dirname(DATA_STORE), exist_ok=True)
    df.to_csv(DATA_STORE, index=False)

# region PAGE CONFIG
# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Smart Tenaga Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
# endregion

# region HEADER
st.markdown('<h1 class="main-header">🔌 Smart Tenaga Dashboard</h1>', unsafe_allow_html=True)
#st.markdown('<p class="sub-header">Real-time monitoring and predictive analytics for optimized energy management.</p>', unsafe_allow_html=True)
st.markdown('''
<p class="sub-header" style="margin-top: -5px; margin-bottom: 5px;">
    Real-time monitoring and predictive analytics for optimized energy management.
</p>
''', unsafe_allow_html=True)
# st.markdown('<h1 class="main-header">Smart Tenaga Dashboard</h1>', unsafe_allow_html=True)
# endregion

#region TELEGRAM
# -----------------------
# TELEGRAM CONFIG
# -----------------------
TELEGRAM_TOKEN = "8250677695:AAGs3Q_aErWN2ZrpCHl9NQJFhtg1RhldNTI"  # Replace with your bot token
TELEGRAM_CHAT_ID = "870985106"  # Replace with your chat ID

def send_telegram_alert(message: str):
    """Send an alert message via Telegram bot."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"⚠️ Telegram alert failed: {e}")

#endregion 

# @st.cache_data(ttl=10)
# def get_live_data():
#     return fetch_thingspeak(CHANNEL_ID, READ_KEY, results=8000)
# ==========================================================
# permanent history + latest merged dataset
# ==========================================================
@st.cache_data(ttl=30)
def get_all_data():
    # Step 1: get newest data from ThingSpeak
    try:
        latest_df = fetch_thingspeak(CHANNEL_ID, READ_KEY, results=8000)
        latest_df['created_at'] = pd.to_datetime(latest_df['created_at'], utc=True)
    except:
        latest_df = pd.DataFrame()

    # Step 2: load saved history
    old_df = load_local_history()

    # Step 3: merge
    full_df = pd.concat([old_df, latest_df], ignore_index=True)

    # Step 4: remove duplicates
    full_df = full_df.drop_duplicates(subset=['created_at'])

    # Step 5: sort
    full_df = full_df.sort_values("created_at").reset_index(drop=True)

    # Step 6: save updated history
    save_local_history(full_df)
    # Convert to Malaysia timezone
    full_df['created_at'] = full_df['created_at'].dt.tz_convert('Asia/Kuala_Lumpur')
    return full_df

# region CUSTOM CSS
# --- CLEAN CSS ---
st.markdown("""
<style>
    /* Global Streamlit overrides */
    .stApp {
        background-color: #0e1117; 
        color: #fafafa; 
        font-family: 'Inter', sans-serif;
    }
    .dashboard-title {
        font-size: 2.4rem !important;
        font-weight: 700;
        text-align: left;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.2rem;
    }

    .main-header {
        font-size: 3rem !important;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    
    
    # /* Custom Header Styles */
    # .main-header {
    #     font-size: 2.8rem !important;
    #     text-align: center;
    #     margin-bottom: 0.5rem;
    #     font-weight: 700;
    #     background: linear-gradient(45deg, #1f77b4, #2E86AB);
    #     -webkit-background-clip: text;
    #     -webkit-text-fill-color: transparent;
    #     font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    # }
    .sub-header {
        text-align: center;
        color: #6c757d !important;
        margin-bottom: 2rem;
        font-size: 1.3rem !important;
        font-weight: 300;
        letter-spacing: 0.5px;
    } 

    /* Gradient Metric Card (Primary Style) */
    .metric-card {
        # background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background: linear-gradient(135deg, #0d1b1e 0%, #40916c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        border: none; /* Removed border to rely on shadow/gradient */
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%; /* Ensure columns look aligned */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: flex-start;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    .metric-card h2, .metric-card h3 {
        color: white;
        margin: 0;
        font-weight: 600;
    }
    .metric-card p {
        margin: 0.2rem 0 0.5rem 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }

    /* Dark Metric Card (for secondary display like KPIs) */
    .dark-metric-card {
        background: #334e68; 
        color: #f0f2f6; 
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 4px solid #4a90e2; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
    }
    .dark-metric-card strong {
        color: #c9d1d9;
        font-weight: 400;
    }
    
    /* Custom Alert Styles */
    .alert-card {
        background: #fff3cd; /* Light warning background */
        border-left: 5px solid #ffc107; /* Orange/Yellow border */
        color: #664d03; /* Dark text for contrast */
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.95rem;
    }
    .critical-card {
        background: #f8d7da; /* Light danger background */
        border-left: 5px solid #dc3545; /* Red border */
        color: #58151c; /* Dark red text */
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        font-weight: 600;
    }

    /* Streamlit widget styling for consistency */
    .stSelectbox, .stNumberInput, .stSlider, .stButton>button {
        border-radius: 8px;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #ffffff;
        padding: 2rem 1rem;
        box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05);
    }
    .sidebar-header {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)
# endregion

# region FIX IMPORT PATH

# --- FIX IMPORT PATH ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from scripts.thingspeak_fetch import fetch_thingspeak
# endregion

# region AUTO REFRESH
#---------------------------------------------------------
st_autorefresh(interval=30_000, limit=None, key="dashboard2_refresh")
# endregion

# region CONFIG
# --- CONFIG ---
CHANNEL_ID = "3135951"
READ_KEY = "0CE36Q6H7NYOB0TN"
MODEL_PATH = "models/energy_predictor.pkl" 
DATA_PATH = "data/merged_feeds_datalog.xlsx"
DATA_PATH_MIN = "data/ml_ready_dataset_min2.xlsx"
# endregion

# region LOAD MODEL (cached)
# --- LOAD MODEL (cached) ---
@st.cache_resource
def load_model():
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None

model = load_model()
# endregion

# region UTILITY FUNCTIONS
# --- UTILITY FUNCTIONS ---
# -------------------------
# DATA CLEANING FUNCTION
# -------------------------
def clean_data(df):
    df = df.sort_values("created_at").reset_index(drop=True)
    df['energy_diff'] = df['energy'].diff().fillna(0)
    df['energy_increment_kwh'] = np.maximum(df['energy_diff'], 0)
    # optional: sensor reset
    time_energy = (df['power'] * df['created_at'].diff().dt.total_seconds().fillna(0)/3600) / 1000
    sensor_reset = df['energy_diff'] < -0.1
    df['energy_increment_kwh'] = np.where(sensor_reset, np.maximum(time_energy, 0), df['energy_increment_kwh'])
    return df

# # -------------------------
# # ADD ML FEATURES
# # -------------------------
# def add_ml_features(df):
#     df['delta_power'] = df['power'].diff().fillna(0)
#     df['delta_voltage'] = df['voltage'].diff().fillna(0)
#     df['delta_energy'] = df['energy_increment_kwh'].diff().fillna(0)
#     df['apparent_power'] = df['voltage'] * df['current']
#     df['pf_efficiency'] = df['power'] / df['apparent_power'].replace(0, np.nan)
#     df['time_diff_min'] = df['created_at'].diff().dt.total_seconds().div(60).fillna(0)
#     df['gap_flag'] = (df['time_diff_min'] > 2).astype(int)
#     df['power_current'] = df['power'] * df['current']

#     # Lag features
#     for col in ['power','energy_increment_kwh']:
#         for lag in [1,2,3,5,10]:
#             df[f'{col}_lag{lag}'] = df[col].shift(lag).fillna(0)
#         for window in [3,5,10]:
#             df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window).mean().fillna(0)
#             df[f'{col}_rolling_std_{window}'] = df[col].rolling(window).std().fillna(0)

#     # Daily cumulative energy
#     df['daily_energy_sum'] = df.groupby(df['created_at'].dt.date)['energy_increment_kwh'].cumsum()

#     return df.fillna(0)


def calculate_energy_insights(df):
    """Calculate energy consumption insights"""
    insights = {}
    if df.empty:
        return {'avg_power': 0, 'max_power': 0, 'total_energy': 0, 'avg_voltage': 0,
                'peak_hour': 0, 'peak_power': 0, 'estimated_cost': 0}
        
    insights['avg_power'] = df['power'].mean()
    insights['max_power'] = df['power'].max()
    insights['total_energy'] = df['energy'].sum()
    insights['avg_voltage'] = df['voltage'].mean()
    
    # Consumption patterns
    df['hour'] = df['created_at'].dt.hour
    hourly_consumption = df.groupby('hour')['power'].mean()
    insights['peak_hour'] = hourly_consumption.idxmax()
    insights['peak_power'] = hourly_consumption.max()
    
    # Cost estimation (assuming RM 0.50 per kWh)
    insights['estimated_cost'] = insights['total_energy'] * 0.50
    
    return insights

def add_ml_features(df):
    df['delta_power'] = df['power'].diff().fillna(0)
    df['delta_voltage'] = df['voltage'].diff().fillna(0)
    df['delta_energy'] = df['energy_increment_kwh'].diff().fillna(0)
    df['apparent_power'] = df['voltage'] * df['current']
    df['pf_efficiency'] = df['power'] / df['apparent_power'].replace(0, np.nan)
    df['time_diff_min'] = df['created_at'].diff().dt.total_seconds().div(60).fillna(0)
    df['gap_flag'] = (df['time_diff_min'] > 2).astype(int)
    df['power_current'] = df['power'] * df['current']

    # Lag features
    lag_cols = ['power','energy_increment_kwh']
    for col in lag_cols:
        for lag in [1,2,3,5,10]:
            df[f'{col}_lag{lag}'] = df[col].shift(lag).fillna(0)

    # Rolling features
    for col in lag_cols:
        for window in [3,5,10]:
            df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window).mean().fillna(0)
            df[f'{col}_rolling_std_{window}'] = df[col].rolling(window).std().fillna(0)

    # Daily cumulative energy
    df['daily_energy_sum'] = df.groupby(df['created_at'].dt.date)['energy_increment_kwh'].cumsum()

    return df.fillna(0)


def detect_anomalies(df):
    """Detect potential anomalies in the data"""
    anomalies = []
    if df.empty or df['voltage'].std() == 0 or df['current'].std() == 0:
        return anomalies
        
    # Voltage anomalies (using 2-sigma for simplicity)
    voltage_mean = df['voltage'].mean()
    voltage_std = df['voltage'].std()
    voltage_anomalies = df[(df['voltage'] > voltage_mean + 2*voltage_std) | 
                           (df['voltage'] < voltage_mean - 2*voltage_std)]
    if len(voltage_anomalies) > 0:
        anomalies.append(f"Voltage anomalies detected: {len(voltage_anomalies)} instances")
    
    # Power factor issues
    low_pf = df[df['power_factor'] < 0.8]
    if len(low_pf) > 0:
        anomalies.append(f"Low power factor detected: {len(low_pf)} instances (Min PF: {df['power_factor'].min():.2f})")
    
    # Current spikes (using 3-sigma for simplicity)
    current_mean = df['current'].mean()
    current_std = df['current'].std()
    current_spikes = df[df['current'] > current_mean + 3*current_std]
    if len(current_spikes) > 0:
        anomalies.append(f"Current spikes detected: {len(current_spikes)} instances")
    
    return anomalies

def generate_energy_report(insights, anomalies):
    """Generate automated energy report"""
    report = []
    
    # Performance summary
    if insights['avg_power'] > 1000:
        report.append("High average power consumption detected - consider energy efficiency measures.")
    elif insights['avg_power'] < 100 and insights['avg_power'] > 0:
        report.append("Low average power consumption - highly efficient operation observed.")
    
    # Peak hour recommendation
    if insights['peak_hour'] in [18, 19, 20]:  # Evening peak hours
        report.append(f"Peak consumption during evening hours ({insights['peak_hour']}:00) - strategic load shifting recommended.")
    
    # Cost insights
    if insights['estimated_cost'] > 50:
        report.append(f"Estimated consumption cost: RM {insights['estimated_cost']:.2f}. Monitor for savings opportunities.")
    
    # Add anomalies to report
    report.extend(anomalies)
    
    if not report:
        report.append("System stability is excellent. No major issues detected in the analyzed period.")
        
    return report
# endregion
#region DEVICE ENERGY 
class DeviceEnergyAnalyzer:
    """
    Smart Tenaga - Device-Level Energy & CO₂ Analyzer
    Works with both Jupyter and dashboard frameworks (e.g., Streamlit).
    """

    def __init__(self, data_path, co2_factor=0.774):
        """Initialize analyzer with dataset path and CO₂ factor (kgCO₂/kWh)."""
        self.df = pd.read_excel(data_path)
        self.device_columns = ['laptop', 'phone', 'lamp', 'ipad', 'monitor', 
                               'powerbank', 'dryer', 'earbuds']
        self.co2_factor = co2_factor
        self.single_device_stats = None
        self.total_allocated_energy = None

    # -------------------------------------------------------------------------
    def preprocess_data(self):
        """Clean and prepare dataset for analysis."""
        self.df.fillna(0, inplace=True)
        self.df['created_at'] = pd.to_datetime(self.df['created_at'])
        self.df.sort_values('created_at', inplace=True)
        print(f"✅ Data loaded: {len(self.df)} rows")
        print(f"📅 Range: {self.df['created_at'].min()} to {self.df['created_at'].max()}")
        return self.df

    # -------------------------------------------------------------------------
    def filter_by_date(self, start=None, end=None):
        """Optionally filter dataset by date range."""
        if start and end:
            mask = (self.df['created_at'] >= start) & (self.df['created_at'] <= end)
            self.df = self.df.loc[mask].reset_index(drop=True)
            print(f"🔎 Filtered data: {len(self.df)} rows from {start} to {end}")

    # -------------------------------------------------------------------------
    def analyze_single_device(self):
        """Compute average and total energy when only one device is active."""
        device_sums = self.df[self.device_columns].sum(axis=1)
        single_device_df = self.df[device_sums == 1].copy()

        device_stats = []
        for device in self.device_columns:
            data = single_device_df[single_device_df[device] == 1]
            if len(data) == 0:
                continue
            avg_power = data['power'].mean()
            avg_energy = data['energy_increment_kwh'].mean()
            total_energy = data['energy_increment_kwh'].sum()
            avg_co2 = avg_energy * self.co2_factor
            co2_kg = total_energy * self.co2_factor

            device_stats.append({
                'device': device,
                'count_active': len(data),
                'avg_power_W': avg_power,
                'avg_energy_kWh': avg_energy,
                'total_energy_kWh': total_energy,
                'avg_CO2_kg': avg_energy * self.co2_factor,
                'total_CO2_kg': co2_kg
            })

        stats_df = pd.DataFrame(device_stats).sort_values('avg_energy_kWh', ascending=False)
        self.single_device_stats = stats_df
        return stats_df

    # -------------------------------------------------------------------------
    def display_single_device_stats(self):
        """Pretty print single-device energy statistics."""
        if self.single_device_stats is None:
            print("⚠️ Run analyze_single_device() first!")
            return
        
        print("=" * 60)
        print("DEVICE STATISTICS (SINGLE DEVICE ACTIVE)")
        print("=" * 60)
        print(f"{'Device':12} | {'Count':>6} | {'Avg Power (W)':>13} | {'Avg Energy (kWh)':>16} | {'Total Energy (kWh)':>19} | {'CO₂ (kg)':>9}")
        print("-" * 90)

        for _, row in self.single_device_stats.iterrows():
            print(f"{row['device']:12} | "
                  f"{int(row['count_active']):6d} | "
                  f"{row['avg_power_W']:13.2f} | "
                  f"{row['avg_energy_kWh']:16.6f} | "
                  f"{row['total_energy_kWh']:19.6f} | "
                  f"{row['total_CO2_kg']:9.3f}")

        print("=" * 90)
    # -------------------------------------------------------------------------
    def allocate_multi_device_energy(self):
        """Distribute energy among active devices for multi-device timestamps."""
        if self.single_device_stats is None:
            raise ValueError("Run analyze_single_device() first!")

        device_avgs = dict(zip(self.single_device_stats['device'],
                               self.single_device_stats['avg_energy_kWh']))

        device_sums = self.df[self.device_columns].sum(axis=1)
        multi_df = self.df[device_sums > 1].copy()

        allocated = {dev: 0 for dev in self.device_columns}

        for _, row in multi_df.iterrows():
            active = [dev for dev in self.device_columns if row[dev] == 1]
            if not active:
                continue
            total_energy = row['energy_increment_kwh']
            weights = np.array([device_avgs.get(d, 1e-6) for d in active])
            weights /= weights.sum()
            for d, w in zip(active, weights):
                allocated[d] += total_energy * w

        # Combine with single-device totals
        total_energy = {}
        for d in self.device_columns:
            single = float(self.single_device_stats.query("device == @d")['total_energy_kWh']) if d in self.single_device_stats['device'].values else 0
            multi = allocated[d]
            total = single + multi
            total_energy[d] = total

        total_df = pd.DataFrame(list(total_energy.items()), columns=['device', 'total_energy_kWh'])
        total_df['total_CO2_kg'] = total_df['total_energy_kWh'] * self.co2_factor

        self.total_allocated_energy = total_df
        return total_df

    # -------------------------------------------------------------------------
    def summary_metrics(self):
        """Compute overall summary values."""
        total_energy = self.total_allocated_energy['total_energy_kWh'].sum()
        total_co2 = total_energy * self.co2_factor
        days = (self.df['created_at'].max() - self.df['created_at'].min()).days or 1
        yearly_projection = total_co2 * (365 / days)
        return {
            'total_energy_kWh': round(total_energy, 3),
            'total_CO2_kg': round(total_co2, 3),
            'days_recorded': days,
            'yearly_CO2_projection_kg': round(yearly_projection, 2)
        }

    # -------------------------------------------------------------------------
    # ---------------------- VISUALIZATIONS -----------------------------------
    # -------------------------------------------------------------------------
    def plot_energy_per_device(self):
        """Bar chart of total energy per device."""
        df = self.total_allocated_energy.sort_values('total_energy_kWh', ascending=False)
        fig = px.bar(df, x='device', y='total_energy_kWh',
                     color='device', text_auto='.3f',
                     title="🔋 Total Energy Consumption per Device (kWh)")
        fig.update_layout(xaxis_title="", yaxis_title="Energy (kWh)", template="plotly_white")
        return fig

    def plot_co2_pie(self):
        """Pie chart of CO₂ share per device."""
        df = self.total_allocated_energy
        fig = px.pie(df, values='total_CO2_kg', names='device',
                     title="🌍 CO₂ Emission Share per Device",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        return fig

    def plot_usage_over_time(self, devices=None):
        """Plot energy increments over time for selected devices."""
        if devices is None:
            devices = ['laptop', 'monitor', 'dryer', 'ipad']
        df = self.df[['created_at', 'energy_increment_kwh'] + devices].copy()
        fig = go.Figure()
        for dev in devices:
            dev_energy = []
            for _, row in df.iterrows():
                active_count = sum(row[d] for d in devices)
                dev_energy.append(row['energy_increment_kwh'] / active_count if row[dev] == 1 and active_count > 0 else 0)
            fig.add_trace(go.Scatter(x=df['created_at'], y=dev_energy, mode='lines', name=dev))
        fig.update_layout(title="📈 Energy Usage Over Time (Key Devices)",
                          xaxis_title="Time", yaxis_title="Estimated Energy (kWh)",
                          template="plotly_white")
        return fig
    
    #endregion
# region SIDEBAR CONTROL CENTER
# --- SIDEBAR WITH CONTROLS ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">Smart Tenaga Control Center</div>', unsafe_allow_html=True)

    # View mode selector
    mode = st.selectbox(
        "View Mode",
        ["Live Monitoring", "Predictive Analytics", "Device Energy & CO₂ Insights"]
    )
    # st.markdown("---")
    st.markdown("")
    st.subheader("Data Configuration")

    # Time Range
    time_range = st.selectbox(
        "Time Range",
        ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last Week", "Custom Range"]
    )

    # If user selects Custom Range
    if time_range == "Custom Range":
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
    else:
        start_date = None
        end_date = None

    st.markdown("")
    st.subheader("Alert Thresholds")

    # Power threshold (kept)
    power_threshold = st.slider("Power Alert Threshold (W)", 0, 1000, 150)

    # Replace VOLTAGE ALERT with CURRENT ALERT (more meaningful)
    current_threshold = st.slider("Current Alert Threshold (A)", 0, 15, 10)

    st.markdown("")
    st.caption("Auto-refresh is active (30 seconds)")
# endregion

# region LIVE MONITORING
if mode == "Live Monitoring":
    st.markdown("<h1 class='dashboard-title'>Live Monitoring</h1>", unsafe_allow_html=True)

    # =========================
    # SETTINGS
    # =========================
    CARBON_EMISSION_FACTOR = 0.774  # kg CO₂ per kWh

    # Fetch and process live data
    # live_df = fetch_thingspeak(CHANNEL_ID, READ_KEY, results=8000)
    # live_df = get_live_data()
    live_df = get_all_data()
    # # -------------------------
    # # DEBUG TIMESTAMP CHECK
    # # -------------------------
    # st.write("Min created_at:", live_df['created_at'].min())
    # st.write("Max created_at:", live_df['created_at'].max())
    # st.write("Now in KL:", pd.Timestamp.now(tz='Asia/Kuala_Lumpur'))
    # st.write("Difference (minutes):",
    #         (pd.Timestamp.now(tz='Asia/Kuala_Lumpur') - live_df['created_at'].max()).total_seconds() / 60)

    if live_df.empty:
        st.error("No data received from ThingSpeak. Please check your connection.")
        st.stop()

    # live_df['created_at'] = pd.to_datetime(live_df['created_at'], utc=True)
    # live_df['created_at'] = live_df['created_at'].dt.tz_convert('Asia/Kuala_Lumpur')


    # -------------------------------------------
    # APPLY TIME RANGE FILTER FOR LIVE MODE
    # -------------------------------------------
    now = pd.Timestamp.now(tz="Asia/Kuala_Lumpur")

    if time_range == "Last 1 Hour":
        live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(hours=1)]

    elif time_range == "Last 6 Hours":
        live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(hours=6)]

    elif time_range == "Last 24 Hours":
        live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(hours=24)]

    elif time_range == "Last Week":
        live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(days=7)]

    elif time_range == "Custom Range" and start_date and end_date:
        live_df = live_df[
            (live_df["created_at"].dt.date >= start_date) &
            (live_df["created_at"].dt.date <= end_date)
        ]

    # Safety check
    if live_df.empty:
        st.warning("No data available for selected time range.")
        st.stop()
    
    # Convert numeric columns
    numeric_cols = ['voltage', 'current', 'power', 'energy', 'frequency', 'power_factor']
    numeric_cols = [col for col in numeric_cols if col in live_df.columns]
    live_df[numeric_cols] = live_df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Clean data → this creates energy_increment_kwh
    live_df = clean_data(live_df)

    # Add ML features (safe)
    live_df = add_ml_features(live_df)

    # Calculate today's total energy based on increments
    live_df['date'] = live_df['created_at'].dt.date
    today = pd.Timestamp.now(tz="Asia/Kuala_Lumpur").date()
    energy_today_total = live_df[live_df['date'] == today]['energy_increment_kwh'].sum()

    # Get latest after cleaning
    live_df = live_df.sort_values("created_at").reset_index(drop=True)
    latest = live_df.iloc[-1]

  
    # =========================
    # TOP ROW: KEY PERFORMANCE INDICATORS - MATCHING PREDICTIVE ANALYTICS STYLE
    # =========================
    st.subheader("Live Performance Metrics")
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        power_status = "Optimal" if latest['power'] <= power_threshold else "High"
        power_color = "#28a745" if latest['power'] <= power_threshold else "#dc3545"
        st.markdown(f"""
        <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
            <div style="line-height:0.9; text-align:center;">
                <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">⚡ Live Power</h4>
                <h2 style="font-size:2.4rem; margin:0; padding:0; color:{power_color}; font-weight:700;">{latest['power']:.1f} W</h2>
                <p style="font-size:0.9rem; margin:0; padding:0; color:white;">{power_status} Consumption</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    

    with kpi_cols[1]:
        st.markdown(f"""
        <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
            <div style="line-height:1.0; text-align:left; white-space:nowrap; margin-left:4px;">
                <h4 style="font-size:1.15rem; margin:0 0 2px 0; color:white; font-weight:600;">🔋 Energy Used Today</h4>
                <h2 style="font-size:2.4rem; margin:-10px 0 0 0; padding:0; color:#17a2b8; font-weight:700;">{energy_today_total:.3f} kWh</h2>
                <p style="font-size:0.9rem; margin:0; padding:0; color:white;">Based on real-time increments</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[2]:
        co2_today = energy_today_total * CARBON_EMISSION_FACTOR
        st.markdown(f"""
        <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
            <div style="line-height:0.9; text-align:center;">
                <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">🌱 Carbon Footprint</h4>
                <h2 style="font-size:2.4rem; margin:0; padding:0; color:#28a745; font-weight:700;">{co2_today:.3f} kg</h2>
                <p style="font-size:0.9rem; margin:0; padding:0; color:white;">Today's CO₂ Equivalent</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


    with kpi_cols[3]:
        total_energy = latest['energy']  # cumulative from ThingSpeak
        st.markdown(f"""
        <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
            <div style="line-height:0.9; text-align:center;">
                <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">📟 Total Energy </h4>
                <h2 style="font-size:2.4rem; margin:0; padding:0; color:#2ca02c; font-weight:700;">{total_energy:.3f} kWh</h2>
                <p style="font-size:0.9rem; margin:0; padding:0; color:white;">Since first installation</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


    # =========================
    # MAIN DASHBOARD LAYOUT
    # =========================
    main_col1, main_col2 = st.columns([2, 1])

    with main_col1:
        # INTERACTIVE CHARTS SECTION
        st.subheader("Real-time Analytics")
        
        # Tabbed interface for different views
        tab1, tab2, tab3 = st.tabs(["Power Analysis", "Multi-Parameter", "Sustainability"])
        
        with tab1:
            # Power analysis with threshold zones
            fig_power = go.Figure()
            fig_power.add_trace(go.Scatter(
                x=live_df['created_at'], 
                y=live_df['power'],
                mode='lines+markers',
                name='Power (W)',
                line=dict(color='#1f77b4', width=3),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.1)'
            ))
            
            # Add threshold zones
            fig_power.add_hrect(
                y0=power_threshold, y1=live_df['power'].max() + 10,
                fillcolor="red", opacity=0.2,
                line_width=0, annotation_text="High Consumption Zone"
            )
            fig_power.add_hrect(
                y0=0, y1=power_threshold,
                fillcolor="green", opacity=0.2,
                line_width=0, annotation_text="Normal Zone"
            )
            
            fig_power.update_layout(
                title="Real-time Power Consumption with Safety Zones",
                xaxis_title="Time",
                yaxis_title="Power (W)",
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig_power, use_container_width=True)
        
        with tab2:
            # Multi-parameter view
            fig_multi = make_subplots(rows=2, cols=2, 
                                    subplot_titles=('Voltage Trend', 'Current Trend', 'Power Factor', 'Frequency'),
                                    vertical_spacing=0.12)
            
            fig_multi.add_trace(go.Scatter(x=live_df['created_at'], y=live_df['voltage'], 
                                         name="Voltage", line=dict(color='#ff7f0e')), row=1, col=1)
            fig_multi.add_trace(go.Scatter(x=live_df['created_at'], y=live_df['current'], 
                                         name="Current", line=dict(color='#d62728')), row=1, col=2)
            fig_multi.add_trace(go.Scatter(x=live_df['created_at'], y=live_df['power_factor'], 
                                         name="PF", line=dict(color='#9467bd')), row=2, col=1)
            if 'frequency' in live_df.columns:
                fig_multi.add_trace(go.Scatter(x=live_df['created_at'], y=live_df['frequency'], 
                                             name="Freq", line=dict(color='#8c564b')), row=2, col=2)
            
            fig_multi.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig_multi, use_container_width=True)
        
        with tab3:

            # ----------------------------
            # 1️⃣ TOP KPI CARDS
            # ----------------------------
            co2_today = energy_today_total * CARBON_EMISSION_FACTOR
            co2_per_kwh = CARBON_EMISSION_FACTOR

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🌍 CO₂ Today", f"{co2_today:.3f} kg")
            c2.metric("⚡ Energy Today", f"{energy_today_total:.3f} kWh")
            c3.metric("♻️ CO₂ Efficiency", f"{co2_per_kwh:.2f} kg/kWh")
            c4.metric("🌱 Sustainability Score", 
                    "Good" if co2_per_kwh < 0.8 else "Poor", 
                    delta="Based on CO₂ intensity")

            st.markdown("")

            # ----------------------------
            # 2️⃣ IMPROVED CO₂ TREND CHART
            # ----------------------------
            df_co2 = live_df.copy()
            df_co2["co2"] = df_co2["energy_increment_kwh"].cumsum() * CARBON_EMISSION_FACTOR

            fig_co2 = go.Figure()

            fig_co2.add_trace(go.Scatter(
                x=df_co2["created_at"],
                y=df_co2["co2"],
                mode="lines",
                line=dict(color="#00cc96", width=4),
                fill="tozeroy",
                fillcolor="rgba(0, 204, 150, 0.25)",
                name="CO₂"
            ))

            fig_co2.update_layout(
                title="🌳 Cumulative CO₂ Emissions",
                xaxis_title="Time",
                yaxis_title="CO₂ (kg)",
                height=360,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white")
            )

            # ----------------------------
            # 3️⃣ BETTER GAUGE (Live Power Zones)
            # ----------------------------
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest["power"],
                title={"text": "Live Power Zone (W)"},
                gauge={
                    "axis": {"range": [0, power_threshold * 1.5]},
                    "bar": {"color": "#1f77b4"},
                    "steps": [
                        {"range": [0, power_threshold * 0.7], "color": "rgba(40,167,69,0.4)"},   # green
                        {"range": [power_threshold * 0.7, power_threshold], "color": "rgba(255,193,7,0.4)"}, # yellow
                        {"range": [power_threshold, power_threshold * 1.5], "color": "rgba(220,53,69,0.4)"}, # red
                    ],
                }
            ))

            fig_gauge.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)")

            # Display side-by-side
            g1, g2 = st.columns([1.2, 1])
            g1.plotly_chart(fig_co2, use_container_width=True)
            g2.plotly_chart(fig_gauge, use_container_width=True)
            co2_per_kwh = CARBON_EMISSION_FACTOR


            # ----------------------------
            # 4️⃣ SUMMARY CARD
            # ----------------------------
            st.markdown("""
            <div style='background:#1c2c22; padding:1rem; border-radius:10px; margin-top:10px'>
                <h4 style='color:#90ee90;'>🌱 Sustainability Summary</h4>
                <p>• Total CO₂ emitted today: <b>{:.3f} kg</b></p>
                <p>• Energy consumed so far: <b>{:.3f} kWh</b></p>
                <p>• Carbon intensity: <b>{:.3f} kg/kWh</b></p>
                <p>• System currently operating in <b>{}</b> zone</p>
            </div>
            """.format(
                co2_today,
                energy_today_total,
                co2_per_kwh,
                "GREEN 🟢" if latest["power"] < power_threshold else "RED 🔴"
            ), unsafe_allow_html=True)

        # with tab3:
        #     # Sustainability metrics
        #     col_a, col_b = st.columns(2)
            
        #     with col_a:
        #         # CO2 emissions over time
        #         df_co2 = live_df.copy()
        #         df_co2["co2"] = df_co2["energy"] * CARBON_EMISSION_FACTOR
        #         fig_co2 = go.Figure()

        #         fig_co2.add_trace(go.Scatter(
        #             x=df_co2["created_at"],
        #             y=df_co2["co2"],
        #             mode="lines",
        #             line=dict(color="#00cc96", width=4),
        #             fill="tozeroy",
        #             fillcolor="rgba(0, 204, 150, 0.2)",
        #             name="CO₂ Emissions"
        #         ))

        #         fig_co2.update_layout(
        #             title="🌱 Cumulative CO₂ Emissions",
        #             xaxis_title="Time",
        #             yaxis_title="CO₂ (kg)",
        #             height=350,
        #             plot_bgcolor="rgba(0,0,0,0)",
        #             paper_bgcolor="rgba(0,0,0,0)",
        #             font=dict(color="white")
        #         )

        #         st.plotly_chart(fig_co2, use_container_width=True)
            
        #     with col_b:
        #         # Energy consumption gauge
        #         fig_gauge = go.Figure(go.Indicator(
        #             mode = "gauge+number+delta",
        #             value = latest['energy'],
        #             domain = {'x': [0, 1], 'y': [0, 1]},
        #             title = {'text': "Energy Consumption (kWh)"},
        #             delta = {'reference': live_df['energy'].mean()},
        #             gauge = {
        #                 'axis': {'range': [None, live_df['energy'].max() * 1.1]},
        #                 'bar': {'color': "darkblue"},
        #                 'steps': [
        #                     {'range': [0, live_df['energy'].mean()], 'color': 'lightgray'},
        #                     {'range': [live_df['energy'].mean(), live_df['energy'].max()], 'color': 'gray'}
        #                 ],
        #             }
        #         ))
        #         st.plotly_chart(fig_gauge, use_container_width=True)

    with main_col2:
        st.subheader("System Status & Alerts")

        # Determine system status
        current_time = pd.Timestamp.now(tz="Asia/Kuala_Lumpur")
        data_time = latest['created_at']
        time_diff = (current_time - data_time).total_seconds()

        if time_diff < 120:
            status_emoji, status_text = "🟢", "LIVE"
            bg_color, border_color, text_color = "#d1e7dd", "#28a745", "#0f5132"
        elif time_diff < 600:
            status_emoji, status_text = "🟡", "DELAYED"
            bg_color, border_color, text_color = "#fff3cd", "#ffc107", "#664d03"
        else:
            status_emoji, status_text = "🔴", "OFFLINE"
            bg_color, border_color, text_color = "#f8d7da", "#dc3545", "#58151c"

        # System Status card (same as alert cards)
        st.markdown(f"""
        <div style='background:{bg_color}; border-left:5px solid {border_color}; padding:1rem; 
                    margin:0.5rem 0; border-radius:8px; height:120px; display:flex; align-items:center;'>
            <span style='font-size:1.5rem; margin-right:0.5rem;'>{status_emoji}</span>
            <div>
                <strong style='color:{text_color}; font-size:1.2rem;'>{status_text}</strong>
                <p style='margin:0.2rem 0 0 0; font-size:0.9rem; color:{text_color};'>
                    Last update: {data_time.strftime('%H:%M:%S')}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)



        # Alerts section
        st.subheader("Active Alerts")
        
        alerts = []

        # Power Alert
        # if latest['power'] > power_threshold:
        #     alerts.append(("🔴", "CRITICAL", "High Power Consumption",
        #                 f"Power at {latest['power']:.1f} W exceeds {power_threshold} W threshold"))
        # Power Alert
        if latest['power'] > power_threshold:
            alert_msg = (
                f"⚠️ HIGH POWER ALERT!\n"
                f"Power is at {latest['power']:.1f} W\n"
                f"Threshold: {power_threshold} W\n"
            )
            alerts.append(("🔴", "CRITICAL", "High Power Consumption",
                        f"Power at {latest['power']:.1f} W exceeds {power_threshold} W threshold"))
            
            # Send Telegram alert
            send_telegram_alert(alert_msg)


        # Current Alert
        # if latest['current'] > current_threshold:
        #     alerts.append(("🔴", "CRITICAL", "High Current Detected",
        #                 f"Current at {latest['current']:.2f} A exceeds {current_threshold} A threshold"))
        # Current Alert
        if latest['current'] > current_threshold:
            alert_msg = (
                f"⚠️ HIGH CURRENT ALERT!\n"
                f"Current is at {latest['current']:.2f} A\n"
                f"Threshold: {current_threshold} A\n"
            )
            alerts.append(("🔴", "CRITICAL", "High Current Detected",
                        f"Current at {latest['current']:.2f} A exceeds {current_threshold} A threshold"))

            # Send Telegram alert
            send_telegram_alert(alert_msg)


        
        if not alerts:
            st.markdown(f"""
            <div class='metric-card' style='height: 100px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);'>
                <div style='text-align: center; color: white;'>
                    <h4 style="margin: 0; font-size: 1.2rem;">✅ All Systems Normal</h4>
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">No active alerts detected</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for emoji, severity, title, message in alerts:
                color = "#dc3545" if severity == "CRITICAL" else "#ffc107"
                st.markdown(f"""
                <div style='background: {color}15; border-left: 4px solid {color}; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                    <div style='display: flex; align-items: start; gap: 0.5rem;'>
                        <span style='font-size: 1.2rem;'>{emoji}</span>
                        <div>
                            <strong style='color: {color};'>{title}</strong>
                            <p style='margin: 0.2rem 0 0 0; color: #666; font-size: 0.9rem;'>{message}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Quick stats in card format
        st.subheader("Quick Stats")
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #1f77b4; margin-bottom: 0.5rem;'>
                <div style='font-size: 0.9rem; color: #6c757d;'>Peak Power</div>
                <div style='font-size: 1.2rem; font-weight: bold; color: #1f77b4;'>{live_df['power'].max():.1f} W</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #ff7f0e; margin-bottom: 0.5rem;'>
                <div style='font-size: 0.9rem; color: #6c757d;'>Avg Voltage</div>
                <div style='font-size: 1.2rem; font-weight: bold; color: #ff7f0e;'>{live_df['voltage'].mean():.1f} V</div>
            </div>
            """, unsafe_allow_html=True)
        
        with stats_col2:
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 0.5rem;'>
                <div style='font-size: 0.9rem; color: #6c757d;'>Data Points</div>
                <div style='font-size: 1.2rem; font-weight: bold; color: #28a745;'>{len(live_df)}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #9467bd; margin-bottom: 0.5rem;'>
                <div style='font-size: 0.9rem; color: #6c757d;'>Session Duration</div>
                <div style='font-size: 1.2rem; font-weight: bold; color: #9467bd;'>{(live_df['created_at'].max() - live_df['created_at'].min()).total_seconds()/3600:.1f} h</div>
            </div>
            """, unsafe_allow_html=True)

        # System Parameters in card format
        st.subheader("Current Operating Parameters")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1rem; border-radius: 12px; border-left: 4px solid #1f77b4;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 0.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;">Live Parameters</h4>
        </div>
        """, unsafe_allow_html=True)

        param_cols = st.columns(2)
        with param_cols[0]:
            st.metric("🔌 Power", f"{latest.get('power',0):.1f} W", label_visibility="visible")
            st.metric("⚡ Voltage", f"{latest.get('voltage',0):.1f} V", label_visibility="visible")
            st.metric("🎯 Power Factor", f"{latest.get('power_factor',0.9):.2f}", label_visibility="visible")
        with param_cols[1]:
            st.metric("🔋 Current", f"{latest.get('current',0):.3f} A", label_visibility="visible")
            st.metric("📡 Frequency", f"{latest.get('frequency',50):.1f} Hz", label_visibility="visible")
            st.metric("📊 Energy Rate", f"{latest.get('energy_increment_kwh',0):.3f} kWh", label_visibility="visible")

    # =========================
    # BOTTOM SECTION - TREND SPARKLINES
    # =========================
    st.markdown("---")
    st.subheader("Live Parameter Trends")
    
    # Create sparkline charts for quick overview
    trend_cols = st.columns(6)
    trends = [
        ('⚡ Voltage', 'voltage', 'V', '#ff7f0e'),
        ('🔌 Current', 'current', 'A', '#d62728'),
        ('🔋 Power', 'power', 'W', '#1f77b4'),
        ('📊 Energy', 'energy', 'kWh', '#2ca02c'),
        ('🎯 Power Factor', 'power_factor', '', '#9467bd'),
        ('🌱 CO₂', 'energy', 'kg', '#28a745')
    ]
    
    for i, (name, col, unit, color) in enumerate(trends):
        with trend_cols[i]:
            if col == 'energy' and name == '🌱 CO₂':
                values = live_df['energy'] * CARBON_EMISSION_FACTOR
                current_val = latest['energy'] * CARBON_EMISSION_FACTOR
            else:
                values = live_df[col]
                current_val = latest[col]
            
            fig = px.line(values, x=live_df['created_at'], y=values, 
                         height=80, color_discrete_sequence=[color])
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis_visible=False,
                yaxis_visible=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"{name}: {current_val:.1f}{unit}")
# endregion


# region PREDICTIVE ANALYTICS
elif mode == "Predictive Analytics":
    st.markdown("<h1 class='dashboard-title'>Energy Consumption Forecasting</h1>", unsafe_allow_html=True)

    # st.markdown('<h2 style="color: #1f77b4; margin-top: 0;">Energy Consumption Forecasting</h2>', unsafe_allow_html=True)

    # -------------------------
    # MODEL CONFIG
    # -------------------------
    LR_MODEL_PATH = "models/lr_model_st.pkl"
    RF_MODEL_PATH = "models/rf_model_st.pkl"
    SCALER_PATH = "models/scaler_st.pkl"
    FEATURES_PATH = "models/feature_names.pkl"
    THRESHOLD_PATH = "models/best_threshold_rf.pkl"
    CARBON_EMISSION_FACTOR = 0.774  # kgCO2 per kWh

    # -------------------------
    # LOAD MODELS
    # -------------------------
    @st.cache_resource
    def load_models():
        try:
            lr_model = joblib.load(LR_MODEL_PATH)
            rf_model = joblib.load(RF_MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            with open(FEATURES_PATH, "rb") as f:
                feature_names = pickle.load(f)
            with open(THRESHOLD_PATH, "rb") as f:
                best_threshold = pickle.load(f)

            return lr_model, rf_model, scaler, feature_names, best_threshold
        except Exception as e:
            st.error(f"Error loading models: {e}")
            return None, None, None, None, None

    lr_model, rf_model, scaler, feature_names, best_threshold = load_models()

    # -------------------------
    # FETCH & PROCESS DATA
    # -------------------------
    try:
        # live_df = fetch_thingspeak(CHANNEL_ID, READ_KEY, results=100)
        live_df = get_all_data()

        live_df['created_at'] = pd.to_datetime(live_df['created_at'])

        # ================================================================
        # CLEAN DATA FIRST (creates energy_diff + energy_increment_kwh)
        # ================================================================
        numeric_cols = ['voltage','current','power','energy','frequency','power_factor']
        for col in numeric_cols:
            if col in live_df.columns:
                live_df[col] = pd.to_numeric(live_df[col], errors='coerce').fillna(0)

        live_df = clean_data(live_df)          # <-- creates energy_diff + energy_increment_kwh
        live_df = add_ml_features(live_df)     # <-- uses increments

        # ================================================================
        # NOW perform minute-level aggregation
        # ================================================================
        live_df['created_at'] = live_df['created_at'].dt.floor('min')

        agg_rules = {
            'voltage': 'mean',
            'current': 'mean',
            'power': 'mean',
            'energy': 'last',
            'energy_increment_kwh': 'sum',
            'energy_diff': 'sum',
            'frequency': 'mean',
            'power_factor': 'mean'
        }

        live_df = live_df.groupby('created_at', as_index=False).agg(agg_rules)
        live_df = live_df.sort_values("created_at").reset_index(drop=True)

        # # ================================================================
        # # FORCE LIVE DATA TO MINUTE-LEVEL AGGREGATION (MATCH ML TRAINING)
        # # ================================================================
        # # 1️⃣ Round timestamps to nearest minute
        # live_df['created_at'] = live_df['created_at'].dt.floor('min')

        # # 2️⃣ Aggregation rules (must match your training notebook)
        # agg_rules = {
        #     'voltage': 'mean',
        #     'current': 'mean',
        #     'power': 'mean',
        #     'energy': 'last',
        #     'energy_increment_kwh': 'sum',  # sum increments inside the same minute
        #     'energy_diff': 'sum',
        #     'frequency': 'mean',
        #     'power_factor': 'mean'
        # }

        # # Apply minute-level aggregation
        # live_df = live_df.groupby('created_at', as_index=False).agg(agg_rules)

        # # 3️⃣ Sort again, just in case
        # live_df = live_df.sort_values('created_at').reset_index(drop=True)

        # --- APPLY TIME RANGE FILTER HERE ---
        now = pd.Timestamp.now(tz="Asia/Kuala_Lumpur")

        if time_range == "Last 1 Hour":
            live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(hours=1)]

        elif time_range == "Last 6 Hours":
            live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(hours=6)]

        elif time_range == "Last 24 Hours":
            live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(hours=24)]

        elif time_range == "Last Week":
            live_df = live_df[live_df['created_at'] >= now - pd.Timedelta(days=7)]

        elif time_range == "Custom Range" and start_date and end_date:
            live_df = live_df[
                (live_df["created_at"].dt.date >= start_date) &
                (live_df["created_at"].dt.date <= end_date)
            ]

        # If no data available
        if live_df.empty:
            st.warning("No data available for the selected time range.")
            st.stop()

        # Continue cleaning and ML feature creation
        numeric_cols = ['voltage','current','power','energy','frequency','power_factor']
        for col in numeric_cols:
            if col in live_df.columns:
                live_df[col] = pd.to_numeric(live_df[col], errors='coerce').fillna(0)

        live_df = clean_data(live_df)
        live_df = add_ml_features(live_df)
        # ROUND live data timestamps to minute-level
        live_df['created_at'] = live_df['created_at'].dt.floor('min')

        # AGGREGATE to 1 minute like your training pipeline
        agg_dict = {
            'voltage': 'mean',
            'current': 'mean',
            'power': 'mean',
            'energy': 'last',
            'energy_increment_kwh': 'sum',
            'frequency': 'mean',
            'power_factor': 'mean',
        }

        live_df = live_df.groupby('created_at', as_index=False).agg(agg_dict)

        # live_df = live_df.sort_values("created_at")
        # # =====================================================================
        # # DETECT ACTUAL SAMPLING INTERVAL FROM LIVE DATA
        # # =====================================================================
        # time_diffs = live_df['created_at'].diff().dt.total_seconds() / 60

        # # Only use positive time differences
        # valid_diffs = time_diffs[time_diffs > 0]

        # if len(valid_diffs) > 0:
        #     sampling_interval_min = valid_diffs.median()
        #     st.info(f"📡 Estimated Sampling Interval: {sampling_interval_min:.2f} minutes per sample")
        # else:
        #     sampling_interval_min = 1  # fallback value
        #     st.warning("⚠️ Unable to detect sampling interval. Assuming 1 minute.")



    except Exception as e:
        st.error(f"Error fetching or preprocessing data: {e}")
        live_df = pd.DataFrame()

    # -------------------------
    # PREDICTION FUNCTION
    # -------------------------
    def predict(df, lr_model, rf_model, scaler, feature_names):
        if df.empty or lr_model is None or rf_model is None:
            df['predicted_energy'] = 0.0
            df['high_energy_flag'] = 0
            return df

        df = add_ml_features(df)

        X = df.copy()
        for col in feature_names:
            if col not in X.columns:
                X[col] = 0
        X = X[feature_names]

        X_scaled = pd.DataFrame(scaler.transform(X[scaler.feature_names_in_]), columns=scaler.feature_names_in_)

        df['predicted_energy'] = lr_model.predict(X_scaled)
        X_scaled['predicted_energy'] = df['predicted_energy']
        
        # ---- NEW THRESHOLD CLASSIFICATION ----
        prob = rf_model.predict_proba(X_scaled)[:, 1]
        df['high_energy_flag'] = (prob >= best_threshold).astype(int)


        return df

    live_df = predict(live_df, lr_model, rf_model, scaler, feature_names)

    # -------------------------
    # LATEST DATA
    # -------------------------
    if live_df.empty:
        latest = pd.Series({'power':0,'voltage':0,'current':0,'energy':0,'power_factor':0.9,'frequency':50,'high_energy_flag':0})
    else:
        latest = live_df.iloc[-1]

    latest_prediction = latest.get('predicted_energy',0.0)
    actual_energy = latest.get('energy',0.0)
    total_with_prediction = actual_energy + latest_prediction
    co2 = total_with_prediction * CARBON_EMISSION_FACTOR
    high_energy_flag = int(latest.get('high_energy_flag',0))

    # ------------------------
    # High Energy Alert
    # ------------------------
    if high_energy_flag == 1:
        cumulative_co2 = latest.get('energy', 0.0) * CARBON_EMISSION_FACTOR
        alert_message = (
            f"⚠️ <b>High Energy Consumption Predicted!</b><br>"
            f"Predicted Energy: {latest_prediction:.3f} kWh<br>"
            f"Cumulative Energy: {latest.get('energy',0.0):.3f} kWh<br>"
            f"Estimated Cumulative CO₂: {cumulative_co2:.2f} kg<br>"
            "Consider turning off high-power devices or rescheduling usage."
        )

        # Display in dashboard
        st.markdown(f"""
        <div style='background:#fff3cd; border-left:5px solid #ffc107; 
                    color:#664d03; padding:1rem; border-radius:8px; 
                    margin:0.5rem 0; font-size:0.95rem;'>{alert_message}</div>
        """, unsafe_allow_html=True)

        # Telegram message
        telegram_message = (
            f"⚠️ High Energy Consumption Predicted!\n"
            f"Predicted Energy: {latest_prediction:.3f} kWh\n"
            f"Cumulative Energy: {latest.get('energy',0.0):.3f} kWh\n"
            f"Estimated Cumulative CO₂: {cumulative_co2:.2f} kg\n"
            "Consider turning off high-power devices or rescheduling usage."
        )
        send_telegram_alert(telegram_message)

    # -------------------------
    # ENHANCED VISUALIZATIONS
    # -------------------------
    st.subheader("Forecasting Performance")
    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        if len(live_df) > 1:
            prev_actual = live_df.iloc[-2].get('energy_increment_kwh', 0)
            accuracy_color = "#28a745" if abs(latest_prediction - prev_actual) < 0.01 else "#ffc107"
            accuracy_text = "High" if abs(latest_prediction - prev_actual) < 0.01 else "Moderate"
            st.markdown(f"""
            <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
                <div style="line-height:0.9; text-align:center;">
                    <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">Prediction Accuracy</h4>
                    <h2 style="font-size:2.4rem; margin:0; padding:0; color:{accuracy_color}; font-weight:700;">{accuracy_text}</h2>
                    <p style="font-size:0.9rem; margin:0; padding:0; color:white;">Model Confidence</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with kpi_cols[1]:
        if len(live_df) > 5:
            recent_avg = live_df['energy_increment_kwh'].tail(5).mean()
            trend = "Increasing" if latest_prediction > recent_avg else "Stable"
            trend_color = "#dc3545" if latest_prediction > recent_avg else "#28a745"
            st.markdown(f"""
            <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
                <div style="line-height:0.9; text-align:center;">
                    <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">Consumption Trend</h4>
                    <h2 style="font-size:2.4rem; margin:0; padding:0; color:{trend_color}; font-weight:700;">{trend}</h2>
                    <p style="font-size:0.9rem; margin:0; padding:0; color:white;">Next 5-min Forecast</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with kpi_cols[2]:
        alert_color = "#dc3545" if high_energy_flag == 1 else "#28a745"
        alert_text = "High" if high_energy_flag == 1 else "Normal"
        st.markdown(f"""
        <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
            <div style="line-height:0.9; text-align:center;">
                <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">Energy Alert</h4>
                <h2 style="font-size:2.4rem; margin:0; padding:0; color:{alert_color}; font-weight:700;">{alert_text}</h2>
                <p style="font-size:0.9rem; margin:-5px 0 0 0; padding:0; color:white;">Risk Assessment</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        st.markdown(f"""
        <div class='metric-card' style='height:140px; display:flex; flex-direction:column; justify-content:center;'>
            <div style="line-height:0.9; text-align:center;">
                <h4 style="font-size:1.3rem; margin:0; padding:0; color:white;">Carbon Impact</h4>
                <h2 style="font-size:2.4rem; margin:0; padding:0; color:#17a2b8; font-weight:700;">{co2:.2f}kgCO₂</h2>
                <p style="font-size:0.9rem; margin:-5px 0 0 0; padding:0; color:white;">CO₂ Equivalent</p>
            </div>
        </div>
        """, unsafe_allow_html=True)


    # Main Content Area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Actual vs Predicted Comparison
        st.subheader("Actual vs Predicted Energy Consumption")
        
        if not live_df.empty and len(live_df) > 5:
            # Create comparison data
            comparison_df = live_df.tail(10).copy()
            
            # Calculate prediction accuracy for previous points
            if len(comparison_df) > 1:
                comparison_df['prev_actual'] = comparison_df['energy_increment_kwh'].shift(-1)
                comparison_df['prediction_error'] = comparison_df['predicted_energy'] - comparison_df['prev_actual']
                latest_accuracy = f"{abs(comparison_df['prediction_error'].iloc[-2]):.3f}" if not pd.isna(comparison_df['prediction_error'].iloc[-2]) else "N/A"
            
            # Create dual-axis chart
            fig_comparison = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Actual energy increments
            fig_comparison.add_trace(
                go.Scatter(x=comparison_df['created_at'], 
                          y=comparison_df['energy_increment_kwh'], 
                          name="Actual Energy", 
                          line=dict(color='#1f77b4', width=3)),
                secondary_y=False,
            )
            
            # Predicted energy
            fig_comparison.add_trace(
                go.Scatter(x=comparison_df['created_at'], 
                          y=comparison_df['predicted_energy'], 
                          name="Predicted Energy", 
                          line=dict(color='#ff7f0e', width=3, dash='dot')),
                secondary_y=False,
            )
            
            # Prediction error (if available)
            if 'prediction_error' in comparison_df.columns:
                fig_comparison.add_trace(
                    go.Bar(x=comparison_df['created_at'], 
                          y=comparison_df['prediction_error'], 
                          name="Prediction Error", 
                          marker_color='#d62728', opacity=0.3),
                    secondary_y=True,
                )
            
            fig_comparison.update_layout(
                title="Energy Consumption: Actual vs Predicted",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#2c3e50'),
                height=400
            )
            fig_comparison.update_yaxes(title_text="Energy (kWh)", secondary_y=False)
            fig_comparison.update_yaxes(title_text="Prediction Error", secondary_y=True)
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Accuracy metrics
            acc_cols = st.columns(3)
            with acc_cols[0]:
                st.metric("Latest Prediction", f"{latest_prediction:.3f} kWh")
            with acc_cols[1]:
                if len(comparison_df) > 1 and not pd.isna(comparison_df['prediction_error'].iloc[-2]):
                    error = comparison_df['prediction_error'].iloc[-2]
                    st.metric("Last Prediction Error", f"{error:.3f} kWh")
            with acc_cols[2]:
                st.metric("Model Confidence", "High" if abs(latest_prediction) > 0.001 else "Calibrating")

        # Feature Importance Visualization
        st.subheader("Model Insights")
        if lr_model is not None and hasattr(lr_model, 'coef_') and feature_names is not None:
            # Get top 8 most important features
            importance_df = pd.DataFrame({
                'feature': feature_names[:len(lr_model.coef_)],
                'importance': np.abs(lr_model.coef_)
            }).nlargest(8, 'importance')
            
            fig_importance = px.bar(importance_df, x='importance', y='feature', 
                                  orientation='h', 
                                  title="Top Influencing Factors on Energy Prediction",
                                  color='importance',
                                  color_continuous_scale='Blues')
            fig_importance.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig_importance, use_container_width=True)

    with col2:
        # Enhanced System Status Panel
        st.subheader("System Status & Forecast")
        
        # Current vs Predicted Comparison Card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0d1b1e 0%, #40916c 100%);
                    padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 1rem;">
            <h4 style="margin: 0 0 1rem 0; color: white;">Energy Forecast</h4>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 0.9rem;">Current</div>
                    <div style="font-size: 1.5rem; font-weight: bold;">{actual_energy:.3f} kWh</div>
                </div>
                <div style="font-size: 1.5rem;">→</div>
                <div>
                    <div style="font-size: 0.9rem;">Forecast</div>
                    <div style="font-size: 1.5rem; font-weight: bold;">{total_with_prediction:.3f} kWh</div>
                </div>
            </div>
            <div style="margin-top: 0.5rem; font-size: 0.8rem; opacity: 0.9;">
                +{latest_prediction:.3f} kWh predicted
            </div>
        </div>
        """, unsafe_allow_html=True)

       
        # System Parameters - COMPRESSED VERSION
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                    padding: 1rem; border-radius: 12px; border-left: 4px solid #1f77b4;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 0.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;">Current Operating Parameters</h4>
        </div>
        """, unsafe_allow_html=True)

        param_cols = st.columns(2)
        with param_cols[0]:
            st.metric("Power", f"{latest.get('power',0):.1f} W", label_visibility="visible")
            st.metric("Voltage", f"{latest.get('voltage',0):.1f} V", label_visibility="visible")
            st.metric("Power Factor", f"{latest.get('power_factor',0.9):.2f}", label_visibility="visible")
        with param_cols[1]:
            st.metric("Current", f"{latest.get('current',0):.3f} A", label_visibility="visible")
            st.metric("Frequency", f"{latest.get('frequency',50):.1f} Hz", label_visibility="visible")
            st.metric("Energy Rate", f"{latest.get('energy_increment_kwh',0):.3f} kWh", label_visibility="visible")


        # Model Performance Summary
        st.markdown("---")
        st.subheader("Model Performance")
        
        performance_data = {
            "Model Type": "Ensemble (Linear + Random Forest)",
            "Features Used": len(feature_names) if feature_names else 0,
            "Prediction Horizon": "5 minutes",
            "Update Frequency": "Real-time",
            "Data Points": len(live_df)
        }
        
        for key, value in performance_data.items():
            st.markdown(f"**{key}:** {value}")

    # Bottom Section: Historical Performance
    st.markdown("---")
    st.subheader("Model Performance Over Time")

    if not live_df.empty and len(live_df) > 1:
        performance_df = live_df.copy()
        
        # DEBUG: Show what's in the data
        with st.expander("Debug Data"):
            st.write("Energy Increment Stats:")
            if 'energy_increment_kwh' in performance_df.columns:
                st.write(f"Min: {performance_df['energy_increment_kwh'].min():.6f}")
                st.write(f"Max: {performance_df['energy_increment_kwh'].max():.6f}")
                st.write(f"Mean: {performance_df['energy_increment_kwh'].mean():.6f}")
                st.write(f"Sample values: {list(performance_df['energy_increment_kwh'].head().round(6))}")
            
            st.write("Predicted Energy Stats:")
            if 'predicted_energy' in performance_df.columns:
                st.write(f"Min: {performance_df['predicted_energy'].min():.6f}")
                st.write(f"Max: {performance_df['predicted_energy'].max():.6f}")
                st.write(f"Mean: {performance_df['predicted_energy'].mean():.6f}")
        
        if 'energy_increment_kwh' in performance_df.columns and 'predicted_energy' in performance_df.columns:
            performance_df['abs_error'] = abs(performance_df['predicted_energy'] - performance_df['energy_increment_kwh'])
            avg_error = performance_df['abs_error'].mean()
            max_error = performance_df['abs_error'].max()
            
            # More robust accuracy calculation
            actual_mean = performance_df['energy_increment_kwh'].mean()
            
            perf_cols = st.columns(4)
            with perf_cols[0]:
                st.metric("Mean Absolute Error", f"{avg_error:.6f} kWh")
            with perf_cols[1]:
                st.metric("Max Error", f"{max_error:.6f} kWh")
            with perf_cols[2]:
                if actual_mean > 0:
                    accuracy = max(0, 100 - (avg_error / actual_mean * 100))
                    st.metric("Model Accuracy", f"{accuracy:.1f}%")
                else:
                    st.metric("Model Accuracy", "Calibrating")
            with perf_cols[3]:
                st.metric("Predictions Analyzed", len(performance_df))



# region DEVICE ENERGY & CO₂ INSIGHTS
elif mode == "Device Energy & CO₂ Insights":
    
    st.markdown("""
    <style>
    /* Metric highlights (already colored) */
    .metric-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        margin: 0.5rem;
    }

    /* Device cards (change background to dark mode friendly) */
    .device-card {
        background: #1e1e2f;   /* Dark background */
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.5);
        color: #f5f5f5;        /* Light text for contrast */
    }

    /* Impact badge */
    .impact-badge {
        background: #2e7d32;
        color: #e8f5e8;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)


    # st.markdown('<h1 style="color: #1f77b4; text-align: center;">Device Energy & CO₂ Insights</h1>', unsafe_allow_html=True)
    st.markdown("<h1 class='dashboard-title'>Device Energy & CO₂ Insights</h1>", unsafe_allow_html=True)


    # Initialize Analyzer
    analyzer = DeviceEnergyAnalyzer(DATA_PATH_MIN)
    df = analyzer.preprocess_data()
    single_df = analyzer.analyze_single_device()
    total_df = analyzer.allocate_multi_device_energy()
    summary = analyzer.summary_metrics()

    # -----------------------
    # 1️⃣ OVERVIEW METRICS
    # -----------------------
    st.subheader("Overall Impact Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_energy = total_df['total_energy_kWh'].sum()
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>⚡ Total Energy</h3>
            <h2>{total_energy:.3f} kWh</h2>
            <p>All Devices Combined</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_co2 = total_df['total_CO2_kg'].sum()
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>🌍 Carbon Footprint</h3>
            <h2>{total_co2:.3f} kg</h2>
            <p>CO₂ Emissions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        days_recorded = summary['days_recorded']
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>📅 Monitoring Period</h3>
            <h2>{days_recorded} days</h2>
            <p>Data Collection</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        monthly_co2 = (total_co2 / days_recorded) * 30
        st.markdown(f"""
        <div class="metric-highlight">
            <h3>📈 Monthly Projection</h3>
            <h2>{monthly_co2:.3f} kgCO₂</h2>
            <p>Estimated CO₂/month</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------
    # 2️⃣ DEVICE PERFORMANCE METRICS
    # -----------------------
    st.subheader("Device-Level Performance")

    # Create columns: 2/3 left for charts, 1/3 right for table
    left_col, right_col = st.columns([2, 1])

    with left_col:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Energy Consumption", "Carbon Impact", "Efficiency Analysis"])

        with tab1:
            # Energy consumption by device (bar chart)
            fig_energy = px.bar(
                total_df.sort_values('total_energy_kWh', ascending=False),
                x='device', y='total_energy_kWh',
                title="Total Energy Consumption per Device",
                color='total_energy_kWh',
                color_continuous_scale='Viridis',
                text_auto='.3f'
            )
            fig_energy.update_layout(xaxis_title="Device", yaxis_title="Energy (kWh)")
            st.plotly_chart(fig_energy, use_container_width=True)

        with tab2:
            # CO2 impact by device (pie chart)
            fig_co2 = px.pie(
                total_df, 
                values='total_CO2_kg', 
                names='device',
                title="CO₂ Emission Distribution by Device",
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig_co2, use_container_width=True)

        with tab3:
            # Power efficiency analysis (scatter)
            efficiency_df = single_df[['device', 'avg_power_W', 'avg_energy_kWh']].copy()
            efficiency_df['efficiency_score'] = 100 / (efficiency_df['avg_power_W'] + 1)
            
            fig_efficiency = px.scatter(
                efficiency_df,
                x='avg_power_W',
                y='avg_energy_kWh',
                size='avg_power_W',
                color='device',
                title="Device Power vs Energy Efficiency",
                labels={'avg_power_W': 'Average Power (W)', 'avg_energy_kWh': 'Energy per Use (kWh)'}
            )
            st.plotly_chart(fig_efficiency, use_container_width=True)

    with right_col:
        # Display the actual numbers table (Energy Consumption Details)
        st.subheader("Energy Consumption Details")
        energy_display = total_df[['device', 'total_energy_kWh']].copy()
        energy_display = energy_display.sort_values('total_energy_kWh', ascending=False)
        energy_display.columns = ['Device', 'Total Energy (kWh)']
        energy_display['Total Energy (kWh)'] = energy_display['Total Energy (kWh)'].round(4)
        st.dataframe(energy_display, use_container_width=True)


    # -----------------------
    # 3️⃣ PRACTICAL CALCULATOR
    # -----------------------
    st.markdown("---")
    st.subheader("Energy & Carbon Calculator")
    
    st.markdown("""
    <div class="device-card">
        <p><strong>See how device usage translates to energy and carbon:</strong></p>
        <p>Based on your actual device measurements, calculate the impact of different usage patterns.</p>
    </div>
    """, unsafe_allow_html=True)
    
    calc_col1, calc_col2, calc_col3 = st.columns([2, 1, 2])
    
    with calc_col1:
        selected_device = st.selectbox(
            "Select a device:",
            options=single_df['device'].tolist(),
            index=0
        )
        
        usage_minutes = st.slider(
            f"Daily usage minutes for {selected_device}:",
            min_value=1,
            max_value=480,
            value=60,
            step=1
        )
    
    with calc_col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("**→**")
    
    with calc_col3:
        if selected_device:
            device_data = single_df[single_df['device'] == selected_device].iloc[0]
            
            # Calculate impacts
            daily_energy = device_data['avg_energy_kWh'] * usage_minutes
            daily_co2 = daily_energy * analyzer.co2_factor
            weekly_energy = daily_energy * 7
            weekly_co2 = daily_co2 * 7
            monthly_energy = daily_energy * 30
            monthly_co2 = daily_co2 * 30
            
            st.markdown(f"""
            <div class="device-card">
                <h4>{selected_device.title()} Impact</h4>
                <p><strong>Daily:</strong> {daily_energy:.4f} kWh | {daily_co2:.4f} kg CO₂</p>
                <p><strong>Weekly:</strong> {weekly_energy:.4f} kWh | {weekly_co2:.4f} kg CO₂</p>
                <p><strong>Monthly:</strong> {monthly_energy:.4f} kWh | {monthly_co2:.4f} kg CO₂</p>
                <p><small>Based on {device_data['count_active']} actual usage observations</small></p>
            </div>
            """, unsafe_allow_html=True)

    # -----------------------
    # 4️⃣ KEY INSIGHTS FROM YOUR DATA
    # -----------------------
    st.markdown("---")
    st.subheader("Key Insights from Your Data")

    # Generate insights based on actual numbers
    insights = []

    # Find top energy consumer
    top_energy_device = total_df.loc[total_df['total_energy_kWh'].idxmax()]
    insights.append(f"<strong>Highest Energy Consumer</strong>: {top_energy_device['device'].title()} used {top_energy_device['total_energy_kWh']:.3f} kWh total")

    # Find most efficient device (lowest power with reasonable usage)
    efficient_devices = single_df[single_df['count_active'] > 10].nsmallest(1, 'avg_power_W')
    if not efficient_devices.empty:
        efficient_device = efficient_devices.iloc[0]
        insights.append(f"<strong>Most Efficient</strong>: {efficient_device['device'].title()} uses only {efficient_device['avg_power_W']:.1f}W average power")

    # Carbon intensity insight
    carbon_intensity = total_co2 / total_energy if total_energy > 0 else 0
    insights.append(f"<strong>Carbon Intensity</strong>: {carbon_intensity:.3f} kg CO₂ per kWh consumed")

    # Usage frequency insight
    most_used_device = single_df.loc[single_df['count_active'].idxmax()]
    insights.append(f"<strong>Most Frequently Used</strong>: {most_used_device['device'].title()} was active {most_used_device['count_active']} times")

    # Display insights
    for insight in insights:
        st.markdown(f'<div class="device-card">{insight}</div>', unsafe_allow_html=True)

    # -----------------------
    # 5️⃣ QUICK COMPARISONS
    # -----------------------
    st.markdown("---")
    st.subheader("Quick Comparisons")
    
    comp_col1, comp_col2 = st.columns(2)
    
    with comp_col1:
        st.markdown("**Energy Consumption Ranking**")
        ranked_energy = total_df.sort_values('total_energy_kWh', ascending=False)
        for i, (_, device) in enumerate(ranked_energy.iterrows(), 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
            st.write(f"{emoji} {device['device'].title()}: {device['total_energy_kWh']:.3f} kWh")
    
    with comp_col2:
        st.markdown("**Carbon Emission Ranking**")
        ranked_co2 = total_df.sort_values('total_CO2_kg', ascending=False)
        for i, (_, device) in enumerate(ranked_co2.iterrows(), 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
            st.write(f"{emoji} {device['device'].title()}: {device['total_CO2_kg']:.3f} kg CO₂")

    # -----------------------
    # 6️⃣ DATA SUMMARY CARD
    # -----------------------
    st.markdown("---")
    st.subheader("Data Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Total Devices Tracked", len(single_df))
        st.metric("Total Data Points", f"{len(df):,}")
    
    with summary_col2:
        avg_power_all = single_df['avg_power_W'].mean()
        st.metric("Average Device Power", f"{avg_power_all:.1f} W")
        st.metric("CO₂ Factor Used", f"{analyzer.co2_factor} kg/kWh")
    
    with summary_col3:
        date_range = f"{df['created_at'].min().strftime('%b %d')} to {df['created_at'].max().strftime('%b %d')}"
        st.metric("Data Collection Period", date_range)
        st.metric("Monitoring Duration", f"{days_recorded} days")

# endregion
# region FOOTER
# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #6c757d; font-size: 0.85rem;'>"
    "Smart Tenaga Monitoring System | "
    f"Last Data Point: {pd.Timestamp.now().tz_localize('Asia/Kuala_Lumpur').strftime('%Y-%m-%d %H:%M:%S')}"
    "</p>", unsafe_allow_html=True
)
# endregion