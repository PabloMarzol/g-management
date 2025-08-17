# utils.py - Utility functions for ALMA Streamlit Application
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Any

def generate_operation_id() -> str:
    """Generate unique operation ID with format MSB-YYYY-MM-DD-XXX"""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    # Use last 3 digits of timestamp for uniqueness
    unique_suffix = str(int(today.timestamp()))[-3:]
    return f"MSB-{date_str}-{unique_suffix}"

def format_currency(amount: float) -> str:
    """Format currency with proper separators"""
    return f"${amount:,.2f}"

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M")

def get_status_color(status: str) -> str:
    """Get color code for operation status"""
    status_colors = {
        "Pending": "#ff7f0e",
        "Assigned": "#2ca02c", 
        "Collecting": "#1f77b4",
        "Collected": "#17becf",
        "Validated": "#9467bd",
        "Delivered to FX": "#8c564b",
        "FX Processing": "#e377c2",
        "Completed": "#2ca02c",
        "Cancelled": "#d62728",
        "Error": "#d62728"
    }
    return status_colors.get(status, "#7f7f7f")

def create_status_badge(status: str) -> str:
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

def calculate_operation_metrics(operations_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate key operational metrics"""
    if operations_df.empty:
        return {
            "total_operations": 0,
            "total_volume": 0,
            "avg_operation_size": 0,
            "completion_rate": 0,
            "total_commission": 0
        }
    
    total_ops = len(operations_df)
    total_volume = operations_df["amount_usd"].sum()
    avg_size = operations_df["amount_usd"].mean()
    completed = len(operations_df[operations_df["status"] == "Completed"])
    completion_rate = (completed / total_ops) * 100 if total_ops > 0 else 0
    
    # Estimate commission (simplified calculation)
    total_commission = operations_df["amount_usd"].sum() * 0.05  # 5% average
    
    return {
        "total_operations": total_ops,
        "total_volume": total_volume,
        "avg_operation_size": avg_size,
        "completion_rate": completion_rate,
        "total_commission": total_commission
    }

def create_operations_chart(operations_df: pd.DataFrame, chart_type: str = "status"):
    """Create various charts for operations data"""
    
    if chart_type == "status":
        status_counts = operations_df["status"].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Operations by Status",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
    elif chart_type == "volume_trend":
        # Group by date and sum volume
        operations_df["date"] = pd.to_datetime(operations_df["created_at"]).dt.date
        daily_volume = operations_df.groupby("date")["amount_usd"].sum().reset_index()
        
        fig = px.line(
            daily_volume,
            x="date",
            y="amount_usd",
            title="Daily Volume Trend",
            markers=True
        )
        fig.update_layout(yaxis_title="Volume (USD)")
        
    elif chart_type == "collector_performance":
        collector_stats = operations_df.groupby("collector").agg({
            "operation_id": "count",
            "amount_usd": "sum"
        }).reset_index()
        collector_stats.columns = ["Collector", "Operations", "Total Volume"]
        
        fig = px.bar(
            collector_stats,
            x="Collector",
            y="Operations",
            title="Operations by Collector"
        )
        
    else:
        # Default to status chart
        return create_operations_chart(operations_df, "status")
    
    return fig

def display_operation_card(operation: pd.Series, show_actions: bool = True):
    """Display operation information in a card format"""
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"**ID:** {operation['operation_id']}")
        st.markdown(f"**Client:** {operation['client_name']}")
        st.markdown(f"**Amount:** {format_currency(operation['amount_usd'])}")
    
    with col2:
        st.markdown(f"**Status:** {operation['status']}")
        st.markdown(f"**Collector:** {operation['collector']}")
        st.markdown(f"**FX Provider:** {operation['fx_provider']}")
    
    with col3:
        st.markdown(f"**Created:** {format_datetime(operation['created_at'])}")
        if show_actions:
            if st.button("📋 Details", key=f"details_{operation['operation_id']}"):
                st.session_state[f"show_details_{operation['operation_id']}"] = True

def create_kpi_cards(metrics: Dict[str, Any]):
    """Create KPI cards for dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Operations",
            value=metrics["total_operations"],
            delta="+3 vs yesterday"
        )
    
    with col2:
        st.metric(
            label="Total Volume",
            value=format_currency(metrics["total_volume"]),
            delta=f"+{metrics['total_volume']*0.15:.0f}"
        )
    
    with col3:
        st.metric(
            label="Avg Operation Size",
            value=format_currency(metrics["avg_operation_size"]),
            delta=f"+{metrics['avg_operation_size']*0.08:.0f}"
        )
    
    with col4:
        st.metric(
            label="Completion Rate",
            value=f"{metrics['completion_rate']:.1f}%",
            delta="+2.3%"
        )

