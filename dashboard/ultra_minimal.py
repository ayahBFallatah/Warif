#!/usr/bin/env python3
"""
Ultra-minimal test to isolate Streamlit issues
"""

import streamlit as st

st.title("Ultra-Minimal Test")

st.write("If you see this, Streamlit is working.")

# Test basic elements
st.button("Test Button")
st.selectbox("Test Select", ["Option 1", "Option 2"])

# Test tabs
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

with tab1:
    st.write("Tab 1 content")

with tab2:
    st.write("Tab 2 content")

st.success("Test complete!")
