# operation_management.py - Advanced Operation Management for ALMA
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils import (
    generate_operation_id, format_currency, format_datetime, 
    create_status_badge, validate_usdt_address, show_operation_timeline
)
from config import calculate_commission, validate_operation_data

def operation_management_page():
    """Main operation management interface"""
    st.markdown("# 🎯 Operation Management Center")
    
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Active Operations", "➕ New Operation", "📊 Analytics", "⚙️ Bulk Actions"])
    
    with tab1:
        active_operations_view()
    
    with tab2:
        new_operation_form()
    
    with tab3:
        operations_analytics()
    
    with tab4:
        bulk_operations_management()

def active_operations_view():
    """Display and manage active operations"""
    st.markdown("### 📋 Active Operations Management")
    
    # Load operations data
    if 'operations_data' not in st.session_state:
        st.session_state.operations_data = get_sample_operations_data()
    
    operations_df = st.session_state.operations_data
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=operations_df['status'].unique(),
            default=operations_df['status'].unique()
        )
    
    with col2:
        collector_filter = st.multiselect(
            "Filter by Collector", 
            options=operations_df['collector'].unique(),
            default=operations_df['collector'].unique()
        )
    
    with col3:
        date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=7))
    
    with col4:
        date_to = st.date_input("To Date", value=datetime.now().date())
    
    # Apply filters
    filtered_df = operations_df[
        (operations_df['status'].isin(status_filter)) &
        (operations_df['collector'].isin(collector_filter)) &
        (operations_df['created_at'].dt.date >= date_from) &
        (operations_df['created_at'].dt.date <= date_to)
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
    
    # Operations list with enhanced management
    for idx, operation in filtered_df.iterrows():
        with st.expander(f"🔹 {operation['operation_id']} - {operation['client_name']} - {format_currency(operation['amount_usd'])}", expanded=False):
            manage_single_operation(operation)

def manage_single_operation(operation):
    """Manage a single operation with all available actions"""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("**📋 Operation Details**")
        st.write(f"**ID:** {operation['operation_id']}")
        st.write(f"**Client:** {operation['client_name']}")
        st.write(f"**Amount:** {format_currency(operation['amount_usd'])}")
        st.write(f"**Estimated USDT:** {operation['estimated_usdt']:,.2f}")
        
    with col2:
        st.markdown("**👥 Assigned Resources**")
        st.write(f"**Status:** {operation['status']}")
        st.write(f"**Collector:** {operation['collector']}")
        st.write(f"**FX Provider:** {operation['fx_provider']}")
        st.write(f"**Created:** {format_datetime(operation['created_at'])}")
    
    with col3:
        st.markdown("**⚡ Quick Actions**")
        
        # Status progression buttons
        current_status = operation['status']
        
        if current_status == 'Pending':
            if st.button("✅ Assign", key=f"assign_{operation['operation_id']}"):
                st.success("Operation assigned to collector")
        
        elif current_status == 'Collecting':
            if st.button("📸 Confirm Collection", key=f"collect_{operation['operation_id']}"):
                st.success("Cash collection confirmed")
        
        elif current_status == 'Collected':
            if st.button("✅ Validate", key=f"validate_{operation['operation_id']}"):
                st.success("Cash validated by admin")
        
        elif current_status == 'FX Processing':
            if st.button("💱 Confirm FX", key=f"fx_{operation['operation_id']}"):
                st.success("FX transfer confirmed")
        
        if st.button("📊 Timeline", key=f"timeline_{operation['operation_id']}"):
            show_operation_timeline(operation['operation_id'])
    
    # Additional operation details in expandable sections
    with st.expander("💰 Financial Breakdown", expanded=False):
        show_financial_breakdown(operation)
    
    with st.expander("📱 Communication Log", expanded=False):
        show_communication_log(operation['operation_id'])
    
    with st.expander("🔧 Advanced Actions", expanded=False):
        show_advanced_actions(operation)

def show_financial_breakdown(operation):
    """Show detailed financial breakdown for operation"""
    amount = operation['amount_usd']
    commission_info = calculate_commission(amount, "regular")  # Assume regular client
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💵 Amount Breakdown**")
        st.write(f"Gross Amount: {format_currency(commission_info['gross_amount'])}")
        st.write(f"Commission ({commission_info['commission_rate']*100:.1f}%): {format_currency(commission_info['commission_amount'])}")
        st.write(f"FX Commission (1.5%): {format_currency(commission_info['fx_commission'])}")
        st.write(f"**Net Amount: {format_currency(commission_info['net_amount'])}**")
    
    with col2:
        st.markdown("**🔄 USDT Conversion**")
        usdt_rate = 0.95  # Sample rate
        estimated_usdt = commission_info['net_amount'] * usdt_rate
        st.write(f"USD to USDT Rate: {usdt_rate}")
        st.write(f"Network Fees: ~$25")
        st.write(f"**Final USDT: {estimated_usdt:,.2f}**")

def show_communication_log(operation_id):
    """Show communication history for operation"""
    st.markdown("**📱 Recent Communications**")
    
    # Sample communication log
    communications = [
        {"time": "14:35", "from": "Jessica (Collector)", "message": "Arrived at client location"},
        {"time": "14:20", "from": "Admin", "message": "Operation assigned to Jessica"},
        {"time": "14:15", "from": "System", "message": "Operation created"},
    ]
    
    for comm in communications:
        st.info(f"**{comm['time']}** - {comm['from']}: {comm['message']}")
    
    # Add new communication
    with st.form(f"new_comm_{operation_id}"):
        new_message = st.text_area("Add Communication Note")
        if st.form_submit_button("Add Note"):
            st.success("Communication note added")

def show_advanced_actions(operation):
    """Show advanced operation management actions"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔄 Status Management**")
        new_status = st.selectbox(
            "Change Status",
            ["Pending", "Assigned", "Collecting", "Collected", "Validated", "FX Processing", "Completed", "Cancelled"],
            index=0,
            key=f"status_{operation['operation_id']}"
        )
        
        if st.button("Update Status", key=f"update_status_{operation['operation_id']}"):
            st.success(f"Status updated to {new_status}")
    
    with col2:
        st.markdown("**👥 Reassignment**")
        new_collector = st.selectbox(
            "Reassign Collector",
            ["Jessica", "Carlos", "Miguel", "Ana"],
            key=f"collector_{operation['operation_id']}"
        )
        
        if st.button("Reassign", key=f"reassign_{operation['operation_id']}"):
            st.success(f"Operation reassigned to {new_collector}")
    
    st.markdown("**⚠️ Emergency Actions**")
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🚨 Mark as Priority", key=f"priority_{operation['operation_id']}"):
            st.warning("Operation marked as priority")
    
    with col4:
        if st.button("❌ Cancel Operation", key=f"cancel_{operation['operation_id']}"):
            st.error("Operation cancelled")

def new_operation_form():
    """Enhanced form for creating new operations"""
    st.markdown("### ➕ Create New Operation")
    
    with st.form("enhanced_new_operation", clear_on_submit=True):
        # Client Information Section
        st.markdown("#### 👤 Client Information")
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("Client Name*", placeholder="Enter full client name")
            client_phone = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
            client_email = st.text_input("Email (Optional)", placeholder="client@example.com")
        
        with col2:
            client_type = st.selectbox("Client Type", ["Regular", "Frequent"])
            client_notes = st.text_area("Client Notes", placeholder="Any special instructions...")
        
        pickup_address = st.text_area("Pickup Address*", placeholder="Full address with landmarks")
        
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
                commission_info = calculate_commission(amount_usd, client_type.lower())
                st.info(f"Commission: {format_currency(commission_info['commission_amount'])} ({commission_info['commission_rate']*100:.1f}%)")
                st.info(f"Net to convert: {format_currency(commission_info['net_amount'])}")
        
        with col4:
            usdt_wallet = st.text_input("USDT Wallet Address*", placeholder="T... or 0x...")
            if usdt_wallet and not validate_usdt_address(usdt_wallet):
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
        auto_notifications = st.checkbox("Send automatic notifications", value=True)
        require_photos = st.checkbox("Require photo evidence", value=True)
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Operation", use_container_width=True)
        
        if submitted:
            # Validate data
            operation_data = {
                "client_name": client_name,
                "amount": amount_usd,
                "usdt_wallet": usdt_wallet,
                "pickup_address": pickup_address
            }
            
            errors = validate_operation_data(operation_data)
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Create operation
                operation_id = generate_operation_id()
                
                # Add to session state (in real app, would save to database)
                new_operation = {
                    "operation_id": operation_id,
                    "client_name": client_name,
                    "amount_usd": amount_usd,
                    "status": "Pending",
                    "collector": collector if collector != "Auto-assign" else "Jessica",
                    "fx_provider": fx_provider if fx_provider != "Auto-select" else "AlphaExchange",
                    "created_at": datetime.now(),
                    "estimated_usdt": commission_info['net_amount'] * 0.95
                }
                
                if 'operations_data' not in st.session_state:
                    st.session_state.operations_data = pd.DataFrame()
                
                # Add new operation to dataframe
                new_row = pd.DataFrame([new_operation])
                st.session_state.operations_data = pd.concat([st.session_state.operations_data, new_row], ignore_index=True)
                
                st.success(f"✅ Operation {operation_id} created successfully!")
                
                # Show operation summary
                with st.expander("📋 Operation Summary", expanded=True):
                    col7, col8 = st.columns(2)
                    with col7:
                        st.write(f"**Operation ID:** {operation_id}")
                        st.write(f"**Client:** {client_name}")
                        st.write(f"**Amount:** {format_currency(amount_usd)}")
                        st.write(f"**Commission:** {format_currency(commission_info['commission_amount'])}")
                    with col8:
                        st.write(f"**Collector:** {collector}")
                        st.write(f"**FX Provider:** {fx_provider}")
                        st.write(f"**Priority:** {priority}")
                        st.write(f"**Estimated USDT:** {new_operation['estimated_usdt']:,.2f}")

def operations_analytics():
    """Analytics dashboard for operations"""
    st.markdown("### 📊 Operations Analytics")
    
    if 'operations_data' not in st.session_state or st.session_state.operations_data.empty:
        st.info("No operations data available for analytics")
        return
    
    operations_df = st.session_state.operations_data
    
    # Time period selector
    period = st.selectbox("Analytics Period", ["Last 7 days", "Last 30 days", "Last 90 days", "All time"])
    
    # Performance metrics
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
        # Volume by collector
        collector_volume = operations_df.groupby('collector')['amount_usd'].sum().reset_index()
        fig_volume = px.bar(
            collector_volume,
            x='collector',
            y='amount_usd',
            title="Volume by Collector"
        )
        st.plotly_chart(fig_volume, use_container_width=True)
    
    # Performance trends
    st.markdown("#### 📈 Performance Trends")
    
    # Create daily aggregation
    operations_df['date'] = operations_df['created_at'].dt.date
    daily_stats = operations_df.groupby('date').agg({
        'operation_id': 'count',
        'amount_usd': 'sum'
    }).reset_index()
    daily_stats.columns = ['Date', 'Operations Count', 'Total Volume']
    
    # Daily operations trend
    fig_trend = px.line(
        daily_stats,
        x='Date',
        y='Operations Count',
        title="Daily Operations Trend",
        markers=True
    )
    st.plotly_chart(fig_trend, use_container_width=True)

def bulk_operations_management():
    """Bulk operations management tools"""
    st.markdown("### ⚙️ Bulk Operations Management")
    
    if 'operations_data' not in st.session_state or st.session_state.operations_data.empty:
        st.info("No operations available for bulk management")
        return
    
    operations_df = st.session_state.operations_data
    
    # Selection criteria
    st.markdown("#### 🎯 Select Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_selection = st.multiselect(
            "By Status",
            options=operations_df['status'].unique(),
            default=[]
        )
    
    with col2:
        collector_selection = st.multiselect(
            "By Collector",
            options=operations_df['collector'].unique(),
            default=[]
        )
    
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=[datetime.now().date() - timedelta(days=7), datetime.now().date()],
            key="bulk_date_range"
        )
    
    # Apply filters
    filtered_df = operations_df.copy()
    
    if status_selection:
        filtered_df = filtered_df[filtered_df['status'].isin(status_selection)]
    if collector_selection:
        filtered_df = filtered_df[filtered_df['collector'].isin(collector_selection)]
    
    st.write(f"**Selected Operations:** {len(filtered_df)}")
    
    if len(filtered_df) > 0:
        # Bulk actions
        st.markdown("#### ⚡ Bulk Actions")
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            if st.button("📧 Send Notifications"):
                st.success(f"Notifications sent for {len(filtered_df)} operations")
        
        with col5:
            if st.button("📊 Export Data"):
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"operations_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col6:
            if st.button("🔄 Bulk Status Update"):
                st.info("Bulk status update feature coming soon")
        
        # Show selected operations
        st.markdown("#### 📋 Selected Operations")
        st.dataframe(
            filtered_df[['operation_id', 'client_name', 'amount_usd', 'status', 'collector']],
            use_container_width=True
        )

def get_sample_operations_data():
    """Generate enhanced sample data"""
    import random
    
    clients = ["John Smith", "Maria Garcia", "David Chen", "Sarah Johnson", "Michael Brown", "Lisa Wang"]
    collectors = ["Jessica", "Carlos", "Miguel", "Ana"]
    fx_providers = ["AlphaExchange", "BetaFX", "GammaFX", "DeltaFX"]
    statuses = ["Pending", "Assigned", "Collecting", "Collected", "Validated", "FX Processing", "Completed"]
    
    operations = []
    
    for i in range(20):
        operation_id = f"MSB-2025-08-{17-i//5}-{str(random.randint(100,999))}"
        amount = random.randint(1000, 35000)
        
        operations.append({
            "operation_id": operation_id,
            "client_name": random.choice(clients),
            "amount_usd": amount,
            "status": random.choice(statuses),
            "collector": random.choice(collectors),
            "fx_provider": random.choice(fx_providers),
            "created_at": datetime.now() - timedelta(hours=random.randint(1, 168)),
            "estimated_usdt": amount * 0.95  # Simplified calculation
        })
    
    return pd.DataFrame(operations)