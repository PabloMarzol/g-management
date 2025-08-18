import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
import time
from typing import Optional, List, Dict, Any

# Try to import database, fall back to sample data
try:
    from alma.database import UserRole, ClientType, OperationStatus
    from alma.crud import db_ops
   
    print("✅ Database available")
except ImportError:
   
    print("⚠️ Using sample data only")


DATABASE_AVAILABLE = False
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
    .status-pending { color: #ff7f0e; font-weight: bold; }
    .status-active { color: #2ca02c; font-weight: bold; }
    .status-completed { color: #17becf; font-weight: bold; }
    .status-error { color: #d62728; font-weight: bold; }
    .operation-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fafafa;
    }
    .priority-high { border-left: 4px solid #ff4444; }
    .priority-urgent { border-left: 4px solid #ff0000; }
    .priority-normal { border-left: 4px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state"""
    defaults = {
        'authenticated': False,
        'user_role': None,
        'user_name': None,
        'user_id': None,
        'selected_operation': None,
        'operations_cache': None,
        'cache_time': None,
        'show_advanced_filters': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def authenticate_user(username: str, password: str):
    """Enhanced authentication with better error handling"""
    # Demo users
    demo_users = {
        "admin": {"role": "admin", "name": "Administrator", "id": str(uuid.uuid4())},
        "fx_provider": {"role": "fx_provider", "name": "FX Provider", "id": str(uuid.uuid4())},
        "jessica": {"role": "collector", "name": "Jessica Garcia", "id": str(uuid.uuid4())},
        "carlos": {"role": "collector", "name": "Carlos Rodriguez", "id": str(uuid.uuid4())}
    }
    
    if username in demo_users and password in ["admin123", "fx123", "jessica123", "carlos123"]:
        return demo_users[username]
    
    # Try database if available
    if DATABASE_AVAILABLE:
        try:
            user = db_ops.authenticate_user(username, password)
            if user:
                return {
                    "role": user.role.value, 
                    "name": user.full_name or user.username,
                    "id": str(user.id)
                }
        except Exception as e:
            st.error(f"Database authentication error: {e}")
    
    return None

def get_sample_data():
    """Enhanced sample operations data"""
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
            'usdt_wallet': f"T{random.randint(100000000000000000000000000000000, 999999999999999999999999999999999)}",
            'priority': random.choice(priorities),
            'notes': f"Sample operation notes {i+1}",
            'deadline': (datetime.now() + timedelta(days=random.randint(1, 7))).date()
        })
    
    return pd.DataFrame(operations)

def load_data_with_cache():
    """Load data with intelligent caching"""
    # Check cache validity (5 minutes)
    if (st.session_state.operations_cache is not None and 
        st.session_state.cache_time is not None and 
        datetime.now() - st.session_state.cache_time < timedelta(minutes=5)):
        return st.session_state.operations_cache
    
    # Load fresh data
    operations_df, analytics = load_data()
    
    # Update cache
    st.session_state.operations_cache = (operations_df, analytics)
    st.session_state.cache_time = datetime.now()
    
    return operations_df, analytics

def clear_cache():
    """Clear data cache"""
    st.session_state.operations_cache = None
    st.session_state.cache_time = None

def load_data():
    """Load data from database or use sample"""
    if not DATABASE_AVAILABLE:
        operations_df = get_sample_data()
        analytics = calculate_analytics_from_df(operations_df)
        return operations_df, analytics
    
    try:
        # Get operations
        operations = db_ops.get_all_operations()
        ops_data = []
        
        for op in operations:
            ops_data.append({
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
                'notes': op.notes or '',
                'deadline': op.deadline.date() if op.deadline else None
            })
        
        operations_df = pd.DataFrame(ops_data) if ops_data else get_sample_data()
        analytics = db_ops.get_operations_analytics()
        
        return operations_df, analytics
        
    except Exception as e:
        st.error(f"Database error: {e}")
        operations_df = get_sample_data()
        analytics = calculate_analytics_from_df(operations_df)
        return operations_df, analytics

def calculate_analytics_from_df(df):
    """Calculate analytics from DataFrame"""
    total_ops = len(df)
    total_volume = df['amount_usd'].sum()
    completed_ops = len(df[df['status'] == 'Completed'])
    active_ops = len(df[df['status'].isin(['Pending', 'Assigned', 'Collecting', 'Collected', 'Validated', 'FX Processing'])])
    total_commission = df['commission_amount'].sum()
    completion_rate = (completed_ops / total_ops * 100) if total_ops > 0 else 0
    
    return {
        "total_operations": total_ops,
        "total_volume": total_volume,
        "completed_operations": completed_ops,
        "active_operations": active_ops,
        "total_commission": total_commission,
        "completion_rate": completion_rate,
        "average_operation_size": total_volume / total_ops if total_ops > 0 else 0
    }

def format_currency(amount):
    """Format currency with proper separators"""
    return f"${amount:,.2f}"

def get_status_color(status):
    """Get color for status"""
    colors = {
        "Pending": "#ff7f0e",
        "Assigned": "#2ca02c",
        "Collecting": "#1f77b4",
        "Collected": "#17becf",
        "Validated": "#9467bd",
        "FX Processing": "#e377c2",
        "Completed": "#2ca02c",
        "Cancelled": "#d62728",
        "Error": "#d62728"
    }
    return colors.get(status, "#7f7f7f")

def create_status_badge(status):
    """Create HTML badge for status"""
    color = get_status_color(status)
    return f"""
    <span style="
        background-color: {color}; 
        color: white; 
        padding: 0.2rem 0.5rem; 
        border-radius: 0.3rem; 
        font-size: 0.8rem;
        font-weight: bold;
    ">{status}</span>
    """

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
                    st.write("**Collector:**")
                    st.code("Username: jessica\nPassword: jessica123")
                with col_b:
                    st.write("**FX Provider:**")
                    st.code("Username: fx_provider\nPassword: fx123")
                    st.write("**Collector 2:**")
                    st.code("Username: carlos\nPassword: carlos123")
            
            if st.form_submit_button("🚀 Login", use_container_width=True):
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_role = user["role"]
                        st.session_state.user_name = user["name"]
                        st.session_state.user_id = user["id"]
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.error("⚠️ Please enter username and password")

def admin_dashboard():
    st.markdown('<h1 class="main-header">📊 Administrator Dashboard</h1>', unsafe_allow_html=True)
    
    operations_df, analytics = load_data_with_cache()
    
    # Enhanced metrics with better formatting
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Active Operations", 
            analytics["active_operations"],
            delta="+3 from yesterday",
            help="Operations currently in progress"
        )
    with col2:
        st.metric(
            "Total Volume", 
            format_currency(analytics["total_volume"]),
            delta=f"+{analytics['total_volume']*0.15:,.0f}",
            help="Total USD volume processed"
        )
    with col3:
        st.metric(
            "Completed", 
            analytics["completed_operations"],
            delta="+2 today",
            help="Successfully completed operations"
        )
    with col4:
        st.metric(
            "Commission", 
            format_currency(analytics["total_commission"]),
            delta=f"+{analytics['total_commission']*0.12:,.0f}",
            help="Total commission earned"
        )
    
    # Refresh button
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col4:
        if st.button("🔄 Refresh Data", help="Refresh all data from database"):
            clear_cache()
            st.rerun()
    
    # Quick filters
    st.markdown("### 🔍 Quick Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status Filter",
            ["All"] + list(operations_df['status'].unique()),
            help="Filter operations by status"
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Priority Filter", 
            ["All"] + list(operations_df['priority'].unique()),
            help="Filter operations by priority"
        )
    
    with col3:
        collector_filter = st.selectbox(
            "Collector Filter",
            ["All"] + list(operations_df['collector'].unique()),
            help="Filter operations by collector"
        )
    
    # Apply filters
    filtered_df = operations_df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    if priority_filter != "All":
        filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
    if collector_filter != "All":
        filtered_df = filtered_df[filtered_df['collector'] == collector_filter]
    
    # Recent operations with enhanced display
    st.markdown("### 📋 Recent Operations")
    st.info(f"Showing {len(filtered_df)} operations (filtered from {len(operations_df)} total)")
    
    for _, op in filtered_df.head(8).iterrows():
        priority_class = f"priority-{op['priority'].lower()}"
        
        with st.expander(
            f"🔹 {op['operation_id']} - {op['client_name']} - {format_currency(op['amount_usd'])} - {op['status']}",
            expanded=False
        ):
            # Enhanced operation display
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
                
                # Action buttons based on status
                if op['status'] == 'Pending':
                    if st.button("✅ Assign", key=f"assign_{op['operation_id']}"):
                        st.success("Operation assigned!")
                        clear_cache()
                        time.sleep(1)
                        st.rerun()
                
                elif op['status'] == 'Collecting':
                    if st.button("📸 Confirm Collection", key=f"collect_{op['operation_id']}"):
                        st.success("Collection confirmed!")
                        clear_cache()
                        time.sleep(1)
                        st.rerun()
                
                elif op['status'] == 'Collected':
                    if st.button("✅ Validate", key=f"validate_{op['operation_id']}"):
                        st.success("Cash validated!")
                        clear_cache()
                        time.sleep(1)
                        st.rerun()
                
                # Always show manage button
                if st.button("📋 Manage", key=f"manage_{op['operation_id']}"):
                    st.session_state.selected_operation = op['operation_id']
                    st.info(f"Managing operation {op['operation_id']}")
                
                # Cancel button for pending operations
                if op['status'] in ['Pending', 'Assigned']:
                    if st.button("❌ Cancel", key=f"cancel_{op['operation_id']}"):
                        if delete_operation(op['id']):
                            st.success("Operation cancelled!")
                            clear_cache()
                            time.sleep(1)
                            st.rerun()
            
            # Additional details in expandable sections
            with st.expander("🔍 Additional Details", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Pickup Address:** {op['pickup_address']}")
                    st.write(f"**USDT Wallet:** {op['usdt_wallet'][:20]}...")
                with col_b:
                    st.write(f"**Deadline:** {op.get('deadline', 'Not set')}")
                    st.write(f"**Notes:** {op['notes'] or 'No notes'}")
    
    # Enhanced analytics charts
    if not operations_df.empty:
        st.markdown("### 📊 Analytics Dashboard")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Enhanced status chart
            status_counts = operations_df['status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values, 
                names=status_counts.index,
                title="Operations by Status",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_status.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Enhanced volume trend
            if len(operations_df) > 0:
                daily_volume = operations_df.groupby(operations_df['created_at'].dt.date)['amount_usd'].sum().reset_index()
                daily_volume.columns = ['date', 'volume']
                
                fig_volume = px.line(
                    daily_volume,
                    x='date',
                    y='volume',
                    title="Daily Volume Trend",
                    markers=True,
                    line_shape='spline'
                )
                fig_volume.update_layout(
                    yaxis_title="Volume (USD)",
                    xaxis_title="Date"
                )
                st.plotly_chart(fig_volume, use_container_width=True)

def fx_provider_dashboard():
    st.markdown('<h1 class="main-header">🔄 FX Provider Dashboard</h1>', unsafe_allow_html=True)
    
    operations_df, analytics = load_data_with_cache()
    
    # Filter for this FX provider (simulate based on username)
    if st.session_state.user_name == "FX Provider":
        my_ops = operations_df[operations_df['fx_provider'] == 'AlphaExchange']
    else:
        my_ops = operations_df.head(5)  # Demo data
    
    # FX Provider metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("My Operations", len(my_ops))
    with col2:
        st.metric("My Volume", format_currency(my_ops['amount_usd'].sum()))
    with col3:
        completed = len(my_ops[my_ops['status'] == 'Completed'])
        st.metric("Completed", completed)
    
    st.markdown("### 📋 Your Assigned Operations")
    if len(my_ops) == 0:
        st.info("No operations currently assigned to you.")
    else:
        for _, op in my_ops.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{op['operation_id']}**")
                    st.write(f"Client: {op['client_name']}")
                    st.write(f"Priority: {op['priority']}")
                with col2:
                    st.write(f"Amount: {format_currency(op['amount_usd'])}")
                    st.write(f"Status: {op['status']}")
                    st.write(f"Created: {op['created_at'].strftime('%Y-%m-%d %H:%M')}")
                with col3:
                    if op['status'] == 'FX Processing':
                        if st.button("✅ Confirm Transfer", key=f"confirm_{op['operation_id']}"):
                            st.success("Transfer confirmed!")
                            clear_cache()
                            time.sleep(1)
                            st.rerun()
                    elif op['status'] == 'Completed':
                        st.success("✅ Completed")
                    else:
                        st.info("⏳ Pending")
                st.divider()

# Database operation functions
def delete_operation(operation_id: str) -> bool:
    """Delete operation"""
    if not DATABASE_AVAILABLE:
        st.success("✅ Demo: Operation would be cancelled in database")
        return True
    
    try:
        result = db_ops.delete_operation(operation_id, st.session_state.get('user_id'))
        return result
    except Exception as e:
        st.error(f"Error deleting operation: {e}")
        return False

def new_operation_form():
    st.markdown('<h1 class="main-header">➕ Create New Operation</h1>', unsafe_allow_html=True)
    
    with st.form("new_operation"):
        # Client Information Section
        st.markdown("#### 👤 Client Information")
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("Client Name*", placeholder="Enter full client name")
            client_phone = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
            client_type = st.selectbox("Client Type", ["regular", "frequent"])
        
        with col2:
            pickup_address = st.text_area("Pickup Address*", placeholder="Full address with landmarks")
            client_notes = st.text_area("Client Notes", placeholder="Any special instructions...")
        
        # Operation Details Section
        st.markdown("#### 💰 Operation Details")
        col3, col4 = st.columns(2)
        
        with col3:
            amount_usd = st.number_input(
                "Amount (USD)*", 
                min_value=100, 
                max_value=100000, 
                step=100,
                help="Amount between $100 and $100,000"
            )
            
            # Real-time commission calculation
            if amount_usd > 0:
                if client_type == "frequent":
                    if amount_usd < 5000:
                        commission_rate = 0.06
                    elif amount_usd <= 20000:
                        commission_rate = 0.05
                    else:
                        commission_rate = 0.04
                else:  # regular
                    if amount_usd < 5000:
                        commission_rate = 0.07
                    elif amount_usd <= 20000:
                        commission_rate = 0.06
                    else:
                        commission_rate = 0.05
                
                commission_amount = amount_usd * commission_rate
                net_amount = amount_usd - commission_amount
                
                st.info(f"Commission: {format_currency(commission_amount)} ({commission_rate*100:.1f}%)")
                st.info(f"Net to convert: {format_currency(net_amount)}")
        
        with col4:
            usdt_wallet = st.text_input("USDT Wallet Address*", placeholder="T... or 0x...")
            
            # Basic wallet validation
            if usdt_wallet:
                if not (usdt_wallet.startswith("T") and len(usdt_wallet) == 34) and not (usdt_wallet.startswith("0x") and len(usdt_wallet) == 42):
                    st.error("Invalid USDT wallet address format")
            
            deadline = st.date_input("Deadline", value=datetime.now().date() + timedelta(days=1))
            priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])
        
        # Resource Assignment Section
        st.markdown("#### 👥 Resource Assignment")
        col5, col6 = st.columns(2)
        
        with col5:
            collector = st.selectbox("Assign Collector", ["Auto-assign", "Jessica", "Carlos", "Miguel", "Ana"])
            collector_notes = st.text_area("Collector Instructions", placeholder="Special instructions for collector...")
        
        with col6:
            fx_provider = st.selectbox("FX Provider", ["Auto-select", "AlphaExchange", "BetaFX", "GammaFX"])
            fx_conditions = st.selectbox("FX Conditions", ["Upfront", "Cash-first"])
        
        # Additional Options
        st.markdown("#### ⚙️ Additional Options")
        col7, col8 = st.columns(2)
        with col7:
            auto_notifications = st.checkbox("Send automatic notifications", value=True)
            require_photos = st.checkbox("Require photo evidence", value=True)
        with col8:
            operation_notes = st.text_area("Operation Notes", placeholder="Additional notes for this operation...")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Operation", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            if not client_name:
                errors.append("Client name is required")
            if not pickup_address:
                errors.append("Pickup address is required")
            if not amount_usd or amount_usd < 100:
                errors.append("Amount must be at least $100")
            if not usdt_wallet:
                errors.append("USDT wallet address is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Create operation
                operation_id = f"MSB-{datetime.now().strftime('%Y-%m-%d')}-{str(int(time.time()))[-3:]}"
                
                st.success(f"✅ Operation {operation_id} created successfully!")
                
                # Show operation summary
                with st.expander("📋 Operation Summary", expanded=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Operation ID:** {operation_id}")
                        st.write(f"**Client:** {client_name}")
                        st.write(f"**Amount:** {format_currency(amount_usd)}")
                        st.write(f"**Commission:** {format_currency(commission_amount)}")
                        st.write(f"**Net Amount:** {format_currency(net_amount)}")
                    with col_b:
                        st.write(f"**Collector:** {collector}")
                        st.write(f"**FX Provider:** {fx_provider}")
                        st.write(f"**Priority:** {priority}")
                        st.write(f"**Deadline:** {deadline}")
                        st.write(f"**Estimated USDT:** {net_amount * 0.95:.2f}")
                
                clear_cache()

def operations_list():
    st.markdown('<h1 class="main-header">📋 Operations List</h1>', unsafe_allow_html=True)
    
    operations_df, _ = load_data_with_cache()
    
    # Enhanced filters
    st.markdown("### 🔍 Advanced Filters")
    
    # Toggle advanced filters
    if st.button("⚙️ Toggle Advanced Filters"):
        st.session_state.show_advanced_filters = not st.session_state.show_advanced_filters
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect("Status", operations_df['status'].unique())
    with col2:
        collector_filter = st.multiselect("Collector", operations_df['collector'].unique())
    with col3:
        priority_filter = st.multiselect("Priority", operations_df['priority'].unique())
    with col4:
        fx_filter = st.multiselect("FX Provider", operations_df['fx_provider'].unique())
    
    if st.session_state.show_advanced_filters:
        st.markdown("#### 📊 Advanced Filters")
        col5, col6, col7 = st.columns(3)
        
        with col5:
            amount_range = st.slider(
                "Amount Range (USD)",
                min_value=int(operations_df['amount_usd'].min()),
                max_value=int(operations_df['amount_usd'].max()),
                value=(int(operations_df['amount_usd'].min()), int(operations_df['amount_usd'].max()))
            )
        
        with col6:
            days_back = st.selectbox("Time Period", [7, 30, 90, 365], index=1)
            cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with col7:
            search_term = st.text_input("Search Operations", placeholder="Search by client name or operation ID...")
    
    # Apply filters
    filtered_df = operations_df.copy()
    
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    if collector_filter:
        filtered_df = filtered_df[filtered_df['collector'].isin(collector_filter)]
    if priority_filter:
        filtered_df = filtered_df[filtered_df['priority'].isin(priority_filter)]
    if fx_filter:
        filtered_df = filtered_df[filtered_df['fx_provider'].isin(fx_filter)]
    
    if st.session_state.show_advanced_filters:
        filtered_df = filtered_df[
            (filtered_df['amount_usd'] >= amount_range[0]) &
            (filtered_df['amount_usd'] <= amount_range[1]) &
            (filtered_df['created_at'] >= cutoff_date)
        ]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['client_name'].str.contains(search_term, case=False, na=False) |
                filtered_df['operation_id'].str.contains(search_term, case=False, na=False)
            ]
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Filtered Operations", len(filtered_df))
    with col2:
        st.metric("Total Volume", format_currency(filtered_df['amount_usd'].sum()))
    with col3:
        pending_ops = len(filtered_df[filtered_df['status'].isin(['Pending', 'Collecting'])])
        st.metric("Pending Actions", pending_ops)
    with col4:
        completed_ops = len(filtered_df[filtered_df['status'] == 'Completed'])
        completion_rate = (completed_ops / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    st.divider()
    
    # Export and bulk actions
    col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 2])
    
    with col_exp1:
        if st.button("📥 Export to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"operations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col_exp2:
        if st.button("📊 Generate Report"):
            st.info("Report generation feature coming soon!")
    
    # Enhanced operations table with better formatting
    if len(filtered_df) > 0:
        st.markdown("### 📋 Operations Table")
        
        # Prepare display data
        display_df = filtered_df.copy()
        display_df['amount_usd'] = display_df['amount_usd'].apply(lambda x: f"${x:,.0f}")
        display_df['estimated_usdt'] = display_df['estimated_usdt'].apply(lambda x: f"{x:,.2f}")
        display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Select columns for display
        display_columns = [
            'operation_id', 'client_name', 'amount_usd', 'status', 
            'priority', 'collector', 'fx_provider', 'created_at'
        ]
        
        st.dataframe(
            display_df[display_columns],
            use_container_width=True,
            column_config={
                "operation_id": "Operation ID",
                "client_name": "Client",
                "amount_usd": "Amount",
                "status": "Status",
                "priority": "Priority",
                "collector": "Collector",
                "fx_provider": "FX Provider",
                "created_at": "Created"
            }
        )
    else:
        st.info("No operations match the current filters.")

def analytics_page():
    st.markdown('<h1 class="main-header">📈 Advanced Analytics</h1>', unsafe_allow_html=True)
    
    operations_df, analytics = load_data_with_cache()
    
    # Time period selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        period = st.selectbox("Analysis Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
    with col2:
        refresh_analytics = st.button("🔄 Refresh Analytics")
        if refresh_analytics:
            clear_cache()
            st.rerun()
    
    # Enhanced key metrics
    st.markdown("### 📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Operations", analytics["total_operations"])
        completion_rate = analytics["completion_rate"]
        st.metric("Success Rate", f"{completion_rate:.1f}%", delta="2.1%")
    
    with col2:
        total_volume = analytics["total_volume"]
        st.metric("Total Volume", format_currency(total_volume))
        avg_size = analytics["average_operation_size"]
        st.metric("Avg Operation Size", format_currency(avg_size))
    
    with col3:
        st.metric("Total Commission", format_currency(analytics["total_commission"]))
        profit_margin = (analytics["total_commission"] / total_volume * 100) if total_volume > 0 else 0
        st.metric("Profit Margin", f"{profit_margin:.1f}%", delta="1.8%")
    
    with col4:
        st.metric("Active Operations", analytics["active_operations"])
        st.metric("Completed Today", analytics["completed_operations"])
    
    # Enhanced charts
    st.markdown("### 📈 Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Enhanced performance by collector
        collector_performance = operations_df.groupby('collector').agg({
            'operation_id': 'count',
            'amount_usd': 'sum',
            'commission_amount': 'sum'
        }).reset_index()
        collector_performance.columns = ['Collector', 'Operations', 'Volume', 'Commission']
        
        fig_collector = px.bar(
            collector_performance,
            x='Collector',
            y='Operations',
            title="Operations by Collector",
            color='Volume',
            color_continuous_scale='Blues'
        )
        fig_collector.update_layout(showlegend=False)
        st.plotly_chart(fig_collector, use_container_width=True)
    
    with col2:
        # Enhanced FX Provider distribution
        fx_distribution = operations_df['fx_provider'].value_counts()
        fig_fx = px.pie(
            values=fx_distribution.values,
            names=fx_distribution.index,
            title="FX Provider Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_fx.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_fx, use_container_width=True)
    
    # Additional analytics
    col3, col4 = st.columns(2)
    
    with col3:
        # Priority distribution
        priority_counts = operations_df['priority'].value_counts()
        fig_priority = px.bar(
            x=priority_counts.index,
            y=priority_counts.values,
            title="Operations by Priority",
            color=priority_counts.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    with col4:
        # Status progression over time
        if len(operations_df) > 0:
            status_timeline = operations_df.groupby([operations_df['created_at'].dt.date, 'status']).size().reset_index()
            status_timeline.columns = ['date', 'status', 'count']
            
            fig_timeline = px.line(
                status_timeline,
                x='date',
                y='count',
                color='status',
                title="Status Timeline",
                markers=True
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

def settings_page():
    st.markdown('<h1 class="main-header">⚙️ System Settings</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Business Rules", "👥 User Management", "🔧 System Config", "📊 Reports"])
    
    with tab1:
        st.markdown("### 💰 Commission Rate Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Regular Clients")
            regular_low = st.slider("Low Amount (<$5K)", 0.0, 0.15, 0.07, format="%.2f", help="Commission for amounts under $5,000")
            regular_med = st.slider("Medium Amount ($5K-$20K)", 0.0, 0.15, 0.06, format="%.2f", help="Commission for amounts $5,000-$20,000")
            regular_high = st.slider("High Amount (>$20K)", 0.0, 0.15, 0.05, format="%.2f", help="Commission for amounts over $20,000")
        
        with col2:
            st.markdown("#### Frequent Clients")
            frequent_low = st.slider("Low Amount (<$5K)", 0.0, 0.15, 0.06, format="%.2f", key="freq_low", help="Commission for frequent clients under $5,000")
            frequent_med = st.slider("Medium Amount ($5K-$20K)", 0.0, 0.15, 0.05, format="%.2f", key="freq_med", help="Commission for frequent clients $5,000-$20,000")
            frequent_high = st.slider("High Amount (>$20K)", 0.0, 0.15, 0.04, format="%.2f", key="freq_high", help="Commission for frequent clients over $20,000")
        
        st.markdown("#### Other Settings")
        fx_commission = st.slider("FX Provider Commission", 0.0, 0.05, 0.015, format="%.3f", help="Fixed commission for FX providers")
        
        col_save1, col_save2 = st.columns([1, 3])
        with col_save1:
            if st.button("💾 Save Commission Settings", use_container_width=True):
                st.success("✅ Commission settings updated successfully!")
                st.info("Note: Changes will apply to new operations only.")
    
    with tab2:
        st.markdown("### 👥 User Management")
        
        # Add new user form
        with st.expander("➕ Add New User", expanded=False):
            col_user1, col_user2 = st.columns(2)
            
            with col_user1:
                new_username = st.text_input("Username", placeholder="Enter username")
                new_fullname = st.text_input("Full Name", placeholder="Enter full name")
                new_email = st.text_input("Email", placeholder="user@company.com")
            
            with col_user2:
                new_role = st.selectbox("Role", ["admin", "fx_provider", "collector"])
                new_phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
                new_password = st.text_input("Password", type="password", placeholder="Enter password")
            
            if st.button("➕ Add User"):
                if new_username and new_fullname and new_password:
                    st.success(f"✅ User {new_username} added with role {new_role}")
                else:
                    st.error("❌ Please fill in all required fields")
        
        # Current users table
        st.markdown("#### Current Users")
        users_data = {
            'Username': ['admin', 'fx_provider', 'jessica', 'carlos'],
            'Full Name': ['Administrator', 'FX Provider', 'Jessica Garcia', 'Carlos Rodriguez'],
            'Role': ['Administrator', 'FX Provider', 'Collector', 'Collector'],
            'Status': ['Active', 'Active', 'Active', 'Active'],
            'Last Login': ['2025-08-18 14:30', '2025-08-18 13:45', '2025-08-18 12:15', '2025-08-18 11:30']
        }
        st.dataframe(pd.DataFrame(users_data), use_container_width=True)
    
    with tab3:
        st.markdown("### 🔧 System Configuration")
        
        col_sys1, col_sys2 = st.columns(2)
        
        with col_sys1:
            st.markdown("#### Operation Limits")
            max_amount = st.number_input("Max Operation Amount ($)", value=50000, min_value=1000, max_value=1000000)
            min_amount = st.number_input("Min Operation Amount ($)", value=100, min_value=10, max_value=10000)
            
            st.markdown("#### Timeouts and Alerts")
            collection_timeout = st.number_input("Collection Timeout (hours)", value=24, min_value=1, max_value=168)
            validation_timeout = st.number_input("Validation Timeout (hours)", value=24, min_value=1, max_value=168)
        
        with col_sys2:
            st.markdown("#### Notifications")
            email_notifications = st.checkbox("Email Notifications", value=True)
            sms_notifications = st.checkbox("SMS Notifications", value=True)
            telegram_notifications = st.checkbox("Telegram Notifications", value=True)
            
            st.markdown("#### Data Retention")
            operation_retention = st.selectbox("Operation Data Retention", ["1 year", "2 years", "5 years", "10 years"], index=2)
            evidence_retention = st.selectbox("Evidence Retention", ["2 years", "5 years", "10 years", "Permanent"], index=1)
        
        if st.button("💾 Save System Settings", use_container_width=True):
            st.success("✅ System settings updated successfully!")
    
    with tab4:
        st.markdown("### 📊 Report Configuration")
        
        col_rep1, col_rep2 = st.columns(2)
        
        with col_rep1:
            st.markdown("#### Automated Reports")
            daily_report = st.checkbox("Daily Operations Report", value=True)
            weekly_report = st.checkbox("Weekly Performance Report", value=True)
            monthly_report = st.checkbox("Monthly Financial Report", value=True)
            
            if daily_report:
                daily_time = st.time_input("Daily Report Time", value=datetime.strptime("08:00", "%H:%M").time())
            
            if weekly_report:
                weekly_day = st.selectbox("Weekly Report Day", ["Monday", "Friday", "Sunday"])
        
        with col_rep2:
            st.markdown("#### Report Recipients")
            admin_reports = st.checkbox("Send to Administrators", value=True)
            manager_reports = st.checkbox("Send to Managers", value=True)
            
            custom_email = st.text_input("Additional Email Recipients", placeholder="email1@company.com, email2@company.com")
        
        if st.button("💾 Save Report Settings", use_container_width=True):
            st.success("✅ Report settings updated successfully!")

def collector_dashboard():
    st.markdown('<h1 class="main-header">📱 Collector Dashboard</h1>', unsafe_allow_html=True)
    
    operations_df, _ = load_data_with_cache()
    
    # Filter for this collector
    collector_name = st.session_state.user_name
    my_ops = operations_df[operations_df['collector'].str.contains(collector_name.split()[0], case=False, na=False)]
    
    # Collector metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("My Operations", len(my_ops))
    with col2:
        pending = len(my_ops[my_ops['status'].isin(['Pending', 'Assigned'])])
        st.metric("Pending", pending)
    with col3:
        collecting = len(my_ops[my_ops['status'] == 'Collecting'])
        st.metric("Collecting", collecting)
    with col4:
        completed = len(my_ops[my_ops['status'] == 'Completed'])
        st.metric("Completed", completed)
    
    st.markdown("### 📋 My Assigned Operations")
    
    if len(my_ops) == 0:
        st.info("No operations currently assigned to you.")
    else:
        for _, op in my_ops.iterrows():
            priority_class = f"priority-{op['priority'].lower()}"
            
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**{op['operation_id']}**")
                    st.write(f"Client: {op['client_name']}")
                    st.write(f"Priority: {op['priority']}")
                    st.write(f"Address: {op['pickup_address'][:50]}...")
                
                with col2:
                    st.write(f"Amount: {format_currency(op['amount_usd'])}")
                    st.write(f"Status: {op['status']}")
                    st.write(f"Created: {op['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    if op.get('deadline'):
                        st.write(f"Deadline: {op['deadline']}")
                
                with col3:
                    if op['status'] == 'Assigned':
                        if st.button("✅ Accept", key=f"accept_{op['operation_id']}"):
                            st.success("Assignment accepted!")
                            clear_cache()
                            time.sleep(1)
                            st.rerun()
                    
                    elif op['status'] == 'Collecting':
                        if st.button("📸 Confirm Collection", key=f"confirm_{op['operation_id']}"):
                            st.success("Collection confirmed!")
                            clear_cache()
                            time.sleep(1)
                            st.rerun()
                    
                    elif op['status'] == 'Completed':
                        st.success("✅ Done")
                    else:
                        st.info("⏳ Waiting")
                
                st.divider()

def transaction_history_page():
    st.markdown('<h1 class="main-header">📊 Transaction History</h1>', unsafe_allow_html=True)
    
    operations_df, _ = load_data_with_cache()
    
    # Filter for completed operations
    completed_ops = operations_df[operations_df['status'] == 'Completed']
    
    if len(completed_ops) == 0:
        st.info("No completed transactions found.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", len(completed_ops))
    
    with col2:
        total_volume = completed_ops['amount_usd'].sum()
        st.metric("Total Volume", format_currency(total_volume))
    
    with col3:
        avg_amount = completed_ops['amount_usd'].mean()
        st.metric("Average Amount", format_currency(avg_amount))
    
    with col4:
        total_commission = completed_ops['commission_amount'].sum()
        st.metric("Total Commission", format_currency(total_commission))
    
    # Transaction history table with enhanced formatting
    st.markdown("### 📋 Recent Transactions")
    
    # Prepare display data
    display_completed = completed_ops.copy()
    display_completed['amount_usd'] = display_completed['amount_usd'].apply(lambda x: f"${x:,.0f}")
    display_completed['commission_amount'] = display_completed['commission_amount'].apply(lambda x: f"${x:,.2f}")
    display_completed['created_at'] = display_completed['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        display_completed[['operation_id', 'client_name', 'amount_usd', 'commission_amount', 'fx_provider', 'created_at']],
        use_container_width=True,
        column_config={
            "operation_id": "Operation ID",
            "client_name": "Client",
            "amount_usd": "Amount",
            "commission_amount": "Commission",
            "fx_provider": "FX Provider",
            "created_at": "Completed"
        }
    )

def main_app():
    # Enhanced sidebar with user info and navigation
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.user_name}")
        st.markdown(f"**Role:** {st.session_state.user_role.title()}")
        st.markdown(f"**Session:** {datetime.now().strftime('%H:%M:%S')}")
        
        st.divider()
        
        # Real-time status indicators
        st.markdown("### 🔴 System Status")
        st.success("✅ Database: Connected")
        st.success("✅ All systems operational")
        st.info(f"🔄 Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Quick stats in sidebar
        if st.session_state.user_role == "admin":
            operations_df, analytics = load_data_with_cache()
            st.markdown("### 📊 Quick Stats")
            st.metric("Active Ops", analytics["active_operations"], label_visibility="visible")
            st.metric("Today's Volume", f"${analytics['total_volume']/30:.0f}", label_visibility="visible")
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                if key.startswith(('authenticated', 'user_')):
                    del st.session_state[key]
            clear_cache()
            st.rerun()
    
    # Main navigation based on role
    if st.session_state.user_role == "admin":
        # Enhanced admin navigation
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
            operations_list()
        
        with tab4:
            analytics_page()
        
        with tab5:
            settings_page()
    
    elif st.session_state.user_role == "fx_provider":
        # FX Provider navigation
        tab1, tab2 = st.tabs([
            "🔄 My Operations", 
            "📊 Transaction History"
        ])
        
        with tab1:
            fx_provider_dashboard()
        
        with tab2:
            transaction_history_page()
    
    elif st.session_state.user_role == "collector":
        # Collector navigation
        tab1, tab2 = st.tabs([
            "📱 My Operations",
            "📊 My History"
        ])
        
        with tab1:
            collector_dashboard()
        
        with tab2:
            # Filter history for this collector
            operations_df, _ = load_data_with_cache()
            collector_name = st.session_state.user_name
            my_completed = operations_df[
                (operations_df['collector'].str.contains(collector_name.split()[0], case=False, na=False)) &
                (operations_df['status'] == 'Completed')
            ]
            
            st.markdown("### 📊 My Completed Operations")
            if len(my_completed) > 0:
                display_data = my_completed.copy()
                display_data['amount_usd'] = display_data['amount_usd'].apply(lambda x: f"${x:,.0f}")
                display_data['created_at'] = display_data['created_at'].dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(
                    display_data[['operation_id', 'client_name', 'amount_usd', 'created_at']],
                    use_container_width=True
                )
            else:
                st.info("No completed operations yet.")

# Main application logic
def main():
    # Initialize session state
    initialize_session_state()
    
    # Show login or main app
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()