#!/usr/bin/env python3
"""
Streamlit Cloud Deployment Entry Point
Tour de France Simulator Dashboard
"""

import warnings
import logging
import os

# Suppress Streamlit ScriptRunContext warnings
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
warnings.filterwarnings("ignore", category=UserWarning)

# Configure logging to suppress warnings
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.scriptrunner_utils').setLevel(logging.ERROR)

# Set environment variables to suppress warnings
os.environ['PYTHONWARNINGS'] = 'ignore'

import streamlit as st
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main dashboard
from dashboard import main

if __name__ == "__main__":
    main() 