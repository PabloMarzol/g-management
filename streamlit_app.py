# streamlit_app.py - Safe production version
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import uuid
import time

# Configure page
st.set_page_config(
    page_title="ALMA - Financial Exchange Control Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state"""
    defaults = {
        'authenticated': False,
        'user_role': None,
        'user_name': None,
        'operations_data': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def authenticate_user(username: str, password: str):
    """Simple authentication"""
    demo_users = {
        "admin": {"role": "admin", "name": "Administrator"},
        "fx_provider": {"role": "fx_provider", "name": "FX Provider"},
        "jessica": {"role": "collector", "name": "Jessica Garcia"}
    }
    
    if username in demo_users and password in ["admin123", "fx123", "jessica123"]:
        return demo_users[username]
    return None

def get_sample_operations_data():
    """Generate sample operations data"""
    import random
    
    clients = ["John Smith", "Maria Garcia", "David Chen", "Sarah Johnson", "Michael Brown", "Lisa Wang"]
    collectors = ["Jessica", "Carlos", "Miguel", "Ana"]
    fx_providers = ["AlphaExchange", "BetaFX", "GammaFX", "DeltaFX"]
    statuses = ["Pending", "Assigned", "Collecting", "Collected", "Validated", "FX Processing", "Completed"]
    priorities = ["Normal", "High", "Urgent"]
    
    operations = []
    for i in range(20):
        amount = random.randint(5000, 35000)
        operations.append({
            'id': str(uuid.uuid4()),
            'operation_id': f"MSB-2025-08-18-{100+i}",
            'client_name': random.choice(clients),
            'amount_usd': amount,
            'status': random.choice(statuses),
            'collector': random.choice(collectors),
            'fx_provider': random.choice(fx_providers),
            'created_at': datetime.now() - timedelta(hours=random.randint(1, 72)),
            'estimated_usdt': amount * 0.95,
            'commission_amount': amount * 0.05,
            'pickup_address': f"{random.randint(100, 999)} Main St, City {i+1}",
            'priority': random.choice(priorities),
            'notes': f"Sample operation notes {i+1}"
        })
    
    return pd.DataFrame(operations)

def format_currency(amount):
    """Format currency with proper separators"""
    return f"${amount:,.2f}"

def login_page():
    st.markdown('<h1 class="main-header">🏦 ALMA Login</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome to ALMA Financial Exchange Control Platform")
        
        with st.form("login"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            with st.expander("🔑 Demo Credentials", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Administrator:**")
                    st.code("Username: admin\nPassword: admin123")
                with col_b:
                    st.write("**FX Provider:**")
                    st.code("Username: fx_provider\nPassword: fx123")
            
            if st.form_submit_button("🚀 Login", use_container_width=True):
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_role = user["role"]
                        st.session_state.user_name = user["name"]
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.error("⚠️ Please enter username and password")

def admin_dashboard():
    st.markdown('<h1 class="main-header">📊 Administrator Dashboard</h1>', unsafe_allow_html=True)
    
    # Load sample data
    if st.session_state.operations_data is None:
        st.session_state.operations_data = get_sample_operations_data()
    
    operations_df = st.session_state.operations_data
    
    # Calculate metrics
    total_ops = len(operations_df)
    total_volume = operations_df['amount_usd'].sum()
    completed_ops = len(operations_df[operations_df['status'] == 'Completed'])
    active_ops = len(operations_df[operations_df['status'].isin(['Pending', 'Assigned', 'Collecting', 'Collected', 'Validated', 'FX Processing'])])
    total_commission = operations_df['commission_amount'].sum()
    
    # Enhanced metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Operations", active_ops, delta="+3 from yesterday")
    with col2:
        st.metric("Total Volume", format_currency(total_volume), delta=f"+{total_volume*0.15:,.0f}")
    with col3:
        st.metric("Completed", completed_ops, delta="+2 today")
    with col4:
        st.metric("Commission", format_currency(total_commission), delta=f"+{total_commission*0.12:,.0f}")
    
    # Recent operations
    st.markdown("### 📋 Recent Operations")
    
    for _, op in operations_df.head(8).iterrows():
        with st.expander(
            f"🔹 {op['operation_id']} - {op['client_name']} - {format_currency(op['amount_usd'])} - {op['status']}",
            expanded=False
        ):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown("**📋 Operation Details**")
                st.write(f"**Status:** {op['status']}")
                st.write(f"**Priority:** {op['priority']}")
                st.write(f"**Collector:** {op['collector']}")
                st.write(f"**FX Provider:** {op['fx_provider']}")
            
            with col2:
                st.markdown("**💰 Financial Details**")
                st.write(f"**Amount USD:** {format_currency(op['amount_usd'])}")
                st.write(f"**Estimated USDT:** {op['estimated_usdt']:,.2f}")
                st.write(f"**Commission:** {format_currency(op['commission_amount'])}")
                st.write(f"**Created:** {op['created_at'].strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                st.markdown("**⚡ Actions**")
                if st.button("📋 Manage", key=f"manage_{op['operation_id']}"):
                    st.info(f"Managing operation {op['operation_id']}")
    
    # Analytics charts
    if not operations_df.empty:
        st.markdown("### 📊 Analytics Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            status_counts = operations_df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values, 
                names=status_counts.index,
                title="Operations by Status",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            collector_volume = operations_df.groupby('collector')['amount_usd'].sum().reset_index()
            fig_volume = px.bar(
                collector_volume,
                x='collector',
                y='amount_usd',
                title="Volume by Collector"
            )
            st.plotly_chart(fig_volume, use_container_width=True)

def fx_provider_dashboard():
    st.markdown('<h1 class="main-header">🔄 FX Provider Dashboard</h1>', unsafe_allow_html=True)
    
    # Sample FX provider operations
    st.info("FX Provider functionality - showing assigned operations")
    
    # Show some sample operations
    sample_ops = pd.DataFrame([
        {"operation_id": "MSB-2025-08-18-001", "client": "John Smith", "amount": 15000, "status": "FX Processing"},
        {"operation_id": "MSB-2025-08-18-002", "client": "Maria Garcia", "amount": 8500, "status": "Completed"},
    ])
    
    st.dataframe(sample_ops, use_container_width=True)

def main_app():
    # Sidebar with user info
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.user_name}")
        st.markdown(f"**Role:** {st.session_state.user_role.title()}")
        st.markdown(f"**Session:** {datetime.now().strftime('%H:%M:%S')}")
        
        st.divider()
        
        # System status
        st.markdown("### 🔴 System Status")
        st.success("✅ System: Operational")
        st.success("✅ Demo Mode: Active")
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith(('authenticated', 'user_')):
                    del st.session_state[key]
            st.rerun()
    
    # Main content based on role
    if st.session_state.user_role == "admin":
        admin_dashboard()
    elif st.session_state.user_role == "fx_provider":
        fx_provider_dashboard()
    else:
        st.info("Dashboard for your role is being developed.")

def main():
    """Main application entry point"""
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()