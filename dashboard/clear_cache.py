#!/usr/bin/env python3
"""
Clear Streamlit cache and force reload
"""

import streamlit as st
import os
import shutil

def clear_cache():
    """Clear all Streamlit cache"""
    try:
        # Clear Streamlit cache
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Clear browser cache directory if it exists
        cache_dir = os.path.expanduser("~/.streamlit/cache")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print(f"✅ Cleared cache directory: {cache_dir}")
        
        print("✅ Streamlit cache cleared successfully!")
        return True
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")
        return False

if __name__ == "__main__":
    clear_cache()
