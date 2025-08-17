import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import asyncio
from typing import Optional, List, Dict, Any
import uuid

# Import our database components
try:
    from database import run_database_setup, Operation, Client, User, OperationStatus, ClientType, UserRole
    from crud import db_ops
    from config import calculate_commission, validate_operation_data
    from utils import validate_usdt_address, generate_operation_id, format_currency
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"Database modules not found: {e}")
    st.error("Please ensure database.py, crud.py, config.py, and utils.py are in the same directory")
    DATABASE_AVAILABLE = False

# Configure page
st.set_page_config(
    page_title="ALMA - Financial Exchange Control Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .status-pending { color: #ff7f0e; }
    .status-active { color: #2ca02c; }
    .status-completed { color: #17becf; }
    .status-error { color: #d62728; }
</style>
""", unsafe_allow_html=True)

# Authentication simulation (in real app, this would be proper auth)
def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'login_form_key' not in st.session_state:
        st.session_state.login_form_key = int(time.time())  # Use timestamp for unique key
    if 'page_reload_counter' not in st.session_state:
        st.session_state.page_reload_counter = 0

# Authentication functions with database
async def authenticate_user_async(username: str, password: str) -> Optional[User]:
    """Authenticate user against database"""
    return await db_ops.authenticate_user(username, password)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Synchronous wrapper for authentication"""
    if not DATABASE_AVAILABLE:
        # Fallback authentication for demo
        demo_users = {
            "admin": {"role": "admin", "full_name": "Administrator"},
            "fx_provider": {"role": "fx_provider", "full_name": "FX Provider"},
            "jessica": {"role": "collector", "full_name": "Jessica Garcia"}
        }
        
        if username in demo_users and password in ["admin123", "fx123", "jessica123"]:
            return {
                "id": str(uuid.uuid4()),
                "username": username,
                "role": demo_users[username]["role"],
                "full_name": demo_users[username]["full_name"]
            }
        return None
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user = loop.run_until_complete(authenticate_user_async(username, password))
        loop.close()
        
        if user:
            return {
                "id": str(user.id),
                "username": user.username,
                "role": user.role.value,
                "full_name": user.full_name or user.username
            }
        return None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

def login_page():
    st.markdown('<h1 class="main-header">🏦 ALMA Login</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Welcome to ALMA Financial Exchange Control Platform")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            # Display demo credentials
            with st.expander("🔑 Demo Credentials"):
                st.write("**Administrator:**")
                st.code("Username: admin\nPassword: admin123")
                st.write("**FX Provider:**")
                st.code("Username: fx_provider\nPassword: fx123")
            
            if st.form_submit_button("Login", use_container_width=True):
                if username and password:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user_role = user_data["role"]
                        st.session_state.user_name = user_data["full_name"]
                        st.session_state.user_id = user_data["id"]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter username and password")
            
            if st.form_submit_button("Login", use_container_width=True):
                # Simple auth simulation
                if username and password:
                    st.session_state.authenticated = True
                    st.session_state.user_role = user_data["role"]
                    st.session_state.user_name = username
                    st.rerun()
                else:
                    st.error("Please enter username and password")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.rerun()

# Database data loading functions
async def load_operations_async() -> List[Operation]:
    """Load operations from database"""
    return await db_ops.get_all_operations()

async def load_analytics_async() -> Dict[str, Any]:
    """Load analytics from database"""
    return await db_ops.get_operations_analytics()

def load_operations_data() -> pd.DataFrame:
    """Load operations data and convert to DataFrame"""
    if not DATABASE_AVAILABLE:
        # Return sample data for demo
        return get_sample_operations_data()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        operations = loop.run_until_complete(load_operations_async())
        loop.close()
        
        if not operations:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for op in operations:
            data.append({
                'id': str(op.id),
                'operation_id': op.operation_id,
                'client_name': op.client.name if op.client else 'Unknown',
                'amount_usd': float(op.amount_usd),
                'status': op.status.value,
                'collector': op.collector.full_name if op.collector else 'Unassigned',
                'fx_provider': op.fx_provider or 'Unassigned',
                'created_at': op.created_at,
                'estimated_usdt': float(op.estimated_usdt),
                'commission_amount': float(op.commission_amount),
                'pickup_address': op.pickup_address,
                'usdt_wallet': op.usdt_wallet,
                'priority': op.priority,
                'notes': op.notes or ''
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading operations: {e}")
        return get_sample_operations_data()

def get_sample_operations_data() -> pd.DataFrame:
    """Generate sample operations data for demo mode"""
    import random
    
    clients = ["John Smith", "Maria Garcia", "David Chen", "Sarah Johnson", "Michael Brown", "Lisa Wang"]
    collectors = ["Jessica", "Carlos", "Miguel", "Ana"]
    fx_providers = ["AlphaExchange", "BetaFX", "GammaFX", "DeltaFX"]
    statuses = ["Pending", "Assigned", "Collecting", "Collected", "Validated", "FX Processing", "Completed"]
    
    operations = []
    
    for i in range(15):
        operation_id = f"MSB-2025-08-{17-i//5}-{str(random.randint(100,999))}"
        amount = random.randint(1000, 35000)
        
        operations.append({
            "id": str(uuid.uuid4()),
            'operation_id': operation_id,
            'client_name': random.choice(clients),
            'amount_usd': amount,
            'status': random.choice(statuses),
            'collector': random.choice(collectors),
            'fx_provider': random.choice(fx_providers),
            'created_at': datetime.now() - timedelta(hours=random.randint(1, 168)),
            'estimated_usdt': amount * 0.95,
            'commission_amount': amount * 0.05,
            'pickup_address': f"{random.randint(100, 999)} Main St, City",
            'usdt_wallet': f"T{random.randint(100000000000000000000000000000000, 999999999999999999999999999999999)}",
            'priority': random.choice(["Normal", "High", "Urgent"]),
            'notes': f"Sample operation {i+1}"
        })
    
    return pd.DataFrame(operations)

def load_analytics_data() -> Dict[str, Any]:
    """Load analytics data"""
    if not DATABASE_AVAILABLE:
        # Return sample analytics for demo
        return {
            "total_operations": 15,
            "total_volume": 285000,
            "completed_operations": 8,
            "active_operations": 7,
            "total_commission": 14250,
            "completion_rate": 53.3,
            "average_operation_size": 19000
        }
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analytics = loop.run_until_complete(load_analytics_async())
        loop.close()
        return analytics
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        return {
            "total_operations": 0,
            "total_volume": 0,
            "completed_operations": 0,
            "active_operations": 0,
            "total_commission": 0,
            "completion_rate": 0,
            "average_operation_size": 0
        }

# Sample data for demonstration (now using real data as fallback)
@st.cache_data
def load_sample_data():
    """Load data from database or fallback to sample data"""
    operations_df = load_operations_data()
    analytics_data = load_analytics_data()
    
    return operations_df, analytics_data

def admin_dashboard():
    st.markdown('<h1 class="main-header">📊 Administrator Dashboard</h1>', unsafe_allow_html=True)
    
    operations_df, analytics_data = load_sample_data()
    
    # Top metrics row with real data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Active Operations", 
            value=analytics_data.get('active_operations', 0),
            delta="+3 from yesterday"
        )
    
    with col2:
        st.metric(
            label="Total Volume", 
            value=f"${analytics_data.get('total_volume', 0):,.0f}",
            delta=f"+{analytics_data.get('total_volume', 0)*0.15:.0f}"
        )
    
    with col3:
        st.metric(
            label="Completed Operations", 
            value=analytics_data.get('completed_operations', 0),
            delta="+2"
        )
    
    with col4:
        st.metric(
            label="Total Commission", 
            value=f"${analytics_data.get('total_commission', 0):,.0f}",
            delta=f"+{analytics_data.get('total_commission', 0)*0.12:.0f}"
        )
    
    # Add refresh button
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col4:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Operations overview
    if operations_df.empty:
        st.info("No operations found. Create your first operation using the 'New Operation' tab!")
        return
    
    st.markdown("### 📋 Recent Operations")
    
    # Status filter
    status_filter = st.multiselect(
        "Filter by Status",
        options=operations_df['status'].unique() if not operations_df.empty else [],
        default=operations_df['status'].unique() if not operations_df.empty else []
    )
    
    if status_filter:
        filtered_ops = operations_df[operations_df['status'].isin(status_filter)]
    else:
        filtered_ops = operations_df
    
    # Display operations with action buttons
    for idx, op in filtered_ops.head(10).iterrows():  # Show latest 10
        with st.expander(f"🔹 {op['operation_id']} - {op['client_name']} - ${op['amount_usd']:,.0f} - {op['status']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Status:** {op['status']}")
                st.write(f"**Collector:** {op['collector']}")
                st.write(f"**FX Provider:** {op['fx_provider']}")
            
            with col2:
                st.write(f"**Amount USD:** ${op['amount_usd']:,.0f}")
                st.write(f"**Estimated USDT:** {op['estimated_usdt']:,.2f}")
                st.write(f"**Commission:** ${op['commission_amount']:,.2f}")
            
            with col3:
                st.write(f"**Created:** {op['created_at'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Priority:** {op['priority']}")
                
                # Action buttons
                button_col1, button_col2 = st.columns(2)
                with button_col1:
                    if st.button(f"📋 Manage", key=f"manage_{op['operation_id']}"):
                        st.session_state.selected_operation = op['operation_id']
                        st.info(f"Managing operation {op['operation_id']}")
                
                with button_col2:
                    if op['status'] in ['Pending', 'Assigned'] and st.button(f"❌ Cancel", key=f"cancel_{op['operation_id']}"):
                        if delete_operation(op['id']):
                            st.success("Operation cancelled successfully!")
                            st.rerun()
    
    # Charts section
    if not operations_df.empty:
        st.markdown("### 📊 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Operations by status
            status_counts = operations_df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values, 
                names=status_counts.index,
                title="Operations by Status"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Revenue trend using real data
            if len(operations_df) > 0:
                daily_volume = operations_df.groupby(operations_df['created_at'].dt.date)['amount_usd'].sum().reset_index()
                daily_volume.columns = ['date', 'volume']
                
                fig_volume = px.line(
                    daily_volume,
                    x='date',
                    y='volume',
                    title="Daily Volume Trend",
                    markers=True
                )
                st.plotly_chart(fig_volume, use_container_width=True)

# Database operation functions
async def get_clients_async() -> List[Client]:
    """Get all clients from database"""
    return await db_ops.get_all_clients()

async def get_collectors_async() -> List[User]:
    """Get all collectors from database"""
    return await db_ops.get_users_by_role(UserRole.COLLECTOR)

async def create_operation_async(operation_data: Dict[str, Any]) -> Operation:
    """Create operation in database"""
    return await db_ops.create_operation(operation_data)

async def delete_operation_async(operation_id: str, user_id: str) -> bool:
    """Delete operation from database"""
    return await db_ops.delete_operation(operation_id, user_id)

def get_clients() -> List[Dict[str, Any]]:
    """Get clients synchronously"""
    if not DATABASE_AVAILABLE:
        # Return sample clients for demo
        return [
            {"id": str(uuid.uuid4()), "name": "John Smith", "type": "frequent"},
            {"id": str(uuid.uuid4()), "name": "Maria Garcia", "type": "regular"},
            {"id": str(uuid.uuid4()), "name": "David Chen", "type": "frequent"},
            {"id": str(uuid.uuid4()), "name": "Sarah Johnson", "type": "regular"}
        ]
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        clients = loop.run_until_complete(get_clients_async())
        loop.close()
        
        return [{"id": str(client.id), "name": client.name, "type": client.client_type.value} 
                for client in clients]
    except Exception as e:
        st.error(f"Error loading clients: {e}")
        return []

def get_collectors() -> List[Dict[str, Any]]:
    """Get collectors synchronously"""
    if not DATABASE_AVAILABLE:
        # Return sample collectors for demo
        return [
            {"id": str(uuid.uuid4()), "name": "Jessica Garcia"},
            {"id": str(uuid.uuid4()), "name": "Carlos Rodriguez"},
            {"id": str(uuid.uuid4()), "name": "Miguel Santos"},
            {"id": str(uuid.uuid4()), "name": "Ana Lopez"}
        ]
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        collectors = loop.run_until_complete(get_collectors_async())
        loop.close()
        
        return [{"id": str(collector.id), "name": collector.full_name or collector.username} 
                for collector in collectors]
    except Exception as e:
        st.error(f"Error loading collectors: {e}")
        return []

def create_operation(operation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create operation synchronously"""
    if not DATABASE_AVAILABLE:
        # Simulate operation creation for demo
        operation_id = f"MSB-{datetime.now().strftime('%Y-%m-%d')}-{str(int(datetime.now().timestamp()))[-3:]}"
        st.success(f"✅ Demo: Operation {operation_id} would be created in database")
        
        # Clear cache to refresh data
        st.cache_data.clear()
        
        return {
            "operation_id": operation_id,
            "id": str(uuid.uuid4()),
            "commission_amount": operation_data['amount_usd'] * 0.05,
            "estimated_usdt": operation_data['amount_usd'] * 0.95
        }
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        operation = loop.run_until_complete(create_operation_async(operation_data))
        loop.close()
        
        # Clear cache to refresh data
        st.cache_data.clear()
        
        return operation
    except Exception as e:
        st.error(f"Error creating operation: {e}")
        return None

def delete_operation(operation_id: str) -> bool:
    """Delete operation synchronously"""
    if not DATABASE_AVAILABLE:
        # Simulate deletion for demo
        st.success("✅ Demo: Operation would be cancelled in database")
        st.cache_data.clear()
        return True
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(delete_operation_async(operation_id, st.session_state.get('user_id')))
        loop.close()
        
        # Clear cache to refresh data
        st.cache_data.clear()
        
        return result
    except Exception as e:
        st.error(f"Error deleting operation: {e}")
        return False
    st.markdown('<h1 class="main-header">🔄 FX Provider Dashboard</h1>', unsafe_allow_html=True)
    
    operations_df, _ = load_sample_data()
    
    # Filter operations for current FX provider (simulation)
    provider_ops = operations_df[operations_df['fx_provider'] == 'AlphaExchange']
    
    st.markdown("### 📋 Your Assigned Operations")
    
    if len(provider_ops) == 0:
        st.info("No operations currently assigned to you.")
        return
    
    for idx, op in provider_ops.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**Operation:** {op['operation_id']}")
                st.markdown(f"**Client:** {op['client_name']}")
                st.markdown(f"**Amount:** ${op['amount_usd']:,}")
            
            with col2:
                st.markdown(f"**Status:** {op['status']}")
                st.markdown(f"**Created:** {op['created_at'].strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**Expected USDT:** {op['estimated_usdt']:,}")
            
            with col3:
                if op['status'] == 'FX Processing':
                    if st.button("Confirm Transfer", key=f"confirm_{op['operation_id']}"):
                        st.success(f"Transfer confirmed for {op['operation_id']}")
                elif op['status'] == 'Completed':
                    st.success("✅ Completed")
                else:
                    st.info("Pending")
            
            st.divider()

def new_operation_form():
    st.markdown('<h1 class="main-header">➕ Create New Operation</h1>', unsafe_allow_html=True)
    
    with st.form("new_operation"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Client Information")
            client_name = st.text_input("Client Name*")
            client_phone = st.text_input("Phone Number")
            client_address = st.text_area("Pickup Address*")
            
        with col2:
            st.markdown("### Operation Details")
            amount_usd = st.number_input("Amount (USD)*", min_value=100, max_value=100000, step=100)
            usdt_wallet = st.text_input("USDT Wallet Address*")
            deadline = st.date_input("Deadline", value=datetime.now().date() + timedelta(days=1))
        
        st.markdown("### Resource Assignment")
        col3, col4 = st.columns(2)
        
        with col3:
            collector = st.selectbox("Assign Collector", ["Jessica", "Carlos", "Miguel", "Ana"])
        
        with col4:
            fx_provider = st.selectbox("Assign FX Provider", ["AlphaExchange", "BetaFX", "GammaFX"])
        
        notes = st.text_area("Additional Notes")
        
        if st.form_submit_button("Create Operation", use_container_width=True):
            if client_name and client_address and amount_usd and usdt_wallet:
                # Generate operation ID
                operation_id = f"MSB-{datetime.now().strftime('%Y-%m-%d')}-{str(int(time.time()))[-3:]}"
                
                st.success(f"✅ Operation {operation_id} created successfully!")
                st.info(f"""
                **Operation Summary:**
                - ID: {operation_id}
                - Client: {client_name}
                - Amount: ${amount_usd:,}
                - Collector: {collector}
                - FX Provider: {fx_provider}
                """)
            else:
                st.error("Please fill in all required fields marked with *")

def main_app():
    # Sidebar user info
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.user_name}")
        st.markdown(f"**Role:** {st.session_state.user_role}")
        
        st.divider()
        
        # Real-time status
        st.markdown("### 🔴 System Status")
        st.success("✅ All systems operational")
        st.info("🔄 Last update: " + datetime.now().strftime("%H:%M:%S"))
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Navigation based on role
    if st.session_state.user_role == "Administrator":
        # Horizontal navigation menu for administrators
        st.markdown("### 🧭 Navigation")
        
        # Create navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "➕ New Operation", 
            "📋 Operations List", 
            "📈 Analytics", 
            "⚙️ Settings"
        ])
        
        with tab1:
            admin_dashboard()
        
        with tab2:
            new_operation_form()
        
        with tab3:
            operations_list_page()
        
        with tab4:
            analytics_page()
        
        with tab5:
            settings_page()
    
    else:  # FX Provider
        # Horizontal navigation for FX providers
        st.markdown("### 🧭 Navigation")
        
        tab1, tab2 = st.tabs([
            "🔄 My Operations", 
            "📊 Transaction History"
        ])
        
        with tab1:
            fx_provider_dashboard()
        
        with tab2:
            transaction_history_page()

def fx_provider_dashboard():
    st.markdown('<h1 class="main-header">🔄 FX Provider Dashboard</h1>', unsafe_allow_html=True)
    
    operations_df, _ = load_sample_data()
    
    if operations_df.empty:
        st.info("No operations currently assigned to you.")
        return
    
    # Filter operations for current FX provider (simulation - in real app, filter by user)
    provider_ops = operations_df[operations_df['fx_provider'] == 'AlphaExchange']
    
    st.markdown("### 📋 Your Assigned Operations")
    
    if len(provider_ops) == 0:
        st.info("No operations currently assigned to your FX provider account.")
        return
    
    for idx, op in provider_ops.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(f"**Operation:** {op['operation_id']}")
                st.markdown(f"**Client:** {op['client_name']}")
                st.markdown(f"**Amount:** ${op['amount_usd']:,.0f}")
            
            with col2:
                st.markdown(f"**Status:** {op['status']}")
                st.markdown(f"**Created:** {op['created_at'].strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**Expected USDT:** {op['estimated_usdt']:,.2f}")
            
            with col3:
                if op['status'] == 'FX Processing':
                    if st.button("Confirm Transfer", key=f"confirm_{op['operation_id']}"):
                        st.success(f"Transfer confirmed for {op['operation_id']}")
                elif op['status'] == 'Completed':
                    st.success("✅ Completed")
                else:
                    st.info("Pending")
            
            st.divider()

def operations_list_page():
    """Comprehensive operations list with advanced filtering"""
    st.markdown("### 📋 Operations List")
    
    operations_df, _ = load_sample_data()
    
    if operations_df.empty:
        st.info("No operations found.")
        return
    
    # Advanced filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect(
            "Status Filter",
            options=operations_df['status'].unique(),
            default=operations_df['status'].unique()
        )
    
    with col2:
        collector_filter = st.multiselect(
            "Collector Filter",
            options=operations_df['collector'].unique(),
            default=operations_df['collector'].unique()
        )
    
    with col3:
        amount_range = st.slider(
            "Amount Range (USD)",
            min_value=int(operations_df['amount_usd'].min()),
            max_value=int(operations_df['amount_usd'].max()),
            value=(int(operations_df['amount_usd'].min()), int(operations_df['amount_usd'].max()))
        )
    
    with col4:
        days_back = st.selectbox("Time Period", [7, 30, 90, 365], index=1)
        cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Apply filters
    filtered_df = operations_df[
        (operations_df['status'].isin(status_filter)) &
        (operations_df['collector'].isin(collector_filter)) &
        (operations_df['amount_usd'] >= amount_range[0]) &
        (operations_df['amount_usd'] <= amount_range[1]) &
        (operations_df['created_at'] >= cutoff_date)
    ]
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Filtered Operations", len(filtered_df))
    with col2:
        st.metric("Total Volume", f"${filtered_df['amount_usd'].sum():,.0f}")
    with col3:
        pending_ops = len(filtered_df[filtered_df['status'].isin(['Pending', 'Collecting'])])
        st.metric("Pending Actions", pending_ops)
    with col4:
        completed_ops = len(filtered_df[filtered_df['status'] == 'Completed'])
        completion_rate = (completed_ops / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    st.divider()
    
    # Export button
    if st.button("📥 Export to CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"operations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # Operations table
    st.dataframe(
        filtered_df[['operation_id', 'client_name', 'amount_usd', 'status', 'collector', 'fx_provider', 'created_at']],
        use_container_width=True
    )

def analytics_page():
    """Advanced analytics and reporting"""
    st.markdown("### 📈 Advanced Analytics")
    
    operations_df, financial_data = load_sample_data()
    
    # Time period selector
    period = st.selectbox("Analysis Period", ["Last 7 days", "Last 30 days", "Last 90 days"])
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Operations", len(operations_df))
        st.metric("Success Rate", "94.2%", delta="2.1%")
    
    with col2:
        total_volume = operations_df['amount_usd'].sum()
        st.metric("Total Volume", f"${total_volume:,.0f}")
        st.metric("Avg Operation Size", f"${operations_df['amount_usd'].mean():,.0f}")
    
    with col3:
        st.metric("Total Commission", f"${total_volume * 0.05:,.0f}")
        st.metric("Profit Margin", "23.4%", delta="1.8%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Performance by collector
        collector_performance = operations_df.groupby('collector').agg({
            'operation_id': 'count',
            'amount_usd': 'sum'
        }).reset_index()
        
        fig_collector = px.bar(
            collector_performance,
            x='collector',
            y='operation_id',
            title="Operations by Collector"
        )
        st.plotly_chart(fig_collector, use_container_width=True)
    
    with col2:
        # FX Provider distribution
        fx_distribution = operations_df['fx_provider'].value_counts()
        fig_fx = px.pie(
            values=fx_distribution.values,
            names=fx_distribution.index,
            title="FX Provider Distribution"
        )
        st.plotly_chart(fig_fx, use_container_width=True)

def settings_page():
    """System settings and configuration"""
    st.markdown("### ⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["💰 Business Rules", "👥 User Management", "🔧 System Config"])
    
    with tab1:
        st.markdown("#### Commission Rates")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Regular Clients**")
            regular_low = st.slider("Low Amount (<$5K)", 0.0, 0.15, 0.07, format="%.2f")
            regular_med = st.slider("Medium Amount ($5K-$20K)", 0.0, 0.15, 0.06, format="%.2f")
            regular_high = st.slider("High Amount (>$20K)", 0.0, 0.15, 0.05, format="%.2f")
        
        with col2:
            st.markdown("**Frequent Clients**")
            frequent_low = st.slider("Low Amount (<$5K)", 0.0, 0.15, 0.06, format="%.2f", key="freq_low")
            frequent_med = st.slider("Medium Amount ($5K-$20K)", 0.0, 0.15, 0.05, format="%.2f", key="freq_med")
            frequent_high = st.slider("High Amount (>$20K)", 0.0, 0.15, 0.04, format="%.2f", key="freq_high")
        
        if st.button("💾 Save Commission Settings"):
            st.success("Commission settings updated successfully!")
    
    with tab2:
        st.markdown("#### User Management")
        
        # Add new user form
        with st.expander("➕ Add New User"):
            new_username = st.text_input("Username")
            new_role = st.selectbox("Role", ["Administrator", "FX Provider", "Collector"])
            if st.button("Add User"):
                st.success(f"User {new_username} added with role {new_role}")
        
        # Current users table
        users_data = {
            'Username': ['admin', 'fx_provider', 'jessica_collector'],
            'Role': ['Administrator', 'FX Provider', 'Collector'],
            'Status': ['Active', 'Active', 'Active'],
            'Last Login': ['2025-08-17 14:30', '2025-08-17 13:45', '2025-08-17 12:15']
        }
        st.dataframe(pd.DataFrame(users_data), use_container_width=True)
    
    with tab3:
        st.markdown("#### System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Operation Limits**")
            max_amount = st.number_input("Max Operation Amount", value=50000)
            min_amount = st.number_input("Min Operation Amount", value=100)
            
        with col2:
            st.markdown("**Notifications**")
            email_notifications = st.checkbox("Email Notifications", value=True)
            sms_notifications = st.checkbox("SMS Notifications", value=True)
        
        if st.button("💾 Save System Settings"):
            st.success("System settings updated successfully!")

def transaction_history_page():
    """Transaction history for FX providers"""
    st.markdown("### 📊 Transaction History")
    
    operations_df, _ = load_sample_data()
    
    # Filter for completed operations
    completed_ops = operations_df[operations_df['status'] == 'Completed']
    
    if len(completed_ops) == 0:
        st.info("No completed transactions found.")
        return
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Transactions", len(completed_ops))
    
    with col2:
        total_volume = completed_ops['amount_usd'].sum()
        st.metric("Total Volume", f"${total_volume:,.0f}")
    
    with col3:
        avg_amount = completed_ops['amount_usd'].mean()
        st.metric("Average Amount", f"${avg_amount:,.0f}")
    
    # Transaction history table
    st.markdown("#### Recent Transactions")
    st.dataframe(
        completed_ops[['operation_id', 'client_name', 'amount_usd', 'created_at']],
        use_container_width=True
    )
    # Sidebar user info
    with st.sidebar:
        st.markdown(f"### Welcome, {st.session_state.user_name}")
        st.markdown(f"**Role:** {st.session_state.user_role}")
        
        st.divider()
        
        # Real-time status
        st.markdown("### 🔴 System Status")
        st.success("✅ All systems operational")
        st.info("🔄 Last update: " + datetime.now().strftime("%H:%M:%S"))
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Navigation based on role
    if st.session_state.user_role == "Administrator":
        # Horizontal navigation menu for administrators
        st.markdown("### 🧭 Navigation")
        
        # Create navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "➕ New Operation", 
            "📋 Operations List", 
            "📈 Analytics", 
            "⚙️ Settings"
        ])
        
        with tab1:
            admin_dashboard()
        
        with tab2:
            new_operation_form()
        
        with tab3:
            operations_list_page()
        
        with tab4:
            analytics_page()
        
        with tab5:
            settings_page()
    
    else:  # FX Provider
        # Horizontal navigation for FX providers
        st.markdown("### 🧭 Navigation")
        
        tab1, tab2 = st.tabs([
            "🔄 My Operations", 
            "📊 Transaction History"
        ])
        
        with tab1:
            fx_provider_dashboard()
        
        with tab2:
            transaction_history_page()

# Main application logic
def main():
    # Initialize session state first
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()