def validate_usdt_address(address: str) -> bool:
    """Basic USDT address validation (simplified)"""
    if not address:
        return False
    
    # Basic validation - should start with T (TRON) or 0x (ETH)
    if address.startswith("T") and len(address) == 34:
        return True
    elif address.startswith("0x") and len(address) == 42:
        return True
    
    return False

def get_sample_operations_data() -> pd.DataFrame:
    """Generate sample operations data for demonstration"""
    import random
    
    clients = ["John Smith", "Maria Garcia", "David Chen", "Sarah Johnson", "Michael Brown", "Lisa Wang"]
    collectors = ["Jessica", "Carlos", "Miguel", "Ana"]
    fx_providers = ["AlphaExchange", "BetaFX", "GammaFX", "DeltaFX"]
    statuses = ["Pending", "Collecting", "Collected", "Validated", "FX Processing", "Completed"]
    
    operations = []
    
    for i in range(15):
        operation_id = f"MSB-2025-08-{17-i//5}-{str(random.randint(100,999))}"
        
        operations.append({
            "operation_id": operation_id,
            "client_name": random.choice(clients),
            "amount_usd": random.randint(5000, 35000),
            "status": random.choice(statuses),
            "collector": random.choice(collectors),
            "fx_provider": random.choice(fx_providers),
            "created_at": datetime.now() - timedelta(hours=random.randint(1, 72)),
            "estimated_usdt": 0  # Will be calculated
        })
    
    df = pd.DataFrame(operations)
    # Calculate estimated USDT (simplified)
    df["estimated_usdt"] = df["amount_usd"] * 0.95  # Assume 5% total fees
    
    return df

def show_operation_timeline(operation_id: str):
    """Show operation timeline/progress"""
    st.markdown(f"### 📊 Operation Timeline: {operation_id}")
    
    # Sample timeline data
    timeline_steps = [
        {"step": "Created", "completed": True, "timestamp": "2025-08-17 09:00"},
        {"step": "Assigned", "completed": True, "timestamp": "2025-08-17 09:15"},
        {"step": "Collecting", "completed": True, "timestamp": "2025-08-17 10:30"},
        {"step": "Collected", "completed": False, "timestamp": ""},
        {"step": "Validated", "completed": False, "timestamp": ""},
        {"step": "FX Processing", "completed": False, "timestamp": ""},
        {"step": "Completed", "completed": False, "timestamp": ""}
    ]
    
    for i, step in enumerate(timeline_steps):
        col1, col2, col3 = st.columns([1, 3, 2])
        
        with col1:
            if step["completed"]:
                st.success("✅")
            else:
                st.info("⏳")
        
        with col2:
            st.write(f"**{step['step']}**")
        
        with col3:
            if step["timestamp"]:
                st.write(step["timestamp"])
            else:
                st.write("Pending")

def create_real_time_updates():
    """Create real-time updates section"""
    st.markdown("### 🔴 Real-time Updates")
    
    # Simulate real-time updates
    updates = [
        {"time": "14:35", "message": "Operation MSB-2025-08-17-001 - Cash collected by Jessica"},
        {"time": "14:32", "message": "Operation MSB-2025-08-17-002 - FX transfer completed"},
        {"time": "14:28", "message": "New operation MSB-2025-08-17-003 created"},
        {"time": "14:25", "message": "Collector Carlos accepted assignment"},
    ]
    
    for update in updates:
        st.info(f"**{update['time']}** - {update['message']}")

def export_operations_data(operations_df: pd.DataFrame, format_type: str = "csv"):
    """Export operations data in various formats"""
    if format_type == "csv":
        return operations_df.to_csv(index=False)
    elif format_type == "excel":
        # For Excel export, you'd use pandas.to_excel()
        return operations_df.to_csv(index=False)  # Simplified for now
    else:
        return operations_df.to_json(orient="records")

# Session state helpers
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'selected_operation' not in st.session_state:
        st.session_state.selected_operation = None
    if 'operations_data' not in st.session_state:
        st.session_state.operations_data = get_sample_operations_data()

def clear_session_state():
    """Clear session state on logout"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]