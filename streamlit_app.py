#!/usr/bin/env python3
"""
Streamlit Cloud Deployment Entry Point
Tour de France Simulator Dashboard
"""

import streamlit as st
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main dashboard
from dashboard import main

if __name__ == "__main__":
    main() 