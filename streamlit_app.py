# streamlit_app.py - Error catching version
import sys
import traceback

# First, let's catch any import errors
try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from datetime import datetime, timedelta
    import uuid
    import time
    
    print("✅ All imports successful")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
    sys.exit(1)

# Wrap the entire app in try-catch
try:
    # Configure page
    st.set_page_config(
        page_title="ALMA - Financial Exchange Control Platform",
        page_icon="🏦",
        layout="wide"
    )
    
    print("✅ Page config successful")
    
    # Simple test content
    st.title("🏦 ALMA - Test Version")
    st.success("✅ App is running successfully!")
    st.write(f"Python version: {sys.version}")
    st.write(f"Streamlit version: {st.__version__}")
    
    # Test basic functionality
    if st.button("Test Button"):
        st.success("Button works!")
    
    # Test data display
    test_data = pd.DataFrame({
        'Operation': ['MSB-001', 'MSB-002', 'MSB-003'],
        'Amount': [5000, 10000, 15000],
        'Status': ['Pending', 'Active', 'Completed']
    })
    
    st.subheader("Test Data")
    st.dataframe(test_data)
    
    # Test chart
    fig = px.bar(test_data, x='Operation', y='Amount', title='Test Chart')
    st.plotly_chart(fig, use_container_width=True)
    
    print("✅ App content rendered successfully")

except Exception as e:
    print(f"❌ App error: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
    
    # Try to still show something in Streamlit
    try:
        st.error(f"Application Error: {e}")
        st.code(traceback.format_exc())
    except:
        print("❌ Can't even display error in Streamlit")
        
    sys.exit(1)

print("✅ Script completed successfully")